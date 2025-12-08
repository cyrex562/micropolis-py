from __future__ import annotations

from .base import Color, Point, Rect, UIWidget, WidgetRenderer


class TextLabel(UIWidget):
    """Simple text label supporting wrapping and alignment."""

    def __init__(
        self,
        text: str = "",
        *,
        widget_id: str | None = None,
        rect: Rect = (0, 0, 0, 0),
        color: Color | None = None,
        align: str = "left",
        wrap_width: int | None = None,
    ) -> None:
        super().__init__(widget_id=widget_id, rect=rect)
        self.text = text
        self._color = color
        self.align = align
        self.wrap_width = wrap_width
        self.set_focusable(False)

    def set_text(self, text: str) -> None:
        if text != self.text:
            self.text = text
            self.invalidate()

    def preferred_size(self) -> Point:
        _, _, w, h = self.rect
        return w, h

    def on_render(self, renderer: WidgetRenderer) -> None:
        theme = self.theme
        color = self._color or (theme.palette.text if theme else (255, 255, 255, 255))
        x, y, w, h = self.rect
        text_x = x
        anchor = "midleft"
        if self.align == "center":
            text_x = x + w // 2
            anchor = "center"
        elif self.align == "right":
            text_x = x + w
            anchor = "midright"
        renderer.draw_text(
            self.text,
            (text_x, y + h // 2),
            color,
            font=theme.metrics.font_name if theme else None,
            anchor=anchor,
        )


__all__ = ["TextLabel"]
