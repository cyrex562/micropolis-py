from __future__ import annotations

from collections.abc import Callable

from .base import (
    Rect,
    UIEvent,
    UIWidget,
    WidgetRenderer,
    rect_contains,
)
from .theme import ThemePalette

_MOUSE_ACTIVATE_BUTTON = 1
_KEY_ACTIVATE = {13, 32}  # Enter, Space


class Button(UIWidget):
    """Clickable button with hover, pressed, and keyboard activation."""

    def __init__(
        self,
        label: str = "",
        # Legacy aliases supported for tests: text / callback
        text: str | None = None,
        *,
        widget_id: str | None = None,
        rect: Rect = (0, 0, 120, 32),
        on_click: Callable[[Button], None] | None = None,
        callback: Callable[..., None] | None = None,
        tooltip: str | None = None,
    ) -> None:
        # Map legacy text -> label if provided
        if text is not None:
            label = text

        super().__init__(widget_id=widget_id, rect=rect)
        self.label = label

        # If a legacy callback is provided, adapt it to the modern on_click
        if callback is not None and on_click is None:
            # Wrap callback so it can accept either zero args or one arg
            def _wrapped(btn: Button) -> None:
                try:
                    callback()
                except TypeError:
                    try:
                        callback(btn)
                    except TypeError:
                        # Best-effort: call with no args
                        callback()

            self._on_click = _wrapped
        else:
            self._on_click = on_click
        self.tooltip = tooltip
        self._hovered = False
        self._pressed = False
        self.set_focusable(True)

    # Backwards-compatible public properties used by tests
    @property
    def hovered(self) -> bool:
        return bool(self._hovered)

    @property
    def pressed(self) -> bool:
        return bool(self._pressed)

    # ------------------------------------------------------------------
    def click(self) -> None:
        if self._on_click is not None and self.enabled:
            self._on_click(self)

    # ------------------------------------------------------------------
    def on_event(self, event: UIEvent) -> bool:
        # Do not process events when hidden or disabled (tests call on_event()
        # directly). Keep parity with handle_event behavior.
        if not (self.visible and self.enabled):
            return False

        # Accept either UIEvent or pygame.Event for backwards-compatibility
        try:
            import pygame  # type: ignore

            is_pygame = hasattr(event, "type") and isinstance(event.type, int)
        except Exception:
            is_pygame = False

        if is_pygame:
            # Convert common pygame mouse/keyboard events into UIEvent-like shape
            et = event.type
            if et == getattr(__import__("pygame"), "MOUSEMOTION"):
                type_str = "mouse_move"
            elif et == getattr(__import__("pygame"), "MOUSEBUTTONDOWN"):
                type_str = "mouse_down"
            elif et == getattr(__import__("pygame"), "MOUSEBUTTONUP"):
                type_str = "mouse_up"
            elif et == getattr(__import__("pygame"), "KEYDOWN"):
                type_str = "key_down"
            elif et == getattr(__import__("pygame"), "KEYUP"):
                type_str = "key_up"
            else:
                return False

            pos = getattr(event, "pos", None) or getattr(event, "position", None)
            button = getattr(event, "button", None)
            key = getattr(event, "key", None)
            # Build a minimal UIEvent-like object
            ui_event = UIEvent(type=type_str, position=pos, button=button, key=key)
            event = ui_event

        if event.type == "mouse_move" and event.position:
            hovered = rect_contains(self.rect, event.position)
            if hovered != self._hovered:
                self._hovered = hovered
                self.invalidate()
            return hovered

        if event.type == "mouse_down" and event.button == _MOUSE_ACTIVATE_BUTTON:
            if event.position and rect_contains(self.rect, event.position):
                self._pressed = True
                self.focus()
                self.invalidate()
                return True

        if event.type == "mouse_up" and event.button == _MOUSE_ACTIVATE_BUTTON:
            if self._pressed:
                self._pressed = False
                inside = event.position and rect_contains(self.rect, event.position)
                self.invalidate()
                if inside:
                    self.click()
                return True

        if event.type == "key_down" and event.key in _KEY_ACTIVATE:
            self._pressed = True
            self.invalidate()
            return True

        if event.type == "key_up" and event.key in _KEY_ACTIVATE:
            if self._pressed:
                self._pressed = False
                self.invalidate()
                self.click()
                return True

        return False

    # ------------------------------------------------------------------
    def on_render(self, renderer: WidgetRenderer) -> None:
        palette = self._palette
        bg = palette.surface
        text_color = palette.text
        if not self.enabled:
            bg = palette.surface_alt
            text_color = palette.text_muted
        elif self._pressed or getattr(self, "toggled", False):
            bg = palette.accent_active
        elif self._hovered:
            bg = palette.accent_hover

        renderer.draw_rect(
            self.rect,
            bg,
            border=True,
            border_color=palette.border,
            radius=self.theme.metrics.border_radius if self.theme else 0,
        )
        renderer.draw_text(
            self.label,
            (self.rect[0] + self.rect[2] // 2, self.rect[1] + self.rect[3] // 2),
            text_color,
            font=self.theme.metrics.font_name if self.theme else None,
        )

    @property
    def _palette(self) -> ThemePalette:
        theme = self.theme
        return theme.palette if theme else ThemePalette()


class ToggleButton(Button):
    """Button that toggles persistent on/off state."""

    def __init__(
        self,
        label: str = "",
        # Legacy aliases supported for tests
        text: str | None = None,
        *,
        widget_id: str | None = None,
        rect: Rect = (0, 0, 120, 32),
        on_click: Callable[[Button], None] | None = None,
        on_toggle: Callable[[ToggleButton, bool], None] | None = None,
        # legacy alias
        callback: Callable[..., None] | None = None,
        tooltip: str | None = None,
    ) -> None:
        # Map legacy text -> label
        if text is not None:
            label = text
        # Do not pass legacy callback down to Button; ToggleButton
        # interprets legacy `callback` as the toggle-state callback
        # (on_toggle) so avoid double-calling the same function from
        # both _on_click and _on_toggle.
        super().__init__(
            label,
            text=None,
            widget_id=widget_id,
            rect=rect,
            on_click=on_click,
            callback=None,
            tooltip=tooltip,
        )
        self.toggled = False
        # Map legacy callback to on_toggle if provided
        if callback is not None and on_toggle is None:

            def _wrapped(btn: ToggleButton, state: bool) -> None:
                try:
                    callback(state)
                except TypeError:
                    try:
                        callback()
                    except TypeError:
                        callback(state)

            self._on_toggle = _wrapped
        else:
            self._on_toggle = on_toggle

    def click(self) -> None:
        self.set_toggled(not self.toggled)
        super().click()

    def set_toggled(self, toggled: bool, *, fire: bool = True) -> None:
        if toggled != self.toggled:
            self.toggled = toggled
            self.invalidate()
            if fire and self._on_toggle is not None:
                self._on_toggle(self, toggled)


class Checkbox(ToggleButton):
    """Specialised toggle that renders traditional checkbox visuals."""

    def __init__(
        self,
        label: str,
        # Legacy alias
        text: str | None = None,
        *,
        widget_id: str | None = None,
        rect: Rect = (0, 0, 160, 24),
        on_toggle: Callable[[ToggleButton, bool], None] | None = None,
        callback: Callable[..., None] | None = None,
    ) -> None:
        # Support legacy text param
        if text is not None:
            label = text
        super().__init__(
            label,
            text=None,
            widget_id=widget_id,
            rect=rect,
            on_toggle=on_toggle,
            callback=callback,
        )

    @property
    def checked(self) -> bool:
        return bool(getattr(self, "toggled", False))

    def on_render(self, renderer: WidgetRenderer) -> None:
        palette = self._palette
        x, y, w, h = self.rect
        box_size = min(h - 4, 24)
        box_rect = (x, y + (h - box_size) // 2, box_size, box_size)
        renderer.draw_rect(
            box_rect,
            palette.surface,
            border=True,
            border_color=palette.border,
            radius=3,
        )
        if self.toggled:
            renderer.draw_line(
                (box_rect[0] + 4, box_rect[1] + box_rect[3] // 2),
                (box_rect[0] + box_rect[2] // 2, box_rect[1] + box_rect[3] - 4),
                palette.accent,
                width=3,
            )
            renderer.draw_line(
                (box_rect[0] + box_rect[2] // 2, box_rect[1] + box_rect[3] - 4),
                (box_rect[0] + box_rect[2] - 4, box_rect[1] + 4),
                palette.accent,
                width=3,
            )
        renderer.draw_text(
            self.label,
            (x + box_size + 8, y + h // 2),
            palette.text,
            font=self.theme.metrics.font_name if self.theme else None,
        )


__all__ = ["Button", "ToggleButton", "Checkbox"]
