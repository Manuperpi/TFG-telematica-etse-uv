"""
Herramienta del orquestador — ENTREGA de ficheros por Telegram SIN re-leerlos.

El orquestador genera un informe y lo guarda con `write_file` en `/workspace/`.
Para ENTREGARLO, en vez de leerlo con `read_file` y re-emitirlo por el LLM (lo que
mandaría su contenido —posiblemente sensible— al modelo del turno, que puede ser
de NUBE), llama a `adjuntar_fichero`: el bot lo envía como DOCUMENTO directo del
disco a Telegram, sin que ningún LLM lo vuelva a leer. Así un informe redactado en
local (perfil privacidad) se entrega sin fuga, con el contenido EXACTO y más rápido.

Mecánica: la tool valida que la ruta esté dentro de `/workspace/` (no se puede
escapar con `..`) y exista, y encola la ruta real en el registro del turno
(`router.metrics`); el bot, al terminar el turno, manda los ficheros encolados.
"""
from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool

from router import metrics

# Raíz del proyecto = carpeta padre de tools/. Los informes viven en /workspace.
ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = ROOT / "workspace"


@tool
def adjuntar_fichero(ruta: str) -> str:
    """Envía un fichero de /workspace/ como documento adjunto por Telegram.

    Úsalo para ENTREGAR un informe ya guardado (p. ej.
    '/workspace/informe_completo.md'): NO hace falta leerlo con read_file ni copiar
    su contenido en el mensaje — el fichero se manda tal cual, directo a Telegram.
    Esto es además lo CORRECTO por privacidad: releer el informe lo pasaría por el
    modelo del turno (puede ser de nube) y filtraría datos sensibles. Pásale la
    ruta del fichero dentro de /workspace/.
    """
    r = (ruta or "").strip()
    if not r:
        return "ERROR: no se indicó la ruta del fichero a adjuntar."
    # Normaliza la ruta virtual del agente (/workspace/x, workspace/x o x) a relativa.
    rel = r.replace("\\", "/").lstrip("/")
    if rel.startswith("workspace/"):
        rel = rel[len("workspace/"):]
    # Resuelve contra /workspace e impide escapar con '..' (defensa en profundidad).
    try:
        real = (WORKSPACE / rel).resolve()
        real.relative_to(WORKSPACE.resolve())
    except (ValueError, OSError):
        return f"ERROR: la ruta {ruta!r} queda fuera de /workspace o es inválida."
    if not real.is_file():
        return (f"ERROR: no existe el fichero {ruta!r} en /workspace. "
                "Genéralo primero con write_file.")
    metrics.queue_file(str(real))
    return (f"Fichero '{real.name}' encolado: se envía como documento adjunto por "
            "Telegram (sin releerlo). No copies su contenido en el mensaje.")
