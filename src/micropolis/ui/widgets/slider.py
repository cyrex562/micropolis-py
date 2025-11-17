from __future__ import annotations

from collections.abc import Callable
from enum import Enum

from .base import Rect, UIEvent, UIWidget, WidgetRenderer, clamp, rect_contains
from .theme import ThemePalette


class SliderOrientation(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class Slider(UIWidget):
    """Continuous slider for numeric values with mouse and keyboard input."""

    def __init__(
        self,
        *,
        widget_id: str | None = None,
        rect: Rect = (0, 0, 200, 28),
        # Legacy aliases: min_val, max_val, initial_val, callback
        min_value: float = 0.0,
        max_value: float = 1.0,
        value: float = 0.0,
        step: float = 0.01,
        orientation: SliderOrientation = SliderOrientation.HORIZONTAL,
        on_change: Callable[[Slider, float], None] | None = None,
        min_val: float | None = None,
        max_val: float | None = None,
        initial_val: float | None = None,
        callback: Callable[..., None] | None = None,
    ) -> None:
        # Map legacy names
        if min_val is not None:
            min_value = min_val
        if max_val is not None:
            max_value = max_val
        if initial_val is not None:
            value = initial_val

        super().__init__(widget_id=widget_id, rect=rect)
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.orientation = orientation
        self._value = clamp(value, min_value, max_value)
        # Adapt legacy callback signatures to the modern on_change(slider, value)
        if callback is not None and on_change is None:

            def _wrapped(slider: Slider, val: float) -> None:
                try:
                    # prefer single-arg callback(val)
                    callback(val)
                except TypeError:
                    try:
                        # fallback: callback(slider)
                        callback(slider)
                    except TypeError:
                        # best-effort: call with no args
                        callback()

            self._on_change = _wrapped
        else:
            self._on_change = on_change
        self._dragging = False
        self.set_focusable(True)

    # ------------------------------------------------------------------
    @property
    def value(self) -> float:
        return self._value

    @property
    def dragging(self) -> bool:
        return bool(self._dragging)

    def set_value(self, value: float, *, fire: bool = True) -> None:
        new_value = self._quantize(clamp(value, self.min_value, self.max_value))
        if new_value != self._value:
            self._value = new_value
            self.invalidate()
            if fire and self._on_change is not None:
                # Call on_change(slider, value)
                try:
                    self._on_change(self, self._value)
                except TypeError:
                    # Fallback for legacy callbacks that accept different args
                    try:
                        self._on_change(self._value)
                    except TypeError:
                        try:
                            self._on_change()
                        except TypeError:
                            pass

    def _quantize(self, value: float) -> float:
        if self.step <= 0:
            return value
        steps = round((value - self.min_value) / self.step)
        return self.min_value + steps * self.step

    # ------------------------------------------------------------------
    def on_event(self, event: UIEvent) -> bool:
        # Do not process events when hidden or disabled
        if not (self.visible and self.enabled):
            return False

        # Accept pygame.Event objects for backwards compatibility
        try:
            import pygame  # type: ignore

            is_pygame = hasattr(event, "type") and isinstance(event.type, int)
        except Exception:
            is_pygame = False

        if is_pygame:
            et = event.type
            if et == getattr(__import__("pygame"), "MOUSEBUTTONDOWN"):
                type_str = "mouse_down"
            elif et == getattr(__import__("pygame"), "MOUSEMOTION"):
                type_str = "mouse_move"
            elif et == getattr(__import__("pygame"), "MOUSEBUTTONUP"):
                type_str = "mouse_up"
            elif et == getattr(__import__("pygame"), "KEYDOWN"):
                type_str = "key_down"
            else:
                return False
            pos = getattr(event, "pos", None) or getattr(event, "position", None)
            button = getattr(event, "button", None)
            key = getattr(event, "key", None)
            event = UIEvent(type=type_str, position=pos, button=button, key=key)

        if event.type == "mouse_down" and event.button == 1:
            if event.position and rect_contains(self.rect, event.position):
                self._dragging = True
                self.focus()
                self._update_value_from_point(event.position)
                return True

        if event.type == "mouse_move" and self._dragging and event.position:
            self._update_value_from_point(event.position)
            return True

        if event.type == "mouse_up" and event.button == 1:
            if self._dragging:
                self._dragging = False
                return True

        if event.type == "key_down":
            # Support both legacy numeric codes and pygame.K_* constants
            try:
                import pygame  # type: ignore

                left_keys = {pygame.K_LEFT, pygame.K_DOWN}
                right_keys = {pygame.K_RIGHT, pygame.K_UP}
            except Exception:
                left_keys = {37, 40}
                right_keys = {39, 38}

            key = event.key
            delta = self.step or (self.max_value - self.min_value) * 0.01
            if key in left_keys:
                self.set_value(self._value - delta)
                return True
            if key in right_keys:
                self.set_value(self._value + delta)
                return True

        return False

    def _update_value_from_point(self, point: tuple[int, int]) -> None:
        x, y, w, h = self.rect
        if self.orientation is SliderOrientation.HORIZONTAL:
            ratio = clamp((point[0] - x) / max(w, 1), 0.0, 1.0)
        else:
            ratio = clamp((point[1] - y) / max(h, 1), 0.0, 1.0)
        value = self.min_value + ratio * (self.max_value - self.min_value)
        self.set_value(value)

    # ------------------------------------------------------------------
    def on_render(self, renderer: WidgetRenderer) -> None:
        palette = self._palette()
        x, y, w, h = self.rect
        track_rect = (x + 4, y + h // 2 - 2, w - 8, 4)
        renderer.draw_rect(track_rect, palette.border)
        knob_pos = self._knob_position()
        knob_rect = (knob_pos[0] - 6, knob_pos[1] - 6, 12, 12)
        renderer.draw_rect(
            knob_rect,
            palette.accent,
            border=True,
            border_color=palette.border,
        )

    def _palette(self) -> ThemePalette:
        theme = self.theme
        return theme.palette if theme else ThemePalette()

    def _knob_position(self) -> tuple[int, int]:
        x, y, w, h = self.rect
        ratio = (self._value - self.min_value) / max(
            self.max_value - self.min_value,
            1e-6,
        )
        if self.orientation is SliderOrientation.HORIZONTAL:
            pos_x = int(x + ratio * w)
            pos_y = y + h // 2
        else:
            pos_x = x + w // 2
            pos_y = int(y + ratio * h)
        return pos_x, pos_y


__all__ = ["Slider", "SliderOrientation"]
