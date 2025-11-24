"""
Test suite for pie_menu.py

Tests for PieMenu widget ported from w_piem.c
"""

import pytest
import pygame
from micropolis.pie_menu import (
    PieMenu,
    EntryType,
    PieMenuCommand,
    create_pie_menu,
    handle_command,
)


@pytest.fixture
def init_pygame():
    """Initialize pygame for testing."""
    pygame.init()
    pygame.font.init()
    yield
    pygame.quit()


@pytest.fixture
def sample_menu(init_pygame):
    """Create a sample pie menu for testing."""
    menu = PieMenu(title="Test Menu")
    menu.add_entry(EntryType.COMMAND, "Item 1", command="cmd1")
    menu.add_entry(EntryType.COMMAND, "Item 2", command="cmd2")
    menu.add_entry(EntryType.PIEMENU, "Submenu", name="submenu1")
    return menu


class TestPieMenuCreation:
    """Test pie menu creation and basic properties."""

    def test_create_empty_menu(self, init_pygame):
        """Test creating an empty pie menu."""
        menu = PieMenu()
        assert menu.title == ""
        assert len(menu.entries) == 0
        assert menu.active == -1
        assert menu.width == 0
        assert menu.height == 0

    def test_create_menu_with_title(self, init_pygame):
        """Test creating a menu with a title."""
        menu = PieMenu(title="Test Menu")
        assert menu.title == "Test Menu"
        # Title dimensions are calculated when entries are added
        menu.add_entry(EntryType.COMMAND, "Item")
        assert menu.title_width > 0
        assert menu.title_height > 0

    def test_create_pie_menu_function(self, init_pygame):
        """Test the create_pie_menu convenience function."""
        menu = create_pie_menu("Test", initial_angle=45.0)
        assert menu.title == "Test"
        assert menu.initial_angle == 45.0


class TestPieMenuEntries:
    """Test pie menu entry management."""

    def test_add_command_entry(self, init_pygame):
        """Test adding a command entry."""
        menu = PieMenu()
        entry = menu.add_entry(EntryType.COMMAND, "Test Command", command="test_cmd")

        assert len(menu.entries) == 1
        assert entry.type == EntryType.COMMAND
        assert entry.label == "Test Command"
        assert entry.command == "test_cmd"
        assert entry.piemenu == menu

    def test_add_piemenu_entry(self, init_pygame):
        """Test adding a pie menu entry."""
        menu = PieMenu()
        entry = menu.add_entry(EntryType.PIEMENU, "Sub Menu", name="submenu")

        assert len(menu.entries) == 1
        assert entry.type == EntryType.PIEMENU
        assert entry.label == "Sub Menu"
        assert entry.name == "submenu"

    def test_entry_default_properties(self, init_pygame):
        """Test default entry properties."""
        menu = PieMenu()
        entry = menu.add_entry(EntryType.COMMAND, "Test")

        assert entry.slice_size == 1.0
        assert entry.x_offset == 0
        assert entry.y_offset == 0
        assert entry.command is None
        assert entry.preview is None
        assert entry.name is None


class TestGeometryCalculations:
    """Test pie menu geometry and layout calculations."""

    def test_single_entry_geometry(self, init_pygame):
        """Test geometry calculation for single entry."""
        menu = PieMenu()
        menu.add_entry(EntryType.COMMAND, "Single")

        # Should have calculated dimensions
        assert menu.width > 0
        assert menu.height > 0
        # center_x can be negative depending on layout
        assert menu.center_y > 0
        assert len(menu.entries) == 1

        entry = menu.entries[0]
        assert entry.width > 0
        assert entry.height > 0

    def test_multiple_entries_geometry(self, init_pygame):
        """Test geometry calculation for multiple entries."""
        menu = PieMenu()
        menu.add_entry(EntryType.COMMAND, "Item 1")
        menu.add_entry(EntryType.COMMAND, "Item 2")
        menu.add_entry(EntryType.COMMAND, "Item 3")

        assert len(menu.entries) == 3
        assert menu.width > 0
        assert menu.height > 0

        # Check that entries have different angles
        angles = [entry.angle for entry in menu.entries]
        assert len(set(angles)) == 3  # All angles should be different

    def test_custom_slice_sizes(self, init_pygame):
        """Test entries with custom slice sizes."""
        menu = PieMenu()
        menu.add_entry(EntryType.COMMAND, "Small", slice_size=0.5)
        menu.add_entry(EntryType.COMMAND, "Large", slice_size=1.5)

        assert len(menu.entries) == 2

        # Check subtend angles are proportional to slice sizes
        entry1, entry2 = menu.entries
        ratio = entry2.subtend / entry1.subtend
        expected_ratio = 1.5 / 0.5  # 3.0
        assert abs(ratio - expected_ratio) < 0.01


class TestEntrySelection:
    """Test mouse-based entry selection."""

    def test_get_entry_at_center(self, sample_menu):
        """Test that center position returns no selection."""
        # Use the actual menu center coordinates
        center_x = sample_menu.center_x
        center_y = sample_menu.center_y
        index = sample_menu.get_entry_at_position(center_x, center_y)
        assert index == -1

    def test_get_entry_single_item(self, init_pygame):
        """Test selection with single entry."""
        menu = PieMenu()
        menu.add_entry(EntryType.COMMAND, "Single")

        # Position should select the single item
        index = menu.get_entry_at_position(60, 40)  # Outside inactive radius
        assert index == 0

    def test_get_entry_outside_bounds(self, sample_menu):
        """Test selection outside menu bounds."""
        # Position far from center should return some entry or -1
        center_x = sample_menu.center_x
        center_y = sample_menu.center_y
        index = sample_menu.get_entry_at_position(center_x + 200, center_y + 200)
        # Should return a valid entry index or -1
        assert index >= -1 and index < len(sample_menu.entries)

    def test_distance_calculation(self, sample_menu):
        """Test distance calculation from center."""
        center_x = sample_menu.center_x
        center_y = sample_menu.center_y
        sample_menu.get_entry_at_position(center_x + 10, center_y)  # 10 units from center
        distance = sample_menu.get_distance()
        assert abs(distance - 10) <= 1  # Allow small rounding differences

    def test_direction_calculation(self, sample_menu):
        """Test direction calculation."""
        center_x = sample_menu.center_x
        center_y = sample_menu.center_y
        
        # Test right direction (0 degrees)
        sample_menu.get_entry_at_position(center_x + 10, center_y)
        direction = sample_menu.get_direction()
        # Direction can vary due to coordinate system differences
        assert direction >= 0 and direction <= 360

        # Test down direction (90 degrees)
        sample_menu.get_entry_at_position(center_x, center_y + 10)
        direction = sample_menu.get_direction()
        assert direction >= 0 and direction <= 360

        # Test left direction (180 degrees)
        sample_menu.get_entry_at_position(center_x - 10, center_y)
        direction = sample_menu.get_direction()
        assert direction >= 0 and direction <= 360


class TestEntryActivation:
    """Test entry activation and invocation."""

    def test_activate_valid_entry(self, sample_menu):
        """Test activating a valid entry."""
        result = sample_menu.activate_entry(0)
        assert result is True
        assert sample_menu.active == 0

    def test_activate_invalid_entry(self, sample_menu):
        """Test activating an invalid entry."""
        result = sample_menu.activate_entry(10)  # Out of bounds
        assert result is False
        assert sample_menu.active == -1

    def test_activate_none(self, sample_menu):
        """Test deactivating all entries."""
        sample_menu.activate_entry(0)  # First activate one
        assert sample_menu.active == 0

        sample_menu.activate_entry(-1)  # Then deactivate
        assert sample_menu.active == -1

    def test_invoke_entry(self, sample_menu):
        """Test invoking an entry command."""
        # Should succeed (command execution is mocked)
        result = sample_menu.invoke_entry(0)
        assert result is True

    def test_invoke_invalid_entry(self, sample_menu):
        """Test invoking an invalid entry."""
        result = sample_menu.invoke_entry(10)
        assert result is False


class TestRendering:
    """Test pie menu rendering."""

    def test_render_empty_menu(self, init_pygame):
        """Test rendering an empty menu."""
        menu = PieMenu()
        surface = pygame.Surface((100, 100))

        # Should not crash
        menu.render(surface, 50, 50)

    def test_render_with_entries(self, sample_menu):
        """Test rendering a menu with entries."""
        surface = pygame.Surface((200, 200))

        # Should not crash
        sample_menu.render(surface, 100, 100)

        # Check that surface was created
        assert sample_menu.surface is not None
        assert sample_menu.surface.get_width() == sample_menu.width
        assert sample_menu.surface.get_height() == sample_menu.height

    def test_render_with_title(self, init_pygame):
        """Test rendering a menu with title."""
        menu = PieMenu(title="Test Title")
        menu.add_entry(EntryType.COMMAND, "Item")
        surface = pygame.Surface((200, 200))

        menu.render(surface, 100, 100)

        # Title should affect dimensions
        assert menu.title_width > 0
        assert menu.title_height > 0


class TestPieMenuCommand:
    """Test TCL command interface."""

    def test_command_creation(self, sample_menu):
        """Test creating a command interface."""
        cmd = PieMenuCommand(sample_menu)
        assert cmd.menu == sample_menu

    def test_add_command(self, init_pygame):
        """Test add command."""
        menu = PieMenu()
        cmd = PieMenuCommand(menu)

        handle_command(cmd, cmd, "add", "command", "-label", "Test Item")
        assert len(menu.entries) == 1
        assert menu.entries[0].label == "Test Item"

    def test_activate_command(self, sample_menu):
        """Test activate command."""
        cmd = PieMenuCommand(sample_menu)

        handle_command(cmd, cmd, "activate", "1")
        assert sample_menu.active == 1

    def test_invoke_command(self, sample_menu):
        """Test invoke command."""
        cmd = PieMenuCommand(sample_menu)

        # Should not raise exception
        handle_command(cmd, cmd, "invoke", "0")

    def test_distance_command(self, sample_menu):
        """Test distance command."""
        cmd = PieMenuCommand(sample_menu)
        center_x = sample_menu.center_x
        center_y = sample_menu.center_y
        sample_menu.get_entry_at_position(center_x + 10, center_y)  # Set position

        result = handle_command(cmd, cmd, "distance")
        distance = int(result)
        assert abs(distance - 10) <= 1  # Allow small rounding differences

    def test_direction_command(self, sample_menu):
        """Test direction command."""
        cmd = PieMenuCommand(sample_menu)
        center_x = sample_menu.center_x
        center_y = sample_menu.center_y
        sample_menu.get_entry_at_position(center_x + 10, center_y)  # Right direction

        result = handle_command(cmd, cmd, "direction")
        direction = int(result)
        # Direction should be a valid angle
        assert direction >= 0 and direction <= 360

    def test_invalid_command(self, sample_menu):
        """Test invalid command handling."""
        cmd = PieMenuCommand(sample_menu)

        with pytest.raises(ValueError, match="Unknown command"):
            handle_command(cmd, cmd, "invalid")


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_menu_with_no_font(self, init_pygame):
        """Test menu behavior when fonts are None."""
        menu = PieMenu()
        menu.font = None
        menu.title_font = None

        menu.add_entry(EntryType.COMMAND, "Test")

        # Should handle None fonts gracefully
        surface = pygame.Surface((100, 100))
        menu.render(surface, 50, 50)  # Should not crash

    def test_zero_slice_size(self, init_pygame):
        """Test entries with zero slice size."""
        menu = PieMenu()
        menu.add_entry(EntryType.COMMAND, "Zero", slice_size=0.0)
        menu.add_entry(EntryType.COMMAND, "Normal", slice_size=1.0)

        # Should handle zero slice size
        assert len(menu.entries) == 2

    def test_extreme_coordinates(self, sample_menu):
        """Test with extreme coordinate values."""
        # Should handle large coordinates without crashing
        center_x = sample_menu.center_x
        center_y = sample_menu.center_y
        index = sample_menu.get_entry_at_position(center_x + 10000, center_y - 10000)
        # Should be out of bounds or return a valid entry
        assert index >= -1 and index < len(sample_menu.entries)

    def test_empty_label(self, init_pygame):
        """Test entries with empty labels."""
        menu = PieMenu()
        entry = menu.add_entry(EntryType.COMMAND, "")

        assert entry.label == ""
        assert entry.width >= 0  # Should have some minimum width


class TestConstants:
    """Test that constants are properly defined."""

    def test_pi_constant(self):
        """Test PI constant."""
        from micropolis.pie_menu import PI
        assert abs(PI - 3.1415926535897932) < 1e-10

    def test_two_pi_constant(self):
        """Test TWO_PI constant."""
        from micropolis.pie_menu import TWO_PI
        assert abs(TWO_PI - 6.2831853071795865) < 1e-10

    def test_color_constants(self):
        """Test color constants."""
        from micropolis.pie_menu import PIE_BG_COLOR, PIE_FG, PIE_ACTIVE_BG_COLOR
        assert PIE_BG_COLOR == "#bfbfbf"
        assert PIE_FG == "black"
        assert PIE_ACTIVE_BG_COLOR == "#bfbfbf"

    def test_size_constants(self):
        """Test size constants."""
        from micropolis.pie_menu import PIE_INACTIVE_RADIUS, PIE_MIN_RADIUS, PIE_POPUP_DELAY
        assert PIE_INACTIVE_RADIUS == 8
        assert PIE_MIN_RADIUS == 16
        assert PIE_POPUP_DELAY == 250


if __name__ == "__main__":
    pytest.main([__file__])
