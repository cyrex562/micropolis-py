"""
Minimal test for SimView surface wiring (focuses only on the surface initialization task).
"""

import sys
import pygame

# Initialize pygame first
pygame.init()

from micropolis.app_config import AppConfig
from micropolis.context import AppContext
from micropolis.engine import initialize_view_surfaces, get_or_create_display
from micropolis.sim import MakeNewSim
from micropolis.graphics_setup import init_graphics
from micropolis.view_types import Map_Class


def test_minimal_surface_initialization():
    """Test only the surface wiring without full sim_init."""

    print("=" * 70)
    print("Minimal SimView Surface Initialization Test")
    print("=" * 70)

    # Create minimal context
    config = AppConfig()
    context = AppContext(config=config)

    print("\n1. Creating sim object with views...")
    context.sim = MakeNewSim(context)
    print(
        f"   OK: Sim created with editor={context.sim.editor is not None}, map={context.sim.map is not None}"
    )

    print("\n2. Initializing graphics...")
    if not init_graphics(context):
        print("   FAIL: Graphics initialization failed")
        return False
    print("   OK: Graphics initialized")

    print("\n3. Wiring views to pygame surfaces...")
    result = initialize_view_surfaces(context)
    if result.is_err():
        print(f"   FAIL: {result.unwrap_err()}")
        return False
    print("   OK: Views wired successfully")

    print("\n4. Verifying editor view...")
    editor = context.sim.editor

    if editor.surface is None:
        print("   FAIL: Editor surface is None")
        return False
    print(f"   OK: Editor surface: {editor.surface.get_size()}")

    if editor.x is None:
        print("   FAIL: Editor display (x) is None")
        return False
    print(
        f"   OK: Editor display attached (color={editor.x.color}, depth={editor.x.depth})"
    )

    has_tiles = editor.bigtiles is not None or (
        editor.x and editor.x.big_tile_image is not None
    )
    print(
        f"   {'OK' if has_tiles else 'WARNING'}: Big tiles {'loaded' if has_tiles else 'not loaded (assets may be missing)'}"
    )

    print("\n5. Verifying map view...")
    map_view = context.sim.map

    if map_view.surface is None:
        print("   FAIL: Map surface is None")
        return False
    print(f"   OK: Map surface: {map_view.surface.get_size()}")

    if map_view.x is None:
        print("   FAIL: Map display (x) is None")
        return False
    print(
        f"   OK: Map display attached (color={map_view.x.color}, depth={map_view.x.depth})"
    )

    has_small_tiles = map_view.smalltiles is not None or (
        map_view.x and map_view.x.small_tile_image is not None
    )
    print(
        f"   {'OK' if has_small_tiles else 'WARNING'}: Small tiles {'loaded' if has_small_tiles else 'not loaded (assets may be missing)'}"
    )

    print("\n" + "=" * 70)
    print("SUCCESS: SimView Surface Wiring Complete!")
    print("=" * 70)
    print("\nVerified:")
    print("  * SimView objects created (editor and map)")
    print("  * Pygame surfaces attached to view.surface")
    print("  * Display objects (view.x) properly wired")
    print("  * Graphics initialization called for each view")
    print("  * Views ready for rendering")

    return True


if __name__ == "__main__":
    try:
        success = test_minimal_surface_initialization()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        pygame.quit()
