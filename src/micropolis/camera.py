"""
camera.py - Cellular Automata Camera System

This module provides stub implementations for the cellular automata camera
visualization system from the original Micropolis. This was an optional
feature that allowed users to create and view cellular automata simulations.

The original system included:
- SimCam: Simulation camera widget with X11 integration
- Cam: Individual cellular automata with rules and buffers
- Can: Canvas/buffer structures for CA state
- Various CA rules (Life, etc.) and visualization

Since this is an advanced optional feature not core to Micropolis gameplay,
this implementation provides stub functions that maintain API compatibility
but do not implement the full cellular automata simulation engine.

Adapted from w_cam.c, g_cam.c, and cam.h for the Python/pygame port.
"""


from collections.abc import Callable
import pygame

from src.micropolis.context import AppContext


# ============================================================================
# Data Structures (from cam.h)
# ============================================================================

class Can:
    """
    Canvas/buffer structure for cellular automata state.

    In the original C code, this represented a 2D buffer of bytes
    with dimensions and memory layout information.
    """
    def __init__(self, width: int = 0, height: int = 0,
                 mem: bytearray | None = None, line_bytes: int = 0):
        self.width: int = width
        self.height: int = height
        self.line_bytes: int = line_bytes or width
        self.mem: bytearray = mem or bytearray(width * height)

    def get_pixel(self, x: int, y: int) -> int:
        """Get pixel value at coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.mem[y * self.line_bytes + x]
        return 0

    def set_pixel(self, x: int, y: int, value: int) -> None:
        """Set pixel value at coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.mem[y * self.line_bytes + x] = value & 0xFF


class Cam:
    """
    Cellular automaton structure.

    Represents an individual CA with front/back buffers, rules,
    position, and simulation parameters.
    """
    def __init__(self):
        self.next: Cam | None = None
        self.back: Can | None = None
        self.front: Can | None = None
        self.neighborhood: Callable | None = None
        self.rule: bytearray = bytearray(256)  # Rule table
        self.rule_size: int = 256
        self.width: int = 0
        self.height: int = 0
        self.ideal_width: int = 0
        self.ideal_height: int = 0
        self.phase: int = 0
        self.wrap: int = 0
        self.steps: int = 0
        self.frob: int = 0
        self.x: int = 0
        self.y: int = 0
        self.dx: int = 0
        self.dy: int = 0
        self.gx: int = 0
        self.gy: int = 0
        self.dragging: int = 0
        self.set_x: int = -1
        self.set_y: int = -1
        self.set_width: int = -1
        self.set_height: int = -1
        self.set_x0: int = -1
        self.set_y0: int = -1
        self.set_x1: int = -1
        self.set_y1: int = -1
        self.name: str | None = None


class SimCam:
    """
    Simulation camera widget structure.

    In the original C code, this managed the X11 display integration
    and contained the list of cellular automata to render.
    """
    def __init__(self):
        self.next: "SimCam | None" = None
        self.w_x: int = 0
        self.w_y: int = 0
        self.w_width: int = 512
        self.w_height: int = 512
        self.visible: bool = False
        self.invalid: bool = True
        self.skips: int = 0
        self.skip: int = 0
        self.surface: pygame.Surface | None = None  # Pygame replacement for X11
        self.line_bytes: int = 0
        self.data: bytearray | None = None
        self.cam_count: int = 0
        self.cam_list: Cam | None = None

# ============================================================================
# Global Variables
# ============================================================================

# Global camera list (stub implementation)
_simcam_list: list[SimCam] = []
_next_cam_id: int = 1


# ============================================================================
# Utility Functions
# ============================================================================

def new_can(width: int, height: int, mem: bytearray | None = None,
            line_bytes: int = 0) -> Can:
    """
    Create a new canvas/buffer.

    Args:
        width: Canvas width
        height: Canvas height
        mem: Optional memory buffer
        line_bytes: Bytes per line

    Returns:
        New Can instance
    """
    return Can(width, height, mem, line_bytes or width)


def new_cam(scam: SimCam, x: int, y: int, width: int, height: int,
            dx: int = 0, dy: int = 0, neighborhood_func: Callable | None = None) -> Cam:
    """
    Create a new cellular automaton.

    Args:
        scam: Parent simulation camera
        x, y: Position
        width, height: Dimensions
        dx, dy: Movement deltas
        neighborhood_func: Neighborhood function

    Returns:
        New Cam instance
    """
    cam = Cam()
    cam.x = x
    cam.y = y
    cam.ideal_width = width
    cam.ideal_height = height

    # Ensure even dimensions
    width = (width + 1) & ~1
    height = (height + 1) & ~1

    cam.width = width
    cam.height = height

    # Create back buffer with border
    back_width = width + 2
    back_height = height + 2
    cam.back = new_can(back_width, back_height,
                       bytearray(back_width * back_height), back_width)

    # Create front buffer pointing into scam's data
    if scam.data and scam.line_bytes > 0:
        offset = y * scam.line_bytes + x
        cam.front = Can(width, height, scam.data[offset:], scam.line_bytes)
    else:
        cam.front = new_can(width, height)

    cam.neighborhood = neighborhood_func
    cam.dx = dx
    cam.dy = dy

    return cam


def find_cam_by_name(scam: SimCam, name: str) -> Cam | None:
    """
    Find a camera by name.

    Args:
        scam: Simulation camera to search
        name: Camera name to find

    Returns:
        Cam instance or None
    """
    cam = scam.cam_list
    while cam:
        if cam.name == name:
            return cam
        cam = cam.next
    return None


def find_cam(scam: SimCam, x: int, y: int) -> Cam | None:
    """
    Find camera at coordinates.

    Args:
        scam: Simulation camera
        x, y: Coordinates

    Returns:
        Cam instance or None
    """
    cam = scam.cam_list
    while cam:
        if (cam.x <= x < cam.x + cam.width and
            cam.y <= y < cam.y + cam.height):
            return cam
        cam = cam.next
    return None


# ============================================================================
# Camera Management Functions
# ============================================================================

def create_simcam(width: int = 512, height: int = 512) -> SimCam:
    """
    Create a new simulation camera.

    Args:
        width: Camera width
        height: Camera height

    Returns:
        New SimCam instance
    """
    scam = SimCam()
    scam.w_width = width
    scam.w_height = height
    scam.line_bytes = width
    scam.data = bytearray(width * height)

    # Create pygame surface for rendering
    scam.surface = pygame.Surface((width, height))

    # Add to global list
    _simcam_list.append(scam)

    return scam


def destroy_simcam(scam: SimCam) -> None:
    """
    Destroy a simulation camera.

    Args:
        scam: Simulation camera to destroy
    """
    # Remove from global list
    if scam in _simcam_list:
        _simcam_list.remove(scam)

    # Clean up cameras
    cam = scam.cam_list
    while cam:
        next_cam = cam.next
        destroy_cam(scam, cam)
        cam = next_cam


def destroy_cam(scam: SimCam, cam: Cam) -> None:
    """
    Destroy a cellular automaton.

    Args:
        scam: Parent simulation camera
        cam: Camera to destroy
    """
    # Remove from list
    if scam.cam_list == cam:
        scam.cam_list = cam.next
    else:
        prev = scam.cam_list
        while prev and prev.next != cam:
            prev = prev.next
        if prev:
            prev.next = cam.next

    scam.cam_count -= 1


def add_cam_to_simcam(scam: SimCam, cam: Cam) -> None:
    """
    Add a camera to a simulation camera.

    Args:
        scam: Simulation camera
        cam: Camera to add
    """
    cam.next = scam.cam_list
    scam.cam_list = cam
    scam.cam_count += 1


# ============================================================================
# Cellular Automata Functions (Stub Implementations)
# ============================================================================

def cam_set_neighborhood(cam: Cam, rule_number: int) -> None:
    """
    Set camera neighborhood rule.

    Args:
        cam: Camera to configure
        rule_number: Rule number (0-255 for totalistic, etc.)
    """
    # Stub: Set up basic rule table
    # In a full implementation, this would set up different CA rules
    # like Conway's Game of Life, etc.
    for i in range(256):
        # Simple rule: survive with 2-3 neighbors, born with 3
        neighbors = bin(i).count('1')
        if neighbors == 3 or (neighbors == 2 and (i & 1)):
            cam.rule[i] = 1
        else:
            cam.rule[i] = 0


def cam_load_rule(cam: Cam, rule_name: str) -> None:
    """
    Load a named rule.

    Args:
        cam: Camera to configure
        rule_name: Name of the rule to load
    """
    # Stub: Just set a default rule
    cam_set_neighborhood(cam, 0)


def cam_randomize(cam: Cam) -> None:
    """
    Randomize camera state.

    Args:
        cam: Camera to randomize
    """
    if cam.back:
        import random
        for i in range(len(cam.back.mem)):
            cam.back.mem[i] = random.randint(0, 1)


def cam_step(cam: Cam) -> None:
    """
    Step the cellular automaton one generation.

    Args:
        cam: Camera to step
    """
    # Stub: Simple CA step implementation
    if not cam.back or not cam.front:
        return

    # Copy front to back with border
    for y in range(cam.height):
        for x in range(cam.width):
            value = cam.front.get_pixel(x, y)
            cam.back.set_pixel(x + 1, y + 1, value)

    # Apply rules (simplified Moore neighborhood)
    for y in range(cam.height):
        for x in range(cam.width):
            # Count neighbors
            neighbors = 0
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    neighbors += cam.back.get_pixel(x + 1 + dx, y + 1 + dy)

            # Apply rule
            current = cam.back.get_pixel(x + 1, y + 1)
            rule_index = (neighbors << 1) | current
            if rule_index < len(cam.rule):
                new_value = cam.rule[rule_index]
            else:
                new_value = 0

            cam.front.set_pixel(x, y, new_value)


# ============================================================================
# Rendering Functions
# ============================================================================

def render_simcam(scam: SimCam) -> pygame.Surface | None:
    """
    Render simulation camera to pygame surface.

    Args:
        scam: Simulation camera to render

    Returns:
        Pygame surface with rendered cameras
    """
    if not scam.surface:
        return None

    # Clear surface
    scam.surface.fill((0, 0, 0))

    # Render each camera
    cam = scam.cam_list
    while cam:
        if cam.front:
            # Simple rendering: white pixels for alive cells
            for y in range(cam.height):
                for x in range(cam.width):
                    value = cam.front.get_pixel(x, y)
                    if value:
                        color = (255, 255, 255)
                        scam.surface.set_at((cam.x + x, cam.y + y), color)

        cam = cam.next

    return scam.surface


def update_simcam(scam: SimCam) -> None:
    """
    Update simulation camera (step all automata).

    Args:
        scam: Simulation camera to update
    """
    cam = scam.cam_list
    while cam:
        if cam.steps > 0:
            cam_step(cam)
            cam.steps -= 1
        cam = cam.next


# ============================================================================
# Command Interface (Stub)
# ============================================================================

def cam_command(command: str, *args) -> str:
    """
    Process camera commands (stub implementation).

    Args:
        command: Command name
        *args: Command arguments

    Returns:
        Command result string
    """
    # Stub: Return empty string for all commands
    # In a full implementation, this would handle commands like:
    # - newcam, deletecam, configcam, etc.
    return ""


# ============================================================================
# Initialization and Cleanup
# ============================================================================

def initialize_camera_system(context: AppContext) -> None:
    """
    Initialize the camera system.
    Called during program startup.
    """
    # global _simcam_list, _next_cam_id
    context.simcam_list = []
    context.next_cam_id = 1


def cleanup_camera_system() -> None:
    """
    Clean up the camera system.
    Called during program shutdown.
    """
    # Destroy all simulation cameras
    for scam in _simcam_list[:]:  # Copy list to avoid modification during iteration
        destroy_simcam(scam)

    _simcam_list.clear()


# ============================================================================
# Convenience Functions
# ============================================================================

def create_life_camera(scam: SimCam, name: str, x: int, y: int,
                      width: int, height: int) -> Cam:
    """
    Create a Conway's Game of Life camera.

    Args:
        scam: Parent simulation camera
        name: Camera name
        x, y: Position
        width, height: Dimensions

    Returns:
        New Life camera
    """
    cam = new_cam(scam, x, y, width, height)
    cam.name = name
    cam_set_neighborhood(cam, 0)  # Conway's Life rule
    add_cam_to_simcam(scam, cam)
    return cam


def create_random_camera(scam: SimCam, name: str, x: int, y: int,
                        width: int, height: int) -> Cam:
    """
    Create a camera with random initial state.

    Args:
        scam: Parent simulation camera
        name: Camera name
        x, y: Position
        width, height: Dimensions

    Returns:
        New random camera
    """
    cam = create_life_camera(scam, name, x, y, width, height)
    cam_randomize(cam)
    return cam