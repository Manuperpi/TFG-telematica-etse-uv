# T2 — Calidad (calculado de judgments.jsonl)

Ítems juzgados: 32 · pares local-vs-nube: 10

## Por ruta

| ruta | n | acierto % | calidad media (1-5) |
|---|---|---|---|
| local | 10 | 90.0 | 4.0 |
| nube | 22 | 95.5 | 4.56 |

## Por perfil

| perfil | ruta | n | acierto % | calidad |
|---|---|---|---|---|
| equilibrio | nube | 11 | 100.0 | 4.76 |
| potencia | nube | 6 | 83.3 | 3.89 |
| privacidad | local | 10 | 90.0 | 4.0 |
| velocidad | nube | 5 | 100.0 | 4.93 |

## Local (privacidad/e4b) vs nube (equilibrio/Gemma) — la pregunta de investigación
- **Win-rate local** (calidad local ≥ equilibrio en la misma tarea): **30.0%** sobre 10 tareas sensibles.
- **Delta media de calidad (equilibrio − local): 0.83** puntos (1-5) = lo que la mejor nube AÑADE sobre el local. Pequeña/negativa ⇒ el local es competitivo (coste de privacidad bajo); grande ⇒ el tradeoff cuesta calidad.

Detalle por tarea en `t2_local_vs_nube.csv`.