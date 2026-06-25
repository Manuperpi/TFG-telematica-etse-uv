# T6 (v3) — Hardware: nuvol-igpu-780m

Barrido robusto: prefill ~50% del ctx (en tokens, sin overflow), 1 reintento, sin cascada de reinicios; piloto medido en estado limpio.

- **gemma4:e4b**: máx ctx estable=131072, prefill=Nones/0 tk, pilota=False (44.5s, ResponseError)
- **qwen3.5:4b**: máx ctx estable=65536, prefill=9.5s/4483 tk, pilota=False (27.7s, ResponseError)
- **nemotron-3-nano:4b**: máx ctx estable=32768, prefill=9.5s/4708 tk, pilota=False (73.3s)
- **ministral-3:8b**: máx ctx estable=16384, prefill=14.0s/4697 tk, pilota=False (0.7s, ResponseError)
- **granite4.1:3b**: máx ctx estable=32768, prefill=7.7s/4480 tk, pilota=False (300.2s, TimeoutError)
- **qwen3.5:9b**: máx ctx estable=16384, prefill=Nones/0 tk, pilota=False (0.8s, ResponseError)
- **functiongemma:270m**: máx ctx estable=131072, prefill=1.0s/4036 tk, pilota=False (2.4s)