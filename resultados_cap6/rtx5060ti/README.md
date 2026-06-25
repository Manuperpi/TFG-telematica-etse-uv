# rtx5060ti — comparación con GPU dedicada

GPU dedicada **NVIDIA 5060 Ti 16 GB** (VRAM GDDR propia), el "siguiente paso" de
*hardware* que anticipa el diseño. Solo los tests de comparación: **T1, T6, T7**.

- `T1_banco/` — banco de modelos.
- `T6_hardware/` — los seis modelos locales alcanzan los 128k de contexto y
  cuatro de seis pilotan el agente completo; el *prefill* a 128k baja a ~20 s
  (frente a ~135 s en la iGPU).
- `T7_colas/` — concurrencia: tiempo de servicio S≈7 s, unas tres veces más rápido
  que la iGPU.

Datos crudos por llamada: `../datos_crudos.zip`.
