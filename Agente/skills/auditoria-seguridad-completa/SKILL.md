---
name: auditoria-seguridad-completa
description: "Usar cuando el usuario pida una auditoría o revisión de seguridad completa del sistema (palabras como 'auditoría', 'revisión de seguridad', 'informe de seguridad'). Revisa SSH, autenticación, cortafuegos y puertos con el subagente de seguridad y responde con un informe breve."
---

# Auditoría de seguridad completa

Revisión de la **postura de seguridad** del mini-PC (SSH, autenticación, cortafuegos,
puertos). Solo lectura pasiva (nada de nmap). **Mantenla CORTA**: la ejecuta el
modelo LOCAL (privacidad) y se satura —devuelve vacío— si el turno tiene muchos pasos.

> **Privacidad (garantía):** lee datos sensibles (intentos SSH, fallos de auth/sudo,
> cortafuegos, puertos) → se ejecuta **100% en LOCAL** (perfil `privacidad`): nada de
> eso sale del equipo. Solo la reputación de IPs (Google Threat Intelligence) consulta
> Internet, como siempre.

## Pasos (POCOS a propósito — el modelo local se satura con turnos largos)

0. **Fija el perfil local:** `set_profile('privacidad')` y avisa en una línea
   ("auditoría en local; tus datos sensibles no salen del equipo").

1. **UNA sola delegación** a `security-agent` (NO una por herramienta): pídele que
   ejecute las cuatro comprobaciones —intentos SSH (`check_ssh_attempts`), fallos de
   auth/sudo (`auth_failures_monitor`), cortafuegos (`check_firewall_rules`) y puertos
   a la escucha (`listening_ports`)— y te devuelva un **resumen BREVE** de hallazgos
   accionables (sin volcados crudos).

2. **Responde TÚ con un informe CONCISO, en el propio mensaje** (texto, no fichero):
   - Resumen ejecutivo (2-4 líneas).
   - Hallazgos por área (SSH, autenticación, cortafuegos, puertos) en **bullets cortos**.
   - 3-5 recomendaciones priorizadas (alta/media/baja).

   **NO uses `write_file`, NO generes diagramas, NO uses `write_todos`.** Cada paso
   extra alarga el turno y el modelo local acaba devolviendo vacío. Cortito y al grano.

3. **Solo si** aparecen IPs atacantes claras: menciónalas y, si quieres su reputación,
   un `task` aparte (`get_ip_address_report`). Si son recurrentes, anótalas en
   `/memories/atacantes.md`.
