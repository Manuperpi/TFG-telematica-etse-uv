"""
Helpers puros del bot (sin aiogram) — así son testeables sin Telegram.

Incluye: parseo de whitelist, troceo de mensajes, formato del pie de métricas,
descripción de acciones para la aprobación humana, y detección de diagramas
nuevos generados durante un turno.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

TELEGRAM_MAX_CHARS = 4000  # margen bajo el límite real de 4096

# ---------------------------------------------------------------------------
# Red de seguridad de PRIVACIDAD (el suelo determinista de la garantía).
# El perfil lo elige el ORQUESTADOR (tool set_profile), pero la garantía de
# privacidad no puede depender de que el LLM "se acuerde": si el mensaje
# contiene alguna de estas palabras EXACTAS, el turno arranca FIJADO en
# privacidad ANTES de llamar a ningún modelo (ni la pregunta sale del equipo).
# Lista corta e inequívoca a propósito; el juicio fino lo pone el LLM.
# ---------------------------------------------------------------------------
PRIVACY_WORDS: frozenset[str] = frozenset({
    # DECISIÓN (2026-06-18, REEXPANDIDA a Tier 1 + Tier 2 al habilitar la iGPU):
    # cubre accesos/credenciales (Tier 1) Y configuración de seguridad (Tier 2:
    # firewall, puertos). Antes (opción B) Tier 2 se dejó fuera porque el local en
    # CPU era lento/inestable; con Ollama en la iGPU (override gfx1102) el camino
    # local es estable y usable (test: 12/12, 0 crashes, ~20-166s), así que ya no
    # compensa dejar firewall/puertos saliendo a la nube. Sigue siendo una garantía
    # DETERMINISTA (fija el perfil ANTES de llamar a ningún LLM). Ver [[tfg-privacidad-tier1]].
    # Tier 1 — quién accede y cómo:
    "ssh", "sshd", "log", "logs", "login", "journalctl", "sudo", "sudoers",
    "contraseña", "contraseñas", "password", "passwords",
    "credencial", "credenciales", "fail2ban", "suid",
    # Tier 2 — configuración/postura de seguridad:
    "firewall", "cortafuegos", "ufw", "iptables", "nft",
})

# FRASES (no palabras sueltas) que también fijan privacidad: cubren los PUERTOS A
# LA ESCUCHA (superficie interna, sensible) SIN pillar "escanea los puertos de X"
# (nmap a un objetivo externo, que no es privado): por eso miramos "a la escucha"/
# "listening", no la palabra "puerto" a secas.
PRIVACY_PHRASES: tuple[str, ...] = ("a la escucha", "listening port")


def needs_privacy(text: str) -> bool:
    """¿El mensaje fuerza el perfil privacidad (palabra o frase sensible)?

    Compara PALABRAS COMPLETAS (trocea por caracteres no alfanuméricos, así
    "tecnología" no dispara por "log") y además algunas FRASES (para distinguir
    "puertos a la escucha" —interno, sensible— de "escanea los puertos" —nmap—).
    """
    limpio = " ".join("".join(c if c.isalnum() else " " for c in (text or "").lower()).split())
    if not PRIVACY_WORDS.isdisjoint(limpio.split()):
        return True
    return any(frase in limpio for frase in PRIVACY_PHRASES)


def parse_whitelist(raw: str) -> set[int]:
    """CSV de user_ids → set de enteros. Vacío/ inválido → set vacío (seguro)."""
    return {
        int(x) for x in (raw or "").split(",") if x.strip().lstrip("-").isdigit()
    }


def split_for_telegram(text: str, limit: int = TELEGRAM_MAX_CHARS) -> list[str]:
    """Trocea `text` en mensajes que entren en Telegram.

    Corta preferentemente por saltos de línea (para no partir tablas ni
    bloques de markdown a la mitad). Si una línea es más larga que `limit`,
    la corta a las bravas.
    """
    if not text:
        return ["(vacío)"]
    chunks: list[str] = []
    remaining = text
    while len(remaining) > limit:
        cut = remaining.rfind("\n", 0, limit)
        if cut <= 0:
            cut = limit  # ninguna línea cabe → corte duro
        chunks.append(remaining[:cut])
        remaining = remaining[cut:].lstrip("\n")
    if remaining:
        chunks.append(remaining)
    return chunks


def _short_model(spec: str) -> str:
    """'google_genai:gemma-4-31b-it' → 'gemma-4-31b-it'."""
    return spec.split(":", 1)[-1]


def format_footer(llm: list[dict[str, Any]], tools: list[dict[str, Any]],
                  verbose: bool = False) -> str:
    """Construye el pie de métricas de una respuesta.

    Lee los registros EN MEMORIA del turno (router.metrics.llm_calls() y
    tool_calls()):
        llm   = [{"model","provider","profile","is_fallback","total_tokens",
                  "completion_tokens","latency_ms","error"}]
        tools = [{"tool","duration_ms","ok"}]
    """
    if not llm and not tools:
        return ""

    total_tok = sum(r.get("total_tokens", 0) for r in llm)
    comp_tok = sum(r.get("completion_tokens", 0) for r in llm)
    lat_ms = sum(r.get("latency_ms", 0) for r in llm)
    toks_s = comp_tok / (lat_ms / 1000.0) if lat_ms and comp_tok else 0.0
    any_fb = any(r.get("is_fallback") for r in llm)
    n_err = sum(1 for r in llm if r.get("error"))

    models = sorted({_short_model(r["model"]) for r in llm if not r.get("error")})
    tool_names = sorted({t["tool"] for t in tools})
    profiles = sorted({r["profile"] for r in llm if r.get("profile")})

    if not verbose:
        bits = []
        if profiles:
            bits.append("🎯 " + "/".join(profiles))
        if models:
            bits.append("🧠 " + ", ".join(models))
        if tool_names:
            bits.append("🔧 " + ", ".join(tool_names))
        bits.append(f"📊 {total_tok} tk")
        if toks_s:
            bits.append(f"⚡ {toks_s:.0f} tk/s")
        bits.append(f"⏱️ {lat_ms / 1000:.1f} s")
        if any_fb:
            bits.append("⚠️ fallback")
        return "———\n" + " · ".join(bits)

    # Modo detallado
    lines = ["———"]
    if profiles:
        lines.append("🎯 Perfil: " + "/".join(profiles))
    if tool_names:
        lines.append("🔧 Tools: " + ", ".join(
            f"{t['tool']} ({t['duration_ms'] / 1000:.1f}s{'' if t['ok'] else ' ✗'})"
            for t in tools
        ))
    lines.append("🧠 Llamadas LLM:")
    for r in llm:
        ctok, lat = r.get("completion_tokens", 0), r.get("latency_ms", 0)
        tps = ctok / (lat / 1000.0) if lat and ctok else 0.0
        estado = (f"ERROR {r['error']}" if r.get("error")
                  else f"{r.get('total_tokens', 0)} tk · {tps:.0f} tk/s · {lat / 1000:.1f}s")
        marca = " ⚠️fallback" if r.get("is_fallback") else ""
        lines.append(f"  · {_short_model(r['model'])} ({r['provider']}){marca}: {estado}")
    lines.append(f"📊 Total: {total_tok} tk · {len(llm)} llamadas · {len(tools)} tools"
                 + (f" · {n_err} errores" if n_err else ""))
    return "\n".join(lines)


def describe_actions(action_requests: Iterable[dict[str, Any]]) -> str:
    """Texto para pedir aprobación humana de una o varias acciones."""
    parts = ["⏸️ El agente quiere ejecutar una acción que requiere tu aprobación:"]
    for a in action_requests:
        name = a.get("name", "?")
        args = a.get("args", {})
        args_str = ", ".join(f"{k}={v!r}" for k, v in args.items()) or "(sin argumentos)"
        parts.append(f"\n• **{name}**\n  {args_str}")
    return "\n".join(parts)


def find_new_files(directory: str | Path, known: set[str]) -> list[str]:
    """Ficheros en `directory` cuyo path no estaba en `known` (diagramas nuevos)."""
    d = Path(directory)
    if not d.is_dir():
        return []
    return sorted(str(p) for p in d.glob("*.png") if str(p) not in known)


def snapshot_files(directory: str | Path) -> set[str]:
    """Conjunto de PNGs presentes ahora (para comparar tras el turno)."""
    d = Path(directory)
    if not d.is_dir():
        return set()
    return {str(p) for p in d.glob("*.png")}
