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

from src.micropolis.constants import TILE_COUNT
from src.micropolis.context import AppContext


# ============================================================================
# Print Functions (Stub Implementations)
# ============================================================================

def PrintRect(context: AppContext, x: int, y: int, w: int, h: int) -> None:
    """
    Print a rectangular area of the map.

    This function was intended to print a rectangular section of the city map,
    including tile counts and the actual tile layout. In the original C code,
    this would generate text output suitable for printing.

    Args:
        x, y: Top-left coordinates of the rectangle
        w, h: Width and height of the rectangle
        :param context:
    """
    # Stub implementation - in a full implementation, this would:
    # 1. Count occurrences of each tile type in the rectangle
    # 2. Print a header with dimensions
    # 3. Print tile definitions for used tiles
    # 4. Print the actual tile grid

    PrintHeader(context, x, y, w, h)

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
            PrintDefTile(context, tile_id)

    # Print the tile grid
    FirstRow(context)
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            # In real implementation: tile = Map[xx][yy] & LOMASK
            tile = 0  # Stub: assume empty tiles
            PrintTile(context, tile)
        PrintNextRow(context)

    PrintFinish(context, x, y, w, h)
    PrintTrailer(context, x, y, w, h)


def PrintHeader(context: AppContext, x: int, y: int, w: int, h: int) -> None:
    """
    Print header information for a map rectangle.

    Args:
        x, y: Top-left coordinates
        w, h: Width and height
        :param context:
    """
    _print(context, f"Map Rectangle: ({x}, {y}) to ({x + w - 1}, {y + h - 1}) - Size: {w}x{h}")


def PrintDefTile(context: AppContext, tile: int) -> None:
    """
    Print tile definition.

    Args:
        tile: Tile ID to define
        :param context:
    """
    # Stub: In a full implementation, this would print tile name/description
    tile_names = {
        0: "Empty",
        1: "Dirt",
        2: "River",
        # ... would include all tile type names
    }
    name = tile_names.get(tile, f"Tile_{tile}")
    _print(context, f"Tile {tile}: {name}")


def FirstRow(context: AppContext) -> None:
    """
    Start printing the first row of tiles.
    :param context:
    """
    _print(context, "Map Data:")


def PrintTile(context: AppContext, tile: int) -> None:
    """
    Print a single tile.

    Args:
        tile: Tile ID to print
        :param context:
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
    _print(context, char, end="")


def PrintNextRow(context: AppContext) -> None:
    """
    Move to the next row in printing.
    :param context:
    """
    _print(context)  # New line


def PrintFinish(context: AppContext, x: int, y: int, w: int, h: int) -> None:
    """
    Finish printing the map rectangle.

    Args:
        x, y: Top-left coordinates
        w, h: Width and height
        :param context:
    """
    _print(context, f"End of map rectangle ({w}x{h} tiles)")


def PrintTrailer(context: AppContext, x: int, y: int, w: int, h: int) -> None:
    """
    Print trailer information.

    Args:
        x, y: Top-left coordinates
        w, h: Width and height
        :param context:
    """
    _print(context, f"Printed rectangle at ({x}, {y}) dimensions {w}x{h}")


# ============================================================================
# Modern Print Alternatives
# ============================================================================

def print_map_to_file(context: AppContext, filename: str, x: int = 0, y: int = 0,
                     w: int = 120, h: int = 100) -> bool:
    """
    Print map to a file (modern alternative).

    Args:
        filename: Output filename
        x, y: Top-left coordinates (default: entire map)
        w, h: Width and height (default: entire map)

    Returns:
        True if successful, False otherwise
        :param context:
    """
    # global _print_file
    try:
        context.print_file = filename
        with open(filename, 'w') as f:
            # Redirect print output to file
            # global _print_output
            context.print_output = ""
            PrintRect(context, x, y, w, h)

            # Write accumulated output to file
            f.write(context.print_output)

        context.print_file = None
        context.print_output = None
        return True
    except Exception:
        context.print_file = None
        context.print_output = None
        return False


def print_map_to_console(context: AppContext, x: int = 0, y: int = 0,
                        w: int = 120, h: int = 100) -> None:
    """
    Print map to console (modern alternative).

    Args:
        x, y: Top-left coordinates (default: entire map)
        w, h: Width and height (default: entire map)
        :param context:
    """
    # global _print_output
    context.print_output = None  # Reset to use stdout
    PrintRect(context, x, y, w, h)


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

def _print(context: AppContext, text: str = "", end: str = "") -> None:
    """
    Internal print function that can redirect output.

    Args:
        text: Text to print
        end: End character (default: newline)
        :param context:
    """
    # global _print_output, _print_file

    if context.print_file:
        # Accumulate output for file writing
        if context.print_output is None:
            context.print_output = ""
        context.print_output += text + end

        # Immediately write to file if it's a direct print call
        try:
            with open(context.print_file, 'a') as f:
                f.write(text + end)
        except Exception:
            pass  # Ignore file write errors in stub implementation
    else:
        # Print to stdout
        print(text, end=end)


# ============================================================================
# Configuration Functions
# ============================================================================

def set_print_destination(context: AppContext, filename: str | None) -> None:
    """
    Set the print output destination.

    Args:
        filename: Filename to print to, or None for stdout
        :param context:
    """
    # global _print_file
    context.print_file = filename


def get_print_destination(context: AppContext) -> str | None:
    """
    Get the current print destination.

    Returns:
        Current print filename, or None for stdout
        :param context:
    """
    return context.print_file


# ============================================================================
# Initialization and Cleanup
# ============================================================================

def initialize_printing(context: AppContext) -> None:
    """
    Initialize the printing system.
    Called during program startup.
    :param context:
    """
    # global _print_output, _print_file
    context.print_output = None
    context.print_file = None


def cleanup_printing(context: AppContext) -> None:
    """
    Clean up the printing system.
    Called during program shutdown.
    :param context:
    """
    # global _print_output, _print_file
    context.print_output = None
    context.print_file = None