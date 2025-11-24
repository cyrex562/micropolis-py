"""
date_display.py - Date display widget for Micropolis Python port

This module implements the date display system ported from w_date.c,
responsible for displaying the current game date (month and year) with
animation effects for time progression.
"""

import pygame
import logging

from micropolis.context import AppContext

logger = logging.getLogger()

# ---------------------------------------------------------------------------
# Context helpers
# ---------------------------------------------------------------------------


def _resolve_context(context: AppContext | None = None) -> AppContext:
    if context is not None:
        return context

    import builtins
    ctx = getattr(builtins, "context", None)
    if isinstance(ctx, AppContext):
        return ctx

    try:
        import importlib

        for pkg_name in ("micropolis", "src.micropolis"):
            try:
                pkg = importlib.import_module(pkg_name)
            except ImportError:
                continue
            candidate = getattr(pkg, "_AUTO_TEST_CONTEXT", None)
            if isinstance(candidate, AppContext):
                return candidate
    except Exception:
        pass

    raise RuntimeError("Date display context is required")


def _sync_time_context(context: AppContext) -> None:
    """No-op: AppContext is now the authoritative source for time data."""
    pass
# ============================================================================
# Constants
# ============================================================================

# Month names (from w_update.c)
MONTH_NAMES = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

# Default colors (adapted from TCL config)
DEFAULT_BG_COLOR = (176, 176, 176)  # #b0b0b0
DEFAULT_FG_COLOR = (0, 0, 0)  # Black text
DEFAULT_GRAY_COLOR = (128, 128, 128)  # Dark gray for animation

# Default font settings
DEFAULT_FONT_SIZE = 14
DEFAULT_FONT_NAME = None  # Use system default

# Layout constants
BORDER_WIDTH = 2
PAD_X = 1
PAD_Y = 1
MONTH_TAB_CHARS = 7  # Character positions for month alignment
YEAR_TAB_CHARS = 13  # Character positions for year alignment

# Animation timing (milliseconds)
DATE_UPDATE_TIME = 200

# ============================================================================
# Date Display Widget
# ============================================================================


class SimDate:
    """
    Date display widget adapted for pygame.

    Ported from SimDate struct in w_date.c.
    Displays current game date with animation effects.
    """

    def __init__(self):
        # Core date state
        self.reset: bool = True
        self.month: int = 0
        self.year: int = 0
        self.last_month: int = 0
        self.last_year: int = 0

        # Display state
        self.visible: bool = False
        self.w_x: int = 0
        self.w_y: int = 0
        self.w_width: int = 0
        self.w_height: int = 0

        # Pygame rendering
        self.surface: pygame.Surface | None = None
        self.font: pygame.font.Font | None = None
        self.needs_redraw: bool = False

        # Layout parameters
        self.border_width: int = BORDER_WIDTH
        self.pad_x: int = PAD_X
        self.pad_y: int = PAD_Y
        self.width: int = 0  # 0 = auto-size
        self.month_tab: int = MONTH_TAB_CHARS
        self.year_tab: int = YEAR_TAB_CHARS

        # Animation state
        self.animation_months: list[int] = []  # Months to show in gray during animation
        self.animation_years: list[int] = []  # Years to show in gray during animation
        self.animation_timer: int = 0

    def set_position(self, x: int, y: int) -> None:
        """Set widget position"""
        self.w_x = x
        self.w_y = y

    def set_size(self, width: int, height: int) -> None:
        """Set widget size and recreate surface"""
        self.w_width = width
        self.w_height = height
        if width > 0 and height > 0:
            self.surface = pygame.Surface((width, height))
            self._init_font()
            self.needs_redraw = True

    def set_visible(self, visible: bool) -> None:
        """Set widget visibility"""
        self.visible = visible
        if visible:
            self.needs_redraw = True

    def set_date(self, month: int, year: int) -> None:
        """
        Set the current date.

        Args:
            month: Month (0-11)
            year: Year
        """
        if month < 0 or month >= 12:
            raise ValueError("Month must be 0-11")
        if year < 0:
            raise ValueError("Year must be non-negative")

        self.month = month
        self.year = year
        self.needs_redraw = True

    def reset_display(self) -> None:
        """Reset the display (clear animation state)"""
        self.reset = True
        self.animation_months.clear()
        self.animation_years.clear()
        self.needs_redraw = True

    def update_date(self, context: AppContext | None = None) -> None:
        """
        Update the date from CityTime.

        Calculates current month and year from CityTime.
        """
        # Calculate current date from CityTime
        # CityTime increments every game tick, 48 ticks = 1 year, 4 ticks = 1 month
        context = _resolve_context(context)
        _sync_time_context(context)

        current_year = (context.city_time // 48) + context.starting_year
        current_month = (context.city_time // 4) % 12

        # Check if date has changed
        if current_year != self.last_year or current_month != self.last_month:
            # Set up animation if this isn't a reset
            if not self.reset:
                self._setup_animation(current_month, current_year)

            # Update current date
            self.month = current_month
            self.year = current_year
            self.last_month = current_month
            self.last_year = current_year
            self.reset = False
            self.needs_redraw = True

    def _setup_animation(self, new_month: int, new_year: int) -> None:
        """
        Set up animation sequence for date change.

        Shows previous months/years in gray before displaying current date.
        """
        self.animation_months.clear()
        self.animation_years.clear()

        # Calculate months and years that have passed
        years_passed = new_year - self.last_year
        if years_passed < 0:
            years_passed = 1
        if years_passed > 9:
            years_passed = 9

        months_passed = (new_month - self.last_month) + (12 * years_passed)
        if months_passed > 11:
            months_passed = 11
        if months_passed == 1:
            months_passed = 0

        # Set up animation sequence
        if months_passed > 0:
            current_month = self.last_month
            for i in range(months_passed):
                self.animation_months.append(current_month)
                current_month += 1
                if current_month == 12:
                    current_month = 0

            # Set up year animation if year changed
            if new_year != self.last_year:
                start_year = self.last_year
                if (new_year - start_year) > 10:
                    start_year = new_year - 10

                for year in range(start_year, new_year):
                    self.animation_years.append(year)

    def _init_font(self) -> None:
        """Initialize font for rendering"""
        try:
            self.font = pygame.font.Font(DEFAULT_FONT_NAME, DEFAULT_FONT_SIZE)
        except Exception as ex:
            logger.exception(f"failed to load font: {ex}")
            self.font = pygame.font.SysFont(None, DEFAULT_FONT_SIZE)

    def _compute_geometry(self) -> tuple:
        """
        Compute widget geometry.

        Returns:
            Tuple of (width, height, month_x, year_x)
        """
        if self.font is None:
            self._init_font()

        # Ensure font is initialized
        assert self.font is not None, "Font should be initialized"

        # Calculate positions
        char_width = self.font.size("0")[0]
        month_x = self.month_tab * char_width
        year_x = self.year_tab * char_width

        # Calculate total width
        if self.width == 0:
            # Auto-size based on maximum expected text
            max_text = "Date: MMM    1000000"
            total_width = self.font.size(max_text)[0]
        else:
            total_width = self.width * char_width

        # Calculate height
        height = self.font.get_height()

        # Add padding and borders
        total_width += 2 * self.pad_x + 2 * self.border_width
        height += 2 * self.pad_y + 2 * self.border_width

        return total_width, height, month_x, year_x

    def render(self) -> None:
        """
        Render the date display to the surface.
        """
        if not self.visible or self.surface is None:
            return

        if self.font is None:
            self._init_font()

        # Ensure font is initialized
        assert self.font is not None, "Font should be initialized"

        # Clear surface with background color
        self.surface.fill(DEFAULT_BG_COLOR)

        # Compute layout
        width, height, month_x, year_x = self._compute_geometry()

        # Calculate text positions
        text_x = self.border_width + self.pad_x
        text_y = self.border_width + self.pad_y + self.font.get_ascent()

        # Draw date label
        date_label = "Date:"
        label_surf = self.font.render(date_label, True, DEFAULT_FG_COLOR)
        self.surface.blit(label_surf, (text_x, text_y - self.font.get_ascent()))

        # Draw animated months (in gray)
        for anim_month in self.animation_months:
            month_text = MONTH_NAMES[anim_month]
            month_surf = self.font.render(month_text, True, DEFAULT_GRAY_COLOR)
            self.surface.blit(
                month_surf, (text_x + month_x, text_y - self.font.get_ascent())
            )

        # Draw animated years (in gray)
        for anim_year in self.animation_years:
            year_text = str(anim_year)
            year_surf = self.font.render(year_text, True, DEFAULT_GRAY_COLOR)
            self.surface.blit(
                year_surf, (text_x + year_x, text_y - self.font.get_ascent())
            )

        # Draw current month and year (in black)
        month_text = MONTH_NAMES[self.month]
        month_surf = self.font.render(month_text, True, DEFAULT_FG_COLOR)
        self.surface.blit(
            month_surf, (text_x + month_x, text_y - self.font.get_ascent())
        )

        year_text = str(self.year)
        year_surf = self.font.render(year_text, True, DEFAULT_FG_COLOR)
        self.surface.blit(year_surf, (text_x + year_x, text_y - self.font.get_ascent()))

        self.needs_redraw = False

    def get_surface(self) -> pygame.Surface | None:
        """
        Get the rendered surface.

        Returns:
            The pygame surface containing the rendered date display
        """
        if self.needs_redraw:
            self.render()
        return self.surface


# ============================================================================
# Date Display Management
# ============================================================================

# Global date display instances
_date_displays: list[SimDate] = []


def create_date_display() -> SimDate:
    """
    Create a new date display instance.

    Returns:
        New SimDate instance
    """
    date_display = SimDate()
    _date_displays.append(date_display)
    return date_display


def get_date_displays() -> list[SimDate]:
    """
    Get all date display instances.

    Returns:
        List of all SimDate instances
    """
    return _date_displays.copy()


def remove_date_display(date_display: SimDate) -> None:
    """
    Remove a date display instance.

    Args:
        date_display: Date display instance to remove
    """
    if date_display in _date_displays:
        _date_displays.remove(date_display)


# ============================================================================
# Date Display Updates
# ============================================================================


def update_date_displays(context: AppContext) -> None:
    """
    Update all date display instances.

    Called from main game loop to update date displays.
    :param context:
    """
    for date_display in _date_displays:
        date_display.update_date(context)
        if date_display.needs_redraw:
            date_display.render()


# ============================================================================
# TCL Command Compatibility (Adapted for pygame)
# ============================================================================


def configure_date_display(date_display: SimDate, **kwargs) -> None:
    """
    Configure date display properties.

    Args:
        date_display: Date display to configure
        **kwargs: Configuration options
    """
    # Handle configuration options
    if "font" in kwargs:
        # Font configuration (simplified for pygame)
        pass

    if "background" in kwargs:
        # Background color (simplified)
        pass

    if "borderwidth" in kwargs:
        try:
            date_display.border_width = int(kwargs["borderwidth"])
        except ValueError:
            pass

    if "padx" in kwargs:
        try:
            date_display.pad_x = int(kwargs["padx"])
        except ValueError:
            pass

    if "pady" in kwargs:
        try:
            date_display.pad_y = int(kwargs["pady"])
        except ValueError:
            pass

    if "width" in kwargs:
        try:
            date_display.width = int(kwargs["width"])
        except ValueError:
            pass

    if "monthtab" in kwargs:
        try:
            date_display.month_tab = int(kwargs["monthtab"])
        except ValueError:
            pass

    if "yeartab" in kwargs:
        try:
            date_display.year_tab = int(kwargs["yeartab"])
        except ValueError:
            pass

    date_display.needs_redraw = True


def get_date_position(date_display: SimDate) -> tuple:
    """
    Get date display position.

    Args:
        date_display: Date display instance

    Returns:
        Tuple of (x, y) coordinates
    """
    return date_display.w_x, date_display.w_y


def set_date_position(date_display: SimDate, x: int, y: int) -> None:
    """
    Set date display position.

    Args:
        date_display: Date display instance
        x: X coordinate
        y: Y coordinate
    """
    date_display.set_position(x, y)


def get_date_size(date_display: SimDate) -> tuple:
    """
    Get date display size.

    Args:
        date_display: Date display instance

    Returns:
        Tuple of (width, height)
    """
    return date_display.w_width, date_display.w_height


def set_date_size(date_display: SimDate, width: int, height: int) -> None:
    """
    Set date display size.

    Args:
        date_display: Date display instance
        width: Width
        height: Height
    """
    date_display.set_size(width, height)


def get_date_visible(date_display: SimDate) -> bool:
    """
    Get date display visibility.

    Args:
        date_display: Date display instance

    Returns:
        True if visible, False otherwise
    """
    return date_display.visible


def set_date_visible(date_display: SimDate, visible: bool) -> None:
    """
    Set date display visibility.

    Args:
        date_display: Date display instance
        visible: True to show, False to hide
    """
    date_display.set_visible(visible)


def reset_date_display(date_display: SimDate) -> None:
    """
    Reset date display.

    Args:
        date_display: Date display instance
    """
    date_display.reset_display()


def set_date(date_display: SimDate, month: int, year: int) -> None:
    """
    Set date display date.

    Args:
        date_display: Date display instance
        month: Month (0-11)
        year: Year
    """
    date_display.set_date(month, year)


# ============================================================================
# Utility Functions
# ============================================================================


def get_current_month_name(context: AppContext | None = None) -> str:
    """
    Get the name of the current month based on CityTime.

    Returns:
        Month name abbreviation
        :param context:
    """
    context = _resolve_context(context)
    _sync_time_context(context)
    current_month = (context.city_time // 4) % 12
    return MONTH_NAMES[current_month]


def get_current_year(context: AppContext | None = None) -> int:
    """
    Get the current year based on CityTime.

    Returns:
        Current year
        :param context:
    """
    context = _resolve_context(context)
    _sync_time_context(context)
    return (context.city_time // 48) + context.starting_year


def format_date_string(context: AppContext | None = None) -> str:
    """
    Format current date as a string.

    Returns:
        Formatted date string (e.g., "Jan 1900")
        :param context:
    """
    context = _resolve_context(context)
    month_name = get_current_month_name(context)
    year = get_current_year(context)
    return f"{month_name} {year}"


# ============================================================================
# Initialization
# ============================================================================


def initialize_date_displays() -> None:
    """
    Initialize the date display system.

    Called during game initialization.
    """
    # Clear any existing displays
    _date_displays.clear()
