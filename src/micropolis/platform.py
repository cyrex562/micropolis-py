"""
platform.py - Platform-specific code adapted for pygame

This module provides platform-specific functionality for Micropolis,
adapted from the original X Window System implementation (w_x.c) to work
with pygame. It handles display management, coordinate conversion,
view management, and drawing operations.
"""

from dataclasses import dataclass
from typing import Any

import pygame

from .types import (
    COLOR_BLACK,
    COLOR_LIGHTBROWN,
    COLOR_WHITE,
    EDITOR_H,
    EDITOR_W,
    WORLD_X,
    WORLD_Y,
    Sim,
    SimView,
)
from .view_types import Editor_Class, Map_Class, X_Mem_View

# Color intensity mapping (from original X implementation)
COLOR_INTENSITIES = [
    255,  # COLOR_WHITE
    170,  # COLOR_YELLOW
    127,  # COLOR_ORANGE
    85,   # COLOR_RED
    63,   # COLOR_DARKRED
    76,   # COLOR_DARKBLUE
    144,  # COLOR_LIGHTBLUE
    118,  # COLOR_BROWN
    76,   # COLOR_LIGHTGREEN
    42,   # COLOR_DARKGREEN
    118,  # COLOR_OLIVE
    144,  # COLOR_LIGHTBROWN
    191,  # COLOR_LIGHTGRAY
    127,  # COLOR_MEDIUMGRAY
    63,   # COLOR_DARKGRAY
    0,    # COLOR_BLACK
]


@dataclass
class PygameDisplay:
    """Pygame display information and resources."""
    screen: pygame.Surface | None = None
    width: int = 0
    height: int = 0
    depth: int = 32
    color: bool = True
    pixels: list[pygame.Color] | None = None
    initialized: bool = False

    def __post_init__(self):
        if self.pixels is None:
            self.pixels = []


# Global surface storage for views (since SimView doesn't have surface attributes)
view_surfaces: dict[int, pygame.Surface] = {}
view_overlay_surfaces: dict[int, pygame.Surface] = {}


def initialize_platform() -> bool:
    """
    Initialize pygame platform support.

    Returns:
        bool: True if initialization successful
    """
    global pygame_display

    try:
        pygame.init()
        pygame_display = PygameDisplay()
        pygame_display.initialized = True

        # Set up color palette
        _setup_color_palette()

        return True
    except Exception as e:
        print(f"Failed to initialize pygame platform: {e}")
        return False


def shutdown_platform() -> None:
    """Shutdown pygame platform support."""
    global pygame_display

    if pygame_display and pygame_display.initialized:
        pygame.quit()
        pygame_display = None


def _setup_color_palette() -> None:
    """Set up the color palette for pygame rendering."""
    global pygame_display

    if not pygame_display:
        return

    # Create pygame colors from intensity values
    pygame_display.pixels = []

    for intensity in COLOR_INTENSITIES:
        if pygame_display.color:
            # RGB color
            color = (intensity, intensity, intensity)
        else:
            # Black and white
            color = (255, 255, 255) if intensity > 127 else (0, 0, 0)

        # Convert to pygame color value
        pygame_color = pygame.Color(color[0], color[1], color[2])
        pygame_display.pixels.append(pygame_color)


def set_display_mode(width: int, height: int, fullscreen: bool = False) -> bool:
    """
    Set the pygame display mode.

    Args:
        width: Display width
        height: Display height
        fullscreen: Whether to use fullscreen mode

    Returns:
        bool: True if successful
    """
    global pygame_display

    if not pygame_display or not pygame_display.initialized:
        return False

    try:
        flags = pygame.FULLSCREEN if fullscreen else 0
        screen = pygame.display.set_mode((width, height), flags)
        pygame_display.screen = screen
        pygame_display.width = width
        pygame_display.height = height
        return True
    except Exception as e:
        print(f"Failed to set display mode: {e}")
        return False


def view_to_tile_coords(view: SimView, x: int, y: int) -> tuple[int, int]:
    """
    Convert view coordinates to tile coordinates.

    Args:
        view: The view to convert coordinates for
        x: View X coordinate
        y: View Y coordinate

    Returns:
        Tuple of (tile_x, tile_y)
    """
    # Convert from view coordinates to world coordinates
    world_x = (view.pan_x - ((view.w_width >> 1) - x)) >> 4
    world_y = (view.pan_y - ((view.w_height >> 1) - y)) >> 4

    # Clamp to world bounds
    if world_x < 0:
        world_x = 0
    if world_x >= WORLD_X:
        world_x = WORLD_X - 1
    if world_y < 0:
        world_y = 0
    if world_y >= WORLD_Y:
        world_y = WORLD_Y - 1

    # Clamp to view bounds
    if world_x < view.tile_x:
        world_x = view.tile_x
    if world_x >= view.tile_x + view.tile_width:
        world_x = view.tile_x + view.tile_width - 1
    if world_y < view.tile_y:
        world_y = view.tile_y
    if world_y >= view.tile_y + view.tile_height:
        world_y = view.tile_y + view.tile_height - 1

    # Handle tool constraints
    if view.tool_x_const != -1:
        world_x = view.tool_x_const
    if view.tool_y_const != -1:
        world_y = view.tool_y_const

    return world_x, world_y


def view_to_pixel_coords(view: SimView, x: int, y: int) -> tuple[int, int]:
    """
    Convert view coordinates to pixel coordinates.

    Args:
        view: The view to convert coordinates for
        x: View X coordinate
        y: View Y coordinate

    Returns:
        Tuple of (pixel_x, pixel_y)
    """
    # Convert from view coordinates to world pixel coordinates
    pixel_x = view.pan_x - ((view.w_width >> 1) - x)
    pixel_y = view.pan_y - ((view.w_height >> 1) - y)

    # Clamp to world bounds
    if pixel_x < 0:
        pixel_x = 0
    if pixel_x >= (WORLD_X << 4):
        pixel_x = (WORLD_X << 4) - 1
    if pixel_y < 0:
        pixel_y = 0
    if pixel_y >= (WORLD_Y << 4):
        pixel_y = (WORLD_Y << 4) - 1

    # Clamp to view bounds
    if pixel_x < (view.tile_x << 4):
        pixel_x = (view.tile_x << 4)
    if pixel_x >= ((view.tile_x + view.tile_width) << 4):
        pixel_x = ((view.tile_x + view.tile_width) << 4) - 1
    if pixel_y < (view.tile_y << 4):
        pixel_y = (view.tile_y << 4)
    if pixel_y >= ((view.tile_y + view.tile_height) << 4):
        pixel_y = ((view.tile_y + view.tile_height) << 4) - 1

    # Handle tool constraints
    if view.tool_x_const != -1:
        pixel_x = (view.tool_x_const << 4) + 8
    if view.tool_y_const != -1:
        pixel_y = (view.tool_y_const << 4) + 8

    return pixel_x, pixel_y


def update_flush() -> None:
    """Update display flushing (adapted for pygame - mainly for timing)."""
    # In pygame, we don't need complex flushing like X11
    # This is mainly for timing/synchronization
    if pygame_display and pygame_display.screen:
        pygame.display.flip()


def create_sim_view(title: str, view_class: int, width: int, height: int) -> SimView:
    """
    Create and initialize a new SimView for pygame.

    Args:
        title: View title
        view_class: View class (Editor_Class or Map_Class)
        width: View width
        height: View height

    Returns:
        Initialized SimView
    """
    view = SimView()

    # Basic initialization
    view.title = title
    view.class_id = view_class
    view.visible = False
    view.invalid = False
    view.skips = view.skip = 0
    view.update = False
    view.map_state = 0  # ALMAP equivalent
    view.show_editors = True
    view.tool_showing = False
    view.tool_mode = 0
    view.tool_x = view.tool_y = 0
    view.tool_x_const = view.tool_y_const = -1
    view.tool_state = 0  # dozeState equivalent
    view.tool_state_save = -1
    view.super_user = False
    view.show_me = True
    view.dynamic_filter = False
    view.tool_event_time = 0
    view.tool_last_event_time = 0
    view.w_x = view.w_y = 0
    view.w_width = view.w_height = 16
    view.m_width = view.m_height = 0
    view.i_width = width
    view.i_height = height
    view.pan_x = view.pan_y = 0
    view.tile_x = view.tile_y = 0
    view.tile_width = view.tile_height = 0
    view.screen_x = view.screen_y = 0
    view.screen_width = view.screen_height = 0
    view.last_x = view.last_y = view.last_button = 0
    view.track_info = None
    view.message_var = None
    view.updates = 0
    view.update_real = view.update_user = view.update_system = 0.0
    view.update_context = 0
    view.auto_goto = False
    view.auto_going = False
    view.auto_x_goal = view.auto_y_goal = 0
    view.auto_speed = 75
    view.follow = None
    view.sound = True
    view.width = 0
    view.height = 0
    view.show_overlay = True
    view.overlay_mode = 0

    # Pygame-specific initialization
    view.surface = None
    view.overlay_surface = None

    # Set view type (always use memory surfaces in pygame)
    view.type = X_Mem_View

    # Set up pixels reference (convert pygame colors to int values for compatibility)
    if pygame_display and pygame_display.pixels:
        view.pixels = [color.r * 256*256 + color.g * 256 + color.b for color in pygame_display.pixels]
    else:
        view.pixels = [0] * 16

    # Handle special dimensions
    if width == EDITOR_W:
        width = 256
    if height == EDITOR_H:
        height = 256

    # Set initial pan position
    view.pan_x = width // 2
    view.pan_y = height // 2

    # Resize view to set up surfaces
    resize_sim_view(view, width, height)

    return view


def resize_sim_view(view: SimView, width: int, height: int) -> None:
    """
    Resize a SimView and recreate its surfaces.

    Args:
        view: View to resize
        width: New width
        height: New height
    """
    view.w_width = width
    view.w_height = height

    if view.class_id == Map_Class:
        # Map view - create main surface
        view.m_width = width
        view.m_height = height

        if id(view) not in view_surfaces:
            view_surfaces[id(view)] = pygame.Surface((width, height))
            # Fill with default color
            if pygame_display and pygame_display.pixels:
                fill_color = pygame_display.pixels[COLOR_LIGHTBROWN]
                view_surfaces[id(view)].fill(fill_color)

    else:
        # Editor view - more complex setup
        # Align to 16-pixel boundaries
        view.m_width = (width + 31) & (~15)
        view.m_height = (height + 31) & (~15)

        # Create main surface
        if id(view) not in view_surfaces or view_surfaces[id(view)].get_size() != (view.m_width, view.m_height):
            view_surfaces[id(view)] = pygame.Surface((view.m_width, view.m_height))
            if pygame_display and pygame_display.pixels:
                fill_color = pygame_display.pixels[COLOR_LIGHTBROWN]
                view_surfaces[id(view)].fill(fill_color)

        # Create overlay surface for editor
        if id(view) not in view_overlay_surfaces or view_overlay_surfaces[id(view)].get_size() != (view.m_width, view.m_height):
            view_overlay_surfaces[id(view)] = pygame.Surface((view.m_width, view.m_height), pygame.SRCALPHA)
            view_overlay_surfaces[id(view)].fill((0, 0, 0, 0))  # Transparent

        if view.class_id == Editor_Class:
            # Adjust pan position
            adjust_pan(view)


def destroy_sim_view(view: SimView) -> None:
    """
    Destroy a SimView and clean up its resources.

    Args:
        view: View to destroy
    """
    # Clean up pygame surfaces
    view_id = id(view)
    if view_id in view_surfaces:
        del view_surfaces[view_id]
    if view_id in view_overlay_surfaces:
        del view_overlay_surfaces[view_id]


def pan_view_by(view: SimView, dx: int, dy: int) -> None:
    """
    Pan a view by the specified delta.

    Args:
        view: View to pan
        dx: Delta X
        dy: Delta Y
    """
    pan_view_to(view, view.pan_x + dx, view.pan_y + dy)


def pan_view_to(view: SimView, x: int, y: int) -> None:
    """
    Pan a view to the specified position.

    Args:
        view: View to pan
        x: Target X position
        y: Target Y position
    """
    if view.class_id != Editor_Class:
        return

    # Clamp to bounds
    if x < 0:
        x = 0
    if y < 0:
        y = 0
    if x > view.i_width:
        x = view.i_width - 1
    if y > view.i_height:
        y = view.i_height - 1

    # Update pan position if changed
    if view.pan_x != x or view.pan_y != y:
        view.pan_x = x
        view.pan_y = y
        adjust_pan(view)


def adjust_pan(view: SimView) -> None:
    """
    Adjust view parameters based on pan position.

    Args:
        view: View to adjust
    """
    ww2 = view.w_width >> 1
    wh2 = view.w_height >> 1
    px = view.pan_x
    py = view.pan_y

    # Calculate tile bounds
    view.tile_x = (px - ww2) >> 4
    if view.tile_x < 0:
        view.tile_x = 0

    view.tile_y = (py - wh2) >> 4
    if view.tile_y < 0:
        view.tile_y = 0

    # Calculate tile dimensions
    view.tile_width = (15 + px + ww2) >> 4
    view.tile_height = (15 + py + wh2) >> 4

    # Clamp tile dimensions
    max_tile_width = view.i_width >> 4
    max_tile_height = view.i_height >> 4

    if view.tile_width > max_tile_width:
        view.tile_width = max_tile_width
    view.tile_width -= view.tile_x

    if view.tile_height > max_tile_height:
        view.tile_height = max_tile_height
    view.tile_height -= view.tile_y

    # Clamp to surface bounds
    max_surface_tile_width = view.m_width >> 4
    max_surface_tile_height = view.m_height >> 4

    if view.tile_width > max_surface_tile_width:
        view.tile_width = max_surface_tile_width
    if view.tile_height > max_surface_tile_height:
        view.tile_height = max_surface_tile_height

    # Calculate screen position and size
    view.screen_x = (ww2 - px) + (view.tile_x << 4)
    view.screen_y = (wh2 - py) + (view.tile_y << 4)
    view.screen_width = view.tile_width << 4
    view.screen_height = view.tile_height << 4

    # Mark view as invalid (needs redraw)
    view.overlay_mode = 0
    view.invalid = True


def blit_view_surface(view: SimView, dest_surface: pygame.Surface, dest_x: int, dest_y: int) -> None:
    """
    Blit a view's surface to a destination surface.

    Args:
        view: View to blit
        dest_surface: Destination surface
        dest_x: Destination X position
        dest_y: Destination Y position
    """
    view_id = id(view)
    if view_id in view_surfaces:
        dest_surface.blit(view_surfaces[view_id], (dest_x, dest_y))


def get_display_pixels() -> list[int]:
    """
    Get the display color pixels array.

    Returns:
        List of color values
    """
    if pygame_display and pygame_display.pixels:
        # Convert pygame colors to int values
        return [color.r * 256*256 + color.g * 256 + color.b for color in pygame_display.pixels]
    return []


def is_platform_initialized() -> bool:
    """
    Check if the platform is initialized.

    Returns:
        bool: True if initialized
    """
    return pygame_display is not None and pygame_display.initialized


def get_display_info() -> dict[str, Any]:
    """
    Get information about the current display.

    Returns:
        Dictionary with display information
    """
    if not pygame_display:
        return {}

    return {
        'width': pygame_display.width,
        'height': pygame_display.height,
        'depth': pygame_display.depth,
        'color': pygame_display.color,
        'initialized': pygame_display.initialized
    }


# Ink/Drawing system adapted for pygame
@dataclass
class Ink:
    """Drawing ink for overlay operations."""
    points: list[tuple[int, int]] | None = None
    color: int = COLOR_WHITE
    next_ink: "Ink | None" = None

    def __post_init__(self):
        if self.points is None:
            self.points = []


def new_ink() -> Ink:
    """Create a new ink object for drawing."""
    return Ink()


def start_ink(ink: Ink, x: int, y: int) -> None:
    """Start drawing with ink at the specified position."""
    ink.points = [(x, y)]


def add_ink(ink: Ink, x: int, y: int) -> None:
    """Add a point to the ink drawing."""
    if ink.points:
        last_x, last_y = ink.points[-1]
        if last_x != x or last_y != y:
            ink.points.append((x, y))


def draw_ink(surface: pygame.Surface, ink: Ink) -> None:
    """Draw ink onto a pygame surface."""
    if not ink.points or len(ink.points) < 2:
        return

    if pygame_display and pygame_display.pixels and ink.color < len(pygame_display.pixels):
        color = pygame_display.pixels[ink.color]
        pygame.draw.lines(surface, color, False, ink.points, 2)


def erase_overlay(view: SimView) -> None:
    """Erase the overlay for a view."""
    view_id = id(view)
    if view_id in view_overlay_surfaces:
        view_overlay_surfaces[view_id].fill((0, 0, 0, 0))  # Transparent


# Error handling (simplified for pygame)
def catch_error() -> bool:
    """Check for pygame errors (simplified)."""
    # pygame doesn't have the same error handling as X11
    # This is mainly for compatibility
    return False


def do_stop_micropolis(sim: Sim) -> None:
    """Stop Micropolis and clean up views (adapted for pygame)."""
    # Clean up all view surfaces
    global view_surfaces, view_overlay_surfaces
    view_surfaces.clear()
    view_overlay_surfaces.clear()

    # Reset sim counters
    sim.editors = 0
    sim.maps = 0
    sim.graphs = 0
    sim.sprites = 0


def do_timeout_listen() -> None:
    """Handle timeout events (adapted for pygame event loop)."""
    # In pygame, this would be handled by the main event loop
    # This function is mainly for compatibility
    pass


def make_new_sim() -> Sim:
    """Create a new Sim instance (adapted for pygame)."""
    sim = Sim()
    sim.editors = 0
    sim.editor = None
    sim.maps = 0
    sim.map = None
    sim.graphs = 0
    sim.graph = None
    sim.sprites = 0
    sim.sprite = None
    return sim