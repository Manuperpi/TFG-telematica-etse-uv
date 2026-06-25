---
name: triage-ip-sospechosa
description: "Usar cuando el usuario dé una dirección IP concreta y quiera valorar si es peligrosa o quién es (p. ej. '¿es peligrosa esta IP?', '¿debería bloquear X.X.X.X?'). Reúne la evidencia local sobre esa IP y emite un veredicto."
---

# Triage de una IP sospechosa

Flujo para valorar una IP concreta combinando la evidencia local y la
inteligencia de amenazas externa (Google Threat Intelligence vía MCP, si está activa).

## Pasos

0. **Fija `privacidad`** con `set_profile('privacidad')` al empezar: este triage lee
   datos sensibles locales (intentos SSH y fallos de auth de esa IP), así que se
   procesa en el modelo **local** y no sale del equipo. (La reputación vía GTI sí
   consulta Internet —es su naturaleza—, pero tu actividad local se queda aquí.)

1. Con `security-agent`, busca la IP en la actividad reciente:
   - intentos SSH (`check_ssh_attempts`): cuántos, contra qué usuarios, éxito/fallo,
   - fallos de autenticación (`auth_failures_monitor`).
2. Con `security-agent`, si está disponible Google Threat Intelligence (MCP),
   consulta la reputación de esa IP (`get_ip_address_report`) y sus relaciones.
3. Valora el patrón:
   - muchos intentos fallidos contra varios usuarios → fuerza bruta,
   - reputación maliciosa alta en GTI/VirusTotal → atacante conocido.
4. Emite un **veredicto claro**: benigna / sospechosa / maliciosa, citando la
   evidencia concreta.
5. Da una **recomendación** accionable (vigilar / bloquear en el cortafuegos) y,
   si procede, cómo bloquearla (sin ejecutarlo tú: solo lectura).
6. Si es maliciosa y recurrente, anótala en `/memories/atacantes.md` con la
   fecha y el motivo, para reconocerla en el futuro.
