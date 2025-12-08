from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .base import Rect, UIEvent, UIWidget, WidgetRenderer, rect_contains
from .theme import ThemePalette


@dataclass(slots=True)
class PaletteItem:
    item_id: str
    label: str
    icon: str | None = None
    tooltip: str | None = None
    enabled: bool = True


class PaletteGrid(UIWidget):
    """Grid of palette entries used for tool selection panels."""

    def __init__(
        self,
        *,
        widget_id: str | None = None,
        rect: Rect = (0, 0, 320, 200),
        items: Sequence[PaletteItem] | None = None,
        columns: int = 4,
        item_size: tuple[int, int] = (48, 48),
        gap: int = 6,
        on_select: Callable[[PaletteItem], None] | None = None,
    ) -> None:
        super().__init__(widget_id=widget_id, rect=rect)
        self.columns = max(1, columns)
        self.item_size = item_size
        self.gap = gap
        self._items: list[PaletteItem] = list(items) if items else []
        self._on_select = on_select
        self.selected_id: str | None = None
        self._hover_id: str | None = None
        self.set_focusable(True)

    # ------------------------------------------------------------------
    def set_items(self, items: Sequence[PaletteItem]) -> None:
        self._items = list(items)
        self.invalidate()

    def add_item(self, item: PaletteItem) -> None:
        self._items.append(item)
        self.invalidate()

    # ------------------------------------------------------------------
    def on_event(self, event: UIEvent) -> bool:
        if event.type == "mouse_move" and event.position:
            self._hover_id = self._item_at_point(event.position)
            return self._hover_id is not None

        if event.type == "mouse_down" and event.button == 1 and event.position:
            item_id = self._item_at_point(event.position)
            if item_id is not None:
                item = self._get_item(item_id)
                if item and item.enabled:
                    self.selected_id = item.item_id
                    self.invalidate()
                    if self._on_select:
                        self._on_select(item)
                return True
        return False

    def _item_at_point(self, point: tuple[int, int]) -> str | None:
        for idx, item in enumerate(self._items):
            rect = self._item_rect(idx)
            if rect_contains(rect, point):
                return item.item_id
        return None

    def _get_item(self, item_id: str) -> PaletteItem | None:
        for item in self._items:
            if item.item_id == item_id:
                return item
        return None

    def _item_rect(self, index: int) -> Rect:
        x, y, _, _ = self.rect
        col = index % self.columns
        row = index // self.columns
        width, height = self.item_size
        offset_x = x + col * (width + self.gap)
        offset_y = y + row * (height + self.gap)
        return (offset_x, offset_y, width, height)

    # ------------------------------------------------------------------
    def on_render(self, renderer: WidgetRenderer) -> None:
        palette = self._palette()
        for idx, item in enumerate(self._items):
            rect = self._item_rect(idx)
            bg = palette.surface_alt if item.enabled else palette.background
            if item.item_id == self.selected_id:
                bg = palette.accent_active
            elif item.item_id == self._hover_id:
                bg = palette.accent_hover
            renderer.draw_rect(rect, bg, border=True, border_color=palette.border)
            renderer.draw_text(
                item.label,
                (rect[0] + rect[2] // 2, rect[1] + rect[3] - 12),
                palette.text if item.enabled else palette.text_muted,
                font=self.theme.metrics.font_name if self.theme else None,
            )
            if item.icon:
                renderer.draw_image(item.icon, rect)

    def _palette(self) -> ThemePalette:
        theme = self.theme
        return theme.palette if theme else ThemePalette()


__all__ = ["PaletteGrid", "PaletteItem"]
