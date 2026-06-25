"""
Paquete `tools`: las herramientas del agente, agrupadas por subagente.

Cada subagente recibe SOLO su colección (principio de menor privilegio). El
orquestador recibe la tool transversal de diagramas.
"""
from tools.actions import kill_process, restart_service
from tools.delivery import adjuntar_fichero
from tools.diagrams import generate_diagram
from tools.routing import set_profile
from tools.pentesting import (
    cve_search,
    dns_recon,
    nmap_scan,
    subdomain_lookup,
    tls_inspect,
)
from tools.security import (
    auth_failures_monitor,
    check_firewall_rules,
    check_ssh_attempts,
    listening_ports,
)
from tools.sysadmin import (
    docker_status,
    service_status,
    system_stats,
    top_processes,
)

# Colecciones por subagente (lo que cada uno "ve").
# Sysadmin: 4 de lectura + 2 de ESCRITURA con aprobación humana (restart/kill).
SYSADMIN_TOOLS = [
    system_stats, top_processes, docker_status, service_status,   # lectura
    restart_service, kill_process,                               # escritura (con HITL)
]
# Seguridad: 4 locales (+ las del MCP de GTI, que se inyectan en agent.py).
SECURITY_TOOLS = [check_ssh_attempts, auth_failures_monitor,
                  check_firewall_rules, listening_ports]
# Pentesting/recon: escaneo con versiones, CVEs, DNS, subdominios y TLS.
PENTESTING_TOOLS = [nmap_scan, cve_search, dns_recon, subdomain_lookup, tls_inspect]

# Tools transversales del orquestador: diagramas + la decisión ADAPTATIVA del
# routing (set_profile) + entrega de informes como adjunto (adjuntar_fichero:
# manda el .md directo a Telegram sin releerlo, evita fugas — ver tools/delivery.py).
ORCHESTRATOR_TOOLS = [generate_diagram, set_profile, adjuntar_fichero]

__all__ = [
    "SYSADMIN_TOOLS", "SECURITY_TOOLS", "PENTESTING_TOOLS", "ORCHESTRATOR_TOOLS",
    "generate_diagram", "set_profile", "adjuntar_fichero",
]
