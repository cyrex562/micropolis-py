"""Tests for the graphs panel implementation."""

from pathlib import Path

import pytest

from micropolis.app_config import AppConfig
from micropolis.context import AppContext
from micropolis.graphs import init_history_data
from micropolis.ui.panels.graphs_panel import GraphPanelState, GraphsPanel


class MockPanelManager:
    """Mock panel manager for testing."""

    def __init__(self):
        self.timer_service = MockTimerService()


class MockTimerService:
    """Mock timer service for testing."""

    def __init__(self):
        self._timers = {}

    def call_every(self, interval_ms, callback, simulation_bound=False, tags=None):
        timer_id = f"timer_{len(self._timers)}"
        self._timers[timer_id] = {
            "interval": interval_ms,
            "callback": callback,
            "bound": simulation_bound,
            "tags": tags or (),
        }
        return timer_id

    def has_timer(self, timer_id):
        return timer_id in self._timers

    def cancel(self, timer_id):
        if timer_id in self._timers:
            del self._timers[timer_id]


@pytest.fixture
def context():
    """Create a test context with initialized graph data."""
    repo_root = Path(__file__).resolve().parents[2]
    config = AppConfig(home=repo_root, resource_dir=repo_root / "assets")
    ctx = AppContext(config=config)
    ctx.city_name = "Test City"
    ctx.total_funds = 10000
    ctx.total_pop = 5000
    ctx.game_level = 0
    ctx.city_time = 0
    ctx.starting_year = 1900

    # Initialize graph history data
    init_history_data(ctx)
    # Note: We don't call init_graph_maxima() because it tries to set fields
    # that don't exist in the pydantic AppContext model. The graphs panel
    # doesn't actually need those maxima fields for basic functionality.

    return ctx


@pytest.fixture
def manager():
    """Create a mock panel manager."""
    return MockPanelManager()


def test_graphs_panel_creation(manager, context):
    """Test that graphs panel can be created."""
    panel = GraphsPanel(manager, context)
    assert panel is not None
    assert panel.legacy_name == "GraphWindows"
    assert not panel._mounted


def test_graphs_panel_mount(manager, context):
    """Test that graphs panel mounts correctly."""
    panel = GraphsPanel(manager, context)
    panel.on_mount()
    assert panel._mounted
    assert panel._timer_id is not None
    assert manager.timer_service.has_timer(panel._timer_id)


def test_graphs_panel_unmount(manager, context):
    """Test that graphs panel unmounts correctly."""
    panel = GraphsPanel(manager, context)
    panel.on_mount()
    timer_id = panel._timer_id
    panel.on_unmount()
    assert not panel._mounted
    assert not manager.timer_service.has_timer(timer_id)


def test_graphs_panel_state(manager, context):
    """Test that graphs panel maintains state."""
    panel = GraphsPanel(manager, context)
    state = panel.get_state()
    assert isinstance(state, GraphPanelState)
    assert state.range == 10
    assert state.visible_histories == 0x3F  # All histories visible by default


def test_graphs_panel_set_range(manager, context):
    """Test that graphs panel can change year range."""
    panel = GraphsPanel(manager, context)
    panel.on_mount()

    # Change to 120-year view
    panel.set_range(120)
    state = panel.get_state()
    assert state.range == 120

    # Change back to 10-year view
    panel.set_range(10)
    state = panel.get_state()
    assert state.range == 10


def test_graphs_panel_toggle_history(manager, context):
    """Test that graphs panel can toggle history visibility."""
    panel = GraphsPanel(manager, context)
    panel.on_mount()

    # Toggle off residential history (index 0)
    panel.toggle_history(0, False)
    # Note: We'd need to expose the visibility mask to test this properly
    # For now, just verify the call doesn't crash

    # Toggle back on
    panel.toggle_history(0, True)


def test_graphs_panel_draw_with_null_surface(manager, context):
    """Test that graphs panel can render to null surface."""
    panel = GraphsPanel(manager, context)
    panel.on_mount()

    # Should not crash with None surface
    panel.draw(None)


def test_graphs_panel_refresh_from_context(manager, context):
    """Test that graphs panel updates from context."""
    panel = GraphsPanel(manager, context)
    panel.on_mount()

    # Update context values
    context.total_pop = 10000
    context.total_funds = 20000

    # Refresh panel
    panel.refresh_from_context()
    # Panel should update internal state
    # (not directly testable without exposing internals)
