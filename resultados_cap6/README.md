# Resultados de la evaluación (Capítulo 6)

Datos de la campaña de evaluación del agente. Es una **única pasada** (resultados
preliminares, sin repetición estadística); el **hardware sí** se compara en tres
configuraciones distintas.

## Configuraciones de hardware

| Carpeta | Equipo | Tests |
|---|---|---|
| [`nuvol-igpu-780m/`](nuvol-igpu-780m) | Mini-PC con iGPU AMD Radeon 780M — **máquina objetivo** | **T1–T9** |
| [`nuvol-cpu/`](nuvol-cpu) | El mismo mini-PC, solo CPU | T1, T6, T7 |
| [`rtx5060ti/`](rtx5060ti) | GPU dedicada NVIDIA 5060 Ti 16 GB | T1, T6, T7 |

Ollama corre en Docker (ROCm) sobre el mini-PC. Banco de preguntas `2026-06-21.1`
(T2 y T5: re-run `2026-06-22.1`, ver más abajo).

## Organización

- Cada carpeta de máquina contiene los **resúmenes** de sus tests
  (`*_summary.md`, `*.csv`), su `SUMMARY.md` y su `RUN_METADATA.json` (hardware,
  versiones de Ollama y modelos, entorno).
- [`figuras/`](figuras) — las figuras del Capítulo 6 en PDF (para LaTeX) y PNG.
- **`datos_crudos.zip`** — el dato bruto por llamada (`*.jsonl`) de todos los
  tests, con la misma estructura de carpetas. Descomprímelo para recomputar las
  cifras desde el crudo.

## Tests, datos y figuras

| Test | Qué mide | Datos clave | Figura |
|---|---|---|---|
| **T1** | Acierto de *tool-call* y velocidad por modelo | `T1_banco/banco_summary.csv` | `fig_t1_banco` |
| **T2** | Calidad de respuesta, local vs nube (juez LLM) | `T2_calidad/t2_scores.md`, `t2_scores_perfil.csv` | `fig_t2_local_vs_nube`, `fig_t2_perfil` |
| **T3** | Garantía de privacidad (0 fugas) | `T3_privacidad/t3_summary.md` | `fig_t3_privacidad` |
| **T4** | *Fallback* / resiliencia del router (4/4) | `T4_fallback/t4_summary.md` | `fig_t4_fallback` |
| **T5** | Latencia de turno por perfil | `T5_perfiles/perfiles_summary.csv` | `fig_t5_perfiles` |
| **T6** | Contexto máximo, *prefill* y pilotaje del agente (×3 hw) | `<hw>/T6_hardware/t6_summary.*` | `fig_t6_contexto`, `fig_t6_prefill`, `fig_hw_velocidad` |
| **T7** | Concurrencia / teoría de colas M/M/1 (×3 hw) | `<hw>/T7_colas/*.csv` | `fig_t7_colas` |
| **T8** | Seguridad empírica: contención de inyección y abuso (6/6) | `T8_inyeccion/t8_summary.md` | `fig_t8_inyeccion` |
| **T9** | Coste-sombra (volumen de *tokens*) | `T9_anunciado_vs_real/*.csv` | `fig_t9_coste` |

## Notas

- **T2 y T5** corresponden al **re-run del 22 de junio** (banco `2026-06-22.1`):
  sus cifras son **idénticas** a las de la primera pasada y a las del TFG, de modo
  que la confirman.
- **`functiongemma:270m`** figura en algunos CSV y en los crudos como medida
  histórica, pero está **excluido de las figuras y del TFG** (modelo juguete de
  270M de parámetros, ~7 % de acierto). Banco efectivo: 15 modelos; locales
  viables: 6.
- **T2 · prompts de CVE**: poco fiables (la salida de referencia llegó vacía), así
  que las cifras del TFG se reportan sobre los 5 *prompts* fiables (auth,
  cortafuegos, puertos, intentos SSH y estado del sistema).
- **T9 · precios**: provisionales (*placeholder*); la figura muestra el **volumen
  de *tokens*** (real), no el coste en euros definitivo.
