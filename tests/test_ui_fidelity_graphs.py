import pytest
from unittest.mock import Mock, patch
from micropolis.context import AppContext
from micropolis.app_config import AppConfig
from micropolis.ui.panel_manager import PanelManager
from micropolis.ui.panels.graphs_panel import GraphsPanel


class TestGraphsPanelFidelity:
    @pytest.fixture
    def context(self):
        config = AppConfig()
        ctx = AppContext(config=config)
        ctx.history_initialized = False
        return ctx

    @pytest.fixture
    def manager(self, context):
        return PanelManager(context)

    @pytest.fixture
    def panel(self, manager, context):
        # We need to handle graphs.init_history_data call in did_mount
        # It allocates arrays on context.
        # We can let it run or patch it if it's slow/complex.
        # Since it's pure python array init, it should be fast.
        panel = GraphsPanel(manager, context)
        panel.did_mount()
        return panel

    def test_initial_state(self, panel):
        """Verify defaults."""
        assert panel._state.range == 10
        assert panel._state.visible_histories == 0x3F  # All 6 bits set

        view = panel._view
        assert view.range_10_button.toggled
        assert not view.range_120_button.toggled

        # Verify checkboxes
        assert len(view.history_checkboxes) == 6
        for cb in view.history_checkboxes:
            assert cb._checked

    def test_range_toggle(self, panel):
        """Verify toggling between 10 and 120 year views."""
        view = panel._view

        # Switch to 120
        # Button click calls set_toggled -> calls handler -> updates panel state
        view.range_120_button.click()

        assert panel._state.range == 120
        assert view.range_120_button.toggled
        assert not view.range_10_button.toggled
        assert view.graph_widget._range == 120

        # Switch back to 10
        view.range_10_button.click()
        assert panel._state.range == 10
        assert view.range_10_button.toggled
        assert view.graph_widget._range == 10

    def test_history_toggle(self, panel):
        """Verify toggling history lines."""
        view = panel._view

        # Toggle off first one (Res)
        cb0 = view.history_checkboxes[0]
        # Simulate clean click event flow or just call click()
        cb0.click()

        assert not cb0._checked
        # Mask should have bit 0 cleared: 111111 (0x3F) -> 111110 (0x3E)
        assert view.graph_widget._visible_mask == 0x3E

        # Toggle back on
        cb0.click()
        assert cb0._checked
        assert view.graph_widget._visible_mask == 0x3F

    def test_refresh_loads_data(self, panel, context):
        """Verify refresh calls graphs update."""
        with patch("micropolis.graphs.update_all_graphs") as mock_update:
            panel.refresh_from_context()
            mock_update.assert_called_with(context)
