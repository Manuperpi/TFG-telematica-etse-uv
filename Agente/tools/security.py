"""
Herramientas del subagente `security-agent` — defensa y auditoría (solo lectura).

Leen logs y estado del sistema; no modifican nada ni atacan. `check_firewall_rules`
necesita root y se apoya en `sudo -n` acotado a comandos concretos (ver
/etc/sudoers.d/agent).
"""
from __future__ import annotations

import re
from collections import Counter

from langchain_core.tools import tool

from router import metrics
from tools._common import run, run_sudo, truncate, which

# --- Patrones del journal de sshd ---
_RE_ACCEPTED = re.compile(r"Accepted (?:password|publickey) for (\S+) from (\S+)")
_RE_FAILED = re.compile(r"Failed password for (?:invalid user )?\S+ from (\S+)")
_RE_INVALID = re.compile(r"Invalid user \S+ from (\S+)")


@tool
def check_ssh_attempts(hours: int = 24) -> str:
    """Resume los intentos de conexión SSH de las últimas N horas (1-168).

    Agrupa por IP y separa logins exitosos, fallos de contraseña e intentos
    con usuario inexistente. Útil para detectar fuerza bruta.
    """
    metrics.force_privacy()  # dato sensible (Tier-1) → pin local: el resultado no sale del equipo
    try:
        h = max(1, min(int(hours), 168))
    except (TypeError, ValueError):
        return f"ERROR: 'hours' inválido: {hours!r}"

    estado, rc, out, err = run(
        ["journalctl", "_COMM=sshd", "--since", f"{h} hours ago", "--no-pager"],
        timeout=15,
    )
    if estado == "notfound":
        return "ERROR: journalctl no disponible (sistema sin systemd)."
    if estado == "timeout":
        return "ERROR: timeout consultando journalctl."
    if rc != 0 and not out:
        return f"ERROR journalctl: {err.strip() or 'sin detalle'}"

    accepted: Counter[tuple[str, str]] = Counter()
    failed: Counter[str] = Counter()
    invalid: Counter[str] = Counter()
    for line in out.splitlines():
        if m := _RE_ACCEPTED.search(line):
            accepted[(m.group(1), m.group(2))] += 1
        elif m := _RE_FAILED.search(line):
            failed[m.group(1)] += 1
        elif m := _RE_INVALID.search(line):
            invalid[m.group(1)] += 1

    if not (accepted or failed or invalid):
        return f"Sin actividad SSH relevante en las últimas {h} horas."

    parts = [f"Actividad SSH — últimas {h} horas:"]
    if accepted:
        parts.append("\n**Logins exitosos:**")
        for (user, ip), n in accepted.most_common():
            parts.append(f"- {user}@{ip} ({n})")
    if failed:
        parts.append("\n**Fallos de contraseña (por IP):**")
        for ip, n in failed.most_common(10):
            parts.append(f"- {ip}: {n} intentos")
    if invalid:
        parts.append("\n**Usuario inexistente (por IP):**")
        for ip, n in invalid.most_common(10):
            parts.append(f"- {ip}: {n} intentos")
    return truncate("\n".join(parts))


@tool
def auth_failures_monitor(hours: int = 24) -> str:
    """Revisa fallos de autenticación y de sudo de las últimas N horas (1-168)."""
    metrics.force_privacy()  # dato sensible (Tier-1) → pin local: el resultado no sale del equipo
    try:
        h = max(1, min(int(hours), 168))
    except (TypeError, ValueError):
        return f"ERROR: 'hours' inválido: {hours!r}"

    estado, rc, out, err = run(
        ["journalctl", "--since", f"{h} hours ago", "--no-pager",
         "_COMM=sudo", "+", "SYSLOG_FACILITY=10"],  # facility 10 = authpriv
        timeout=15,
    )
    if estado == "notfound":
        return "ERROR: journalctl no disponible (sistema sin systemd)."
    if estado == "timeout":
        return "ERROR: timeout consultando journalctl."

    sudo_fail = Counter()
    auth_fail = Counter()
    for line in out.splitlines():
        low = line.lower()
        if "authentication failure" in low or "auth failure" in low:
            if m := re.search(r"user=(\S+)", line):
                auth_fail[m.group(1)] += 1
            else:
                auth_fail["(desconocido)"] += 1
        if "sudo" in low and ("incorrect password" in low or "authentication failure" in low or "NOT in sudoers" in line):
            # Usuario tras el prefijo 'sudo[pid]:' ('sudo: manu : ...'); si no, el
            # 'user=' del registro PAM. Anclar evita capturar la hora del timestamp.
            m = re.search(r"sudo(?:\[\d+\])?:\s+(\S+?)\s*:", line) or re.search(r"\buser=(\S+)", line)
            if m:
                sudo_fail[m.group(1)] += 1

    if not (sudo_fail or auth_fail):
        return f"Sin fallos de autenticación/sudo en las últimas {h} horas."

    parts = [f"Fallos de autenticación — últimas {h} horas:"]
    if sudo_fail:
        parts.append("\n**sudo fallido (por usuario):**")
        for u, n in sudo_fail.most_common(10):
            parts.append(f"- {u}: {n}")
    if auth_fail:
        parts.append("\n**Fallos de autenticación (por usuario):**")
        for u, n in auth_fail.most_common(10):
            parts.append(f"- {u}: {n}")
    return truncate("\n".join(parts))


@tool
def check_firewall_rules() -> str:
    """Muestra el estado y reglas del cortafuegos (prueba ufw, nftables, iptables)."""
    metrics.force_privacy()  # postura de seguridad (Tier-2) → pin local: no sale del equipo
    # 1) ufw (lo más habitual en Ubuntu). Requiere root.
    if which("ufw"):
        estado, rc, out, err = run_sudo(["ufw", "status", "verbose"], timeout=10)
        if estado == "ok" and rc == 0 and out.strip():
            return truncate("**ufw**\n" + out.strip())

    # 2) nftables (moderno).
    if which("nft"):
        estado, rc, out, err = run_sudo(["nft", "list", "ruleset"], timeout=10)
        if estado == "ok" and rc == 0 and out.strip():
            return truncate("**nftables**\n" + out.strip())

    # 3) iptables (clásico).
    if which("iptables"):
        estado, rc, out, err = run_sudo(["iptables", "-L", "-n", "-v"], timeout=10)
        if estado == "ok" and rc == 0:
            return truncate("**iptables**\n" + (out.strip() or "(sin reglas)"))

    return ("No se pudo leer el cortafuegos. ¿Sin ufw/nft/iptables, o sin "
            "permiso sudo para esos comandos? (ver /etc/sudoers.d/agent)")


@tool
def listening_ports() -> str:
    """Lista los puertos a la escucha (TCP/UDP) y el proceso que los abre.

    Es la visión INTERNA (complemento de nmap, que mira desde fuera).
    """
    metrics.force_privacy()  # postura de seguridad (Tier-2) → pin local: no sale del equipo
    if not which("ss"):
        return "ERROR: 'ss' no disponible (paquete iproute2, sistema no-Linux?)."
    estado, rc, out, err = run(["ss", "-tulpn"], timeout=10)
    if estado == "timeout":
        return "ERROR: timeout consultando ss."
    if rc != 0 and not out:
        return f"ERROR ss: {err.strip() or 'sin detalle'}"
    if not out.strip():
        return "No hay puertos a la escucha."
    return truncate("Puertos a la escucha (ss -tulpn):\n" + out.strip())
