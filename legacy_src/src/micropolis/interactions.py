"""
interactions.py - Interactive UI components for Micropolis

This module provides pygame-based interactive widgets that replace
the TCL/Tk interval widget from the original Micropolis implementation.

The Interval class implements a dual-handle range slider that allows
selecting min/max values on a scale, with support for vertical/horizontal
orientation, tick marks, labels, and mouse interaction.
"""

import pygame
from typing import Optional, Callable, Tuple
from enum import Enum


class Orientation(Enum):
    """Orientation for interval widgets"""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class IntervalState(Enum):
    """State of the interval widget"""
    NORMAL = "normal"
    DISABLED = "disabled"


class Interval:
    """
    A dual-handle range slider widget for pygame.

    This replaces the TCL/Tk "interval" widget from w_inter.c,
    providing a pygame-based implementation with similar functionality.
    """

    def __init__(self,
                 rect: pygame.Rect,
                 min_value: int = 0,
                 max_value: int = 100,
                 from_value: int = 0,
                 to_value: int = 100,
                 orientation: Orientation = Orientation.HORIZONTAL,
                 tick_interval: int = 0,
                 label: str = "",
                 show_value: bool = True,
                 state: IntervalState = IntervalState.NORMAL,
                 command: Optional[Callable[[int, int], None]] = None):
        """
        Initialize the interval widget.

        Args:
            rect: Rectangle defining the widget position and size
            min_value: Current minimum value of the range
            max_value: Current maximum value of the range
            from_value: Minimum possible value (left/bottom of scale)
            to_value: Maximum possible value (right/top of scale)
            orientation: HORIZONTAL or VERTICAL
            tick_interval: Distance between tick marks (0 = no ticks)
            label: Text label to display
            show_value: Whether to display current values
            state: NORMAL or DISABLED
            command: Callback function called when values change
        """
        self.rect = rect
        self.min_value = min_value
        self.max_value = max_value
        self.from_value = from_value
        self.to_value = to_value
        self.orientation = orientation
        self.tick_interval = tick_interval
        self.label = label
        self.show_value = show_value
        self.state = state
        self.command = command

        # Colors (similar to TCL/Tk defaults)
        self.bg_color = (240, 240, 240)  # Light gray background
        self.slider_color = (200, 200, 200)  # Slider background
        self.active_color = (150, 150, 150)  # Active slider
        self.handle_color = (100, 100, 100)  # Handle color
        self.active_handle_color = (70, 70, 70)  # Active handle
        self.text_color = (0, 0, 0)  # Black text
        self.border_color = (100, 100, 100)  # Dark gray border

        # Dimensions
        self.border_width = 2
        self.handle_width = 10
        self.handle_height = 20
        self.tick_length = 5

        # State
        self.dragging = False  # Which handle is being dragged (None, 'min', 'max', 'center')
        self.hover = False
        self.active = False

        # Font
        self.font = pygame.font.SysFont('arial', 12)

        # Cached surfaces
        self.surface = None
        self.needs_redraw = True

    def set_values(self, min_value: int, max_value: int, notify: bool = True):
        """
        Set the current min/max values of the interval.

        Args:
            min_value: New minimum value
            max_value: New maximum value
            notify: Whether to call the command callback
        """
        # Ensure min <= max
        if min_value > max_value:
            min_value, max_value = max_value, min_value

        # Clamp to valid range
        min_value = max(self.from_value, min(self.to_value, min_value))
        max_value = max(self.from_value, min(self.to_value, max_value))

        # Update values
        old_min, old_max = self.min_value, self.max_value
        self.min_value = min_value
        self.max_value = max_value

        # Redraw if changed
        if old_min != min_value or old_max != max_value:
            self.needs_redraw = True
            if notify and self.command:
                self.command(min_value, max_value)

    def get_values(self) -> Tuple[int, int]:
        """Get the current min/max values."""
        return self.min_value, self.max_value

    def reset(self):
        """Reset to the full range (from_value to to_value)."""
        self.set_values(self.from_value, self.to_value)

    def _value_to_pixel(self, value: int) -> int:
        """Convert a value to pixel coordinate."""
        value_range = self.to_value - self.from_value
        if value_range == 0:
            return 0

        if self.orientation == Orientation.HORIZONTAL:
            pixel_range = self.rect.width - 2 * self.border_width - 2 * self.handle_width
            pixel = ((value - self.from_value) * pixel_range) // value_range
            return self.rect.left + self.border_width + self.handle_width + pixel
        else:  # VERTICAL
            pixel_range = self.rect.height - 2 * self.border_width - 2 * self.handle_width
            pixel = ((value - self.from_value) * pixel_range) // value_range
            return self.rect.bottom - self.border_width - self.handle_width - pixel

    def _pixel_to_value(self, pixel: int) -> int:
        """Convert a pixel coordinate to value."""
        value_range = self.to_value - self.from_value
        if value_range == 0:
            return self.from_value

        if self.orientation == Orientation.HORIZONTAL:
            pixel_range = self.rect.width - 2 * self.border_width - 2 * self.handle_width
            relative_pixel = pixel - (self.rect.left + self.border_width + self.handle_width)
            relative_pixel = max(0, min(pixel_range, relative_pixel))
            return self.from_value + (relative_pixel * value_range) // pixel_range
        else:  # VERTICAL
            pixel_range = self.rect.height - 2 * self.border_width - 2 * self.handle_width
            relative_pixel = (self.rect.bottom - self.border_width - self.handle_width) - pixel
            relative_pixel = max(0, min(pixel_range, relative_pixel))
            return self.from_value + (relative_pixel * value_range) // pixel_range

    def _get_handle_rects(self) -> Tuple[pygame.Rect, pygame.Rect]:
        """Get rectangles for the min and max handles."""
        min_pixel = self._value_to_pixel(self.min_value)
        max_pixel = self._value_to_pixel(self.max_value)

        if self.orientation == Orientation.HORIZONTAL:
            min_rect = pygame.Rect(
                min_pixel - self.handle_width // 2,
                self.rect.centery - self.handle_height // 2,
                self.handle_width,
                self.handle_height
            )
            max_rect = pygame.Rect(
                max_pixel - self.handle_width // 2,
                self.rect.centery - self.handle_height // 2,
                self.handle_width,
                self.handle_height
            )
        else:  # VERTICAL
            min_rect = pygame.Rect(
                self.rect.centerx - self.handle_height // 2,
                min_pixel - self.handle_width // 2,
                self.handle_height,
                self.handle_width
            )
            max_rect = pygame.Rect(
                self.rect.centerx - self.handle_height // 2,
                max_pixel - self.handle_width // 2,
                self.handle_height,
                self.handle_width
            )

        return min_rect, max_rect

    def _draw_horizontal(self, surface: pygame.Surface):
        """Draw horizontal interval widget."""
        # Background
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, self.border_width)

        # Slider track
        track_rect = pygame.Rect(
            self.rect.left + self.border_width,
            self.rect.centery - 2,
            self.rect.width - 2 * self.border_width,
            4
        )
        pygame.draw.rect(surface, self.slider_color, track_rect)

        # Active range
        min_pixel = self._value_to_pixel(self.min_value)
        max_pixel = self._value_to_pixel(self.max_value)
        active_rect = pygame.Rect(
            min_pixel,
            self.rect.centery - 2,
            max_pixel - min_pixel,
            4
        )
        active_color = self.active_color if self.active else self.slider_color
        pygame.draw.rect(surface, active_color, active_rect)

        # Tick marks
        if self.tick_interval > 0:
            for value in range(self.from_value, self.to_value + 1, self.tick_interval):
                pixel = self._value_to_pixel(value)
                pygame.draw.line(surface, self.text_color,
                               (pixel, self.rect.centery - 10),
                               (pixel, self.rect.centery - 5), 1)

                # Tick label
                if self.show_value:
                    text = self.font.render(str(value), True, self.text_color)
                    text_rect = text.get_rect(centerx=pixel, bottom=self.rect.centery - 12)
                    surface.blit(text, text_rect)

        # Handles
        min_handle, max_handle = self._get_handle_rects()
        handle_color = self.active_handle_color if self.active else self.handle_color
        pygame.draw.rect(surface, handle_color, min_handle)
        pygame.draw.rect(surface, handle_color, max_handle)

        # Value labels
        if self.show_value:
            min_text = self.font.render(str(self.min_value), True, self.text_color)
            max_text = self.font.render(str(self.max_value), True, self.text_color)

            min_text_rect = min_text.get_rect(centerx=min_pixel, top=self.rect.centery + 10)
            max_text_rect = max_text.get_rect(centerx=max_pixel, top=self.rect.centery + 10)

            surface.blit(min_text, min_text_rect)
            surface.blit(max_text, max_text_rect)

        # Label
        if self.label:
            label_text = self.font.render(self.label, True, self.text_color)
            label_rect = label_text.get_rect(centerx=self.rect.centerx, bottom=self.rect.top - 5)
            surface.blit(label_text, label_rect)

    def _draw_vertical(self, surface: pygame.Surface):
        """Draw vertical interval widget."""
        # Background
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, self.border_width)

        # Slider track
        track_rect = pygame.Rect(
            self.rect.centerx - 2,
            self.rect.top + self.border_width,
            4,
            self.rect.height - 2 * self.border_width
        )
        pygame.draw.rect(surface, self.slider_color, track_rect)

        # Active range
        min_pixel = self._value_to_pixel(self.min_value)
        max_pixel = self._value_to_pixel(self.max_value)
        active_rect = pygame.Rect(
            self.rect.centerx - 2,
            max_pixel,
            4,
            min_pixel - max_pixel
        )
        active_color = self.active_color if self.active else self.slider_color
        pygame.draw.rect(surface, active_color, active_rect)

        # Tick marks
        if self.tick_interval > 0:
            for value in range(self.from_value, self.to_value + 1, self.tick_interval):
                pixel = self._value_to_pixel(value)
                pygame.draw.line(surface, self.text_color,
                               (self.rect.centerx + 5, pixel),
                               (self.rect.centerx + 10, pixel), 1)

                # Tick label
                if self.show_value:
                    text = self.font.render(str(value), True, self.text_color)
                    text_rect = text.get_rect(left=self.rect.centerx + 12, centery=pixel)
                    surface.blit(text, text_rect)

        # Handles
        min_handle, max_handle = self._get_handle_rects()
        handle_color = self.active_handle_color if self.active else self.handle_color
        pygame.draw.rect(surface, handle_color, min_handle)
        pygame.draw.rect(surface, handle_color, max_handle)

        # Value labels
        if self.show_value:
            min_text = self.font.render(str(self.min_value), True, self.text_color)
            max_text = self.font.render(str(self.max_value), True, self.text_color)

            min_text_rect = min_text.get_rect(right=self.rect.centerx - 5, centery=min_pixel)
            max_text_rect = max_text.get_rect(right=self.rect.centerx - 5, centery=max_pixel)

            surface.blit(min_text, min_text_rect)
            surface.blit(max_text, max_text_rect)

        # Label
        if self.label:
            label_text = self.font.render(self.label, True, self.text_color)
            label_rect = label_text.get_rect(centerx=self.rect.centerx, top=self.rect.bottom + 5)
            surface.blit(label_text, label_rect)

    def draw(self, surface: pygame.Surface):
        """Draw the interval widget to the surface."""
        if self.needs_redraw or self.surface is None:
            self.surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            self.surface.fill((0, 0, 0, 0))  # Transparent background

            if self.orientation == Orientation.HORIZONTAL:
                self._draw_horizontal(self.surface)
            else:
                self._draw_vertical(self.surface)

            self.needs_redraw = False

        surface.blit(self.surface, self.rect.topleft)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events for the interval widget.

        Returns True if the event was handled by this widget.
        """
        if self.state == IntervalState.DISABLED:
            return False

        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            self.hover = self.rect.collidepoint(mouse_pos)

            if self.dragging:
                if self.dragging == 'min':
                    new_value = self._pixel_to_value(mouse_pos[0] if self.orientation == Orientation.HORIZONTAL else mouse_pos[1])
                    self.set_values(new_value, self.max_value)
                elif self.dragging == 'max':
                    new_value = self._pixel_to_value(mouse_pos[0] if self.orientation == Orientation.HORIZONTAL else mouse_pos[1])
                    self.set_values(self.min_value, new_value)
                elif self.dragging == 'center':
                    # Move both handles together
                    center_value = (self.min_value + self.max_value) // 2
                    new_center = self._pixel_to_value(mouse_pos[0] if self.orientation == Orientation.HORIZONTAL else mouse_pos[1])
                    delta = new_center - center_value
                    new_min = self.min_value + delta
                    new_max = self.max_value + delta
                    self.set_values(new_min, new_max)
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if self.rect.collidepoint(mouse_pos):
                min_handle, max_handle = self._get_handle_rects()

                if min_handle.collidepoint(mouse_pos):
                    self.dragging = 'min'
                    self.active = True
                    self.needs_redraw = True
                    return True
                elif max_handle.collidepoint(mouse_pos):
                    self.dragging = 'max'
                    self.active = True
                    self.needs_redraw = True
                    return True
                elif self.rect.collidepoint(mouse_pos):
                    # Check if clicking in the active range (center area)
                    min_pixel = self._value_to_pixel(self.min_value)
                    max_pixel = self._value_to_pixel(self.max_value)

                    if self.orientation == Orientation.HORIZONTAL:
                        if min_pixel <= mouse_pos[0] <= max_pixel:
                            self.dragging = 'center'
                            self.active = True
                            self.needs_redraw = True
                            return True
                    else:
                        if max_pixel <= mouse_pos[1] <= min_pixel:
                            self.dragging = 'center'
                            self.active = True
                            self.needs_redraw = True
                            return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = None
                self.active = False
                self.needs_redraw = True
                return True

        return False

    def configure(self, **kwargs):
        """Configure widget properties."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                self.needs_redraw = True

        # Special handling for value changes
        if 'min_value' in kwargs or 'max_value' in kwargs:
            min_val = kwargs.get('min_value', self.min_value)
            max_val = kwargs.get('max_value', self.max_value)
            self.set_values(min_val, max_val)


# Convenience functions for backward compatibility
def Tk_IntervalCmd(*args, **kwargs):
    """
    Stub function for TCL/Tk compatibility.
    In the original C code, this creates a TCL command.
    Here we just return a configured Interval instance.
    """
    # This would be called from TCL in the original
    # For now, return None as a placeholder
    return None


def create_interval_widget(rect: pygame.Rect, **kwargs) -> Interval:
    """
    Create and return a new Interval widget.

    This is a convenience function for creating interval widgets
    with the pygame-based implementation.
    """
    return Interval(rect, **kwargs)