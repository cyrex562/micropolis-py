"""
graphics_setup.py - Graphics initialization for Micropolis Python port

This module handles loading of graphics assets and initialization of display
structures, adapted from g_setup.c for pygame instead of X11/TCL-Tk.
"""

import os
from typing import List, Optional, Any

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    pygame = None

from . import types, view_types


# ============================================================================
# Graphics Constants (from g_setup.c)
# ============================================================================

# Tile constants
SIM_SMTILE = 385
SIM_BWTILE = 386
SIM_GSMTILE = 388
SIM_LGTILE = 544

# Stipple pattern dimensions
STIPPLE_WIDTH = 16
STIPPLE_HEIGHT = 16

# Stipple pattern bitmaps (from g_setup.c)
GRAY25_BITS = bytes([
    0x77, 0x77,
    0xdd, 0xdd,
    0x77, 0x77,
    0xdd, 0xdd,
    0x77, 0x77,
    0xdd, 0xdd,
    0x77, 0x77,
    0xdd, 0xdd,
    0x77, 0x77,
    0xdd, 0xdd,
    0x77, 0x77,
    0xdd, 0xdd,
    0x77, 0x77,
    0xdd, 0xdd,
    0x77, 0x77,
    0xdd, 0xdd,
])

GRAY50_BITS = bytes([
    0x55, 0x55,
    0xaa, 0xaa,
    0x55, 0x55,
    0xaa, 0xaa,
    0x55, 0x55,
    0xaa, 0xaa,
    0x55, 0x55,
    0xaa, 0xaa,
    0x55, 0x55,
    0xaa, 0xaa,
    0x55, 0x55,
    0xaa, 0xaa,
    0x55, 0x55,
    0xaa, 0xaa,
    0x55, 0x55,
    0xaa, 0xaa,
])

GRAY75_BITS = bytes([
    0x88, 0x88,
    0x22, 0x22,
    0x88, 0x88,
    0x22, 0x22,
    0x88, 0x88,
    0x22, 0x22,
    0x88, 0x88,
    0x22, 0x22,
    0x88, 0x88,
    0x22, 0x22,
    0x88, 0x88,
    0x22, 0x22,
    0x88, 0x88,
    0x22, 0x22,
    0x88, 0x88,
    0x22, 0x22,
])

VERT_BITS = bytes([
    0xaa, 0xaa,
    0xaa, 0xaa,
    0xaa, 0xaa,
    0xaa, 0xaa,
    0xaa, 0xaa,
    0xaa, 0xaa,
    0xaa, 0xaa,
    0xaa, 0xaa,
    0xaa, 0xaa,
    0xaa, 0xaa,
    0xaa, 0xaa,
    0xaa, 0xaa,
    0xaa, 0xaa,
    0xaa, 0xaa,
    0xaa, 0xaa,
    0xaa, 0xaa,
])

HORIZ_BITS = bytes([
    0xff, 0xff,
    0x00, 0x00,
    0xff, 0xff,
    0x00, 0x00,
    0xff, 0xff,
    0x00, 0x00,
    0xff, 0xff,
    0x00, 0x00,
    0xff, 0xff,
    0x00, 0x00,
    0xff, 0xff,
    0x00, 0x00,
    0xff, 0xff,
    0x00, 0x00,
    0xff, 0xff,
    0x00, 0x00,
])

DIAG_BITS = bytes([
    0x55, 0x55,
    0xee, 0xee,
    0x55, 0x55,
    0xba, 0xbb,
    0x55, 0x55,
    0xee, 0xee,
    0x55, 0x55,
    0xba, 0xbb,
    0x55, 0x55,
    0xee, 0xee,
    0x55, 0x55,
    0xba, 0xbb,
    0x55, 0x55,
    0xee, 0xee,
    0x55, 0x55,
    0xba, 0xbb,
])


# ============================================================================
# Graphics Loading Functions
# ============================================================================

def get_resource_path(filename: str) -> str:
    """
    Get the full path to a resource file.

    Args:
        filename: Name of the resource file

    Returns:
        Full path to the resource file
    """
    # Try multiple possible locations for resources based on new assets/ structure
    possible_paths = [
        # New assets/ directory structure
        os.path.join(os.path.dirname(__file__), '..', '..', 'assets', filename),  # hexa.*, snro.*, stri.*, tcl files
        os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'images', filename),  # XPM and image files
        os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'sounds', filename),  # audio files
        os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'dejavu-lgc', filename),  # fonts
        
        # Legacy paths for backward compatibility
        os.path.join(os.path.dirname(__file__), '..', '..', 'images', filename),
        os.path.join(os.path.dirname(__file__), '..', '..', 'res', filename),
        os.path.join(os.getcwd(), 'images', filename),
        os.path.join(os.getcwd(), 'res', filename),
        filename  # Try current directory as fallback
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return filename  # Return as-is if not found


def load_xpm_surface(filename: str) -> Optional[Any]:
    """
    Load an XPM file as a pygame surface.

    Args:
        filename: Name of the XPM file to load

    Returns:
        pygame Surface if successful, None if failed
    """
    if not PYGAME_AVAILABLE or pygame is None:
        print(f"Warning: pygame not available, cannot load {filename}")
        return None

    try:
        filepath = get_resource_path(filename)
        surface = pygame.image.load(filepath)
        return surface
    except (pygame.error, FileNotFoundError) as e:
        print(f"Warning: Failed to load XPM file {filename}: {e}")
        return None


def load_hexa_resource(resource_id: int) -> Optional[bytes]:
    """
    Load a hexa resource file.

    Ported from MickGetHexa() in g_setup.c.

    Args:
        resource_id: The resource ID (e.g., SIM_GSMTILE = 388)

    Returns:
        Raw bytes from the hexa file, or None if failed
    """
    filename = f"hexa.{resource_id}"
    filepath = get_resource_path(filename)

    try:
        with open(filepath, 'rb') as f:
            return f.read()
    except (FileNotFoundError, IOError) as e:
        print(f"Warning: Failed to load hexa resource {resource_id}: {e}")
        return None


def create_small_tiles_surface() -> Optional[Any]:
    """
    Create a pygame surface for small tiles (map view) from hexa resource.

    Ported from the monochrome small tiles loading in GetViewTiles().

    Returns:
        pygame Surface containing small tile data, or None if failed
    """
    if not PYGAME_AVAILABLE or pygame is None:
        return None

    # Load the hexa resource for small tiles
    hexa_data = load_hexa_resource(SIM_GSMTILE)
    if hexa_data is None:
        return None

    # The hexa data is 4 pixels wide × 3 pixels high × TILE_COUNT tiles
    # We need to convert this to 4×4 pixels per tile with padding
    expected_size = 4 * 3 * types.TILE_COUNT  # 11520
    if len(hexa_data) < expected_size:
        print(f"Warning: Hexa data too small {len(hexa_data)}, expected at least {expected_size}")
        return None

    # Use only the expected amount of data, ignore any extra
    actual_data = hexa_data[:expected_size]

    try:
        # Create surface for 4×4 tiles: TILE_COUNT tiles × 4×4 pixels × 4 bytes per pixel (RGBA)
        surface_width = 4  # 4 pixels per tile
        surface_height = 4 * types.TILE_COUNT  # 4 pixels high per tile × TILE_COUNT tiles

        surface = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)

        # Process each tile
        data_index = 0
        for tile in range(types.TILE_COUNT):
            # Read 3 rows of 4 pixels each from hexa data
            for y in range(3):
                for x in range(4):
                    if data_index < len(actual_data):
                        pixel_value = actual_data[data_index]
                        # Convert grayscale to RGBA
                        color = (pixel_value, pixel_value, pixel_value, 255)
                        surface.set_at((x, tile * 4 + y), color)
                        data_index += 1

            # Add padding row (4th row is transparent)
            for x in range(4):
                surface.set_at((x, tile * 4 + 3), (0, 0, 0, 0))

        return surface

    except Exception as e:
        print(f"Error creating small tiles surface: {e}")
        return None


def load_big_tiles_surface(color: bool = True) -> Optional[Any]:
    """
    Load big tiles surface for editor view.

    This would normally load from tiles.xpm or tilesbw.xpm, but since we don't have
    those files, we'll create a placeholder surface for now.

    Args:
        color: Whether to load color or monochrome tiles

    Returns:
        pygame Surface for big tiles, or None if failed
    """
    if not PYGAME_AVAILABLE or pygame is None:
        return None

    try:
        # For now, create a placeholder surface
        # Big tiles are 16×16 pixels per tile
        tiles_per_row = 16  # Assume tiles are arranged in a grid
        rows = (types.TILE_COUNT + tiles_per_row - 1) // tiles_per_row

        surface_width = tiles_per_row * 16
        surface_height = rows * 16

        surface = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)

        # Fill with a placeholder pattern (checkerboard)
        for tile_y in range(rows):
            for tile_x in range(tiles_per_row):
                tile_index = tile_y * tiles_per_row + tile_x
                if tile_index >= types.TILE_COUNT:
                    break

                # Create a simple colored rectangle for each tile
                color_value = (tile_index * 7) % 256  # Vary color based on tile index
                tile_color = (color_value, (color_value + 85) % 256, (color_value + 170) % 256, 255)

                pygame.draw.rect(surface, tile_color,
                               (tile_x * 16, tile_y * 16, 16, 16))

        return surface

    except Exception as e:
        print(f"Error creating big tiles surface: {e}")
        return None


def create_stipple_surface(bits: bytes, width: int = STIPPLE_WIDTH,
                          height: int = STIPPLE_HEIGHT) -> Optional[Any]:
    """
    Create a pygame surface from stipple pattern bits.

    Args:
        bits: Bitmap data as bytes
        width: Width of the stipple pattern
        height: Height of the stipple pattern

    Returns:
        pygame Surface with the stipple pattern
    """
    if not PYGAME_AVAILABLE or pygame is None:
        return None

    try:
        # Create a surface for the stipple pattern
        surface = pygame.Surface((width, height), pygame.SRCALPHA)

        # Convert bitmap data to surface pixels
        # Each byte represents 8 pixels (1 bit per pixel)
        for y in range(height):
            for x in range(0, width, 8):
                if y * (width // 8) + (x // 8) < len(bits):
                    byte_val = bits[y * (width // 8) + (x // 8)]
                    for bit in range(8):
                        if x + bit < width:
                            pixel_value = 255 if (byte_val & (1 << (7 - bit))) else 0
                            surface.set_at((x + bit, y), (pixel_value, pixel_value, pixel_value, 255))

        return surface
    except Exception as e:
        print(f"Warning: Failed to create stipple surface: {e}")
        return None


def get_object_surfaces(object_id: int, frames: int) -> Optional[List[Any]]:
    """
    Load object sprite surfaces for a given object type.

    Ported from GetObjectXpms() in g_setup.c.

    Args:
        object_id: Object type ID (TRA, COP, AIR, etc.)
        frames: Number of animation frames

    Returns:
        List of pygame surfaces for the object, or None if failed
    """
    if not PYGAME_AVAILABLE:
        return None

    surfaces = []

    # Map object IDs to filename patterns
    object_names = {
        types.TRA: "obj1",  # Train
        types.COP: "obj2",  # Police helicopter
        types.AIR: "obj3",  # Airplanes
        types.SHI: "obj4",  # Ships
        types.GOD: "obj5",  # God
        types.TOR: "obj6",  # Tornado
        types.EXP: "obj7",  # Explosion
        types.BUS: "obj8",  # Bus
    }

    if object_id not in object_names:
        print(f"Warning: Unknown object ID {object_id}")
        return None

    base_name = object_names[object_id]

    for frame in range(frames):
        filename = f"{base_name}-{frame}.xpm"
        surface = load_xpm_surface(filename)
        if surface is None:
            print(f"Warning: Failed to load object {base_name} frame {frame}")
            return None
        surfaces.append(surface)

    return surfaces


def get_pixmaps(display: view_types.XDisplay) -> None:
    """
    Initialize pixmaps and stipple patterns for the display.

    Ported from GetPixmaps() in g_setup.c.

    Args:
        display: XDisplay structure to initialize
    """
    if not PYGAME_AVAILABLE:
        print("Warning: pygame not available, skipping pixmap initialization")
        return

    # Create stipple patterns if not already created
    if display.gray25_stipple is None:
        display.gray25_stipple = create_stipple_surface(GRAY25_BITS)
        display.gray50_stipple = create_stipple_surface(GRAY50_BITS)
        display.gray75_stipple = create_stipple_surface(GRAY75_BITS)
        display.vert_stipple = create_stipple_surface(VERT_BITS)
        display.horiz_stipple = create_stipple_surface(HORIZ_BITS)
        display.diag_stipple = create_stipple_surface(DIAG_BITS)

    # Load object sprites if not already loaded
    if display.objects is None:
        display.objects = []  # Initialize as empty list
        for _ in range(types.OBJN):
            display.objects.append(None)  # Add None for each object slot

        # Load sprites for each object type with their frame counts
        object_frames = {
            types.TRA: 5,  # Train: 5 frames
            types.COP: 8,  # Police helicopter: 8 frames
            types.AIR: 11, # Airplanes: 11 frames
            types.SHI: 8,  # Ships: 8 frames
            types.GOD: 16, # God: 16 frames
            types.TOR: 3,  # Tornado: 3 frames
            types.EXP: 6,  # Explosion: 6 frames
            types.BUS: 4,  # Bus: 4 frames
        }

        for obj_id, frames in object_frames.items():
            surfaces = get_object_surfaces(obj_id, frames)
            if surfaces is not None:
                display.objects[obj_id] = surfaces
            else:
                print(f"Warning: Failed to load sprites for object {obj_id}")


def get_view_tiles(view: Any) -> None:
    """
    Load tile graphics for a view.

    Ported from GetViewTiles() in g_setup.c.

    Args:
        view: View structure to initialize with tiles
    """
    if not PYGAME_AVAILABLE:
        print("Warning: pygame not available, skipping tile loading")
        return

    # Determine if this is an editor or map view
    is_editor = view_types.IsEditorView(view)
    is_map = view_types.IsMapView(view)

    if is_editor:
        # Load tiles for editor view (16x16 pixels per tile)
        if view.type == view_types.X_Mem_View:
            if view.x.big_tile_image is None:
                # Try to load from XPM first, then fall back to generated surface
                tiles_filename = "tiles.xpm" if view.x.color else "tilesbw.xpm"
                view.x.big_tile_image = load_xpm_surface(tiles_filename)

                if view.x.big_tile_image is None:
                    # Fall back to generated placeholder surface
                    view.x.big_tile_image = load_big_tiles_surface(view.x.color)

                if view.x.big_tile_image is None:
                    print("Error: Failed to load big tile image")
                    return

            # Extract tile data from the surface
            view.bigtiles = view.x.big_tile_image

        elif view.type == view_types.X_Wire_View:
            if view.x.big_tile_pixmap is None:
                tiles_filename = "tiles.xpm" if view.x.color else "tilesbw.xpm"
                view.x.big_tile_pixmap = load_xpm_surface(tiles_filename)

                if view.x.big_tile_pixmap is None:
                    # Fall back to generated placeholder surface
                    view.x.big_tile_pixmap = load_big_tiles_surface(view.x.color)

                if view.x.big_tile_pixmap is None:
                    print("Error: Failed to load big tile pixmap")
                    return

    elif is_map:
        # Load tiles for map view (3x3 pixels per tile, expanded to 4x4)
        if view.x.small_tile_image is None:
            if view.x.color:
                # Try to load color tiles from XPM
                tiles_filename = "tilessm.xpm"
                view.x.small_tile_image = load_xpm_surface(tiles_filename)

                if view.x.small_tile_image is None:
                    print(f"Warning: Failed to load small tile image {tiles_filename}, using placeholder")
                    # For now, create a placeholder - we don't have the actual small tile graphics
                    view.x.small_tile_image = pygame.Surface((4, 3 * types.TILE_COUNT), pygame.SRCALPHA)

            else:
                # For monochrome, load from hexa resource
                hexa_data = load_hexa_resource(SIM_GSMTILE)
                if hexa_data is not None:
                    # Create XImage-like structure from hexa data
                    # This mimics the XCreateImage call in the C code
                    view.x.small_tile_image = pygame.Surface((4, 3 * types.TILE_COUNT), pygame.SRCALPHA)

                    # Fill surface with hexa data (grayscale)
                    for i, pixel_value in enumerate(hexa_data):
                        x = i % 4
                        y = i // 4
                        if y < 3 * types.TILE_COUNT:
                            color = (pixel_value, pixel_value, pixel_value, 255)
                            view.x.small_tile_image.set_at((x, y), color)
                else:
                    print("Warning: Failed to load monochrome small tiles")
                    return

        # Process the small tile data into 4x4 format
        if view.smalltiles is None:
            # Convert 4x3 tiles to 4x4 tiles with padding (matching C code logic)
            pixel_bytes = 4  # RGBA
            source_surface = view.x.small_tile_image

            # Allocate space for 4x4 tiles
            view.smalltiles = bytearray(4 * 4 * types.TILE_COUNT * pixel_bytes)

            to_index = 0
            for tile in range(types.TILE_COUNT):
                # Copy 3 rows of 4 pixels each
                for y in range(3):
                    for x in range(4):
                        if source_surface is not None:
                            color = source_surface.get_at((x, tile * 3 + y))
                            # Store as RGBA bytes
                            view.smalltiles[to_index] = color[0]  # R
                            view.smalltiles[to_index + 1] = color[1]  # G
                            view.smalltiles[to_index + 2] = color[2]  # B
                            view.smalltiles[to_index + 3] = color[3]  # A
                        to_index += pixel_bytes

                # Add padding row (4th row is transparent)
                for x in range(4):
                    view.smalltiles[to_index] = 0  # R
                    view.smalltiles[to_index + 1] = 0  # G
                    view.smalltiles[to_index + 2] = 0  # B
                    view.smalltiles[to_index + 3] = 0  # A
                    to_index += pixel_bytes


# ============================================================================
# Initialization Functions
# ============================================================================

def init_graphics() -> bool:
    """
    Initialize the graphics system.

    Returns:
        True if initialization successful, False otherwise
    """
    if not PYGAME_AVAILABLE or pygame is None:
        print("Error: pygame not available for graphics initialization")
        return False

    try:
        # Initialize pygame if not already done
        if not pygame.get_init():
            pygame.init()

        # Get the main display
        if not hasattr(types, 'MainDisplay') or types.MainDisplay is None:
            types.MainDisplay = view_types.MakeNewXDisplay()

        # Initialize pixmaps for the main display
        get_pixmaps(types.MainDisplay)

        return True

    except Exception as e:
        print(f"Error initializing graphics: {e}")
        return False


def init_view_graphics(view: Any) -> bool:
    """
    Initialize graphics for a specific view.

    Args:
        view: View to initialize graphics for

    Returns:
        True if successful, False otherwise
    """
    if not PYGAME_AVAILABLE:
        return False

    try:
        # Ensure the view has a display
        if not hasattr(view, 'x') or view.x is None:
            print("Error: View has no display")
            return False

        # Load tiles for this view
        get_view_tiles(view)

        return True

    except Exception as e:
        print(f"Error initializing view graphics: {e}")
        return False


def cleanup_graphics() -> None:
    """
    Clean up graphics resources.
    """
    # This would free surfaces and other resources
    # For now, pygame cleanup is handled automatically
    pass


# ============================================================================
# Utility Functions
# ============================================================================

def get_tile_surface(tile_id: int, view: Any) -> Optional[Any]:
    """
    Get the surface for a specific tile.

    Args:
        tile_id: ID of the tile to get
        view: View containing the tile graphics

    Returns:
        pygame Surface for the tile, or None if not found
    """
    if not PYGAME_AVAILABLE or pygame is None:
        return None

    try:
        if view_types.IsEditorView(view) and hasattr(view, 'bigtiles'):
            # Extract 16x16 tile from the big tiles image
            tiles_per_row = view.bigtiles.get_width() // 16
            tile_x = (tile_id % tiles_per_row) * 16
            tile_y = (tile_id // tiles_per_row) * 16

            tile_surface = pygame.Surface((16, 16), pygame.SRCALPHA)
            tile_surface.blit(view.bigtiles, (0, 0), (tile_x, tile_y, 16, 16))
            return tile_surface

        elif view_types.IsMapView(view) and hasattr(view, 'smalltiles'):
            # Extract 4x4 tile from the small tiles image (3x3 pixels + 1 padding)
            tiles_per_row = view.smalltiles.get_width() // 4
            tile_x = (tile_id % tiles_per_row) * 4
            tile_y = (tile_id // tiles_per_row) * 4

            tile_surface = pygame.Surface((4, 4), pygame.SRCALPHA)
            tile_surface.blit(view.smalltiles, (0, 0), (tile_x, tile_y, 4, 4))
            return tile_surface

    except Exception as e:
        print(f"Error getting tile surface for tile {tile_id}: {e}")

    return None


def get_object_surface(object_id: int, frame: int = 0, display: Optional[view_types.XDisplay] = None) -> Optional[Any]:
    """
    Get the surface for a specific object sprite.

    Args:
        object_id: ID of the object
        frame: Animation frame number
        display: Display containing the object graphics

    Returns:
        pygame Surface for the object sprite, or None if not found
    """
    if display is None:
        display = types.MainDisplay

    if display is None or display.objects is None:
        return None

    try:
        if 0 < object_id < len(display.objects) and display.objects[object_id] is not None:
            frames = display.objects[object_id]
            if frames is not None and 0 <= frame < len(frames):
                return frames[frame]
    except (IndexError, TypeError):
        pass

    return None


# ============================================================================
# Validation Functions
# ============================================================================

def validate_graphics_setup() -> bool:
    """
    Validate that graphics have been properly initialized.

    Returns:
        True if graphics are properly set up, False otherwise
    """
    if not PYGAME_AVAILABLE:
        return False

    try:
        # Check main display
        if not hasattr(types, 'MainDisplay') or types.MainDisplay is None:
            return False

        display = types.MainDisplay

        # Check stipple patterns
        stipples = [
            display.gray25_stipple,
            display.gray50_stipple,
            display.gray75_stipple,
            display.vert_stipple,
            display.horiz_stipple,
            display.diag_stipple
        ]

        for stipple in stipples:
            if stipple is None:
                return False

        # Check object sprites (at least some should be loaded)
        if display.objects is None:
            return False

        # Check that at least one object has sprites loaded
        has_objects = any(obj is not None for obj in display.objects[1:] if obj is not None)
        if not has_objects:
            return False

        return True

    except (AttributeError, TypeError):
        return False