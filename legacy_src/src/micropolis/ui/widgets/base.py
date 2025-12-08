from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from .theme import Theme


class RectLike:
    """Lightweight rect-like sequence that is indexable and provides
    common pygame.Rect-style attributes used by tests (topleft, center).
    Keeps internal storage as ints and is iterable/unpackable so existing
    tuple-based code continues to work."""

    __slots__ = ("_x", "_y", "_w", "_h")

    def __init__(self, x: int, y: int, w: int, h: int) -> None:
        self._x = int(x)
        self._y = int(y)
        self._w = int(w)
        self._h = int(h)

    def __iter__(self):
        yield self._x
        yield self._y
        yield self._w
        yield self._h

    def __len__(self) -> int:
        return 4

    def __getitem__(self, idx: int) -> int:
        return (self._x, self._y, self._w, self._h)[idx]

    def __eq__(self, other: object) -> bool:  # pragma: no cover - simple equality
        if isinstance(other, RectLike):
            return (self._x, self._y, self._w, self._h) == (
                other._x,
                other._y,
                other._w,
                other._h,
            )
        if isinstance(other, tuple):
            return (self._x, self._y, self._w, self._h) == other
        return False

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    @property
    def w(self) -> int:
        return self._w

    @property
    def h(self) -> int:
        return self._h

    @property
    def topleft(self) -> tuple[int, int]:
        return (self._x, self._y)

    @property
    def center(self) -> tuple[int, int]:
        return (self._x + self._w // 2, self._y + self._h // 2)

    # pygame.Rect-compatible aliases used in tests
    @property
    def left(self) -> int:
        return self._x

    @property
    def top(self) -> int:
        return self._y

    @property
    def right(self) -> int:
        return self._x + self._w

    @property
    def bottom(self) -> int:
        return self._y + self._h

    @property
    def width(self) -> int:
        return self._w

    @property
    def height(self) -> int:
        return self._h

    def as_tuple(self) -> tuple[int, int, int, int]:
        return (self._x, self._y, self._w, self._h)


Rect = RectLike
Point = tuple[int, int]
Color = tuple[int, int, int, int]


@dataclass(slots=True)
class UIEvent:
    """Generic UI event used by the widget toolkit."""

    type: str
    position: Point | None = None
    button: int | None = None
    key: int | None = None
    unicode: str | None = None
    scroll_delta: Point | None = None
    modifiers: frozenset[str] = frozenset()
    timestamp: float | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def with_changes(self, **overrides: Any) -> UIEvent:
        return replace(self, **overrides)


@runtime_checkable
class WidgetRenderer(Protocol):
    """Protocol describing the rendering surface operations needed by widgets."""

    def draw_rect(
        self,
        rect: Rect,
        color: Color,
        border: bool = False,
        border_color: Color | None = None,
        radius: int = 0,
    ) -> None: ...

    def draw_text(
        self,
        text: str,
        position: Point,
        color: Color,
        font: str | None = None,
        size: int | None = None,
    ) -> None: ...

    def draw_line(
        self,
        start: Point,
        end: Point,
        color: Color,
        width: int = 1,
    ) -> None: ...

    def draw_image(
        self,
        image_id: str,
        dest: Rect,
        tint: Color | None = None,
    ) -> None: ...


class WidgetState(Enum):
    IDLE = auto()
    HOVERED = auto()
    PRESSED = auto()
    DISABLED = auto()
    FOCUSED = auto()


def rect_contains(rect: Rect, point: Point) -> bool:
    x, y, w, h = rect
    px, py = point
    return x <= px < x + w and y <= py < y + h


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


class UIWidget:
    """Base widget supporting layout, focus, events, and dirty tracking."""

    _focused_widget: ClassVar[UIWidget | None] = None

    def __init__(
        self,
        widget_id: str | None = None,
        rect: Rect | tuple[int, int, int, int] = (0, 0, 0, 0),
        theme: Theme | None = None,
    ) -> None:
        self.id = widget_id
        # Normalize rect into RectLike so it supports tuple-unpacking and
        # provides pygame.Rect-like attributes (topleft, center) used in tests.
        if isinstance(rect, RectLike):
            self._rect = rect
        else:
            # Accept pygame.Rect or tuple-like
            try:
                import pygame  # type: ignore

                if isinstance(rect, getattr(pygame, "Rect")):
                    x, y, w, h = rect.x, rect.y, rect.width, rect.height
                else:
                    x, y, w, h = rect
            except Exception:
                x, y, w, h = rect
            self._rect = RectLike(x, y, w, h)
        self._children: list[UIWidget] = []
        self._parent: UIWidget | None = None
        self._visible = True
        self._enabled = True
        self._focusable = False
        self._has_focus = False
        self._dirty_regions: list[Rect] = [rect]
        self._z_index = 0
        self._needs_layout = True
        self._theme = theme

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def rect(self) -> Rect:
        return self._rect

    def set_rect(self, rect: Rect) -> None:
        # Normalize the rect into RectLike so callers can pass tuples or
        # pygame.Rect and tests can access .topleft/.left/.top etc.
        if isinstance(rect, RectLike):
            normalized = rect
        else:
            try:
                import pygame  # type: ignore

                if isinstance(rect, getattr(pygame, "Rect")):
                    x, y, w, h = rect.x, rect.y, rect.width, rect.height
                else:
                    x, y, w, h = rect
            except Exception:
                x, y, w, h = rect
            normalized = RectLike(x, y, w, h)

        if normalized != self._rect:
            self._rect = normalized
            self.invalidate()
            self.mark_layout_dirty()

    @property
    def theme(self) -> Theme | None:
        return self._theme

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        for child in self._children:
            child.set_theme(theme)
        self.invalidate()

    @property
    def parent(self) -> UIWidget | None:
        return self._parent

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        # Allow assignment to `visible` in legacy tests (maps to show/hide)
        if value:
            self.show()
        else:
            self.hide()

    def show(self) -> None:
        if not self._visible:
            self._visible = True
            self.invalidate()

    def hide(self) -> None:
        if self._visible:
            self._visible = False
            self.invalidate()
            if self._has_focus:
                self.blur()

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        if self._enabled != enabled:
            self._enabled = enabled
            if not enabled and self._has_focus:
                self.blur()
            self.invalidate()

    @property
    def focusable(self) -> bool:
        return self._focusable

    def set_focusable(self, focusable: bool) -> None:
        self._focusable = focusable

    @property
    def has_focus(self) -> bool:
        return self._has_focus

    # Backwards compatible alias used by legacy tests
    @property
    def focused(self) -> bool:
        return self._has_focus

    @focused.setter
    def focused(self, val: bool) -> None:
        if val:
            self.focus()
        else:
            self.blur()

    # ------------------------------------------------------------------
    # Children management
    # ------------------------------------------------------------------
    def add_child(self, widget: UIWidget, index: int | None = None) -> None:
        if widget._parent is not None:
            raise ValueError("Widget already has a parent")
        widget._parent = self
        if index is None:
            self._children.append(widget)
        else:
            self._children.insert(index, widget)
        widget.mark_layout_dirty()
        self.invalidate()

    def remove_child(self, widget: UIWidget) -> None:
        if widget in self._children:
            self._children.remove(widget)
            widget._parent = None
            if widget._has_focus:
                widget.blur()
            self.invalidate()

    def iter_children(self, reverse: bool = False) -> Iterable[UIWidget]:
        children = self._children[::-1] if reverse else self._children
        return list(children)

    # ------------------------------------------------------------------
    # Dirty tracking & layout
    # ------------------------------------------------------------------
    def invalidate(self, rect: Rect | None = None) -> None:
        region = rect or self._rect
        self._dirty_regions.append(region)

    def consume_dirty_regions(self) -> list[Rect]:
        regions = self._dirty_regions[:]
        self._dirty_regions.clear()
        return regions

    def mark_layout_dirty(self) -> None:
        self._needs_layout = True
        if self._parent:
            self._parent.mark_layout_dirty()

    def layout_if_needed(self) -> None:
        if self._needs_layout:
            self._needs_layout = False
            self.layout()
        for child in self._children:
            child.layout_if_needed()

    def layout(self) -> None:  # pragma: no cover - override point
        """Override to position children."""

    # ------------------------------------------------------------------
    # Focus management
    # ------------------------------------------------------------------
    def focus(self) -> bool:
        if not (self._focusable and self._visible and self._enabled):
            return False
        current = UIWidget._focused_widget
        if current is self:
            return True
        if current is not None:
            current._has_focus = False
            current.on_blur()
        UIWidget._focused_widget = self
        self._has_focus = True
        self.on_focus()
        return True

    def blur(self) -> None:
        if self._has_focus:
            self._has_focus = False
            if UIWidget._focused_widget is self:
                UIWidget._focused_widget = None
            self.on_blur()

    def on_focus(self) -> None:  # pragma: no cover - hook
        pass

    def on_blur(self) -> None:  # pragma: no cover - hook
        pass

    def focus_next(self) -> bool:
        root = self.root
        focusables = root._gather_focusable()
        if not focusables:
            return False
        current = UIWidget._focused_widget
        if current not in focusables:
            return focusables[0].focus()
        idx = focusables.index(current)
        return focusables[(idx + 1) % len(focusables)].focus()

    def focus_previous(self) -> bool:
        root = self.root
        focusables = root._gather_focusable()
        if not focusables:
            return False
        current = UIWidget._focused_widget
        if current not in focusables:
            return focusables[-1].focus()
        idx = focusables.index(current)
        return focusables[(idx - 1) % len(focusables)].focus()

    def _gather_focusable(self) -> list[UIWidget]:
        nodes: list[UIWidget] = []
        if self._focusable and self._visible and self._enabled:
            nodes.append(self)
        for child in self._children:
            nodes.extend(child._gather_focusable())
        return nodes

    @property
    def root(self) -> UIWidget:
        node = self
        while node._parent is not None:
            node = node._parent
        return node

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def handle_event(self, event: UIEvent) -> bool:
        if not (self._visible and self._enabled):
            return False
        # Children receive events first (top-most last child first)
        for child in reversed(self._children):
            if child.handle_event(event):
                return True
        return self.on_event(event)

    def on_event(self, event: UIEvent) -> bool:  # pragma: no cover - override
        return False

    # ------------------------------------------------------------------
    # Update & render
    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        for child in self._children:
            child.update(dt)

    def render(self, renderer: WidgetRenderer) -> None:
        if not self._visible:
            return
        self.on_render(renderer)
        for child in self._children:
            child.render(renderer)

    def on_render(self, renderer: WidgetRenderer) -> None:  # pragma: no cover - hook
        pass

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def global_to_local(self, point: Point) -> Point:
        x, y, _, _ = self._rect
        px, py = point
        return px - x, py - y

    def local_to_global(self, point: Point) -> Point:
        x, y, _, _ = self._rect
        px, py = point
        return px + x, py + y

    def contains_point(self, point: Point) -> bool:
        return rect_contains(self._rect, point)

    def set_z_index(self, value: int) -> None:
        self._z_index = value
        if self._parent:
            self._parent._children.sort(key=lambda w: w._z_index)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r}, rect={self._rect})"
