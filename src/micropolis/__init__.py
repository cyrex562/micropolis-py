"""Top-level package for micropolis.

Avoid importing submodules at package import time to prevent large
import cascades and circular import issues. Submodules may be imported
by consumer code as needed (e.g. `from src.micropolis import sim_control`).
"""

import sys
from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = ["sim_control", "budget", "resources", "audio", "platform", "stubs", "camera"]

if TYPE_CHECKING:  # pragma: no cover - import-time hints only
    from src.micropolis import audio as audio_module
    from src.micropolis import budget as budget_module
    from src.micropolis import camera as camera_module
    from src.micropolis import platform as platform_module
    from src.micropolis import resources as resources_module
    from src.micropolis import sim_control as sim_control_module
    from src.micropolis import stubs as stubs_module

    sim_control = sim_control_module
    budget = budget_module
    resources = resources_module
    audio = audio_module
    platform = platform_module
    stubs = stubs_module
    camera = camera_module


def __getattr__(name: str) -> Any:
    """Lazy-load requested submodules on attribute access.

    This avoids importing heavy submodules when the package is imported
    (which previously caused circular import problems during early
    initialization/compat checks).
    """
    if name in __all__:
        alias = f"{__name__}.{name}"
        # If the alias already exists (for example, set by tests that import
        # via ``micropolis.sim_control``), reuse it to ensure we don't create
        # duplicate module objects with different names.
        mod = sys.modules.get(alias)
        if mod is None:
            mod = import_module(f"src.micropolis.{name}")
            sys.modules[alias] = mod
        globals()[name] = mod
        return mod
    raise AttributeError(name)


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
