# disasters.py: Disaster simulation system for Micropolis Python port
#
# This module implements the disaster mechanics including fires, floods,
# earthquakes, monster attacks, tornadoes, and nuclear meltdowns.
#
# Original C files: s_disast.c, parts of w_sprite.c, s_sim.c
# Ported to maintain algorithmic fidelity with the original Micropolis simulation

import micropolis.macros as macros
import micropolis.random as random
import micropolis.types as types
import micropolis.utilities

# ============================================================================
# Disaster System Constants
# ============================================================================

# Disaster probability table (chance per simulation step)
DISASTER_CHANCES = [10 * 48, 5 * 48, 60]  # Easy, Medium, Hard


# ============================================================================
# Main Disaster Control Functions
# ============================================================================


def DoDisasters() -> None:
    """
    Main disaster control function called each simulation step.

    Randomly triggers various disasters based on difficulty level and pollution.
    Handles scenario-specific disasters and flood countdown.
    """
    # Decrement flood counter
    if types.flood_cnt:
        types.flood_cnt -= 1

    # Handle scenario disasters
    if types.disaster_event:
        ScenarioDisaster()

    # Get difficulty level (clamp to valid range)
    x = types.game_level
    if x > 2:
        x = 0

    # Skip disasters if disabled
    if types.no_disasters:
        return

    # Random disaster check
    if not random.Rand(DISASTER_CHANCES[x]):
        # Select random disaster type
        disaster_type = random.Rand(8)

        if disaster_type <= 1:
            # Fire disaster
            SetFire()
        elif disaster_type <= 3:
            # Flood disaster
            MakeFlood()
        elif disaster_type == 4:
            # No disaster (skip)
            pass
        elif disaster_type == 5:
            # Tornado disaster
            MakeTornado()
        elif disaster_type == 6:
            # Earthquake disaster
            MakeEarthquake()
        elif disaster_type >= 7:
            # Monster disaster (only if pollution is high)
            if types.pollute_average > 60:  # Original uses /* 80 */ 60
                MakeMonster()


def ScenarioDisaster() -> None:
    """
    Handle scenario-specific disasters.

    Different cities have different disaster scenarios that trigger
    at specific times during gameplay.
    """
    if types.disaster_event == 1:
        # Dullsville - no disaster
        pass
    elif types.disaster_event == 2:
        # San Francisco - earthquake
        if types.disaster_wait == 1:
            MakeEarthquake()
    elif types.disaster_event == 3:
        # Hamburg - fire bombing
        DropFireBombs()
    elif types.disaster_event == 4:
        # Bern - no disaster
        pass
    elif types.disaster_event == 5:
        # Tokyo - monster
        if types.disaster_wait == 1:
            MakeMonster()
    elif types.disaster_event == 6:
        # Detroit - no disaster
        pass
    elif types.disaster_event == 7:
        # Boston - nuclear meltdown
        if types.disaster_wait == 1:
            MakeMeltdown()
    elif types.disaster_event == 8:
        # Rio - periodic floods
        if (types.disaster_wait % 24) == 0:
            MakeFlood()

    # Decrement disaster wait counter
    if types.disaster_wait:
        types.disaster_wait -= 1
    else:
        types.disaster_event = 0


# ============================================================================
# Fire Disaster Functions
# ============================================================================


def SetFire() -> None:
    """
    Start a fire disaster at a random arsonable location.

    Finds a random tile that can burn and sets it on fire.
    """
    for _ in range(40):  # Try up to 40 times to find a suitable location
        x = random.Rand(macros.WORLD_X - 1)
        y = random.Rand(macros.WORLD_Y - 1)
        tile = types.map_data[x][y]

        # Check if tile is arsonable (can be set on fire)
        if not (tile & macros.ZONEBIT):
            tile_base = tile & macros.LOMASK
            if (tile_base > macros.LHTHR) and (tile_base < macros.LASTZONE):
                # Set tile on fire with animation
                types.map_data[x][y] = (
                    macros.FIRE + macros.ANIMBIT + (random.sim_rand() & 7)
                )
                types.crash_x = x
                types.crash_y = y
                # Send disaster message (placeholder - would send to UI)
                # SendMesAt(-20, x, y)
                return


def MakeFire() -> None:
    """
    Create a fire at a random flammable location.

    Alternative fire creation function that looks for tiles that are
    already burning or have burn bits set.
    """
    for _ in range(40):  # Try up to 40 times
        x = random.Rand(macros.WORLD_X - 1)
        y = random.Rand(macros.WORLD_Y - 1)
        tile = types.map_data[x][y]

        # Check for flammable tiles (not zoned, has burn bit set)
        if (not (tile & macros.ZONEBIT)) and (tile & macros.BURNBIT):
            tile_base = tile & macros.LOMASK
            if (tile_base > 21) and (tile_base < macros.LASTZONE):
                # Set tile on fire
                types.map_data[x][y] = (
                    macros.FIRE + macros.ANIMBIT + (random.sim_rand() & 7)
                )
                # Send disaster message (placeholder)
                # SendMesAt(20, x, y)
                return


def FireBomb() -> None:
    """
    Create a fire bomb explosion (used in Hamburg scenario).

    Drops a bomb at a random location causing an explosion.
    """
    types.crash_x = random.Rand(macros.WORLD_X - 1)
    types.crash_y = random.Rand(macros.WORLD_Y - 1)
    MakeExplosion(types.crash_x, types.crash_y)
    # Clear messages and send disaster message (placeholder)
    # ClearMes()
    # SendMesAt(-30, CrashX, CrashY)


def DropFireBombs() -> None:
    """
    Drop multiple fire bombs (Hamburg scenario).

    Creates multiple explosions across the city.
    """
    # Implementation would create multiple fire bombs
    # For now, just drop one as a placeholder
    FireBomb()


# ============================================================================
# Flood Disaster Functions
# ============================================================================


def MakeFlood() -> None:
    """
    Start a flood disaster near a river edge.

    Finds a river edge tile and starts flooding adjacent floodable areas.
    """
    # Direction offsets for checking adjacent tiles
    dx = [0, 1, 0, -1]
    dy = [-1, 0, 1, 0]

    for _ in range(300):  # Try up to 300 times to find river edge
        x = random.Rand(macros.WORLD_X - 1)
        y = random.Rand(macros.WORLD_Y - 1)

        tile = types.map_data[x][y] & macros.LOMASK

        # Check if tile is river edge (tiles 5-20)
        if (tile > 4) and (tile < 21):
            # Check adjacent tiles for floodable areas
            for direction in range(4):
                xx = x + dx[direction]
                yy = y + dy[direction]

                if macros.TestBounds(xx, yy):
                    adjacent_tile = types.map_data[xx][yy]

                    # Check if adjacent tile is floodable
                    # TILE_IS_FLOODABLE: (c == 0) || ((c & BULLBIT) && (c & BURNBIT))
                    if (adjacent_tile == 0) or (
                        (adjacent_tile & macros.BULLBIT)
                        and (adjacent_tile & macros.BURNBIT)
                    ):
                        # Start flood
                        types.map_data[xx][yy] = macros.FLOOD
                        types.flood_cnt = 30
                        # Send disaster message (placeholder)
                        # SendMesAt(-42, xx, yy)
                        types.flood_x = xx
                        types.flood_y = yy
                        return


def DoFlood() -> None:
    """
    Process ongoing flood propagation.

    Called during map scanning to spread floods to adjacent areas.
    """
    if not types.flood_cnt:
        return

    # Direction offsets
    dx = [0, 1, 0, -1]
    dy = [-1, 0, 1, 0]

    # Spread flood to adjacent tiles (25% chance per direction)
    for direction in range(4):
        if not (random.sim_rand() & 7):  # 1/8 chance
            xx = types.s_map_x + dx[direction]
            yy = types.s_map_y + dy[direction]

            if macros.TestBounds(xx, yy):
                tile = types.map_data[xx][yy]
                tile_base = tile & macros.LOMASK

                # Check if tile is floodable
                # TILE_IS_FLOODABLE2: (c & BURNBIT) || (c == 0) || ((t >= WOODS5) && (t < FLOOD))
                floodable = (
                    (tile & macros.BURNBIT)
                    or (tile == 0)
                    or ((tile_base >= macros.WOODS5) and (tile_base < macros.FLOOD))
                )

                if floodable:
                    if tile & macros.ZONEBIT:
                        # Fire zone if it's a zoned building
                        FireZone(xx, yy, tile)
                    # Set flood tile with random variation
                    types.map_data[xx][yy] = macros.FLOOD + random.Rand(2)
    else:
        # Random chance to clear flood (1/16 chance)
        if not (random.sim_rand() & 15):
            types.map_data[types.s_map_x][types.s_map_y] = 0


# ============================================================================
# Earthquake Disaster Functions
# ============================================================================


def MakeEarthquake() -> None:
    """
    Trigger an earthquake disaster.

    Damages random buildings across the city, turning them into rubble or fire.
    """
    # Trigger earthquake effect (placeholder - would shake screen)
    DoEarthQuake()

    # Send disaster message (placeholder)
    # SendMesAt(-23, CCx, CCy)

    # Calculate damage duration based on random time
    time = random.Rand(700) + 300

    # Damage random tiles
    for z in range(time):
        x = random.Rand(macros.WORLD_X - 1)
        y = random.Rand(macros.WORLD_Y - 1)

        # Skip out of bounds (shouldn't happen with Rand range, but safety check)
        if (x < 0) or (x >= macros.WORLD_X) or (y < 0) or (y >= macros.WORLD_Y):
            continue

        # Check if tile is vulnerable to earthquake damage
        if Vunerable(types.map_data[x][y]):
            if z & 0x3:  # 75% chance
                # Turn into rubble
                types.map_data[x][y] = (macros.RUBBLE + macros.BULLBIT) + (
                    random.sim_rand() & 3
                )
            else:  # 25% chance
                # Set on fire
                types.map_data[x][y] = (
                    macros.FIRE + macros.ANIMBIT + (random.sim_rand() & 7)
                )


def Vunerable(tile: int) -> bool:
    """
    Check if a tile is vulnerable to earthquake damage.

    Args:
        tile: Tile ID with status bits

    Returns:
        True if tile can be damaged by earthquake, False otherwise
    """
    tile_base = tile & macros.LOMASK

    # Not vulnerable if below residential base or above last zone
    if (tile_base < macros.RESBASE) or (tile_base > macros.LASTZONE):
        return False

    # Not vulnerable if zoned (already developed)
    if tile & macros.ZONEBIT:
        return False

    return True


def DoEarthQuake() -> None:
    """
    Trigger earthquake visual effect.

    In original game, this would shake the screen and play sound.
    For Python port, this is a placeholder.
    """
    # Placeholder - would trigger screen shake and sound
    # MakeSound("city", "Explosion-Low")
    # Eval("UIEarthQuake")
    types.shake_now += 1
    # Earthquake timer handling would go here


# ============================================================================
# Monster Disaster Functions
# ============================================================================


def MakeMonster() -> None:
    """
    Spawn a monster (Godzilla) disaster.

    Creates or redirects a monster sprite to attack the city.
    """
    # Try to reuse existing monster sprite
    sprite = micropolis.utilities.GetSprite()
    if sprite and sprite.type == macros.GOD:
        sprite.sound_count = 1
        sprite.count = 1000
        sprite.dest_x = types.pol_max_x << 4
        sprite.dest_y = types.pol_max_y << 4
        return

    # Find suitable spawning location near river
    for _ in range(300):
        x = random.Rand(macros.WORLD_X - 20) + 10
        y = random.Rand(macros.WORLD_Y - 10) + 5

        # Check for river tile
        tile = types.map_data[x][y]
        if (tile == macros.RIVER) or (tile == (macros.RIVER + macros.BULLBIT)):
            MonsterHere(x, y)
            return

    # Fallback location if no river found
    MonsterHere(60, 50)


def MonsterHere(x: int, y: int) -> None:
    """
    Spawn monster at specific location.

    Args:
        x: World X coordinate
        y: World Y coordinate
    """
    # Create monster sprite
    sprite = micropolis.utilities.MakeNewSprite()
    if sprite:
        sprite.type = macros.GOD
        sprite.x = (x << 4) + 48
        sprite.y = y << 4
        # Clear messages and send disaster message (placeholder)
        # ClearMes()
        # SendMesAt(-21, x + 5, y)


# ============================================================================
# Tornado Disaster Functions
# ============================================================================


def MakeTornado() -> None:
    """
    Spawn a tornado disaster.

    Creates or redirects a tornado sprite to damage the city.
    """
    # Try to reuse existing tornado sprite
    sprite = micropolis.utilities.GetSprite()
    if sprite and sprite.type == macros.TOR:
        sprite.count = 200
        return

    # Generate random position for tornado
    x = random.Rand((macros.WORLD_X << 4) - 800) + 400
    y = random.Rand((macros.WORLD_Y << 4) - 200) + 100

    # Create tornado sprite
    sprite = micropolis.utilities.MakeNewSprite()
    if sprite:
        sprite.type = macros.TOR
        sprite.x = x
        sprite.y = y
        # Clear messages and send disaster message (placeholder)
        # ClearMes()
        # SendMesAt(-22, (x >> 4) + 3, (y >> 4) + 2)


# ============================================================================
# Nuclear Meltdown Functions
# ============================================================================


def MakeMeltdown() -> None:
    """
    Trigger a nuclear meltdown disaster.

    Finds a nuclear power plant and causes it to meltdown.
    """
    # Search for nuclear power plant
    for x in range(macros.WORLD_X - 1):
        for y in range(macros.WORLD_Y - 1):
            tile = types.map_data[x][y] & macros.LOMASK
            if tile == macros.NUCLEAR:
                DoMeltdown(x, y)
                return


def DoMeltdown(sx: int, sy: int) -> None:
    """
    Execute nuclear meltdown at specified location.

    Args:
        sx: World X coordinate of nuclear plant
        sy: World Y coordinate of nuclear plant
    """
    # Record meltdown location
    types.melt_x = sx
    types.melt_y = sy

    # Create explosions around the plant
    MakeExplosion(sx - 1, sy - 1)
    MakeExplosion(sx - 1, sy + 2)
    MakeExplosion(sx + 2, sy - 1)
    MakeExplosion(sx + 2, sy + 2)

    # Set central area on fire
    for x in range(sx - 1, sx + 3):
        for y in range(sy - 1, sy + 3):
            if macros.TestBounds(x, y):
                types.map_data[x][y] = (
                    macros.FIRE + (random.sim_rand() & 3) + macros.ANIMBIT
                )

    # Spread radiation to surrounding area
    for _ in range(200):
        x = sx - 20 + random.Rand(40)
        y = sy - 15 + random.Rand(30)

        if not macros.TestBounds(x, y):
            continue

        tile = types.map_data[x][y]

        # Skip zoned areas
        if tile & macros.ZONEBIT:
            continue

        # Convert burnable or empty tiles to radiation
        if (tile & macros.BURNBIT) or (tile == 0):
            types.map_data[x][y] = macros.RADTILE

    # Send disaster message (placeholder)
    # ClearMes()
    # SendMesAt(-43, sx, sy)


# ============================================================================
# Explosion Functions
# ============================================================================


def MakeExplosion(x: int, y: int) -> None:
    """
    Create an explosion at the specified location.

    Args:
        x: World X coordinate
        y: World Y coordinate
    """
    if (x >= 0) and (x < macros.WORLD_X) and (y >= 0) and (y < macros.WORLD_Y):
        MakeExplosionAt((x << 4) + 8, (y << 4) + 8)


def MakeExplosionAt(x: int, y: int) -> None:
    """
    Create an explosion sprite at pixel coordinates.

    Args:
        x: Pixel X coordinate
        y: Pixel Y coordinate
    """
    # Create explosion sprite
    sprite = micropolis.utilities.MakeNewSprite()
    if sprite:
        sprite.type = macros.EXP
        sprite.x = x - 40
        sprite.y = y - 16


# ============================================================================
# Zone Fire Functions
# ============================================================================


def FireZone(x_loc: int, y_loc: int, ch: int) -> None:
    """
    Handle fire damage to a zone/building.

    Reduces zone effectiveness and bulldozes roads around the affected area.

    Args:
        x_loc: World X coordinate
        y_loc: World Y coordinate
        ch: Tile value
    """
    # Reduce zone rating (downsampled to 8x8 grid)
    rate_x = x_loc >> 3
    rate_y = y_loc >> 3
    if rate_x < 15 and rate_y < 13:  # Bounds check
        types.rate_og_mem[rate_x][rate_y] -= 20

    # Determine bulldoze area size based on building type
    ch_base = ch & macros.LOMASK
    if ch_base < macros.PORTBASE:
        xy_max = 2
    elif ch_base == macros.AIRPORT:
        xy_max = 5
    else:
        xy_max = 4

    # Bulldoze roads around the building
    for x in range(-1, xy_max):
        for y in range(-1, xy_max):
            xx = x_loc + x
            yy = y_loc + y

            if macros.TestBounds(xx, yy):
                tile = types.map_data[xx][yy] & macros.LOMASK
                # Bulldoze roads (ROADBASE and above)
                if tile >= macros.ROADBASE:
                    types.map_data[xx][yy] |= macros.BULLBIT
