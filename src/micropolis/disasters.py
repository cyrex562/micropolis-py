# disasters.py: Disaster simulation system for Micropolis Python port
#
# This module implements the disaster mechanics including fires, floods,
# earthquakes, monster attacks, tornadoes, and nuclear meltdowns.
#
# Original C files: s_disast.c, parts of w_sprite.c, s_sim.c
# Ported to maintain algorithmic fidelity with the original Micropolis simulation
from src.micropolis.constants import WORLD_X, WORLD_Y, ZONEBIT, LOMASK, LHTHR, LASTZONE, FIRE, ANIMBIT, BURNBIT, \
    BULLBIT, FLOOD, WOODS5, RUBBLE, RESBASE, GOD, RIVER, NUCLEAR, TOR, RADTILE, EXP, PORTBASE, AIRPORT, ROADBASE
from src.micropolis.context import AppContext
from src.micropolis.macros import TestBounds
from src.micropolis.simulation import rand
from src.micropolis.utilities import GetSprite, MakeNewSprite

# ============================================================================
# Disaster System Constants
# ============================================================================

# Disaster probability table (chance per simulation step)
DISASTER_CHANCES = [10 * 48, 5 * 48, 60]  # Easy, Medium, Hard


# ============================================================================
# Main Disaster Control Functions
# ============================================================================


def do_disasters(context: AppContext) -> None:
    """
    ported from DoDisasters
    Main disaster control function called each simulation step.

    Randomly triggers various disasters based on difficulty level and pollution.
    Handles scenario-specific disasters and flood countdown.
    :param context: 
    """
    # Decrement flood counter
    if context.flood_cnt:
        context.flood_cnt -= 1

    # Handle scenario disasters
    if context.disaster_event:
        scenario_disaster(context)

    # Get difficulty level (clamp to valid range)
    x = context.game_level
    if x > 2:
        x = 0

    # Skip disasters if disabled
    if context.no_disasters:
        return

    # Random disaster check
    if not rand(context, DISASTER_CHANCES[x]):
        # Select random disaster type
        disaster_type = rand(context, 8)

        if disaster_type <= 1:
            # Fire disaster
            set_fire(context)
        elif disaster_type <= 3:
            # Flood disaster
            start_flood_disaster(context)
        elif disaster_type == 4:
            # No disaster (skip)
            pass
        elif disaster_type == 5:
            # Tornado disaster
            spawn_tornado_disaster()
        elif disaster_type == 6:
            # Earthquake disaster
            trigger_earthquake_disaster(context)
        elif disaster_type >= 7:
            # Monster disaster (only if pollution is high)
            if context.pollute_average > 60:  # Original uses /* 80 */ 60
                spawn_monster_disaster(context)


def scenario_disaster(context: AppContext) -> None:
    """
    ported from ScenarioDisaster
    Handle scenario-specific disasters.

    Different cities have different disaster scenarios that trigger
    at specific times during gameplay.
    :param context: 
    """
    if context.disaster_event == 1:
        # Dullsville - no disaster
        pass
    elif context.disaster_event == 2:
        # San Francisco - earthquake
        if context.disaster_wait == 1:
            trigger_earthquake_disaster(context)
    elif context.disaster_event == 3:
        # Hamburg - fire bombing
        drop_fire_bombs(context)
    elif context.disaster_event == 4:
        # Bern - no disaster
        pass
    elif context.disaster_event == 5:
        # Tokyo - monster
        if context.disaster_wait == 1:
            spawn_monster_disaster(context)
    elif context.disaster_event == 6:
        # Detroit - no disaster
        pass
    elif context.disaster_event == 7:
        # Boston - nuclear meltdown
        if context.disaster_wait == 1:
            trigger_nuclear_meltdown(context)
    elif context.disaster_event == 8:
        # Rio - periodic floods
        if (context.disaster_wait % 24) == 0:
            start_flood_disaster(context)

    # Decrement disaster wait counter
    if context.disaster_wait:
        context.disaster_wait -= 1
    else:
        context.disaster_event = 0


# ============================================================================
# Fire Disaster Functions
# ============================================================================


def set_fire(context: AppContext) -> None:
    """
    ported from SetFire
    Start a fire disaster at a random arsonable location.

    Finds a random tile that can burn and sets it on fire.
    :param context:
    """
    for _ in range(40):  # Try up to 40 times to find a suitable location
        x = rand(context, WORLD_X - 1)
        y = rand(context, WORLD_Y - 1)
        tile = context.map_data[x][y]

        # Check if tile is arsonable (can be set on fire)
        if not (tile & ZONEBIT):
            tile_base = tile & LOMASK
            if (tile_base > LHTHR) and (tile_base < LASTZONE):
                # Set tile on fire with animation
                context.map_data[x][y] = (
                    FIRE + ANIMBIT + (context.sim_rand() & 7)
                )
                context.crash_x = x
                context.crash_y = y
                # Send disaster message (placeholder - would send to UI)
                # SendMesAt(-20, x, y)
                return


def create_fire_disaster(context: AppContext) -> None:
    """
    ported from MakeFire
    Create a fire at a random flammable location.

    Alternative fire creation function that looks for tiles that are
    already burning or have burn bits set.
    :param context:
    """
    for _ in range(40):  # Try up to 40 times
        x = rand(context, WORLD_X - 1)
        y = rand(context, WORLD_Y - 1)
        tile = context.map_data[x][y]

        # Check for flammable tiles (not zoned, has burn bit set)
        if (not (tile & ZONEBIT)) and (tile & BURNBIT):
            tile_base = tile & LOMASK
            if (tile_base > 21) and (tile_base < LASTZONE):
                # Set tile on fire
                context.map_data[x][y] = (
                    FIRE + ANIMBIT + (context.sim_rand() & 7)
                )
                # Send disaster message (placeholder)
                # SendMesAt(20, x, y)
                return


def create_fire_bomb_explosion(context: AppContext) -> None:
    """
    ported from FireBomb
    Create a fire bomb explosion (used in Hamburg scenario).

    Drops a bomb at a random location causing an explosion.
    :param context:
    """
    context.crash_x = rand(context, WORLD_X - 1)
    context.crash_y = rand(context, WORLD_Y - 1)
    create_explosion(context.crash_x, context.crash_y)
    # Clear messages and send disaster message (placeholder)
    # ClearMes()
    # SendMesAt(-30, CrashX, CrashY)


def drop_fire_bombs(context: AppContext) -> None:
    """
    ported from DropFireBombs
    Drop multiple fire bombs (Hamburg scenario).

    Creates multiple explosions across the city.
    :param context:
    """
    # Implementation would create multiple fire bombs
    # For now, just drop one as a placeholder
    create_fire_bomb_explosion(context)


# ============================================================================
# Flood Disaster Functions
# ============================================================================


def start_flood_disaster(context: AppContext) -> None:
    """
    ported from MakeFlood
    Start a flood disaster near a river edge.

    Finds a river edge tile and starts flooding adjacent floodable areas.
    :param context:
    """
    # Direction offsets for checking adjacent tiles
    dx = [0, 1, 0, -1]
    dy = [-1, 0, 1, 0]

    for _ in range(300):  # Try up to 300 times to find river edge
        x = rand(context, WORLD_X - 1)
        y = rand(context, WORLD_Y - 1)

        tile = context.map_data[x][y] & LOMASK

        # Check if tile is river edge (tiles 5-20)
        if (tile > 4) and (tile < 21):
            # Check adjacent tiles for floodable areas
            for direction in range(4):
                xx = x + dx[direction]
                yy = y + dy[direction]

                if TestBounds(xx, yy):
                    adjacent_tile = context.map_data[xx][yy]

                    # Check if adjacent tile is floodable
                    # TILE_IS_FLOODABLE: (c == 0) || ((c & BULLBIT) && (c & BURNBIT))
                    if (adjacent_tile == 0) or (
                        (adjacent_tile & BULLBIT)
                        and (adjacent_tile & BURNBIT)
                    ):
                        # Start flood
                        context.map_data[xx][yy] = FLOOD
                        context.flood_cnt = 30
                        # Send disaster message (placeholder)
                        # SendMesAt(-42, xx, yy)
                        context.flood_x = xx
                        context.flood_y = yy
                        return


def do_flood(context: AppContext) -> None:
    """
    ported from DoFlood
    Process ongoing flood propagation.

    Called during map scanning to spread floods to adjacent areas.
    :param context:
    """
    if not context.flood_cnt:
        return

    # Direction offsets
    dx = [0, 1, 0, -1]
    dy = [-1, 0, 1, 0]

    # Spread flood to adjacent tiles (25% chance per direction)
    for direction in range(4):
        if not (context.sim_rand() & 7):  # 1/8 chance
            xx = context.s_map_x + dx[direction]
            yy = context.s_map_y + dy[direction]

            if TestBounds(xx, yy):
                tile = context.map_data[xx][yy]
                tile_base = tile & LOMASK

                # Check if tile is floodable
                # TILE_IS_FLOODABLE2: (c & BURNBIT) || (c == 0) || ((t >= WOODS5) && (t < FLOOD))
                floodable = (
                    (tile & BURNBIT)
                    or (tile == 0)
                    or ((tile_base >= WOODS5) and (tile_base < FLOOD))
                )

                if floodable:
                    if tile & ZONEBIT:
                        # Fire zone if it's a zoned building
                        fire_zone(context, xx, yy, tile)
                    # Set flood tile with random variation
                    context.map_data[xx][yy] = FLOOD + rand(context, 2)
    else:
        # Random chance to clear flood (1/16 chance)
        if not (context.sim_rand() & 15):
            context.map_data[context.s_map_x][context.s_map_y] = 0


# ============================================================================
# Earthquake Disaster Functions
# ============================================================================


def trigger_earthquake_disaster(context: AppContext) -> None:
    """
    ported from MakeEarthquake
    Trigger an earthquake disaster.

    Damages random buildings across the city, turning them into rubble or fire.
    :param context:
    """
    # Trigger earthquake effect (placeholder - would shake screen)
    do_earth_quake(context)

    # Send disaster message (placeholder)
    # SendMesAt(-23, CCx, CCy)

    # Calculate damage duration based on random time
    time = rand(context, 700) + 300

    # Damage random tiles
    for z in range(time):
        x = rand(context, WORLD_X - 1)
        y = rand(context, WORLD_Y - 1)

        # Skip out of bounds (shouldn't happen with Rand range, but safety check)
        if (x < 0) or (x >= WORLD_X) or (y < 0) or (y >= WORLD_Y):
            continue

        # Check if tile is vulnerable to earthquake damage
        if vulnerable(context.map_data[x][y]):
            if z & 0x3:  # 75% chance
                # Turn into rubble
                context.map_data[x][y] = (RUBBLE + BULLBIT) + (
                    context.sim_rand() & 3
                )
            else:  # 25% chance
                # Set on fire
                context.map_data[x][y] = (
                    FIRE + ANIMBIT + (context.sim_rand() & 7)
                )


def vulnerable(tile: int) -> bool:
    """
    ported from Vunerable
    Check if a tile is vulnerable to earthquake damage.

    Args:
        tile: Tile ID with status bits

    Returns:
        True if tile can be damaged by earthquake, False otherwise
    """
    tile_base = tile & LOMASK

    # Not vulnerable if below residential base or above last zone
    if (tile_base < RESBASE) or (tile_base > LASTZONE):
        return False

    # Not vulnerable if zoned (already developed)
    if tile & ZONEBIT:
        return False

    return True


def do_earth_quake(context: AppContext) -> None:
    """
    ported from DoEarthQuake

    Trigger earthquake visual effect.

    In original game, this would shake the screen and play sound.
    For Python port, this is a placeholder.
    :param context:
    """
    # Placeholder - would trigger screen shake and sound
    # MakeSound("city", "Explosion-Low")
    # Eval("UIEarthQuake")
    context.shake_now += 1
    # Earthquake timer handling would go here


# ============================================================================
# Monster Disaster Functions
# ============================================================================


def spawn_monster_disaster(context: AppContext) -> None:
    """
    ported from MakeMonster
    Spawn a monster (Godzilla) disaster.

    Creates or redirects a monster sprite to attack the city.
    :param context:
    """
    # Try to reuse existing monster sprite
    sprite = GetSprite()
    if sprite and sprite.type == GOD:
        sprite.sound_count = 1
        sprite.count = 1000
        sprite.dest_x = context.pol_max_x << 4
        sprite.dest_y = context.pol_max_y << 4
        return

    # Find suitable spawning location near river
    for _ in range(300):
        x = rand(context, WORLD_X - 20) + 10
        y = rand(context, WORLD_Y - 10) + 5

        # Check for river tile
        tile = context.map_data[x][y]
        if (tile == RIVER) or (tile == (RIVER + BULLBIT)):
            monster_here(x, y)
            return

    # Fallback location if no river found
    monster_here(60, 50)


def monster_here(x: int, y: int) -> None:
    """
    ported from MonsterHere
    Spawn monster at specific location.

    Args:
        x: World X coordinate
        y: World Y coordinate
    """
    # Create monster sprite
    sprite = MakeNewSprite()
    if sprite:
        sprite.type = GOD
        sprite.x = (x << 4) + 48
        sprite.y = y << 4
        # Clear messages and send disaster message (placeholder)
        # ClearMes()
        # SendMesAt(-21, x + 5, y)


# ============================================================================
# Tornado Disaster Functions
# ============================================================================


def spawn_tornado_disaster() -> None:
    """
    ported from MakeTornado
    Spawn a tornado disaster.

    Creates or redirects a tornado sprite to damage the city.
    """
    # Try to reuse existing tornado sprite
    sprite = GetSprite()
    if sprite and sprite.type == TOR:
        sprite.count = 200
        return

    # Generate random position for tornado
    x = rand(context, (WORLD_X << 4) - 800) + 400
    y = rand(context, (WORLD_Y << 4) - 200) + 100

    # Create tornado sprite
    sprite = MakeNewSprite()
    if sprite:
        sprite.type = TOR
        sprite.x = x
        sprite.y = y
        # Clear messages and send disaster message (placeholder)
        # ClearMes()
        # SendMesAt(-22, (x >> 4) + 3, (y >> 4) + 2)


# ============================================================================
# Nuclear Meltdown Functions
# ============================================================================


def trigger_nuclear_meltdown(context: AppContext) -> None:
    """
    ported from MakeMeltdown
    Trigger a nuclear meltdown disaster.

    Finds a nuclear power plant and causes it to meltdown.
    :param context:
    """
    # Search for nuclear power plant
    for x in range(WORLD_X - 1):
        for y in range(WORLD_Y - 1):
            tile = context.map_data[x][y] & LOMASK
            if tile == NUCLEAR:
                do_meltdown(context, x, y)
                return


def do_meltdown(context: AppContext, sx: int, sy: int) -> None:
    """
    ported from DoMeltdown
    Execute nuclear meltdown at specified location.

    Args:
        sx: World X coordinate of nuclear plant
        sy: World Y coordinate of nuclear plant
        :param context:
    """
    # Record meltdown location
    context.melt_x = sx
    context.melt_y = sy

    # Create explosions around the plant
    create_explosion(sx - 1, sy - 1)
    create_explosion(sx - 1, sy + 2)
    create_explosion(sx + 2, sy - 1)
    create_explosion(sx + 2, sy + 2)

    # Set central area on fire
    for x in range(sx - 1, sx + 3):
        for y in range(sy - 1, sy + 3):
            if TestBounds(x, y):
                context.map_data[x][y] = (
                    FIRE + (context.sim_rand() & 3) + ANIMBIT
                )

    # Spread radiation to surrounding area
    for _ in range(200):
        x = sx - 20 + rand(context, 40)
        y = sy - 15 + rand(context, 30)

        if not TestBounds(x, y):
            continue

        tile = context.map_data[x][y]

        # Skip zoned areas
        if tile & ZONEBIT:
            continue

        # Convert burnable or empty tiles to radiation
        if (tile & BURNBIT) or (tile == 0):
            context.map_data[x][y] = RADTILE

    # Send disaster message (placeholder)
    # ClearMes()
    # SendMesAt(-43, sx, sy)


# ============================================================================
# Explosion Functions
# ============================================================================


def create_explosion(x: int, y: int) -> None:
    """
    ported from MakeExplosion
    Create an explosion at the specified location.

    Args:
        x: World X coordinate
        y: World Y coordinate
    """
    if (x >= 0) and (x < WORLD_X) and (y >= 0) and (y < WORLD_Y):
        make_explosion_at((x << 4) + 8, (y << 4) + 8)


def make_explosion_at(x: int, y: int) -> None:
    """
    ported from MakeExplosionAt
    Create an explosion sprite at pixel coordinates.

    Args:
        x: Pixel X coordinate
        y: Pixel Y coordinate
    """
    # Create explosion sprite
    sprite = MakeNewSprite()
    if sprite:
        sprite.type = EXP
        sprite.x = x - 40
        sprite.y = y - 16


# ============================================================================
# Zone Fire Functions
# ============================================================================


def fire_zone(context: AppContext, x_loc: int, y_loc: int, ch: int) -> None:
    """
    ported to FireZone
    Handle fire damage to a zone/building.

    Reduces zone effectiveness and bulldozes roads around the affected area.

    Args:
        x_loc: World X coordinate
        y_loc: World Y coordinate
        ch: Tile value
        :param context:
    """
    # Reduce zone rating (downsampled to 8x8 grid)
    rate_x = x_loc >> 3
    rate_y = y_loc >> 3
    if rate_x < 15 and rate_y < 13:  # Bounds check
        context.rate_og_mem[rate_x][rate_y] -= 20

    # Determine bulldoze area size based on building type
    ch_base = ch & LOMASK
    if ch_base < PORTBASE:
        xy_max = 2
    elif ch_base == AIRPORT:
        xy_max = 5
    else:
        xy_max = 4

    # Bulldoze roads around the building
    for x in range(-1, xy_max):
        for y in range(-1, xy_max):
            xx = x_loc + x
            yy = y_loc + y

            if TestBounds(xx, yy):
                tile = context.map_data[xx][yy] & LOMASK
                # Bulldoze roads (ROADBASE and above)
                if tile >= ROADBASE:
                    context.map_data[xx][yy] |= BULLBIT
