"""
Configuración del router de modelos: qué cadena de modelos usa cada PERFIL.

En pocas palabras: es la TABLA que dice "para el perfil X, usa estos modelos en
este orden". Si quieres cambiar qué LLM se usa, se toca aquí y solo aquí.

Esta es la ÚNICA fuente de verdad del reparto de modelos. Para añadir, quitar o
reordenar modelos, edita `PROFILES`. El resto del código (fallback, agente) no
necesita cambios.

Cada candidato es un `spec` "<provider>:<model_id>" (lo que entiende
init_chat_model de LangChain). Dentro de un perfil, el ORDEN importa: el primero
es el preferido; el resto son fallbacks (si el preferido falla/429, se prueba el
siguiente).

⚠️ VERIFICAR los model_id exactos contra cada proveedor antes de arrancar en
producción (un id mal escrito hace fallar el cliente al instanciarse).
"""
from __future__ import annotations

import os

# --- Identificadores de modelo (TODOS abiertos) ---
# Pool: 4 modelos abiertos en 2 proveedores cloud (Google + OpenRouter) + el
# modelo local (Ollama). (Groq se descartó: su cuota diaria de tokens era
# demasiado ajustada y caía a fallback siempre.)
GEMMA_31B = "google_genai:gemma-4-31b-it"
GEMMA_26B = "google_genai:gemma-4-26b-a4b-it"  # verificado contra la API de Google
# OpenRouter (modelos ':free', necesita OPENROUTER_API_KEY + langchain-openrouter).
# Disponibles (los populares como qwen3-next/llama-70b dan 429 constante) y
# buenos tool-callers. Cuota gratuita por CUENTA (~1000/día con saldo). Dos papeles y dos
# TAMAÑOS distintos (medido con tests/bench_serio.py, 10 llamadas c/u):
#   - gpt-oss-120B  → CALIDAD: 10/10 tool-calls, latencia CLAVADA (2,1-3,4 s).
#   - nemotron-nano-30B (3B activos) → VELOCIDAD: el más rápido (1,3 s) y 10/10.
# Se RETIRÓ Nemotron-Super 120B: mismo tamaño que gpt-oss (redundante) y menos
# consistente (1,3-9,1 s). Antes ya se descartó la "Ultra" 550B por inusable
# (~0,1 tok/s, 269 s/llamada). Y se EVITAN los ':free' de razonamiento: gastan su
# presupuesto "pensando" y a veces no llegan a emitir la llamada (finish=length).
OPENROUTER_OSS = "openrouter:openai/gpt-oss-120b:free"                 # OpenAI 120B (calidad)
OPENROUTER_NANO = "openrouter:nvidia/nemotron-3-nano-30b-a3b:free"     # NVIDIA 30B/3B-act (velocidad)

# OpenRouter solo entra si hay key. Sin key, los modelos OpenRouter se omiten.
OPENROUTER_ENABLED = bool(os.environ.get("OPENROUTER_API_KEY", "").strip())

# --- Modelo local (Ollama) ---
# Cumple dos papeles: (1) ÚNICO modelo del perfil "privacidad" (todo en local,
# los datos NO salen del mini-PC) y (2) ÚLTIMO RECURSO que CIERRA las demás
# cadenas (velocidad, equilibrio, potencia) — la válvula de escape sin cuota:
# si toda la nube falla (429/caída), el agente sigue respondiendo (lento, pero vivo).
# Se activa con OLLAMA_ENABLED=true; apagado, simplemente no entra en las cadenas.
OLLAMA_ENABLED = os.environ.get("OLLAMA_ENABLED", "false").strip().lower() == "true"
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = "ollama:" + os.environ.get("OLLAMA_MODEL", "gemma4:e4b")
# Ventana de contexto de Ollama. El system prompt de deepagents ocupa ~8000
# tokens; el defecto de Ollama (~4096) lo TRUNCA y el modelo se queda sin
# instrucciones/tools → respuestas vacías. Subimos a 16k y NO más: 32k salió peor y
# 128k CUELGA la iGPU (GPU Hang en prefills grandes). 16k es el techo ESTABLE de esta
# iGPU; los informes pesados se resuelven con split-delegation, no con más contexto.
OLLAMA_NUM_CTX = int(os.environ.get("OLLAMA_NUM_CTX", "16384"))

# Temperatura por defecto (0 = determinista, mejor para reproducibilidad/tests).
DEFAULT_TEMPERATURE = 0.0


# ===========================================================================
#  ACCIONES DE ESCRITURA (con aprobación humana) — administración real
# ===========================================================================
# Servicios que el agente PUEDE reiniciar (restart_service). Lista blanca: todo lo
# que no esté aquí se rechaza, aunque el LLM lo pida. En nuvol TODO corre en Docker,
# así que de servicios del HOST solo existen 'docker' y 'cron'; se deja SOLO 'cron'
# ('docker' se excluye a propósito: reiniciarlo tiraría todos los contenedores). Se
# excluyen también 'ssh'/'sshd' (no quedarte fuera) y 'agente' (no auto-matarse). La
# acción útil en una máquina Docker sería reiniciar CONTENEDORES (un restart_container,
# pendiente como trabajo futuro). Defensa en profundidad: el sudoers permite solo estos.
RESTART_WHITELIST: set[str] = {"cron"}

# PID mínimo que se permite terminar (kill_process). Por debajo viven procesos
# del sistema (init=1, daemons tempranos); rechazarlos evita accidentes graves.
KILL_MIN_PID = 100

# Procesos que NUNCA se pueden terminar (kill_process), aunque su PID sea >= 100:
# matarlos te dejaría FUERA (sshd, tailscaled) o tumbaría el HOST (systemd, docker,
# containerd). Se compara con el NOMBRE del proceso (psutil .name()); además se
# rechaza todo lo que empiece por "systemd" (journald/logind/resolved…). El propio
# agente ya está protegido aparte (guard de PID propio/padre en kill_process).
KILL_PROTECTED_NAMES: set[str] = {
    "systemd", "init", "sshd", "tailscaled", "dockerd", "containerd",
}


# ===========================================================================
#  MCP (Google Threat Intelligence) — qué tools del servidor exponer
# ===========================================================================
# El servidor GTI expone ~25 herramientas; inyectarlas todas dispara el nº de
# tools del subagente (mal para modelos pequeños/locales). Nos quedamos solo con
# las que de verdad usamos. Vaciar el set = exponerlas todas (no recomendado).
GTI_TOOLS_WHITELIST: set[str] = {"get_ip_address_report", "get_domain_report"}


# ===========================================================================
#  PERFILES DE ENRUTAMIENTO ADAPTATIVO  (el corazón del TFG)
# ===========================================================================
# El PERFIL del turno lo elige el ORQUESTADOR razonando (tool set_profile), con
# dos fijados que mandan más: el forzado del usuario (/perfil) y la red de
# seguridad de privacidad (botutils.needs_privacy). El ROUTER (fallback.py)
# escoge el modelo concreto DENTRO del perfil (el preferido, y cae al siguiente
# si falla/429/vacío). Así el enrutamiento se adapta a (1) la petición —vía
# perfil— y (2) el estado de los proveedores —vía fallback.
#
# Cada perfil es una cadena de modelos (preferido primero). Los que no se puedan
# construir/usar (sin key / Ollama apagado) se omiten solos; si un perfil se
# queda sin modelos, el router cae a EQUILIBRIO — SALVO 'privacidad', que nunca
# degrada a la nube (ver router/fallback.py).
_CLOUD_BIG = [OPENROUTER_OSS] if OPENROUTER_ENABLED else []    # gpt-oss (calidad)
_CLOUD_FAST = [OPENROUTER_NANO] if OPENROUTER_ENABLED else []  # nano-30b (el cloud más rápido)
_LOCAL = [OLLAMA_MODEL] if OLLAMA_ENABLED else []

PROFILES: dict[str, list[str]] = {
    # Máxima calidad: gpt-oss (el grande) primero, luego Gemma; local de salvavidas.
    "potencia": [*_CLOUD_BIG, GEMMA_31B, GEMMA_26B, *_LOCAL],
    # Mínima latencia: el nano-30B (el más rápido, 1,3 s) primero; Gemma-26B de
    # respaldo (cuota); el local (más lento, en la iGPU) cierra como último recurso.
    "velocidad": [*_CLOUD_FAST, GEMMA_26B, *_LOCAL],
    # SOLO local: nada sale del mini-PC. Si Ollama no está vivo, el router NO cae
    # a la nube: se niega y avisa (la privacidad es la garantía del perfil).
    "privacidad": [*_LOCAL],
    # Balance (por defecto). Gemma (Google) PRIMERO por fiabilidad y cuota alta;
    # gpt-oss de refuerzo; el local CIERRA la cadena: si toda la nube falla, el
    # agente no se muere.
    "equilibrio": [GEMMA_31B, GEMMA_26B, *_CLOUD_BIG, *_LOCAL],
}
DEFAULT_PROFILE = "equilibrio"
# Perfil SOLO-local: el router nunca lo degrada a la nube (garantía de privacidad).
PRIVACY_PROFILE = "privacidad"
PROFILE_NAMES = list(PROFILES)


def specs_for_profile(profile: str | None) -> list[str]:
    """Cadena de modelos (specs) de un perfil. Desconocido/vacío → EQUILIBRIO."""
    return PROFILES.get(profile or "") or PROFILES[DEFAULT_PROFILE]
