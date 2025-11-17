"""Widget toolkit for the Micropolis pygame UI."""

from .base import (
    Color,
    Point,
    Rect,
    UIEvent,
    UIWidget,
    WidgetRenderer,
    WidgetState,
    clamp,
    rect_contains,
)

from .button import Button, Checkbox, ToggleButton
from .label import TextLabel
from .modal import ModalDialog
from .palette import PaletteGrid, PaletteItem
from .renderer import NullRenderer, RenderCommand, RecordingRenderer
from .scroll import ScrollContainer
from .slider import Slider, SliderOrientation
from .theme import THEME_MANAGER, Theme, ThemeManager, ThemeMetrics, ThemePalette
from .tooltip import Tooltip

__all__ = [
    "Color",
    "Point",
    "Rect",
    "UIEvent",
    "UIWidget",
    "WidgetRenderer",
    "WidgetState",
    "clamp",
    "rect_contains",
    "Button",
    "ToggleButton",
    "Checkbox",
    "TextLabel",
    "Slider",
    "SliderOrientation",
    "ScrollContainer",
    "ModalDialog",
    "PaletteGrid",
    "PaletteItem",
    "Tooltip",
    "Theme",
    "ThemePalette",
    "ThemeMetrics",
    "ThemeManager",
    "THEME_MANAGER",
    "RecordingRenderer",
    "RenderCommand",
    "NullRenderer",
]
