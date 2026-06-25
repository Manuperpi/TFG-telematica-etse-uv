# T7 — Concurrencia / colas

- **S local** (mediana) = 27.5996097009629s → μ_local = 0.0362 turnos/s (M/M/1, NUM_PARALLEL=1)
- (pasada solo-local: nube no medida)
- Nube: el límite NO es la cola sino la CUOTA (Gemma 15 RPM; OpenRouter 1000/día).
- `mm1_local.csv`: curva W(λ). `predicho_vs_medido.csv`: ráfagas reales vs K·S.

Caveat: el bot serializa por chat (lock) y va en paralelo entre chats;
las ráfagas modelan chats distintos concurrentes.