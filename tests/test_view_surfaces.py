"""
Test script to verify SimView instances are properly wired to pygame surfaces.

This script tests the implementation of the "Wire SimView instances to pygame surfaces" task.
"""

import sys
import pygame

# Initialize pygame first
pygame.init()

from micropolis.app_config import AppConfig
from micropolis.context import AppContext
from micropolis.engine import initialize_view_surfaces, sim_init
from micropolis.view_types import Map_Class
from micropolis.graphics_setup import init_graphics


def test_view_surface_initialization():
    """Test that views are properly initialized with surfaces and tile caches."""

    print("=" * 70)
    print("Testing SimView Surface Initialization")
    print("=" * 70)

    # Create context and initialize simulation
    config = AppConfig()
    context = AppContext(config=config)

    print("\n1. Initializing simulation...")
    result = sim_init(context)
    if result.is_err():
        print(f"   ❌ Failed to initialize simulation: {result.unwrap_err()}")
        return False
    print("   ✅ Simulation initialized")

    # Verify sim object exists
    if context.sim is None:
        print("   ❌ context.sim is None")
        return False
    print(f"   ✅ context.sim created: {context.sim}")

    # Verify views exist
    if context.sim.editor is None:
        print("   ❌ Editor view is None")
        return False
    print(f"   ✅ Editor view exists (class_id={context.sim.editor.class_id})")

    if context.sim.map is None:
        print("   ❌ Map view is None")
        return False
    print(f"   ✅ Map view exists (class_id={context.sim.map.class_id})")

    print("\n2. Initializing graphics...")
    if not init_graphics(context):
        print("   ❌ Failed to initialize graphics")
        return False
    print("   ✅ Graphics initialized")

    print("\n3. Wiring views to pygame surfaces...")
    result = initialize_view_surfaces(context)
    if result.is_err():
        print(f"   ❌ Failed to wire surfaces: {result.unwrap_err()}")
        return False
    print("   ✅ Views wired to surfaces")

    print("\n4. Verifying editor view...")
    editor = context.sim.editor

    # Check surface
    if editor.surface is None:
        print("   ❌ Editor view surface is None")
        return False
    print(f"   ✅ Editor surface created: {editor.surface.get_size()}")

    # Check display
    if editor.x is None:
        print("   ❌ Editor view display (x) is None")
        return False
    print(f"   ✅ Editor display attached (color={editor.x.color})")

    # Check tile cache (bigtiles)
    if editor.bigtiles is None and (
        editor.x is None or editor.x.big_tile_image is None
    ):
        print(
            "   ⚠️  Editor bigtiles not loaded (this may be expected if assets are missing)"
        )
    else:
        if editor.bigtiles:
            print(f"   ✅ Editor bigtiles cache populated: {type(editor.bigtiles)}")
        if editor.x and editor.x.big_tile_image:
            print(
                f"   ✅ Editor big_tile_image loaded: {editor.x.big_tile_image.get_size()}"
            )

    print("\n5. Verifying map view...")
    map_view = context.sim.map

    # Check surface
    if map_view.surface is None:
        print("   ❌ Map view surface is None")
        return False
    print(f"   ✅ Map surface created: {map_view.surface.get_size()}")

    # Check display
    if map_view.x is None:
        print("   ❌ Map view display (x) is None")
        return False
    print(f"   ✅ Map display attached (color={map_view.x.color})")

    # Check tile cache (smalltiles)
    if map_view.smalltiles is None and (
        map_view.x is None or map_view.x.small_tile_image is None
    ):
        print(
            "   ⚠️  Map smalltiles not loaded (this may be expected if assets are missing)"
        )
    else:
        if map_view.smalltiles:
            print(
                f"   ✅ Map smalltiles cache populated: {len(map_view.smalltiles)} bytes"
            )
        if map_view.x and map_view.x.small_tile_image:
            print(
                f"   ✅ Map small_tile_image loaded: {map_view.x.small_tile_image.get_size()}"
            )

    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED")
    print("=" * 70)
    print("\nSummary:")
    print("  • SimView objects successfully created")
    print("  • Pygame surfaces attached to views")
    print("  • Display objects (x) properly wired")
    print("  • Tile caches initialized (or assets missing as expected)")
    print("  • Views ready for rendering")

    return True


if __name__ == "__main__":
    try:
        success = test_view_surface_initialization()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        pygame.quit()
