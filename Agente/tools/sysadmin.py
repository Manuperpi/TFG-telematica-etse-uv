"""
Herramientas del subagente `sysadmin-agent` — estado y mantenimiento del sistema.

Todas son de solo lectura. La mayoría usan `psutil` (portable) o comandos de
solo consulta (`systemctl is-active`). No modifican nada.
"""
from __future__ import annotations

import time

import psutil
from langchain_core.tools import tool

from tools._common import run, truncate


@tool
def system_stats() -> str:
    """Estado actual del sistema: uptime, CPU (carga, uso %, temperatura), RAM y disco."""
    # --- Uptime (lo primero que se espera de "¿cómo va el servidor?") ---
    arriba = int(time.time() - psutil.boot_time())
    dias, resto = divmod(arriba, 86400)
    horas, minutos = divmod(resto // 60, 60)
    uptime_str = f"{dias}d {horas}h {minutos}m" if dias else f"{horas}h {minutos}m"

    # --- CPU ---
    try:
        l1, l5, l15 = psutil.getloadavg()
        load_str = f"{l1:.2f} / {l5:.2f} / {l15:.2f}"
    except (AttributeError, OSError):
        load_str = "N/A"  # Windows / VM sin loadavg
    cpu_pct = psutil.cpu_percent(interval=0.5)

    # --- Temperatura (puede no existir en VM/Windows) ---
    temp_str = "N/A"
    try:
        temps = psutil.sensors_temperatures()
        for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz"):
            if temps.get(key):
                values = [t.current for t in temps[key] if t.current is not None]
                if values:
                    temp_str = f"{max(values):.1f}°C"
                    break
    except (AttributeError, OSError):
        pass

    # --- RAM ---
    ram = psutil.virtual_memory()
    ram_str = f"{ram.used / 1e9:.1f} / {ram.total / 1e9:.1f} GB ({ram.percent:.0f}%)"

    # --- Disco: por cada punto de montaje (no solo la raíz) ---
    disk_lines = []
    for part in psutil.disk_partitions(all=False):
        try:
            u = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue
        disk_lines.append(f"- {part.mountpoint}: {u.used / 1e9:.1f} / {u.total / 1e9:.1f} GB ({u.percent:.0f}%)")
    disk_str = "\n".join(disk_lines) or "- (no disponible)"

    return (
        f"**Sistema**: encendido desde hace {uptime_str}\n\n"
        f"**CPU**\n"
        f"- Carga (1/5/15 min): {load_str}\n"
        f"- Uso actual: {cpu_pct:.0f}%\n"
        f"- Temperatura: {temp_str}\n\n"
        f"**RAM**: {ram_str}\n\n"
        f"**Disco (por montaje)**\n{disk_str}"
    )


@tool
def top_processes(n: int = 10, by: str = "cpu") -> str:
    """Lista los N procesos que más recursos consumen.

    - n: cuántos procesos mostrar (1-20, por defecto 10).
    - by: criterio de orden, "cpu" o "mem".
    """
    try:
        n = max(1, min(int(n), 20))
    except (TypeError, ValueError):
        n = 10
    by = by.lower().strip()
    if by not in ("cpu", "mem"):
        return f"ERROR: 'by' inválido: {by!r} (usa 'cpu' o 'mem')"

    # Primera pasada para "cebar" cpu_percent (psutil mide entre dos lecturas).
    for p in psutil.process_iter():
        try:
            p.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    psutil.cpu_percent(interval=0.5)

    procs = []
    for p in psutil.process_iter(["pid", "name", "username"]):
        try:
            cpu = p.cpu_percent(None)
            mem = p.memory_percent()
            procs.append((p.info["pid"], p.info["name"] or "?", cpu, mem))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    key = 2 if by == "cpu" else 3
    procs.sort(key=lambda x: x[key], reverse=True)

    lines = [f"Top {n} procesos por {'CPU' if by == 'cpu' else 'RAM'}:"]
    lines.append(f"{'PID':>7}  {'CPU%':>6}  {'MEM%':>6}  NOMBRE")
    for pid, name, cpu, mem in procs[:n]:
        lines.append(f"{pid:>7}  {cpu:>6.1f}  {mem:>6.1f}  {name}")
    return "\n".join(lines)


@tool
def docker_status() -> str:
    """Lista los contenedores Docker: en ejecución (CPU/memoria) Y parados/caídos."""
    estado, rc, out, err = run(
        ["docker", "stats", "--no-stream", "--format",
         "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"],
        timeout=20,
    )
    if estado == "notfound":
        return "ERROR: docker no está instalado o no está en el PATH."
    if estado == "timeout":
        return "ERROR: timeout consultando docker."
    if rc != 0:
        msg = err.strip() or "sin detalle"
        if "permission denied" in msg.lower():
            return "ERROR: sin permiso para el socket de Docker (¿usuario en el grupo 'docker'?)."
        return f"ERROR docker: {msg}"

    if not out.strip():
        lines = ["No hay contenedores en ejecución."]
    else:
        lines = ["Contenedores en ejecución:", f"{'NOMBRE':<24} {'CPU%':>7} {'MEM':>18} {'MEM%':>6}"]
        for row in out.strip().splitlines():
            parts = row.split("\t")
            if len(parts) == 4:
                name, cpu, mem, memp = parts
                lines.append(f"{name:<24} {cpu:>7} {mem:>18} {memp:>6}")

    # Contenedores PARADOS/caídos: `docker stats` solo ve los vivos, y la
    # pregunta de administración real es "¿hay algo caído?".
    estado, rc, out, _ = run(
        ["docker", "ps", "-a", "--filter", "status=exited",
         "--format", "{{.Names}}\t{{.Status}}"],
        timeout=10,
    )
    if estado == "ok" and rc == 0 and out.strip():
        lines.append("\n**Parados/caídos:**")
        for row in out.strip().splitlines():
            parts = row.split("\t")
            if len(parts) == 2:
                lines.append(f"- {parts[0]}: {parts[1]}")
    return truncate("\n".join(lines))


@tool
def service_status(service: str) -> str:
    """Comprueba si un servicio systemd se está EJECUTANDO ahora (activo/parado/fallido).

    - service: nombre del servicio (ej. "nginx", "docker", "ssh").
    """
    service = service.strip()
    # Validación: nombre de unidad systemd razonable (evita inyección).
    if not service or not all(c.isalnum() or c in "-_.@" for c in service):
        return f"ERROR: nombre de servicio inválido: {service!r}"

    def _estado(unit: str) -> tuple[str, str, str]:
        est, _, a_out, _ = run(["systemctl", "is-active", unit], timeout=10)
        if est == "notfound":
            return "__nosystemd__", "", ""
        if est == "timeout":
            return "__timeout__", "", ""
        _, _, e_out, _ = run(["systemctl", "is-enabled", unit], timeout=5)
        return unit, (a_out or "").strip() or "desconocido", (e_out or "").strip() or "desconocido"

    unit, active, enabled = _estado(service)
    if unit == "__nosystemd__":
        return "ERROR: systemctl no disponible (sistema sin systemd)."
    if unit == "__timeout__":
        return "ERROR: timeout consultando systemctl."

    # Algunos sistemas exponen ssh como 'ssh' y otros como 'sshd'. Si la unidad
    # pedida no corre, probamos su alias habitual antes de dar "parado": así no
    # decimos que SSH está caído solo porque el nombre de la unidad difiere.
    _ALIAS = {"ssh": "sshd", "sshd": "ssh"}
    if active != "active" and service in _ALIAS:
        _, a2, e2 = _estado(_ALIAS[service])
        if a2 == "active":
            active, enabled = a2, e2

    # PRIMERA LÍNEA = veredicto inequívoco en español: es lo que un modelo pequeño
    # va a copiar tal cual, así que aquí NO debe aparecer ninguna palabra ambigua
    # (nada de "disabled" suelto, que se confunde con "no funciona").
    if active == "active":
        verdict = f"El servicio '{service}' SÍ está activo: se está EJECUTANDO ahora mismo. ✅"
    elif active == "failed":
        verdict = f"El servicio '{service}' está FALLIDO (intentó arrancar y falló). ⚠️"
    elif active in ("activating", "deactivating"):
        verdict = f"El servicio '{service}' está cambiando de estado ({active}). ⏳"
    else:
        verdict = f"El servicio '{service}' NO está activo: está PARADO, no se ejecuta ahora. ⛔"

    # Arranque al boot, traducido y SEPARADO del estado actual (es otra cosa).
    arranque = {
        "enabled": "sí, se inicia solo al encender el equipo",
        "disabled": "no por sí solo (se arranca a mano o por socket)",
        "static": "solo cuando otra unidad lo necesita",
        "alias": "es un alias de otra unidad",
        "masked": "está bloqueado (masked)",
        "indirect": "depende de otra unidad",
    }.get(enabled, enabled)

    return (
        f"{verdict}\n"
        f"(Dato aparte, no confundir — arranque automático al encender: {arranque}. "
        f"Esto es independiente de si se está ejecutando ahora.)"
    )
