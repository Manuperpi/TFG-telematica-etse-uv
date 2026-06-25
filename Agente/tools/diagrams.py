"""
Herramienta transversal del orquestador — generación de diagramas (Mermaid → PNG).

El LLM escribe el diagrama en lenguaje Mermaid; esta tool lo renderiza con
**Kroki** (un contenedor Docker en el propio mini-PC → privacidad: los datos
del diagrama no salen de la máquina) y guarda el PNG en `workspace/diagrams/`.

El bot detecta los PNG nuevos generados durante el turno y los envía como
imagen por Telegram (ver bot.py).
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from langchain_core.tools import tool

# Raíz del proyecto = carpeta padre de tools/. Las imágenes van al workspace.
ROOT = Path(__file__).resolve().parent.parent
DIAGRAMS_DIR = ROOT / "workspace" / "diagrams"


@tool
def generate_diagram(mermaid_code: str, title: str = "diagrama") -> str:
    """Genera un diagrama visual a partir de código Mermaid y lo envía como imagen.

    - mermaid_code: el diagrama en sintaxis Mermaid (flowchart, sequenceDiagram…).
    - title: título corto para el fichero/imagen.
    Úsalo para visualizar resultados: mapas de red (nmap), mapas de ataque SSH,
    árboles de procesos, etc. La imagen se manda automáticamente por Telegram.
    """
    import httpx

    code = (mermaid_code or "").strip()
    if not code:
        return "ERROR: no se proporcionó código Mermaid."

    kroki = os.environ.get("KROKI_URL", "http://localhost:8001").rstrip("/")
    try:
        r = httpx.post(f"{kroki}/mermaid/png", content=code.encode("utf-8"), timeout=20.0)
    except httpx.HTTPError as e:
        return (f"ERROR: no se pudo contactar con Kroki en {kroki} "
                f"({type(e).__name__}). ¿Está el contenedor levantado?")

    if r.status_code != 200:
        # Kroki devuelve el motivo (p. ej. sintaxis Mermaid inválida).
        return f"ERROR renderizando el diagrama (HTTP {r.status_code}): {r.text[:300]}"

    DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)[:40] or "diagrama"
    fname = f"{safe}_{int(time.time())}.png"
    fpath = DIAGRAMS_DIR / fname
    fpath.write_bytes(r.content)

    # El bot detecta el PNG nuevo por snapshot del directorio y lo envía solo.
    return f"Diagrama '{title}' generado y enviado como imagen por Telegram."
