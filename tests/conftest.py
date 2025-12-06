from __future__ import annotations

import sys
import os
from pathlib import Path

import pytest
import pygame

from micropolis.app_config import AppConfig
from micropolis.context import AppContext


@pytest.fixture(autouse=True)
def test_context(request):
    """Provide a test AppContext and pygame display for every test.

    This fixture is autouse so it runs for all tests. It injects a module-level
    `context` variable into the test module and builtins. It also creates a
    small pygame display surface.
    """

    # Initialize pygame (safe to call multiple times)
    pygame.init()
    _prev_fast_tests = os.environ.get("MICROPOLIS_FAST_TESTS")
    os.environ["MICROPOLIS_FAST_TESTS"] = "1"
    try:
        screen = pygame.display.set_mode((320, 240))
    except Exception:
        screen = pygame.Surface((320, 240))

    # Build AppContext with default config
    cfg = AppConfig()
    ctx = AppContext(config=cfg)
    ctx.main_display = screen

    # Canonicalize module objects
    try:
        for mod_name in list(sys.modules.keys()):
            try:
                if mod_name.startswith("src.micropolis."):
                    alias = mod_name.replace("src.", "", 1)
                    if alias not in sys.modules:
                        sys.modules[alias] = sys.modules[mod_name]
                elif mod_name == "src.micropolis":
                    if "micropolis" not in sys.modules:
                        sys.modules["micropolis"] = sys.modules[mod_name]
                elif mod_name.startswith("micropolis."):
                    alias = "src." + mod_name
                    if alias not in sys.modules:
                        sys.modules[alias] = sys.modules[mod_name]
            except Exception:
                continue
    except Exception:
        pass

    # Initialize legacy attributes on AppContext
    ctx.last_keys = "    "
    ctx.punish_cnt = 0
    ctx.dozing = 0
    from micropolis.constants import WORLD_X, WORLD_Y

    ctx.map_data = [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]

    # Initialize engine
    try:
        try:
            from micropolis import engine as _engine
        except Exception:
            try:
                from src.micropolis import engine as _engine
            except Exception:
                _engine = None

        if _engine is not None:
            try:
                _engine.sim_init(ctx)
                _engine.initialize_view_surfaces(ctx)
            except Exception:
                pass
    except Exception:
        pass

    # Set default funds
    ctx.total_funds = 10_000_000
    ctx.last_funds = ctx.total_funds

    # Inject _AUTO_TEST_CONTEXT for legacy shims (e.g. MakeSound)
    try:
        import importlib

        pkg = importlib.import_module("micropolis")
        setattr(pkg, "_AUTO_TEST_CONTEXT", ctx)
    except Exception:
        pass
    try:
        import importlib

        pkg_src = importlib.import_module("src.micropolis")
        setattr(pkg_src, "_AUTO_TEST_CONTEXT", ctx)
    except Exception:
        pass

    # Tools aliases
    try:
        from micropolis import tools as _tools

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
        ctx.pygame_display = screen

        from micropolis import messages as _messages

        setattr(_tools, "clear_mes", _messages.clear_mes)
        setattr(_tools, "send_mes", _messages.send_mes)
    except Exception:
        pass

    # Inject context into test module
    try:
        test_module = request.node.getparent(pytest.Item).module
    except Exception:
        test_module = getattr(request, "module", None)
    if test_module is not None:
        setattr(test_module, "context", ctx)
        setattr(test_module, "pygame_display", screen)

    # Inject into builtins
    import builtins

    setattr(builtins, "context", ctx)
    setattr(builtins, "pygame_display", screen)

    yield ctx

    # Teardown
    try:
        if _prev_fast_tests is None:
            del os.environ["MICROPOLIS_FAST_TESTS"]
        else:
            os.environ["MICROPOLIS_FAST_TESTS"] = _prev_fast_tests
    except Exception:
        pass

    try:
        delattr(test_module, "context")
    except Exception:
        pass
    try:
        delattr(test_module, "pygame_display")
    except Exception:
        pass
    try:
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
