"""
Utilidades compartidas por las herramientas.

Centraliza el patrón que la documentación de Deep Agents recomienda para
herramientas que tocan el sistema: ejecución con *timeout*, salida truncada
(para no inundar el contexto del modelo) y manejo limpio de errores.
"""
from __future__ import annotations

import shutil
import subprocess

# Tope de caracteres por salida de herramienta. Deep Agents además descarga a
# disco lo que pase de ~20k tokens, pero truncamos en origen por prudencia.
MAX_OUTPUT = 6000


def which(name: str) -> str | None:
    """Ruta del binario `name` si está instalado, o None."""
    return shutil.which(name)


def truncate(text: str, limit: int = MAX_OUTPUT) -> str:
    """Recorta `text` a `limit` caracteres añadiendo un aviso si se trunca."""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n…(salida truncada)"


def run(cmd: list[str], timeout: int = 15) -> tuple[str, int, str, str]:
    """Ejecuta `cmd` sin shell y devuelve (estado, returncode, stdout, stderr).

    estado ∈ {"ok", "notfound", "timeout", "error"}. Nunca lanza excepción: las
    herramientas deben degradar con un mensaje legible, no romperse.
    """
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return "ok", r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return "notfound", -1, "", ""
    except subprocess.TimeoutExpired:
        return "timeout", -1, "", ""
    except OSError as e:  # sin permiso de ejecución, formato inválido, FD agotados…
        return "error", -1, "", f"{type(e).__name__}: {e}"


def run_sudo(cmd: list[str], timeout: int = 15) -> tuple[str, int, str, str]:
    """Como `run`, pero con `sudo -n` (no interactivo: falla en vez de colgarse).

    Solo funcionará para los comandos permitidos en /etc/sudoers.d/agent
    (principio de menor privilegio). Si sudo pide contraseña, devuelve error.
    """
    return run(["sudo", "-n", *cmd], timeout=timeout)
