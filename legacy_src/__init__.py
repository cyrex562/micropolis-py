"""Compatibility shim so ``import micropolis.*`` works without installation.

The canonical implementation lives under ``src/micropolis``. This module
behaves like a namespace package that forwards attribute and submodule
lookups to the real implementation so existing imports such as
``from micropolis import constants`` continue to function.
"""

from __future__ import annotations

import pkgutil
import sys
from collections.abc import Iterable
from importlib import import_module
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC_ROOT = _PROJECT_ROOT.joinpath("src", "micropolis")
__all__: list[str] = []

__path__: list[str] = []

if _SRC_ROOT.is_dir():
    __path__.append(str(_SRC_ROOT))

# Include the project root so ``micropolis.tests`` resolves to the in-tree
# pytest package when running from a checkout.
__path__.append(str(_PROJECT_ROOT))

if __spec__ is not None:  # type: ignore[name-defined]
    __spec__.submodule_search_locations = list(__path__)  # type: ignore[attr-defined]


def _import_from_src(name: str) -> Any:
    target = f"src.micropolis.{name}"
    module = import_module(target)
    globals()[name] = module
    sys.modules.setdefault(f"{__name__}.{name}", module)
    if name not in __all__:
        __all__.append(name)
    return module


def __getattr__(name: str) -> Any:
    try:
        return _import_from_src(name)
    except ModuleNotFoundError as exc:  # pragma: no cover - mirrors stdlib behaviour
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc


def __dir__() -> list[str]:
    names: set[str] = set(globals()) | set(__all__)
    for path in _iter_namespace():
        names.add(path)
    return sorted(names)


def _iter_namespace() -> Iterable[str]:
    if not __path__:
        return []
    return (name for _, name, _ in pkgutil.iter_modules(__path__))
