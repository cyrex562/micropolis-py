"""
test_platform.py - Comprehensive tests for platform.py

Tests pygame platform functionality including display management,
coordinate conversion, view management, and drawing operations.
"""

import pytest
import pygame
from unittest.mock import Mock, patch

from .platform import (
    initialize_platform, shutdown_platform, set_display_mode,
    view_to_tile_coords, view_to_pixel_coords, update_flush,
    create_sim_view, resize_sim_view, destroy_sim_view,
    pan_view_by, pan_view_to, blit_view_surface,
    get_display_pixels, is_platform_initialized, get_display_info,
    new_ink, start_ink, add_ink, draw_ink, erase_overlay,
    catch_error, do_stop_micropolis, do_timeout_listen, make_new_sim,
    PygameDisplay, Ink, view_surfaces, view_overlay_surfaces
)
from .types import SimView, Sim
from .view_types import Map_Class, Editor_Class
from .types import COLOR_WHITE, COLOR_BLACK


class TestPlatformInitialization:
    """Test platform initialization and shutdown."""

    def test_initialize_platform_success(self):
        """Test successful platform initialization."""
        with patch('pygame.init') as mock_init:
            result = initialize_platform()
            assert result is True
            mock_init.assert_called_once()

    def test_initialize_platform_failure(self):
        """Test platform initialization failure."""
        with patch('pygame.init', side_effect=Exception("Init failed")):
            result = initialize_platform()
            assert result is False

    def test_shutdown_platform(self):
        """Test platform shutdown."""
        with patch('pygame.quit') as mock_quit:
            shutdown_platform()
            mock_quit.assert_called_once()

    def test_is_platform_initialized(self):
        """Test platform initialization status check."""
        # Initially not initialized
        assert is_platform_initialized() is False

        # After initialization
        with patch('pygame.init'):
            initialize_platform()
            assert is_platform_initialized() is True

        # After shutdown
        shutdown_platform()
        assert is_platform_initialized() is False


class TestDisplayManagement:
    """Test display mode and pixel management."""

    def test_set_display_mode_success(self):
        """Test successful display mode setting."""
        initialize_platform()
        with patch('pygame.display.set_mode') as mock_set_mode:
            mock_surface = Mock()
            mock_set_mode.return_value = mock_surface

            result = set_display_mode(800, 600)
            assert result is True
            mock_set_mode.assert_called_once_with((800, 600), 0)

    def test_set_display_mode_failure(self):
        """Test display mode setting failure."""
        initialize_platform()
        with patch('pygame.display.set_mode', side_effect=Exception("Set mode failed")):
            result = set_display_mode(800, 600)
            assert result is False

    def test_get_display_pixels(self):
        """Test getting display pixel colors."""
        initialize_platform()
        pixels = get_display_pixels()
        assert isinstance(pixels, list)
        assert len(pixels) == 16  # Should have 16 colors

    def test_get_display_info(self):
        """Test getting display information."""
        info = get_display_info()
        assert isinstance(info, dict)
        assert 'width' in info
        assert 'height' in info
        assert 'depth' in info
        assert 'color' in info
        assert 'initialized' in info


class TestCoordinateConversion:
    """Test coordinate conversion functions."""

    def test_view_to_tile_coords(self):
        """Test view to tile coordinate conversion."""
        view = SimView()
        view.pan_x = 100
        view.pan_y = 100
        view.w_width = 200
        view.w_height = 200
        view.tile_x = 0
        view.tile_y = 0
        view.tile_width = 10
        view.tile_height = 10

        # Test center of view
        tile_x, tile_y = view_to_tile_coords(view, 100, 100)
        assert isinstance(tile_x, int)
        assert isinstance(tile_y, int)

    def test_view_to_pixel_coords(self):
        """Test view to pixel coordinate conversion."""
        view = SimView()
        view.pan_x = 100
        view.pan_y = 100
        view.w_width = 200
        view.w_height = 200
        view.tile_x = 0
        view.tile_y = 0
        view.tile_width = 10
        view.tile_height = 10

        # Test center of view
        pixel_x, pixel_y = view_to_pixel_coords(view, 100, 100)
        assert isinstance(pixel_x, int)
        assert isinstance(pixel_y, int)

    def test_view_to_tile_coords_with_constraints(self):
        """Test coordinate conversion with tool constraints."""
        view = SimView()
        view.pan_x = 100
        view.pan_y = 100
        view.w_width = 200
        view.w_height = 200
        view.tile_x = 0
        view.tile_y = 0
        view.tile_width = 10
        view.tile_height = 10
        view.tool_x_const = 5
        view.tool_y_const = 5

        tile_x, tile_y = view_to_tile_coords(view, 50, 50)
        assert tile_x == 5
        assert tile_y == 5


class TestViewManagement:
    """Test view creation, resizing, and destruction."""

    def setup_method(self):
        """Set up test environment."""
        initialize_platform()
        # Clear any existing surfaces
        view_surfaces.clear()
        view_overlay_surfaces.clear()

    def teardown_method(self):
        """Clean up test environment."""
        view_surfaces.clear()
        view_overlay_surfaces.clear()
        shutdown_platform()

    def test_create_sim_view_editor(self):
        """Test creating an editor view."""
        view = create_sim_view("Test Editor", Editor_Class, 256, 256)

        assert view.title == "Test Editor"
        assert view.class_id == Editor_Class
        assert view.w_width == 256
        assert view.w_height == 256
        assert id(view) in view_surfaces
        assert id(view) in view_overlay_surfaces

    def test_create_sim_view_map(self):
        """Test creating a map view."""
        view = create_sim_view("Test Map", Map_Class, 360, 300)

        assert view.title == "Test Map"
        assert view.class_id == Map_Class
        assert view.w_width == 360
        assert view.w_height == 300
        assert id(view) in view_surfaces

    def test_resize_sim_view(self):
        """Test resizing a view."""
        view = create_sim_view("Test View", Editor_Class, 256, 256)
        original_surface = view_surfaces[id(view)]

        resize_sim_view(view, 512, 512)

        assert view.w_width == 512
        assert view.w_height == 512
        # Surface should be recreated
        assert view_surfaces[id(view)] is not original_surface

    def test_destroy_sim_view(self):
        """Test destroying a view."""
        view = create_sim_view("Test View", Editor_Class, 256, 256)
        view_id = id(view)

        assert view_id in view_surfaces
        assert view_id in view_overlay_surfaces

        destroy_sim_view(view)

        assert view_id not in view_surfaces
        assert view_id not in view_overlay_surfaces


class TestViewPanning:
    """Test view panning functionality."""

    def setup_method(self):
        """Set up test environment."""
        initialize_platform()

    def teardown_method(self):
        """Clean up test environment."""
        shutdown_platform()

    def test_pan_view_by(self):
        """Test panning view by delta."""
        view = create_sim_view("Test View", Editor_Class, 256, 256)
        original_pan_x = view.pan_x
        original_pan_y = view.pan_y

        pan_view_by(view, 10, 20)

        assert view.pan_x == original_pan_x + 10
        assert view.pan_y == original_pan_y + 20

    def test_pan_view_to(self):
        """Test panning view to specific position."""
        view = create_sim_view("Test View", Editor_Class, 256, 256)

        pan_view_to(view, 100, 150)

        assert view.pan_x == 100
        assert view.pan_y == 150

    def test_pan_view_to_clamped(self):
        """Test panning with boundary clamping."""
        view = create_sim_view("Test View", Editor_Class, 256, 256)

        # Try to pan outside bounds
        pan_view_to(view, -100, -100)

        assert view.pan_x == 0
        assert view.pan_y == 0

    def test_pan_view_map_ignored(self):
        """Test that panning is ignored for map views."""
        view = create_sim_view("Test Map", Map_Class, 360, 300)
        original_pan_x = view.pan_x
        original_pan_y = view.pan_y

        pan_view_to(view, 100, 100)

        # Map view panning should be ignored
        assert view.pan_x == original_pan_x
        assert view.pan_y == original_pan_y


class TestSurfaceOperations:
    """Test surface-related operations."""

    def setup_method(self):
        """Set up test environment."""
        initialize_platform()

    def teardown_method(self):
        """Clean up test environment."""
        shutdown_platform()

    def test_blit_view_surface(self):
        """Test blitting view surface to destination."""
        view = create_sim_view("Test View", Editor_Class, 256, 256)
        dest_surface = pygame.Surface((512, 512))

        # Should not raise an exception
        blit_view_surface(view, dest_surface, 0, 0)

    def test_blit_view_surface_no_surface(self):
        """Test blitting when view has no surface."""
        view = SimView()  # Create view without surface
        dest_surface = pygame.Surface((512, 512))

        # Should not raise an exception
        blit_view_surface(view, dest_surface, 0, 0)


class TestInkDrawing:
    """Test ink drawing functionality."""

    def setup_method(self):
        """Set up test environment."""
        initialize_platform()

    def teardown_method(self):
        """Clean up test environment."""
        shutdown_platform()

    def test_new_ink(self):
        """Test creating new ink."""
        ink = new_ink()
        assert isinstance(ink, Ink)
        assert ink.color == COLOR_WHITE
        assert ink.points == []

    def test_start_ink(self):
        """Test starting ink drawing."""
        ink = new_ink()
        start_ink(ink, 10, 20)

        assert len(ink.points) == 1
        assert ink.points[0] == (10, 20)

    def test_add_ink(self):
        """Test adding points to ink."""
        ink = new_ink()
        start_ink(ink, 10, 20)
        add_ink(ink, 15, 25)

        assert len(ink.points) == 2
        assert ink.points[1] == (15, 25)

    def test_add_ink_same_point_ignored(self):
        """Test that adding the same point is ignored."""
        ink = new_ink()
        start_ink(ink, 10, 20)
        add_ink(ink, 10, 20)  # Same point

        assert len(ink.points) == 1

    def test_draw_ink(self):
        """Test drawing ink on surface."""
        ink = new_ink()
        start_ink(ink, 10, 20)
        add_ink(ink, 15, 25)
        add_ink(ink, 20, 30)

        surface = pygame.Surface((100, 100))

        # Should not raise an exception
        draw_ink(surface, ink)

    def test_draw_ink_insufficient_points(self):
        """Test drawing ink with insufficient points."""
        ink = new_ink()
        start_ink(ink, 10, 20)  # Only one point

        surface = pygame.Surface((100, 100))

        # Should not raise an exception
        draw_ink(surface, ink)

    def test_erase_overlay(self):
        """Test erasing overlay."""
        view = create_sim_view("Test View", Editor_Class, 256, 256)

        # Should not raise an exception
        erase_overlay(view)


class TestUtilityFunctions:
    """Test utility and helper functions."""

    def test_update_flush(self):
        """Test display flushing."""
        # Should not raise an exception
        update_flush()

    def test_catch_error(self):
        """Test error catching."""
        # Should return False (no pygame errors to catch)
        result = catch_error()
        assert isinstance(result, bool)

    def test_do_timeout_listen(self):
        """Test timeout listening."""
        # Should not raise an exception
        do_timeout_listen()

    def test_make_new_sim(self):
        """Test creating new sim instance."""
        sim = make_new_sim()

        assert isinstance(sim, Sim)
        assert sim.editors == 0
        assert sim.maps == 0
        assert sim.graphs == 0
        assert sim.sprites == 0

    def test_do_stop_micropolis(self):
        """Test stopping micropolis."""
        sim = make_new_sim()

        # Create some views (variables not used but needed for cleanup)
        create_sim_view("View1", Editor_Class, 256, 256)
        create_sim_view("View2", Map_Class, 360, 300)

        # Stop micropolis
        do_stop_micropolis(sim)

        # Check that surfaces were cleared
        assert len(view_surfaces) == 0
        assert len(view_overlay_surfaces) == 0

        # Check sim counters were reset
        assert sim.editors == 0
        assert sim.maps == 0
        assert sim.graphs == 0
        assert sim.sprites == 0


class TestPygameDisplay:
    """Test PygameDisplay dataclass."""

    def test_pygame_display_creation(self):
        """Test creating PygameDisplay instance."""
        display = PygameDisplay()
        assert display.screen is None
        assert display.width == 0
        assert display.height == 0
        assert display.depth == 32
        assert display.color is True
        assert display.pixels == []
        assert display.initialized is False

    def test_pygame_display_post_init(self):
        """Test PygameDisplay post-initialization."""
        display = PygameDisplay(pixels=None)
        assert display.pixels == []


class TestInkDataclass:
    """Test Ink dataclass."""

    def test_ink_creation(self):
        """Test creating Ink instance."""
        ink = Ink()
        assert ink.points == []
        assert ink.color == COLOR_WHITE
        assert ink.next_ink is None

    def test_ink_with_points(self):
        """Test creating Ink with points."""
        points = [(10, 20), (15, 25)]
        ink = Ink(points=points, color=COLOR_BLACK)
        assert ink.points == points
        assert ink.color == COLOR_BLACK


if __name__ == "__main__":
    pytest.main([__file__])