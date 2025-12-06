import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

# Mock pygame before importing panel
mock_pygame = MagicMock()
mock_pygame.MOUSEBUTTONDOWN = 5
mock_pygame.MOUSEBUTTONUP = 6
mock_pygame.MOUSEMOTION = 4
# sys.modules["pygame"] = mock_pygame # This might affect other tests if not careful.
# Better to patch where it's used.

from micropolis.context import AppContext
from micropolis.app_config import AppConfig
from micropolis.ui.panel_manager import PanelManager
from micropolis.ui.panels.tool_palette_panel import ToolPalettePanel
from micropolis.constants import residentialState, roadState, nuclearState, CostOf


class TestToolPalettePanelFidelity:
    @pytest.fixture
    def context(self):
        config = AppConfig()
        ctx = AppContext(config=config)
        ctx.total_funds = 20000
        ctx.sim = Mock()
        ctx.sim.current_tool_state = residentialState
        return ctx

    @pytest.fixture
    def manager(self, context):
        return PanelManager(context)

    @pytest.fixture
    def panel(self, manager, context):
        with (
            patch("micropolis.ui.panels.tool_palette_panel._HAVE_PYGAME", True),
            patch("micropolis.ui.panels.tool_palette_panel.pygame", mock_pygame),
        ):
            panel = ToolPalettePanel(manager, context)
            panel.did_mount()
            # Force grid initialization
            panel._init_palette_grid()
            return panel

    def test_initial_selection(self, panel):
        """Verify initial tool is consistent with context."""
        assert panel.get_current_tool() == residentialState
        assert panel._palette_grid.selected_id == f"tool_{residentialState}"

    def test_tool_click(self, panel, context):
        """Verify clicking a tool updates state."""
        # Find road tool item
        road_item = next(
            i for i in panel._palette_items if i.item_id == f"tool_{roadState}"
        )

        # Simulate selection call from grid
        panel._on_tool_selected(road_item)

        assert panel.get_current_tool() == roadState
        assert context.current_tool_state == roadState
        assert panel._palette_grid.selected_id == f"tool_{roadState}"

    def test_funds_enable_disable(self, panel, context):
        """Verify tools are disabled if insufficient funds."""
        # Nuclear plant cost is 5000 usually
        nuke_cost = CostOf[nuclearState]
        assert nuke_cost > 0

        # Set funds to 0
        context.total_funds = 0

        # Trigger update
        panel._on_funds_updated(None)

        # Check nuclear tool
        nuke_item = next(
            i for i in panel._palette_items if i.item_id == f"tool_{nuclearState}"
        )
        assert not nuke_item.enabled

        # Check free tool (if any) or cheap tool?
        # Bulldozer is usually $1 but some might be free?
        # Let's check logic: item.enabled = cost == 0 or total_funds >= cost

        # Give enough money
        context.total_funds = nuke_cost + 1
        panel._on_funds_updated(None)
        assert nuke_item.enabled

    def test_context_sync(self, panel):
        """Verify external tool change updates panel."""
        # publish event
        panel._event_bus.publish("tool.changed", {"tool_state": roadState})

        # Handler is subscribed
        # But publish is usually deferred?
        # PanelManager usually pumps events.
        # Here we can call handler directly or pump bus.
        # Let's call callback directly for unit integrity
        panel._on_tool_changed({"tool_state": roadState})

        assert panel.get_current_tool() == roadState
        assert panel._palette_grid.selected_id == f"tool_{roadState}"
