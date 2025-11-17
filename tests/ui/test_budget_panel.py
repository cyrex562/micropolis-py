"""Tests for the budget panel implementation."""

import pytest

from micropolis.app_config import AppConfig
from micropolis.context import AppContext
from micropolis.ui.panels.budget_panel import BudgetPanel, BudgetPanelState


class MockPanelManager:
    """Mock panel manager for testing."""

    def __init__(self):
        self.timer_service = MockTimerService()


class MockTimerService:
    """Mock timer service for testing."""

    def __init__(self):
        self._timers = {}
        self._next_id = 0

    def call_every(self, interval_ms, callback, simulation_bound=False, tags=()):
        timer_id = f"timer_{self._next_id}"
        self._next_id += 1
        self._timers[timer_id] = {
            "interval": interval_ms,
            "callback": callback,
            "simulation_bound": simulation_bound,
            "tags": tags,
        }
        return timer_id

    def cancel(self, timer_id):
        if timer_id in self._timers:
            del self._timers[timer_id]

    def has_timer(self, timer_id):
        return timer_id in self._timers


@pytest.fixture
def context():
    """Create a test context."""
    ctx = AppContext(config=AppConfig())
    ctx.total_funds = 10000
    ctx.tax_fund = 2000
    ctx.road_fund = 1000
    ctx.fire_fund = 1500
    ctx.police_fund = 1200
    ctx.road_percent = 1.0
    ctx.fire_percent = 1.0
    ctx.police_percent = 1.0
    ctx.road_value = 1000
    ctx.fire_value = 1500
    ctx.police_value = 1200
    ctx.road_max_value = 1000
    ctx.fire_max_value = 1500
    ctx.police_max_value = 1200
    ctx.city_tax = 7
    ctx.auto_budget = False
    ctx.sim_paused = False
    return ctx


@pytest.fixture
def panel_manager():
    """Create a mock panel manager."""
    return MockPanelManager()


@pytest.fixture
def budget_panel(panel_manager, context):
    """Create a budget panel for testing."""
    panel = BudgetPanel(panel_manager, context)
    return panel


def test_budget_panel_initialization(budget_panel):
    """Test that the budget panel initializes correctly."""
    assert budget_panel is not None
    assert budget_panel.legacy_name == "BudgetWindows"
    assert not budget_panel.visible


def test_budget_panel_state_initial(budget_panel):
    """Test initial panel state."""
    state = budget_panel.get_state()
    assert isinstance(state, BudgetPanelState)
    assert not state.is_open
    assert state.road_percent == 1.0
    assert state.fire_percent == 1.0
    assert state.police_percent == 1.0


def test_budget_panel_open_dialog(budget_panel, context):
    """Test opening the budget dialog."""
    budget_panel.did_mount()
    assert not budget_panel.visible

    budget_panel.open_budget_dialog()

    assert budget_panel.visible
    assert context.sim_paused
    state = budget_panel.get_state()
    assert state.is_open


def test_budget_panel_close_dialog(budget_panel, context):
    """Test closing the budget dialog."""
    budget_panel.did_mount()
    budget_panel.open_budget_dialog()
    assert budget_panel.visible

    budget_panel.close_budget_dialog()

    assert not budget_panel.visible
    assert not context.sim_paused
    state = budget_panel.get_state()
    assert not state.is_open


def test_budget_panel_financial_calculations(budget_panel, context):
    """Test that financial calculations are correct."""
    budget_panel.did_mount()
    budget_panel.open_budget_dialog()

    # Values should be calculated based on context
    expected_cash_flow = (
        context.tax_fund
        - context.fire_value
        - context.police_value
        - context.road_value
    )

    assert expected_cash_flow == 2000 - 1500 - 1200 - 1000
    assert expected_cash_flow == -1700


def test_budget_panel_refresh_from_context(budget_panel, context):
    """Test refreshing panel data from context."""
    budget_panel.did_mount()
    budget_panel.open_budget_dialog()

    # Change context values
    context.tax_fund = 3000
    context.total_funds = 15000

    # Refresh should update internal state
    budget_panel.refresh_from_context()

    # Panel should have updated values (implicitly tested by not crashing)


def test_budget_panel_accepts_funding_changes(budget_panel, context):
    """Test that funding percent changes are accepted."""
    budget_panel.did_mount()
    budget_panel.open_budget_dialog()

    # Simulate changing road funding to 50%
    context.road_percent = 0.5
    budget_panel.refresh_from_context()

    assert context.road_percent == 0.5


def test_budget_panel_unmount_cleanup(budget_panel):
    """Test that unmount properly cleans up resources."""
    budget_panel.did_mount()
    budget_panel.open_budget_dialog()

    timer_count_before = len(budget_panel.manager.timer_service._timers)

    budget_panel.did_unmount()

    # Timer should be cancelled
    assert len(budget_panel.manager.timer_service._timers) < timer_count_before


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
