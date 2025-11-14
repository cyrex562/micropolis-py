from importlib import import_module
from typing import Any

__all__ = ["sim_control", "budget", "evaluation_ui", "tkinter_bridge"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        mod = import_module(f"src.micropolis.{name}")
        globals()[name] = mod
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
