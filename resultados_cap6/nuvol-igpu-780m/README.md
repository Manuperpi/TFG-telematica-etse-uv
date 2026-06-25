# nuvol-igpu-780m — máquina objetivo

Mini-PC con iGPU **AMD Radeon 780M** (memoria compartida DDR5), Ollama en
Docker/ROCm. Es el equipo sobre el que se desplegó el agente y se ejecutó la
campaña **completa (T1–T9)**.

- `T1_banco/` — banco de modelos: acierto de *tool-call*, latencia y velocidad.
- `T2_calidad/` — calidad de respuesta local vs nube (juez LLM). *Del re-run del 22-jun.*
- `T3_privacidad/` — garantía de privacidad: 0 fugas, red determinista 1,0/1,0.
- `T4_fallback/` — resiliencia del router ante los cuatro modos de fallo (4/4).
- `T5_perfiles/` — latencia de turno por perfil. *Del re-run del 22-jun.*
- `T6_hardware/` — contexto máximo estable, coste de *prefill* y pilotaje del agente.
- `T7_colas/` — concurrencia del camino local (modelo M/M/1).
- `T8_inyeccion/` — contención de inyección indirecta y abuso (6/6).
- `T9_anunciado_vs_real/` — coste-sombra y anunciado frente a medido.

Datos crudos por llamada: `../datos_crudos.zip`. Entorno y versiones: `RUN_METADATA.json`.
