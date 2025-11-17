from __future__ import annotations

import sys
from pathlib import Path

import pytest
import pygame

from micropolis.app_config import AppConfig
from micropolis.context import AppContext


@pytest.fixture(autouse=True)
def test_context(request):
    """Provide a test AppContext and pygame display for every test.

    This fixture is autouse so it runs for all tests (including unittest
    TestCase-based tests). It injects a module-level `context` variable
    into the test module so legacy tests that reference `context` at
    module scope will find it. It also creates a small pygame display
    surface and exposes it as `pygame_display` on the test module.

    The fixture tears down pygame and removes injected names after each
    test.
    """

    # Initialize pygame (safe to call multiple times)
    pygame.init()
    try:
        # Try to create a small hidden display surface; some CI systems
        # may not support a visible window so allow fallback to a
        # software surface.
        screen = pygame.display.set_mode((320, 240))
    except Exception:
        # Fallback: create a Surface manually
        screen = pygame.Surface((320, 240))

    # Build AppContext with default config
    cfg = AppConfig()
    ctx = AppContext(config=cfg)
    ctx.main_display = screen

    # Provide a few legacy module-level fields that many tests expect
    # These are small, safe defaults used by the keyboard tests and a
    # few other legacy test cases. Tests are free to overwrite these
    # values as needed.
    # Initialize a few legacy attributes on the AppContext. These fields
    # are now defined on the model so normal assignment is safe and will
    # participate in state-contract notifications.
    ctx.last_keys = "    "
    ctx.punish_cnt = 0
    ctx.dozing = 0
    # Initialize a full-size empty map so legacy tools that index into
    # `context.map_data[x][y]` don't hit IndexError during tests. Some
    # older tests expected a pre-sized map and would overwrite it as
    # needed; using the canonical WORLD_X/WORLD_Y sizes is the safest
    # default.
    from micropolis.constants import WORLD_X, WORLD_Y

    ctx.map_data = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]

    # Provide test-friendly financial defaults so tools can be used without
    # each test having to set funds explicitly.
    ctx.total_funds = 10_000_000
    ctx.last_funds = ctx.total_funds

    # Ensure micropolis.types.* arrays point at the same buffers so tests
    # that modify module-level `types.map_data` are visible to code that
    # reads from the injected `context` (and vice-versa).
    try:
        import micropolis.types as _types_mod

        # Mirror common buffers into the types module so legacy tests that
        # mutate module-level arrays (eg. `types.map_data`) are visible to
        # code that reads from the injected AppContext and vice-versa.
        _types_mod.map_data = ctx.map_data
        # Mirror other optional buffers if present
        if hasattr(ctx, "pop_density"):
            _types_mod.pop_density = ctx.pop_density
        if hasattr(ctx, "land_value_mem"):
            _types_mod.land_value_mem = ctx.land_value_mem
        if hasattr(ctx, "crime_mem"):
            _types_mod.crime_mem = ctx.crime_mem
        if hasattr(ctx, "pollution_mem"):
            _types_mod.pollution_mem = ctx.pollution_mem
        if hasattr(ctx, "rate_og_mem"):
            _types_mod.rate_og_mem = ctx.rate_og_mem
        # Traffic/transport arrays seen in some legacy tests
        if hasattr(ctx, "trf_density"):
            _types_mod.trf_density = ctx.trf_density

        # Mirror financial totals when present so tests that set
        # micropolis.types.total_funds are reflected into the context.
        if hasattr(_types_mod, "total_funds"):
            ctx.total_funds = getattr(_types_mod, "total_funds")
        elif hasattr(_types_mod, "TotalFunds"):
            ctx.total_funds = getattr(_types_mod, "TotalFunds")
    except Exception:
        # Not all test runs need these; ignore import errors
        pass

    # Populate tool size/offset arrays from the tools compatibility lists so
    # ToolDrag and other helpers can index into them safely during tests.
    try:
        from micropolis import tools as _tools

        # Create common lowercase aliases for legacy callsites/tests that
        # expect functions like `tools.tool_down` (lowercase) while the
        # implementation provides `ToolDown` (PascalCase). These aliases are
        # test-only and help bridge the API surface during migration.
        for src_name, alias in (
            ("ToolDown", "tool_down"),
            ("ToolDrag", "tool_drag"),
            ("ToolUp", "tool_up"),
            ("DoTool", "do_tool"),
            ("DidTool", "did_tool"),
        ):
            if hasattr(_tools, src_name) and not hasattr(_tools, alias):
                try:
                    setattr(_tools, alias, getattr(_tools, src_name))
                except Exception:
                    pass
        ctx.tool_size = list(getattr(_tools, "toolSize", []))
        ctx.tool_offset = list(getattr(_tools, "toolOffset", []))
        # Expose legacy pygame_display alias used in some modules/tests
        ctx.pygame_display = screen

        # Ensure message helpers referenced by tools (clear_mes/send_mes)
        # are available in the tools module namespace so calls like
        # clear_mes(context) succeed.
        from micropolis import messages as _messages

        setattr(_tools, "clear_mes", _messages.clear_mes)
        setattr(_tools, "send_mes", _messages.send_mes)
    except Exception:
        # If the package modules aren't available yet, tests can still run
        # and may patch these later. Ignore import errors here.
        pass

    # Inject into the test module namespace so tests can reference
    # `context` and `pygame_display` as globals (many tests use these).
    # Determine test module robustly (works for both pytest-style functions
    # and unittest.TestCase-based tests). When the module cannot be resolved
    # from the request node we fall back to the request.module attribute.
    try:
        test_module = request.node.getparent(pytest.Item).module
    except Exception:
        test_module = getattr(request, "module", None)
    if test_module is not None:
        setattr(test_module, "context", ctx)
        setattr(test_module, "pygame_display", screen)

    # Also inject into builtins so legacy tests that reference `context`
    # at module level (or in C extension code) can still resolve the name
    # even when module-level globals weren't patched correctly. This is a
    # conservative test-only shim and is removed during teardown.
    import builtins

    setattr(builtins, "context", ctx)
    setattr(builtins, "pygame_display", screen)

    # Also provide convenience wrappers on micropolis submodules so existing
    # tests that call functions without an explicit `context` argument keep
    # working. We wrap functions whose first parameter is a required
    # 'context' to automatically supply the test context when the caller
    # omits it.
    import importlib
    import inspect
    import types as _types

    patched = []
    # Patch modules imported either as `micropolis.*` or `src.micropolis.*`.
    # Some tests import via the `src` package path; scan sys.modules so we
    # catch both import styles and wrap functions that expect a leading
    # `context` argument but are called without one.
    for mod_name, mod in list(sys.modules.items()):
        if not isinstance(mod, _types.ModuleType):
            continue
        if not (
            mod_name.startswith("micropolis.") or mod_name.startswith("src.micropolis.")
        ):
            continue
        for obj_name in dir(mod):
            try:
                obj = getattr(mod, obj_name)
            except Exception:
                continue
            if not inspect.isfunction(obj):
                continue
            # Only wrap functions defined in this package namespace
            if not getattr(obj, "__module__", "").startswith(
                ("micropolis", "src.micropolis")
            ):
                continue
            sig = inspect.signature(obj)
            params = list(sig.parameters.values())
            if (
                params
                and params[0].name == "context"
                and params[0].default is inspect._empty
                and params[0].kind
                in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )
            ):
                # create wrapper that injects ctx when missing
                def _make_wrapper(func):
                    # Attempt to import AppContext for runtime type checks
                    try:
                        from micropolis.context import AppContext as _AppContext
                    except Exception:
                        _AppContext = None

                    def _wrapper(*args, __func=func, **kwargs):
                        # If caller omitted the leading context arg or passed a
                        # non-AppContext first argument, insert the test ctx.
                        # Only inject the test context when the caller truly
                        # omitted the leading `context` argument (no args),
                        # or when the first arg is present but is clearly
                        # not an AppContext (legacy call shape). If the
                        # caller passed ``None`` explicitly we must not
                        # inject the test ctx because some functions treat
                        # ``None`` as a meaningful explicit value (e.g.
                        # _ensure_context(None)). Treat ``None`` as an
                        # explicit value and do not replace it.
                        # If the caller explicitly provided 'context' as a
                        # keyword argument, do not inject — respect the
                        # caller's intent (this avoids double-injection
                        # when callers already pass context via kwargs).
                        if "context" in kwargs:
                            return __func(*args, **kwargs)
                        # Decide whether to inject the test context.
                        # Heuristics:
                        # - If caller provided 'context' as kwarg, do not inject.
                        # - If caller passed no positional args, inject.
                        # - If caller passed a simple primitive as first arg,
                        #   assume legacy call shape and inject.
                        # - If caller passed exactly one fewer positional
                        #   argument than the function requires (i.e. they
                        #   omitted the leading context), inject as well.
                        inject_ctx = False
                        if len(args) < 1:
                            inject_ctx = True
                        else:
                            # simple primitive legacy shape
                            if (
                                _AppContext is not None
                                and args[0] is not None
                                and not isinstance(args[0], _AppContext)
                                and isinstance(args[0], (int, float, str, bool))
                            ):
                                inject_ctx = True
                            else:
                                # Fallback heuristic: compare number of
                                # supplied positional args with the function's
                                # required positional parameters; if the
                                # caller provided exactly one fewer, they
                                # likely omitted the leading context.
                                try:
                                    _sig = inspect.signature(func)
                                    _params = [
                                        p
                                        for p in _sig.parameters.values()
                                        if p.kind
                                        in (
                                            inspect.Parameter.POSITIONAL_ONLY,
                                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                        )
                                    ]
                                    # count required (no default) positional params
                                    _required = [
                                        p
                                        for p in _params
                                        if p.default is inspect._empty
                                    ]
                                    if _required and _required[0].name == "context":
                                        if len(args) == (len(_required) - 1):
                                            inject_ctx = True
                                except Exception:
                                    pass

                        if inject_ctx:
                            # Sync a small set of common legacy module-level
                            # globals into the AppContext before calling. Many
                            # legacy tests mutate `micropolis.types` (eg
                            # `types.map_data` and `types.total_funds`) and
                            # expect tool functions to operate on those
                            # buffers. When we inject the test context we
                            # mirror those module-level values into the ctx so
                            # wrapped calls observe the test-modified state.
                            try:
                                import micropolis.types as _types_mod

                                # Mirror map/overlay buffers if present
                                if hasattr(_types_mod, "map_data"):
                                    ctx.map_data = getattr(_types_mod, "map_data")
                                if hasattr(_types_mod, "pop_density"):
                                    ctx.pop_density = getattr(_types_mod, "pop_density")
                                if hasattr(_types_mod, "land_value_mem"):
                                    ctx.land_value_mem = getattr(
                                        _types_mod, "land_value_mem"
                                    )
                                if hasattr(_types_mod, "crime_mem"):
                                    ctx.crime_mem = getattr(_types_mod, "crime_mem")
                                if hasattr(_types_mod, "pollution_mem"):
                                    ctx.pollution_mem = getattr(
                                        _types_mod, "pollution_mem"
                                    )
                                if hasattr(_types_mod, "rate_og_mem"):
                                    ctx.rate_og_mem = getattr(_types_mod, "rate_og_mem")

                                # Mirror funds: prefer lowercase attr often set by
                                # tests, fall back to legacy TotalFunds constant.
                                if hasattr(_types_mod, "total_funds"):
                                    ctx.total_funds = getattr(_types_mod, "total_funds")
                                elif hasattr(_types_mod, "TotalFunds"):
                                    ctx.total_funds = getattr(_types_mod, "TotalFunds")
                            except Exception:
                                # If mirroring fails, continue with existing ctx
                                pass

                            return __func(ctx, *args, **kwargs)
                        return __func(*args, **kwargs)

                    _wrapper.__name__ = func.__name__
                    _wrapper.__doc__ = func.__doc__
                    return _wrapper

                original = obj
                wrapper = _make_wrapper(original)
                try:
                    setattr(mod, obj_name, wrapper)
                    patched.append((mod, obj_name, original))
                except Exception:
                    # If we cannot set attribute (builtins or C extension), skip
                    continue

    # Expose the test context on the micropolis package objects so lightweight
    # compatibility shims can pick it up if they need a default context during
    # tests (this keeps the production API requiring explicit AppContext).
    try:
        pkg = importlib.import_module("micropolis")
        setattr(pkg, "_AUTO_TEST_CONTEXT", ctx)
    except Exception:
        pass
    try:
        pkg_src = importlib.import_module("src.micropolis")
        setattr(pkg_src, "_AUTO_TEST_CONTEXT", ctx)
    except Exception:
        pass

    # Test-only compatibility: ensure sibling micropolis submodules are
    # available as attributes on each other so legacy code that expects
    # module-level attributes (eg. `editor.types` or `engine.graphs`) keeps
    # working during migration. We build a map of short-name -> module and
    # then inject missing attributes onto each loaded micropolis module.
    try:
        # Pre-import a small set of commonly-referenced submodules so they
        # appear in sys.modules and can be injected as attributes on sibling
        # modules. This prevents timing/order-dependent failures in tests
        # that expect attributes like `engine.evaluation_ui` to exist.
        common = (
            "types",
            "graphs",
            "evaluation_ui",
            "generation",
            "stubs",
            "network",
            "pie_menu",
            "tools",
            "messages",
            "map_view",
            "map_renderer",
            "mini_maps",
            "power",
            "tkinter_bridge",
        )
        for name in common:
            try:
                importlib.import_module(f"micropolis.{name}")
            except Exception:
                try:
                    importlib.import_module(f"src.micropolis.{name}")
                except Exception:
                    # ignore failures; we'll still inject whatever is loaded
                    pass

        # Collect micropolis submodules currently loaded
        submods: dict[str, object] = {}
        for mname, mobj in list(sys.modules.items()):
            if not isinstance(mobj, _types.ModuleType):
                continue
            if mname.startswith("micropolis.") or mname.startswith("src.micropolis."):
                short = mname.split(".")[-1]
                # prefer the canonical micropolis.* module object when both
                # src.micropolis.* and micropolis.* are present
                if short in submods and mname.startswith("src.micropolis."):
                    # skip src.* duplicate if we already have micropolis.*
                    continue
                submods[short] = mobj

        # Inject missing sibling attributes onto each micropolis module
        for mname, mobj in list(sys.modules.items()):
            if not isinstance(mobj, _types.ModuleType):
                continue
            if not (
                mname.startswith("micropolis.") or mname.startswith("src.micropolis.")
            ):
                continue
            for short, submod in submods.items():
                try:
                    if not hasattr(mobj, short):
                        setattr(mobj, short, submod)
                except Exception:
                    # best-effort only; don't fail tests for attribute errors
                    continue
    except Exception:
        pass

    # Provide test-only module-level shims for tkinter_bridge so tests that
    # monkeypatch module attributes (eg. main_window, command_callbacks,
    # stdin_thread) find them even when the production code stores state on
    # the AppContext instead. These are conservative defaults that tests
    # can override.
    try:
        import queue as _queue

        for tb_name in ("micropolis.tkinter_bridge", "src.micropolis.tkinter_bridge"):
            try:
                tb_mod = importlib.import_module(tb_name)
            except Exception:
                continue
            try:
                if not hasattr(tb_mod, "main_window"):
                    setattr(tb_mod, "main_window", None)
                if not hasattr(tb_mod, "command_callbacks"):
                    setattr(tb_mod, "command_callbacks", {})
                if not hasattr(tb_mod, "stdin_thread"):
                    setattr(tb_mod, "stdin_thread", None)
                if not hasattr(tb_mod, "stdin_queue"):
                    setattr(tb_mod, "stdin_queue", _queue.Queue())
                if not hasattr(tb_mod, "running"):
                    setattr(tb_mod, "running", False)
                # Timer flags commonly referenced by tests
                if not hasattr(tb_mod, "sim_timer_token"):
                    setattr(tb_mod, "sim_timer_token", None)
                if not hasattr(tb_mod, "sim_timer_set"):
                    setattr(tb_mod, "sim_timer_set", False)
                if not hasattr(tb_mod, "sim_timer_idle"):
                    setattr(tb_mod, "sim_timer_idle", False)
                if not hasattr(tb_mod, "earthquake_timer_token"):
                    setattr(tb_mod, "earthquake_timer_token", None)
                if not hasattr(tb_mod, "earthquake_timer_set"):
                    setattr(tb_mod, "earthquake_timer_set", False)
                if not hasattr(tb_mod, "update_delayed"):
                    setattr(tb_mod, "update_delayed", False)
            except Exception:
                # best-effort safety: don't raise during fixture setup
                continue
    except Exception:
        pass

    yield ctx

    # restore patched functions
    for mod, name, original in patched:
        try:
            setattr(mod, name, original)
        except Exception:
            pass

    # Teardown: remove injected names and quit pygame display
    try:
        delattr(test_module, "context")
    except Exception:
        pass
    try:
        delattr(test_module, "pygame_display")
    except Exception:
        pass
    try:
        import builtins

        delattr(builtins, "context")
        delattr(builtins, "pygame_display")
    except Exception:
        pass

    try:
        pygame.display.quit()
    except Exception:
        pass
    try:
        pygame.quit()
    except Exception:
        pass


# Ensure `src/` and repository root are importable when running tests from
# the checked-out workspace. This mirrors repository test helpers used
# elsewhere and keeps imports working without installing the package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
root_path = str(PROJECT_ROOT)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

src_dir = PROJECT_ROOT / "src"
src_path = str(src_dir)
if src_dir.exists() and src_path not in sys.path:
    sys.path.insert(0, src_path)
