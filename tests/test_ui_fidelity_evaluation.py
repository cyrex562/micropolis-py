import pytest
from unittest.mock import Mock, patch
from micropolis.context import AppContext
from micropolis.app_config import AppConfig
from micropolis.ui.panel_manager import PanelManager
from micropolis.ui.panels.evaluation_panel import EvaluationPanel, PROBLEM_STRINGS


class TestEvaluationPanelFidelity:
    @pytest.fixture
    def context(self):
        config = AppConfig()
        ctx = AppContext(config=config)
        ctx.city_score = 750
        ctx.delta_city_score = 10
        ctx.city_pop = 123456
        ctx.delta_city_pop = 500
        ctx.city_class = 2  # CITY
        ctx.game_level = 0  # Easy
        ctx.city_ass_value = 50000000
        ctx.city_yes = 60
        ctx.city_no = 40
        ctx.auto_evaluation = False

        # Initialize problem arrays (usually done in engine/sim logic)
        ctx.problem_votes = [0] * len(PROBLEM_STRINGS)
        ctx.problem_order = list(range(len(PROBLEM_STRINGS)))
        return ctx

    @pytest.fixture
    def manager(self, context):
        return PanelManager(context)

    @pytest.fixture
    def panel(self, manager, context):
        panel = EvaluationPanel(manager, context)
        panel.did_mount()
        return panel

    def test_initial_state_sync(self, panel, context):
        """Verify panel initializes with values from context."""
        panel.open_evaluation()
        view = panel._dialog_view

        assert view.score_value.text == "750"
        assert view.score_delta.text == "(+10)"
        assert view.approval_yes.text == "60% Yes"
        assert view.approval_no.text == "40% No"

        # Verify category rows
        assert view._category_rows["population"].value_label.text == "123,456"
        assert view._category_rows["class"].value_label.text == "CITY"
        assert view._category_rows["level"].value_label.text == "Easy"
        assert view._category_rows["value"].value_label.text == "$50,000,000"

    def test_problem_list_display(self, panel, context):
        """Verify top problems are displayed correctly."""
        # Setup mock problems
        # Crime (0) = 25%
        # Traffic (4) = 15%
        context.problem_votes[0] = 25
        context.problem_votes[4] = 15

        # Problem order should typically be sorted by votes in engine,
        # but UI uses problem_order directly.
        # Let's mock order: Crime first, then Traffic
        context.problem_order[0] = 0
        context.problem_order[1] = 4

        panel.open_evaluation()
        view = panel._dialog_view

        # Check first item (Crime)
        item0 = panel._dialog_view._problem_items[0]
        assert item0.visible
        assert item0.name_label.text == "Crime"
        assert item0.vote_label.text == "25%"

        # Check second item (Traffic)
        item1 = panel._dialog_view._problem_items[1]
        assert item1.visible
        assert item1.name_label.text == "Traffic"
        assert item1.vote_label.text == "15%"

        # Check unused items hidden
        assert not panel._dialog_view._problem_items[2].visible

    def test_city_class_mapping(self, panel, context):
        """Verify city class integer maps to correct string."""
        mappings = {
            0: "VILLAGE",
            1: "TOWN",
            2: "CITY",
            3: "CAPITAL",
            4: "METROPOLIS",
            5: "MEGALOPOLIS",
        }

        for class_id, expected_name in mappings.items():
            context.city_class = class_id
            panel.refresh_from_context()  # Trigger refresh directly
            assert (
                panel._dialog_view._category_rows["class"].value_label.text
                == expected_name
            )

    def test_auto_eval_toggle(self, panel, context):
        """Verify auto-evaluation checkbox updates context."""
        panel.open_evaluation()
        view = panel._dialog_view

        # Initial state false
        assert not context.auto_evaluation

        # Toggle UI
        view.auto_eval_checkbox.set_toggled(True)

        assert context.auto_evaluation

        # Toggle back
        view.auto_eval_checkbox.set_toggled(False)
        assert not context.auto_evaluation

    def test_score_color_logic(self, panel):
        """Verify score bar color logic."""
        # 750 -> Green
        assert panel._dialog_view._get_score_color(750) == (50, 200, 50, 255)
        # 550 -> Yellow
        assert panel._dialog_view._get_score_color(550) == (200, 200, 50, 255)
        # 350 -> Orange
        assert panel._dialog_view._get_score_color(350) == (200, 150, 50, 255)
        # 100 -> Red
        assert panel._dialog_view._get_score_color(100) == (200, 50, 50, 255)
