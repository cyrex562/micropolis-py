"""
test_graphs.py - Tests for graphs.py module

Tests the graph display system ported from w_graph.c.
"""

import pytest
import pygame
from unittest.mock import MagicMock, patch

from micropolis import constants as const
from src.micropolis import graphs


class TestGraphCreation:
    """Test graph creation and management"""

    def test_create_graph(self):
        """Test creating a new graph instance"""
        initial_count = len(graphs.get_graphs())
        graph = graphs.create_graph()

        assert isinstance(graph, graphs.SimGraph)
        assert graph.range == 10
        assert graph.mask == const.ALL_HISTORIES
        assert not graph.visible
        assert len(graphs.get_graphs()) == initial_count + 1

    def test_remove_graph(self):
        """Test removing a graph instance"""
        graph = graphs.create_graph()
        initial_count = len(graphs.get_graphs())

        graphs.remove_graph(graph)
        assert len(graphs.get_graphs()) == initial_count - 1

    def test_get_graphs(self):
        """Test getting all graph instances"""
        graphs_list = graphs.get_graphs()
        assert isinstance(graphs_list, list)


class TestGraphConfiguration:
    """Test graph configuration methods"""

    def setup_method(self):
        """Setup for each test"""
        self.graph = graphs.create_graph()

    def teardown_method(self):
        """Cleanup after each test"""
        graphs.remove_graph(self.graph)

    def test_set_position(self):
        """Test setting graph position"""
        self.graph.set_position(100, 200)
        assert self.graph.w_x == 100
        assert self.graph.w_y == 200

    def test_set_size(self):
        """Test setting graph size"""
        self.graph.set_size(400, 300)
        assert self.graph.w_width == 400
        assert self.graph.w_height == 300
        assert self.graph.surface is not None
        assert self.graph.needs_redraw

    def test_set_range(self):
        """Test setting graph range"""
        self.graph.set_range(120)
        assert self.graph.range == 120
        assert self.graph.needs_redraw

        # Test invalid range (should not change)
        self.graph.set_range(50)
        assert self.graph.range == 120

    def test_set_mask(self):
        """Test setting graph mask"""
        self.graph.set_mask(const.RES_HIST | const.COM_HIST)
        assert self.graph.mask == (const.RES_HIST | const.COM_HIST)
        assert self.graph.needs_redraw

    def test_set_visible(self):
        """Test setting graph visibility"""
        self.graph.set_visible(True)
        assert self.graph.visible
        assert self.graph.needs_redraw


class TestHistoryData:
    """Test history data management"""

    def setup_method(self):
        """Setup for each test"""
        graphs.init_history_data(context)

    def test_init_history_data(self):
        """Test history data initialization"""
        assert graphs.history_initialized
        assert len(graphs.history_10) == const.HISTORIES
        assert len(graphs.history_120) == const.HISTORIES

        for hist in graphs.history_10:
            assert len(hist) == 120
            assert all(x == 0 for x in hist)

        for hist in graphs.history_120:
            assert len(hist) == 120
            assert all(x == 0 for x in hist)

    def test_init_graph_maxima(self):
        """Test graph maxima initialization"""
        # Setup some test data
        context.res_his = [100, 200, 150, 300] + [0] * 236
        context.com_his = [50, 100, 75, 250] + [0] * 236
        context.ind_his = [25, 50, 40, 150] + [0] * 236

        graphs.init_graph_maxima(context)

        assert context.res_his_max == 300
        assert context.com_his__max == 250
        assert context.ind_his_max == 150
        assert graphs.graph_10_max == 300

    def test_draw_month(self):
        """Test draw_month scaling function"""
        source = [0, 50, 100, 150, 200] + [0] * 115  # 120 elements
        dest = [0] * 120

        graphs.draw_month(source, dest, 0.5)  # Scale by 0.5

        # Values should be scaled and reversed
        assert dest[119] == 0  # source[0] * 0.5
        assert dest[118] == 25  # source[1] * 0.5
        assert dest[117] == 50  # source[2] * 0.5
        assert dest[116] == 75  # source[3] * 0.5
        assert dest[115] == 100  # source[4] * 0.5

    def test_do_all_graphs(self):
        """Test do_all_graphs data processing"""
        # Setup test history data
        context.res_his = [100, 200, 300] + [0] * 237
        context.com_his = [50, 100, 150] + [0] * 237
        context.ind_his = [25, 50, 75] + [0] * 237
        context.money_his = [1000, 2000, 3000] + [0] * 237
        context.crime_his = [10, 20, 30] + [0] * 237
        context.pollution_his = [5, 10, 15] + [0] * 237

        graphs.init_graph_maxima(context)
        graphs.do_all_graphs(context)

        # Check that data was processed
        assert len(graphs.history_10[const.RES_HIST]) == 120
        assert len(graphs.history_10[const.COM_HIST]) == 120
        assert len(graphs.history_10[const.MONEY_HIST]) == 120


class TestGraphRendering:
    """Test graph rendering functionality"""

    def setup_method(self):
        """Setup for each test"""
        pygame.init()
        self.graph = graphs.create_graph()
        self.graph.set_size(400, 300)

    def teardown_method(self):
        """Cleanup after each test"""
        graphs.remove_graph(self.graph)
        pygame.quit()

    def test_update_graph_not_visible(self):
        """Test update_graph with invisible graph"""
        self.graph.visible = False
        graphs.update_graph(context, self.graph)
        # Should not crash, surface should remain unchanged

    def test_update_graph_no_surface(self):
        """Test update_graph with no surface"""
        self.graph.visible = True
        self.graph.surface = None
        graphs.update_graph(context, self.graph)
        # Should not crash

    def test_update_graph_visible(self):
        """Test update_graph with visible graph"""
        self.graph.visible = True
        self.graph.set_size(400, 300)

        # Setup some test data
        graphs.history_10[const.RES_HIST] = [i * 2 for i in range(120)]
        graphs.history_10[const.COM_HIST] = [i for i in range(120)]

        graphs.update_graph(context, self.graph)

        # Graph should be marked as not needing redraw
        assert not self.graph.needs_redraw

    def test_update_all_graphs(self):
        """Test update_all_graphs function"""
        # Create a test graph
        graph = graphs.create_graph()
        graph.set_size(400, 300)

        # Setup census changed flag
        context.census_changed = 1

        graphs.update_all_graphs(context)

        # CensusChanged should be reset
        assert context.census_changed == 0

        # Graph should be marked for redraw
        assert graph.needs_redraw

        graphs.remove_graph(graph)


class TestGraphPanel:
    """Tests for the pygame graph overlay panel."""

    def setup_method(self):
        graphs.set_graph_panel_visible(context, False)
        graphs.graph_panel_surface = None
        graphs.graph_panel_dirty = False

    def test_panel_hidden_without_pygame(self):
        """Panel rendering returns None when pygame is unavailable."""
        with patch.object(graphs, "PYGAME_AVAILABLE", False):
            graphs.set_graph_panel_visible(context, True)
            assert graphs.is_graph_panel_visible()
            assert graphs.render_graph_panel(context) is None

    def test_panel_render_with_pygame(self):
        """Panel rendering requests a pygame surface."""
        with (
            patch.object(graphs, "PYGAME_AVAILABLE", True),
            patch.object(graphs, "pygame") as mock_pygame,
        ):
            mock_pygame.SRCALPHA = 0
            mock_surface = MagicMock()
            mock_pygame.Surface.return_value = mock_surface
            mock_surface.get_size.return_value = graphs.graph_panel_size
            mock_surface.fill = MagicMock()
            mock_pygame.draw.rect = MagicMock()

            graphs.set_graph_panel_visible(context, True)
            surface = graphs.render_graph_panel(context)

            assert surface is mock_surface
            mock_pygame.Surface.assert_called()

    def test_panel_resize_marks_dirty(self):
        """Changing panel size recreates the surface."""
        with (
            patch.object(graphs, "PYGAME_AVAILABLE", True),
            patch.object(graphs, "pygame") as mock_pygame,
        ):
            mock_pygame.SRCALPHA = 0
            initial_surface = MagicMock()
            initial_surface.get_size.return_value = graphs.graph_panel_size
            initial_surface.fill = MagicMock()
            resized_surface = MagicMock()
            resized_surface.get_size.return_value = (512, 256)
            resized_surface.fill = MagicMock()
            mock_pygame.Surface.side_effect = [initial_surface, resized_surface]
            mock_pygame.draw.rect = MagicMock()

            graphs.set_graph_panel_visible(context, True)
            graphs.set_graph_panel_size(context, 512, 256)
            surface = graphs.render_graph_panel(context)

            assert surface is resized_surface
            mock_pygame.Surface.assert_called_with((512, 256), mock_pygame.SRCALPHA)


class TestDataAccess:
    """Test data access functions"""

    def test_get_history_data(self):
        """Test get_history_data function"""
        # Reset initialization to ensure clean state
        graphs.history_initialized = False
        graphs.init_history_data(context)

        # Test 10-year data
        data = graphs.get_history_data(context, 10, const.RES_HIST)
        assert len(data) == 120
        assert all(x == 0 for x in data)

        # Test 120-year data
        data = graphs.get_history_data(context, 120, const.COM_HIST)
        assert len(data) == 120
        assert all(x == 0 for x in data)

        # Test invalid range
        data = graphs.get_history_data(context, 50, const.IND_HIST)
        assert data == []

    def test_get_history_names(self):
        """Test get_history_names function"""
        names = graphs.get_history_names()
        assert len(names) == 6
        assert "Residential" in names
        assert "Commercial" in names
        assert "Industrial" in names
        assert "Cash Flow" in names
        assert "Crime" in names
        assert "Pollution" in names

    def test_get_history_colors(self):
        """Test get_history_colors function"""
        colors = graphs.get_history_colors()
        assert len(colors) == 6
        assert all(isinstance(color, tuple) and len(color) == 3 for color in colors)


class TestInitialization:
    """Test initialization functions"""

    def test_initialize_graphs(self):
        """Test initialize_graphs function"""
        graph = graphs.create_graph()

        # Set some non-default values
        graph.range = 120
        graph.mask = const.RES_HIST

        graphs.initialize_graphs(context)

        # Should reset to defaults
        assert graph.range == 10
        assert graph.mask == const.ALL_HISTORIES

        graphs.remove_graph(graph)

        # Check history initialization
        assert graphs.history_initialized
        assert len(graphs.history_10) == const.HISTORIES
        assert len(graphs.history_120) == const.HISTORIES


class TestIntegration:
    """Integration tests"""

    def setup_method(self):
        """Setup for integration tests"""
        pygame.init()
        graphs.initialize_graphs(context)

    def teardown_method(self):
        """Cleanup after integration tests"""
        pygame.quit()

    def test_full_graph_workflow(self):
        """Test complete graph workflow"""
        # Create and configure graph
        graph = graphs.create_graph()
        graph.set_size(400, 300)
        graph.set_visible(True)
        graph.set_range(10)
        graph.set_mask(const.RES_HIST | const.COM_HIST)

        # Setup history data
        context.res_his = [i * 10 for i in range(240)]
        context.com_his = [i * 5 for i in range(240)]
        context.ind_his = [i * 2 for i in range(240)]
        context.money_his = [1000 + i * 100 for i in range(240)]
        context.crime_his = [i for i in range(240)]
        context.pollution_his = [i // 2 for i in range(240)]

        # Process data
        graphs.init_graph_maxima(context)
        graphs.do_all_graphs(context)

        # Update graphs
        context.census_changed = 1
        graphs.update_all_graphs(context)

        # Render graph
        graphs.update_graph(context, graph)

        # Verify graph was rendered
        assert not graph.needs_redraw
        assert graph.surface is not None

        graphs.remove_graph(graph)
