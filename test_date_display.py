"""
test_date_display.py - Tests for date_display.py module

Tests the date display widget ported from w_date.c.
"""

import pytest
import pygame
from src.micropolis import date_display, types


class TestDateDisplayCreation:
    """Test date display creation and management"""

    def test_create_date_display(self):
        """Test creating a new date display instance"""
        initial_count = len(date_display.get_date_displays())
        display = date_display.create_date_display()

        assert isinstance(display, date_display.SimDate)
        assert display.month == 0
        assert display.year == 0
        assert not display.visible
        assert len(date_display.get_date_displays()) == initial_count + 1

    def test_remove_date_display(self):
        """Test removing a date display instance"""
        display = date_display.create_date_display()
        initial_count = len(date_display.get_date_displays())

        date_display.remove_date_display(display)
        assert len(date_display.get_date_displays()) == initial_count - 1

    def test_get_date_displays(self):
        """Test getting all date display instances"""
        displays = date_display.get_date_displays()
        assert isinstance(displays, list)


class TestDateDisplayConfiguration:
    """Test date display configuration methods"""

    def setup_method(self):
        """Setup for each test"""
        pygame.init()
        pygame.font.init()  # Ensure font system is initialized
        self.display = date_display.create_date_display()

    def teardown_method(self):
        """Cleanup after each test"""
        date_display.remove_date_display(self.display)
        pygame.quit()

    def test_set_position(self):
        """Test setting display position"""
        self.display.set_position(100, 200)
        assert self.display.w_x == 100
        assert self.display.w_y == 200

    def test_set_size(self):
        """Test setting display size"""
        self.display.set_size(400, 300)
        assert self.display.w_width == 400
        assert self.display.w_height == 300
        assert self.display.surface is not None
        assert self.display.needs_redraw

    def test_set_visible(self):
        """Test setting display visibility"""
        self.display.set_visible(True)
        assert self.display.visible
        assert self.display.needs_redraw

    def test_set_date(self):
        """Test setting date"""
        self.display.set_date(5, 1950)  # June 1950
        assert self.display.month == 5
        assert self.display.year == 1950
        assert self.display.needs_redraw

    def test_set_date_invalid_month(self):
        """Test setting invalid month"""
        with pytest.raises(ValueError, match="Month must be 0-11"):
            self.display.set_date(12, 1950)

    def test_set_date_invalid_year(self):
        """Test setting invalid year"""
        with pytest.raises(ValueError, match="Year must be non-negative"):
            self.display.set_date(5, -1)

    def test_reset_display(self):
        """Test resetting display"""
        self.display.set_date(5, 1950)
        self.display.reset_display()
        assert self.display.reset
        assert self.display.needs_redraw


class TestDateUpdate:
    """Test date updating from CityTime"""

    def setup_method(self):
        """Setup for each test"""
        self.display = date_display.create_date_display()
        # Reset CityTime for consistent testing
        types.CityTime = 0
        types.StartingYear = 1900

    def teardown_method(self):
        """Cleanup after each test"""
        date_display.remove_date_display(self.display)

    def test_update_date_initial(self):
        """Test initial date update"""
        self.display.update_date()
        assert self.display.month == 0  # January
        assert self.display.year == 1900
        assert self.display.last_month == 0
        assert self.display.last_year == 1900

    def test_update_date_advance_month(self):
        """Test date update when advancing one month"""
        # Set initial state
        self.display.last_month = 0
        self.display.last_year = 1900

        # Advance CityTime by 4 ticks (1 month)
        types.CityTime = 4

        self.display.update_date()
        assert self.display.month == 1  # February
        assert self.display.year == 1900

    def test_update_date_advance_year(self):
        """Test date update when advancing one year"""
        # Set initial state
        self.display.last_month = 0
        self.display.last_year = 1900

        # Advance CityTime by 48 ticks (1 year)
        types.CityTime = 48

        self.display.update_date()
        assert self.display.month == 0  # January
        assert self.display.year == 1901

    def test_update_date_no_change(self):
        """Test date update when CityTime hasn't changed enough"""
        # Set initial state
        self.display.last_month = 0
        self.display.last_year = 1900
        self.display.month = 0
        self.display.year = 1900

        # Advance CityTime by only 1 tick (not enough for month change)
        types.CityTime = 1

        self.display.update_date()
        # Should not change
        assert self.display.month == 0
        assert self.display.year == 1900


class TestAnimation:
    """Test date change animation"""

    def setup_method(self):
        """Setup for each test"""
        self.display = date_display.create_date_display()

    def teardown_method(self):
        """Cleanup after each test"""
        date_display.remove_date_display(self.display)

    def test_setup_animation_months_only(self):
        """Test animation setup for month changes only"""
        self.display.last_month = 0  # January
        self.display.last_year = 1900
        self.display.reset = False

        self.display._setup_animation(3, 1900)  # April 1900

        # Should show January, February, and March in animation (months that have passed)
        assert self.display.animation_months == [0, 1, 2]  # Jan, Feb, Mar
        assert self.display.animation_years == []

    def test_setup_animation_with_year_change(self):
        """Test animation setup with year change"""
        self.display.last_month = 10  # November
        self.display.last_year = 1899
        self.display.reset = False

        self.display._setup_animation(1, 1900)  # February 1900

        # Should show November, December 1899 and January 1900
        assert self.display.animation_months == [10, 11, 0]  # Nov, Dec, Jan
        assert self.display.animation_years == [1899]

    def test_setup_animation_no_change(self):
        """Test animation setup with no change"""
        self.display.last_month = 5
        self.display.last_year = 1900
        self.display.reset = False

        self.display._setup_animation(5, 1900)  # Same date

        assert self.display.animation_months == []
        assert self.display.animation_years == []


class TestRendering:
    """Test date display rendering"""

    def setup_method(self):
        """Setup for each test"""
        pygame.init()
        self.display = date_display.create_date_display()
        self.display.set_size(400, 300)

    def teardown_method(self):
        """Cleanup after each test"""
        date_display.remove_date_display(self.display)
        pygame.quit()

    def test_render_not_visible(self):
        """Test rendering when not visible"""
        self.display.visible = False
        self.display.render()
        # Should not crash

    def test_render_no_surface(self):
        """Test rendering with no surface"""
        self.display.visible = True
        self.display.surface = None
        self.display.render()
        # Should not crash

    def test_render_visible(self):
        """Test rendering when visible"""
        self.display.visible = True
        self.display.set_date(5, 1950)  # June 1950

        self.display.render()

        assert not self.display.needs_redraw
        assert self.display.surface is not None

    def test_get_surface(self):
        """Test getting rendered surface"""
        self.display.visible = True
        self.display.needs_redraw = True

        surface = self.display.get_surface()

        assert surface is not None
        assert not self.display.needs_redraw


class TestTCLCommands:
    """Test TCL command compatibility functions"""

    def setup_method(self):
        """Setup for each test"""
        pygame.init()
        pygame.font.init()  # Ensure font system is initialized
        self.display = date_display.create_date_display()

    def teardown_method(self):
        """Cleanup after each test"""
        date_display.remove_date_display(self.display)
        pygame.quit()

    def test_configure_date_display(self):
        """Test configuring date display"""
        date_display.configure_date_display(self.display, borderwidth="3", padx="2")
        assert self.display.border_width == 3
        assert self.display.pad_x == 2
        assert self.display.needs_redraw

    def test_position_commands(self):
        """Test position get/set commands"""
        # Set position
        date_display.set_date_position(self.display, 100, 200)
        assert self.display.w_x == 100
        assert self.display.w_y == 200

        # Get position
        x, y = date_display.get_date_position(self.display)
        assert x == 100
        assert y == 200

    def test_size_commands(self):
        """Test size get/set commands"""
        # Set size
        date_display.set_date_size(self.display, 400, 300)
        assert self.display.w_width == 400
        assert self.display.w_height == 300

        # Get size
        w, h = date_display.get_date_size(self.display)
        assert w == 400
        assert h == 300

    def test_visibility_commands(self):
        """Test visibility get/set commands"""
        # Set visible
        date_display.set_date_visible(self.display, True)
        assert self.display.visible

        # Get visible
        visible = date_display.get_date_visible(self.display)
        assert visible

    def test_reset_command(self):
        """Test reset command"""
        self.display.set_date(5, 1950)
        date_display.reset_date_display(self.display)
        assert self.display.reset

    def test_set_date_command(self):
        """Test set date command"""
        date_display.set_date(self.display, 5, 1950)
        assert self.display.month == 5
        assert self.display.year == 1950


class TestUtilityFunctions:
    """Test utility functions"""

    def setup_method(self):
        """Setup for each test"""
        types.CityTime = 0
        types.StartingYear = 1900

    def test_get_current_month_name(self):
        """Test getting current month name"""
        month_name = date_display.get_current_month_name()
        assert month_name == "Jan"

        # Advance to June (5 months * 4 ticks = 20 ticks)
        types.CityTime = 20
        month_name = date_display.get_current_month_name()
        assert month_name == "Jun"

    def test_get_current_year(self):
        """Test getting current year"""
        year = date_display.get_current_year()
        assert year == 1900

        # Advance by 1 year (48 ticks)
        types.CityTime = 48
        year = date_display.get_current_year()
        assert year == 1901

    def test_format_date_string(self):
        """Test formatting date string"""
        date_str = date_display.format_date_string()
        assert date_str == "Jan 1900"

        # Advance to June 1901
        types.CityTime = 48 + 20  # 1 year + 5 months
        date_str = date_display.format_date_string()
        assert date_str == "Jun 1901"


class TestInitialization:
    """Test initialization functions"""

    def test_initialize_date_displays(self):
        """Test initializing date displays"""
        # Create a display first
        date_display.create_date_display()

        # Initialize (should clear existing displays)
        date_display.initialize_date_displays()

        # Should have no displays after initialization
        assert len(date_display.get_date_displays()) == 0


class TestConstants:
    """Test constants and month names"""

    def test_month_names(self):
        """Test month name constants"""
        assert len(date_display.MONTH_NAMES) == 12
        assert date_display.MONTH_NAMES[0] == "Jan"
        assert date_display.MONTH_NAMES[11] == "Dec"

    def test_default_colors(self):
        """Test default color constants"""
        assert date_display.DEFAULT_BG_COLOR == (176, 176, 176)
        assert date_display.DEFAULT_FG_COLOR == (0, 0, 0)
        assert date_display.DEFAULT_GRAY_COLOR == (128, 128, 128)