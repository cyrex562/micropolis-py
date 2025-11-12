"""
sprite_manager.py - Sprite management system for Micropolis Python port

This module implements the sprite management system ported from w_sprite.c,
responsible for managing moving objects (cars, disasters, helicopters, etc.)
in the game world.
"""

from src.micropolis.constants import OBJN, TRA, SHI, WORLD_X, WORLD_Y, GOD, COP, AIR, TOR, EXP, BUS, RAILBASE, LASTRAIL, \
    RAILVPOWERH, RAILHPOWERV, RIVER, CHANNEL, POWERBASE, BRWH, BRWV, LOMASK, ROADBASE, LASTROAD, HRAILROAD, VRAILROAD, \
    DIRT, TRA_GROOVE_X, TRA_GROOVE_Y, BUS_GROOVE_X, BUS_GROOVE_Y, BULLBIT, TREEBASE, BURNBIT, ZONEBIT, RZB, SOMETINYEXP, \
    ANIMBIT, FIRE
from src.micropolis.context import AppContext
from src.micropolis.random import Rand, Rand16
from src.micropolis.sim_sprite import SimSprite
from src.micropolis.sim_view import SimView


# ============================================================================
# Constants
# ============================================================================





# ============================================================================
# Sprite Lifecycle Management
# ============================================================================


def new_sprite(context: AppContext,
    name: str, sprite_type: int, x: int = 0, y: int = 0
) -> SimSprite:
    """
    Create a new sprite.

    Args:
        name: Sprite name
        sprite_type: Sprite type (TRA, COP, etc.)
        x: Initial X position
        y: Initial Y position

    Returns:
        New SimSprite instance
        :param context: 
    """
    # global FreeSprites

    sprite: SimSprite | None = None

    if context.free_sprites:
        sprite = context.free_sprites
        context.free_sprites = sprite.next
    else:
        sprite = SimSprite()

    sprite.name = name
    sprite.type = sprite_type

    init_sprite(context, sprite, x, y)

    # Add to simulation sprite list
    if context.sim:
        context.sim.sprites += 1
        sprite.next = context.sim.sprite
        context.sim.sprite = sprite

    return sprite


def init_sprite(context: AppContext, sprite: SimSprite, x: int, y: int) -> None:
    """
    Initialize sprite with default values and type-specific settings.

    Args:
        sprite: Sprite to initialize
        x: Initial X position
        y: Initial Y position
        :param context:
    """
    sprite.x = x
    sprite.y = y
    sprite.frame = 0
    sprite.orig_x = 0
    sprite.orig_y = 0
    sprite.dest_x = 0
    sprite.dest_y = 0
    sprite.count = 0
    sprite.sound_count = 0
    sprite.dir = 0
    sprite.new_dir = 0
    sprite.step = 0
    sprite.flag = 0
    sprite.control = -1
    sprite.turn = 0
    sprite.accel = 0
    sprite.speed = 100

    # Set global sprite reference if none exists for this type
    if global_sprites[sprite.type] is None:
        global_sprites[sprite.type] = sprite

    # Type-specific initialization
    if sprite.type == TRA:  # Train
        sprite.width = 32
        sprite.height = 32
        sprite.x_offset = 32
        sprite.y_offset = -16
        sprite.x_hot = 40
        sprite.y_hot = -8
        sprite.frame = 1
        sprite.dir = 4

    elif sprite.type == SHI:  # Ship
        sprite.width = 48
        sprite.height = 48
        sprite.x_offset = 32
        sprite.y_offset = -16
        sprite.x_hot = 48
        sprite.y_hot = 0
        if x < (4 << 4):
            sprite.frame = 3
        elif x >= ((WORLD_X - 4) << 4):
            sprite.frame = 7
        elif y < (4 << 4):
            sprite.frame = 5
        elif y >= ((WORLD_Y - 4) << 4):
            sprite.frame = 1
        else:
            sprite.frame = 3
        sprite.new_dir = sprite.frame
        sprite.dir = 10
        sprite.count = 1

    elif sprite.type == GOD:  # Monster
        sprite.width = 48
        sprite.height = 48
        sprite.x_offset = 24
        sprite.y_offset = 0
        sprite.x_hot = 40
        sprite.y_hot = 16
        if x > ((WORLD_X << 4) // 2):
            if y > ((WORLD_Y << 4) // 2):
                sprite.frame = 10
            else:
                sprite.frame = 7
        else:
            if y > ((WORLD_Y << 4) // 2):
                sprite.frame = 1
            else:
                sprite.frame = 4
        sprite.count = 1000
        sprite.dest_x = context.pol_max_x << 4
        sprite.dest_y = context.pol_max_y << 4
        sprite.orig_x = sprite.x
        sprite.orig_y = sprite.y

    elif sprite.type == COP:  # Helicopter
        sprite.width = 32
        sprite.height = 32
        sprite.x_offset = 32
        sprite.y_offset = -16
        sprite.x_hot = 40
        sprite.y_hot = -8
        sprite.frame = 5
        sprite.count = 1500
        sprite.dest_x = Rand(context, (WORLD_X << 4) - 1)
        sprite.dest_y = Rand(context, (WORLD_Y << 4) - 1)
        sprite.orig_x = x - 30
        sprite.orig_y = y

    elif sprite.type == AIR:  # Airplane
        sprite.width = 48
        sprite.height = 48
        sprite.x_offset = 24
        sprite.y_offset = 0
        sprite.x_hot = 48
        sprite.y_hot = 16
        if x > ((WORLD_X - 20) << 4):
            sprite.x -= 100 + 48
            sprite.dest_x = sprite.x - 200
            sprite.frame = 7
        else:
            sprite.dest_x = sprite.x + 200
            sprite.frame = 11
        sprite.dest_y = sprite.y

    elif sprite.type == TOR:  # Tornado
        sprite.width = 48
        sprite.height = 48
        sprite.x_offset = 24
        sprite.y_offset = 0
        sprite.x_hot = 40
        sprite.y_hot = 36
        sprite.frame = 1
        sprite.count = 200

    elif sprite.type == EXP:  # Explosion
        sprite.width = 48
        sprite.height = 48
        sprite.x_offset = 24
        sprite.y_offset = 0
        sprite.x_hot = 40
        sprite.y_hot = 16
        sprite.frame = 1

    elif sprite.type == BUS:  # Bus
        sprite.width = 32
        sprite.height = 32
        sprite.x_offset = 30
        sprite.y_offset = -18
        sprite.x_hot = 40
        sprite.y_hot = -8
        sprite.frame = 1
        sprite.dir = 1


def destroy_sprite(context: AppContext, sprite: SimSprite) -> None:
    """
    Destroy a sprite and return it to the free pool.

    Args:
        sprite: Sprite to destroy
        :param context:
    """
    # global free_sprites

    # Remove from global sprites if it's the global instance
    if context.global_sprites[sprite.type] == sprite:
        context.global_sprites[sprite.type] = None

    # Clear name
    if sprite.name:
        sprite.name = ""

    # Remove from simulation sprite list
    if context.sim:
        current = context.sim.sprite
        prev: SimSprite | None = None
        while current:
            if current == sprite:
                if prev:
                    prev.next = current.next
                else:
                    context.sim.sprite = current.next
                context.sim.sprites -= 1
                break
            prev = current
            current = current.next

    # Add to free pool
    sprite.next = context.free_sprites
    context.free_sprites = sprite


def destroy_all_sprites(context: AppContext) -> None:
    """
    Destroy all sprites in the simulation.
    :param context:
    """
    if not context.sim:
        return

    sprite = context.sim.sprite
    while sprite:
        sprite.frame = 0
        sprite = sprite.next


def get_sprite(context: AppContext, sprite_type: int) -> SimSprite | None:
    """
    Get the global sprite instance for a type.

    Args:
        sprite_type: Sprite type to get

    Returns:
        Sprite instance if it exists and is active, None otherwise
        :param context:
    """
    sprite = context.global_sprites[sprite_type]
    if sprite and sprite.frame == 0:
        return None
    return sprite


def make_sprite(context: AppContext, sprite_type: int, x: int, y: int) -> SimSprite:
    """
    Create or reuse a sprite of the given type.

    Args:
        sprite_type: Type of sprite to create
        x: Initial X position
        y: Initial Y position

    Returns:
        Sprite instance
    """
    sprite = context.global_sprites[sprite_type]
    if sprite is None:
        sprite = new_sprite(context, "", sprite_type, x, y)
    else:
        init_sprite(context, sprite, x, y)
    return sprite


def make_new_sprite(context: AppContext,
    sprite_type: int, x: int, y: int
) -> SimSprite:
    """
    Create a new sprite instance (not reusing global).

    Args:
        sprite_type: Type of sprite to create
        x: Initial X position
        y: Initial Y position

    Returns:
        New sprite instance
        :param context:
    """
    return new_sprite(context, "", sprite_type, x, y)


# ============================================================================
# Sprite Movement and Animation
# ============================================================================


def move_objects(context: AppContext) -> None:
    """
    Update all sprites in the simulation.
    :param context:
    """
    # global cycle

    if not context.sim_speed:
        return

    context.cycle += 1

    if not context.sim:
        return

    sprite = context.sim.sprite
    while sprite:
        if sprite.frame:
            # Call appropriate movement function based on sprite type
            if sprite.type == TRA:
                do_train_sprite(context, sprite)
            elif sprite.type == COP:
                do_copter_sprite(context, sprite)
            elif sprite.type == AIR:
                do_airplane_sprite(context, sprite)
            elif sprite.type == SHI:
                do_ship_sprite(context, sprite)
            elif sprite.type == GOD:
                do_monster_sprite(context, sprite)
            elif sprite.type == TOR:
                do_tornado_sprite(context, sprite)
            elif sprite.type == EXP:
                do_explosion_sprite(context, sprite)
            elif sprite.type == BUS:
                do_bus_sprite(context, sprite)

            sprite = sprite.next
        else:
            # Remove inactive sprites
            if not sprite.name:  # Unnamed sprites get destroyed
                temp = sprite
                sprite = sprite.next
                destroy_sprite(context, temp)
            else:
                sprite = sprite.next


# ============================================================================
# Individual Sprite Movement Functions
# ============================================================================


def do_train_sprite(context: AppContext, sprite: SimSprite) -> None:
    """
    Handle train sprite movement and animation.

    Args:
        sprite: Train sprite to update
        :param context:
    """
    # Train movement tables
    Cx = [0, 16, 0, -16]
    Cy = [-16, 0, 16, 0]
    Dx = [0, 4, 0, -4, 0]
    Dy = [-4, 0, 4, 0, 0]
    TrainPic2 = [1, 2, 1, 2, 5]

    if sprite.frame == 3 or sprite.frame == 4:
        sprite.frame = TrainPic2[sprite.dir]

    sprite.x += Dx[sprite.dir]
    sprite.y += Dy[sprite.dir]

    if not (cycle & 3):
        dir_choice = Rand16(context) & 3
        for z in range(dir_choice, dir_choice + 4):
            dir2 = z & 3
            if sprite.dir != 4:
                if dir2 == ((sprite.dir + 2) & 3):
                    continue
            c = get_char(context, sprite.x + Cx[dir2] + 48, sprite.y + Cy[dir2])
            if (
                (RAILBASE <= c <= LASTRAIL)
                or (c == RAILVPOWERH)
                or (c == RAILHPOWERV)
            ):
                if (sprite.dir != dir2) and (sprite.dir != 4):
                    if (sprite.dir + dir2) == 3:
                        sprite.frame = 3
                    else:
                        sprite.frame = 4
                else:
                    sprite.frame = TrainPic2[dir2]

                if c == RAILBASE or c == (RAILBASE + 1):
                    sprite.frame = 5
                sprite.dir = dir2
                return

        if sprite.dir == 4:
            sprite.frame = 0
            return
        sprite.dir = 4


def do_copter_sprite(context: AppContext, sprite: SimSprite) -> None:
    """
    Handle helicopter sprite movement and animation.

    Args:
        sprite: Helicopter sprite to update
    """
    # Copter movement tables
    CDx = [0, 0, 3, 5, 3, 0, -3, -5, -3]
    CDy = [0, -5, -3, 0, 3, 5, 3, 0, -6]  # Note: last value adjusted from -3

    if sprite.sound_count > 0:
        sprite.sound_count -= 1

    if sprite.control < 0:
        if sprite.count > 0:
            sprite.count -= 1

        if not sprite.count:
            # Attract copter to monster and tornado
            s = get_sprite(context, GOD)
            if s is None:
                s = get_sprite(context, TOR)
            if s:
                sprite.dest_x = s.x
                sprite.dest_y = s.y
            else:
                sprite.dest_x = sprite.orig_x
                sprite.dest_y = sprite.orig_y

        if not sprite.count:  # land
            get_dir(sprite.x, sprite.y, sprite.orig_x, sprite.orig_y)
            if context.abs_dist < 30:
                sprite.frame = 0
                return
    else:
        get_dir(sprite.x, sprite.y, sprite.dest_x, sprite.dest_y)
        if context.abs_dist < 16:
            sprite.dest_x = sprite.orig_x
            sprite.dest_y = sprite.orig_y
            sprite.control = -1

    if not sprite.sound_count:  # send report
        x = (sprite.x + 48) >> 5
        y = sprite.y >> 5
        if (
                0 <= x < (WORLD_X >> 1)
                    and 0 <= y < (WORLD_Y >> 1)
        ):
            z = context.trf_density[x][y] >> 6
            if z > 1:
                z -= 1
            if z > 170 and (Rand16(context) & 7) == 0:
                # Send heavy traffic message
                pass  # Message system not implemented yet
            sprite.sound_count = 200

    z = sprite.frame
    if not (cycle & 3):
        d = get_dir(sprite.x, sprite.y, sprite.dest_x, sprite.dest_y)
        z = turn_to(z, d)
        sprite.frame = z

    sprite.x += CDx[z]
    sprite.y += CDy[z]


def do_airplane_sprite(context: AppContext, sprite: SimSprite) -> None:
    """
    Handle airplane sprite movement and animation.

    Args:
        sprite: Airplane sprite to update
        :param context:
    """
    # Airplane movement tables
    CDx = [0, 0, 6, 8, 6, 0, -6, -8, -6, 8, 8, 8]
    CDy = [0, -8, -6, 0, 6, 8, 6, 0, -6, 0, 0, 0]

    z = sprite.frame

    if not (cycle % 5):
        if z > 8:  # TakeOff
            z -= 1
            if z < 9:
                z = 3
            sprite.frame = z
        else:  # goto destination
            d = get_dir(sprite.x, sprite.y, sprite.dest_x, sprite.dest_y)
            z = turn_to(z, d)
            sprite.frame = z

    if context.abs_dist < 50:  # at destination
        sprite.dest_x = Rand(context, (WORLD_X * 16) + 100) - 50
        sprite.dest_y = Rand(context, (WORLD_Y * 16) + 100) - 50

    # Check for disasters
    if not context.no_disasters:
        s = context.sim.sprite if context.sim else None
        explode = False
        while s:
            if (
                s.frame != 0
                and ((s.type == COP) or (sprite != s and s.type == AIR))
                and check_sprite_collision(sprite, s)
            ):
                explode_sprite(context, s)
                explode = True
            s = s.next
        if explode:
            explode_sprite(context, sprite)

    sprite.x += CDx[z]
    sprite.y += CDy[z]
    if sprite_not_in_bounds(sprite):
        sprite.frame = 0


def do_ship_sprite(context: AppContext, sprite: SimSprite) -> None:
    """
    Handle ship sprite movement and animation.

    Args:
        sprite: Ship sprite to update
        :param context:
    """
    # Ship movement tables
    BDx = [0, 0, 1, 1, 1, 0, -1, -1, -1]
    BDy = [0, -1, -1, 0, 1, 1, 1, 0, -1]
    BPx = [0, 0, 2, 2, 2, 0, -2, -2, -2]
    BPy = [0, -2, -2, 0, 2, 2, 2, 0, -2]
    BtClrTab = [
        RIVER,
        CHANNEL,

        POWERBASE,
        POWERBASE + 1,
        RAILBASE,
        RAILBASE + 1,
        BRWH,
        BRWV,
    ]

    if sprite.sound_count > 0:
        sprite.sound_count -= 1
    if not sprite.sound_count:
        if (Rand16(context) & 3) == 1:
            if context.scenario_id == 2 and Rand(context, 10) < 5:  # San Francisco
                # MakeSound("city", "HonkHonk-Low -speed 80")
                pass
            else:
                # MakeSound("city", "HonkHonk-Low")
                pass
        sprite.sound_count = 200

    if sprite.count > 0:
        sprite.count -= 1
    if not sprite.count:
        sprite.count = 9
        if sprite.frame != sprite.new_dir:
            sprite.frame = turn_to(sprite.frame, sprite.new_dir)
            return
        tem = Rand16(context) & 7
        pem = tem  # Initialize pem
        t = 0  # Initialize t to default value
        for pem in range(tem, tem + 8):
            z = (pem & 7) + 1

            if z == sprite.dir:
                continue
            x = ((sprite.x + (48 - 1)) >> 4) + BDx[z]
            y = (sprite.y >> 4) + BDy[z]
            if test_bounds(x, y):
                t = context.map_data[x][y] & LOMASK
                if (
                    (t == CHANNEL)
                    or (t == BRWH)
                    or (t == BRWV)
                    or try_other(t, sprite.dir, z)
                ):
                    sprite.new_dir = z
                    sprite.frame = turn_to(sprite.frame, sprite.new_dir)
                    sprite.dir = z + 4
                    if sprite.dir > 8:
                        sprite.dir -= 8
                    break
        if pem == (tem + 8):
            sprite.dir = 10
            sprite.new_dir = (Rand16(context) & 7) + 1
    else:
        z = sprite.frame
        if z == sprite.new_dir:
            sprite.x += BPx[z]
            sprite.y += BPy[z]

    if sprite_not_in_bounds(sprite):
        sprite.frame = 0
        return

    for z in range(8):
        if t == BtClrTab[z]:
            break
        if z == 7:
            explode_sprite(context, sprite)


def do_monster_sprite(context: AppContext, sprite: SimSprite) -> None:
    """
    Handle monster sprite movement and animation.

    Args:
        sprite: Monster sprite to update
        :param context:
    """
    # Monster movement tables
    Gx = [2, 2, -2, -2, 0]
    Gy = [-2, 2, 2, -2, 0]
    ND1 = [0, 1, 2, 3]
    ND2 = [1, 2, 3, 0]
    nn1 = [2, 5, 8, 11]
    nn2 = [11, 2, 5, 8]

    if sprite.sound_count > 0:
        sprite.sound_count -= 1

    if sprite.control < 0:
        # business as usual
        if sprite.control == -2:
            d = (sprite.frame - 1) // 3
            z = (sprite.frame - 1) % 3
            if z == 2:
                sprite.step = 0
            if z == 0:
                sprite.step = 1
            if sprite.step:
                z += 1
            else:
                z -= 1
            c = get_dir(sprite.x, sprite.y, sprite.dest_x, sprite.dest_y)
            if context.abs_dist < 18:
                sprite.control = -1
                sprite.count = 1000
                sprite.flag = 1
                sprite.dest_x = sprite.orig_x
                sprite.dest_y = sprite.orig_y
            else:
                c = (c - 1) // 2
                if ((c != d) and (not Rand(context, 5))) or (not Rand(context, 20)):
                    diff = (c - d) & 3
                    if (diff == 1) or (diff == 3):
                        d = c
                    else:
                        if Rand16(context) & 1:
                            d += 1
                        else:
                            d -= 1
                        d &= 3
                else:
                    if not Rand(context, 20):
                        if Rand16(context) & 1:
                            d += 1
                        else:
                            d -= 1
                        d &= 3
        else:
            d = (sprite.frame - 1) // 3

            if d < 4:  # turn n s e w
                z = (sprite.frame - 1) % 3
                if z == 2:
                    sprite.step = 0
                if z == 0:
                    sprite.step = 1
                if sprite.step:
                    z += 1
                else:
                    z -= 1
                get_dir(sprite.x, sprite.y, sprite.dest_x, sprite.dest_y)
                if context.abs_dist < 60:
                    if sprite.flag == 0:
                        sprite.flag = 1
                        sprite.dest_x = sprite.orig_x
                        sprite.dest_y = sprite.orig_y
                    else:
                        sprite.frame = 0
                        return
                c = get_dir(sprite.x, sprite.y, sprite.dest_x, sprite.dest_y)
                c = (c - 1) // 2
                if (c != d) and (not Rand(context, 10)):
                    if Rand16(context) & 1:
                        z = ND1[d]
                    else:
                        z = ND2[d]
                    d = 4
                    if not sprite.sound_count:
                        # MakeSound("city", "Monster -speed [MonsterSpeed]")
                        sprite.sound_count = 50 + Rand(context, 100)
            else:
                d = 4
                c = sprite.frame
                z = (c - 13) & 3
                if not (Rand16(context) & 3):
                    if Rand16(context) & 1:
                        z = nn1[z]
                    else:
                        z = nn2[z]
                    d = (z - 1) // 3
                    z = (z - 1) % 3
    else:
        # somebody's taken control of the monster
        d = sprite.control
        z = (sprite.frame - 1) % 3

        if z == 2:
            sprite.step = 0
        if z == 0:
            sprite.step = 1
        if sprite.step:
            z += 1
        else:
            z -= 1

    z = ((d * 3) + z) + 1
    if z > 16:
        z = 16
    sprite.frame = z

    sprite.x += Gx[d]
    sprite.y += Gy[d]

    if sprite.count > 0:
        sprite.count -= 1
    c = get_char(context, sprite.x + sprite.x_hot, sprite.y + sprite.y_hot)
    if (c == -1) or (
        (c == RIVER) and (sprite.count != 0) and (sprite.control == -1)
    ):
        sprite.frame = 0  # kill zilla

    # Check collisions with other sprites
    s = context.sim.sprite if context.sim else None
    while s:
        if (
            s.frame != 0
            and (
                (s.type == AIR)
                or (s.type == COP)
                or (s.type == SHI)
                or (s.type == TRA)
            )
            and check_sprite_collision(sprite, s)
        ):
            explode_sprite(context, s)
        s = s.next

    destroy(context, sprite.x + 48, sprite.y + 16)


def do_tornado_sprite(context: AppContext, sprite: SimSprite) -> None:
    """
    Handle tornado sprite movement and animation.

    Args:
        sprite: Tornado sprite to update
        :param context:
    """
    CDx = [2, 3, 2, 0, -2, -3]
    CDy = [-2, 0, 2, 3, 2, 0]

    z = sprite.frame

    if z == 2:  # cycle animation
        if sprite.flag:
            z = 3
        else:
            z = 1
    else:
        if z == 1:
            sprite.flag = 1
        else:
            sprite.flag = 0
        z = 2

    if sprite.count > 0:
        sprite.count -= 1

    sprite.frame = z

    # Check collisions with other sprites
    s = context.sim.sprite if context.sim else None
    while s:
        if (
            s.frame != 0
            and (
                (s.type == AIR)
                or (s.type == COP)
                or (s.type == SHI)
                or (s.type == TRA)
            )
            and check_sprite_collision(sprite, s)
        ):
            explode_sprite(context, s)
        s = s.next

    z = Rand(context, 5)
    sprite.x += CDx[z]
    sprite.y += CDy[z]
    if sprite_not_in_bounds(sprite):
        sprite.frame = 0

    if (sprite.count != 0) and (not Rand(context, 500)):
        sprite.frame = 0

    destroy(context, sprite.x + 48, sprite.y + 40)


def do_explosion_sprite(context: AppContext, sprite: SimSprite) -> None:
    """
    Handle explosion sprite animation.

    Args:
        sprite: Explosion sprite to update
        :param context:
    """
    if not (cycle & 1):
        if sprite.frame == 1:
            # MakeSound("city", "Explosion-High")
            pass
        sprite.frame += 1

    if sprite.frame > 6:
        sprite.frame = 0

        # Start fires around explosion
        start_fire(context, sprite.x + 48 - 8, sprite.y + 16)
        start_fire(context, sprite.x + 48 - 24, sprite.y)
        start_fire(context, sprite.x + 48 + 8, sprite.y)
        start_fire(context, sprite.x + 48 - 24, sprite.y + 32)
        start_fire(context, sprite.x + 48 + 8, sprite.y + 32)
        return


def do_bus_sprite(context: AppContext, sprite: SimSprite) -> None:
    """
    Handle bus sprite movement and animation.

    Args:
        sprite: Bus sprite to update
        :param context:
    """
    Dx = [0, 1, 0, -1, 0]
    Dy = [-1, 0, 1, 0, 0]
    Dir2Frame = [1, 2, 1, 2]

    if sprite.turn:
        if sprite.turn < 0:  # ccw
            if sprite.dir & 1:  # up or down
                sprite.frame = 4
            else:  # left or right
                sprite.frame = 3
            sprite.turn += 1
            sprite.dir = (sprite.dir - 1) & 3
        else:  # cw
            if sprite.dir & 1:  # up or down
                sprite.frame = 3
            else:  # left or right
                sprite.frame = 4
            sprite.turn -= 1
            sprite.dir = (sprite.dir + 1) & 3
    else:
        # finish turn
        if (sprite.frame == 3) or (sprite.frame == 4):
            sprite.frame = Dir2Frame[sprite.dir]

    speed = 0  # Initialize speed to avoid unbound variable

    if sprite.speed == 0:
        # brake
        dx = 0
        dy = 0
    else:  # cruise at traffic speed
        tx = (sprite.x + sprite.x_hot) >> 5
        ty = (sprite.y + sprite.y_hot) >> 5
        if (
                0 <= tx < (WORLD_X >> 1)
                    and 0 <= ty < (WORLD_Y >> 1)
        ):
            z = context.trf_density[tx][ty] >> 6
            if z > 1:
                z -= 1
        else:
            z = 0

        context.speed = 8  # Initialize speed
        if z == 0:
            context.speed = 8
        elif z == 1:
            context.speed = 4
        else:
            context.speed = 1

        # govern speed
        if context.speed > sprite.speed:
            context.speed = sprite.speed

        if sprite.turn:
            if context.speed > 1:
                context.speed = 1
            dx = Dx[sprite.dir] * context.speed
            dy = Dy[sprite.dir] * context.speed
        else:
            dx = Dx[sprite.dir] * context.speed
            dy = Dy[sprite.dir] * context.speed

            tx = (sprite.x + sprite.x_hot) >> 4
            ty = (sprite.y + sprite.y_hot) >> 4

            # drift into the right lane
            if sprite.dir == 0:  # up
                z = ((tx << 4) + 4) - (sprite.x + sprite.x_hot)
                if z < 0:
                    dx = -1
                elif z > 0:
                    dx = 1
            elif sprite.dir == 1:  # right
                z = ((ty << 4) + 4) - (sprite.y + sprite.y_hot)
                if z < 0:
                    dy = -1
                elif z > 0:
                    dy = 1
            elif sprite.dir == 2:  # down
                z = (tx << 4) - (sprite.x + sprite.x_hot)
                if z < 0:
                    dx = -1
                elif z > 0:
                    dx = 1
            elif sprite.dir == 3:  # left
                z = (ty << 4) - (sprite.y + sprite.y_hot)
                if z < 0:
                    dy = -1
                elif z > 0:
                    dy = 1

    # Check ahead for obstacles
    otx = (sprite.x + sprite.x_hot + (Dx[sprite.dir] * 8)) >> 4
    oty = (sprite.y + sprite.y_hot + (Dy[sprite.dir] * 8)) >> 4
    if otx < 0:
        otx = 0
    elif otx >= WORLD_X:
        otx = WORLD_X - 1
    if oty < 0:
        oty = 0
    elif oty >= WORLD_Y:
        oty = WORLD_Y - 1

    tx = (sprite.x + sprite.x_hot + dx + (Dx[sprite.dir] * 8)) >> 4
    ty = (sprite.y + sprite.y_hot + dy + (Dy[sprite.dir] * 8)) >> 4
    if tx < 0:
        tx = 0
    elif tx >= WORLD_X:
        tx = WORLD_X - 1
    if ty < 0:
        ty = 0
    elif ty >= WORLD_Y:
        ty = WORLD_Y - 1

    if (tx != otx) or (ty != oty):
        z = can_drive_on(context, tx, ty)
        if z == 0:
            # can't drive forward into a new tile
            if speed == 8:
                # bulldozer_tool(None, tx, ty)  # Would need tools import
                pass
        else:
            # drive forward into a new tile
            if z > 0:
                # cool, cruise along
                pass
            else:
                # bumpy
                dx //= 2
                dy //= 2

    tx = (sprite.x + sprite.x_hot + dx) >> 4
    ty = (sprite.y + sprite.y_hot + dy) >> 4
    z = can_drive_on(context, tx, ty)
    if z > 0:
        # cool, cruise along
        pass
    else:
        if z < 0:
            # bumpy
            pass
        else:
            # something in the way
            pass

    sprite.x += dx
    sprite.y += dy

    if not context.no_disasters:
        s = context.sim.sprite if context.sim else None
        explode = False
        while s:
            if (
                sprite != s
                and s.frame != 0
                and (
                    (s.type == BUS) or ((s.type == TRA) and (s.frame != 5))
                )
                and check_sprite_collision(sprite, s)
            ):
                explode_sprite(context, s)
                explode = True
            s = s.next
        if explode:
            explode_sprite(context, sprite)


# ============================================================================
# Utility Functions
# ============================================================================


def get_char(context: AppContext, x: int, y: int) -> int:
    """
    Get tile character at world coordinates.

    Args:
        x: World X coordinate
        y: World Y coordinate

    Returns:
        Tile ID or -1 if out of bounds
        :param context:
    """
    x >>= 4
    y >>= 4
    if not test_bounds(x, y):
        return -1
    else:
        return context.map_data[x][y] & LOMASK


def turn_to(p: int, d: int) -> int:
    """
    Turn sprite direction towards destination.

    Args:
        p: Current direction
        d: Desired direction

    Returns:
        New direction
    """
    if p == d:
        return p
    if p < d:
        if (d - p) < 4:
            p += 1
        else:
            p -= 1
    else:
        if (p - d) < 4:
            p -= 1
        else:
            p += 1
    if p > 8:
        p = 1
    if p < 1:
        p = 8
    return p


def try_other(tpoo: int, told: int, tnew: int) -> int:
    """
    Check if sprite can turn to new direction on special tiles.

    Args:
        tpoo: Tile type
        told: Current direction
        tnew: New direction

    Returns:
        1 if turn is allowed, 0 otherwise
    """
    z = told + 4
    if z > 8:
        z -= 8
    if tnew != z:
        return 0
    if (
        (tpoo == POWERBASE)
        or (tpoo == POWERBASE + 1)
        or (tpoo == RAILBASE)
        or (tpoo == RAILBASE + 1)
    ):
        return 1
    return 0


def sprite_not_in_bounds(sprite: SimSprite) -> int:
    """
    Check if sprite is outside world bounds.

    Args:
        sprite: Sprite to check

    Returns:
        1 if out of bounds, 0 otherwise
    """
    x = sprite.x + sprite.x_hot
    y = sprite.y + sprite.y_hot

    if (
        (x < 0)
        or (y < 0)
        or (x >= (WORLD_X << 4))
        or (y >= (WORLD_Y << 4))
    ):
        return 1
    return 0


def get_dir(org_x: int, org_y: int, des_x: int, des_y: int) -> int:
    """
    Calculate direction from origin to destination.

    Args:
        org_x: Origin X coordinate
        org_y: Origin Y coordinate
        des_x: Destination X coordinate
        des_y: Destination Y coordinate

    Returns:
        Direction (1-8)
    """
    Gdtab = [0, 3, 2, 1, 3, 4, 5, 7, 6, 5, 7, 8, 1]
    disp_x = des_x - org_x
    disp_y = des_y - org_y
    z = 0

    if disp_x < 0:
        if disp_y < 0:
            z = 11
        else:
            z = 8
    else:
        if disp_y < 0:
            z = 2
        else:
            z = 5

    abs_disp_x = abs(disp_x)
    abs_disp_y = abs(disp_y)
    abs_dist = abs_disp_x + abs_disp_y

    if (abs_disp_x << 1) < abs_disp_y:
        z += 1
    elif (abs_disp_y << 1) < abs_disp_x:
        z -= 1

    if (z < 0) or (z > 12):
        z = 0

    return Gdtab[z]


def get_dis(x1: int, y1: int, x2: int, y2: int) -> int:
    """
    Calculate Manhattan distance between two points.

    Args:
        x1: Point 1 X coordinate
        y1: Point 1 Y coordinate
        x2: Point 2 X coordinate
        y2: Point 2 Y coordinate

    Returns:
        Manhattan distance
    """
    if x1 > x2:
        disp_x = x1 - x2
    else:
        disp_x = x2 - x1
    if y1 > y2:
        disp_y = y1 - y2
    else:
        disp_y = y2 - y1

    return disp_x + disp_y


def check_sprite_collision(
    s1: SimSprite, s2: SimSprite
) -> int:
    """
    Check if two sprites are colliding.

    Args:
        s1: First sprite
        s2: Second sprite

    Returns:
        1 if colliding, 0 otherwise
    """
    if (
        (s1.frame != 0)
        and (s2.frame != 0)
        and get_dis(s1.x + s1.x_hot, s1.y + s1.y_hot, s2.x + s2.x_hot, s2.y + s2.y_hot)
        < 30
    ):
        return 1
    return 0


def can_drive_on(context: AppContext, x: int, y: int) -> int:
    """
    Check if a vehicle can drive on the given tile.

    Args:
        x: Tile X coordinate
        y: Tile Y coordinate

    Returns:
        1 if drivable, -1 if bumpy, 0 if blocked
        :param context:
    """
    if not test_bounds(x, y):
        return 0

    tile = context.map_data[x][y] & LOMASK

    if (
        (
            (tile >= ROADBASE)
            and (tile <= LASTROAD)
            and (tile != BRWH)
            and (tile != BRWV)
        )
        or (tile == HRAILROAD)
        or (tile == VRAILROAD)
    ):
        return 1

    if (tile == DIRT) or tally(tile):  # tally function not implemented yet
        return -1

    return 0


def test_bounds(x: int, y: int) -> bool:
    """
    Check if coordinates are within world bounds.

    Args:
        x: X coordinate
        y: Y coordinate

    Returns:
        True if in bounds, False otherwise
    """
    return (
        0 <= x < WORLD_X and 0 <= y < WORLD_Y
    )


def tally(tile: int) -> bool:
    """
    Check if tile is a tally-able building (placeholder).

    Args:
        tile: Tile ID

    Returns:
        True if tally-able, False otherwise
    """
    # Placeholder - would need implementation from original C code
    return False


# ============================================================================
# Sprite Generation Functions
# ============================================================================


def generate_train(context: AppContext, x: int, y: int) -> None:
    """
    Generate a train sprite at the given location.

    Args:
        x: X coordinate
        y: Y coordinate
        :param context:
    """
    if context.total_pop > 20 and get_sprite(context, TRA) is None and not Rand(context, 25):
        make_sprite(context, TRA, (x << 4) + TRA_GROOVE_X, (y << 4) + TRA_GROOVE_Y)


def generate_bus(context: AppContext, x: int, y: int) -> None:
    """
    Generate a bus sprite at the given location.

    Args:
        x: X coordinate
        y: Y coordinate
        :param context:
    """
    if get_sprite(context, BUS) is None and not Rand(context, 25):
        make_sprite(context, BUS, (x << 4) + BUS_GROOVE_X, (y << 4) + BUS_GROOVE_Y)


def generate_ship(context: AppContext) -> None:
    """
    Generate a ship sprite in a channel.
    :param context:
    """
    if not (Rand16(context) & 3):
        for x in range(4, WORLD_X - 2):
            if context.map_data[x][0] == CHANNEL:
                make_ship_here(context, x, 0)
                return
    if not (Rand16(context) & 3):
        for y in range(1, WORLD_Y - 2):
            if context.map_data[0][y] == CHANNEL:
                make_ship_here(context, 0, y)
                return
    if not (Rand16(context) & 3):
        for x in range(4, WORLD_X - 2):
            if context.map_data[x][WORLD_Y - 1] == CHANNEL:
                make_ship_here(context, x, WORLD_Y - 1)
                return
    if not (Rand16(context) & 3):
        for y in range(1, WORLD_Y - 2):
            if context.map_data[WORLD_X - 1][y] == CHANNEL:
                make_ship_here(context, WORLD_X - 1, y)
                return


def make_ship_here(context: AppContext, x: int, y: int, z: int = 0) -> None:
    """
    Create a ship at the given location.

    Args:
        x: X coordinate
        y: Y coordinate
        z: Unused parameter (for compatibility)
        :param context:
    """
    make_sprite(context, SHI, (x << 4) - (48 - 1), (y << 4))


def make_monster(context: AppContext) -> None:
    """
    Generate a monster sprite.
    :param context:
    """
    sprite = get_sprite(context, GOD)
    if sprite:
        sprite.sound_count = 1
        sprite.count = 1000
        return

    for z in range(300):
        x = Rand(context, WORLD_X - 20) + 10
        y = Rand(context, WORLD_Y - 10) + 5
        if (context.map_data[x][y] == RIVER) or (
            context.map_data[x][y] == RIVER + BULLBIT
        ):
            monster_here(context, x, y)
            return
    monster_here(context, 60, 50)


def monster_here(context: AppContext, x: int, y: int) -> None:
    """
    Create a monster at the given location.

    Args:
        x: X coordinate
        y: Y coordinate
        :param context:
    """
    make_sprite(context, GOD, (x << 4) + 48, (y << 4))
    # ClearMes() - message system not implemented
    # SendMesAt(-21, x + 5, y)


def generate_copter(context: AppContext, x: int, y: int) -> None:
    """
    Generate a helicopter sprite.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    if get_sprite(context, COP):
        return

    make_sprite(context, COP, (x << 4), (y << 4) + 30)


def generate_plane(context: AppContext, x: int, y: int) -> None:
    """
    Generate an airplane sprite.

    Args:
        x: X coordinate
        y: Y coordinate
        :param context:
    """
    if get_sprite(context, AIR):
        return

    make_sprite(context, AIR, (x << 4) + 48, (y << 4) + 12)


def make_tornado(context: AppContext) -> None:
    """
    Generate a tornado sprite.
    :param context:
    """
    sprite = get_sprite(context, TOR)
    if sprite:
        sprite.count = 200
        return

    x = Rand(context, (WORLD_X << 4) - 800) + 400
    y = Rand(context, (WORLD_Y << 4) - 200) + 100
    make_sprite(context, TOR, x, y)
    # ClearMes() - message system not implemented


# Legacy API compatibility ----------------------------------------------------


def GenerateTrain(context: AppContext, x: int, y: int) -> None:
    """Compatibility wrapper for legacy camel-case API.
    :param context:
    """
    generate_train(context, x, y)


def GenerateBus(context: AppContext, x: int, y: int) -> None:
    generate_bus(context, x, y)


def GenerateShip(context: AppContext) -> None:
    generate_ship(context)


def GeneratePlane(context: AppContext, x: int, y: int) -> None:
    generate_plane(context, x, y)


def GenerateCopter(context: AppContext, x: int, y: int) -> None:
    generate_copter(context, x, y)


def MakeExplosion(context: AppContext, x: int, y: int) -> None:
    make_explosion(context, x, y)


def MakeExplosionAt(context: AppContext, x: int, y: int) -> None:
    make_explosion_at(context, x, y)


def GetSprite(context: AppContext, sprite_type: int) -> SimSprite | None:
    return get_sprite(context, sprite_type)


def MakeSprite(context: AppContext, sprite_type: int, x: int, y: int) -> SimSprite:
    return make_sprite(context, sprite_type, x, y)
    # SendMesAt(-22, (x >> 4) + 3, (y >> 4) + 2)


def make_explosion(context: AppContext, x: int, y: int) -> None:
    """
    Create an explosion at the given location.

    Args:
        x: X coordinate
        y: Y coordinate
        :param context:
    """
    if (
            0 <= x < WORLD_X
                and 0 <= y < WORLD_Y
    ):
        make_explosion_at(context, (x << 4) + 8, (y << 4) + 8)


def make_explosion_at(context: AppContext, x: int, y: int) -> None:
    """
    Create an explosion sprite at the given world coordinates.

    Args:
        x: World X coordinate
        y: World Y coordinate
        :param context:
    """
    make_new_sprite(context, EXP, x - 40, y - 16)


# ============================================================================
# Sprite Destruction and Effects
# ============================================================================


def explode_sprite(context: AppContext, sprite: SimSprite) -> None:
    """
    Explode a sprite and create appropriate effects.

    Args:
        sprite: Sprite to explode
        :param context:
    """
    # global crash_x, crash_y

    sprite.frame = 0

    x = sprite.x + sprite.x_hot
    y = sprite.y + sprite.y_hot
    make_explosion_at(context, x, y)

    x = x >> 4
    y = y >> 4

    if sprite.type == AIR:
        context.crash_x = x
        context.crash_y = y
        # SendMesAt(-24, x, y)
    elif sprite.type == SHI:
        context.crash_x = x
        context.crash_y = y
        # SendMesAt(-25, x, y)
    elif sprite.type == TRA:
        context.crash_x = x
        context.crash_y = y
        # SendMesAt(-26, x, y)
    elif sprite.type == COP:
        context.crash_x = x
        context.crash_y = y
        # SendMesAt(-27, x, y)
    elif sprite.type == BUS:
        context.crash_x = x
        context.crash_y = y
        # SendMesAt(-26, x, y)  # XXX for now

    # MakeSound("city", "Explosion-High")
    return


def destroy(context: AppContext, x: int, y: int) -> None:
    """
    Destroy tiles at the given location.

    Args:
        x: World X coordinate
        y: World Y coordinate
        :param context:
    """
    tile_x = x >> 4
    tile_y = y >> 4
    if not test_bounds(tile_x, tile_y):
        return
    z = context.map_data[tile_x][tile_y]
    t = z & LOMASK
    if t >= TREEBASE:
        if not (z & BURNBIT):
            if (t >= ROADBASE) and (t <= LASTROAD):
                context.map_data[tile_x][tile_y] = RIVER
            return
        if z & ZONEBIT:
            # OFireZone(tile_x, tile_y, z)  # Not implemented yet
            if t > RZB:
                make_explosion_at(context, x, y)
        if check_wet(t):
            context.map_data[tile_x][tile_y] = RIVER
        else:
            context.map_data[tile_x][tile_y] = (
                (SOMETINYEXP - 3) | BULLBIT | ANIMBIT
            )


def check_wet(x: int) -> int:
    """
    Check if tile is a water-related tile.

    Args:
        x: Tile ID

    Returns:
        1 if wet, 0 otherwise
    """
    if (
        (x == POWERBASE)
        or (x == POWERBASE + 1)
        or (x == RAILBASE)
        or (x == RAILBASE + 1)
        or (x == BRWH)
        or (x == BRWV)
    ):
        return 1
    else:
        return 0


def start_fire(context: AppContext, x: int, y: int) -> None:
    """
    Start a fire at the given location.

    Args:
        x: World X coordinate
        y: World Y coordinate
        :param context:
    """
    tile_x = x >> 4
    tile_y = y >> 4
    if (
        (tile_x >= WORLD_X)
        or (tile_y >= WORLD_Y)
        or (tile_x < 0)
        or (tile_y < 0)
    ):
        return
    z = context.map_data[tile_x][tile_y]
    t = z & LOMASK
    if (not (z & BURNBIT)) and (t != 0):
        return
    if z & ZONEBIT:
        return
    context.map_data[tile_x][tile_y] = FIRE + (Rand16(context) & 3) + ANIMBIT


# ============================================================================
# Rendering Functions (Pygame Adaptation)
# ============================================================================


def draw_objects(context: AppContext, view: SimView) -> None:
    """
    Draw all sprites in the view.

    Args:
        view: View to draw sprites in
        :param context:
    """
    sprite = context.sim.sprite if context.sim else None

    # XXX: sort these by layer (not implemented)

    while sprite:
        draw_sprite(view, sprite)
        sprite = sprite.next


def draw_sprite(
    view: SimView, sprite: SimSprite
) -> None:
    """
    Draw a single sprite in the view.

    Args:
        view: View to draw in
        sprite: Sprite to draw
    """
    if sprite.frame == 0:
        return

    # Calculate screen position (for future pygame rendering)
    x = (
        sprite.x
        - ((view.tile_x << 4) - view.screen_x)  # noqa: F841
        + sprite.x_offset
    )
    y = (
        sprite.y
        - ((view.tile_y << 4) - view.screen_y)  # noqa: F841
        + sprite.y_offset
    )

    # Placeholder for pygame rendering
    # In full implementation, this would:
    # 1. Get the appropriate sprite image from view.x.objects[sprite.type][frame_index]
    # 2. Set up clipping with mask
    # 3. Blit to the view's surface

    # For now, just mark that rendering would happen here
    pass


# ============================================================================
# TCL Command Interface
# ============================================================================


class SpriteCommand:
    """
    TCL command interface for sprite objects.

    Provides TCL-compatible commands for querying and modifying sprite properties.
    """

    def __init__(self, sprite: SimSprite):
        """
        Initialize sprite command interface.

        Args:
            sprite: Sprite to control via TCL commands
        """
        self.sprite = sprite

    def handle_command(self, command: str, *args) -> str:
        """
        Handle a TCL command for the sprite.

        Args:
            command: Command name
            *args: Command arguments

        Returns:
            Command result as string

        Raises:
            ValueError: If command is invalid
        """
        if command == "name":
            if args:
                self.sprite.name = args[0]
                return args[0]
            else:
                return self.sprite.name or ""

        elif command == "type":
            if args:
                try:
                    self.sprite.type = int(args[0])
                    return args[0]
                except ValueError:
                    raise ValueError(f"Invalid type: {args[0]}")
            else:
                return str(self.sprite.type)

        elif command == "frame":
            if args:
                try:
                    self.sprite.frame = int(args[0])
                    return args[0]
                except ValueError:
                    raise ValueError(f"Invalid frame: {args[0]}")
            else:
                return str(self.sprite.frame)

        elif command == "x":
            if args:
                try:
                    self.sprite.x = int(args[0])
                    return args[0]
                except ValueError:
                    raise ValueError(f"Invalid x coordinate: {args[0]}")
            else:
                return str(self.sprite.x)

        elif command == "y":
            if args:
                try:
                    self.sprite.y = int(args[0])
                    return args[0]
                except ValueError:
                    raise ValueError(f"Invalid y coordinate: {args[0]}")
            else:
                return str(self.sprite.y)

        else:
            raise ValueError(f"Unknown sprite command: {command}")


# ============================================================================
# Initialization
# ============================================================================


def initialize_sprite_system(context: AppContext) -> None:
    """
    Initialize the sprite management system.
    """
    # global global_sprites, free_sprites, cycle, crash_x, crash_y

    # Initialize global sprite array
    context.global_sprites = [None] * OBJN

    # Clear free sprite pool
    context.free_sprites = None

    # Reset cycle counter
    context.cycle = 0

    # Reset crash locations
    context.crash_x = 0
    context.crash_y = 0

    # Clear all sprites from simulation
    if context.sim:
        context.sim.sprites = 0
        context.sim.sprite = None
