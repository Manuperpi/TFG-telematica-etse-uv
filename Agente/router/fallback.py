"""
FallbackChatModel: el modelo "envoltorio" donde vive el ENRUTAMIENTO ADAPTATIVO.

En pocas palabras: es el CEREBRO del router. Para deepagents parece un modelo
normal, pero por dentro mira el perfil del turno, elige el modelo de ese perfil
y, si falla, prueba el siguiente. Es el corazón del TFG.

Para deepagents es un `BaseChatModel` normal. Por dentro, en cada generación:
  1. Mira el PERFIL activo del turno (potencia/velocidad/privacidad/
     equilibrio; lo elige el ORQUESTADOR con la tool set_profile, salvo que el
     usuario lo fuerce o la red de seguridad de privacidad lo fije) y resuelve
     la cadena de modelos de ese perfil (ver `config.PROFILES`).
  2. Prueba esa cadena EN ORDEN: vincula las tools al vuelo, llama al proveedor
     real y, si falla (caído / 429 / respuesta vacía), cae al siguiente modelo.
  3. Registra métricas en memoria (perfil, modelo, proveedor, fallback, tokens,
     latencia) para el pie de la respuesta en Telegram.

Así el enrutamiento se adapta a la PETICIÓN (el perfil) y, ante un fallo del
proveedor preferido, degrada con elegancia al siguiente — el eje "adaptativo"
del TFG. (El control fino de cuota/circuit-breaker se retiró: el fallback ante
error/429 cubre el caso real sin la complejidad del token-bucket.)

Los modelos se construyen una sola vez y se cachean por spec (`_MODEL_CACHE`),
compartidos por todas las copias que deepagents cree con `bind_tools`.
"""
from __future__ import annotations

import sys
import threading
import time
from typing import Any, Optional

from langchain.chat_models import init_chat_model
from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import ConfigDict

from router import config, metrics


class EmptyResponseError(RuntimeError):
    """El modelo devolvió una respuesta SIN texto ni tool_calls.

    Es el fallo intermitente documentado de algunos ':free' de OpenRouter:
    la llamada "tiene éxito" pero llega vacía. Se trata como un fallo más
    para que el router caiga al siguiente candidato de la cadena.
    """


def _is_empty(message: BaseMessage) -> bool:
    """¿Respuesta sin contenido útil? (sin tool_calls y sin texto)."""
    if getattr(message, "tool_calls", None):
        return False
    c = message.content
    if isinstance(c, list):  # contenido por bloques → aplanar el texto
        c = "".join(b if isinstance(b, str) else str(b.get("text", ""))
                    for b in c if isinstance(b, (str, dict)))
    return not str(c).strip()


def _flatten_content(message: BaseMessage) -> BaseMessage:
    """Aplana el contenido por BLOQUES de los modelos 'thinking' a texto plano.

    Los modelos con razonamiento (qwen3.5, Gemma-4, gpt-oss) devuelven el
    contenido como lista de bloques (texto + razonamiento). Esos bloques de
    razonamiento (1) ROMPEN a otros proveedores al reenviarse como historial
    (langchain-openai/OpenRouter solo acepta bloques 'text'/'image_url') y (2)
    confunden la detección de 'vacío'. Nos quedamos solo con el TEXTO; los
    `tool_calls` y demás metadatos se preservan intactos (van en otro campo).
    """
    c = message.content
    if not isinstance(c, list):
        return message
    text = "".join(b if isinstance(b, str) else str(b.get("text", ""))
                   for b in c if isinstance(b, (str, dict)))
    return message.model_copy(update={"content": text})


def _provider_of(spec: str) -> str:
    return spec.split(":", 1)[0]


def _make(spec: str, temperature: float) -> BaseChatModel:
    """Convierte '<provider>:<model_id>' en un ChatModel instanciado."""
    provider, _, model_id = spec.partition(":")
    if not model_id:
        raise ValueError(f"spec inválido: {spec!r} (esperado 'provider:model')")
    kwargs: dict[str, Any] = {"model_provider": provider, "temperature": temperature}
    if provider == "ollama":
        kwargs["base_url"] = config.OLLAMA_BASE_URL
        kwargs["num_ctx"] = config.OLLAMA_NUM_CTX  # evita truncar el system prompt
        # Desactiva el modo 'thinking' del modelo local (lo tenían qwen3.5 y otros):
        # en contexto cargado de tools se quedaban RAZONANDO sin emitir respuesta ni
        # tool_call → el router lo leía como respuesta "vacía". Sin thinking, gastan
        # los tokens en la respuesta o en la llamada a herramienta, que es lo que el
        # agente necesita. (gemma4:e4b no usa thinking; el flag es inocuo entonces.)
        kwargs["reasoning"] = False
    return init_chat_model(model_id, **kwargs)


# ---------------------------------------------------------------------------
# Caché global de modelos construidos ((spec, temperatura) → modelo, o None).
# La temperatura entra en la clave: dos temperaturas distintas son dos modelos.
# ---------------------------------------------------------------------------
_MODEL_CACHE: dict[tuple[str, float], Optional[BaseChatModel]] = {}
_CACHE_LOCK = threading.Lock()

# Sonda de vida de Ollama: para gatear el perfil PRIVACIDAD y para saltar un
# daemon caído sin malgastar un intento. Se cachea unos segundos (el daemon no
# aparece/desaparece a cada llamada) y usa un timeout corto.
_OLLAMA_PROBE: tuple[float, bool] = (0.0, False)
_OLLAMA_PROBE_TTL = 30.0
_OLLAMA_PROBE_LOCK = threading.Lock()


def _ollama_alive() -> bool:
    """¿Responde el daemon de Ollama en OLLAMA_BASE_URL? (cacheado ~30s)."""
    global _OLLAMA_PROBE
    now = time.monotonic()
    with _OLLAMA_PROBE_LOCK:
        ts, alive = _OLLAMA_PROBE
        if now - ts < _OLLAMA_PROBE_TTL:
            return alive
    alive = False
    try:
        import httpx
        r = httpx.get(config.OLLAMA_BASE_URL.rstrip("/") + "/api/tags", timeout=1.5)
        alive = r.status_code == 200
    except Exception:  # noqa: BLE001 — daemon apagado / inalcanzable
        alive = False
    with _OLLAMA_PROBE_LOCK:
        _OLLAMA_PROBE = (now, alive)
    return alive


def _get_model(spec: str, temperature: float) -> Optional[BaseChatModel]:
    """Devuelve el modelo de `spec` (construyéndolo y cacheándolo una vez).

    Si no se puede construir (falta API key / paquete / Ollama apagado), cachea
    y devuelve None: ese candidato simplemente no se usa (degradación elegante).
    """
    key = (spec, temperature)
    with _CACHE_LOCK:
        if key in _MODEL_CACHE:
            return _MODEL_CACHE[key]
    model: Optional[BaseChatModel]
    try:
        model = _make(spec, temperature)
    except Exception as error:  # noqa: BLE001
        print(f"[router] aviso: omito {spec!r} ({type(error).__name__}: "
              f"{str(error)[:80]}).", file=sys.stderr)
        model = None
    with _CACHE_LOCK:
        _MODEL_CACHE[key] = model
    return model


class FallbackChatModel(BaseChatModel):
    """ChatModel adaptativo: elige modelo por PERFIL activo y cae al siguiente."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    temperature: float = config.DEFAULT_TEMPERATURE
    # Tools a vincular al vuelo (en langchain 1.x, bind_tools devuelve un
    # _ChatModelBinding que no es BaseChatModel; las guardamos y vinculamos en
    # cada llamada vía la interfaz Runnable).
    bound_tools: Optional[Any] = None
    bound_kwargs: Optional[dict] = None

    @property
    def _llm_type(self) -> str:
        return "fallback-router"

    def __hash__(self) -> int:
        return id(self)

    # ------------------------------------------------------------------ #
    # Resolución de candidatos según el perfil activo
    # ------------------------------------------------------------------ #
    def _usable(self, spec: str) -> bool:
        """¿El spec es construible y, si es local (Ollama), está vivo el daemon?

        El gate de vida va aquí, no en `_get_model`, para no cachear un None
        permanente: si Ollama vuelve a estar disponible, el modelo se reutiliza
        sin reiniciar el proceso.
        """
        if _get_model(spec, self.temperature) is None:
            return False
        if spec.startswith("ollama:") and not _ollama_alive():
            return False
        return True

    def _active_specs(self) -> list[str]:
        """Cadena USABLE del perfil activo.

        Si el perfil se queda sin modelos, cae a EQUILIBRIO… SALVO 'privacidad',
        que devuelve [] (nunca degrada a la nube: es la garantía del perfil; el
        `_generate` lo convierte en un error claro).
        """
        profile = metrics.current_profile()
        specs = [s for s in config.specs_for_profile(profile) if self._usable(s)]
        if specs:
            return specs
        if profile == config.PRIVACY_PROFILE:
            return []
        return [s for s in config.specs_for_profile(config.DEFAULT_PROFILE)
                if self._usable(s)]

    def _no_model_error(self) -> RuntimeError:
        """Error claro cuando no hay ningún modelo usable (mensaje según perfil)."""
        profile = metrics.current_profile()
        if profile == config.PRIVACY_PROFILE:
            return RuntimeError(
                "Perfil PRIVACIDAD sin modelo LOCAL disponible: Ollama está "
                "apagado o no responde. No envío datos sensibles a la nube. "
                "Arranca Ollama (o cambia de perfil con /perfil) y reintenta."
            )
        return RuntimeError("No hay ningún modelo disponible (revisa claves/Ollama).")

    def _candidate(self, spec: str):
        model = _get_model(spec, self.temperature)
        if self.bound_tools is not None:
            return model.bind_tools(self.bound_tools, **(self.bound_kwargs or {}))
        return model

    def _record(self, spec: str, is_fallback: bool, message: BaseMessage, latency_ms: int) -> None:
        usage = getattr(message, "usage_metadata", None) or {}
        metrics.record_llm(
            model=spec, provider=_provider_of(spec), is_fallback=is_fallback,
            prompt_tokens=int(usage.get("input_tokens", 0)),
            completion_tokens=int(usage.get("output_tokens", 0)),
            latency_ms=latency_ms,
        )

    def _fail(self, spec: str, is_fallback: bool, error: Exception) -> None:
        metrics.record_llm(
            model=spec, provider=_provider_of(spec), is_fallback=is_fallback,
            error=type(error).__name__,
        )

    @staticmethod
    def _call_kwargs(stop, kwargs) -> dict:
        ck = dict(kwargs)
        if stop is not None:
            ck["stop"] = stop
        return ck

    # ------------------------------------------------------------------ #
    # Interfaz BaseChatModel
    # ------------------------------------------------------------------ #
    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        specs = self._active_specs()
        if not specs:
            raise self._no_model_error()
        preferred = specs[0]
        ck = self._call_kwargs(stop, kwargs)
        last_error: Optional[Exception] = None
        for spec in specs:
            t0 = time.monotonic()
            try:
                message = _flatten_content(self._candidate(spec).invoke(messages, **ck))
                if _is_empty(message):
                    raise EmptyResponseError(f"respuesta vacía de {spec}")
                self._record(spec, spec != preferred, message, int((time.monotonic() - t0) * 1000))
                return ChatResult(generations=[ChatGeneration(message=message)])
            except Exception as error:  # noqa: BLE001 — probamos el siguiente
                self._fail(spec, spec != preferred, error)
                last_error = error
        assert last_error is not None
        raise last_error

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        specs = self._active_specs()
        if not specs:
            raise self._no_model_error()
        preferred = specs[0]
        ck = self._call_kwargs(stop, kwargs)
        last_error: Optional[Exception] = None
        for spec in specs:
            t0 = time.monotonic()
            try:
                message = _flatten_content(await self._candidate(spec).ainvoke(messages, **ck))
                if _is_empty(message):
                    raise EmptyResponseError(f"respuesta vacía de {spec}")
                self._record(spec, spec != preferred, message, int((time.monotonic() - t0) * 1000))
                return ChatResult(generations=[ChatGeneration(message=message)])
            except Exception as error:  # noqa: BLE001
                self._fail(spec, spec != preferred, error)
                last_error = error
        assert last_error is not None
        raise last_error

    def bind_tools(self, tools, **kwargs) -> "FallbackChatModel":
        """Guarda las tools (se vinculan al vuelo en cada llamada)."""
        return FallbackChatModel(
            temperature=self.temperature,
            bound_tools=tools, bound_kwargs=(kwargs or None),
        )


# ---------------------------------------------------------------------------
# Fábrica pública
# ---------------------------------------------------------------------------
def model_for(temperature: float = config.DEFAULT_TEMPERATURE) -> FallbackChatModel:
    """Devuelve el FallbackChatModel del agente.

    El modelo concreto se decide EN CADA LLAMADA según el perfil activo (y, ante
    un fallo, cae al siguiente de la cadena), no al construir.
    """
    return FallbackChatModel(temperature=temperature)
