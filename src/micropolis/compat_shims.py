"""Compatibility helpers for adding lightweight legacy wrappers.

These helpers are intentionally small and test-focused: they provide a
convenient way to wrap existing context-first functions so legacy code
or tests that call them without an explicit ``context`` argument still
work during incremental migration.

The wrappers search sys.modules for a module with the ``_AUTO_TEST_CONTEXT``
attribute (set by the test autouse fixture) and use that AppContext when
the caller omitted the context. If no test context is found the wrapper
raises a TypeError to preserve explicitness in production code.
"""

from __future__ import annotations

import functools
import importlib
import inspect
import sys
import types
from typing import Any, Callable, Iterable

from micropolis.context import AppContext
from .legacy_state import LEGACY_MIRROR_ATTRS


_MIRROR_DEPTHS: dict[int, int] = {}


def _enter_mirror(ctx: AppContext) -> int:
    key = id(ctx)
    depth = _MIRROR_DEPTHS.get(key, 0) + 1
    _MIRROR_DEPTHS[key] = depth
    return depth


def _exit_mirror(ctx: AppContext) -> None:
    key = id(ctx)
    depth = _MIRROR_DEPTHS.get(key, 1) - 1
    if depth <= 0:
        _MIRROR_DEPTHS.pop(key, None)
    else:
        _MIRROR_DEPTHS[key] = depth


def _copy_from_types(ctx: AppContext, types_module: types.ModuleType) -> None:
    for attr in LEGACY_MIRROR_ATTRS:
        if hasattr(types_module, attr):
            try:
                setattr(ctx, attr, getattr(types_module, attr))
            except Exception:
                pass


def _copy_to_types(ctx: AppContext, types_module: types.ModuleType) -> None:
    for attr in LEGACY_MIRROR_ATTRS:
        if hasattr(ctx, attr):
            try:
                setattr(types_module, attr, getattr(ctx, attr))
            except Exception:
                pass


def _find_auto_context() -> AppContext | None:
    """Search loaded modules for the test-injected AppContext.

    Returns the first found AppContext or None if none present.
    """
    for mod in list(sys.modules.values()):
        try:
            ctx = getattr(mod, "_AUTO_TEST_CONTEXT", None)
            if isinstance(ctx, AppContext):
                return ctx
        except Exception:
            continue
    return None


def inject_legacy_wrappers(module, names: Iterable[str]) -> None:
    """Replace attributes on ``module`` with wrappers that accept
    either (context, ...) or the legacy signature without the leading
    context argument.

    Only applies the wrapper if the attribute exists and is callable.
    """
    for name in names:
        orig = getattr(module, name, None)
        if orig is None or not callable(orig):
            continue

        # Heuristic: only wrap callables that expect an AppContext as the
        # first parameter (named 'context' or annotated as AppContext). This
        # prevents wrapping legacy helpers that don't take a context (e.g.
        # tally, checkSize) which would otherwise receive an extra injected
        # argument and raise TypeError.
        try:
            sig = inspect.signature(orig)
            params = list(sig.parameters.values())
            if not params:
                continue
            first = params[0]
            if first.name != "context":
                # Not a context-first function; skip wrapping.
                continue
        except (ValueError, TypeError):
            # If we can't inspect the signature conservatively skip wrapping.
            continue

        @functools.wraps(orig)
        def _wrapper(*args, __orig=orig, **kwargs):
            def _mirror_call(
                target_ctx: AppContext, call_args: tuple, call_kwargs: dict
            ) -> Any:
                try:
                    _types_mod = importlib.import_module("micropolis.types")
                except Exception:
                    _types_mod = None
                depth = _enter_mirror(target_ctx)
                try:
                    if depth == 1 and _types_mod is not None:
                        _copy_from_types(target_ctx, _types_mod)
                    return __orig(*call_args, **call_kwargs)
                finally:
                    if _types_mod is not None:
                        _copy_to_types(target_ctx, _types_mod)
                    _exit_mirror(target_ctx)

            if args and isinstance(args[0], AppContext):
                ctx_arg = args[0]
                auto_ctx = _find_auto_context()
                if auto_ctx is not None:
                    return _mirror_call(ctx_arg, args, kwargs)
                return __orig(*args, **kwargs)

            ctx = _find_auto_context()
            if ctx is not None:
                return _mirror_call(ctx, (ctx,) + args, kwargs)

            raise TypeError(
                f"{name}() missing required AppContext argument and no test context was found"
            )

        try:
            setattr(module, name, _wrapper)
        except Exception:
            # Be conservative — if we can't replace the attribute, skip it.
            continue
