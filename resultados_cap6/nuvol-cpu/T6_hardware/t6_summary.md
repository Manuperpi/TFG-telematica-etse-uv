# T6 (v3) — Hardware: nuvol-cpu

Barrido robusto: prefill ~50% del ctx (en tokens, sin overflow), 1 reintento, sin cascada de reinicios; piloto medido en estado limpio.

- **gemma4:e4b**: máx ctx estable=131072, prefill=35.1s/4034 tk, pilota=None (Nones)
- **qwen3.5:4b**: máx ctx estable=131072, prefill=39.9s/4483 tk, pilota=None (Nones)
- **nemotron-3-nano:4b**: máx ctx estable=131072, prefill=44.6s/4708 tk, pilota=None (Nones)
- **ministral-3:8b**: máx ctx estable=65536, prefill=81.9s/4697 tk, pilota=None (Nones)
- **granite4.1:3b**: máx ctx estable=65536, prefill=38.4s/4480 tk, pilota=None (Nones)
- **qwen3.5:9b**: máx ctx estable=131072, prefill=67.9s/4483 tk, pilota=None (Nones)
- **functiongemma:270m**: máx ctx estable=131072, prefill=2.1s/4036 tk, pilota=None (Nones)