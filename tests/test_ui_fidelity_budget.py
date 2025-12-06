import pytest
from unittest.mock import Mock, patch
from micropolis.context import AppContext
from micropolis.app_config import AppConfig
from micropolis.ui.panel_manager import PanelManager
from micropolis.ui.panels.budget_panel import BudgetPanel


class TestBudgetPanelFidelity:
    @pytest.fixture
    def context(self):
        config = AppConfig()
        ctx = AppContext(config=config)
        ctx.total_funds = 10000
        ctx.tax_fund = 500
        ctx.city_tax = 7
        ctx.road_percent = 1.0
        ctx.fire_percent = 1.0
        ctx.police_percent = 1.0
        return ctx

    @pytest.fixture
    def manager(self, context):
        return PanelManager(context)

    @pytest.fixture
    def panel(self, manager, context):
        panel = BudgetPanel(manager, context)
        panel.did_mount()
        return panel

    def test_initial_state_sync(self, panel, context):
        """Verify panel initializes with values from context."""
        panel.open_budget_dialog()

        # Access internal view widgets
        view = panel._dialog_view

        assert view.tax_rate_label.text == "7%"
        assert view.tax_slider.value == 7

        assert view.road_slider._percent == 1.0
        assert view.fire_slider._percent == 1.0
        assert view.police_slider._percent == 1.0

    def test_tax_slider_update(self, panel, context):
        """Verify moving tax slider updates label and context."""
        panel.open_budget_dialog()
        view = panel._dialog_view

        # Simulate slider movement to 9%
        view.tax_slider.set_value(9)

        assert context.city_tax == 9
        assert view.tax_rate_label.text == "9%"

    def test_funding_slider_calculations(self, panel, context):
        """Verify funding sliders display correct calculated amounts."""
        context.road_max_value = 1000
        panel.open_budget_dialog()
        view = panel._dialog_view

        # 100% of 1000
        assert "100% of $1,000" in view.road_slider.request_label.text

        # Change to 50%
        view.road_slider.slider.set_value(0.5)

        assert "50% of $1,000" in view.road_slider.request_label.text
        # Note: Actual context percent only updates on accept?
        # Checking implementation: _handle_road_change calls set_road_percent which updates context immediately?
        # Let's verify logic in budget_module or if it's stubbed.
        # But here we act on the slider widget.

    def test_financial_info_display(self, panel, context):
        """Verify collected taxes and cashflow display."""
        context.tax_fund = 2000
        context.fire_value = 100
        context.police_value = 100
        context.road_value = 100
        # Cash flow = 2000 - 300 = 1700

        panel.open_budget_dialog()
        view = panel._dialog_view

        assert view.collected_value.text == "$2,000"
        assert view.cashflow_value.text == "+$1,700"

    def test_budget_acceptance(self, panel, context):
        """Verify budget acceptance commits changes."""
        panel.open_budget_dialog()

        # Capture current funds
        start_funds = context.total_funds

        # Set some spending
        context.fire_value = 100
        context.police_value = 100
        context.road_value = 100
        context.tax_fund = 0
        # Deficit of 300

        # We need to mock budget_module.spend to verify it's called
        with patch("micropolis.ui.panels.budget_panel.budget_module") as mock_budget:
            panel._handle_budget_accept()

            # Should spend logic: more_dough = tax_fund - expenses = 0 - 300 = -300
            # spend(-more_dough) -> spend(300)
            mock_budget.spend.assert_called_with(context, 300)

            assert not panel._state.is_open
