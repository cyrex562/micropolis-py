"""Editor options panel implementation.

This panel provides configuration options for the editor:
- AutoGoto: Automatically center view on important events
- Chalk Overlay: Show construction preview overlay
- Dynamic Filter: Apply dynamic filtering to map view
- Skip Frequency: Control editor redraw frequency
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from micropolis.context import AppContext
from micropolis.sim_control import (
    get_auto_goto,
    get_sim_skips,
    set_auto_goto,
    set_sim_skips,
)
from micropolis.ui.event_bus import EventBus, get_default_event_bus
from micropolis.ui.uipanel import UIPanel
from micropolis.ui.widgets.button import Checkbox
from micropolis.ui.widgets.label import TextLabel
from micropolis.ui.widgets.slider import Slider

if TYPE_CHECKING:
    from micropolis.ui.panel_manager import PanelManager
    from micropolis.ui.widgets.base import UIWidget

try:
    import pygame

    _HAVE_PYGAME = True
except Exception:  # pragma: no cover - pygame optional in tests
    pygame = None  # type: ignore
    _HAVE_PYGAME = False


class EditorOptionsPanel(UIPanel):
    """Editor configuration options panel."""

    def __init__(self, manager: PanelManager, context: AppContext) -> None:
        super().__init__(manager, context)
        self.panel_id = "editor_options"
        self.legacy_name = "EditorOptionsWindow"

        # Event bus subscription
        self._event_bus: EventBus = get_default_event_bus()
        self._subscriptions: list[Any] = []

        # Widgets
        self._widgets: list[UIWidget] = []
        self._auto_goto_checkbox: Checkbox | None = None
        self._chalk_overlay_checkbox: Checkbox | None = None
        self._dynamic_filter_checkbox: Checkbox | None = None
        self._skip_frequency_slider: Slider | None = None

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------
    def did_mount(self) -> None:
        """Initialize the options panel after mounting."""
        # Subscribe to relevant events
        self._subscriptions.append(
            self._event_bus.subscribe("editor.options.update", self._on_options_update)
        )

        # Create widgets
        self._create_widgets()

        # Load current values from context
        self._refresh_values()

    def did_unmount(self) -> None:
        """Clean up when panel is removed."""
        for sub in self._subscriptions:
            self._event_bus.unsubscribe(sub)
        self._subscriptions.clear()
        self._widgets.clear()

    def did_resize(self, size: tuple[int, int]) -> None:
        """Update layout when window resizes."""
        self._layout_widgets()
        self.invalidate()

    # ------------------------------------------------------------------
    # Widget creation and layout
    # ------------------------------------------------------------------
    def _create_widgets(self) -> None:
        """Create all option widgets."""
        x, y, w, h = self.rect

        # Title label
        title_label = TextLabel(
            text="Editor Options",
            widget_id="editor_options_title",
            rect=(x + 10, y + 10, w - 20, 30),
        )
        self._widgets.append(title_label)

        # AutoGoto checkbox
        self._auto_goto_checkbox = Checkbox(
            label="Auto Goto (center on events)",
            widget_id="auto_goto_checkbox",
            rect=(x + 20, y + 50, w - 40, 28),
            on_toggle=self._on_auto_goto_toggle,
        )
        self._widgets.append(self._auto_goto_checkbox)

        # Chalk Overlay checkbox
        self._chalk_overlay_checkbox = Checkbox(
            label="Chalk Overlay (construction preview)",
            widget_id="chalk_overlay_checkbox",
            rect=(x + 20, y + 85, w - 40, 28),
            on_toggle=self._on_chalk_overlay_toggle,
        )
        self._widgets.append(self._chalk_overlay_checkbox)

        # Dynamic Filter checkbox
        self._dynamic_filter_checkbox = Checkbox(
            label="Dynamic Filter (overlay filtering)",
            widget_id="dynamic_filter_checkbox",
            rect=(x + 20, y + 120, w - 40, 28),
            on_toggle=self._on_dynamic_filter_toggle,
        )
        self._widgets.append(self._dynamic_filter_checkbox)

        # Skip Frequency label
        skip_label = TextLabel(
            text="Editor Redraw Skip Frequency:",
            widget_id="skip_frequency_label",
            rect=(x + 20, y + 160, w - 40, 24),
        )
        self._widgets.append(skip_label)

        # Skip Frequency slider (0-10)
        self._skip_frequency_slider = Slider(
            widget_id="skip_frequency_slider",
            rect=(x + 20, y + 190, w - 40, 28),
            min_value=0.0,
            max_value=10.0,
            value=0.0,
            step=1.0,
            on_change=self._on_skip_frequency_change,
        )
        self._widgets.append(self._skip_frequency_slider)

        # Skip Frequency value display
        self._skip_value_label = TextLabel(
            text="0",
            widget_id="skip_value_label",
            rect=(x + 20, y + 225, w - 40, 24),
        )
        self._widgets.append(self._skip_value_label)

    def _layout_widgets(self) -> None:
        """Update widget positions based on panel rect."""
        x, y, w, h = self.rect

        # Re-position widgets
        widget_y = y + 10
        for widget in self._widgets:
            widget_x, _, widget_w, widget_h = widget.rect
            widget.rect = (x + (widget_x - self.rect[0]), widget_y, widget_w, widget_h)
            widget_y += widget_h + 5

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def draw(self, surface: Any) -> None:
        """Render the options panel."""
        if not _HAVE_PYGAME or not self.visible:
            return

        x, y, w, h = self.rect

        # Draw panel background
        pygame.draw.rect(surface, (50, 50, 55), (x, y, w, h))  # type: ignore
        pygame.draw.rect(surface, (80, 80, 85), (x, y, w, h), 2)  # type: ignore

        # Draw all widgets
        for widget in self._widgets:
            if hasattr(widget, "on_render"):
                # Use simple pygame rendering for now
                try:
                    self._render_widget(surface, widget)
                except Exception as e:
                    print(f"Error rendering widget {widget.widget_id}: {e}")

    def _render_widget(self, surface: Any, widget: UIWidget) -> None:
        """Simple widget rendering helper."""
        if not _HAVE_PYGAME:
            return

        # For checkboxes
        if isinstance(widget, Checkbox):
            x, y, w, h = widget.rect
            box_size = min(h - 4, 24)
            box_rect = (x, y + (h - box_size) // 2, box_size, box_size)

            # Draw checkbox box
            pygame.draw.rect(surface, (240, 240, 240), box_rect)  # type: ignore
            pygame.draw.rect(surface, (100, 100, 100), box_rect, 2)  # type: ignore

            # Draw checkmark if toggled
            if widget.toggled:
                pygame.draw.line(  # type: ignore
                    surface,
                    (0, 180, 0),
                    (box_rect[0] + 4, box_rect[1] + box_size // 2),
                    (box_rect[0] + box_size // 2, box_rect[1] + box_size - 4),
                    3,
                )
                pygame.draw.line(  # type: ignore
                    surface,
                    (0, 180, 0),
                    (box_rect[0] + box_size // 2, box_rect[1] + box_size - 4),
                    (box_rect[0] + box_size - 4, box_rect[1] + 4),
                    3,
                )

            # Draw label
            font = pygame.font.SysFont("dejavusans", 14)  # type: ignore
            text = font.render(widget.label, True, (220, 220, 220))
            surface.blit(text, (x + box_size + 8, y + h // 2 - 8))

        # For sliders
        elif isinstance(widget, Slider):
            x, y, w, h = widget.rect

            # Draw track
            track_rect = (x + 4, y + h // 2 - 2, w - 8, 4)
            pygame.draw.rect(surface, (100, 100, 100), track_rect)  # type: ignore

            # Draw knob
            ratio = (widget.value - widget.min_value) / max(
                widget.max_value - widget.min_value, 1e-6
            )
            knob_x = int(x + ratio * w)
            knob_y = y + h // 2
            knob_rect = (knob_x - 6, knob_y - 6, 12, 12)
            pygame.draw.rect(surface, (0, 180, 255), knob_rect)  # type: ignore
            pygame.draw.rect(surface, (100, 100, 100), knob_rect, 2)  # type: ignore

        # For labels
        elif isinstance(widget, TextLabel):
            x, y, w, h = widget.rect
            font = pygame.font.SysFont("dejavusans", 14)  # type: ignore
            text = font.render(widget.text, True, (220, 220, 220))
            surface.blit(text, (x, y))

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def handle_panel_event(self, event: Any) -> bool:
        """Handle pygame events for widget interaction."""
        if not _HAVE_PYGAME or not self.enabled:
            return False

        # Forward events to widgets
        for widget in self._widgets:
            if hasattr(widget, "on_event"):
                # Convert pygame event to UIEvent format
                ui_event = self._convert_event(event)
                if widget.on_event(ui_event):
                    self.invalidate()
                    return True

        return False

    def _convert_event(self, pg_event: Any) -> dict[str, Any]:
        """Convert pygame event to UIEvent format."""
        if not _HAVE_PYGAME:
            return {}

        if pg_event.type == pygame.MOUSEBUTTONDOWN:  # type: ignore
            return {
                "type": "mouse_down",
                "button": pg_event.button,
                "position": pg_event.pos,
            }
        elif pg_event.type == pygame.MOUSEBUTTONUP:  # type: ignore
            return {
                "type": "mouse_up",
                "button": pg_event.button,
                "position": pg_event.pos,
            }
        elif pg_event.type == pygame.MOUSEMOTION:  # type: ignore
            return {"type": "mouse_move", "position": pg_event.pos}
        elif pg_event.type == pygame.KEYDOWN:  # type: ignore
            return {"type": "key_down", "key": pg_event.key}
        elif pg_event.type == pygame.KEYUP:  # type: ignore
            return {"type": "key_up", "key": pg_event.key}

        return {}

    # ------------------------------------------------------------------
    # Widget callbacks
    # ------------------------------------------------------------------
    def _on_auto_goto_toggle(self, checkbox: Checkbox, toggled: bool) -> None:
        """Handle AutoGoto checkbox toggle."""
        set_auto_goto(self.context, toggled)
        self._event_bus.publish("editor.auto_goto.changed", {"enabled": toggled})

    def _on_chalk_overlay_toggle(self, checkbox: Checkbox, toggled: bool) -> None:
        """Handle Chalk Overlay checkbox toggle."""
        # Store in context (we'll add this field if needed)
        if not hasattr(self.context, "chalk_overlay"):
            self.context.chalk_overlay = toggled  # type: ignore
        else:
            self.context.chalk_overlay = toggled  # type: ignore

        self._event_bus.publish("editor.chalk_overlay.changed", {"enabled": toggled})

    def _on_dynamic_filter_toggle(self, checkbox: Checkbox, toggled: bool) -> None:
        """Handle Dynamic Filter checkbox toggle."""
        # Store in context (we'll add this field if needed)
        if not hasattr(self.context, "dynamic_filter"):
            self.context.dynamic_filter = toggled  # type: ignore
        else:
            self.context.dynamic_filter = toggled  # type: ignore

        self._event_bus.publish("editor.dynamic_filter.changed", {"enabled": toggled})

    def _on_skip_frequency_change(self, slider: Slider, value: float) -> None:
        """Handle skip frequency slider change."""
        skip_value = int(value)
        set_sim_skips(self.context, skip_value)

        # Update value label
        if self._skip_value_label:
            self._skip_value_label.text = str(skip_value)

        self._event_bus.publish("editor.skip_frequency.changed", {"value": skip_value})

    # ------------------------------------------------------------------
    # Value refresh
    # ------------------------------------------------------------------
    def _refresh_values(self) -> None:
        """Load current values from context into widgets."""
        # AutoGoto
        if self._auto_goto_checkbox:
            auto_goto = getattr(self.context, "auto_goto", None)
            if auto_goto is None:
                auto_goto = get_auto_goto(self.context)
            self._auto_goto_checkbox.set_toggled(bool(auto_goto), fire=False)

        # Chalk Overlay
        if self._chalk_overlay_checkbox:
            chalk_overlay = getattr(self.context, "chalk_overlay", True)
            self._chalk_overlay_checkbox.set_toggled(chalk_overlay, fire=False)

        # Dynamic Filter
        if self._dynamic_filter_checkbox:
            dynamic_filter = getattr(self.context, "dynamic_filter", False)
            self._dynamic_filter_checkbox.set_toggled(dynamic_filter, fire=False)

        # Skip Frequency
        if self._skip_frequency_slider:
            skip_value = getattr(self.context, "sim_skips", None)
            if skip_value is None:
                skip_value = get_sim_skips(self.context)
            self._skip_frequency_slider.set_value(float(skip_value), fire=False)

            if self._skip_value_label:
                self._skip_value_label.text = str(skip_value)

    def _on_options_update(self, data: Any) -> None:
        """Handle external options update events."""
        self._refresh_values()
        self.invalidate()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def show(self) -> None:
        """Show the options panel."""
        self.visible = True
        self._refresh_values()
        self.invalidate()

    def hide(self) -> None:
        """Hide the options panel."""
        self.visible = False
