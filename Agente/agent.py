"""
Ensamblado del deep agent: orquestador + 3 subagentes especializados.

Se MONTA el agente. Se juntan el orquestador (que reparte
el trabajo), los 3 subagentes (sysadmin/security/pentesting) con sus herramientas,
las pausas de aprobación (HITL) y la "caja de archivos" (backend).

Sigue la documentación de Deep Agents:
  - `create_deep_agent(...)` con `subagents=[...]` (la tool `task` se inyecta
    sola para delegar).
  - `backend=CompositeBackend(...)` que enruta `/workspace/` y `/memories/` a
    `FilesystemBackend(virtual_mode=True)` (sandbox REAL: bloquea rutas
    absolutas y `..`), y el resto a `StateBackend` (efímero). Patrón recomendado
    por la doc de backends.
  - `interrupt_on={"nmap_scan": True}` → aprobación humana (HITL). Se configura
    DENTRO del subagente `pentesting-agent` (que es quien ejecuta `nmap_scan`),
    como muestra la doc de subagentes/HITL de Deep Agents — no a nivel del
    orquestador, que nunca llama a esa herramienta.
  - `system_prompt=AGENTS.md` → las reglas del orquestador van AL FRENTE del
    prompt (deepagents las antepone a su prompt base). Se pasa el texto del
    fichero, no `memory=[ruta]`: `memory` resuelve rutas contra el BACKEND, y con
    CompositeBackend(default=StateBackend) una ruta absoluta cae al backend de
    estado (vacío) y la memoria se descartaría en silencio. La memoria APRENDIDA
    (hechos entre conversaciones) la gestiona el agente escribiendo en /memories/.
  - `checkpointer=MemorySaver()` → historial por `thread_id` (en RAM).
  - Modelos: `model_for()` devuelve el FallbackChatModel adaptativo por perfil
    (router): el modelo se elige por el PERFIL del turno (no por quién llama) y
    cae al siguiente de la cadena si falla.

La construcción se hace mediante `build_agent()` (no a nivel de módulo) para no
exigir claves/proveedores al importar — útil para desarrollar fuera del mini-PC.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from dotenv import load_dotenv

load_dotenv()

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagents.middleware.filesystem import FilesystemPermission
from langgraph.checkpoint.memory import MemorySaver

from router import model_for
from tools import (
    ORCHESTRATOR_TOOLS,
    PENTESTING_TOOLS,
    SECURITY_TOOLS,
    SYSADMIN_TOOLS,
)

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT / "workspace"
MEMORIES = ROOT / "memories"
SKILLS = ROOT / "skills"
WORKSPACE.mkdir(exist_ok=True)
MEMORIES.mkdir(exist_ok=True)
SKILLS.mkdir(exist_ok=True)

# Acciones que requieren aprobación humana (ruidosas). Se aplica en el subagente
# que EJECUTA la herramienta (pentesting-agent), no a nivel global.
INTERRUPT_ON: dict[str, bool] = {"nmap_scan": True}

# Permisos de ficheros (defensa en profundidad). Los skills se cargan solos vía
# SkillsMiddleware (no por las tools de ficheros), así que denegar la ESCRITURA en
# /skills impide que un write_file/edit_file CORROMPA las definiciones de skills,
# sin afectar a su carga ni a su lectura. /workspace y /memories siguen escribibles;
# el resto cae al StateBackend efímero (no toca el disco real). Los subagentes
# heredan estas reglas. (FilesystemOperation = "read" | "write".)
FS_PERMISSIONS: list[FilesystemPermission] = [
    FilesystemPermission(operations=["write"], paths=["/skills/**"], mode="deny"),
]


def _backend() -> CompositeBackend:
    """Backend compuesto: estado efímero por defecto + disco sandboxeado.

    `virtual_mode=True` es OBLIGATORIO: sin él, rutas absolutas y `..` escapan
    del root_dir (la propia librería avisa de que "no aporta seguridad").
    """
    return CompositeBackend(
        default=StateBackend(),
        routes={
            "/workspace/": FilesystemBackend(root_dir=str(WORKSPACE), virtual_mode=True),
            "/memories/": FilesystemBackend(root_dir=str(MEMORIES), virtual_mode=True),
            "/skills/": FilesystemBackend(root_dir=str(SKILLS), virtual_mode=True),
        },
    )


def build_subagents(
    model_factory: Callable[[], Any] = model_for,
    mcp_tools: Optional[Sequence[Any]] = None,
) -> list[dict[str, Any]]:
    """Construye los 3 subagentes. `mcp_tools` (GTI: reputación/threat-intel) se suma a security."""
    security_tools = [*SECURITY_TOOLS, *(mcp_tools or [])]
    return [
        {
            "name": "sysadmin-agent",
            "description": (
                "Estado y mantenimiento del sistema local: CPU, RAM, disco (por "
                "montaje), procesos, contenedores Docker y servicios systemd. También "
                "puede reiniciar servicios y terminar procesos (con aprobación humana)."
            ),
            "system_prompt": (
                "Eres un administrador de sistemas. Para diagnosticar, LLAMA a la "
                "herramienta de lectura adecuada (system_stats, top_processes, "
                "docker_status, service_status) y responde breve y técnico a partir "
                "de su salida. NO uses herramientas de ficheros ni de shell "
                "(ls/glob/grep/read_file/execute) para esto.\n"
                "Puedes ACTUAR con restart_service (reiniciar un servicio) y "
                "kill_process (terminar un proceso), pero SOLO cuando el usuario lo "
                "pida claramente. Ambas muestran botones de aprobación ✅/❌ al "
                "llamarlas: LLÁMALAS DIRECTAMENTE; NUNCA pidas confirmación en texto "
                "('envía ✅ o escribe sí') — los botones SON la confirmación. "
                "Nunca inventes datos que no vengan de una herramienta."
            ),
            "tools": SYSADMIN_TOOLS,
            "model": model_factory(),
            # HITL: las dos acciones de escritura se pausan para pedir aprobación.
            "interrupt_on": {"restart_service": True, "kill_process": True},
        },
        {
            "name": "security-agent",
            "description": (
                "Defensa y auditoría: intentos de conexión SSH, fallos de "
                "autenticación, reglas del cortafuegos, puertos a la escucha y "
                "reputación de IPs/dominios (Google Threat Intelligence)."
            ),
            "system_prompt": (
                "Eres un analista de seguridad defensivo (solo lectura). Para "
                "auditar, LLAMA DIRECTAMENTE a tus herramientas (check_ssh_attempts, "
                "auth_failures_monitor, listening_ports, check_firewall_rules) y "
                "resume hallazgos accionables; si una IP "
                "parece atacante, destácala. Si dispones de herramientas de Google "
                "Threat Intelligence (MCP) —get_ip_address_report, get_domain_report— "
                "úsalas para comprobar si una IP o dominio es malicioso conocido. NO "
                "explores el sistema de ficheros ni uses shell (nada de "
                "ls/glob/grep/read_file/execute): tus herramientas ya traen los datos "
                "del sistema. Nunca ataques ni inventes resultados."
            ),
            "tools": security_tools,
            "model": model_factory(),
        },
        {
            "name": "pentesting-agent",
            "description": (
                "Reconocimiento de red (sin ataques activos): escaneo de puertos y "
                "versiones con nmap, búsqueda de CVEs, registros DNS, enumeración de "
                "subdominios e inspección de certificados TLS."
            ),
            "system_prompt": (
                "Eres un especialista en reconocimiento de red. El recon PASIVO está "
                "permitido y DEBES ejecutarlo SIN pedir permiso: dns_recon, "
                "subdomain_lookup, tls_inspect y cve_search usan la red con normalidad "
                "— LLÁMALAS siempre que se pidan y responde con el VALOR EXACTO que "
                "devuelvan.\n"
                "ENCADENA cuando tenga sentido: tras un nmap_scan (que detecta "
                "versiones, p. ej. 'OpenSSH 8.9'), usa cve_search con esa versión para "
                "buscar vulnerabilidades conocidas.\n"
                "PROHIBIDO responder con instrucciones para que el usuario lo averigüe "
                "por su cuenta o decir que 'no puedes obtenerlo': si te falta un dato, "
                "la respuesta correcta es LLAMAR a la herramienta, no excusarte.\n"
                "SOLO nmap_scan requiere aprobación humana: muestra botones ✅/❌ al "
                "llamarlo, así que LLÁMALO DIRECTAMENTE y NUNCA pidas confirmación en "
                "texto ('envía ✅ o escribe sí') — los botones SON la confirmación. "
                "Para escanear una RED o rango, hazlo en UNA sola llamada con el rango "
                "(p. ej. 192.168.1.0/24), NO una llamada por host. No uses "
                "herramientas de ficheros ni de shell (ls/glob/grep/read_file/execute). "
                "Nunca inventes resultados."
            ),
            "tools": PENTESTING_TOOLS,
            "model": model_factory(),
            # HITL: el escaneo nmap se pausa para pedir aprobación. Se declara
            # aquí porque es ESTE subagente quien ejecuta `nmap_scan`.
            "interrupt_on": INTERRUPT_ON,
        },
    ]


def build_agent(
    model_factory: Callable[[], Any] = model_for,
    mcp_tools: Optional[Sequence[Any]] = None,
):
    """Construye y devuelve el deep agent compilado (orquestador + subagentes)."""
    return create_deep_agent(
        model=model_factory(),
        tools=ORCHESTRATOR_TOOLS,
        system_prompt=(ROOT / "AGENTS.md").read_text(encoding="utf-8"),
        skills=["/skills/"],
        subagents=build_subagents(model_factory, mcp_tools),
        backend=_backend(),
        permissions=FS_PERMISSIONS,
        checkpointer=MemorySaver(),
        # El HITL (interrupt_on) va dentro del subagente pentesting-agent, que es
        # quien ejecuta nmap_scan (ver build_subagents).
    )


# ---------------------------------------------------------------------------
# Utilidad compartida con el bot: extraer el texto legible de la salida.
# ---------------------------------------------------------------------------
_HIDDEN_BLOCK_TYPES = {"thinking", "tool_use", "tool_result"}


def _is_visible_text_block(block: object) -> bool:
    if not isinstance(block, dict):
        return False
    if block.get("type") in _HIDDEN_BLOCK_TYPES:
        return False
    text = block.get("text")
    return isinstance(text, str) and bool(text)


def extract_text(out: dict) -> str:
    """Devuelve el texto legible del último mensaje del agente."""
    messages = out.get("messages") or []
    if not messages:
        return "(sin respuesta)"
    content = getattr(messages[-1], "content", messages[-1])
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [b["text"] for b in content if _is_visible_text_block(b)]
        return "\n".join(parts) or "(sin texto visible)"
    return str(content)


# ---------------------------------------------------------------------------
# CLI mínimo para probar sin Telegram:  python agent.py "estado del sistema"
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import asyncio
    import sys

    async def _cli() -> None:
        agent = build_agent()
        question = " ".join(sys.argv[1:]) or "Resume tus capacidades."
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": question}]},
            config={"configurable": {"thread_id": "cli"}},
        )
        print(extract_text(result))

    asyncio.run(_cli())
