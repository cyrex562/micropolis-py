from __future__ import annotations

from .base import Rect, UIWidget, WidgetRenderer
from .theme import ThemePalette


class Tooltip(UIWidget):
    """Delayed tooltip bubble that follows an anchor rectangle."""

    def __init__(
        self,
        *,
        widget_id: str | None = None,
        delay_ms: int | None = None,
        # Legacy params for tests
        text: str | None = None,
    ) -> None:
        super().__init__(widget_id=widget_id, rect=(0, 0, 0, 0))
        self.text: str = ""
        self.anchor_rect: Rect | None = None
        self.delay_ms = delay_ms
        self._timer = 0.0
        self._visible = False
        self.set_focusable(False)

        # Map legacy constructor param
        if text is not None:
            self.text = text

    def queue(self, text: str, anchor_rect: Rect) -> None:
        self.text = text
        self.anchor_rect = anchor_rect
        self._timer = 0.0
        self._visible = False
        self._reposition()
        self.invalidate()

    # Backwards-compatible aliases used by legacy tests
    def on_mouse_enter(self) -> None:
        # Start the tooltip timer using current anchor_rect
        self._timer = 0.0
        self._visible = False
        # Ensure there's an anchor_rect so update() will progress the timer
        if not self.anchor_rect:
            self.anchor_rect = (0, 0, 0, 0)
            self._reposition()

    def on_mouse_leave(self) -> None:
        self.hide()

    def on_update(self, dt_ms: float) -> None:
        # Tests call on_update with milliseconds
        self.update(dt_ms / 1000.0)

    @property
    def visible(self) -> bool:
        return bool(self._visible)

    def set_position(self, pos: tuple[int, int]) -> None:
        # Legacy tests pass a position; set anchor_rect accordingly
        x, y = pos
        self.anchor_rect = (x, y, 0, 0)
        self._reposition()

    def hide(self) -> None:
        self._visible = False
        self.anchor_rect = None
        self.invalidate()

    @property
    def is_visible(self) -> bool:
        return self._visible

    def _reposition(self) -> None:
        if not self.anchor_rect:
            return
        x, y, w, _ = self.anchor_rect
        text_width = max(80, len(self.text) * 7)
        height = 28
        # Position tooltip below/right of anchor (legacy tests expect the
        # tooltip to be offset so its left/top are >= the mouse position).
        self.set_rect((x + w // 2, y + 8, text_width, height))

    def update(self, dt: float) -> None:
        super().update(dt)
        threshold = (self.delay_ms or self._default_delay()) / 1000.0
        if not self.anchor_rect:
            self._visible = False
            return
        if not self._visible:
            self._timer += dt
            if self._timer >= threshold:
                self._visible = True
                self.invalidate()

    def _default_delay(self) -> int:
        theme = self.theme
        return theme.metrics.tooltip_delay_ms if theme else 300

    def on_render(self, renderer: WidgetRenderer) -> None:
        if not self._visible or not self.text:
            return
        palette = self._palette()
        renderer.draw_rect(
            self.rect,
            palette.tooltip_bg,
            border=True,
            border_color=palette.border,
        )
        renderer.draw_text(
            self.text,
            (self.rect[0] + 8, self.rect[1] + self.rect[3] // 2),
            palette.tooltip_text,
            font=self.theme.metrics.font_name if self.theme else None,
        )

    def _palette(self) -> ThemePalette:
        theme = self.theme
        return theme.palette if theme else ThemePalette()


__all__ = ["Tooltip"]
