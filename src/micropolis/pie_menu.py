"""
pie_menu.py - Pie Menu widget for Micropolis

Port of w_piem.c from C/Tk to Python/pygame.
Implements circular pie menus with configurable slices and TCL command interface.
"""

import math
from dataclasses import dataclass, field
from enum import Enum

import pygame

from src.micropolis.pie_menu_entry import PieMenuEntry

# Constants (ported from w_piem.c)
PI = 3.1415926535897932
TWO_PI = 6.2831853071795865
PIE_SPOKE_INSET = 6
PIE_BG_COLOR = "#bfbfbf"
PIE_ACTIVE_FG_COLOR = "black"
PIE_ACTIVE_BG_COLOR = "#bfbfbf"
PIE_FG = "black"
PIE_ACTIVE_BORDER_WIDTH = 2
PIE_INACTIVE_RADIUS = 8
PIE_MIN_RADIUS = 16
PIE_EXTRA_RADIUS = 2
PIE_BORDER_WIDTH = 2
PIE_POPUP_DELAY = 250


def deg_to_rad(deg: float) -> float:
    """Convert degrees to radians."""
    return (deg * TWO_PI) / 360.0


def rad_to_deg(rad: float) -> float:
    """Convert radians to degrees."""
    return (rad * 360.0) / TWO_PI


class EntryType(Enum):
    """Types of pie menu entries."""
    COMMAND = 0
    PIEMENU = 1


@dataclass
class PieMenu:
    """Pie menu widget with circular layout."""

    # Basic properties
    title: str = ""
    entries: list[PieMenuEntry] = field(default_factory=list)
    active: int = -1  # Active entry index (-1 = none)

    # Position and tracking
    root_x: int = 0
    root_y: int = 0
    dx: int = 0  # Cursor offset from center
    dy: int = 0

    # Display properties
    width: int = 0
    height: int = 0
    title_x: int = 0
    title_y: int = 0
    title_width: int = 0
    title_height: int = 0

    # Layout parameters
    initial_angle: float = 0.0  # Initial angle in degrees
    inactive_radius: int = PIE_INACTIVE_RADIUS
    min_radius: int = PIE_MIN_RADIUS
    fixed_radius: int = 0
    extra_radius: int = PIE_EXTRA_RADIUS
    label_radius: int = 0
    center_x: int = 0
    center_y: int = 0

    # Colors and fonts
    bg_color: str = PIE_BG_COLOR
    fg_color: str = PIE_FG
    active_bg_color: str = PIE_ACTIVE_BG_COLOR
    active_fg_color: str = PIE_ACTIVE_FG_COLOR
    border_width: int = PIE_BORDER_WIDTH
    active_border_width: int = PIE_ACTIVE_BORDER_WIDTH

    # State
    posted_submenu: PieMenuEntry | None = None
    flags: int = 0
    popup_delay: int = PIE_POPUP_DELAY
    shaped: bool = True

    # Pygame surfaces
    surface: pygame.Surface | None = None
    font: pygame.font.Font | None = None
    title_font: pygame.font.Font | None = None

    last_cursor_dx = 0
    last_cursor_dy = 0

    def __post_init__(self):
        """Initialize after dataclass creation."""
        if self.font is None:
            self.font = pygame.font.SysFont("helvetica", 12, bold=True)
        if self.title_font is None:
            self.title_font = pygame.font.SysFont("helvetica", 12, bold=True)

    def add_entry(self, entry_type: EntryType, label: str = "", **kwargs) -> PieMenuEntry:
        """Add a new entry to the pie menu."""
        entry = PieMenuEntry(
            type=entry_type,
            piemenu=self,
            label=label,
            **kwargs
        )
        self.entries.append(entry)
        self._recalculate_geometry()
        return entry

    def get_entry_at_position(self, x: int, y: int) -> int:
        """
        Get the entry index at the given position relative to menu center.

        Returns -1 if no entry is at the position.
        """
        # Translate to center-relative coordinates (right-side up)
        rel_x = x - self.center_x + 1
        rel_y = self.center_y - y - 1

        # Cursor tracking for distance/direction queries
        self.last_cursor_dx = rel_x
        self.last_cursor_dy = rel_y

        # Check if within inactive center region
        if len(self.entries) == 0 or (rel_x * rel_x + rel_y * rel_y <
                                      self.inactive_radius * self.inactive_radius):
            return -1

        # Single entry case
        if len(self.entries) == 1:
            return 0

        # Calculate quadrant and slope for cursor position
        quadrant, numerator, denominator = self._calc_quadrant_slope(rel_x, rel_y)

        # Start checking from item before current active one
        first = self.active - 1
        if first < 0:
            first = len(self.entries) - 1

        last_i = -1
        last_order = -1
        i = first

        while True:
            entry = self.entries[i]
            order = self._calc_order(quadrant, numerator, denominator, entry)

            # If we were counter-clockwise of last edge and clockwise of this edge,
            # then we were in the last menu item
            if last_order == 1 and order == 0:
                return last_i

            last_order = order
            last_i = i

            # Move to next item counter-clockwise
            i += 1
            if i >= len(self.entries):
                i = 0

            # If we've checked all items, return the last one
            if i == first:
                return last_i

    def _calc_quadrant_slope(self, x: float, y: float) -> tuple[int, int, int]:
        """Calculate quadrant, numerator, and denominator for slope calculation."""
        if y > 0:
            quadrant = 0 if x > 0 else 1
        elif y < 0:
            quadrant = 2 if x < 0 else 3
        else:
            quadrant = 0 if x > 0 else 2

        if quadrant & 1:
            numerator = abs(int(x))
            denominator = abs(int(y))
        else:
            numerator = abs(int(y))
            denominator = abs(int(x))

        return quadrant, numerator, denominator

    def _calc_order(self, cursor_quadrant: int, numerator: int, denominator: int,
                    entry: PieMenuEntry) -> int:
        """Calculate if cursor is clockwise or counter-clockwise of entry edge."""
        quad_diff = (cursor_quadrant - entry.quadrant) & 3

        if quad_diff == 0:
            # Same quadrant: compare slopes
            return 1 if numerator >= denominator * entry.slope else 0
        elif quad_diff == 1:
            return 1
        elif quad_diff == 2:
            # Opposite quadrant: compare slopes
            return 1 if numerator < denominator * entry.slope else 0
        else:  # quad_diff == 3
            return 0

    def _recalculate_geometry(self):
        """Recalculate menu geometry and layout."""
        if not self.entries:
            return

        # Calculate total slice size
        total_slice = sum(entry.slice_size for entry in self.entries)
        if total_slice == 0:
            total_slice = len(self.entries)  # Fallback to equal slices

        # Calculate geometry for each entry
        angle = deg_to_rad(self.initial_angle)
        for i, entry in enumerate(self.entries):
            # Calculate text/bitmap size
            if entry.bitmap:
                entry.width = entry.bitmap.get_width()
                entry.height = entry.bitmap.get_height()
            else:
                if self.font:
                    text_surface = self.font.render(entry.label, True, (0, 0, 0))
                    entry.width = text_surface.get_width()
                    entry.height = text_surface.get_height()
                else:
                    entry.width = len(entry.label) * 8  # Rough estimate
                    entry.height = 16

            entry.width += 2 * self.active_border_width + 2
            entry.height += 2 * self.active_border_width + 2

            # Calculate slice geometry
            entry.subtend = TWO_PI * entry.slice_size / total_slice
            twist = entry.subtend / 2.0
            if i != 0:
                angle += twist
            entry.angle = angle
            entry.dx = math.cos(angle)
            entry.dy = math.sin(angle)

            # Calculate edge quadrant and slope
            edge_dx = math.cos(angle - twist)
            edge_dy = math.sin(angle - twist)
            quadrant, numerator, denominator = self._calc_quadrant_slope(edge_dx, edge_dy)
            entry.quadrant = quadrant
            entry.slope = numerator / denominator if denominator != 0 else 0

            angle += twist

        # Calculate label radius
        radius = self.fixed_radius
        if radius == 0:
            radius = self.min_radius
            if len(self.entries) > 1:
                self._adjust_radius_for_overlaps(radius)

        self.label_radius = radius + self.extra_radius

        # Position all labels
        self._position_labels()

        # Calculate title size if present
        if self.title and self.title_font:
            title_surface = self.title_font.render(self.title, True, (0, 0, 0))
            self.title_width = title_surface.get_width() + 2
            self.title_height = title_surface.get_height() + 2
        else:
            self.title_width = self.title_height = 0

        # Calculate overall menu bounds
        self._calculate_bounds()

    def _adjust_radius_for_overlaps(self, radius: int):
        """Adjust radius to prevent label overlaps."""
        # Simplified overlap detection - expand radius until no overlaps
        while True:
            overlaps = False
            for i, entry1 in enumerate(self.entries):
                for j, entry2 in enumerate(self.entries):
                    if i != j and self._entries_overlap(entry1, entry2, radius):
                        overlaps = True
                        break
                if overlaps:
                    break
            if not overlaps:
                break
            radius += 1

    def _entries_overlap(self, entry1: PieMenuEntry, entry2: PieMenuEntry, radius: int) -> bool:
        """Check if two entries overlap at given radius."""
        x1 = entry1.dx * radius + entry1.x_offset
        y1 = entry1.dy * radius + entry1.y_offset
        x2 = entry2.dx * radius + entry2.x_offset
        y2 = entry2.dy * radius + entry2.y_offset

        # Adjust for label positioning
        if abs(x1) <= 2:
            x1 -= entry1.width / 2
            if y1 < 0:
                y1 -= entry1.height
        else:
            if x1 < 0:
                x1 -= entry1.width
            y1 -= entry1.height / 2

        if abs(x2) <= 2:
            x2 -= entry2.width / 2
            if y2 < 0:
                y2 -= entry2.height
        else:
            if x2 < 0:
                x2 -= entry2.width
            y2 -= entry2.height / 2

        # Check rectangle overlap
        return not (x1 + entry1.width <= x2 or x2 + entry2.width <= x1 or
                   y1 + entry1.height <= y2 or y2 + entry2.height <= y1)

    def _position_labels(self):
        """Position all menu labels at the calculated radius."""
        minx = miny = maxx = maxy = 0

        for entry in self.entries:
            entry.x = int(self.label_radius * entry.dx + entry.x_offset)
            entry.y = int(self.label_radius * entry.dy + entry.y_offset)

            # Adjust for label positioning
            if abs(entry.x) <= 2:
                entry.x -= entry.width // 2
                if entry.y < 0:
                    entry.y -= entry.height
            else:
                if entry.x < 0:
                    entry.x -= entry.width
                entry.y -= entry.height // 2

            entry.label_x = entry.x + self.active_border_width + 1
            entry.label_y = entry.y + self.active_border_width + 1

            # Update bounds
            minx = min(minx, entry.x)
            maxx = max(maxx, entry.x + entry.width)
            miny = min(miny, entry.y)
            maxy = max(maxy, entry.y + entry.height)

        # Add title to bounds if present
        if self.title:
            minx = min(minx, -self.title_width // 2)
            maxx = max(maxx, self.title_width // 2)
            maxy += 2 * self.border_width + self.title_height

        # Add border padding
        minx -= 2 * self.border_width
        miny -= 2 * self.border_width
        maxx += 2 * self.border_width
        maxy += 2 * self.border_width

        # Set menu dimensions and center
        self.center_x = -minx
        self.center_y = maxy
        self.width = maxx - minx
        self.height = maxy - miny

        # Position title
        self.title_x = self.center_x - self.title_width // 2 + 1
        if self.title_font:
            self.title_y = 2 * self.border_width + self.title_font.get_height() // 2 + 1
        else:
            self.title_y = 2 * self.border_width + 12  # Default height

        # Convert to X coordinate system (flip Y)
        for entry in self.entries:
            entry.y = (self.center_y - entry.y) - entry.height
            entry.label_y = (self.center_y - entry.label_y) - entry.height
            entry.x += self.center_x
            entry.label_x += self.center_x

    def _calculate_bounds(self):
        """Calculate the overall menu bounds."""
        if not self.entries:
            return

        minx = min(entry.x for entry in self.entries)
        miny = min(entry.y for entry in self.entries)
        maxx = max(entry.x + entry.width for entry in self.entries)
        maxy = max(entry.y + entry.height for entry in self.entries)

        if self.title:
            minx = min(minx, self.title_x)
            maxx = max(maxx, self.title_x + self.title_width)
            maxy = max(maxy, self.title_y + self.title_height)

        self.width = maxx - minx + 4 * self.border_width
        self.height = maxy - miny + 4 * self.border_width
        self.center_x = -minx + 2 * self.border_width
        self.center_y = maxy + 2 * self.border_width

    def render(self, surface: pygame.Surface, x: int, y: int):
        """Render the pie menu at the given position."""
        if not self.surface or self.surface.get_size() != (self.width, self.height):
            self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        self.surface.fill((0, 0, 0, 0))  # Clear with transparency

        # Draw title if present
        if self.title and self.title_font:
            title_surface = self.title_font.render(self.title, True, self.fg_color)
            self.surface.blit(title_surface, (self.title_x, self.title_y))

        # Draw pie spokes (simplified)
        if len(self.entries) > 1:
            center = (self.center_x, self.center_y)
            angle = deg_to_rad(self.initial_angle) - (self.entries[0].subtend / 2.0)

            for entry in self.entries:
                end_x = self.center_x + math.cos(angle) * (self.label_radius - PIE_SPOKE_INSET)
                end_y = self.center_y - math.sin(angle) * (self.label_radius - PIE_SPOKE_INSET)
                pygame.draw.line(self.surface, self.fg_color,
                               center, (end_x, end_y), 1)
                angle += entry.subtend

        # Draw entries
        for i, entry in enumerate(self.entries):
            # Draw entry background
            color = self.active_bg_color if i == self.active else self.bg_color
            pygame.draw.rect(self.surface, color,
                           (entry.x, entry.y, entry.width, entry.height))

            # Draw entry border
            border_color = self.active_fg_color if i == self.active else self.fg_color
            pygame.draw.rect(self.surface, border_color,
                           (entry.x, entry.y, entry.width, entry.height), 1)

            # Draw label or bitmap
            if entry.bitmap:
                self.surface.blit(entry.bitmap, (entry.label_x, entry.label_y))
            elif entry.label and self.font:
                text_surface = self.font.render(entry.label, True, self.fg_color)
                self.surface.blit(text_surface, (entry.label_x, entry.label_y))

        # Draw outer border
        pygame.draw.rect(self.surface, self.fg_color,
                        (0, 0, self.width, self.height), self.border_width)

        # Blit to target surface
        surface.blit(self.surface, (x - self.center_x, y - self.center_y))

    def activate_entry(self, index: int, preview: bool = True) -> bool:
        """Activate the specified entry."""
        if index < -1 or index >= len(self.entries):
            return False

        self.active = index

        # Handle preview commands
        if preview and index >= 0:
            entry = self.entries[index]
            if entry.preview:
                # Execute preview command (would integrate with TCL interpreter)
                pass

        return True

    def invoke_entry(self, index: int) -> bool:
        """Invoke the command for the specified entry."""
        if index < 0 or index >= len(self.entries):
            return False

        entry = self.entries[index]
        if entry.command:
            # Execute command (would integrate with TCL interpreter)
            print(f"Invoking command: {entry.command}")
            return True

        return False

    def get_distance(self) -> int:
        """Get distance from cursor to menu center."""
        return int(math.sqrt(self.last_cursor_dx * self.last_cursor_dx + 
                           self.last_cursor_dy * self.last_cursor_dy) + 0.5)

    def get_direction(self) -> int:
        """Get direction from menu center to cursor in degrees."""
        direction = int(rad_to_deg(math.atan2(self.last_cursor_dy, self.last_cursor_dx)) + 0.5)
        if direction < 0:
            direction += 360
        return direction


# TCL Command Interface (stub for now)
class PieMenuCommand:
    """TCL command interface for pie menus."""

    def __init__(self, menu: PieMenu):
        self.menu = menu

    def handle_command(self, command: str, *args) -> str:
        """Handle TCL commands for the pie menu."""
        if command == "add":
            if len(args) < 1:
                raise ValueError("Usage: add <type> ?options?")
            entry_type = EntryType.COMMAND if args[0] == "command" else EntryType.PIEMENU
            
            # Parse options
            label = ""
            command_str = ""
            name = ""
            i = 1
            while i < len(args):
                if args[i] == "-label" and i + 1 < len(args):
                    label = args[i + 1]
                    i += 2
                elif args[i] == "-command" and i + 1 < len(args):
                    command_str = args[i + 1]
                    i += 2
                elif args[i] == "-name" and i + 1 < len(args):
                    name = args[i + 1]
                    i += 2
                else:
                    i += 1
            
            self.menu.add_entry(entry_type, label=label, command=command_str, name=name)
            return ""

        elif command == "activate":
            if len(args) != 1:
                raise ValueError("Usage: activate <index>")
            index = int(args[0])
            self.menu.activate_entry(index)
            return ""

        elif command == "invoke":
            if len(args) != 1:
                raise ValueError("Usage: invoke <index>")
            index = int(args[0])
            self.menu.invoke_entry(index)
            return ""

        elif command == "distance":
            return str(self.menu.get_distance())

        elif command == "direction":
            return str(self.menu.get_direction())

        else:
            raise ValueError(f"Unknown command: {command}")


def create_pie_menu(title: str = "", **kwargs) -> PieMenu:
    """Create a new pie menu."""
    return PieMenu(title=title, **kwargs)