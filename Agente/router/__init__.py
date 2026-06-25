"""
Paquete `router`: el pilar del TFG — enrutamiento adaptativo de modelos por perfil.

Expone `model_for()` y `FallbackChatModel`. Se importan de forma PEREZOSA
(vía __getattr__) para que se pueda usar `router.config` / `router.metrics`
(Python puro) sin arrastrar langchain — útil para los tests de la lógica.
"""
from __future__ import annotations

from typing import Any

__all__ = ["FallbackChatModel", "model_for"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from router import fallback
        return getattr(fallback, name)
    raise AttributeError(f"module 'router' has no attribute {name!r}")
