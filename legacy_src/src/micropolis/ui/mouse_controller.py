"""
mouse_controller.py - Mouse input controller for Micropolis pygame UI

Handles mouse events (click, drag, wheel) with state management for different
interaction modes (tool application, panning, selection, etc.).
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum, auto
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from ..context import AppContext


class MouseButton(Enum):
    """Mouse button enumeration."""

    LEFT = 1
    MIDDLE = 2
    RIGHT = 3
    WHEEL_UP = 4
    WHEEL_DOWN = 5


class MouseMode(Enum):
    """Mouse interaction mode."""

    NORMAL = auto()  # Default cursor/tool mode
    PANNING = auto()  # Right-click drag panning
    PAINTING = auto()  # Left-click drag tool application
    SELECTING = auto()  # Shift+drag rectangle selection
    CHALKING = auto()  # Middle-click chalk annotation


class MouseInputController:
    """
    Manages mouse input state and dispatches events to handlers.

    Tracks button states, drag operations, and mode transitions.
    """

    def __init__(self, context: AppContext):
        """Initialize mouse input controller."""
        self.context = context
        self.mode: MouseMode = MouseMode.NORMAL

        # Button state tracking
        self.buttons_down: set[MouseButton] = set()
        self.drag_start_pos: tuple[int, int] | None = None
        self.last_pos: tuple[int, int] = (0, 0)
        self.current_pos: tuple[int, int] = (0, 0)

        # Mode-specific state
        self.shift_pressed: bool = False
        self.ctrl_pressed: bool = False
        self.alt_pressed: bool = False

        # Event handlers
        self.on_click: Callable[[tuple[int, int], MouseButton], None] | None = None
        self.on_drag: Callable[[tuple[int, int], tuple[int, int]], None] | None = None
        self.on_drag_end: Callable[[tuple[int, int]], None] | None = None
        self.on_wheel: Callable[[int], None] | None = None
        self.on_hover: Callable[[tuple[int, int]], None] | None = None

    def update_modifiers(self, event: pygame.event.Event) -> None:
        """
        Update modifier key state from event.

        Args:
            event: Pygame event
        """
        mods = pygame.key.get_mods()
        self.shift_pressed = bool(mods & pygame.KMOD_SHIFT)
        self.ctrl_pressed = bool(mods & (pygame.KMOD_CTRL | pygame.KMOD_META))
        self.alt_pressed = bool(mods & pygame.KMOD_ALT)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame mouse event.

        Args:
            event: Pygame event

        Returns:
            True if event was handled
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_button_down(event)
        elif event.type == pygame.MOUSEBUTTONUP:
            return self._handle_button_up(event)
        elif event.type == pygame.MOUSEMOTION:
            return self._handle_motion(event)
        elif event.type == pygame.MOUSEWHEEL:
            return self._handle_wheel(event)

        return False

    def _handle_button_down(self, event: pygame.event.Event) -> bool:
        """Handle mouse button down event."""
        self.update_modifiers(event)

        button = self._get_button(event.button)
        if button is None:
            return False

        self.buttons_down.add(button)
        self.drag_start_pos = event.pos
        self.last_pos = event.pos
        self.current_pos = event.pos

        # Determine mode based on button and modifiers
        if button == MouseButton.LEFT:
            if self.shift_pressed:
                self.mode = MouseMode.SELECTING
            else:
                self.mode = MouseMode.PAINTING
        elif button == MouseButton.MIDDLE:
            self.mode = MouseMode.CHALKING
        elif button == MouseButton.RIGHT:
            self.mode = MouseMode.PANNING

        # Dispatch click event
        if self.on_click:
            self.on_click(event.pos, button)

        return True

    def _handle_button_up(self, event: pygame.event.Event) -> bool:
        """Handle mouse button up event."""
        button = self._get_button(event.button)
        if button is None:
            return False

        self.buttons_down.discard(button)
        self.current_pos = event.pos

        # End drag operation if active
        if self.drag_start_pos is not None:
            if self.on_drag_end:
                self.on_drag_end(event.pos)
            self.drag_start_pos = None

        # Reset mode if no buttons pressed
        if not self.buttons_down:
            self.mode = MouseMode.NORMAL

        return True

    def _handle_motion(self, event: pygame.event.Event) -> bool:
        """Handle mouse motion event."""
        self.last_pos = self.current_pos
        self.current_pos = event.pos

        # Handle drag operations
        if self.drag_start_pos is not None:
            if self.on_drag:
                self.on_drag(self.drag_start_pos, event.pos)
            return True

        # Handle hover
        if self.on_hover:
            self.on_hover(event.pos)
            return True

        return False

    def _handle_wheel(self, event: pygame.event.Event) -> bool:
        """Handle mouse wheel event."""
        if self.on_wheel:
            # Pygame wheel event: y > 0 is up, y < 0 is down
            self.on_wheel(event.y)
            return True

        return False

    def _get_button(self, button_id: int) -> MouseButton | None:
        """Convert pygame button ID to MouseButton enum."""
        button_map = {
            1: MouseButton.LEFT,
            2: MouseButton.MIDDLE,
            3: MouseButton.RIGHT,
            4: MouseButton.WHEEL_UP,
            5: MouseButton.WHEEL_DOWN,
        }
        return button_map.get(button_id)

    def is_dragging(self) -> bool:
        """Check if currently in a drag operation."""
        return self.drag_start_pos is not None

    def get_drag_delta(self) -> tuple[int, int]:
        """
        Get drag delta from start position.

        Returns:
            (dx, dy) pixel delta from drag start
        """
        if self.drag_start_pos is None:
            return 0, 0

        dx = self.current_pos[0] - self.drag_start_pos[0]
        dy = self.current_pos[1] - self.drag_start_pos[1]
        return dx, dy

    def get_drag_distance(self) -> float:
        """
        Get total drag distance from start position.

        Returns:
            Distance in pixels
        """
        dx, dy = self.get_drag_delta()
        return (dx * dx + dy * dy) ** 0.5

    def reset(self) -> None:
        """Reset controller state."""
        self.mode = MouseMode.NORMAL
        self.buttons_down.clear()
        self.drag_start_pos = None
        self.shift_pressed = False
        self.ctrl_pressed = False
        self.alt_pressed = False


class AutoPanController:
    """
    Manages automatic viewport panning when cursor is near edges.

    Provides smooth velocity-based panning with configurable speed and
    edge threshold.
    """

    def __init__(self):
        """Initialize autopan controller."""
        self.enabled: bool = True
        self.edge_threshold: int = 32  # Pixels from edge to trigger
        self.pan_speed: float = 200.0  # Pixels per second
        self.velocity: tuple[float, float] = (0.0, 0.0)
        self.is_active: bool = False

    def update(
        self, mouse_pos: tuple[int, int], viewport_rect: pygame.Rect, dt: float
    ) -> tuple[int, int]:
        """
        Update autopan state and calculate pan delta.

        Args:
            mouse_pos: Current mouse position in screen coordinates
            viewport_rect: Viewport rectangle
            dt: Delta time in seconds

        Returns:
            (dx, dy) pan delta to apply
        """
        if not self.enabled:
            self.velocity = (0.0, 0.0)
            self.is_active = False
            return 0, 0

        x, y = mouse_pos
        vx, vy, vw, vh = viewport_rect

        # Check if mouse is in viewport
        if not viewport_rect.collidepoint(x, y):
            self.velocity = (0.0, 0.0)
            self.is_active = False
            return 0, 0

        # Calculate velocity based on distance from edge
        vel_x, vel_y = 0.0, 0.0

        # Left edge
        if x - vx < self.edge_threshold:
            vel_x = -self.pan_speed
            self.is_active = True
        # Right edge
        elif (vx + vw) - x < self.edge_threshold:
            vel_x = self.pan_speed
            self.is_active = True

        # Top edge
        if y - vy < self.edge_threshold:
            vel_y = -self.pan_speed
            self.is_active = True
        # Bottom edge
        elif (vy + vh) - y < self.edge_threshold:
            vel_y = self.pan_speed
            self.is_active = True

        if not self.is_active:
            self.velocity = (0.0, 0.0)
            return 0, 0

        self.velocity = (vel_x, vel_y)

        # Calculate pan delta
        dx = int(vel_x * dt)
        dy = int(vel_y * dt)

        return dx, dy

    def set_speed(self, speed: float) -> None:
        """Set autopan speed in pixels per second."""
        self.pan_speed = max(0.0, speed)

    def set_edge_threshold(self, threshold: int) -> None:
        """Set edge detection threshold in pixels."""
        self.edge_threshold = max(0, threshold)
