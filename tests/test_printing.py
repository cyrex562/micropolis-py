"""
test_printing.py - Tests for printing functionality

Tests the printing system stub implementations.
These tests ensure that the printing functions work correctly
and maintain API compatibility with the original C code.
"""

import os
import tempfile
import pytest
import pygame

from src.micropolis import printing


class TestPrintFunctions:
    """Test basic print functions."""

    def test_print_header(self):
        """Test printing header."""
        # Capture output by redirecting to file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            temp_filename = f.name
            f.close()  # Close the file so printing can open it

            try:
                printing.set_print_destination(temp_filename)
                printing.PrintHeader(10, 20, 30, 40)

                # Read back the output
                with open(temp_filename, 'r') as rf:
                    content = rf.read()
                    assert "Map Rectangle: (10, 20) to (39, 59)" in content
                    assert "Size: 30x40" in content
            finally:
                printing.set_print_destination(None)
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)

    def test_print_def_tile(self):
        """Test printing tile definition."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            temp_filename = f.name
            f.close()

            try:
                printing.set_print_destination(temp_filename)
                printing.PrintDefTile(0)
                printing.PrintDefTile(2)
                printing.PrintDefTile(999)  # Unknown tile

                with open(temp_filename, 'r') as rf:
                    content = rf.read()
                    assert "Tile 0: Empty" in content
                    assert "Tile 2: River" in content
                    assert "Tile_999" in content
            finally:
                printing.set_print_destination(None)
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)

    def test_print_tile(self):
        """Test printing individual tiles."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            temp_filename = f.name
            f.close()

            try:
                printing.set_print_destination(temp_filename)
                printing.PrintTile(0)  # Empty
                printing.PrintTile(1)  # Dirt
                printing.PrintTile(2)  # Water
                printing.PrintTile(999)  # Unknown

                with open(temp_filename, 'r') as rf:
                    content = rf.read()
                    assert "." in content  # Empty
                    assert "#" in content  # Dirt
                    assert "~" in content  # Water
                    assert "?" in content  # Unknown
            finally:
                printing.set_print_destination(None)
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)

    def test_first_row_and_next_row(self):
        """Test row printing functions."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            temp_filename = f.name
            f.close()

            try:
                printing.set_print_destination(temp_filename)
                printing.FirstRow()
                printing.PrintTile(0)
                printing.PrintTile(1)
                printing.PrintNextRow()
                printing.PrintTile(2)
                printing.PrintNextRow()

                with open(temp_filename, 'r') as rf:
                    content = rf.read()
                    lines = content.strip().split('\n')
                    assert "Map Data:" in lines[0]
                    assert ".#" in lines[1]  # First row
                    assert "~" in lines[2]   # Second row
            finally:
                printing.set_print_destination(None)
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)

    def test_print_finish_and_trailer(self):
        """Test finish and trailer printing."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            temp_filename = f.name
            f.close()

            try:
                printing.set_print_destination(temp_filename)
                printing.PrintFinish(5, 10, 15, 20)
                printing.PrintTrailer(5, 10, 15, 20)

                with open(temp_filename, 'r') as rf:
                    content = rf.read()
                    assert "End of map rectangle (15x20 tiles)" in content
                    assert "Printed rectangle at (5, 10) dimensions 15x20" in content
            finally:
                printing.set_print_destination(None)
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)


class TestPrintRect:
    """Test PrintRect function."""

    def test_print_rect_small(self):
        """Test printing a small rectangle."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            temp_filename = f.name
            f.close()

            try:
                printing.set_print_destination(temp_filename)
                printing.PrintRect(0, 0, 2, 2)

                with open(temp_filename, 'r') as rf:
                    content = rf.read()
                    # Should contain header, tile definitions, and grid
                    assert "Map Rectangle:" in content
                    assert "Map Data:" in content
                    assert "End of map rectangle" in content
            finally:
                printing.set_print_destination(None)
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)

    def test_print_rect_console(self):
        """Test printing rectangle to console (no file redirection)."""
        # This should not crash
        printing.set_print_destination(None)
        printing.PrintRect(0, 0, 1, 1)


class TestModernAlternatives:
    """Test modern printing alternatives."""

    def test_print_map_to_file(self):
        """Test printing map to file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.close()  # Close so printing can open it

            try:
                result = printing.print_map_to_file(f.name, 0, 0, 3, 3)
                assert result is True

                # Check that file was created and has content
                with open(f.name, 'r') as rf:
                    content = rf.read()
                    assert len(content) > 0
                    assert "Map Rectangle:" in content
            finally:
                if os.path.exists(f.name):
                    os.unlink(f.name)

    def test_print_map_to_file_failure(self):
        """Test printing to invalid file."""
        # Try to print to a directory (should fail)
        with tempfile.TemporaryDirectory() as tmpdir:
            result = printing.print_map_to_file(tmpdir)
            assert result is False

    def test_print_map_to_console(self):
        """Test printing map to console."""
        # This should not crash
        printing.print_map_to_console(0, 0, 2, 2)

    def test_print_map_to_surface(self):
        """Test printing map to pygame surface."""
        surface = pygame.Surface((100, 100))
        initial_color = surface.get_at((50, 50))

        printing.print_map_to_surface(surface, 0, 0, 10, 10)

        # Surface should have been modified (filled with light gray)
        new_color = surface.get_at((50, 50))
        assert new_color != initial_color


class TestConfiguration:
    """Test configuration functions."""

    def test_set_get_print_destination(self):
        """Test setting and getting print destination."""
        # Initially None
        assert printing.get_print_destination() is None

        # Set a filename
        printing.set_print_destination("test.txt")
        assert printing.get_print_destination() == "test.txt"

        # Reset to None
        printing.set_print_destination(None)
        assert printing.get_print_destination() is None


class TestSystemLifecycle:
    """Test system initialization and cleanup."""

    def test_initialize_printing(self):
        """Test initializing printing system."""
        printing.initialize_printing()
        assert printing.get_print_destination() is None

    def test_cleanup_printing(self):
        """Test cleaning up printing system."""
        printing.set_print_destination("test.txt")
        printing.cleanup_printing()
        assert printing.get_print_destination() is None


class TestConstants:
    """Test constants."""

    def test_tile_count(self):
        """Test TILE_COUNT constant."""
        assert printing.TILE_COUNT == 960


class TestInternalFunctions:
    """Test internal helper functions."""

    def test_private_print_to_file(self):
        """Test internal _print function with file output."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            temp_filename = f.name
            f.close()

            try:
                printing.set_print_destination(temp_filename)
                printing._print("Hello")
                printing._print("World", end="")
                printing._print("!")

                with open(temp_filename, 'r') as rf:
                    content = rf.read()
                    assert content == "Hello\nWorld!\n"
            finally:
                printing.set_print_destination(None)
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)

    def test_private_print_to_stdout(self, capsys):
        """Test internal _print function to stdout."""
        printing.set_print_destination(None)
        printing._print("Test output")
        printing._print("No newline", end="")
        printing._print("!")

        captured = capsys.readouterr()
        assert captured.out == "Test output\nNo newline!\n"


if __name__ == "__main__":
    pytest.main([__file__])