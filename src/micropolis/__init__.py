"""Top-level package for micropolis.

Avoid importing submodules at package import time to prevent large
import cascades and circular import issues. Submodules may be imported
by consumer code as needed (e.g. `from src.micropolis import sim_control`).
"""

import sys
from importlib import import_module
from typing import Any


def __getattr__(name: str) -> Any:
    """Lazy-load any submodule on attribute access.

    Tests and legacy code import modules via the ``src.micropolis`` package
    path and sometimes expect attributes (submodules) to be present on the
    package. Rather than eagerly importing everything at package import time
    (which caused circular-imports and startup cost), we lazily import the
    requested submodule when it is first accessed.

    We use the current package name (``__name__``) so this works whether the
    package is imported as ``micropolis`` or ``src.micropolis``.
    """
    alias = f"{__name__}.{name}"
    # If module already loaded under the fully-qualified name, return it
    mod = sys.modules.get(alias)
    if mod is not None:
        globals()[name] = mod
        return mod

    # Attempt to import the submodule relative to this package
    try:
        mod = import_module(alias)
    except Exception as exc:  # pragma: no cover - fall through to AttributeError
        raise AttributeError(f"module {__name__} has no attribute {name}") from exc

    # Register and expose
    sys.modules[alias] = mod
    globals()[name] = mod
    return mod


def __dir__() -> list[str]:
    # Return current attributes; dynamic submodules will appear once accessed
    return sorted(list(globals().keys()))
