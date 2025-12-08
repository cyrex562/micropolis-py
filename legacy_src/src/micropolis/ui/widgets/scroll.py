from __future__ import annotations

from .base import Rect, UIEvent, UIWidget, WidgetRenderer, clamp
from .theme import ThemePalette


class ScrollContainer(UIWidget):
    """Viewport that hosts a single child widget with scrollbars."""

    def __init__(
        self,
        *,
        widget_id: str | None = None,
        rect: Rect = (0, 0, 320, 200),
    ) -> None:
        super().__init__(widget_id=widget_id, rect=rect)
        self._scroll_x = 0
        self._scroll_y = 0
        self._content: UIWidget | None = None
        self._scroll_step = 24
        self.set_focusable(True)

    # ------------------------------------------------------------------
    def set_content(self, widget: UIWidget) -> None:
        if self._content is widget:
            return
        if self._content is not None:
            self.remove_child(self._content)
        self._content = widget
        self.add_child(widget)
        self._sync_content_rect()

    @property
    def content(self) -> UIWidget | None:
        return self._content

    # ------------------------------------------------------------------
    def scroll_to(self, x: float, y: float) -> None:
        max_x, max_y = self._max_scroll()
        new_x = clamp(x, 0, max_x)
        new_y = clamp(y, 0, max_y)
        if (new_x, new_y) != (self._scroll_x, self._scroll_y):
            self._scroll_x = new_x
            self._scroll_y = new_y
            self._sync_content_rect()
            self.invalidate()

    def scroll_by(self, dx: float, dy: float) -> None:
        self.scroll_to(self._scroll_x + dx, self._scroll_y + dy)

    def _max_scroll(self) -> tuple[float, float]:
        if not self._content:
            return 0.0, 0.0
        _, _, w, h = self.rect
        cw, ch = self._content.rect[2], self._content.rect[3]
        return max(0.0, cw - w), max(0.0, ch - h)

    def _sync_content_rect(self) -> None:
        if not self._content:
            return
        x, y, _, _ = self.rect
        cw, ch = self._content.rect[2], self._content.rect[3]
        self._content.set_rect(
            (int(x - self._scroll_x), int(y - self._scroll_y), cw, ch)
        )

    # ------------------------------------------------------------------
    def on_event(self, event: UIEvent) -> bool:
        if event.type in {"mouse_wheel", "scroll"}:
            dx = 0
            dy = -event.scroll_delta[1] if event.scroll_delta else self._scroll_step
            self.scroll_by(dx, dy)
            return True
        return False

    # ------------------------------------------------------------------
    def on_render(self, renderer: WidgetRenderer) -> None:
        palette = self._palette()
        renderer.draw_rect(
            self.rect,
            palette.surface,
            border=True,
            border_color=palette.border,
        )

    def _palette(self) -> ThemePalette:
        theme = self.theme
        return theme.palette if theme else ThemePalette()


__all__ = ["ScrollContainer"]
