"""
Bot de Telegram (aiogram 3.x) que expone el deep agent.

En pocas palabras: es la PUERTA de entrada. Recibe tus mensajes de Telegram,
comprueba que estás autorizado, llama al agente y te devuelve la respuesta —con
botones de aprobación si hace falta, diagramas y el pie de métricas—.

Funciones:
  - Whitelist por user_id (rechazo silencioso a no autorizados).
  - Un hilo conversacional por chat (thread_id = chat_id).
  - Human-in-the-loop: si el agente se pausa (p. ej. antes de nmap), muestra
    botones ✅/❌ y reanuda con Command(resume=...).
  - Envía como imagen los diagramas generados durante el turno.
  - Pie de métricas (en memoria) bajo cada respuesta (perfil, modelo, tokens,
    tok/s, tiempo); /verbose alterna el desglose detallado.

Ejecutar:  python bot.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from contextlib import suppress

from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command as CommandFilter
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotenv import load_dotenv
from langgraph.types import Command
import telegramify_markdown

from agent import build_agent, extract_text
from router import config
from router.metrics import (
    ToolMetricsCallback,
    current_profile,
    files_to_send,
    llm_calls,
    start_turn,
    tool_calls,
)
from tools.diagrams import DIAGRAMS_DIR
from tools.mcp_setup import build_mcp_tools
import botutils as bu

load_dotenv()

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    sys.exit("Falta TELEGRAM_BOT_TOKEN en .env")
_ALLOWED = bu.parse_whitelist(os.environ.get("TELEGRAM_ALLOWED_USERS", ""))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Estado por chat
_AGENT = None                       # se construye en main()
_verbose: set[int] = set()          # chats con pie detallado
# Aprobaciones pendientes por chat: (nº de acciones, perfil del turno pausado).
# Guardamos el perfil para REANUDAR con el mismo: si el turno era 'privacidad',
# la aprobación no debe degradarlo a la nube.
_pending: dict[int, tuple[int, str]] = {}
_forced_profile: dict[int, str] = {}  # perfil FORZADO por chat (ausente = auto)
_chat_locks: dict[int, asyncio.Lock] = {}  # un turno a la vez por chat

# Respuestas por TEXTO que valen como aprobación HITL (cuando el usuario escribe
# 'sí'/'no' en vez de pulsar el botón). Coincidencia EXACTA, para no malinterpretar
# una frase ("no sé qué hacer" no debe contar como rechazo).
_AFFIRM = {"si", "sí", "vale", "ok", "okay", "dale", "adelante", "sip", "yes", "✅", "👍"}
_NEGATE = {"no", "nop", "nope", "cancela", "cancelar", "rechaza", "rechazar", "para", "❌"}
_REJECT_MSG = ("El usuario ha RECHAZADO esta acción; NO se ejecuta. Informa brevemente de "
               "que la acción se ha cancelado y NO vuelvas a pedir confirmación.")


def _lock_for(chat_id: int) -> asyncio.Lock:
    """Candado por chat: evita dos turnos concurrentes sobre el mismo hilo
    (escribir mientras el agente trabaja corrompería el historial compartido)."""
    return _chat_locks.setdefault(chat_id, asyncio.Lock())


def _authorized(user_id: int | None) -> bool:
    return bool(_ALLOWED) and user_id in _ALLOWED


def _approval_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Aprobar", callback_data="approve"),
        InlineKeyboardButton(text="❌ Rechazar", callback_data="reject"),
    ]])


async def _keep_typing(chat_id: int) -> None:
    """Mantiene vivo el indicador 'escribiendo…' durante operaciones largas.

    El indicador de Telegram caduca a los ~5 s; lo refrescamos cada 4 s para
    que un escaneo largo (nmap puede tardar más de un minuto) no parezca colgado.
    """
    try:
        while True:
            await bot.send_chat_action(chat_id, "typing")
            await asyncio.sleep(4)
    except asyncio.CancelledError:
        pass


async def _reply(message: Message, text: str) -> None:
    """Envía `text` convirtiendo el Markdown del LLM al formato de Telegram.

    El LLM escribe Markdown de GitHub (**negrita**, ### títulos, tablas) que
    Telegram no interpreta. `telegramify_markdown` lo pasa a MarkdownV2
    (negrita real, tablas como bloques monoespaciados, escapando caracteres).
    Si la conversión o el envío fallan, cae a TEXTO PLANO (nunca se pierde el
    mensaje).
    """
    for chunk in bu.split_for_telegram(text, limit=3500):  # margen para el escape
        try:
            await message.answer(
                telegramify_markdown.markdownify(chunk), parse_mode="MarkdownV2"
            )
        except Exception:  # noqa: BLE001 — formato roto → texto plano
            await message.answer(chunk)


async def _run(chat_id: int, payload, message: Message,
               profile: str, locked: bool = True) -> None:
    """Invoca al agente y gestiona el resultado (interrupt o respuesta final).

    `profile` es el perfil INICIAL del turno y `locked` si está FIJADO: forzado
    por el usuario (/perfil), red de seguridad de privacidad o reanudación HITL.
    Si no está fijado, el ORQUESTADOR puede elegirlo con la tool set_profile.
    """
    async with _lock_for(chat_id):  # un turno a la vez por chat
        # `forced` = el usuario fijó este perfil con /perfil (no la red ni el HITL):
        # entonces es ABSOLUTO y ni force_privacy lo cambia (modo prueba/comparativa).
        start_turn(profile, locked=locked, forced=(chat_id in _forced_profile))

        before = bu.snapshot_files(DIAGRAMS_DIR)
        run_config = {
            "configurable": {"thread_id": str(chat_id)},
            "callbacks": [ToolMetricsCallback()],  # registra tool-calls (en memoria)
        }
        # Aviso VISIBLE mientras trabaja (se borra al llegar la respuesta) + el
        # indicador 'escribiendo…' de fondo.
        placeholder = await message.answer("⏳ Pensando…")
        typing = asyncio.create_task(_keep_typing(chat_id))
        try:
            result = await _AGENT.ainvoke(payload, config=run_config)
        except Exception as e:  # noqa: BLE001 — no tirar el bot por un fallo de un turno
            await message.answer(f"⚠️ Error procesando la petición: {type(e).__name__}: {e}")
            return
        finally:
            typing.cancel()
            try:
                await placeholder.delete()  # quitamos el "Pensando…"
            except Exception:  # noqa: BLE001
                pass

        # ¿El agente se ha pausado pidiendo aprobación?
        interrupts = result.get("__interrupt__") if isinstance(result, dict) else None
        if interrupts:
            value = getattr(interrupts[0], "value", interrupts[0])
            actions = value.get("action_requests", []) if isinstance(value, dict) else []
            # Guardamos el perfil VIGENTE (el orquestador pudo haberlo cambiado
            # con set_profile) para reanudar con el mismo.
            _pending[chat_id] = (len(actions) or 1, current_profile())
            desc = bu.describe_actions(actions)
            try:
                await message.answer(
                    telegramify_markdown.markdownify(desc),
                    reply_markup=_approval_keyboard(), parse_mode="MarkdownV2",
                )
            except Exception:  # noqa: BLE001 — formato roto → texto plano
                await message.answer(desc, reply_markup=_approval_keyboard())
            return

        # Respuesta final (Markdown del LLM → formato Telegram, troceada).
        await _reply(message, extract_text(result))

        # Diagramas nuevos generados durante el turno → como imagen.
        for path in bu.find_new_files(DIAGRAMS_DIR, before):
            try:
                await message.answer_photo(FSInputFile(path))
            except Exception:  # noqa: BLE001
                pass

        # Ficheros que el agente pidió adjuntar (informes) → como DOCUMENTO,
        # directo del disco a Telegram, SIN que ningún LLM relea su contenido
        # (evita fugar a la nube un informe redactado en local + entrega exacta).
        for path in files_to_send():
            try:
                await message.answer_document(FSInputFile(path))
            except Exception:  # noqa: BLE001
                pass

        # Pie de métricas (registros en memoria del turno).
        footer = bu.format_footer(llm_calls(), tool_calls(), chat_id in _verbose)
        if footer:
            await message.answer(footer)


# --------------------------------------------------------------------------- #
# Comandos
# --------------------------------------------------------------------------- #
def _profile_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="🤖 Auto (lo elige el agente)", callback_data="prof:auto")]]
    rows += [[InlineKeyboardButton(text=p.capitalize(), callback_data=f"prof:{p}")]
             for p in config.PROFILE_NAMES]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(CommandFilter("start", "help"))
async def cmd_help(msg: Message) -> None:
    if not _authorized(msg.from_user.id if msg.from_user else None):
        return
    await msg.answer(
        "Soy tu agente de administración y seguridad. Pregúntame por el estado "
        "del sistema, la seguridad o haz reconocimiento de red.\n\n"
        "Comandos:\n"
        "• /perfil — elegir perfil de enrutamiento (o dejarlo en auto)\n"
        "• /verbose — alterna el detalle del pie de métricas"
    )


@dp.message(CommandFilter("perfil"))
async def cmd_perfil(msg: Message) -> None:
    if not _authorized(msg.from_user.id if msg.from_user else None):
        return
    actual = _forced_profile.get(msg.chat.id)
    estado = f"forzado a *{actual}*" if actual else "🤖 *auto* (lo elige el agente)"
    await msg.answer(
        f"Perfil de enrutamiento actual: {estado}.\nElige uno:",
        reply_markup=_profile_keyboard(),
    )


@dp.message(CommandFilter("verbose"))
async def cmd_verbose(msg: Message) -> None:
    if not _authorized(msg.from_user.id if msg.from_user else None):
        return
    cid = msg.chat.id
    if cid in _verbose:
        _verbose.discard(cid)
        await msg.answer("Pie de métricas: modo compacto.")
    else:
        _verbose.add(cid)
        await msg.answer("Pie de métricas: modo detallado.")


# --------------------------------------------------------------------------- #
# Mensajes de texto y botones de aprobación
# --------------------------------------------------------------------------- #
async def _resume_pending(chat_id: int, approve: bool, reply_to: Message) -> None:
    """Reanuda el turno pausado por HITL (botón ✅/❌ o 'sí'/'no' por texto).

    Reanuda con el MISMO perfil del turno pausado, FIJADO: si era 'privacidad', el
    resto del turno tampoco sale a la nube.
    """
    rec = _pending.pop(chat_id, None)
    if rec is None:
        return
    n, profile = rec
    decisions = ([{"type": "approve"} for _ in range(n)] if approve
                 else [{"type": "reject", "message": _REJECT_MSG} for _ in range(n)])
    await _run(chat_id, Command(resume={"decisions": decisions}), reply_to, profile, locked=True)


@dp.message(F.text)
async def on_text(msg: Message) -> None:
    if not _authorized(msg.from_user.id if msg.from_user else None):
        return  # rechazo silencioso
    text = msg.text or ""
    chat_id = msg.chat.id
    # ¿Hay una aprobación HITL pendiente? Si el usuario responde por TEXTO en vez de
    # pulsar el botón, interpretamos sí/no y reanudamos; si es ambiguo, recordamos los
    # botones (no arrancamos un turno nuevo, que dejaría el __interrupt__ colgado).
    if chat_id in _pending:
        low = text.strip().lower().strip(" .!,;?¿¡")
        if low in _AFFIRM:
            await _resume_pending(chat_id, True, msg)
        elif low in _NEGATE:
            await _resume_pending(chat_id, False, msg)
        else:
            await msg.answer("⏸️ Tienes una acción pendiente de aprobación: pulsa ✅/❌ "
                             "arriba, o responde «sí» o «no».")
        return
    # Enrutamiento adaptativo: el perfil lo elige el ORQUESTADOR (tool set_profile)…
    # con dos excepciones que lo FIJAN antes de llamar a ningún modelo: el forzado del
    # usuario (/perfil) y la red de privacidad (palabras sensibles → ni la pregunta sale).
    forced = _forced_profile.get(chat_id)
    if forced:
        profile, locked = forced, True
    elif bu.needs_privacy(text):
        profile, locked = config.PRIVACY_PROFILE, True
    else:
        profile, locked = config.DEFAULT_PROFILE, False
    await _run(chat_id, {"messages": [{"role": "user", "content": text}]},
               msg, profile, locked=locked)


@dp.callback_query(F.data.in_({"approve", "reject"}))
async def on_decision(cb: CallbackQuery) -> None:
    # Responder YA para que Telegram no reintente el callback (operaciones
    # largas como nmap tardan mucho y Telegram reenviaría la pulsación).
    await cb.answer()
    if not _authorized(cb.from_user.id if cb.from_user else None):
        return
    chat_id = cb.message.chat.id
    # Guard anti-duplicado: si no hay aprobación pendiente, es una pulsación repetida.
    if chat_id not in _pending:
        return
    approve = cb.data == "approve"
    with suppress(TelegramBadRequest):
        await cb.message.edit_text("✅ Aprobado. Ejecutando…" if approve else "❌ Rechazado.")
    await _resume_pending(chat_id, approve, cb.message)


@dp.callback_query(F.data.startswith("prof:"))
async def on_profile(cb: CallbackQuery) -> None:
    await cb.answer()
    if not _authorized(cb.from_user.id if cb.from_user else None):
        return
    p = cb.data.split(":", 1)[1]
    cid = cb.message.chat.id
    if p == "auto":
        _forced_profile.pop(cid, None)
        text = "Perfil de enrutamiento: 🤖 Auto (lo elige el agente)."
    else:
        _forced_profile[cid] = p
        text = f"Perfil de enrutamiento FORZADO a: {p}."
        if p != config.PRIVACY_PROFILE:
            text += ("\n⚠️ Override TOTAL: en este perfil los datos sensibles "
                     "(ssh/auth/firewall/puertos) TAMBIÉN saldrán a la nube. "
                     "Vuelve a «Auto» o /perfil privacidad para la protección automática.")
    # Pulsar el mismo botón dos veces deja el texto idéntico y Telegram
    # rechaza el edit ("message is not modified"); es inofensivo, lo tragamos.
    with suppress(TelegramBadRequest):
        await cb.message.edit_text(text)


# --------------------------------------------------------------------------- #
# Arranque
# --------------------------------------------------------------------------- #
async def main() -> None:
    global _AGENT
    # MCP: build_mcp_tools() devuelve [] mientras esté apagado (arranque limpio).
    mcp_tools = await build_mcp_tools()
    _AGENT = build_agent(mcp_tools=mcp_tools)
    if not _ALLOWED:
        print("AVISO: TELEGRAM_ALLOWED_USERS vacío → el bot rechazará a todos.")

    print("Bot en marcha (long-polling).")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
