# nuvol-cpu — comparación en CPU

El **mismo mini-PC** que `nuvol-igpu-780m`, pero forzando la inferencia en **CPU**
(sin usar la iGPU). Sirve para aislar qué parte del techo local lo pone el
*hardware*. Solo los tests de comparación: **T1, T6, T7**.

- `T1_banco/` — banco de modelos (acierto y velocidad en CPU).
- `T6_hardware/` — contexto, *prefill* y velocidad. El *prefill* a 128k en `e4b`
  llega a ~610 s (diez minutos solo para leer la entrada).
- `T7_colas/` — concurrencia.

Datos crudos por llamada: `../datos_crudos.zip`.
