"""
test_mouse_interactions.py - Unit tests for mouse interaction system

Tests cursor manager, hit-testing, and mouse controllers.
"""

import unittest
from unittest.mock import MagicMock

import pygame

from micropolis.context import AppContext
from micropolis.ui.cursor_manager import CursorManager
from micropolis.ui.hit_testing import HitTester, get_hit_tester
from micropolis.ui.mouse_controller import (
    AutoPanController,
    MouseButton,
    MouseInputController,
    MouseMode,
)


class TestCursorManager(unittest.TestCase):
    """Test cursor manager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        pygame.init()
        self.context = MagicMock(spec=AppContext)
        self.cursor_manager = CursorManager(self.context)

    def tearDown(self):
        """Clean up."""
        pygame.quit()

    def test_initialization(self):
        """Test cursor manager initializes correctly."""
        # Note: current_cursor may be None in headless mode
        self.assertIsNone(self.cursor_manager.current_tool)
        self.assertTrue(self.cursor_manager.is_valid_placement)
        self.assertFalse(self.cursor_manager.is_in_autopan_zone)

    def test_update_cursor_for_tool(self):
        """Test cursor updates based on tool state."""
        # Test building tool
        self.cursor_manager.update_cursor_for_tool(0, True)  # Residential
        self.assertEqual(self.cursor_manager.current_tool, 0)
        self.assertTrue(self.cursor_manager.is_valid_placement)

        # Test chalk tool
        self.cursor_manager.update_cursor_for_tool(10, True)  # Chalk
        self.assertEqual(self.cursor_manager.current_tool, 10)

    def test_edge_autopan_zone_detection(self):
        """Test autopan edge zone detection."""
        viewport_rect = pygame.Rect(0, 0, 800, 600)

        # Test inside edge threshold (left edge)
        is_in_zone, dx, dy = self.cursor_manager.is_edge_autopan_zone(
            (20, 300), viewport_rect, edge_threshold=32
        )
        self.assertTrue(is_in_zone)
        self.assertEqual(dx, -1)
        self.assertEqual(dy, 0)

        # Test outside edge threshold (center)
        is_in_zone, dx, dy = self.cursor_manager.is_edge_autopan_zone(
            (400, 300), viewport_rect, edge_threshold=32
        )
        self.assertFalse(is_in_zone)
        self.assertEqual(dx, 0)
        self.assertEqual(dy, 0)


class TestHitTester(unittest.TestCase):
    """Test hit-testing utilities."""

    def setUp(self):
        """Set up test fixtures."""
        self.hit_tester = HitTester()

    def test_screen_to_tile(self):
        """Test screen to tile coordinate conversion."""
        # No offset, 16px tiles
        tile_x, tile_y = self.hit_tester.screen_to_tile((32, 48), (0, 0))
        self.assertEqual(tile_x, 2)
        self.assertEqual(tile_y, 3)

        # With offset
        tile_x, tile_y = self.hit_tester.screen_to_tile((32, 48), (16, 16))
        self.assertEqual(tile_x, 3)
        self.assertEqual(tile_y, 4)

    def test_tile_to_screen(self):
        """Test tile to screen coordinate conversion."""
        # No offset
        screen_x, screen_y = self.hit_tester.tile_to_screen((2, 3), (0, 0))
        self.assertEqual(screen_x, 32)
        self.assertEqual(screen_y, 48)

        # With offset
        screen_x, screen_y = self.hit_tester.tile_to_screen((2, 3), (16, 16))
        self.assertEqual(screen_x, 16)
        self.assertEqual(screen_y, 32)

    def test_is_valid_tile(self):
        """Test tile bounds checking."""
        self.assertTrue(self.hit_tester.is_valid_tile((0, 0)))
        self.assertTrue(self.hit_tester.is_valid_tile((119, 99)))
        self.assertFalse(self.hit_tester.is_valid_tile((-1, 0)))
        self.assertFalse(self.hit_tester.is_valid_tile((120, 0)))
        self.assertFalse(self.hit_tester.is_valid_tile((0, 100)))

    def test_snap_to_orthogonal(self):
        """Test orthogonal line snapping."""
        # Horizontal line (dx > dy)
        snapped = self.hit_tester.snap_to_orthogonal((0, 0), (10, 2))
        self.assertEqual(snapped, (10, 0))

        # Vertical line (dy > dx)
        snapped = self.hit_tester.snap_to_orthogonal((0, 0), (2, 10))
        self.assertEqual(snapped, (0, 10))

    def test_get_line_tiles(self):
        """Test line tile generation."""
        # Horizontal line
        tiles = self.hit_tester.get_line_tiles((0, 0), (3, 0), False)
        self.assertEqual(len(tiles), 4)
        self.assertIn((0, 0), tiles)
        self.assertIn((3, 0), tiles)

        # Vertical line
        tiles = self.hit_tester.get_line_tiles((0, 0), (0, 3), False)
        self.assertEqual(len(tiles), 4)
        self.assertIn((0, 0), tiles)
        self.assertIn((0, 3), tiles)

    def test_get_rect_tiles(self):
        """Test rectangle tile generation."""
        tiles = self.hit_tester.get_rect_tiles((0, 0), (2, 2))
        self.assertEqual(len(tiles), 9)  # 3x3 rectangle
        self.assertIn((0, 0), tiles)
        self.assertIn((2, 2), tiles)
        self.assertIn((1, 1), tiles)

    def test_get_hit_tester_singleton(self):
        """Test global singleton accessor."""
        tester1 = get_hit_tester()
        tester2 = get_hit_tester()
        self.assertIs(tester1, tester2)


class TestMouseInputController(unittest.TestCase):
    """Test mouse input controller."""

    def setUp(self):
        """Set up test fixtures."""
        pygame.init()
        self.context = MagicMock(spec=AppContext)
        self.controller = MouseInputController(self.context)

    def tearDown(self):
        """Clean up."""
        pygame.quit()

    def test_initialization(self):
        """Test controller initializes correctly."""
        self.assertEqual(self.controller.mode, MouseMode.NORMAL)
        self.assertEqual(len(self.controller.buttons_down), 0)
        self.assertIsNone(self.controller.drag_start_pos)

    def test_button_down_left(self):
        """Test left button down event."""
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (100, 200)}
        )

        handled = self.controller.handle_event(event)
        self.assertTrue(handled)
        self.assertIn(MouseButton.LEFT, self.controller.buttons_down)
        self.assertEqual(self.controller.mode, MouseMode.PAINTING)
        self.assertEqual(self.controller.drag_start_pos, (100, 200))

    def test_button_down_right(self):
        """Test right button down event."""
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 3, "pos": (100, 200)}
        )

        handled = self.controller.handle_event(event)
        self.assertTrue(handled)
        self.assertIn(MouseButton.RIGHT, self.controller.buttons_down)
        self.assertEqual(self.controller.mode, MouseMode.PANNING)

    def test_button_up(self):
        """Test button up event."""
        # Press button first
        down_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (100, 200)}
        )
        self.controller.handle_event(down_event)

        # Release button
        up_event = pygame.event.Event(
            pygame.MOUSEBUTTONUP, {"button": 1, "pos": (150, 250)}
        )
        handled = self.controller.handle_event(up_event)

        self.assertTrue(handled)
        self.assertNotIn(MouseButton.LEFT, self.controller.buttons_down)
        self.assertEqual(self.controller.mode, MouseMode.NORMAL)
        self.assertIsNone(self.controller.drag_start_pos)

    def test_is_dragging(self):
        """Test drag state detection."""
        self.assertFalse(self.controller.is_dragging())

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (100, 200)}
        )
        self.controller.handle_event(event)

        self.assertTrue(self.controller.is_dragging())

    def test_get_drag_delta(self):
        """Test drag delta calculation."""
        # Start drag
        down_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (100, 200)}
        )
        self.controller.handle_event(down_event)

        # Move mouse
        self.controller.current_pos = (150, 250)

        dx, dy = self.controller.get_drag_delta()
        self.assertEqual(dx, 50)
        self.assertEqual(dy, 50)


class TestAutoPanController(unittest.TestCase):
    """Test autopan controller."""

    def setUp(self):
        """Set up test fixtures."""
        pygame.init()
        self.autopan = AutoPanController()

    def tearDown(self):
        """Clean up."""
        pygame.quit()

    def test_initialization(self):
        """Test autopan initializes correctly."""
        self.assertTrue(self.autopan.enabled)
        self.assertEqual(self.autopan.edge_threshold, 32)
        self.assertFalse(self.autopan.is_active)

    def test_edge_detection_left(self):
        """Test left edge autopan."""
        viewport = pygame.Rect(0, 0, 800, 600)
        mouse_pos = (20, 300)  # Near left edge

        dx, dy = self.autopan.update(mouse_pos, viewport, 0.016)

        self.assertTrue(self.autopan.is_active)
        self.assertLess(dx, 0)  # Panning left
        self.assertEqual(dy, 0)

    def test_edge_detection_center(self):
        """Test no autopan in center."""
        viewport = pygame.Rect(0, 0, 800, 600)
        mouse_pos = (400, 300)  # Center

        dx, dy = self.autopan.update(mouse_pos, viewport, 0.016)

        self.assertFalse(self.autopan.is_active)
        self.assertEqual(dx, 0)
        self.assertEqual(dy, 0)

    def test_disabled(self):
        """Test autopan when disabled."""
        self.autopan.enabled = False
        viewport = pygame.Rect(0, 0, 800, 600)
        mouse_pos = (20, 300)  # Near left edge

        dx, dy = self.autopan.update(mouse_pos, viewport, 0.016)

        self.assertFalse(self.autopan.is_active)
        self.assertEqual(dx, 0)
        self.assertEqual(dy, 0)


if __name__ == "__main__":
    unittest.main()
