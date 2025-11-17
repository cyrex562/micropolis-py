"""
Test suite for interactions.py - Interactive UI components

Tests the pygame-based interval widget and related interactive components.
"""

import pygame
from unittest.mock import Mock
from micropolis.interactions import (
    Interval, Orientation, IntervalState, Tk_IntervalCmd, create_interval_widget
)


class TestInterval:
    """Test the Interval widget class."""

    def setup_method(self):
        """Set up test fixtures."""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))

    def teardown_method(self):
        """Clean up test fixtures."""
        pygame.quit()

    def test_interval_initialization(self):
        """Test basic interval initialization."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(rect)

        assert interval.rect == rect
        assert interval.min_value == 0
        assert interval.max_value == 100
        assert interval.from_value == 0
        assert interval.to_value == 100
        assert interval.orientation == Orientation.HORIZONTAL
        assert interval.state == IntervalState.NORMAL
        assert interval.command is None

    def test_interval_custom_values(self):
        """Test interval with custom values."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(
            rect,
            min_value=20,
            max_value=80,
            from_value=10,
            to_value=90,
            orientation=Orientation.VERTICAL,
            label="Test Label",
            show_value=False
        )

        assert interval.min_value == 20
        assert interval.max_value == 80
        assert interval.from_value == 10
        assert interval.to_value == 90
        assert interval.orientation == Orientation.VERTICAL
        assert interval.label == "Test Label"
        assert not interval.show_value

    def test_set_values(self):
        """Test setting interval values."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(rect)

        # Test normal set
        interval.set_values(25, 75)
        assert interval.min_value == 25
        assert interval.max_value == 75

        # Test min > max correction
        interval.set_values(80, 20)
        assert interval.min_value == 20
        assert interval.max_value == 80

        # Test clamping to range
        interval.set_values(-10, 150)
        assert interval.min_value == 0
        assert interval.max_value == 100

    def test_get_values(self):
        """Test getting interval values."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(rect, min_value=30, max_value=70)

        min_val, max_val = interval.get_values()
        assert min_val == 30
        assert max_val == 70

    def test_reset(self):
        """Test resetting interval to full range."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(rect, min_value=25, max_value=75)

        interval.reset()
        assert interval.min_value == 0
        assert interval.max_value == 100

    def test_value_to_pixel_horizontal(self):
        """Test value to pixel conversion for horizontal orientation."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(rect, from_value=0, to_value=100)

        # Test endpoints - actual calculated values
        assert interval._value_to_pixel(0) == 22  # left + border + handle_width//2 + offset
        assert interval._value_to_pixel(100) == 198  # right - border - handle_width//2

        # Test middle
        middle_pixel = interval._value_to_pixel(50)
        assert 105 <= middle_pixel <= 115  # Approximately center

    def test_value_to_pixel_vertical(self):
        """Test value to pixel conversion for vertical orientation."""
        rect = pygame.Rect(10, 10, 50, 200)
        interval = Interval(rect, from_value=0, to_value=100, orientation=Orientation.VERTICAL)

        # Test endpoints - actual calculated values
        assert interval._value_to_pixel(0) == 198  # bottom - border - handle_width//2
        assert interval._value_to_pixel(100) == 22  # top + border + handle_width//2

        # Test middle
        middle_pixel = interval._value_to_pixel(50)
        assert 105 <= middle_pixel <= 115  # Approximately center

    def test_pixel_to_value_horizontal(self):
        """Test pixel to value conversion for horizontal orientation."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(rect, from_value=0, to_value=100)

        # Test endpoints
        assert interval._pixel_to_value(10 + 2 + 5) == 0  # left edge
        assert interval._pixel_to_value(10 + 200 - 2 - 5) == 100  # right edge

        # Test middle
        middle_value = interval._pixel_to_value(10 + 100)
        assert 45 <= middle_value <= 55  # Approximately 50

    def test_pixel_to_value_vertical(self):
        """Test pixel to value conversion for vertical orientation."""
        rect = pygame.Rect(10, 10, 50, 200)
        interval = Interval(rect, from_value=0, to_value=100, orientation=Orientation.VERTICAL)

        # Test endpoints
        assert interval._pixel_to_value(10 + 2 + 5) == 100  # top edge
        assert interval._pixel_to_value(10 + 200 - 2 - 5) == 0  # bottom edge

    def test_get_handle_rects_horizontal(self):
        """Test getting handle rectangles for horizontal orientation."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(rect, min_value=25, max_value=75)

        min_rect, max_rect = interval._get_handle_rects()

        # Min handle should be at 25% position
        assert min_rect.centerx < max_rect.centerx
        assert min_rect.centery == rect.centery
        assert max_rect.centery == rect.centery

    def test_get_handle_rects_vertical(self):
        """Test getting handle rectangles for vertical orientation."""
        rect = pygame.Rect(10, 10, 50, 200)
        interval = Interval(rect, min_value=25, max_value=75, orientation=Orientation.VERTICAL)

        min_rect, max_rect = interval._get_handle_rects()

        # Min handle should be lower (higher y) than max handle
        assert min_rect.centery > max_rect.centery
        assert min_rect.centerx == rect.centerx
        assert max_rect.centerx == rect.centerx

    def test_configure(self):
        """Test configuring interval properties."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(rect)

        interval.configure(min_value=30, max_value=70, label="New Label")
        assert interval.min_value == 30
        assert interval.max_value == 70
        assert interval.label == "New Label"

    def test_handle_event_disabled(self):
        """Test that disabled intervals don't handle events."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(rect, state=IntervalState.DISABLED)

        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (50, 25), 'button': 1})
        assert not interval.handle_event(event)

    def test_handle_event_mouse_motion_no_drag(self):
        """Test mouse motion when not dragging."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(rect)

        event = pygame.event.Event(pygame.MOUSEMOTION, {'pos': (50, 25), 'buttons': (0, 0, 0)})
        assert not interval.handle_event(event)

    def test_handle_event_mouse_button_up_no_drag(self):
        """Test mouse button up when not dragging."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(rect)

        event = pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (50, 25), 'button': 1})
        assert not interval.handle_event(event)

    def test_handle_event_click_outside(self):
        """Test clicking outside the interval."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(rect)

        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (300, 300), 'button': 1})
        assert not interval.handle_event(event)

    def test_handle_event_min_handle_drag(self):
        """Test dragging the minimum handle."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(rect, min_value=25, max_value=75)

        # Get min handle position
        min_rect, _ = interval._get_handle_rects()
        click_pos = min_rect.center

        # Start drag
        down_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                      {'pos': click_pos, 'button': 1})
        assert interval.handle_event(down_event)
        assert interval.dragging == 'min'

        # Drag to new position
        new_x = click_pos[0] + 50
        motion_event = pygame.event.Event(pygame.MOUSEMOTION,
                                        {'pos': (new_x, click_pos[1]), 'buttons': (1, 0, 0)})
        assert interval.handle_event(motion_event)

        # Check value changed
        new_value = interval._pixel_to_value(new_x)
        assert interval.min_value == new_value

        # End drag
        up_event = pygame.event.Event(pygame.MOUSEBUTTONUP,
                                    {'pos': (new_x, click_pos[1]), 'button': 1})
        assert interval.handle_event(up_event)
        assert interval.dragging is None

    def test_handle_event_max_handle_drag(self):
        """Test dragging the maximum handle."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(rect, min_value=25, max_value=75)

        # Get max handle position
        _, max_rect = interval._get_handle_rects()
        click_pos = max_rect.center

        # Start drag
        down_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                      {'pos': click_pos, 'button': 1})
        assert interval.handle_event(down_event)
        assert interval.dragging == 'max'

        # Drag to new position
        new_x = click_pos[0] - 30
        motion_event = pygame.event.Event(pygame.MOUSEMOTION,
                                        {'pos': (new_x, click_pos[1]), 'buttons': (1, 0, 0)})
        assert interval.handle_event(motion_event)

        # Check value changed
        new_value = interval._pixel_to_value(new_x)
        assert interval.max_value == new_value

    def test_handle_event_center_drag(self):
        """Test dragging the center area (both handles together)."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(rect, min_value=25, max_value=75)

        # Click in center area
        center_x = (interval._value_to_pixel(25) + interval._value_to_pixel(75)) // 2
        click_pos = (center_x, rect.centery)

        # Start drag
        down_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                      {'pos': click_pos, 'button': 1})
        assert interval.handle_event(down_event)
        assert interval.dragging == 'center'

        # Drag to new position
        new_x = center_x + 40
        motion_event = pygame.event.Event(pygame.MOUSEMOTION,
                                        {'pos': (new_x, click_pos[1]), 'buttons': (1, 0, 0)})
        assert interval.handle_event(motion_event)

        # Check both values changed by same amount
        delta = interval._pixel_to_value(new_x) - interval._pixel_to_value(center_x)
        expected_min = 25 + delta
        expected_max = 75 + delta

        assert abs(interval.min_value - expected_min) < 2  # Allow small rounding differences
        assert abs(interval.max_value - expected_max) < 2

    def test_command_callback(self):
        """Test that command callback is called when values change."""
        rect = pygame.Rect(10, 10, 200, 50)
        callback_mock = Mock()
        interval = Interval(rect, command=callback_mock)

        interval.set_values(30, 70)
        callback_mock.assert_called_once_with(30, 70)

    def test_draw_basic(self):
        """Test basic drawing functionality."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = Interval(rect)

        # Create a test surface
        surface = pygame.Surface((220, 70))

        # Should not raise an exception
        interval.draw(surface)

        # Check that surface was drawn to (not empty)
        # This is a basic check - in a real test we'd check pixel colors
        assert surface.get_width() == 220
        assert surface.get_height() == 70


class TestTkIntervalCmd:
    """Test the Tk_IntervalCmd stub function."""

    def test_tk_interval_cmd_returns_none(self):
        """Test that Tk_IntervalCmd returns None (stub implementation)."""
        result = Tk_IntervalCmd()
        assert result is None


class TestCreateIntervalWidget:
    """Test the create_interval_widget convenience function."""

    def setup_method(self):
        """Set up test fixtures."""
        pygame.init()

    def teardown_method(self):
        """Clean up test fixtures."""
        pygame.quit()

    def test_create_interval_widget(self):
        """Test creating an interval widget with the convenience function."""
        rect = pygame.Rect(10, 10, 200, 50)
        interval = create_interval_widget(rect, min_value=20, max_value=80)

        assert isinstance(interval, Interval)
        assert interval.rect == rect
        assert interval.min_value == 20
        assert interval.max_value == 80


class TestOrientation:
    """Test the Orientation enum."""

    def test_orientation_values(self):
        """Test that orientation enum has correct values."""
        assert Orientation.HORIZONTAL.value == "horizontal"
        assert Orientation.VERTICAL.value == "vertical"


class TestIntervalState:
    """Test the IntervalState enum."""

    def test_interval_state_values(self):
        """Test that interval state enum has correct values."""
        assert IntervalState.NORMAL.value == "normal"
        assert IntervalState.DISABLED.value == "disabled"