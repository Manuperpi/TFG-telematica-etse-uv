# T6 (v3) — Hardware: rtx5060ti

Barrido robusto: prefill ~50% del ctx (en tokens, sin overflow), 1 reintento, sin cascada de reinicios; piloto medido en estado limpio.

- **gemma4:e4b**: máx ctx estable=131072, prefill=1.3s/4034 tk, pilota=True (27.4s)
- **qwen3.5:4b**: máx ctx estable=131072, prefill=1.4s/4483 tk, pilota=False (16.7s)
- **nemotron-3-nano:4b**: máx ctx estable=131072, prefill=1.5s/4708 tk, pilota=False (18.1s)
- **ministral-3:8b**: máx ctx estable=131072, prefill=1.9s/4697 tk, pilota=True (38.2s)
- **granite4.1:3b**: máx ctx estable=131072, prefill=0.9s/4480 tk, pilota=True (24.2s)
- **qwen3.5:9b**: máx ctx estable=131072, prefill=2.0s/4483 tk, pilota=True (61.0s)
- **functiongemma:270m**: máx ctx estable=131072, prefill=0.5s/4036 tk, pilota=False (0.8s)