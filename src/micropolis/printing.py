"""
printing.py - Print functionality for Micropolis

This module provides stub implementations for printing functionality
from the original Micropolis. The original w_print.c contained incomplete
implementations for printing map areas, but this has been replaced with
modern alternatives.

The original system included:
- PrintRect: Print a rectangular area of the map
- PrintTile: Print individual tiles
- PrintHeader/PrintTrailer: Print formatting functions

Since printing functionality is rarely needed in modern applications
and the original implementation was incomplete, this provides stub
implementations that maintain API compatibility.

Adapted from w_print.c for the Python/pygame port.
"""


import pygame


# ============================================================================
# Constants (from original C code)
# ============================================================================

TILE_COUNT = 960  # From sim.h


# ============================================================================
# Global State
# ============================================================================

# Print output destination (could be file, stdout, etc.)
_print_output: str | None = None
_print_file: str | None = None


# ============================================================================
# Print Functions (Stub Implementations)
# ============================================================================

def PrintRect(x: int, y: int, w: int, h: int) -> None:
    """
    Print a rectangular area of the map.

    This function was intended to print a rectangular section of the city map,
    including tile counts and the actual tile layout. In the original C code,
    this would generate text output suitable for printing.

    Args:
        x, y: Top-left coordinates of the rectangle
        w, h: Width and height of the rectangle
    """
    # Stub implementation - in a full implementation, this would:
    # 1. Count occurrences of each tile type in the rectangle
    # 2. Print a header with dimensions
    # 3. Print tile definitions for used tiles
    # 4. Print the actual tile grid

    PrintHeader(x, y, w, h)

    # Count tile occurrences (stub - would analyze actual map data)
    tally = [0] * TILE_COUNT

    # Simulate counting tiles in the rectangle
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            # In real implementation: tile = Map[xx][yy] & LOMASK
            tile = 0  # Stub: assume empty tiles
            if 0 <= tile < TILE_COUNT:
                tally[tile] += 1

    # Print tile definitions for used tiles
    for tile_id in range(TILE_COUNT):
        if tally[tile_id] > 0:
            PrintDefTile(tile_id)

    # Print the tile grid
    FirstRow()
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            # In real implementation: tile = Map[xx][yy] & LOMASK
            tile = 0  # Stub: assume empty tiles
            PrintTile(tile)
        PrintNextRow()

    PrintFinish(x, y, w, h)
    PrintTrailer(x, y, w, h)


def PrintHeader(x: int, y: int, w: int, h: int) -> None:
    """
    Print header information for a map rectangle.

    Args:
        x, y: Top-left coordinates
        w, h: Width and height
    """
    _print(f"Map Rectangle: ({x}, {y}) to ({x+w-1}, {y+h-1}) - Size: {w}x{h}")


def PrintDefTile(tile: int) -> None:
    """
    Print tile definition.

    Args:
        tile: Tile ID to define
    """
    # Stub: In a full implementation, this would print tile name/description
    tile_names = {
        0: "Empty",
        1: "Dirt",
        2: "River",
        # ... would include all tile type names
    }
    name = tile_names.get(tile, f"Tile_{tile}")
    _print(f"Tile {tile}: {name}")


def FirstRow() -> None:
    """
    Start printing the first row of tiles.
    """
    _print("Map Data:")


def PrintTile(tile: int) -> None:
    """
    Print a single tile.

    Args:
        tile: Tile ID to print
    """
    # Stub: Print tile as a character representation
    # In a full implementation, this might use ASCII art or symbols
    tile_chars = {
        0: ".",  # Empty
        1: "#",  # Dirt/building
        2: "~",  # Water
        # ... more tile representations
    }
    char = tile_chars.get(tile, "?")
    _print(char, end="")


def PrintNextRow() -> None:
    """
    Move to the next row in printing.
    """
    _print()  # New line


def PrintFinish(x: int, y: int, w: int, h: int) -> None:
    """
    Finish printing the map rectangle.

    Args:
        x, y: Top-left coordinates
        w, h: Width and height
    """
    _print(f"End of map rectangle ({w}x{h} tiles)")


def PrintTrailer(x: int, y: int, w: int, h: int) -> None:
    """
    Print trailer information.

    Args:
        x, y: Top-left coordinates
        w, h: Width and height
    """
    _print(f"Printed rectangle at ({x}, {y}) dimensions {w}x{h}")


# ============================================================================
# Modern Print Alternatives
# ============================================================================

def print_map_to_file(filename: str, x: int = 0, y: int = 0,
                     w: int = 120, h: int = 100) -> bool:
    """
    Print map to a file (modern alternative).

    Args:
        filename: Output filename
        x, y: Top-left coordinates (default: entire map)
        w, h: Width and height (default: entire map)

    Returns:
        True if successful, False otherwise
    """
    global _print_file
    try:
        _print_file = filename
        with open(filename, 'w') as f:
            # Redirect print output to file
            global _print_output
            _print_output = ""
            PrintRect(x, y, w, h)

            # Write accumulated output to file
            f.write(_print_output)

        _print_file = None
        _print_output = None
        return True
    except Exception:
        _print_file = None
        _print_output = None
        return False


def print_map_to_console(x: int = 0, y: int = 0,
                        w: int = 120, h: int = 100) -> None:
    """
    Print map to console (modern alternative).

    Args:
        x, y: Top-left coordinates (default: entire map)
        w, h: Width and height (default: entire map)
    """
    global _print_output
    _print_output = None  # Reset to use stdout
    PrintRect(x, y, w, h)


def print_map_to_surface(surface: pygame.Surface, x: int = 0, y: int = 0,
                        w: int = 120, h: int = 100) -> None:
    """
    Render map to pygame surface (modern alternative).

    Args:
        surface: Pygame surface to render to
        x, y: Top-left coordinates
        w, h: Width and height
    """
    # Stub: In a full implementation, this would render the map
    # visually to a pygame surface instead of text printing
    # For now, just fill with a placeholder color
    surface.fill((200, 200, 200))  # Light gray background


# ============================================================================
# Internal Helper Functions
# ============================================================================

def _print(text: str = "", end: str = "\n") -> None:
    """
    Internal print function that can redirect output.

    Args:
        text: Text to print
        end: End character (default: newline)
    """
    global _print_output, _print_file

    if _print_file:
        # Accumulate output for file writing
        if _print_output is None:
            _print_output = ""
        _print_output += text + end

        # Immediately write to file if it's a direct print call
        try:
            with open(_print_file, 'a') as f:
                f.write(text + end)
        except Exception:
            pass  # Ignore file write errors in stub implementation
    else:
        # Print to stdout
        print(text, end=end)


# ============================================================================
# Configuration Functions
# ============================================================================

def set_print_destination(filename: str | None) -> None:
    """
    Set the print output destination.

    Args:
        filename: Filename to print to, or None for stdout
    """
    global _print_file
    _print_file = filename


def get_print_destination() -> str | None:
    """
    Get the current print destination.

    Returns:
        Current print filename, or None for stdout
    """
    return _print_file


# ============================================================================
# Initialization and Cleanup
# ============================================================================

def initialize_printing() -> None:
    """
    Initialize the printing system.
    Called during program startup.
    """
    global _print_output, _print_file
    _print_output = None
    _print_file = None


def cleanup_printing() -> None:
    """
    Clean up the printing system.
    Called during program shutdown.
    """
    global _print_output, _print_file
    _print_output = None
    _print_file = None