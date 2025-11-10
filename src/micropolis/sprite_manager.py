"""
sprite_manager.py - Sprite management system for Micropolis Python port

This module implements the sprite management system ported from w_sprite.c,
responsible for managing moving objects (cars, disasters, helicopters, etc.)
in the game world.
"""


import pygame

from . import random, types

# ============================================================================
# Constants
# ============================================================================

# Sprite groove offsets (from w_sprite.c)
TRA_GROOVE_X = -39
TRA_GROOVE_Y = 6
BUS_GROOVE_X = -39
BUS_GROOVE_Y = 6

# Sprite directions (8-directional movement)
DIR_NORTH = 0
DIR_NORTHEAST = 1
DIR_EAST = 2
DIR_SOUTHEAST = 3
DIR_SOUTH = 4
DIR_SOUTHWEST = 5
DIR_WEST = 6
DIR_NORTHWEST = 7

# Animation cycle counter
Cycle = 0

# Crash locations (for message reporting)
CrashX = 0
CrashY = 0

# Global sprite instances (one per type)
GlobalSprites: list[types.SimSprite | None] = [None] * types.OBJN

# Free sprite pool
FreeSprites: types.SimSprite | None = None

# ============================================================================
# Sprite Lifecycle Management
# ============================================================================

def new_sprite(name: str, sprite_type: int, x: int = 0, y: int = 0) -> types.SimSprite:
    """
    Create a new sprite.

    Args:
        name: Sprite name
        sprite_type: Sprite type (TRA, COP, etc.)
        x: Initial X position
        y: Initial Y position

    Returns:
        New SimSprite instance
    """
    global FreeSprites

    sprite: types.SimSprite | None = None

    if FreeSprites:
        sprite = FreeSprites
        FreeSprites = sprite.next
    else:
        sprite = types.SimSprite()

    sprite.name = name
    sprite.type = sprite_type

    init_sprite(sprite, x, y)

    # Add to simulation sprite list
    if types.sim:
        types.sim.sprites += 1
        sprite.next = types.sim.sprite
        types.sim.sprite = sprite

    return sprite

def init_sprite(sprite: types.SimSprite, x: int, y: int) -> None:
    """
    Initialize sprite with default values and type-specific settings.

    Args:
        sprite: Sprite to initialize
        x: Initial X position
        y: Initial Y position
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
    if GlobalSprites[sprite.type] is None:
        GlobalSprites[sprite.type] = sprite

    # Type-specific initialization
    if sprite.type == types.TRA:  # Train
        sprite.width = 32
        sprite.height = 32
        sprite.x_offset = 32
        sprite.y_offset = -16
        sprite.x_hot = 40
        sprite.y_hot = -8
        sprite.frame = 1
        sprite.dir = 4

    elif sprite.type == types.SHI:  # Ship
        sprite.width = 48
        sprite.height = 48
        sprite.x_offset = 32
        sprite.y_offset = -16
        sprite.x_hot = 48
        sprite.y_hot = 0
        if x < (4 << 4):
            sprite.frame = 3
        elif x >= ((types.WORLD_X - 4) << 4):
            sprite.frame = 7
        elif y < (4 << 4):
            sprite.frame = 5
        elif y >= ((types.WORLD_Y - 4) << 4):
            sprite.frame = 1
        else:
            sprite.frame = 3
        sprite.new_dir = sprite.frame
        sprite.dir = 10
        sprite.count = 1

    elif sprite.type == types.GOD:  # Monster
        sprite.width = 48
        sprite.height = 48
        sprite.x_offset = 24
        sprite.y_offset = 0
        sprite.x_hot = 40
        sprite.y_hot = 16
        if x > ((types.WORLD_X << 4) // 2):
            if y > ((types.WORLD_Y << 4) // 2):
                sprite.frame = 10
            else:
                sprite.frame = 7
        else:
            if y > ((types.WORLD_Y << 4) // 2):
                sprite.frame = 1
            else:
                sprite.frame = 4
        sprite.count = 1000
        sprite.dest_x = types.PolMaxX << 4
        sprite.dest_y = types.PolMaxY << 4
        sprite.orig_x = sprite.x
        sprite.orig_y = sprite.y

    elif sprite.type == types.COP:  # Helicopter
        sprite.width = 32
        sprite.height = 32
        sprite.x_offset = 32
        sprite.y_offset = -16
        sprite.x_hot = 40
        sprite.y_hot = -8
        sprite.frame = 5
        sprite.count = 1500
        sprite.dest_x = random.Rand((types.WORLD_X << 4) - 1)
        sprite.dest_y = random.Rand((types.WORLD_Y << 4) - 1)
        sprite.orig_x = x - 30
        sprite.orig_y = y

    elif sprite.type == types.AIR:  # Airplane
        sprite.width = 48
        sprite.height = 48
        sprite.x_offset = 24
        sprite.y_offset = 0
        sprite.x_hot = 48
        sprite.y_hot = 16
        if x > ((types.WORLD_X - 20) << 4):
            sprite.x -= 100 + 48
            sprite.dest_x = sprite.x - 200
            sprite.frame = 7
        else:
            sprite.dest_x = sprite.x + 200
            sprite.frame = 11
        sprite.dest_y = sprite.y

    elif sprite.type == types.TOR:  # Tornado
        sprite.width = 48
        sprite.height = 48
        sprite.x_offset = 24
        sprite.y_offset = 0
        sprite.x_hot = 40
        sprite.y_hot = 36
        sprite.frame = 1
        sprite.count = 200

    elif sprite.type == types.EXP:  # Explosion
        sprite.width = 48
        sprite.height = 48
        sprite.x_offset = 24
        sprite.y_offset = 0
        sprite.x_hot = 40
        sprite.y_hot = 16
        sprite.frame = 1

    elif sprite.type == types.BUS:  # Bus
        sprite.width = 32
        sprite.height = 32
        sprite.x_offset = 30
        sprite.y_offset = -18
        sprite.x_hot = 40
        sprite.y_hot = -8
        sprite.frame = 1
        sprite.dir = 1

def destroy_sprite(sprite: types.SimSprite) -> None:
    """
    Destroy a sprite and return it to the free pool.

    Args:
        sprite: Sprite to destroy
    """
    global FreeSprites

    # Remove from global sprites if it's the global instance
    if GlobalSprites[sprite.type] == sprite:
        GlobalSprites[sprite.type] = None

    # Clear name
    if sprite.name:
        sprite.name = ""

    # Remove from simulation sprite list
    if types.sim:
        current = types.sim.sprite
        prev: types.SimSprite | None = None
        while current:
            if current == sprite:
                if prev:
                    prev.next = current.next
                else:
                    types.sim.sprite = current.next
                types.sim.sprites -= 1
                break
            prev = current
            current = current.next

    # Add to free pool
    sprite.next = FreeSprites
    FreeSprites = sprite

def destroy_all_sprites() -> None:
    """
    Destroy all sprites in the simulation.
    """
    if not types.sim:
        return

    sprite = types.sim.sprite
    while sprite:
        sprite.frame = 0
        sprite = sprite.next

def get_sprite(sprite_type: int) -> types.SimSprite | None:
    """
    Get the global sprite instance for a type.

    Args:
        sprite_type: Sprite type to get

    Returns:
        Sprite instance if it exists and is active, None otherwise
    """
    sprite = GlobalSprites[sprite_type]
    if sprite and sprite.frame == 0:
        return None
    return sprite

def make_sprite(sprite_type: int, x: int, y: int) -> types.SimSprite:
    """
    Create or reuse a sprite of the given type.

    Args:
        sprite_type: Type of sprite to create
        x: Initial X position
        y: Initial Y position

    Returns:
        Sprite instance
    """
    sprite = GlobalSprites[sprite_type]
    if sprite is None:
        sprite = new_sprite("", sprite_type, x, y)
    else:
        init_sprite(sprite, x, y)
    return sprite

def make_new_sprite(sprite_type: int, x: int, y: int) -> types.SimSprite:
    """
    Create a new sprite instance (not reusing global).

    Args:
        sprite_type: Type of sprite to create
        x: Initial X position
        y: Initial Y position

    Returns:
        New sprite instance
    """
    return new_sprite("", sprite_type, x, y)

# ============================================================================
# Sprite Movement and Animation
# ============================================================================

def move_objects() -> None:
    """
    Update all sprites in the simulation.
    """
    global Cycle

    if not types.SimSpeed:
        return

    Cycle += 1

    if not types.sim:
        return

    sprite = types.sim.sprite
    while sprite:
        if sprite.frame:
            # Call appropriate movement function based on sprite type
            if sprite.type == types.TRA:
                do_train_sprite(sprite)
            elif sprite.type == types.COP:
                do_copter_sprite(sprite)
            elif sprite.type == types.AIR:
                do_airplane_sprite(sprite)
            elif sprite.type == types.SHI:
                do_ship_sprite(sprite)
            elif sprite.type == types.GOD:
                do_monster_sprite(sprite)
            elif sprite.type == types.TOR:
                do_tornado_sprite(sprite)
            elif sprite.type == types.EXP:
                do_explosion_sprite(sprite)
            elif sprite.type == types.BUS:
                do_bus_sprite(sprite)

            sprite = sprite.next
        else:
            # Remove inactive sprites
            if not sprite.name:  # Unnamed sprites get destroyed
                temp = sprite
                sprite = sprite.next
                destroy_sprite(temp)
            else:
                sprite = sprite.next

# ============================================================================
# Individual Sprite Movement Functions
# ============================================================================

def do_train_sprite(sprite: types.SimSprite) -> None:
    """
    Handle train sprite movement and animation.

    Args:
        sprite: Train sprite to update
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

    if not (Cycle & 3):
        dir_choice = random.Rand16() & 3
        for z in range(dir_choice, dir_choice + 4):
            dir2 = z & 3
            if sprite.dir != 4:
                if dir2 == ((sprite.dir + 2) & 3):
                    continue
            c = get_char(sprite.x + Cx[dir2] + 48, sprite.y + Cy[dir2])
            if ((c >= types.RAILBASE and c <= types.LASTRAIL) or
                (c == types.RAILVPOWERH) or
                (c == types.RAILHPOWERV)):
                if (sprite.dir != dir2) and (sprite.dir != 4):
                    if (sprite.dir + dir2) == 3:
                        sprite.frame = 3
                    else:
                        sprite.frame = 4
                else:
                    sprite.frame = TrainPic2[dir2]

                if c == types.RAILBASE or c == (types.RAILBASE + 1):
                    sprite.frame = 5
                sprite.dir = dir2
                return

        if sprite.dir == 4:
            sprite.frame = 0
            return
        sprite.dir = 4

def do_copter_sprite(sprite: types.SimSprite) -> None:
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
            s = get_sprite(types.GOD)
            if s is None:
                s = get_sprite(types.TOR)
            if s:
                sprite.dest_x = s.x
                sprite.dest_y = s.y
            else:
                sprite.dest_x = sprite.orig_x
                sprite.dest_y = sprite.orig_y

        if not sprite.count:  # land
            get_dir(sprite.x, sprite.y, sprite.orig_x, sprite.orig_y)
            if types.absDist < 30:
                sprite.frame = 0
                return
    else:
        get_dir(sprite.x, sprite.y, sprite.dest_x, sprite.dest_y)
        if types.absDist < 16:
            sprite.dest_x = sprite.orig_x
            sprite.dest_y = sprite.orig_y
            sprite.control = -1

    if not sprite.sound_count:  # send report
        x = (sprite.x + 48) >> 5
        y = sprite.y >> 5
        if (x >= 0 and x < (types.WORLD_X >> 1) and
            y >= 0 and y < (types.WORLD_Y >> 1)):
            z = types.TrfDensity[x][y] >> 6
            if z > 1:
                z -= 1
            if z > 170 and (random.Rand16() & 7) == 0:
                # Send heavy traffic message
                pass  # Message system not implemented yet
            sprite.sound_count = 200

    z = sprite.frame
    if not (Cycle & 3):
        d = get_dir(sprite.x, sprite.y, sprite.dest_x, sprite.dest_y)
        z = turn_to(z, d)
        sprite.frame = z

    sprite.x += CDx[z]
    sprite.y += CDy[z]

def do_airplane_sprite(sprite: types.SimSprite) -> None:
    """
    Handle airplane sprite movement and animation.

    Args:
        sprite: Airplane sprite to update
    """
    # Airplane movement tables
    CDx = [0, 0, 6, 8, 6, 0, -6, -8, -6, 8, 8, 8]
    CDy = [0, -8, -6, 0, 6, 8, 6, 0, -6, 0, 0, 0]

    z = sprite.frame

    if not (Cycle % 5):
        if z > 8:  # TakeOff
            z -= 1
            if z < 9:
                z = 3
            sprite.frame = z
        else:  # goto destination
            d = get_dir(sprite.x, sprite.y, sprite.dest_x, sprite.dest_y)
            z = turn_to(z, d)
            sprite.frame = z

    if types.absDist < 50:  # at destination
        sprite.dest_x = random.Rand((types.WORLD_X * 16) + 100) - 50
        sprite.dest_y = random.Rand((types.WORLD_Y * 16) + 100) - 50

    # Check for disasters
    if not types.NoDisasters:
        s = types.sim.sprite if types.sim else None
        explode = False
        while s:
            if (s.frame != 0 and
                ((s.type == types.COP) or
                 (sprite != s and s.type == types.AIR)) and
                check_sprite_collision(sprite, s)):
                explode_sprite(s)
                explode = True
            s = s.next
        if explode:
            explode_sprite(sprite)

    sprite.x += CDx[z]
    sprite.y += CDy[z]
    if sprite_not_in_bounds(sprite):
        sprite.frame = 0

def do_ship_sprite(sprite: types.SimSprite) -> None:
    """
    Handle ship sprite movement and animation.

    Args:
        sprite: Ship sprite to update
    """
    # Ship movement tables
    BDx = [0, 0, 1, 1, 1, 0, -1, -1, -1]
    BDy = [0, -1, -1, 0, 1, 1, 1, 0, -1]
    BPx = [0, 0, 2, 2, 2, 0, -2, -2, -2]
    BPy = [0, -2, -2, 0, 2, 2, 2, 0, -2]
    BtClrTab = [types.RIVER, types.CHANNEL, types.POWERBASE, types.POWERBASE + 1,
                types.RAILBASE, types.RAILBASE + 1, types.BRWH, types.BRWV]

    if sprite.sound_count > 0:
        sprite.sound_count -= 1
    if not sprite.sound_count:
        if (random.Rand16() & 3) == 1:
            if types.ScenarioID == 2 and random.Rand(10) < 5:  # San Francisco
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
        tem = random.Rand16() & 7
        pem = tem  # Initialize pem
        t = 0      # Initialize t to default value
        for pem in range(tem, tem + 8):
            z = (pem & 7) + 1

            if z == sprite.dir:
                continue
            x = ((sprite.x + (48 - 1)) >> 4) + BDx[z]
            y = (sprite.y >> 4) + BDy[z]
            if test_bounds(x, y):
                t = types.Map[x][y] & types.LOMASK
                if ((t == types.CHANNEL) or (t == types.BRWH) or (t == types.BRWV) or
                    try_other(t, sprite.dir, z)):
                    sprite.new_dir = z
                    sprite.frame = turn_to(sprite.frame, sprite.new_dir)
                    sprite.dir = z + 4
                    if sprite.dir > 8:
                        sprite.dir -= 8
                    break
        if pem == (tem + 8):
            sprite.dir = 10
            sprite.new_dir = (random.Rand16() & 7) + 1
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
            explode_sprite(sprite)

def do_monster_sprite(sprite: types.SimSprite) -> None:
    """
    Handle monster sprite movement and animation.

    Args:
        sprite: Monster sprite to update
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
            if types.absDist < 18:
                sprite.control = -1
                sprite.count = 1000
                sprite.flag = 1
                sprite.dest_x = sprite.orig_x
                sprite.dest_y = sprite.orig_y
            else:
                c = (c - 1) // 2
                if ((c != d) and (not random.Rand(5))) or (not random.Rand(20)):
                    diff = (c - d) & 3
                    if (diff == 1) or (diff == 3):
                        d = c
                    else:
                        if random.Rand16() & 1:
                            d += 1
                        else:
                            d -= 1
                        d &= 3
                else:
                    if not random.Rand(20):
                        if random.Rand16() & 1:
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
                if types.absDist < 60:
                    if sprite.flag == 0:
                        sprite.flag = 1
                        sprite.dest_x = sprite.orig_x
                        sprite.dest_y = sprite.orig_y
                    else:
                        sprite.frame = 0
                        return
                c = get_dir(sprite.x, sprite.y, sprite.dest_x, sprite.dest_y)
                c = (c - 1) // 2
                if (c != d) and (not random.Rand(10)):
                    if random.Rand16() & 1:
                        z = ND1[d]
                    else:
                        z = ND2[d]
                    d = 4
                    if not sprite.sound_count:
                        # MakeSound("city", "Monster -speed [MonsterSpeed]")
                        sprite.sound_count = 50 + random.Rand(100)
            else:
                d = 4
                c = sprite.frame
                z = (c - 13) & 3
                if not (random.Rand16() & 3):
                    if random.Rand16() & 1:
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

    z = (((d * 3) + z) + 1)
    if z > 16:
        z = 16
    sprite.frame = z

    sprite.x += Gx[d]
    sprite.y += Gy[d]

    if sprite.count > 0:
        sprite.count -= 1
    c = get_char(sprite.x + sprite.x_hot, sprite.y + sprite.y_hot)
    if (c == -1) or ((c == types.RIVER) and (sprite.count != 0) and (sprite.control == -1)):
        sprite.frame = 0  # kill zilla

    # Check collisions with other sprites
    s = types.sim.sprite if types.sim else None
    while s:
        if (s.frame != 0 and
            ((s.type == types.AIR) or (s.type == types.COP) or
             (s.type == types.SHI) or (s.type == types.TRA)) and
            check_sprite_collision(sprite, s)):
            explode_sprite(s)
        s = s.next

    destroy(sprite.x + 48, sprite.y + 16)

def do_tornado_sprite(sprite: types.SimSprite) -> None:
    """
    Handle tornado sprite movement and animation.

    Args:
        sprite: Tornado sprite to update
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
    s = types.sim.sprite if types.sim else None
    while s:
        if (s.frame != 0 and
            ((s.type == types.AIR) or (s.type == types.COP) or
             (s.type == types.SHI) or (s.type == types.TRA)) and
            check_sprite_collision(sprite, s)):
            explode_sprite(s)
        s = s.next

    z = random.Rand(5)
    sprite.x += CDx[z]
    sprite.y += CDy[z]
    if sprite_not_in_bounds(sprite):
        sprite.frame = 0

    if (sprite.count != 0) and (not random.Rand(500)):
        sprite.frame = 0

    destroy(sprite.x + 48, sprite.y + 40)

def do_explosion_sprite(sprite: types.SimSprite) -> None:
    """
    Handle explosion sprite animation.

    Args:
        sprite: Explosion sprite to update
    """
    if not (Cycle & 1):
        if sprite.frame == 1:
            # MakeSound("city", "Explosion-High")
            pass
        sprite.frame += 1

    if sprite.frame > 6:
        sprite.frame = 0

        # Start fires around explosion
        start_fire(sprite.x + 48 - 8, sprite.y + 16)
        start_fire(sprite.x + 48 - 24, sprite.y)
        start_fire(sprite.x + 48 + 8, sprite.y)
        start_fire(sprite.x + 48 - 24, sprite.y + 32)
        start_fire(sprite.x + 48 + 8, sprite.y + 32)
        return

def do_bus_sprite(sprite: types.SimSprite) -> None:
    """
    Handle bus sprite movement and animation.

    Args:
        sprite: Bus sprite to update
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
        if (tx >= 0 and tx < (types.WORLD_X >> 1) and
            ty >= 0 and ty < (types.WORLD_Y >> 1)):
            z = types.TrfDensity[tx][ty] >> 6
            if z > 1:
                z -= 1
        else:
            z = 0

        speed = 8  # Initialize speed
        if z == 0:
            speed = 8
        elif z == 1:
            speed = 4
        else:
            speed = 1

        # govern speed
        if speed > sprite.speed:
            speed = sprite.speed

        if sprite.turn:
            if speed > 1:
                speed = 1
            dx = Dx[sprite.dir] * speed
            dy = Dy[sprite.dir] * speed
        else:
            dx = Dx[sprite.dir] * speed
            dy = Dy[sprite.dir] * speed

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
                z = ((tx << 4)) - (sprite.x + sprite.x_hot)
                if z < 0:
                    dx = -1
                elif z > 0:
                    dx = 1
            elif sprite.dir == 3:  # left
                z = ((ty << 4)) - (sprite.y + sprite.y_hot)
                if z < 0:
                    dy = -1
                elif z > 0:
                    dy = 1

    # Check ahead for obstacles
    otx = (sprite.x + sprite.x_hot + (Dx[sprite.dir] * 8)) >> 4
    oty = (sprite.y + sprite.y_hot + (Dy[sprite.dir] * 8)) >> 4
    if otx < 0:
        otx = 0
    elif otx >= types.WORLD_X:
        otx = types.WORLD_X - 1
    if oty < 0:
        oty = 0
    elif oty >= types.WORLD_Y:
        oty = types.WORLD_Y - 1

    tx = (sprite.x + sprite.x_hot + dx + (Dx[sprite.dir] * 8)) >> 4
    ty = (sprite.y + sprite.y_hot + dy + (Dy[sprite.dir] * 8)) >> 4
    if tx < 0:
        tx = 0
    elif tx >= types.WORLD_X:
        tx = types.WORLD_X - 1
    if ty < 0:
        ty = 0
    elif ty >= types.WORLD_Y:
        ty = types.WORLD_Y - 1

    if (tx != otx) or (ty != oty):
        z = can_drive_on(tx, ty)
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
    z = can_drive_on(tx, ty)
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

    if not types.NoDisasters:
        s = types.sim.sprite if types.sim else None
        explode = False
        while s:
            if (sprite != s and s.frame != 0 and
                ((s.type == types.BUS) or
                 ((s.type == types.TRA) and (s.frame != 5))) and
                check_sprite_collision(sprite, s)):
                explode_sprite(s)
                explode = True
            s = s.next
        if explode:
            explode_sprite(sprite)

# ============================================================================
# Utility Functions
# ============================================================================

def get_char(x: int, y: int) -> int:
    """
    Get tile character at world coordinates.

    Args:
        x: World X coordinate
        y: World Y coordinate

    Returns:
        Tile ID or -1 if out of bounds
    """
    x >>= 4
    y >>= 4
    if not test_bounds(x, y):
        return -1
    else:
        return types.Map[x][y] & types.LOMASK

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
    if ((tpoo == types.POWERBASE) or (tpoo == types.POWERBASE + 1) or
        (tpoo == types.RAILBASE) or (tpoo == types.RAILBASE + 1)):
        return 1
    return 0

def sprite_not_in_bounds(sprite: types.SimSprite) -> int:
    """
    Check if sprite is outside world bounds.

    Args:
        sprite: Sprite to check

    Returns:
        1 if out of bounds, 0 otherwise
    """
    x = sprite.x + sprite.x_hot
    y = sprite.y + sprite.y_hot

    if ((x < 0) or (y < 0) or
        (x >= (types.WORLD_X << 4)) or
        (y >= (types.WORLD_Y << 4))):
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
    types.absDist = abs_disp_x + abs_disp_y

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

def check_sprite_collision(s1: types.SimSprite, s2: types.SimSprite) -> int:
    """
    Check if two sprites are colliding.

    Args:
        s1: First sprite
        s2: Second sprite

    Returns:
        1 if colliding, 0 otherwise
    """
    if ((s1.frame != 0) and (s2.frame != 0) and
        get_dis(s1.x + s1.x_hot, s1.y + s1.y_hot,
                s2.x + s2.x_hot, s2.y + s2.y_hot) < 30):
        return 1
    return 0

def can_drive_on(x: int, y: int) -> int:
    """
    Check if a vehicle can drive on the given tile.

    Args:
        x: Tile X coordinate
        y: Tile Y coordinate

    Returns:
        1 if drivable, -1 if bumpy, 0 if blocked
    """
    if not test_bounds(x, y):
        return 0

    tile = types.Map[x][y] & types.LOMASK

    if (((tile >= types.ROADBASE) and (tile <= types.LASTROAD) and
         (tile != types.BRWH) and (tile != types.BRWV)) or
        (tile == types.HRAILROAD) or (tile == types.VRAILROAD)):
        return 1

    if (tile == types.DIRT) or tally(tile):  # tally function not implemented yet
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
    return 0 <= x < types.WORLD_X and 0 <= y < types.WORLD_Y

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

def generate_train(x: int, y: int) -> None:
    """
    Generate a train sprite at the given location.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    if (types.TotalPop > 20 and
        get_sprite(types.TRA) is None and
        not random.Rand(25)):
        make_sprite(types.TRA, (x << 4) + TRA_GROOVE_X, (y << 4) + TRA_GROOVE_Y)

def generate_bus(x: int, y: int) -> None:
    """
    Generate a bus sprite at the given location.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    if (get_sprite(types.BUS) is None and not random.Rand(25)):
        make_sprite(types.BUS, (x << 4) + BUS_GROOVE_X, (y << 4) + BUS_GROOVE_Y)

def generate_ship() -> None:
    """
    Generate a ship sprite in a channel.
    """
    if not (random.Rand16() & 3):
        for x in range(4, types.WORLD_X - 2):
            if types.Map[x][0] == types.CHANNEL:
                make_ship_here(x, 0)
                return
    if not (random.Rand16() & 3):
        for y in range(1, types.WORLD_Y - 2):
            if types.Map[0][y] == types.CHANNEL:
                make_ship_here(0, y)
                return
    if not (random.Rand16() & 3):
        for x in range(4, types.WORLD_X - 2):
            if types.Map[x][types.WORLD_Y - 1] == types.CHANNEL:
                make_ship_here(x, types.WORLD_Y - 1)
                return
    if not (random.Rand16() & 3):
        for y in range(1, types.WORLD_Y - 2):
            if types.Map[types.WORLD_X - 1][y] == types.CHANNEL:
                make_ship_here(types.WORLD_X - 1, y)
                return

def make_ship_here(x: int, y: int, z: int = 0) -> None:
    """
    Create a ship at the given location.

    Args:
        x: X coordinate
        y: Y coordinate
        z: Unused parameter (for compatibility)
    """
    make_sprite(types.SHI, (x << 4) - (48 - 1), (y << 4))

def make_monster() -> None:
    """
    Generate a monster sprite.
    """
    sprite = get_sprite(types.GOD)
    if sprite:
        sprite.sound_count = 1
        sprite.count = 1000
        return

    for z in range(300):
        x = random.Rand(types.WORLD_X - 20) + 10
        y = random.Rand(types.WORLD_Y - 10) + 5
        if ((types.Map[x][y] == types.RIVER) or
            (types.Map[x][y] == types.RIVER + types.BULLBIT)):
            monster_here(x, y)
            return
    monster_here(60, 50)

def monster_here(x: int, y: int) -> None:
    """
    Create a monster at the given location.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    make_sprite(types.GOD, (x << 4) + 48, (y << 4))
    # ClearMes() - message system not implemented
    # SendMesAt(-21, x + 5, y)

def generate_copter(x: int, y: int) -> None:
    """
    Generate a helicopter sprite.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    if get_sprite(types.COP):
        return

    make_sprite(types.COP, (x << 4), (y << 4) + 30)

def generate_plane(x: int, y: int) -> None:
    """
    Generate an airplane sprite.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    if get_sprite(types.AIR):
        return

    make_sprite(types.AIR, (x << 4) + 48, (y << 4) + 12)

def make_tornado() -> None:
    """
    Generate a tornado sprite.
    """
    sprite = get_sprite(types.TOR)
    if sprite:
        sprite.count = 200
        return

    x = random.Rand((types.WORLD_X << 4) - 800) + 400
    y = random.Rand((types.WORLD_Y << 4) - 200) + 100
    make_sprite(types.TOR, x, y)
    # ClearMes() - message system not implemented

# Legacy API compatibility ----------------------------------------------------

def GenerateTrain(x: int, y: int) -> None:
    """Compatibility wrapper for legacy camel-case API."""
    generate_train(x, y)


def GenerateBus(x: int, y: int) -> None:
    generate_bus(x, y)


def GenerateShip() -> None:
    generate_ship()


def GeneratePlane(x: int, y: int) -> None:
    generate_plane(x, y)


def GenerateCopter(x: int, y: int) -> None:
    generate_copter(x, y)


def MakeExplosion(x: int, y: int) -> None:
    make_explosion(x, y)


def MakeExplosionAt(x: int, y: int) -> None:
    make_explosion_at(x, y)


def GetSprite(sprite_type: int) -> types.SimSprite | None:
    return get_sprite(sprite_type)


def MakeSprite(sprite_type: int, x: int, y: int) -> types.SimSprite:
    return make_sprite(sprite_type, x, y)
    # SendMesAt(-22, (x >> 4) + 3, (y >> 4) + 2)

def make_explosion(x: int, y: int) -> None:
    """
    Create an explosion at the given location.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    if (x >= 0 and x < types.WORLD_X and
        y >= 0 and y < types.WORLD_Y):
        make_explosion_at((x << 4) + 8, (y << 4) + 8)

def make_explosion_at(x: int, y: int) -> None:
    """
    Create an explosion sprite at the given world coordinates.

    Args:
        x: World X coordinate
        y: World Y coordinate
    """
    make_new_sprite(types.EXP, x - 40, y - 16)

# ============================================================================
# Sprite Destruction and Effects
# ============================================================================

def explode_sprite(sprite: types.SimSprite) -> None:
    """
    Explode a sprite and create appropriate effects.

    Args:
        sprite: Sprite to explode
    """
    global CrashX, CrashY

    sprite.frame = 0

    x = sprite.x + sprite.x_hot
    y = sprite.y + sprite.y_hot
    make_explosion_at(x, y)

    x = x >> 4
    y = y >> 4

    if sprite.type == types.AIR:
        CrashX = x
        CrashY = y
        # SendMesAt(-24, x, y)
    elif sprite.type == types.SHI:
        CrashX = x
        CrashY = y
        # SendMesAt(-25, x, y)
    elif sprite.type == types.TRA:
        CrashX = x
        CrashY = y
        # SendMesAt(-26, x, y)
    elif sprite.type == types.COP:
        CrashX = x
        CrashY = y
        # SendMesAt(-27, x, y)
    elif sprite.type == types.BUS:
        CrashX = x
        CrashY = y
        # SendMesAt(-26, x, y)  # XXX for now

    # MakeSound("city", "Explosion-High")
    return

def destroy(x: int, y: int) -> None:
    """
    Destroy tiles at the given location.

    Args:
        x: World X coordinate
        y: World Y coordinate
    """
    tile_x = x >> 4
    tile_y = y >> 4
    if not test_bounds(tile_x, tile_y):
        return
    z = types.Map[tile_x][tile_y]
    t = z & types.LOMASK
    if t >= types.TREEBASE:
        if not (z & types.BURNBIT):
            if ((t >= types.ROADBASE) and (t <= types.LASTROAD)):
                types.Map[tile_x][tile_y] = types.RIVER
            return
        if z & types.ZONEBIT:
            # OFireZone(tile_x, tile_y, z)  # Not implemented yet
            if t > types.RZB:
                make_explosion_at(x, y)
        if check_wet(t):
            types.Map[tile_x][tile_y] = types.RIVER
        else:
            types.Map[tile_x][tile_y] = (types.SOMETINYEXP - 3) | types.BULLBIT | types.ANIMBIT

def check_wet(x: int) -> int:
    """
    Check if tile is a water-related tile.

    Args:
        x: Tile ID

    Returns:
        1 if wet, 0 otherwise
    """
    if ((x == types.POWERBASE) or (x == types.POWERBASE + 1) or
        (x == types.RAILBASE) or (x == types.RAILBASE + 1) or
        (x == types.BRWH) or (x == types.BRWV)):
        return 1
    else:
        return 0

def start_fire(x: int, y: int) -> None:
    """
    Start a fire at the given location.

    Args:
        x: World X coordinate
        y: World Y coordinate
    """
    tile_x = x >> 4
    tile_y = y >> 4
    if ((tile_x >= types.WORLD_X) or (tile_y >= types.WORLD_Y) or
        (tile_x < 0) or (tile_y < 0)):
        return
    z = types.Map[tile_x][tile_y]
    t = z & types.LOMASK
    if ((not (z & types.BURNBIT)) and (t != 0)):
        return
    if z & types.ZONEBIT:
        return
    types.Map[tile_x][tile_y] = types.FIRE + (random.Rand16() & 3) + types.ANIMBIT

# ============================================================================
# Rendering Functions (Pygame Adaptation)
# ============================================================================

def draw_objects(view: types.SimView) -> None:
    """
    Draw all sprites in the view.

    Args:
        view: View to draw sprites in
    """
    sprite = types.sim.sprite if types.sim else None

    # XXX: sort these by layer (not implemented)

    while sprite:
        draw_sprite(view, sprite)
        sprite = sprite.next

def draw_sprite(view: types.SimView, sprite: types.SimSprite) -> None:
    """
    Draw a single sprite in the view.

    Args:
        view: View to draw in
        sprite: Sprite to draw
    """
    if sprite.frame == 0:
        return

    # Calculate screen position (for future pygame rendering)
    x = (sprite.x - ((view.tile_x << 4) - view.screen_x) +  # noqa: F841
         sprite.x_offset)
    y = (sprite.y - ((view.tile_y << 4) - view.screen_y) +  # noqa: F841
         sprite.y_offset)

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
    def __init__(self, sprite: types.SimSprite):
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

def initialize_sprite_system() -> None:
    """
    Initialize the sprite management system.
    """
    global GlobalSprites, FreeSprites, Cycle, CrashX, CrashY

    # Initialize global sprite array
    GlobalSprites = [None] * types.OBJN

    # Clear free sprite pool
    FreeSprites = None

    # Reset cycle counter
    Cycle = 0

    # Reset crash locations
    CrashX = 0
    CrashY = 0

    # Clear all sprites from simulation
    if types.sim:
        types.sim.sprites = 0
        types.sim.sprite = None
