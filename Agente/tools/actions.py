"""
Acciones de ESCRITURA del agente — administración real, con aprobación humana.

A diferencia del resto de herramientas (solo lectura), estas MODIFICAN el
estado del sistema. Por eso:
  - Se ejecutan SOLO tras aprobación humana (HITL): el agente declara estas
    tools en `interrupt_on` del sysadmin-agent (ver agent.py), así Deep Agents
    pausa y el bot pregunta antes de ejecutarlas.
  - Están acotadas: `restart_service` solo admite servicios de una lista blanca
    (config.RESTART_WHITELIST) y `kill_process` rechaza PIDs de sistema.
  - Usan `sudo -n` con comandos concretos permitidos en /etc/sudoers.d/agent
    (principio de menor privilegio).

Es la combinación HITL + lista blanca + sudoers acotado lo que hace que dar
capacidad de actuar al agente sea razonablemente seguro.
"""
from __future__ import annotations

import os

import psutil
from langchain_core.tools import tool

from router import config
from tools._common import run, run_sudo


@tool
def restart_service(service: str) -> str:
    """Reinicia un servicio systemd. REQUIERE APROBACIÓN HUMANA.

    Solo se permiten servicios de la lista blanca configurada (en este equipo,
    solo `cron`). Cualquier otro se rechaza, aunque se pida explícitamente.

    - service: nombre del servicio (ej. "nginx").
    """
    service = service.strip()
    if service not in config.RESTART_WHITELIST:
        return (f"ERROR: '{service}' no está en la lista blanca de servicios "
                f"reiniciables: {sorted(config.RESTART_WHITELIST)}.")
    estado, rc, out, err = run_sudo(["systemctl", "restart", service], timeout=30)
    if estado == "notfound":
        return "ERROR: systemctl no disponible."
    if estado == "timeout":
        return f"ERROR: timeout al reiniciar {service}."
    if rc != 0:
        return (f"ERROR al reiniciar {service}: {err.strip() or 'sin detalle'} "
                f"(¿falta el permiso en /etc/sudoers.d/agent?).")
    # Comprobamos cómo quedó el servicio tras el reinicio.
    _, _, activo, _ = run(["systemctl", "is-active", service], timeout=10)
    return f"✅ Servicio '{service}' reiniciado. Estado actual: {activo.strip() or 'desconocido'}."


@tool
def kill_process(pid: int) -> str:
    """Termina un proceso por su PID. REQUIERE APROBACIÓN HUMANA.

    Rechaza los PIDs de sistema (1 y los menores que config.KILL_MIN_PID) para
    evitar tumbar procesos críticos por accidente.

    - pid: identificador numérico del proceso (lo da, p. ej., top_processes).
    """
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return f"ERROR: PID no válido: {pid!r}"
    if pid < config.KILL_MIN_PID:
        return (f"ERROR: el PID {pid} es de sistema (< {config.KILL_MIN_PID}); "
                "no se permite terminarlo.")
    # El agente no puede terminarse a sí mismo (ni a su proceso padre).
    if pid in (os.getpid(), os.getppid()):
        return f"ERROR: el PID {pid} pertenece al propio agente; no se permite."
    # Recuperamos el nombre del proceso (para confirmar al usuario qué se mata).
    try:
        nombre = psutil.Process(pid).name()
    except psutil.NoSuchProcess:
        return f"No existe ningún proceso con PID {pid}."
    except psutil.Error:
        nombre = "?"
    # Lista negra: procesos críticos que te dejarían fuera (sshd, tailscaled) o
    # tumbarían el host (systemd*, dockerd, containerd). El sudoers no puede filtrar
    # `kill` por PID, así que el muro va aquí, en la app.
    if nombre in config.KILL_PROTECTED_NAMES or nombre.startswith("systemd"):
        return (f"ERROR: '{nombre}' (PID {pid}) es un proceso CRÍTICO protegido "
                f"(matarlo te dejaría sin acceso o tumbaría el sistema); no se permite.")
    estado, rc, out, err = run_sudo(["kill", str(pid)], timeout=10)
    if estado == "notfound":
        return "ERROR: el comando 'kill' no está disponible."
    if rc != 0:
        return (f"ERROR al terminar el proceso {pid} ({nombre}): "
                f"{err.strip() or 'sin permiso'}.")
    return f"✅ Señal de terminación enviada al proceso {pid} ({nombre})."
