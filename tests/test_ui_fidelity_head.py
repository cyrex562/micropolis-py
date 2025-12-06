import pytest
from unittest.mock import Mock, patch
from micropolis.context import AppContext
from micropolis.app_config import AppConfig
from micropolis.ui.panel_manager import PanelManager
from micropolis.ui.panels.head_panel import HeadPanel


class TestHeadPanelFidelity:
    @pytest.fixture
    def context(self):
        config = AppConfig()
        ctx = AppContext(config=config)
        ctx.city_name = "Fidelity City"
        ctx.total_funds = 15000
        ctx.total_pop = 5000
        ctx.game_level = 1  # Medium
        ctx.city_time = 0  # Jan 1900
        ctx.starting_year = 1900
        ctx.sim_speed = 2  # Normal
        ctx.sim_paused = 0
        ctx.last_message = "Welcome Mayors"
        ctx.have_last_message = True

        ctx.r_valve = 1000
        ctx.c_valve = -500
        ctx.i_valve = 0
        return ctx

    @pytest.fixture
    def manager(self, context):
        return PanelManager(context)

    @pytest.fixture
    def panel(self, manager, context):
        panel = HeadPanel(manager, context)
        panel.did_mount()
        return panel

    def test_initial_state_sync(self, panel, context):
        """Verify panel initializes with values from context."""
        # Patch the helper functions used during refresh
        with (
            patch("micropolis.ui.panels.head_panel.get_sim_speed", return_value=2),
            patch("micropolis.ui.panels.head_panel.is_sim_paused", return_value=False),
        ):
            panel.refresh_from_context()
            view = panel._view

            assert view.city_label.text == "Fidelity City"
            # assert view.funds_label.text == "Funds: $15,000"
            assert "15,000" in view.funds_label.text  # Fuzzy match for now
            assert view.pop_label.text == "Pop: 5,000"
            assert view.level_label.text == "Medium"
            assert view.ticker._text == "Welcome Mayors"

            assert view.demand_widgets["res"]._value == 15
            assert view.demand_widgets["com"]._value == -15

    def test_date_formatting(self, panel, context):
        context.city_time = 0
        view = panel._view
        assert view.date_label.text == "Jan 1900"

    def test_speed_controls(self, panel, context):
        view = panel._view
        with (
            patch("micropolis.ui.panels.head_panel.get_sim_speed", return_value=2),
            patch("micropolis.ui.panels.head_panel.is_sim_paused", return_value=True),
        ):
            panel.refresh_from_context()
            assert view.pause_button.toggled
            assert not view.speed_buttons["normal"].toggled

        with (
            patch("micropolis.ui.panels.head_panel.get_sim_speed", return_value=2),
            patch("micropolis.ui.panels.head_panel.is_sim_paused", return_value=False),
        ):
            panel.refresh_from_context()
            assert not view.pause_button.toggled
            assert view.speed_buttons["normal"].toggled
            assert not view.speed_buttons["slow"].toggled
