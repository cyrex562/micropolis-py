"""
engine.py - Main simulation engine and state management for Micropolis Python port

This module contains the main simulation orchestration, initialization, and
state management functions ported from sim.c, adapted for Python/pygame.
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from typing import TYPE_CHECKING

import pygame
from result import Err, Ok, Result

from . import graphics_setup, initialization
from .allocation import init_map_arrays
from .app_config import AppConfig
from .audio import initialize_sound
from .constants import (
    ALMAP,
    COMAP,
    CRMAP,
    DEFAULT_STARTING_FUNDS,
    DIRT,
    DYMAP,
    EDITOR_H,
    EDITOR_W,
    FIMAP,
    INMAP,
    LVMAP,
    MAP_H,
    MAP_W,
    MICROPOLIS_VERSION,
    NMAPS,
    PDMAP,
    PLMAP,
    POMAP,
    PRMAP,
    RDMAP,
    REMAP,
    RESBASE,
    RGMAP,
    TDMAP,
    WORLD_X,
    WORLD_Y,
)
from .context import AppContext
from .editor import do_update_editor
from .graphics_setup import init_graphics
from .graphs import render_graph_panel, request_graph_panel_redraw, update_all_graphs
from .initialization import InitWillStuff
from .input_actions import InputActionDispatcher
from .macros import LOMASK, ZONEBIT
from .map_view import MemDrawMap
from .sim_view import SimView, create_editor_view, create_map_view
from .simulation import sim_frame
from .ui.event_bus import get_default_event_bus
from .ui.input_bindings import get_default_input_binding_manager
from .ui.keybindings_overlay import KeybindingsOverlay
from .ui.panel_manager import PanelManager
from .ui.panels import EditorPanel, ToolPalettePanel
from .ui_utilities import handle_keyboard_shortcut
from .view_types import (
    MakeNewSimGraph,
    MakeNewSimDate,
    MakeNewXDisplay,
    XDisplay,
    Map_Class,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .sim import Sim

# ============================================================================
# Global Simulation State
# ============================================================================

# Version information
# MicropolisVersion: str = "4.0"

# Main simulation instance
# sim: micropolis.sim.Sim | None = None

# Simulation timing and control
# sim_loops: int = 0
# sim_delay: int = 50
# sim_skips: int = 0
# sim_skip: int = 0
# sim_paused: int = 0
# sim_paused_speed: int = 3
# sim_tty: int = 0

# Heat simulation (experimental feature)
# heat_steps: int = 0
# heat_flow: int = -7
# heat_rule: int = 0
# heat_wrap: int = 3
# current_tool_tile: int = RESBASE
# editor_viewport_size: tuple[int, int] = (0, 0)

# Timing variables (simplified for Python)
# start_time: float = 0.0
# beat_time: float = 0.0
# last_now_time: float = 0.0

# File and startup settings
# city_file_name: str | None = None
# startup: int = 0
# startup_game_level: int = 0

# ============================================================================
# View Management Functions
# ============================================================================


# ported from InvalidateMaps
def invalidate_maps(sim: Sim) -> Result[None, Exception]:
    """
    Invalidate all map views to force redraw.

    Marks all map views as needing to be updated.
    """
    # if not sim or not sim.map:
    #     return Err(ValueError)

    view = sim.map
    while view:
        view.invalid = True
        view = view.next
    return Ok(None)


# ported from InvalidateEditors
def invalidate_errors(sim: Sim) -> Result[None, Exception]:
    """
    Invalidate all editor views to force redraw.

    Marks all editor views as needing to be updated.
    """
    # if not sim or not sim.editor:
    #     return

    view = sim.editor
    while view:
        view.invalid = True
        view = view.next

    return Ok(None)


# startup_name: str | None = None

# Mode flags
# wire_mode: int = 0
# multi_player_mode: int = 0
# SugarMode: int = 0

# Animation and display
# tiles_animated: int = 0
# do_animation: int = 1
# do_messages: int = 1
# do_notices: int = 1

# Display settings (simplified for pygame)
# displays: str | None = None
# first_display: str | None = None

# Exit handling
# exit_return: int = 0
# tk_must_exit: bool = False

# Heat simulation arrays (experimental)
# CellSrc: list[int] = []
# CellDst: list[int] = []


# ============================================================================
# Helper Functions
# ============================================================================


def get_or_create_display(context: AppContext) -> XDisplay:
    """Ensure there is a display object available for view wiring."""
    if context.main_display is None:
        context.main_display = MakeNewXDisplay()
        context.main_display.color = 1
        context.main_display.depth = 32

    return context.main_display


def set_current_tool(context: AppContext, tile_id: int) -> None:
    """Update the currently selected placement tile."""
    context.current_tool_tile = tile_id & LOMASK


def apply_tool_to_tile(
    context: AppContext, sim: Sim, tile_x: int, tile_y: int, bulldoze: bool = False
) -> Result[None, Exception]:
    """Modify the map at the requested tile coordinates."""
    if not (0 <= tile_x < WORLD_X and 0 <= tile_y < WORLD_Y):
        return Err(ValueError(f"Invalid tile coordinates: {tile_x}, {tile_y}"))

    if bulldoze:
        new_tile = DIRT
    else:
        new_tile = (context.current_tool_tile & LOMASK) | ZONEBIT

    context.map_data[tile_x][tile_y] = new_tile
    context.new_map = 1

    result = invalidate_maps(sim)
    if result.is_err():
        return result

    result = invalidate_errors(sim)
    if result.is_err():
        return result
    return Ok(None)


def area_contains_point(area: tuple[int, int, int, int], pos: tuple[int, int]) -> bool:
    """Return True if the screen position lies within the given rectangle."""
    ax, ay, aw, ah = area
    return ax <= pos[0] < ax + aw and ay <= pos[1] < ay + ah


def handle_map_click(
    context: AppContext,
    sim: Sim,
    pos: tuple[int, int],
    area: tuple[int, int, int, int],
    button: int,
) -> bool:
    """Handle mouse clicks within the map viewport."""
    if not area_contains_point(area, pos):
        return False

    ax, ay, _, _ = area
    tile_x = (pos[0] - ax) // 3
    tile_y = (pos[1] - ay) // 3
    apply_tool_to_tile(context, sim, tile_x, tile_y, bulldoze=(button == 3))
    return True


def handle_tool_hotkey(
    context: AppContext, key: int, tool_hotkeys: dict[int, int]
) -> bool:
    """Switch tool selection if the key matches a hotkey entry."""
    tile = tool_hotkeys.get(key)
    if tile is None:
        return False

    set_current_tool(context, tile)
    logger.info(f"Selected tool tile {tile}")  # Basic feedback until UI is built
    return True


# def ensure_sim_structures(context: AppContext) -> Result[None, Exception]:
#     """Create the global simulation object and default views if needed."""
#     global sim

#     # if types.sim is None:
#     #     types.sim = types.MakeNewSim()

#     # sim = types.sim

#     # if sim.editor is None:
#     #     sim.editor = _create_editor_view()
#     #     sim.editors = 1

#     # if sim.map is None:
#     #     sim.map = _create_map_view()
#     #     sim.maps = 1

#     # if sim.graph is None:
#     #     sim.graph = view_types.MakeNewSimGraph()
#     #     sim.graphs = 1

#     # if sim.date is None:
#     #     sim.date = view_types.MakeNewSimDate()
#     #     sim.dates = 1

#     # return sim


# def _create_editor_view() -> micropolis.sim_view.SimView:
#     """Create and configure the primary editor view."""
#     # view = types.MakeNewView()
#     _populate_common_view_fields(
#         view, types.EDITOR_W, types.EDITOR_H, view_types.Editor_Class
#     )
#     # view.tile_width = types.WORLD_X
#     # view.tile_height = types.WORLD_Y
#     # view.line_bytes = view.width * view.pixel_bytes
#     # view.tool_state = types.dozeState
#     # view.tool_state_save = -1
#     editor_view.initialize_editor_tiles(view)
#     return view


# def _create_map_view() -> micropolis.sim_view.SimView:
#     """Create and configure the primary map view."""
#     view = types.MakeNewView()
#     _populate_common_view_fields(view, types.MAP_W, types.MAP_H, view_types.Map_Class)
#     view.tile_width = types.WORLD_X
#     view.tile_height = types.WORLD_Y
#     return view


# def _populate_common_view_fields(
#     view: types.SimView, width: int, height: int, class_id: int
# ) -> None:
#     """Populate shared view attributes for pygame rendering."""
#     # display = _get_or_create_display()

#     # view.class_id = class_id
#     # view.type = view_types.X_Mem_View
#     # view.visible = True
#     # view.invalid = True
#     # view.x = display
#     # view.surface = None
#     # view.width = width
#     # view.height = height
#     # view.m_width = width
#     # view.m_height = height
#     # view.w_width = width
#     # view.w_height = height
#     # view.i_width = width
#     # view.i_height = height
#     # view.screen_width = width
#     # view.screen_height = height
#     # view.pixel_bytes = 4
#     # view.line_bytes = width * view.pixel_bytes
#     # view.map_state = types.ALMAP
#     # view.tile_x = 0
#     # view.tile_y = 0
#     # view.tile_width = types.WORLD_X
#     # view.tile_height = types.WORLD_Y
#     # view.pan_x = 0
#     # view.pan_y = 0
#     # view.next = None


def _iter_views(head: SimView | None):
    """Iterate over a linked list of views."""
    current = head
    while current:
        yield current
        current = current.next


def _iter_all_views(sim_obj: Sim):
    """Yield all editor and map views."""
    yield from _iter_views(sim_obj.editor)
    yield from _iter_views(sim_obj.map)


def pan_editor_view(
    context: AppContext, dx: int, dy: int, viewport: tuple[int, int]
) -> None:
    """Pan the editor preview by the requested pixel delta."""
    if not context.sim or not context.sim.editor:
        return

    view = context.sim.editor
    width, height = viewport
    if width <= 0 or height <= 0:
        return

    max_x = max(0, view.width - width)
    max_y = max(0, view.height - height)

    view.pan_x = max(0, min(max_x, view.pan_x + dx))
    view.pan_y = max(0, min(max_y, view.pan_y + dy))


def initialize_view_surfaces(context: AppContext) -> Result[None, Exception]:
    """Attach pygame surfaces and tile caches to all views.

    This function:
    1. Creates pygame surfaces for each view
    2. Loads tile graphics from assets
    3. Populates tile caches (bigtiles for editor, smalltiles for map)
    4. Ensures views are ready for rendering

    :param context: Application context containing sim and views
    """

    if context.sim is None:
        logger.error("Cannot initialize view surfaces: context.sim is None")
        return Err(ValueError("context.sim is None"))

    display = get_or_create_display(context)

    # Initialize pixmaps and object sprites for the display
    graphics_setup.get_pixmaps(display)

    # Process all editor and map views
    for view in _iter_all_views(context.sim):
        # Ensure view has display reference
        if view.x is None:
            view.x = display
            logger.debug(f"Attached display to view (class_id={view.class_id})")

        # Create pygame surface if needed
        if view.surface is None:
            width, height = (
                (MAP_W, MAP_H) if view.class_id == Map_Class else (EDITOR_W, EDITOR_H)
            )
            view.surface = pygame.Surface((width, height), pygame.SRCALPHA)
            logger.debug(
                f"Created surface for view: {width}x{height} (class_id={view.class_id})"
            )

        # Load tile graphics for this view
        try:
            success = graphics_setup.init_view_graphics(view)
            if not success:
                logger.error(
                    f"Failed to initialize graphics for view (class_id={view.class_id})"
                )
                return Err(ValueError(f"Failed to initialize view graphics"))

            # Verify tile caches were populated
            if view.class_id == Map_Class:
                if view.smalltiles is None and view.x.small_tile_image is None:
                    logger.warning("Map view has no small tiles loaded")
                else:
                    logger.debug(
                        f"Map view tile cache initialized: smalltiles={'present' if view.smalltiles else 'from image'}"
                    )
            else:  # Editor view
                if view.bigtiles is None and (
                    view.x is None or view.x.big_tile_image is None
                ):
                    logger.warning("Editor view has no big tiles loaded")
                else:
                    logger.debug(
                        f"Editor view tile cache initialized: bigtiles={'present' if view.bigtiles else 'from image'}"
                    )

        except Exception as exc:  # pragma: no cover - defensive
            logger.exception(f"Failed to initialize view graphics: {exc}")
            return Err(exc)

    logger.info("All view surfaces initialized successfully")
    return Ok(None)


def blit_views_to_screen(
    context: AppContext,
    screen,
    map_area: tuple[int, int, int, int],
    editor_area: tuple[int, int, int, int],
) -> None:
    """Composite map/editor surfaces onto the main pygame screen.
    :param screen:
    """

    context.fill((64, 128, 64))

    if context.sim and context.sim.map and context.sim.map.surface:
        map_surface = pygame.transform.smoothscale(
            context.sim.map.surface, (map_area[2], map_area[3])
        )
        context.blit(map_surface, (map_area[0], map_area[1]))

    if context.sim and context.sim.editor and context.sim.editor.surface:
        editor_surface = context.sim.editor.surface
        viewport_w, viewport_h = context.editor_viewport_size
        if viewport_w <= 0 or viewport_h <= 0:
            viewport_w, viewport_h = editor_area[2], editor_area[3]

        viewport_w = min(viewport_w, editor_surface.get_width())
        viewport_h = min(viewport_h, editor_surface.get_height())
        max_x = max(0, editor_surface.get_width() - viewport_w)
        max_y = max(0, editor_surface.get_height() - viewport_h)
        pan_x = max(0, min(max_x, context.sim.editor.pan_x))
        pan_y = max(0, min(max_y, context.sim.editor.pan_y))

        rect = pygame.Rect(pan_x, pan_y, viewport_w, viewport_h)
        region = editor_surface.subsurface(rect).copy()
        scaled = pygame.transform.smoothscale(region, (editor_area[2], editor_area[3]))
        context.blit(scaled, (editor_area[0], editor_area[1]))

    _blit_overlay_panels(screen)


def _blit_overlay_panels(screen) -> None:
    """Render graph/evaluation overlays when their toggles are enabled."""
    # Import the submodules and call their functions via the module attribute
    # so that test monkeypatches such as `monkeypatch.setattr(engine.graphs, ...)`
    # affect the behavior here. This is more robust than referencing imported
    # symbols captured at module import time.
    from . import graphs as _graphs
    from . import evaluation_ui as _evaluation_ui
    import sys

    # Prefer module attributes attached to this engine module (tests may
    # monkeypatch `engine.graphs` / `engine.evaluation_ui`). Fall back to the
    # imported modules above when those attributes are absent.
    _mod = sys.modules.get(__name__)
    _graphs_mod = getattr(_mod, "graphs", _graphs)
    _evaluation_mod = getattr(_mod, "evaluation_ui", _evaluation_ui)

    overlays = []

    # render_graph_panel may be a zero-arg legacy function (tests monkeypatch
    # it that way) or a context-accepting function. Try zero-arg first, then
    # fall back to passing a context/module object.
    graph_surface = None
    try:
        graph_surface = _graphs_mod.render_graph_panel()
    except TypeError:
        try:
            graph_surface = _graphs_mod.render_graph_panel(context)
        except Exception:
            # If that still fails, give up and treat as no surface
            graph_surface = None
    if graph_surface is not None:
        overlays.append(graph_surface)

    # evaluation_ui.get_evaluation_surface is also patched by tests via
    # engine.evaluation_ui; call through the module attribute to respect
    # monkeypatches.
    try:
        evaluation_surface = _evaluation_mod.get_evaluation_surface()
    except TypeError:
        try:
            evaluation_surface = _evaluation_mod.get_evaluation_surface(context)
        except Exception:
            evaluation_surface = None
    if evaluation_surface is not None:
        overlays.append(evaluation_surface)

    if not overlays:
        return

    margin = 16
    spacing = 12
    anchor_x = screen.get_width() - margin
    y = margin

    for overlay_surface in overlays:
        width, height = overlay_surface.get_size()
        screen.blit(overlay_surface, (anchor_x - width, y))
        y += height + spacing


# ============================================================================
# Exit and Signal Handling
# ============================================================================


def sim_exit(context: AppContext, val: int) -> None:
    """
    Signal that the simulation should exit.

    Ported from sim_exit() in sim.c.

    Args:
        val: Exit code
    """
    # global tk_must_exit, exit_return
    context.tk_must_exit = True
    context.exit_return = val


def sim_really_exit(context: AppContext, val: int) -> None:
    """
    Actually exit the simulation.

    Ported from sim_really_exit() in sim.c.

    Args:
        val: Exit code
        :param context:
    """
    # Stop any running simulation
    DoStopMicropolis(context)
    sys.exit(val)


def SignalExitHandler(context: AppContext, signum: int, frame) -> None:
    """
    Handle Unix signals for graceful shutdown.

    Ported from SignalExitHandler() in sim.c.
    :param context:
    """
    print("\nMicropolis has been terminated by a signal.")
    print("Exiting gracefully...")
    sim_really_exit(context, -1)


def signal_init(context: AppContext) -> Result[None, Exception]:
    """
    Initialize signal handlers.

    Ported from signal_init() in sim.c.
    """
    try:
        # Only set up signals that are commonly available
        signal.signal(signal.SIGINT, SignalExitHandler)
        signal.signal(signal.SIGTERM, SignalExitHandler)
        # Other signals may not be available on all platforms
    except (OSError, ValueError, AttributeError) as e:
        # Signals may not be available in some environments
        logger.exception("Failed to set up signal handlers.")
        return Err(e)
    return Ok(None)


# ============================================================================
# Simulation Initialization
# ============================================================================


def sim_init(context: AppContext) -> Result[None, Exception]:
    """
    Initialize the simulation system.

    Ported from sim_init() in sim.c.
    """
    # Initialize signal handlers
    result = signal_init(context)
    if result.is_err():
        return result

    # Create the global simulation instance with all required views
    from .sim import MakeNewSim

    context.sim = MakeNewSim(context)

    # Verify that views have surfaces initialized
    if context.sim.editor and context.sim.editor.surface is None:
        logger.debug(
            "Editor view surface not yet initialized (will be set during graphics setup)"
        )
    if context.sim.map and context.sim.map.surface is None:
        logger.debug(
            "Map view surface not yet initialized (will be set during graphics setup)"
        )

    # Initialize simulation state
    # types.UserSoundOn = 1
    # types.MustUpdateOptions = 1
    # types.HaveLastMessage = 0
    # types.ScenarioID = 0
    # types.StartingYear = 1900
    # types.tileSynch = 0x01
    # global sim_skips, sim_skip
    # sim_skips = sim_skip = 0
    # types.autoGo = 1
    # types.CityTax = 7
    # types.CityTime = 50
    # types.NoDisasters = 0
    # types.PunishCnt = 0
    # types.autoBulldoze = 1
    # types.autoBudget = 1
    # types.MesNum = 0
    # types.LastMesTime = 0
    # types.flagBlink = 1
    # types.SimSpeed = 3

    # Initialize various systems
    # InitializeSound(context)
    initialize_sound(context)
    init_map_arrays(context)
    initGraphs(context)
    InitFundingLevel(context)
    setUpMapProcs(context)
    StopEarthquake(context)
    ResetMapState(context)
    ResetEditorState(context)
    ClearMap(context)
    InitWillStuff(context)
    SetFunds(context, 0)
    SetGameLevelFunds(context, context.startup_game_level)
    setSpeed(context, 0)
    setSkips(context, 0)

    return Ok(None)


# ============================================================================
# Simulation Update Functions
# ============================================================================


def sim_update(context: AppContext) -> Result[None, Exception]:
    """
    Update all simulation views and systems.

    Ported from sim_update() in sim.c.
    """
    # global flagBlink

    now_time = time.time()
    context.flag_blink = 1 if (now_time % 1.0) < 0.5 else -1

    if context.sim_speed and not context.heat_steps:
        # global tiles_animated
        context.tiles_animated = 0

    sim_update_editors(context)
    sim_update_maps(context)
    sim_update_graphs(context)
    sim_update_budgets(context)
    sim_update_evaluations(context)

    UpdateFlush()

    return Ok(None)


def sim_update_editors(context: AppContext) -> None:
    """
    Update all editor views.

    Ported from sim_update_editors() in sim.c.
    """
    if not context.sim:
        logger.warning("sim_update_editors called but context.sim is None - skipping")
        return

    view = context.sim.editor
    while view:
        # Mark view as invalid to force redraw
        view.invalid = True
        DoUpdateEditor(view, context)
        view = view.next

    DoUpdateHeads()


def sim_update_maps(context: AppContext) -> None:
    """
    Update all map views.

    Ported from sim_update_maps() in sim.c.
    """
    if not context.sim:
        logger.warning("sim_update_maps called but context.sim is None - skipping")
        return

    view = context.sim.map
    while view:
        must_update_map = (
            context.new_map_flags[view.map_state]
            or context.new_map
            or context.shake_now
        )
        if must_update_map:
            view.invalid = True

        if view.invalid:
            if must_update_map:
                pass  # Could add skip logic here
            if DoUpdateMap(context, view):
                pass  # Could handle redraw cancellation here

        view = view.next

    context.new_map = 0
    for i in range(NMAPS):
        context.new_map_flags[i] = 0


def sim_update_graphs(context: AppContext) -> None:
    """
    Update graph displays.

    Ported from sim_update_graphs() in sim.c.
    :param context:
    """
    graphDoer(context)


def sim_update_budgets(context: AppContext) -> None:
    """
    Update budget displays.

    Ported from sim_update_budgets() in sim.c.
    :param context:
    """
    if context.sim_skips != 0 and context.sim_skip != 0:
        return

    UpdateBudgetWindow()


def sim_update_evaluations(context: AppContext) -> None:
    """
    Update evaluation displays.

    Ported from sim_update_evaluations() in sim.c.
    """
    if context.sim_skips != 0 and context.sim_skip != 0:
        return

    scoreDoer()


# ============================================================================
# Heat Simulation (Experimental Feature)
# ============================================================================


def sim_heat(context: AppContext) -> None:
    """
    Run heat/cellular automata simulation.

    Ported from sim_heat() in sim.c.
    This appears to be an experimental feature for cellular automata simulation.
    """
    # global CellSrc, CellDst

    if context.cell_src is None:
        # Initialize heat simulation arrays
        size = (WORLD_X + 2) * (WORLD_Y + 2)
        context.cell_src = [0] * size
        context.cell_dst = context.map_data[0]  # Point to main map

    # Heat simulation implementation would go here
    # This is a complex cellular automata system that appears experimental
    # For now, we'll leave it as a placeholder
    pass


# ============================================================================
# Main Simulation Loop
# ============================================================================


def sim_timeout_loop(context: AppContext, doSim: bool) -> None:
    """
    Main timeout loop for simulation.

    Ported from sim_timeout_loop() in sim.c.

    Args:
        doSim: Whether to run simulation step
    """
    if context.sim_speed:
        sim_loop(context, doSim)
    DoTimeoutListen()


def sim_loop(context: AppContext, doSim: bool) -> None:
    """
    Main simulation loop iteration.

    Ported from sim_loop() in sim.c.

    Args:
        doSim: Whether to run simulation step
        :param context:
    """
    # global sim_loops

    if context.heat_steps:
        # Run heat simulation steps
        for j in range(context.heat_steps):
            sim_heat(context)
        MoveObjects()
        context.new_map = 1
    else:
        # Run normal simulation
        if doSim:
            sim_frame(context)
        MoveObjects()

    context.sim_loops += 1
    sim_update(context)


# ============================================================================
# Utility Functions (Placeholders)
# ============================================================================


def DoStopMicropolis(context: AppContext) -> None:
    """Stop the Micropolis simulation and clean up all resources.

    This function performs a complete teardown of the game including:
    - Setting exit flag to stop the main loop
    - Stopping all pygame timers
    - Shutting down audio system and releasing mixer channels
    - Cleaning up graphics resources
    - Stopping tkinter bridge resources
    - Clearing event bus subscriptions
    - Resetting global state variables

    After calling this function, the pygame loop should exit cleanly.

    Ported from DoStopMicropolis() in w_x.c
    :param context: Application context
    """
    logger.info("Stopping Micropolis...")

    # Set exit flag to stop main loop
    context.tk_must_exit = True
    context.running = False

    # Stop all pygame timers
    try:
        from .constants import SIM_TIMER_EVENT, EARTHQUAKE_TIMER_EVENT, UPDATE_EVENT

        pygame.time.set_timer(SIM_TIMER_EVENT, 0)
        pygame.time.set_timer(EARTHQUAKE_TIMER_EVENT, 0)
        pygame.time.set_timer(UPDATE_EVENT, 0)
        logger.debug("Stopped all pygame timers")
    except Exception as e:
        logger.warning(f"Error stopping timers: {e}")

    # Stop and clean up tkinter bridge resources
    try:
        from . import tkinter_bridge

        tkinter_bridge.tk_main_cleanup(context)
        logger.debug("Cleaned up tkinter bridge")
    except Exception as e:
        logger.warning(f"Error cleaning up tkinter bridge: {e}")

    # Shutdown audio system and release mixer channels
    try:
        from . import audio

        audio.shutdown_sound(context)
        logger.debug("Shut down audio system")
    except Exception as e:
        logger.warning(f"Error shutting down audio: {e}")

    # Clean up graphics resources
    try:
        from . import graphics_setup

        graphics_setup.cleanup_graphics()
        logger.debug("Cleaned up graphics")
    except Exception as e:
        logger.warning(f"Error cleaning up graphics: {e}")

    # Clear event bus subscriptions
    try:
        from .ui.event_bus import get_default_event_bus

        event_bus = get_default_event_bus()
        event_bus.clear()
        logger.debug("Cleared event bus")
    except Exception as e:
        logger.warning(f"Error clearing event bus: {e}")

    # Reset simulation state flags
    context.sim_paused = 0
    context.sim_paused_speed = 3

    logger.info("Micropolis stopped successfully")


# def InitializeSound() -> None:
#     """Initialize sound system using pygame mixer"""
#     from . import audio

#     audio.initialize_sound()


def initGraphs(context: AppContext) -> None:
    """Initialize graphs (placeholder)
    :param context:
    """
    pass


def InitFundingLevel(context: AppContext) -> None:
    """
    Initialize funding levels for city services.

    Sets up the initial budget allocations for police, fire, and road services
    based on the game difficulty level.

    Ported from InitFundingLevel() in w_budget.c and initialization.py.
    :param context: Application context containing budget state
    """
    # Set default funding percentages (100% for roads initially)
    context.road_percent = 1.0
    context.police_percent = 0.0
    context.fire_percent = 0.0

    # Set maximum values for budget sliders
    context.road_max_value = 100
    context.police_max_value = 100
    context.fire_max_value = 100

    # Set effects (how much funding provides coverage)
    context.road_effect = 32
    context.police_effect = 1000
    context.fire_effect = 1000

    # Initialize tax and fund values
    context.city_tax = 7  # 7% default tax rate
    context.road_fund = 0
    context.police_fund = 0
    context.fire_fund = 0
    context.tax_fund = 0

    # Set initial funds based on difficulty level
    SetFunds(context, DEFAULT_STARTING_FUNDS)
    SetGameLevelFunds(context, context.startup_game_level)


def setUpMapProcs(context: AppContext) -> None:
    """
    Initialize the map procedure array with all drawing functions.

    Registers callback functions for each overlay type (residential, commercial,
    industrial, power, traffic, pollution, crime, etc.) that the map view uses
    to render different visualization modes.

    Ported from setUpMapProcs() in map_view.py.
    :param context: Application context containing mapProcs array
    """
    from . import map_view

    # Register all overlay drawing functions
    context.mapProcs[ALMAP] = map_view.drawAll
    context.mapProcs[REMAP] = map_view.drawRes
    context.mapProcs[COMAP] = map_view.drawCom
    context.mapProcs[INMAP] = map_view.drawInd
    context.mapProcs[PRMAP] = map_view.drawPower
    context.mapProcs[RDMAP] = map_view.drawLilTransMap
    context.mapProcs[PDMAP] = map_view.drawPopDensity
    context.mapProcs[RGMAP] = map_view.drawRateOfGrowth
    context.mapProcs[TDMAP] = map_view.drawTrafMap
    context.mapProcs[PLMAP] = map_view.drawPolMap
    context.mapProcs[CRMAP] = map_view.drawCrimeMap
    context.mapProcs[LVMAP] = map_view.drawLandMap
    context.mapProcs[FIMAP] = map_view.drawFireRadius
    context.mapProcs[POMAP] = map_view.drawPoliceRadius
    context.mapProcs[DYMAP] = map_view.drawDynamic


def StopEarthquake(context: AppContext) -> None:
    """Stop earthquake effect (placeholder)
    :param context:
    """
    pass


def ResetMapState(context: AppContext) -> None:
    """Reset map view states (placeholder)
    :param context:
    """
    initialization.ResetMapState(context)


def ResetEditorState(context: AppContext) -> None:
    """Reset editor view states (placeholder)
    :param context:
    """
    initialization.ResetEditorState(context)


def ClearMap(context: AppContext) -> None:
    """
    Clear the entire map and initialize to dirt tiles.

    This function resets the map to a clean state with all dirt tiles,
    which can then be used as a base for terrain generation.

    Ported from ClearMap() in s_gen.c via generation.py.
    :param context: Application context containing map data
    """
    # Clear all map cells to DIRT
    for x in range(WORLD_X):
        for y in range(WORLD_Y):
            context.map_data[x][y] = DIRT

    # Mark map as changed/new
    context.new_map = 1

    # Log for debugging
    logging.info("Map cleared - all tiles set to DIRT")


def SetFunds(context: AppContext, amount: int) -> None:
    """
    Set the city's total funds to a specific amount.

    Ensures the amount is never negative and updates both current and
    last funds values for comparison tracking.

    :param context: Application context containing fund state
    :param amount: The new fund amount (will be clamped to >= 0)
    """
    # Ensure funds are never negative
    context.total_funds = max(0, amount)
    context.last_funds = context.total_funds

    # Log for debugging
    logging.debug(f"Funds set to: ${context.total_funds}")


def SetGameLevelFunds(context: AppContext, level: int) -> None:
    """
    Set initial funds based on game difficulty level.

    Difficulty levels:
    - 0 (Easy): $20,000
    - 1 (Medium): $10,000
    - 2 (Hard): $5,000

    :param context: Application context containing fund state
    :param level: Game difficulty level (0=Easy, 1=Medium, 2=Hard)
    """
    # Map difficulty levels to starting funds
    level_funds = [20000, 10000, 5000]

    # Clamp level to valid range
    bounded_level = max(0, min(level, len(level_funds) - 1))

    # Set funds based on difficulty
    SetFunds(context, level_funds[bounded_level])

    # Log for debugging
    difficulty_names = ["Easy", "Medium", "Hard"]
    difficulty_name = (
        difficulty_names[bounded_level]
        if bounded_level < len(difficulty_names)
        else "Unknown"
    )
    logging.info(
        f"Game level set to {bounded_level} ({difficulty_name}) - Starting funds: ${level_funds[bounded_level]}"
    )


def setSpeed(context: AppContext, speed: int) -> int:
    """Set simulation speed
    :param speed:
    :param context:
    """
    context.sim_speed = speed
    return 0


def setSkips(context: AppContext, skips: int) -> int:
    """Set simulation skips"""
    # global sim_skips
    context.sim_skips = skips
    return 0


def graphDoer(context: AppContext) -> None:
    """Update graph history buffers and refresh pygame overlays.
    :param context:
    """
    update_all_graphs(context)
    request_graph_panel_redraw(context)


def UpdateBudgetWindow() -> None:
    """Update budget window (placeholder)"""
    pass


def scoreDoer(context: AppContext) -> None:
    """Update evaluation data and pygame panel state."""
    from .evaluation_ui import score_doer as eval_score_doer, update_evaluation

    eval_score_doer(context)
    update_evaluation(context)


def UpdateFlush() -> None:
    """Flush updates (placeholder)"""
    pass


def DoUpdateEditor(context: AppContext, view) -> None:
    """Update editor view
    :param context:
    :param view:
    """
    do_update_editor(context, context.sim.editor)


def DoUpdateHeads() -> None:
    """Update header displays (placeholder)"""
    pass


def DoUpdateMap(context: AppContext, view) -> bool:
    """Update map view (placeholder)
    :param context:
    :param view:
    """
    if not view or not view.visible:
        return False

    MemDrawMap(context, view)
    view.invalid = False
    return True


def MoveObjects() -> None:
    """Move simulation objects (placeholder)"""
    pass


def DoTimeoutListen() -> None:
    """Handle timeout events (placeholder)"""
    pass


# ============================================================================
# Command Line Argument Parsing
# ============================================================================


# def parse_arguments() -> argparse.Namespace:
#     """
#     Parse command line arguments.
#
#     Adapted from main() argument parsing in sim.c.
#     """
#     parser = argparse.ArgumentParser(
#         description="Micropolis City Simulation",
#         formatter_class=argparse.RawDescriptionHelpFormatter,
#         epilog="""
# Game levels: 1: Easy, 2: Medium, 3: Hard
# Scenarios: 1: Dullsville, 2: San_Francisco, 3: Hamburg, 4: Bern,
#            5: Tokyo, 6: Detroit, 7: Boston, 8: Rio_de_Janeiro
#         """,
#     )
#
#     parser.add_argument(
#         "-g",
#         "--generate",
#         action="store_true",
#         help="Generate new terrain and start playing",
#     )
#
#     parser.add_argument(
#         "-l",
#         "--level",
#         type=str,
#         choices=["1", "easy", "2", "medium", "3", "hard"],
#         help="Game difficulty level",
#     )
#
#     parser.add_argument(
#         "-s",
#         "--scenario",
#         type=str,
#         choices=[
#             "1",
#             "Dullsville",
#             "2",
#             "San_Francisco",
#             "3",
#             "Hamburg",
#             "4",
#             "Bern",
#             "5",
#             "Tokyo",
#             "6",
#             "Detroit",
#             "7",
#             "Boston",
#             "8",
#             "Rio_de_Janeiro",
#         ],
#         help="Start with specific scenario",
#     )
#
#     parser.add_argument(
#         "-w",
#         "--wire-mode",
#         action="store_true",
#         help="Use networking mode (no shared memory)",
#     )
#
#     parser.add_argument(
#         "-m", "--multiplayer", action="store_true", help="Enable multiplayer mode"
#     )
#
#     parser.add_argument(
#         "-S",
#         "--sugar",
#         action="store_true",
#         help="Enable OLPC Sugar interface integration",
#     )
#
#     parser.add_argument(
#         "filename", nargs="?", help="City file to load (.cty) or new city name"
#     )
#
#     args = parser.parse_args()
#
#     # Process level argument
#     if args.level:
#         level_map = {"1": 0, "easy": 0, "2": 1, "medium": 1, "3": 2, "hard": 2}
#         # global startup_game_level
#         context.startup_game_level = level_map[args.level.lower()]
#
#     # Process scenario argument
#     if args.scenario:
#         scenario_map = {
#             "1": 1,
#             "Dullsville": 1,
#             "2": 2,
#             "San_Francisco": 2,
#             "3": 3,
#             "Hamburg": 3,
#             "4": 4,
#             "Bern": 4,
#             "5": 5,
#             "Tokyo": 5,
#             "6": 6,
#             "Detroit": 6,
#             "7": 7,
#             "Boston": 7,
#             "8": 8,
#             "Rio_de_Janeiro": 8,
#         }
#         global startup
#         startup = scenario_map[args.scenario]
#
#     # Process other flags
#     global wire_mode, multi_player_mode, SugarMode
#     if args.wire_mode:
#         wire_mode = 1
#     if args.multiplayer:
#         multi_player_mode = 1
#     if args.sugar:
#         SugarMode = 1
#
#     # Process filename
#     if args.filename:
#         global startup_name
#         if args.generate:
#             # Generate new city with given name
#             startup = -1
#             startup_name = args.filename
#         else:
#             # Load existing city file
#             startup = -2
#             startup_name = args.filename
#
#     return args


# ============================================================================
# Main Entry Point
# ============================================================================


def main() -> int:
    """
    Main entry point for Micropolis.

    Adapted from main() in sim.c for Python environment.
    """
    logger.info(f"Welcome to Python Micropolis version {MICROPOLIS_VERSION}")
    logger.info("Copyright (C) 2002 by Electronic Arts, Maxis. All rights reserved.")

    app_config: AppConfig = AppConfig()
    context: AppContext = AppContext(config=app_config)

    result = sim_init(context)
    if result.is_err():
        logger.error(f"Simulation initialization error: {result.unwrap_err()}")
        return -1

    # Start the main pygame loop (placeholder for now)
    result = pygame_main_loop(context)
    if result.is_err():
        logger.error(f"Simulation error: {result.unwrap_err()}")
        return -1

    return 0


def ensure_sim_structures():
    pass


def pygame_main_loop(context: AppContext) -> Result[None, Exception]:
    """
    Main pygame event loop.

    This replaces the TCL/Tk main loop from the original C version.
    :param context:
    """
    logger.debug("Initializing pygame graphics...")
    event_bus = get_default_event_bus()
    input_manager = None
    keybindings_overlay = None
    dispatcher = None
    panel_manager = None

    # Initialize graphics
    if not init_graphics(context):
        return Err(ValueError("Failed to initialize graphics"))

    # Set up display
    try:
        input_manager = get_default_input_binding_manager(context=context)
        keybindings_overlay = KeybindingsOverlay(input_manager)
        dispatcher = InputActionDispatcher(
            context,
            input_manager,
            on_show_keybindings=keybindings_overlay.toggle,
        )
        # import pygame

        # global editor_viewport_size

        # Set up a basic window
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Micropolis Python")
        map_area = (16, 16, MAP_W, MAP_H)
        preview_width = screen.get_width() // 2
        preview_height = screen.get_height() // 2
        editor_area = (
            screen.get_width() - preview_width - 16,
            screen.get_height() - preview_height - 16,
            preview_width,
            preview_height,
        )
        context.editor_viewport_size = (preview_width, preview_height)
        tool_hotkeys = {
            pygame.K_r: context.RESBASE,
            pygame.K_c: context.COMBASE,
            pygame.K_i: context.INDBASE,
            pygame.K_p: context.POWERBASE,
        }

        ensure_sim_structures()

        # Wire SimView instances to pygame surfaces and load tile graphics
        result = initialize_view_surfaces(context)
        if result.is_err():
            logger.error(f"Failed to initialize view surfaces: {result.unwrap_err()}")
            return Err(result.unwrap_err())

        # Initialize PanelManager and register editor panel
        panel_manager = PanelManager(context, surface=screen, event_bus=event_bus)

        # Register EditorPanel factory
        def editor_panel_factory(
            manager: PanelManager, context: AppContext, **factory_kwargs
        ) -> EditorPanel:
            return EditorPanel(manager, context)

        panel_manager.register_panel_type("EditorWindows", editor_panel_factory)

        # Register ToolPalettePanel factory (if needed)
        def tool_palette_factory(
            manager: PanelManager, context: AppContext, **factory_kwargs
        ) -> ToolPalettePanel:
            return ToolPalettePanel(manager, context)

        panel_manager.register_panel_type("ToolPalette", tool_palette_factory)

        # Create editor panel instance
        try:
            editor_panel = panel_manager.create_panel(
                "EditorWindows", panel_id="main-editor"
            )
            # Position the editor panel (set rect attribute if UIPanel supports it)
            if hasattr(editor_panel, "rect"):
                editor_panel.rect = editor_area  # type: ignore
            # Resize the panel to match viewport
            editor_panel.on_resize(context.editor_viewport_size)
            logger.info("Editor panel created and registered successfully")
        except Exception as e:
            logger.error(f"Failed to create editor panel: {e}")
            # Continue without editor panel for now

        sim_update(context)
        blit_views_to_screen(context, screen, map_area, editor_area)
        pygame.display.flip()

        logger.info("Pygame window initialized. Press Ctrl+C to exit")

        clock = pygame.time.Clock()

        try:
            while not context.tk_must_exit:
                # Handle pygame events
                for event in pygame.event.get():
                    overlay_consumed = False
                    overlay_active_before = keybindings_overlay.visible
                    if overlay_active_before:
                        overlay_consumed = keybindings_overlay.handle_event(event)
                        if overlay_consumed:
                            continue

                    event_bus.publish_pygame_event(event)
                    overlay_block = overlay_active_before or keybindings_overlay.visible

                    if event.type == pygame.QUIT:
                        logger.info("Quit event received")
                        DoStopMicropolis(context)
                        break

                    if overlay_block:
                        continue

                    # Route event through PanelManager first (if panels consume it, skip fallback handling)
                    panel_consumed = False
                    if panel_manager is not None:
                        try:
                            panel_consumed = panel_manager.handle_event(event)
                        except Exception as e:
                            logger.error(f"Error handling event in PanelManager: {e}")

                    if panel_consumed:
                        continue  # Panel handled the event, don't process further

                    # Fallback keyboard/mouse handling (legacy behavior)
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            logger.info("Escape key pressed")
                            DoStopMicropolis(context)
                            break
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            pan_editor_view(
                                context, -32, 0, context.editor_viewport_size
                            )
                            continue
                        if event.key in (pygame.K_RIGHT, pygame.K_d):
                            pan_editor_view(
                                context, 32, 0, context.editor_viewport_size
                            )
                            continue
                        if event.key in (pygame.K_UP, pygame.K_w):
                            pan_editor_view(
                                context, 0, -32, context.editor_viewport_size
                            )
                            continue
                        if event.key in (pygame.K_DOWN, pygame.K_s):
                            pan_editor_view(
                                context, 0, 32, context.editor_viewport_size
                            )
                            continue
                        if handle_tool_hotkey(context, event.key, tool_hotkeys):
                            continue
                        if handle_keyboard_shortcut(context, event.key):
                            continue
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if handle_map_click(
                            context, context.sim, event.pos, map_area, event.button
                        ):
                            continue

                event_bus.flush()

                if context.tk_must_exit:
                    break

                # Update simulation step and redraw
                sim_loop(context, True)
                blit_views_to_screen(context, screen, map_area, editor_area)

                # Render panels if PanelManager is active
                if panel_manager is not None:
                    try:
                        panel_manager.render(screen)
                    except Exception as e:
                        logger.error(f"Error rendering panels: {e}")

                keybindings_overlay.render(screen)
                pygame.display.flip()

                # Maintain 60 FPS
                clock.tick(60)

        except KeyboardInterrupt:
            return Err(RuntimeError("Interrupted by user"))

    except Exception as e:
        return Err(Exception(f"Error in pygame main loop: {e}"))

    finally:
        # Clean up
        if dispatcher is not None:
            dispatcher.shutdown()
        if input_manager is not None:
            input_manager.shutdown()
        pygame.quit()

    return Ok(None)


# NONE
