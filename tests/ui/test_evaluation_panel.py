"""Tests for the evaluation panel implementation."""

import pytest

from micropolis.app_config import AppConfig
from micropolis.context import AppContext
from micropolis.ui.panels.evaluation_panel import (
    EvaluationPanel,
    EvaluationPanelState,
)


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

    # Set up evaluation data
    ctx.city_score = 650
    ctx.delta_city_score = 25
    ctx.city_pop = 75000
    ctx.delta_city_pop = 5000
    ctx.city_class = 2  # City
    ctx.game_level = 1  # Medium
    ctx.city_ass_value = 50000000
    ctx.city_yes = 65
    ctx.city_no = 35
    ctx.city_time = 2400  # ~50 years
    ctx.starting_year = 1900
    ctx.total_pop = 1000  # Set to ensure evaluation runs

    # Initialize problem arrays (PROBNUM = 8 from constants)
    from micropolis.constants import PROBNUM

    ctx.problem_votes = [30, 25, 20, 15, 10, 5, 2, 0]
    ctx.problem_order = [0, 1, 2, 3, 4, 5, 6, 7]
    ctx.problem_table = [100, 80, 60, 40, 30, 20, 10, 0]
    ctx.problem_taken = [0] * PROBNUM

    # Evaluation settings
    ctx.auto_evaluation = False
    ctx.eval_notifications = True

    return ctx


@pytest.fixture
def panel_manager():
    """Create a mock panel manager."""
    return MockPanelManager()


@pytest.fixture
def evaluation_panel(panel_manager, context):
    """Create an evaluation panel for testing."""
    panel = EvaluationPanel(panel_manager, context)
    return panel


def test_evaluation_panel_initialization(evaluation_panel):
    """Test that the evaluation panel initializes correctly."""
    assert evaluation_panel is not None
    assert evaluation_panel.legacy_name == "EvaluationWindows"
    assert not evaluation_panel.visible


def test_evaluation_panel_state_initial(evaluation_panel):
    """Test initial panel state."""
    state = evaluation_panel.get_state()
    assert isinstance(state, EvaluationPanelState)
    assert not state.is_visible
    assert state.city_score == 0
    assert state.city_pop == 0
    assert not state.auto_evaluation


def test_evaluation_panel_open(evaluation_panel, context):
    """Test opening the evaluation panel."""
    evaluation_panel.did_mount()
    assert not evaluation_panel.visible

    evaluation_panel.open_evaluation()
    assert evaluation_panel.visible

    state = evaluation_panel.get_state()
    assert state.is_visible
    assert state.city_score == context.city_score
    assert state.city_pop == context.city_pop


def test_evaluation_panel_close(evaluation_panel):
    """Test closing the evaluation panel."""
    evaluation_panel.did_mount()
    evaluation_panel.open_evaluation()
    assert evaluation_panel.visible

    evaluation_panel.close_evaluation()
    assert not evaluation_panel.visible

    state = evaluation_panel.get_state()
    assert not state.is_visible


def test_evaluation_panel_toggle(evaluation_panel):
    """Test toggling the evaluation panel."""
    evaluation_panel.did_mount()

    # Initially closed
    assert not evaluation_panel.visible

    # Toggle open
    evaluation_panel.toggle_evaluation()
    assert evaluation_panel.visible

    # Toggle closed
    evaluation_panel.toggle_evaluation()
    assert not evaluation_panel.visible


def test_evaluation_panel_data_refresh(evaluation_panel, context):
    """Test that data refresh updates state correctly."""
    evaluation_panel.did_mount()
    evaluation_panel.open_evaluation()

    # Verify state reflects context data
    state = evaluation_panel.get_state()
    assert state.city_score == 650
    assert state.score_delta == 25
    assert state.city_pop == 75000
    assert state.pop_delta == 5000
    assert state.city_class == "CITY"
    assert state.game_level == "Medium"
    assert state.approval_yes == 65
    assert state.approval_no == 35


def test_evaluation_panel_problem_list(evaluation_panel, context):
    """Test that problems are correctly extracted and displayed."""
    evaluation_panel.did_mount()
    evaluation_panel.open_evaluation()

    state = evaluation_panel.get_state()
    problems = state.top_problems

    # Should have problems with votes > 0
    assert len(problems) > 0
    assert problems[0][1] >= problems[1][1]  # Sorted by vote percentage


def test_evaluation_panel_auto_evaluation_toggle(evaluation_panel, context):
    """Test auto-evaluation toggle functionality."""
    evaluation_panel.did_mount()
    evaluation_panel.open_evaluation()

    # Initially off
    assert not context.auto_evaluation

    # Enable auto-evaluation through dialog
    evaluation_panel._dialog_view._handle_auto_eval_toggle(True)
    assert context.auto_evaluation

    # Disable auto-evaluation
    evaluation_panel._dialog_view._handle_auto_eval_toggle(False)
    assert not context.auto_evaluation


def test_evaluation_panel_render_without_pygame(evaluation_panel):
    """Test that panel can render without pygame (using NullRenderer)."""
    evaluation_panel.did_mount()
    evaluation_panel.open_evaluation()

    # Should not raise an exception
    evaluation_panel.draw(None)


def test_evaluation_panel_unmount_cleanup(evaluation_panel):
    """Test that unmounting cleans up resources."""
    evaluation_panel.did_mount()
    evaluation_panel.open_evaluation()

    # Enable auto-eval to create timer
    evaluation_panel.context.auto_evaluation = True
    evaluation_panel._start_auto_eval_timer()
    timer_id = evaluation_panel._auto_eval_timer_id
    assert timer_id is not None

    # Unmount should cancel timer
    evaluation_panel.did_unmount()
    assert evaluation_panel._auto_eval_timer_id is None


def test_evaluation_panel_state_snapshot(evaluation_panel, context):
    """Test that state snapshot captures all relevant data."""
    evaluation_panel.did_mount()
    evaluation_panel.open_evaluation()

    state = evaluation_panel.get_state()

    # Verify all key fields are present
    assert hasattr(state, "is_visible")
    assert hasattr(state, "city_score")
    assert hasattr(state, "score_delta")
    assert hasattr(state, "city_pop")
    assert hasattr(state, "pop_delta")
    assert hasattr(state, "city_class")
    assert hasattr(state, "game_level")
    assert hasattr(state, "assessed_value")
    assert hasattr(state, "approval_yes")
    assert hasattr(state, "approval_no")
    assert hasattr(state, "top_problems")
    assert hasattr(state, "auto_evaluation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
