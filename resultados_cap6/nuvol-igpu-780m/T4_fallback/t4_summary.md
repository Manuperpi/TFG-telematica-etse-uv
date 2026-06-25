# T4 — Fallback / resiliencia

- ✅ **preferido_falla** — gemma-4-31b-it error → gemma-4-26b-a4b-it (fallback)
- ✅ **preferido_vacio** — gemma-4-31b-it vacío → gemma-4-26b-a4b-it
- ✅ **toda_nube_cae_local** — nube ✗ → local (ollama) cierra
- ✅ **privacidad_sin_local_se_niega** — Ollama caído → RuntimeError, 0 nube

**4/4 casos correctos.**