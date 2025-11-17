"""Unit tests for the animation utilities in micropolis.animations.

These tests expect an autouse fixture named `context` (AppContext) to be
provided by tests/conftest.py which also sets up a pygame display surface.

They also rely on `micropolis.constants` for tile constants.
"""

from micropolis import animations
from micropolis import constants

from tests.assertions import Assertions


class TestAnimations(Assertions):
    """Test cases for the tile animation system."""

    def setUp(self):
        # Initialize a fresh map for each test on the AppContext
        context.map_data = [
            [0 for _ in range(constants.WORLD_Y)] for _ in range(constants.WORLD_X)
        ]

    def test_animate_tiles_no_animated_tiles(self):
        """animate_tiles should leave a non-animated world unchanged."""
        for x in range(constants.WORLD_X):
            for y in range(constants.WORLD_Y):
                context.map_data[x][y] = 100

        original_map = [row[:] for row in context.map_data]
        animations.animate_tiles(context)

        self.assertEqual(context.map_data, original_map)

    def test_animate_tiles_fire_animation(self):
        """Fire tile should advance one frame while preserving ANIMBIT."""
        tx, ty = 10, 20
        context.map_data[tx][ty] = 56 | constants.ANIMBIT

        animations.animate_tiles(context)

        self.assertEqual(context.map_data[tx][ty], 57 | constants.ANIMBIT)

    def test_count_animated_tiles_and_positions(self):
        """count_animated_tiles and get_animated_tile_positions should agree."""
        context.map_data[0][0] = 56 | constants.ANIMBIT
        context.map_data[5][5] = 56 | constants.ANIMBIT
        context.map_data[10][10] = 100

        count = animations.count_animated_tiles(context)
        positions = animations.get_animated_tile_positions(context)

        self.assertEqual(count, 2)
        self.assertIn((0, 0), positions)
        self.assertIn((5, 5), positions)

    def test_get_animation_info_non_animated(self):
        context.map_data[5][5] = 100
        self.assertIsNone(animations.get_animation_info(context, 5, 5))

    def test_get_animation_info_animated(self):
        tile_value = 56 | constants.ANIMBIT | constants.PWRBIT
        context.map_data[5][5] = tile_value

        info = animations.get_animation_info(context, 5, 5)

        self.assertIsNotNone(info)
        self.assertEqual(info["position"], (5, 5))
        self.assertEqual(info["tile_value"], tile_value)
        self.assertEqual(info["tile_index"], 56)
        self.assertEqual(info["tile_flags"], tile_value & constants.ALLBITS)
        self.assertTrue(info["is_animated"])

    def test_animate_tiles_preserve_flags(self):
        flags = (
            constants.ANIMBIT | constants.PWRBIT | constants.CONDBIT | constants.BURNBIT
        )
        context.map_data[5][5] = 56 | flags

        animations.animate_tiles(context)

        res = context.map_data[5][5]
        self.assertEqual(res & constants.ANIMBIT, constants.ANIMBIT)
        self.assertEqual(res & constants.PWRBIT, constants.PWRBIT)
        self.assertEqual(res & constants.CONDBIT, constants.CONDBIT)
        self.assertEqual(res & constants.BURNBIT, constants.BURNBIT)
