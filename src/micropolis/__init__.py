"""Top-level package for micropolis.

Avoid importing submodules at package import time to prevent large
import cascades and circular import issues. Submodules may be imported
by consumer code as needed (e.g. `from src.micropolis import sim_control`).
"""

__all__ = ["sim_control", "budget", "resources", "audio", "platform", "stubs", "camera"]

from importlib import import_module
from types import ModuleType
from typing import Any


def __getattr__(name: str) -> Any:
    """Lazy-load requested submodules on attribute access.

    This avoids importing heavy submodules when the package is imported
    (which previously caused circular import problems during early
    initialization/compat checks).
    """
    if name in __all__:
        mod = import_module(f"src.micropolis.{name}")
        globals()[name] = mod
        return mod
    raise AttributeError(name)


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
