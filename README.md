# Agente de IA para administración de sistemas, seguridad y pentesting

Agente de inteligencia artificial para la administración de sistemas, la seguridad
y el *pentesting* de una máquina Linux, operado en lenguaje natural a través de
Telegram. Orquesta varios modelos de lenguaje gratuitos —en la nube y en local—
mediante un **encaminamiento adaptativo** que selecciona el modelo de cada petición
según su naturaleza y la disponibilidad de los proveedores, manteniendo las
consultas sensibles **exclusivamente en local**.

Código del Trabajo Fin de Grado del Grado en Ingeniería Telemática (ETSE-UV).

- **Autor:** Manuel Perpiñá Martínez
- **Tutores:** Antonio S. · Juan G.
- **Universitat de València — Escola Tècnica Superior d'Enginyeria**, 2026

## Estructura del repositorio

```
Agente/          Código del agente (runtime)
  agent.py             Ensamblado: orquestador + 3 subagentes (Deep Agents)
  bot.py               Interfaz de Telegram (lista blanca, HITL, candado por chat)
  botutils.py          Utilidades + red de seguridad de privacidad
  AGENTS.md            Reglas del orquestador (prompt de sistema)
  router/              Modelos, perfiles y encaminamiento con fallback
  tools/               18 herramientas (sysadmin, seguridad, pentesting) + MCP
  skills/              Flujos reutilizables (auditoría de seguridad, triaje de IP)
  pyproject.toml       Dependencias del proyecto
  .env.example         Plantilla de configuración (sin secretos)
resultados_cap6/       Datos de la evaluación (Capítulo 6): pruebas T1–T9 sobre
  README.md            tres configuraciones de hardware, con sus figuras. Los
  figuras/             resúmenes (.md/.csv) y figuras son navegables; el dato
  nuvol-igpu-780m/     crudo por llamada (.jsonl) va en datos_crudos.zip.
  nuvol-cpu/  rtx5060ti/
  datos_crudos.zip
```

## Configuración

El agente se configura mediante variables de entorno. Copia la plantilla y
rellena tus propias claves:

```bash
cp Agente/.env.example Agente/.env
```

Las claves necesarias (Telegram, Google AI Studio, OpenRouter, VirusTotal) se
obtienen de forma gratuita en cada proveedor. El fichero `.env` con los secretos
reales **no** se incluye en este repositorio.

## Probar el agente

El bot funciona sobre mi propio despliegue, con una lista blanca de usuarios
autorizados. Si quieres probarlo por Telegram, escríbeme a
**permarma@alumni.uv.es** con tu id de usuario de Telegram, que necesito para
autorizarte. Para obtenerlo:

1. En Telegram, abre **@userinfobot** ([t.me/userinfobot](https://t.me/userinfobot)).
2. Pulsa **Iniciar**.
3. Te responderá con tus datos y tu id.

Cuando me lo envíes, te añado a la lista blanca y podrás escribirle al bot en
**@TFG_ETSE_bot**.

## Licencia

Distribuido bajo licencia MIT. Véase el fichero [LICENSE](LICENSE).
