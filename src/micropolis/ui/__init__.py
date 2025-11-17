"""pygame UI package scaffolding for Micropolis."""

from .asset_service import (
    AssetService,
    SoundRouter,
    SpriteSheet,
    SpriteSheetSpec,
    ThemeService,
    get_default_asset_service,
    get_default_theme_service,
    set_default_asset_service,
    set_default_theme_service,
)
from .cursor_manager import CursorManager
from .editor_mouse_handler import EditorMouseHandler
from .event_bus import (
    BusEvent,
    EventBus,
    get_default_event_bus,
    set_default_event_bus,
)
from .hit_testing import HitTester, get_hit_tester
from .keybindings_overlay import KeybindingsOverlay
from .map_mouse_handler import GraphMouseHandler, MapMouseHandler
from .mouse_controller import (
    AutoPanController,
    MouseButton,
    MouseInputController,
    MouseMode,
)
from .panel_manager import (
    PanelFactory,
    PanelLookupError,
    PanelManager,
    PanelProtocol,
    PanelRegistrationError,
)
from .sugar_bridge import (
    SugarCommand,
    SugarProtocolBridge,
    get_default_sugar_bridge,
    set_default_sugar_bridge,
)
from .timer_service import (
    TimerEvent,
    TimerService,
    get_default_timer_service,
    set_default_timer_service,
)
from .uipanel import Rect, UIPanel
from .widgets import (
    Button,
    Checkbox,
    ModalDialog,
    PaletteGrid,
    PaletteItem,
    RecordingRenderer,
    RenderCommand,
    ScrollContainer,
    Slider,
    SliderOrientation,
    TextLabel,
    Theme,
    ThemeManager,
    ThemeMetrics,
    ThemePalette,
    ToggleButton,
    Tooltip,
)

__all__ = [
    "AssetService",
    "ThemeService",
    "SoundRouter",
    "SpriteSheet",
    "SpriteSheetSpec",
    "get_default_asset_service",
    "set_default_asset_service",
    "get_default_theme_service",
    "set_default_theme_service",
    "CursorManager",
    "HitTester",
    "get_hit_tester",
    "MouseInputController",
    "MouseButton",
    "MouseMode",
    "AutoPanController",
    "EditorMouseHandler",
    "MapMouseHandler",
    "GraphMouseHandler",
    "PanelManager",
    "PanelFactory",
    "PanelProtocol",
    "PanelRegistrationError",
    "PanelLookupError",
    "KeybindingsOverlay",
    "EventBus",
    "BusEvent",
    "get_default_event_bus",
    "set_default_event_bus",
    "SugarCommand",
    "SugarProtocolBridge",
    "get_default_sugar_bridge",
    "set_default_sugar_bridge",
    "TimerService",
    "TimerEvent",
    "get_default_timer_service",
    "set_default_timer_service",
    "UIPanel",
    "Rect",
    "Button",
    "ToggleButton",
    "Checkbox",
    "Slider",
    "SliderOrientation",
    "ScrollContainer",
    "ModalDialog",
    "PaletteGrid",
    "PaletteItem",
    "Tooltip",
    "TextLabel",
    "Theme",
    "ThemePalette",
    "ThemeMetrics",
    "ThemeManager",
    "RecordingRenderer",
    "RenderCommand",
]
