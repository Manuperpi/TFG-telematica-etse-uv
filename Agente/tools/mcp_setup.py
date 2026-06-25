"""
Integración MCP: servidor OFICIAL de Google Threat Intelligence (GTI).

Nos conectamos a un servidor MCP **oficial de Google** (`google/mcp-security`,
servidor GTI), no a uno escrito por nosotros ni a uno comunitario. GTI da
inteligencia de amenazas sobre IPs, dominios, hashes y ficheros (está construido
sobre VirusTotal, propiedad de Google). Eso es interoperabilidad MCP real y de
fuente fiable, y encaja con el subagente de SEGURIDAD (defensa).

Patrón de la doc de Deep Agents: `MultiServerMCPClient` → `get_tools()`.

Requisitos para activarlo (si faltan, devuelve [] y el agente arranca sin MCP):
  - `uv` instalado (pip install uv).
  - El repo `google/mcp-security` CLONADO en el equipo; `GTI_MCP_DIR` apunta a
    su carpeta `server/gti/gti_mcp` (así ejecutas código que puedes auditar).
  - `VT_APIKEY` = clave de VirusTotal (tier gratuito en virustotal.com).
"""
from __future__ import annotations

import os
import sys
from typing import Any

from router import config

# Variables de entorno NO sensibles que el subproceso (uv + servidor GTI)
# necesita para arrancar. Pasamos SOLO estas + VT_APIKEY: así el servidor de
# terceros no hereda tus secretos (token de Telegram, claves de Google/OpenRouter).
_SAFE_ENV_KEYS = ("PATH", "HOME", "USER", "LANG", "LC_ALL", "TMPDIR", "TEMP", "TMP")


async def build_mcp_tools() -> list[Any]:
    """Conecta al servidor MCP oficial de GTI y devuelve sus herramientas.

    Filtra a la whitelist (config.GTI_TOOLS_WHITELIST): GTI expone ~25 tools, pero
    inyectarlas todas confunde a los modelos pequeños y dispara el contexto. Nos
    quedamos solo con las que usamos.
    """
    api_key = os.environ.get("VT_APIKEY", "").strip()
    gti_dir = os.environ.get("GTI_MCP_DIR", "").strip()  # .../server/gti/gti_mcp
    if not api_key or not gti_dir:
        return []  # MCP desactivado: arranque limpio sin GTI

    # Entorno MÍNIMO para el subproceso: solo variables no sensibles + la clave VT.
    safe_env = {k: os.environ[k] for k in _SAFE_ENV_KEYS if k in os.environ}
    safe_env["VT_APIKEY"] = api_key

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        client = MultiServerMCPClient({
            "gti": {
                "transport": "stdio",
                "command": "uv",
                # Ejecuta el servidor GTI desde el repo clonado (código auditable).
                "args": ["--directory", gti_dir, "run", "server.py"],
                "env": safe_env,
            },
        })
        tools = await client.get_tools()
        whitelist = config.GTI_TOOLS_WHITELIST
        if whitelist:  # nos quedamos solo con las herramientas elegidas
            tools = [t for t in tools if getattr(t, "name", "") in whitelist]
        return list(tools)
    except Exception as error:  # noqa: BLE001 — nunca tumbar el bot por el MCP
        print(f"[mcp] aviso: no se pudo activar el MCP de GTI "
              f"({type(error).__name__}: {error}). ¿Está 'uv' y GTI_MCP_DIR bien?",
              file=sys.stderr)
        return []
