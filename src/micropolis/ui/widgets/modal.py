from __future__ import annotations

from .base import Color, Rect, UIEvent, UIWidget, WidgetRenderer, rect_contains
from .theme import ThemePalette


class ModalDialog(UIWidget):
    """Modal overlay that traps focus until dismissed."""

    def __init__(
        self,
        *,
        widget_id: str | None = None,
        rect: Rect = (0, 0, 640, 480),
        overlay_color: Color = (0, 0, 0, 160),
        dismiss_on_background: bool = True,
    ) -> None:
        super().__init__(widget_id=widget_id, rect=rect)
        self.overlay_color = overlay_color
        self.dismiss_on_background = dismiss_on_background
        self._content: UIWidget | None = None
        self._is_open = False
        self._previous_focus: UIWidget | None = None
        self.set_focusable(True)

    # ------------------------------------------------------------------
    def set_content(self, widget: UIWidget) -> None:
        if self._content is widget:
            return
        if self._content is not None:
            self.remove_child(self._content)
        self._content = widget
        self.add_child(widget)
        self._layout_content()

    def _layout_content(self) -> None:
        if not self._content:
            return
        x, y, w, h = self.rect
        _, _, cw, ch = self._content.rect
        cx = x + (w - cw) // 2
        cy = y + (h - ch) // 2
        self._content.set_rect((cx, cy, cw, ch))

    # ------------------------------------------------------------------
    @property
    def is_open(self) -> bool:
        return self._is_open

    def open(self) -> None:
        if self._is_open:
            return
        self._is_open = True
        self.show()
        self._previous_focus = UIWidget._focused_widget
        self.focus()

    def close(self) -> None:
        if not self._is_open:
            return
        self._is_open = False
        self.hide()
        if self._previous_focus is not None:
            self._previous_focus.focus()
        self._previous_focus = None

    # ------------------------------------------------------------------
    def handle_event(self, event: UIEvent) -> bool:
        if not self._is_open or not self.visible:
            return False
        if event.type == "mouse_down" and event.position:
            if self._content and not rect_contains(self._content.rect, event.position):
                if self.dismiss_on_background:
                    self.close()
                return True
        if event.type == "key_down" and event.key == 27:  # ESC
            self.close()
            return True
        return super().handle_event(event)

    # ------------------------------------------------------------------
    def on_render(self, renderer: WidgetRenderer) -> None:
        palette = self._palette()
        renderer.draw_rect(self.rect, self.overlay_color or palette.surface)

    def _palette(self) -> ThemePalette:
        theme = self.theme
        return theme.palette if theme else ThemePalette()


__all__ = ["ModalDialog"]
