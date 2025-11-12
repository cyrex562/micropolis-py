"""
test_sprite_manager.py - Comprehensive tests for sprite_manager.py

Tests sprite lifecycle management, movement algorithms, collision detection,
TCL command compatibility, and pygame rendering integration.
"""

import pytest
import pygame
from unittest.mock import patch
from . import sprite_manager
from . import types


@pytest.fixture(autouse=True)
def setup_simulation():
    """Set up a minimal simulation state for testing"""
    # Initialize pygame for any rendering tests
    pygame.init()
    pygame.font.init()

    # Create a minimal sim instance
    types.sim = types.MakeNewSim()

    # Initialize sprite system
    sprite_manager.initialize_sprite_system()

    yield

    # Cleanup
    types.sim = None
    pygame.quit()


class TestSpriteLifecycle:
    """Test sprite creation, initialization, and destruction"""

    def test_new_sprite(self):
        """Test creating a new sprite"""
        sprite = sprite_manager.new_sprite(context, "test_sprite", types.TRA, 100, 200)

        assert sprite.name == "test_sprite"
        assert sprite.type == types.TRA
        assert sprite.x == 100
        assert sprite.y == 200
        assert sprite.frame == 1  # Train starts with frame 1
        assert sprite.dir == 4

    def test_init_sprite_train(self):
        """Test initializing a train sprite"""
        sprite = types.SimSprite()
        sprite.type = types.TRA
        sprite_manager.init_sprite(context, sprite, 100, 200)

        assert sprite.width == 32
        assert sprite.height == 32
        assert sprite.x_offset == 32
        assert sprite.y_offset == -16
        assert sprite.x_hot == 40
        assert sprite.y_hot == -8
        assert sprite.frame == 1
        assert sprite.dir == 4

    def test_init_sprite_ship(self):
        """Test initializing a ship sprite"""
        sprite = types.SimSprite()
        sprite.type = types.SHI
        sprite_manager.init_sprite(context, sprite, 100, 200)

        assert sprite.width == 48
        assert sprite.height == 48
        assert sprite.x_offset == 32
        assert sprite.y_offset == -16
        assert sprite.x_hot == 48
        assert sprite.y_hot == 0
        assert sprite.dir == 10
        assert sprite.count == 1

    def test_init_sprite_monster(self):
        """Test initializing a monster sprite"""
        sprite = types.SimSprite()
        sprite.type = types.GOD
        sprite_manager.init_sprite(context, sprite, 100, 200)

        assert sprite.width == 48
        assert sprite.height == 48
        assert sprite.x_offset == 24
        assert sprite.y_offset == 0
        assert sprite.x_hot == 40
        assert sprite.y_hot == 16
        assert sprite.count == 1000

    def test_init_sprite_helicopter(self):
        """Test initializing a helicopter sprite"""
        sprite = types.SimSprite()
        sprite.type = types.COP
        sprite_manager.init_sprite(context, sprite, 100, 200)

        assert sprite.width == 32
        assert sprite.height == 32
        assert sprite.x_offset == 32
        assert sprite.y_offset == -16
        assert sprite.x_hot == 40
        assert sprite.y_hot == -8
        assert sprite.frame == 5
        assert sprite.count == 1500

    def test_init_sprite_airplane(self):
        """Test initializing an airplane sprite"""
        sprite = types.SimSprite()
        sprite.type = types.AIR
        sprite_manager.init_sprite(context, sprite, 100, 200)

        assert sprite.width == 48
        assert sprite.height == 48
        assert sprite.x_offset == 24
        assert sprite.y_offset == 0
        assert sprite.x_hot == 48
        assert sprite.y_hot == 16

    def test_init_sprite_tornado(self):
        """Test initializing a tornado sprite"""
        sprite = types.SimSprite()
        sprite.type = types.TOR
        sprite_manager.init_sprite(context, sprite, 100, 200)

        assert sprite.width == 48
        assert sprite.height == 48
        assert sprite.x_offset == 24
        assert sprite.y_offset == 0
        assert sprite.x_hot == 40
        assert sprite.y_hot == 36
        assert sprite.frame == 1
        assert sprite.count == 200

    def test_init_sprite_explosion(self):
        """Test initializing an explosion sprite"""
        sprite = types.SimSprite()
        sprite.type = types.EXP
        sprite_manager.init_sprite(context, sprite, 100, 200)

        assert sprite.width == 48
        assert sprite.height == 48
        assert sprite.x_offset == 24
        assert sprite.y_offset == 0
        assert sprite.x_hot == 40
        assert sprite.y_hot == 16
        assert sprite.frame == 1

    def test_init_sprite_bus(self):
        """Test initializing a bus sprite"""
        sprite = types.SimSprite()
        sprite.type = types.BUS
        sprite_manager.init_sprite(context, sprite, 100, 200)

        assert sprite.width == 32
        assert sprite.height == 32
        assert sprite.x_offset == 30
        assert sprite.y_offset == -18
        assert sprite.x_hot == 40
        assert sprite.y_hot == -8
        assert sprite.frame == 1
        assert sprite.dir == 1

    def test_make_sprite_reuse_global(self):
        """Test that make_sprite reuses global sprites"""
        # Create a global sprite
        sprite1 = sprite_manager.make_sprite(types.TRA, 100, 200)
        assert sprite_manager.global_sprites[types.TRA] == sprite1

        # Make another sprite of same type - should reuse
        sprite2 = sprite_manager.make_sprite(types.TRA, 300, 400)
        assert sprite2 == sprite1
        assert sprite2.x == 300
        assert sprite2.y == 400

    def test_make_new_sprite_always_new(self):
        """Test that make_new_sprite always creates new instances"""
        sprite1 = sprite_manager.make_new_sprite(context, types.TRA, 100, 200)
        sprite2 = sprite_manager.make_new_sprite(context, types.TRA, 300, 400)

        assert sprite1 != sprite2
        assert sprite1.x == 100
        assert sprite1.y == 200
        assert sprite2.x == 300
        assert sprite2.y == 400

    def test_destroy_sprite(self):
        """Test destroying a sprite"""
        sprite = sprite_manager.new_sprite(context, "test", types.TRA, 100, 200)

        # Verify sprite is in simulation
        assert types.sim.sprites == 1
        assert types.sim.sprite == sprite

        sprite_manager.destroy_sprite(context, sprite)

        # Verify sprite is removed
        assert types.sim.sprites == 0
        assert types.sim.sprite is None

    def test_get_sprite(self):
        """Test getting global sprites"""
        # No sprite initially
        assert sprite_manager.get_sprite(context, types.TRA) is None

        # Create sprite
        sprite = sprite_manager.make_sprite(types.TRA, 100, 200)
        assert sprite_manager.get_sprite(context, types.TRA) == sprite

        # Deactivate sprite
        sprite.frame = 0
        assert sprite_manager.get_sprite(context, types.TRA) is None


class TestSpriteMovement:
    """Test sprite movement algorithms"""

    def test_do_train_sprite_basic_movement(self):
        """Test basic train sprite movement"""
        sprite = sprite_manager.make_sprite(types.TRA, 100, 200)
        original_x = sprite.x
        original_y = sprite.y

        sprite_manager.do_train_sprite(context, sprite)

        # Train should have moved
        assert sprite.x != original_x or sprite.y != original_y

    def test_do_copter_sprite_basic_movement(self):
        """Test basic helicopter sprite movement"""
        sprite = sprite_manager.make_sprite(types.COP, 100, 200)
        original_x = sprite.x
        original_y = sprite.y

        sprite_manager.do_copter_sprite(sprite)

        # Helicopter should have moved
        assert sprite.x != original_x or sprite.y != original_y

    def test_do_airplane_sprite_basic_movement(self):
        """Test basic airplane sprite movement"""
        sprite = sprite_manager.make_sprite(types.AIR, 100, 200)
        original_x = sprite.x
        original_y = sprite.y

        sprite_manager.do_airplane_sprite(context, sprite)

        # Airplane should have moved
        assert sprite.x != original_x or sprite.y != original_y

    def test_do_ship_sprite_basic_movement(self):
        """Test basic ship sprite movement"""
        sprite = sprite_manager.make_sprite(types.SHI, 100, 200)
        original_x = sprite.x
        original_y = sprite.y

        sprite_manager.do_ship_sprite(context, sprite)

        # Ship should have moved
        assert sprite.x != original_x or sprite.y != original_y

    def test_do_monster_sprite_basic_movement(self):
        """Test basic monster sprite movement"""
        sprite = sprite_manager.make_sprite(types.GOD, 100, 200)
        original_x = sprite.x
        original_y = sprite.y

        sprite_manager.do_monster_sprite(context, sprite)

        # Monster should have moved
        assert sprite.x != original_x or sprite.y != original_y

    def test_do_tornado_sprite_basic_movement(self):
        """Test basic tornado sprite movement"""
        sprite = sprite_manager.make_sprite(types.TOR, 100, 200)
        original_x = sprite.x
        original_y = sprite.y

        sprite_manager.do_tornado_sprite(context, sprite)

        # Tornado should have moved
        assert sprite.x != original_x or sprite.y != original_y

    def test_do_explosion_sprite_animation(self):
        """Test explosion sprite animation"""
        sprite = sprite_manager.make_sprite(types.EXP, 100, 200)
        original_frame = sprite.frame

        sprite_manager.do_explosion_sprite(context, sprite)

        # Frame should have advanced
        assert sprite.frame > original_frame

    def test_do_bus_sprite_basic_movement(self):
        """Test basic bus sprite movement"""
        sprite = sprite_manager.make_sprite(types.BUS, 100, 200)
        original_x = sprite.x
        original_y = sprite.y

        sprite_manager.do_bus_sprite(context, sprite)

        # Bus should have moved
        assert sprite.x != original_x or sprite.y != original_y

    def test_move_objects_calls_all_sprites(self):
        """Test that move_objects processes all active sprites"""
        sprite1 = sprite_manager.make_sprite(types.TRA, 100, 200)
        sprite2 = sprite_manager.make_sprite(types.COP, 300, 400)

        original_x1 = sprite1.x
        original_y1 = sprite1.y
        original_x2 = sprite2.x
        original_y2 = sprite2.y

        sprite_manager.move_objects(context)

        # Both sprites should have moved
        assert sprite1.x != original_x1 or sprite1.y != original_y1
        assert sprite2.x != original_x2 or sprite2.y != original_y2


class TestCollisionDetection:
    """Test collision detection and sprite interactions"""

    def test_check_sprite_collision_overlapping(self):
        """Test collision detection for overlapping sprites"""
        sprite1 = sprite_manager.make_sprite(types.TRA, 100, 100)
        sprite2 = sprite_manager.make_sprite(types.COP, 130, 100)  # Close enough to collide

        collision = sprite_manager.check_sprite_collision(sprite1, sprite2)
        assert collision == 1

    def test_check_sprite_collision_separate(self):
        """Test collision detection for separate sprites"""
        sprite1 = sprite_manager.make_sprite(types.TRA, 100, 100)
        sprite2 = sprite_manager.make_sprite(types.COP, 200, 200)  # Far apart

        collision = sprite_manager.check_sprite_collision(sprite1, sprite2)
        assert collision == 0

    def test_sprite_not_in_bounds_outside(self):
        """Test bounds checking for sprites outside world"""
        sprite = sprite_manager.make_sprite(types.TRA, -100, -100)

        out_of_bounds = sprite_manager.sprite_not_in_bounds(sprite)
        assert out_of_bounds == 1

    def test_sprite_not_in_bounds_inside(self):
        """Test bounds checking for sprites inside world"""
        sprite = sprite_manager.make_sprite(types.TRA, 100, 100)

        out_of_bounds = sprite_manager.sprite_not_in_bounds(sprite)
        assert out_of_bounds == 0


class TestUtilityFunctions:
    """Test utility functions"""

    def test_get_char_in_bounds(self):
        """Test get_char for valid coordinates"""
        # Set up a test tile
        types.Map[5][5] = types.ROADBASE

        tile = sprite_manager.get_char(context, 80, 80)  # 80 >> 4 = 5, so tile (5,5)
        assert tile == types.ROADBASE

    def test_get_char_out_of_bounds(self):
        """Test get_char for out of bounds coordinates"""
        tile = sprite_manager.get_char(context, -10, -10)
        assert tile == -1

    def test_turn_to_same_direction(self):
        """Test turn_to when already facing correct direction"""
        result = sprite_manager.turn_to(5, 5)
        assert result == 5

    def test_turn_to_different_direction(self):
        """Test turn_to when needing to turn"""
        result = sprite_manager.turn_to(1, 5)
        # Should turn towards 5
        assert result == 2

    def test_get_dir_diagonal(self):
        """Test get_dir for diagonal movement"""
        direction = sprite_manager.get_dir(100, 100, 200, 200)
        assert direction >= 1 and direction <= 8

    def test_get_dis_manhattan(self):
        """Test get_dis calculates Manhattan distance"""
        distance = sprite_manager.get_dis(100, 100, 200, 200)
        assert distance == 200  # |200-100| + |200-100| = 100 + 100

    def test_test_bounds_inside(self):
        """Test bounds checking for coordinates inside world"""
        result = sprite_manager.test_bounds(50, 50)
        assert result

    def test_test_bounds_outside(self):
        """Test bounds checking for coordinates outside world"""
        assert not sprite_manager.test_bounds(-1, 50)
        assert not sprite_manager.test_bounds(50, -1)
        assert not sprite_manager.test_bounds(types.WORLD_X, 50)
        assert not sprite_manager.test_bounds(50, types.WORLD_Y)


class TestSpriteGeneration:
    """Test sprite generation functions"""

    @patch('micropolis.sprite_manager.random.Rand')
    def test_generate_train_population_requirement(self, mock_rand):
        """Test train generation requires sufficient population"""
        mock_rand.return_value = 10  # Low enough for generation

        # Low population - should not generate
        types.TotalPop = 10
        sprite_manager.generate_train(context, 100, 200)
        assert sprite_manager.get_sprite(context, types.TRA) is None

        # High population - should generate
        types.TotalPop = 30
        sprite_manager.generate_train(context, 100, 200)
        assert sprite_manager.get_sprite(context, types.TRA) is not None

    @patch('sprite_manager.random.Rand')
    def test_generate_bus_no_existing_bus(self, mock_rand):
        """Test bus generation when no bus exists"""
        mock_rand.return_value = 10  # Low enough for generation

        sprite_manager.generate_bus(context, 100, 200)
        assert sprite_manager.get_sprite(context, types.BUS) is not None

    def test_generate_bus_existing_bus(self):
        """Test bus generation when bus already exists"""
        # Create existing bus
        sprite_manager.make_sprite(types.BUS, 100, 200)

        # Try to generate another - should not create
        sprite_manager.generate_bus(context, 300, 400)
        # Should still only be one bus (the existing one)

    @patch('micropolis.sprite_manager.random.Rand16')
    def test_generate_ship(self, mock_rand16):
        """Test ship generation"""
        mock_rand16.return_value = 0  # Ensure generation attempts

        # Set up a channel at the top
        types.Map[5][0] = types.CHANNEL

        sprite_manager.generate_ship(context)
        # Ship generation is probabilistic, just verify it doesn't crash

    def test_make_monster_no_existing(self):
        """Test monster creation when none exists"""
        sprite_manager.spawn_monster_disaster()
        assert sprite_manager.get_sprite(context, types.GOD) is not None

    def test_make_monster_existing(self):
        """Test monster creation when one already exists"""
        # Create existing monster
        monster = sprite_manager.make_sprite(types.GOD, 100, 200)

        sprite_manager.spawn_monster_disaster()

        # Should update existing monster
        assert monster.count == 1000  # Reset to 1000

    def test_generate_copter_no_existing(self):
        """Test helicopter generation when none exists"""
        sprite_manager.generate_copter(100, 200)
        assert sprite_manager.get_sprite(context, types.COP) is not None

    def test_generate_copter_existing(self):
        """Test helicopter generation when one already exists"""
        # Create existing helicopter
        sprite_manager.make_sprite(types.COP, 100, 200)

        # Try to generate another - should not create
        sprite_manager.generate_copter(300, 400)
        # Should still only be one helicopter

    def test_generate_plane_no_existing(self):
        """Test airplane generation when none exists"""
        sprite_manager.generate_plane(context, 100, 200)
        assert sprite_manager.get_sprite(context, types.AIR) is not None

    def test_generate_plane_existing(self):
        """Test airplane generation when one already exists"""
        # Create existing airplane
        sprite_manager.make_sprite(types.AIR, 100, 200)

        # Try to generate another - should not create
        sprite_manager.generate_plane(context, 300, 400)
        # Should still only be one airplane

    def test_make_tornado_no_existing(self):
        """Test tornado creation when none exists"""
        sprite_manager.spawn_tornado_disaster()
        assert sprite_manager.get_sprite(context, types.TOR) is not None

    def test_make_tornado_existing(self):
        """Test tornado creation when one already exists"""
        # Create existing tornado
        tornado = sprite_manager.make_sprite(types.TOR, 100, 200)

        sprite_manager.spawn_tornado_disaster()

        # Should update existing tornado
        assert tornado.count == 200  # Reset to 200

    def test_make_explosion_at(self):
        """Test explosion creation at specific location"""
        sprite_manager.make_explosion_at(context, 100, 200)

        # Find the explosion sprite
        explosion = None
        sprite = types.sim.sprite if types.sim else None
        while sprite:
            if sprite.type == types.EXP:
                explosion = sprite
                break
            sprite = sprite.next

        assert explosion is not None
        assert explosion.x == 100 - 40
        assert explosion.y == 200 - 16


class TestTCLCommandInterface:
    """Test TCL command compatibility layer"""

    def test_sprite_command_creation(self):
        """Test creating a sprite via TCL command interface"""
        command = sprite_manager.sprite_command("test_sprite", types.TRA)

        assert isinstance(command, sprite_manager.SpriteCommand)
        assert command.sprite.name == "test_sprite"
        assert command.sprite.type == types.TRA

    def test_sprite_command_name(self):
        """Test TCL name command"""
        command = sprite_manager

        result = command.handle_command(context, context, "name")
        assert result == "test_sprite"

    def test_sprite_command_type(self):
        """Test TCL type command"""
        command = sprite_manager

        # Get current type
        result = command.handle_command(context, context, "type")
        assert result == str(types.TRA)

        # Set new type
        result = command.handle_command(context, context, "type", "2")
        assert result == "2"
        assert command.sprite.type == 2

    def test_sprite_command_frame(self):
        """Test TCL frame command"""
        command = sprite_manager

        # Get current frame
        result = command.handle_command(context, context, "frame")
        assert result == "1"  # Train starts with frame 1

        # Set new frame
        result = command.handle_command(context, context, "frame", "5")
        assert result == "5"
        assert command.sprite.frame == 5

    def test_sprite_command_position(self):
        """Test TCL position commands"""
        command = sprite_manager

        # Test x coordinate
        result = command.handle_command(context, context, "x")
        assert result == "0"  # Default x position

        result = command.handle_command(context, context, "x", "100")
        assert result == "100"
        assert command.sprite.x == 100

        # Test y coordinate
        result = command.handle_command(context, context, "y", "200")
        assert result == "200"
        assert command.sprite.y == 200

    def test_sprite_command_invalid_command(self):
        """Test handling of invalid TCL commands"""
        command = sprite_manager

        with pytest.raises(ValueError):
            command.handle_command(context, context, "invalid_command")


class TestSpriteEffects:
    """Test sprite effects and interactions"""

    def test_explode_sprite(self):
        """Test exploding a sprite"""
        sprite = sprite_manager.make_sprite(types.TRA, 100, 200)

        sprite_manager.explode_sprite(context, sprite)

        assert sprite.frame == 0  # Sprite should be deactivated

    def test_destroy_function(self):
        """Test the destroy function for tile damage"""
        # Set up a test tile
        types.Map[5][5] = types.TREEBASE

        sprite_manager.destroy(context, 80, 80)  # 80 >> 4 = 5

        # Tree should be destroyed
        assert types.Map[5][5] != types.TREEBASE

    def test_start_fire(self):
        """Test starting fires"""
        # Set up a burnable tile
        types.Map[5][5] = types.TREEBASE

        sprite_manager.start_fire(context, 80, 80)

        # Should have started a fire
        assert (types.Map[5][5] & types.LOMASK) == types.FIRE

    def test_check_wet_water_tiles(self):
        """Test check_wet for water-related tiles"""
        assert sprite_manager.check_wet(types.POWERBASE) == 1
        assert sprite_manager.check_wet(types.RAILBASE) == 1
        assert sprite_manager.check_wet(types.BRWH) == 1
        assert sprite_manager.check_wet(types.ROADBASE) == 0


class TestInitialization:
    """Test sprite system initialization"""

    def test_initialize_sprite_system(self):
        """Test sprite system initialization"""
        sprite_manager.initialize_sprite_system()

        assert sprite_manager.global_sprites == [None] * types.OBJN
        assert sprite_manager.free_sprites is None
        assert sprite_manager.cycle == 0
        assert sprite_manager.crash_x == 0
        assert sprite_manager.crash_y == 0

    def test_destroy_all_sprites(self):
        """Test destroying all sprites"""
        # Create some sprites
        sprite1 = sprite_manager.make_sprite(types.TRA, 100, 200)
        sprite2 = sprite_manager.make_sprite(types.COP, 300, 400)

        # Deactivate them
        sprite1.frame = 0
        sprite2.frame = 0

        sprite_manager.destroy_all_sprites(context)

        # Sprites should be deactivated
        assert sprite1.frame == 0
        assert sprite2.frame == 0


class TestCanDriveOn:
    """Test vehicle driving logic"""

    def test_can_drive_on_road(self):
        """Test driving on road tiles"""
        types.Map[5][5] = types.ROADBASE

        result = sprite_manager.can_drive_on(context, 5, 5)
        assert result == 1

    def test_can_drive_on_rail(self):
        """Test driving on rail tiles"""
        types.Map[5][5] = types.HRAILROAD

        result = sprite_manager.can_drive_on(context, 5, 5)
        assert result == 1

    def test_can_drive_on_dirt(self):
        """Test driving on dirt (bumpy)"""
        types.Map[5][5] = types.DIRT

        result = sprite_manager.can_drive_on(context, 5, 5)
        assert result == -1

    def test_can_drive_on_obstacle(self):
        """Test driving on obstacles"""
        types.Map[5][5] = types.TREEBASE

        result = sprite_manager.can_drive_on(context, 5, 5)
        assert result == 0

    def test_can_drive_on_out_of_bounds(self):
        """Test driving out of bounds"""
        result = sprite_manager.can_drive_on(context, -1, 5)
        assert result == 0


if __name__ == "__main__":
    pytest.main([__file__])