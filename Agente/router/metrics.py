"""
Observabilidad EN MEMORIA: el registro por turno de llamadas LLM y de tools.

En pocas palabras: lleva la "cuenta" de lo que pasó en cada mensaje (qué modelos
y herramientas se usaron, cuántos tokens, cuánto tardó) para mostrar el pie de
métricas al final de la respuesta. Aquí vive también el PERFIL del turno.

Sin dependencias ni persistencia. Cada turno guarda su estado en `contextvars`
que se fijan UNA vez al inicio (`start_turn`) y después solo se MUTAN: así los
subcontextos que LangGraph copia para el orquestador y los subagentes comparten
el mismo objeto — y por eso la tool `set_profile` (que corre en un subcontexto)
puede cambiar el perfil del turno y que el router lo vea. Un `ContextVar.set()`
dentro del subcontexto NO propagaría; mutar el objeto compartido sí.

Antes esto persistía en SQLite; para el TFG basta el registro en memoria.
"""
from __future__ import annotations

import contextvars
import time
from typing import Any, Optional

from langchain_core.callbacks import BaseCallbackHandler

from router import config

# ---------------------------------------------------------------------------
# Estado del turno (perfil + registros). None = "fuera de turno".
# ---------------------------------------------------------------------------
_turn_profile: contextvars.ContextVar[Optional[dict]] = contextvars.ContextVar(
    "_turn_profile", default=None
)
_llm_calls: contextvars.ContextVar[Optional[list[dict]]] = contextvars.ContextVar(
    "_llm_calls", default=None
)
_tool_calls: contextvars.ContextVar[Optional[list[dict]]] = contextvars.ContextVar(
    "_tool_calls", default=None
)
# Ficheros que el agente pide ADJUNTAR (informes): se envían como documento por
# Telegram SIN que ningún LLM relea su contenido (evita fugas a la nube).
_files_to_send: contextvars.ContextVar[Optional[list[str]]] = contextvars.ContextVar(
    "_files_to_send", default=None
)


def start_turn(profile: str = config.DEFAULT_PROFILE, locked: bool = False,
               forced: bool = False) -> None:
    """Arranca un turno: registros vacíos y perfil inicial.

    `locked=True` FIJA el perfil para todo el turno (lo usan el forzado del
    usuario vía /perfil, la red de seguridad de privacidad y la reanudación
    HITL): `set_profile` no podrá cambiarlo.
    `forced=True` (SOLO /perfil explícito del usuario) hace el perfil ABSOLUTO:
    ni siquiera `force_privacy` (el pin de las tools sensibles) lo cambia. Sirve
    para pruebas/comparativas (cap. evaluación): fuerzas un perfil y se usa ESE
    pase lo que pase. El modo AUTO (forced=False) sí queda siempre protegido.
    """
    _turn_profile.set({"profile": profile, "locked": locked, "forced": forced})
    _llm_calls.set([])
    _tool_calls.set([])
    _files_to_send.set([])


def current_profile() -> str:
    """Perfil activo del turno (el por defecto si no hay turno)."""
    estado = _turn_profile.get()
    return estado["profile"] if estado else config.DEFAULT_PROFILE


def set_profile(profile: str) -> bool:
    """Cambia el perfil del turno (lo usa la tool `set_profile` del orquestador).

    Devuelve False si no hay turno o el perfil está FIJADO (usuario o red de
    seguridad): la decisión del LLM nunca pisa una garantía.
    """
    estado = _turn_profile.get()
    if estado is None or estado["locked"]:
        return False
    estado["profile"] = profile
    return True


def force_privacy() -> None:
    """Fija privacidad para el RESTO del turno y lo BLOQUEA (garantía determinista).

    La invocan las herramientas que LEEN datos sensibles (intentos SSH, fallos de
    auth/sudo —Tier-1—, cortafuegos y puertos —Tier-2—): aunque el turno empezara en
    la nube (la red de palabras no saltó porque el mensaje no traía palabra-trampa,
    p. ej. "¿y esa IP?" o "haz la auditoría"), el RESULTADO sensible lo procesa el
    modelo LOCAL en el siguiente salto y NO sale del equipo. Es fail-safe: solo hace
    el turno MÁS privado, nunca menos.

    EXCEPCIÓN: si el usuario FORZÓ un perfil con `/perfil` (`forced=True`), se
    respeta — ese override es EXPLÍCITO (para pruebas/comparativas del cap.
    evaluación). El modo AUTO (por defecto) sigue siempre protegido.
    """
    estado = _turn_profile.get()
    if estado is None or estado.get("forced"):
        return
    estado["profile"] = config.PRIVACY_PROFILE
    estado["locked"] = True


# ---------------------------------------------------------------------------
# Registro de llamadas LLM (lo escribe el FallbackChatModel)
# ---------------------------------------------------------------------------
def record_llm(
    *,
    model: str,
    provider: str,
    is_fallback: bool,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    latency_ms: int = 0,
    error: Optional[str] = None,
) -> None:
    """Apunta una llamada LLM del turno."""
    calls = _llm_calls.get()
    if calls is None:
        return
    calls.append(
        {
            "model": model,
            "provider": provider,
            "profile": current_profile(),
            "is_fallback": is_fallback,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "latency_ms": latency_ms,
            "error": error,
        }
    )


def llm_calls() -> list[dict]:
    """Llamadas LLM registradas en el turno actual (lista vacía fuera de turno)."""
    return _llm_calls.get() or []


def tool_calls() -> list[dict]:
    """Tool-calls registradas en el turno actual (lista vacía fuera de turno)."""
    return _tool_calls.get() or []


def queue_file(path: str) -> None:
    """Encola un fichero para que el bot lo ENVÍE como documento tras el turno.

    Lo usa la tool `adjuntar_fichero`: el fichero (p. ej. un informe en /workspace)
    se manda directo a Telegram SIN que ningún LLM relea su contenido (evita fugas
    a la nube + entrega exacta). Muta la lista compartida del turno (igual que el
    resto de registros), así el append en el subcontexto de la tool lo ve el bot.
    """
    files = _files_to_send.get()
    if files is not None:
        files.append(path)


def files_to_send() -> list[str]:
    """Ficheros encolados en el turno actual para adjuntar por Telegram."""
    return _files_to_send.get() or []


class ToolMetricsCallback(BaseCallbackHandler):
    """Apunta en memoria cada tool-call del turno (inicio→fin) para el pie.

    LangGraph propaga este callback a TODOS los nodos (orquestador y subagentes),
    así que captura todas las tool-calls del turno con su duración y resultado.
    """

    def __init__(self) -> None:
        self._starts: dict[Any, tuple[float, str]] = {}

    def on_tool_start(self, serialized, input_str, *, run_id=None, **kwargs) -> None:
        name = (serialized or {}).get("name") or "?"
        self._starts[run_id] = (time.monotonic(), name)

    def _finish(self, run_id, ok: bool) -> None:
        rec = self._starts.pop(run_id, None)
        if not rec:
            return
        t0, name = rec
        calls = _tool_calls.get()
        if calls is not None:
            calls.append(
                {"tool": name, "duration_ms": int((time.monotonic() - t0) * 1000), "ok": ok}
            )

    def on_tool_end(self, output, *, run_id=None, **kwargs) -> None:
        self._finish(run_id, True)

    def on_tool_error(self, error, *, run_id=None, **kwargs) -> None:
        self._finish(run_id, False)
