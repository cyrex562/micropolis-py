"""Budget panel implementation for the pygame UI stack."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from micropolis import budget as budget_module
from micropolis.context import AppContext
from micropolis.ui.event_bus import EventBus, get_default_event_bus
from micropolis.ui.timer_service import TimerEvent
from micropolis.ui.uipanel import UIPanel
from micropolis.ui.widgets import (
    Button,
    ModalDialog,
    NullRenderer,
    RecordingRenderer,
    Slider,
    TextLabel,
    Theme,
    ThemeManager,
    UIEvent,
    UIWidget,
    WidgetRenderer,
)

try:  # Optional dependency for real rendering
    import pygame

    _HAVE_PYGAME = True
except Exception:  # pragma: no cover - pygame optional in tests
    pygame = None  # type: ignore
    _HAVE_PYGAME = False


_AUTO_CANCEL_TIMEOUT_MS = 30000  # 30 seconds
_COUNTDOWN_UPDATE_INTERVAL_MS = 1000  # 1 second


@dataclass(frozen=True)
class BudgetPanelState:
    """Snapshot of the budget panel display for tests and diagnostics."""

    is_open: bool = False
    road_percent: float = 1.0
    fire_percent: float = 1.0
    police_percent: float = 1.0
    tax_rate: int = 7
    taxes_collected: int = 0
    cash_flow: int = 0
    previous_funds: int = 0
    current_funds: int = 0
    remaining_seconds: int = 0
    auto_budget_enabled: bool = False


class _PygameWidgetRenderer(WidgetRenderer):
    """Minimal pygame-backed renderer satisfying the widget protocol."""

    def __init__(self, surface: Any) -> None:
        if not _HAVE_PYGAME or surface is None:
            raise RuntimeError("pygame surface required")
        self._surface = surface
        self._font_cache: dict[tuple[str | None, int | None], Any] = {}

    def _color(self, color: tuple[int, int, int, int]) -> tuple[int, int, int]:
        r, g, b, _ = color
        return int(r), int(g), int(b)

    def _font(self, font: str | None, size: int | None) -> Any:
        key = (font, size)
        cached = self._font_cache.get(key)
        if cached is not None:
            return cached
        resolved = pygame.font.SysFont(font or "dejavusans", size or 16)
        self._font_cache[key] = resolved
        return resolved

    def draw_rect(
        self,
        rect: tuple[int, int, int, int],
        color: tuple[int, int, int, int],
        border: bool = False,
        border_color: tuple[int, int, int, int] | None = None,
        radius: int = 0,
    ) -> None:
        pg_rect = pygame.Rect(rect)
        pygame.draw.rect(
            self._surface,
            self._color(color),
            pg_rect,
            width=0 if not border else 0,
            border_radius=radius,
        )
        if border:
            pygame.draw.rect(
                self._surface,
                self._color(border_color or color),
                pg_rect,
                width=1,
                border_radius=radius,
            )

    def draw_text(
        self,
        text: str,
        position: tuple[int, int],
        color: tuple[int, int, int, int],
        font: str | None = None,
        size: int | None = None,
    ) -> None:
        font_obj = self._font(font, size)
        surface = font_obj.render(text, True, self._color(color))
        text_rect = surface.get_rect()
        text_rect.center = position
        self._surface.blit(surface, text_rect)

    def draw_line(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int, int],
        width: int = 1,
    ) -> None:
        pygame.draw.line(self._surface, self._color(color), start, end, width)

    def draw_image(
        self,
        image_id: str,
        dest: tuple[int, int, int, int],
        tint: tuple[int, int, int, int] | None = None,
    ) -> None:  # pragma: no cover - images not yet used
        return None


class _FundingSliderWidget(UIWidget):
    """Composite widget combining a slider and label for funding allocation."""

    def __init__(
        self,
        label: str,
        rect: tuple[int, int, int, int],
        theme: Theme,
        on_change: callable,
    ) -> None:
        super().__init__(widget_id=f"funding-{label.lower()}", rect=rect)
        self._label = label
        self._on_change = on_change
        self._max_value = 0
        self._percent = 1.0

        x, y, w, h = rect
        padding = 8

        self.title_label = TextLabel(
            f"{label} Fund",
            widget_id=f"{label.lower()}-title",
        )
        self.title_label.set_rect((x, y, w, 24))

        self.request_label = TextLabel(
            "100% of $0 = $0",
            widget_id=f"{label.lower()}-request",
        )
        self.request_label.set_rect((x, y + 30, w, 20))

        self.slider = Slider(
            widget_id=f"{label.lower()}-slider",
            rect=(x + padding, y + 56, w - padding * 2, 28),
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.01,
            on_change=self._handle_slider_change,
        )

        self.add_child(self.title_label)
        self.add_child(self.request_label)
        self.add_child(self.slider)

    def set_funding(self, max_value: int, percent: float) -> None:
        self._max_value = max_value
        self._percent = percent
        allocated = int(max_value * percent)
        self.request_label.set_text(
            f"{int(percent * 100)}% of ${max_value:,} = ${allocated:,}"
        )
        self.slider.set_value(percent, fire=False)

    def _handle_slider_change(self, slider: Slider, value: float) -> None:
        self._percent = value
        allocated = int(self._max_value * value)
        self.request_label.set_text(
            f"{int(value * 100)}% of ${self._max_value:,} = ${allocated:,}"
        )
        if self._on_change:
            self._on_change(value)

    def on_render(self, renderer: WidgetRenderer) -> None:
        palette = self.theme.palette if self.theme else None
        if palette:
            renderer.draw_rect(
                self.rect,
                palette.surface,
                border=True,
                border_color=palette.border,
            )


class _BudgetDialogView(UIWidget):
    """Widget tree for the budget dialog modal."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        theme: Theme,
        context: AppContext,
    ) -> None:
        super().__init__(widget_id="budget-dialog", rect=rect)
        self.context = context

        x, y, w, h = rect
        padding = 16

        # Title
        self.title_label = TextLabel(
            "Micropolis has paused to set the budget...",
            widget_id="budget-title",
        )
        self.title_label.set_rect((x + padding, y + padding, w - padding * 2, 32))
        self.add_child(self.title_label)

        # Left column - financial info
        left_x = x + padding
        left_w = (w - padding * 3) // 2
        info_y = y + 64
        info_h = 80

        self.collected_label = TextLabel("Taxes Collected", widget_id="collected-title")
        self.collected_label.set_rect((left_x, info_y, left_w, 24))
        self.add_child(self.collected_label)

        self.collected_value = TextLabel("$0", widget_id="collected-value")
        self.collected_value.set_rect((left_x, info_y + 28, left_w, 24))
        self.add_child(self.collected_value)

        self.cashflow_label = TextLabel("Cash Flow", widget_id="cashflow-title")
        self.cashflow_label.set_rect((left_x, info_y + info_h, left_w, 24))
        self.add_child(self.cashflow_label)

        self.cashflow_value = TextLabel("+$0", widget_id="cashflow-value")
        self.cashflow_value.set_rect((left_x, info_y + info_h + 28, left_w, 24))
        self.add_child(self.cashflow_value)

        self.previous_label = TextLabel("Previous Funds", widget_id="previous-title")
        self.previous_label.set_rect((left_x, info_y + info_h * 2, left_w, 24))
        self.add_child(self.previous_label)

        self.previous_value = TextLabel("$0", widget_id="previous-value")
        self.previous_value.set_rect((left_x, info_y + info_h * 2 + 28, left_w, 24))
        self.add_child(self.previous_value)

        self.current_label = TextLabel("Current Funds", widget_id="current-title")
        self.current_label.set_rect((left_x, info_y + info_h * 3, left_w, 24))
        self.add_child(self.current_label)

        self.current_value = TextLabel("$0", widget_id="current-value")
        self.current_value.set_rect((left_x, info_y + info_h * 3 + 28, left_w, 24))
        self.add_child(self.current_value)

        # Right column - funding sliders
        right_x = x + padding * 2 + left_w
        right_w = left_w
        slider_h = 100

        self.road_slider = _FundingSliderWidget(
            "Road",
            (right_x, info_y, right_w, slider_h),
            theme,
            lambda v: self._handle_road_change(v),
        )
        self.add_child(self.road_slider)

        self.fire_slider = _FundingSliderWidget(
            "Fire",
            (right_x, info_y + slider_h + padding, right_w, slider_h),
            theme,
            lambda v: self._handle_fire_change(v),
        )
        self.add_child(self.fire_slider)

        self.police_slider = _FundingSliderWidget(
            "Police",
            (right_x, info_y + (slider_h + padding) * 2, right_w, slider_h),
            theme,
            lambda v: self._handle_police_change(v),
        )
        self.add_child(self.police_slider)

        # Tax rate slider
        tax_y = info_y + (slider_h + padding) * 3
        self.tax_label = TextLabel("Tax Rate", widget_id="tax-title")
        self.tax_label.set_rect((right_x, tax_y, right_w, 24))
        self.add_child(self.tax_label)

        self.tax_rate_label = TextLabel("7%", widget_id="tax-rate")
        self.tax_rate_label.set_rect((right_x, tax_y + 28, right_w, 20))
        self.add_child(self.tax_rate_label)

        self.tax_slider = Slider(
            widget_id="tax-slider",
            rect=(right_x + 8, tax_y + 54, right_w - 16, 28),
            min_value=0,
            max_value=20,
            value=7,
            step=1,
            on_change=self._handle_tax_change,
        )
        self.add_child(self.tax_slider)

        # Bottom buttons
        button_y = y + h - 200
        button_w = 240
        button_h = 32
        button_spacing = 8
        center_x = x + w // 2

        self.continue_button = Button(
            "Continue With These Figures",
            widget_id="continue-button",
            rect=(center_x - button_w // 2, button_y, button_w, button_h),
            on_click=lambda _: self._handle_continue(),
        )
        self.add_child(self.continue_button)

        self.reset_button = Button(
            "Reset to Original Figures",
            widget_id="reset-button",
            rect=(
                center_x - button_w // 2,
                button_y + button_h + button_spacing,
                button_w,
                button_h,
            ),
            on_click=lambda _: self._handle_reset(),
        )
        self.add_child(self.reset_button)

        self.cancel_button = Button(
            "Cancel Changes and Continue",
            widget_id="cancel-button",
            rect=(
                center_x - button_w // 2,
                button_y + (button_h + button_spacing) * 2,
                button_w,
                button_h,
            ),
            on_click=lambda _: self._handle_cancel(),
        )
        self.add_child(self.cancel_button)

        self.timer_button = Button(
            "Timeout in 30 seconds...",
            widget_id="timer-button",
            rect=(
                center_x - button_w // 2,
                button_y + (button_h + button_spacing) * 3,
                button_w,
                button_h,
            ),
            on_click=lambda _: self._handle_toggle_timer(),
        )
        self.add_child(self.timer_button)

        self.autobudget_button = Button(
            "Enable Auto Budget",
            widget_id="autobudget-button",
            rect=(
                center_x - button_w // 2,
                button_y + (button_h + button_spacing) * 4,
                button_w,
                button_h,
            ),
            on_click=lambda _: self._handle_toggle_autobudget(),
        )
        self.add_child(self.autobudget_button)

        self._on_continue = None
        self._on_reset = None
        self._on_cancel = None
        self._original_values = {}

    def set_callbacks(self, on_continue, on_reset, on_cancel):
        self._on_continue = on_continue
        self._on_reset = on_reset
        self._on_cancel = on_cancel

    def update_financial_display(
        self,
        collected: int,
        cash_flow: int,
        previous: int,
        current: int,
    ) -> None:
        self.collected_value.set_text(f"${collected:,}")
        flow_str = f"+${cash_flow:,}" if cash_flow >= 0 else f"-${abs(cash_flow):,}"
        self.cashflow_value.set_text(flow_str)
        self.previous_value.set_text(f"${previous:,}")
        self.current_value.set_text(f"${current:,}")

    def update_funding_sliders(
        self,
        road_max: int,
        road_percent: float,
        fire_max: int,
        fire_percent: float,
        police_max: int,
        police_percent: float,
    ) -> None:
        self.road_slider.set_funding(road_max, road_percent)
        self.fire_slider.set_funding(fire_max, fire_percent)
        self.police_slider.set_funding(police_max, police_percent)

    def update_tax_rate(self, rate: int) -> None:
        self.tax_rate_label.set_text(f"{rate}%")
        self.tax_slider.set_value(rate, fire=False)

    def update_timer_display(self, seconds: int) -> None:
        self.timer_button.label = f"Timeout in {seconds} seconds..."
        self.timer_button.invalidate()

    def update_autobudget_button(self, enabled: bool) -> None:
        self.autobudget_button.label = (
            "Disable Auto Budget" if enabled else "Enable Auto Budget"
        )
        self.autobudget_button.invalidate()

    def store_original_values(self) -> None:
        self._original_values = {
            "road_percent": self.context.road_percent,
            "fire_percent": self.context.fire_percent,
            "police_percent": self.context.police_percent,
            "tax_rate": self.context.city_tax,
        }

    def _handle_road_change(self, value: float) -> None:
        budget_module.set_road_percent(self.context, value)

    def _handle_fire_change(self, value: float) -> None:
        budget_module.set_fire_percent(self.context, value)

    def _handle_police_change(self, value: float) -> None:
        budget_module.set_police_percent(self.context, value)

    def _handle_tax_change(self, slider: Slider, value: float) -> None:
        tax_rate = int(value)
        self.context.city_tax = tax_rate
        self.tax_rate_label.set_text(f"{tax_rate}%")

    def _handle_continue(self) -> None:
        if self._on_continue:
            self._on_continue()

    def _handle_reset(self) -> None:
        if self._original_values:
            self.context.road_percent = self._original_values["road_percent"]
            self.context.fire_percent = self._original_values["fire_percent"]
            self.context.police_percent = self._original_values["police_percent"]
            self.context.city_tax = self._original_values["tax_rate"]

            self.road_slider.set_funding(
                self.context.road_max_value,
                self.context.road_percent,
            )
            self.fire_slider.set_funding(
                self.context.fire_max_value,
                self.context.fire_percent,
            )
            self.police_slider.set_funding(
                self.context.police_max_value,
                self.context.police_percent,
            )
            self.update_tax_rate(self.context.city_tax)

        if self._on_reset:
            self._on_reset()

    def _handle_cancel(self) -> None:
        self._handle_reset()  # Reset first
        if self._on_cancel:
            self._on_cancel()

    def _handle_toggle_timer(self) -> None:
        # Timer toggle would be implemented here
        pass

    def _handle_toggle_autobudget(self) -> None:
        self.context.auto_budget = not self.context.auto_budget
        self.update_autobudget_button(self.context.auto_budget)

    def on_render(self, renderer: WidgetRenderer) -> None:
        palette = self.theme.palette if self.theme else None
        if palette:
            renderer.draw_rect(
                self.rect,
                palette.surface,
                border=True,
                border_color=palette.border,
                radius=8,
            )


class BudgetPanel(UIPanel):
    """Modal budget dialog mirroring `wbudget.tcl`."""

    legacy_name = "BudgetWindows"

    def __init__(self, manager, context: AppContext) -> None:
        super().__init__(manager, context)
        self.legacy_name = "BudgetWindows"  # Restore after parent init
        self.visible = False  # Budget modal is hidden until opened
        self._theme = ThemeManager().current
        self._event_bus: EventBus = (
            getattr(context, "event_bus", None) or get_default_event_bus()
        )
        self._state = BudgetPanelState()
        self._renderer = RecordingRenderer()
        self._timer_id: str | None = None
        self._countdown_timer_id: str | None = None
        self._remaining_seconds = 30
        self._timer_enabled = True
        self._budget_subscription_id: str | None = None

        # Create modal dialog
        self._modal = ModalDialog(
            widget_id="budget-modal",
            rect=(0, 0, 1024, 768),
            overlay_color=(0, 0, 0, 180),
            dismiss_on_background=False,
        )

        # Create dialog content
        dialog_rect = (112, 34, 800, 700)
        self._dialog_view = _BudgetDialogView(dialog_rect, self._theme, context)
        self._dialog_view.set_callbacks(
            on_continue=self._handle_budget_accept,
            on_reset=self._handle_budget_reset,
            on_cancel=self._handle_budget_cancel,
        )
        self._modal.set_content(self._dialog_view)

    # Lifecycle ------------------------------------------------------------
    def did_mount(self) -> None:
        self.set_rect((0, 0, 1024, 768))
        self._register_event_subscriptions()
        self.hide()  # Start hidden, shown on budget trigger

    def did_unmount(self) -> None:
        self._unregister_event_subscriptions()
        self._stop_countdown_timer()

    # Public API -----------------------------------------------------------
    def open_budget_dialog(self) -> None:
        """Open the budget dialog and pause simulation."""
        if self._state.is_open:
            return

        # Store original values for reset
        self._dialog_view.store_original_values()

        # Refresh data from context
        self.refresh_from_context()

        # Pause simulation
        self.context.sim_paused = True

        # Open modal
        self._modal.open()
        self.show()

        # Start countdown timer
        self._start_countdown_timer()

        # Update state
        self._state = BudgetPanelState(
            is_open=True,
            road_percent=self.context.road_percent,
            fire_percent=self.context.fire_percent,
            police_percent=self.context.police_percent,
            tax_rate=self.context.city_tax,
            taxes_collected=self.context.tax_fund,
            previous_funds=self.context.total_funds,
            auto_budget_enabled=self.context.auto_budget,
        )

        # Publish event
        self._event_bus.publish(
            "budget.opened",
            {},
            source="budget-panel",
            tags=("ui", "budget"),
            defer=True,
        )

    def close_budget_dialog(self) -> None:
        """Close the budget dialog and resume simulation."""
        if not self._state.is_open:
            return

        self._stop_countdown_timer()
        self._modal.close()
        self.hide()
        self.context.sim_paused = False

        self._state = BudgetPanelState(is_open=False)

        # Publish event
        self._event_bus.publish(
            "budget.closed",
            {},
            source="budget-panel",
            tags=("ui", "budget"),
            defer=True,
        )

    # Rendering ------------------------------------------------------------
    def draw(self, surface: Any) -> None:
        if not self.visible:
            return

        renderer: WidgetRenderer
        if isinstance(surface, WidgetRenderer):
            renderer = surface
        elif _HAVE_PYGAME and isinstance(surface, pygame.Surface):
            renderer = _PygameWidgetRenderer(surface)
        else:
            renderer = self._renderer if surface is None else NullRenderer()

        self._modal.render(renderer)

    # Event handling -------------------------------------------------------
    def handle_panel_event(self, event: Any) -> bool:
        if not self.visible:
            return False

        ui_event = self._convert_event(event)
        if ui_event is None:
            return False

        return self._modal.handle_event(ui_event)

    def _convert_event(self, event: Any) -> UIEvent | None:
        if isinstance(event, UIEvent):
            return event
        if event is None:
            return None

        type_name = getattr(event, "type", None)
        if isinstance(type_name, int):
            # pygame event type
            if type_name == 4:  # MOUSEMOTION
                type_str = "mouse_move"
            elif type_name == 5:  # MOUSEBUTTONDOWN
                type_str = "mouse_down"
            elif type_name == 6:  # MOUSEBUTTONUP
                type_str = "mouse_up"
            elif type_name == 2:  # KEYDOWN
                type_str = "key_down"
            elif type_name == 3:  # KEYUP
                type_str = "key_up"
            else:
                return None
        elif isinstance(type_name, str):
            type_str = type_name.lower()
        else:
            return None

        pos = getattr(event, "pos", None) or getattr(event, "position", None)
        button = getattr(event, "button", None)
        key = getattr(event, "key", None)
        unicode_text = getattr(event, "unicode", None)

        return UIEvent(
            type=type_str,
            position=pos,
            button=button,
            key=key,
            unicode=unicode_text,
        )

    # Data updates ---------------------------------------------------------
    def refresh_from_context(self) -> None:
        """Refresh all display values from context."""
        ctx = self.context

        # Calculate cash flow
        cash_flow = ctx.tax_fund - ctx.fire_value - ctx.police_value - ctx.road_value
        current_funds = ctx.total_funds + cash_flow

        # Update financial display
        self._dialog_view.update_financial_display(
            collected=ctx.tax_fund,
            cash_flow=cash_flow,
            previous=ctx.total_funds,
            current=current_funds,
        )

        # Update funding sliders
        self._dialog_view.update_funding_sliders(
            road_max=ctx.road_max_value,
            road_percent=ctx.road_percent,
            fire_max=ctx.fire_max_value,
            fire_percent=ctx.fire_percent,
            police_max=ctx.police_max_value,
            police_percent=ctx.police_percent,
        )

        # Update tax rate
        self._dialog_view.update_tax_rate(ctx.city_tax)

        # Update auto budget button
        self._dialog_view.update_autobudget_button(ctx.auto_budget)

    # Timer management -----------------------------------------------------
    def _start_countdown_timer(self) -> None:
        self._remaining_seconds = _AUTO_CANCEL_TIMEOUT_MS // 1000
        self._timer_enabled = True
        self._dialog_view.update_timer_display(self._remaining_seconds)

        self._countdown_timer_id = self.manager.timer_service.call_every(
            _COUNTDOWN_UPDATE_INTERVAL_MS,
            self._handle_countdown_tick,
            simulation_bound=False,
            tags=("ui", "budget", "countdown"),
        )

    def _stop_countdown_timer(self) -> None:
        if self._countdown_timer_id and self.manager.timer_service.has_timer(
            self._countdown_timer_id
        ):
            self.manager.timer_service.cancel(self._countdown_timer_id)
        self._countdown_timer_id = None

    def _handle_countdown_tick(self, _: TimerEvent) -> None:
        if not self._timer_enabled:
            return

        self._remaining_seconds -= 1
        self._dialog_view.update_timer_display(self._remaining_seconds)

        if self._remaining_seconds <= 0:
            self._handle_budget_cancel()

    # Button handlers ------------------------------------------------------
    def _handle_budget_accept(self) -> None:
        """Accept budget and continue."""
        ctx = self.context

        # Apply funding allocations
        ctx.fire_spend = ctx.fire_value
        ctx.police_spend = ctx.police_value
        ctx.road_spend = ctx.road_value

        total = ctx.fire_spend + ctx.police_spend + ctx.road_spend
        more_dough = ctx.tax_fund - total
        budget_module.spend(ctx, -more_dough)

        # Update budget displays
        budget_module.draw_budget_window(ctx)
        budget_module.draw_curr_percents(ctx)
        budget_module.update_heads()

        # Publish event
        self._event_bus.publish(
            "budget.accepted",
            {
                "fire": ctx.fire_spend,
                "police": ctx.police_spend,
                "road": ctx.road_spend,
                "tax_rate": ctx.city_tax,
            },
            source="budget-panel",
            tags=("budget", "accepted"),
            defer=True,
        )

        self.close_budget_dialog()

    def _handle_budget_reset(self) -> None:
        """Reset to original values."""
        self.refresh_from_context()

        self._event_bus.publish(
            "budget.reset",
            {},
            source="budget-panel",
            tags=("budget", "reset"),
            defer=True,
        )

    def _handle_budget_cancel(self) -> None:
        """Cancel changes and close."""
        # Reset is called by dialog view before cancel

        self._event_bus.publish(
            "budget.cancelled",
            {},
            source="budget-panel",
            tags=("budget", "cancelled"),
            defer=True,
        )

        self.close_budget_dialog()

    # Event subscriptions --------------------------------------------------
    def _register_event_subscriptions(self) -> None:
        self._budget_subscription_id = self._event_bus.subscribe(
            "simulation.budget_requested",
            self._handle_budget_requested,
        )

    def _unregister_event_subscriptions(self) -> None:
        if self._budget_subscription_id:
            self._event_bus.unsubscribe(self._budget_subscription_id)
            self._budget_subscription_id = None

    def _handle_budget_requested(self, event) -> None:
        """Handle budget request from simulation."""
        self.open_budget_dialog()

    # State snapshot -------------------------------------------------------
    def get_state(self) -> BudgetPanelState:
        """Get current panel state for testing."""
        return self._state


__all__ = ["BudgetPanel", "BudgetPanelState"]
