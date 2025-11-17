from typing import Any

import pygame
from pydantic import BaseModel, ConfigDict

from . import view_types
from .constants import ALMAP, EDITOR_H, EDITOR_W, MAP_H, MAP_W, DOZE_STATE
from .context import AppContext
from .sim_sprite import SimSprite
from .terrain import WORLD_X, WORLD_Y


class SimView(BaseModel):
    """View for displaying map/editor"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Basic properties
    title: str = ""
    type: int = 0
    class_id: int = 0  # renamed from 'class' to avoid Python keyword

    # Graphics
    pixels: list[int] = []
    line_bytes: int = 0
    pixel_bytes: int = 0
    depth: int = 0
    data: bytes | None = None
    line_bytes8: int = 0
    data8: bytes | None = None
    visible: bool = False
    invalid: bool = False
    skips: int = 0
    skip: int = 0
    update: bool = False

    # Map display
    smalltiles: bytes | None = None
    map_state: int = 0
    show_editors: bool = False

    # Editor display
    bigtiles: bytes | None = None
    power_type: int = 0
    tool_showing: bool = False
    tool_mode: int = 0
    tool_x: int = 0
    tool_y: int = 0
    tool_x_const: int = 0
    tool_y_const: int = 0
    tool_state: int = 0
    tool_state_save: int = 0
    super_user: bool = False
    show_me: bool = False
    dynamic_filter: int = 0
    tool_event_time: int = 0
    tool_last_event_time: int = 0

    # Scrolling/positioning
    w_x: int = 0
    w_y: int = 0
    w_width: int = 0
    w_height: int = 0
    m_width: int = 0
    m_height: int = 0
    i_width: int = 0
    i_height: int = 0
    pan_x: int = 0
    pan_y: int = 0
    tile_x: int = 0
    tile_y: int = 0
    tile_width: int = 0
    tile_height: int = 0
    screen_x: int = 0
    screen_y: int = 0
    screen_width: int = 0
    screen_height: int = 0

    # Tracking
    orig_pan_x: int = 0
    orig_pan_y: int = 0
    last_x: int = 0
    last_y: int = 0
    last_button: int = 0
    track_info: str = ""
    message_var: str = ""

    # Window system (placeholder for pygame port)
    flags: int = 0

    # Tile cache for rendering optimization (short **tiles in C)
    tiles: list[list[int]] = []

    # X11 display (adapted for pygame)
    x: Any | None = None

    # Timing
    updates: int = 0
    update_real: float = 0.0
    update_user: float = 0.0
    update_system: float = 0.0
    update_context: int = 0

    # Auto goto
    auto_goto: bool = False
    auto_going: bool = False
    auto_x_goal: int = 0
    auto_y_goal: int = 0
    auto_speed: int = 0
    follow: SimSprite | None = None

    # Sound
    sound: bool = False

    # Configuration
    width: int = 0
    height: int = 0

    # Overlay
    show_overlay: bool = False
    overlay_mode: int = 0
    overlay_time: float = 0.0  # Simplified from struct timeval

    surface: pygame.Surface | None = None  # Pygame surface for rendering
    overlay_surface: pygame.Surface | None = None  # Overlay (alpha) surface

    next: "SimView|None" = None


def populate_common_view_fields(
    context: AppContext, view: SimView, width: int, height: int, class_id: int
) -> None:
    # Get or create display object (inlined to avoid circular import)
    if context.main_display is None:
        from .view_types import MakeNewXDisplay

        context.main_display = MakeNewXDisplay()
        context.main_display.color = 1
        context.main_display.depth = 32

    display = context.main_display

    view.class_id = class_id
    view.type = view_types.X_Mem_View
    view.visible = True
    view.invalid = True
    view.x = display
    view.surface = None
    view.width = width
    view.height = height
    view.m_width = width
    view.m_height = height
    view.w_width = width
    view.w_height = height
    view.i_width = width
    view.i_height = height
    view.screen_width = width
    view.screen_height = height
    view.pixel_bytes = 4
    view.line_bytes = width * view.pixel_bytes
    view.map_state = ALMAP
    view.tile_x = 0
    view.tile_y = 0
    view.tile_width = WORLD_X
    view.tile_height = WORLD_Y
    view.pan_x = 0
    view.pan_y = 0
    view.next = None


def create_editor_view(context: AppContext) -> SimView:
    view = SimView()
    view.tool_state = DOZE_STATE
    view.tool_state_save = -1
    # _populate_common_view_fields(
    #     view, types.EDITOR_W, types.EDITOR_H, view_types.Editor_Class
    # )
    populate_common_view_fields(
        context, view, EDITOR_W, EDITOR_H, view_types.Editor_Class
    )
    from .editor_view import initialize_editor_tiles

    initialize_editor_tiles(view)
    return view


def create_map_view(context: AppContext) -> SimView:
    view = SimView()
    # _populate_common_view_fields(
    #     view, types.MAP_W, types.MAP_H, view_types.Map_Class
    # )
    populate_common_view_fields(context, view, MAP_W, MAP_H, view_types.Map_Class)

    return view


# END OF FILE
