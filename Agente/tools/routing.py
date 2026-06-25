"""
Herramienta transversal del orquestador — la decisión ADAPTATIVA del routing.

`set_profile` deja que el ORQUESTADOR elija el perfil del turno RAZONANDO sobre
la petición (decisión del LLM, no de una regla). El perfil fija qué cadena de
modelos usa el router (ver `router/config.py::PROFILES`).

Dos límites deliberados:
  - Si el usuario forzó un perfil (/perfil) o la red de seguridad de privacidad
    saltó (palabras sensibles en el mensaje, ver botutils.needs_privacy), el
    perfil está FIJADO y esta tool no lo cambia: el juicio del LLM nunca pisa
    una garantía.
  - El cambio afecta a las llamadas POSTERIORES del turno: por eso las reglas
    del orquestador (AGENTS.md) piden llamarla AL PRINCIPIO, antes de delegar.
"""
from __future__ import annotations

from langchain_core.tools import tool

from router import config, metrics


@tool
def set_profile(profile: str) -> str:
    """Fija el perfil de enrutamiento del turno. Llámala AL PRINCIPIO, antes de delegar.

    Elige según la petición Y la respuesta esperada:
    - "privacidad": datos LOCALES sensibles — accesos/credenciales (logs, intentos
      SSH, fallos de auth/sudo, contraseñas) Y configuración de seguridad (firewall,
      puertos a la escucha) → los procesa el modelo LOCAL (rápido y estable en la GPU),
      así NO salen a un LLM en la nube. OJO: las herramientas que consultan Internet
      por naturaleza (reputación de IP, CVEs, DNS, TLS, subdominios) SIGUEN saliendo
      aunque el perfil sea privacidad; para esas no aporta nada → "equilibrio".
    - "potencia": análisis profundo / informes / auditorías de máxima calidad QUE NO
      lean datos de seguridad locales. Si el informe va a leer logs/ssh/auth/firewall/
      puertos → usa "privacidad" (manda sobre potencia: mejor en local que filtrar a la nube).
    - "velocidad": consultas rápidas, simples y NO sensibles (¿está activo nginx?,
      estado en una línea). Las que tocan ssh/logs/credenciales/firewall/puertos ya van fijadas a privacidad.
    - "equilibrio": todo lo demás (es el valor por defecto: si dudas, no la llames).
    """
    p = (profile or "").strip().lower()
    if p not in config.PROFILE_NAMES:
        return (f"ERROR: perfil inválido {profile!r}. "
                f"Válidos: {', '.join(config.PROFILE_NAMES)}.")
    if not metrics.set_profile(p):
        return ("El perfil de este turno ya está FIJADO (forzado por el usuario "
                "o por la red de seguridad de privacidad). Continúa con la tarea.")
    return f"Perfil de enrutamiento fijado: '{p}'. Continúa con la tarea."
