"""
tools.py - Tool selection and application system for Micropolis Python port

This module implements the tool system ported from w_tool.c, providing
the core gameplay mechanics for placing buildings, infrastructure, and
interacting with the city map.

The tool system includes:
- Building placement tools (residential, commercial, industrial zones)
- Infrastructure tools (roads, rails, power lines)
- Service buildings (police, fire stations, stadium, etc.)
- Special tools (parks, airports, seaports, nuclear plants)
- Query tool for zone information
- Bulldozer tool for demolition
- Drawing tools (chalk, eraser) for annotations
- Network/telecommunications tool

Ported from w_tool.c with pygame integration.
"""

from dataclasses import dataclass

import micropolis.constants
import micropolis.sim_view

from . import macros, messages, random, types

# ============================================================================
# Tool State Constants (from w_tool.c)
# ============================================================================

# Tool state enumeration
residentialState = 0
commercialState = 1
industrialState = 2
fireState = 3
queryState = 4
policeState = 5
wireState = 6
dozeState = 7
rrState = 8
roadState = 9
chalkState = 10
eraserState = 11
stadiumState = 12
parkState = 13
seaportState = 14
powerState = 15
nuclearState = 16
airportState = 17
networkState = 18

# Tool state range
firstState = residentialState
lastState = networkState

# ============================================================================
# Tool Configuration Arrays (from w_tool.c)
# ============================================================================

# Cost of each tool
CostOf: list[int] = [
    100,
    100,
    100,
    500,  # residential, commercial, industrial, fire
    0,
    500,
    5,
    1,  # query, police, wire, bulldoze
    20,
    10,
    0,
    0,  # rail, road, chalk, eraser
    5000,
    10,
    3000,
    3000,  # stadium, park, seaport, coal power
    5000,
    10000,
    100,  # nuclear, airport, network
]

# Size of each tool (radius from center)
toolSize: list[int] = [
    3,
    3,
    3,
    3,  # residential, commercial, industrial, fire (3x3)
    1,
    3,
    1,
    1,  # query, police, wire, bulldoze (1x1 or 3x3)
    1,
    1,
    0,
    0,  # rail, road, chalk, eraser (1x1 or freeform)
    4,
    1,
    4,
    4,  # stadium, park, seaport, coal power (4x4)
    4,
    6,
    1,
    0,  # nuclear, airport, network (4x4, 6x6, 1x1)
]

# Offset from map coordinates to tool center
toolOffset: list[int] = [
    1,
    1,
    1,
    1,  # residential, commercial, industrial, fire
    0,
    1,
    0,
    0,  # query, police, wire, bulldoze
    0,
    0,
    0,
    0,  # rail, road, chalk, eraser
    1,
    0,
    1,
    1,  # stadium, park, seaport, coal power
    1,
    1,
    0,
    0,  # nuclear, airport, network
]

# Tool colors for overlay display (RGB pairs)
toolColors: list[int] = [
    0x00FF00,
    0x00FFFF,
    0xFFFF00,
    0x00FF00,  # residential (green), commercial (cyan), industrial (yellow), fire (green/red)
    0xFF8000,
    0x00FF00,
    0x808080,
    0x808080,  # query (orange), police (green/cyan), wire (gray/yellow), bulldoze (brown/gray)
    0x808080,
    0xFFFFFF,
    0xC0C0C0,
    0x808080,  # rail (gray/olive), road (gray/white), chalk (gray/gray), eraser (gray/gray)
    0xC0C0FF,
    0x806040,
    0xC0C0FF,
    0xC0C0FF,  # stadium (gray/green), park (brown/green), seaport (gray/blue), power (gray/yellow)
    0xC0C0FF,
    0xC0C0FF,
    0xC0C0FF,
    0xFF0000,  # nuclear (gray/yellow), airport (gray/brown), network (gray/red), (unused)
]

# ============================================================================
# Global Variables (from w_tool.c)
# ============================================================================

specialBase: int = types.CHURCH
OverRide: int = 0
Expensive: int = 1000
Players: int = 1
Votes: int = 0
PendingTool: int = -1
PendingX: int = 0
PendingY: int = 0

# ============================================================================
# Utility Functions
# ============================================================================


def Spend(amount: int) -> None:
    """
    Deduct funds from city treasury.

    Args:
        amount: Amount to spend
    """
    types.total_funds -= amount


def MakeSound(channel: str, sound_name: str) -> None:
    """
    Play a sound effect.

    Args:
        channel: Sound channel ("city", "edit", etc.)
        sound_name: Name of sound to play
    """
    messages.make_sound(channel, sound_name)


def MakeSoundOn(
    view: "micropolis.sim_view.SimView", channel: str, sound_name: str
) -> None:
    """
    Play a sound effect if view has sound enabled.

    Args:
        view: View that triggered the sound
        channel: Sound channel
        sound_name: Name of sound to play
    """
    if view.sound:
        MakeSound(channel, sound_name)


def ConnecTile(x: int, y: int, tile_ptr: list[int], command: int) -> int:
    """
    Connect infrastructure tiles (roads, rails, power lines).

    This is a placeholder implementation. The actual connection logic
    should be implemented based on the tile connection algorithms.

    Args:
        x: X coordinate
        y: Y coordinate
        tile_ptr: Reference to tile value (modified in place)
        command: Connection command (2=road, 3=rail, 4=wire)

    Returns:
        1 if successful, 0 if failed
    """
    # Placeholder - need to implement actual connection logic
    # For now, just place the tile without connection logic
    if not macros.TestBounds(x, y):
        return 0

    current_tile = types.map_data[x][y] & types.LOMASK

    # Simple connection logic placeholder
    if command == 2:  # Road
        if current_tile == 0:  # Empty tile
            types.map_data[x][y] = types.ROADBASE | types.BNCNBIT
            Spend(CostOf[roadState])
            return 1
    elif command == 3:  # Rail
        if current_tile == 0:  # Empty tile
            types.map_data[x][y] = types.RAILBASE | types.BNCNBIT
            Spend(CostOf[rrState])
            return 1
    elif command == 4:  # Wire
        if current_tile == 0:  # Empty tile
            types.map_data[x][y] = types.POWERBASE | types.BNCNBIT | types.CONDBIT
            Spend(CostOf[wireState])
            return 1

    return 0


def tally(tileValue: int) -> int:
    """
    Check if a tile can be auto-bulldozed.

    Determines if a tile contains bulldozable infrastructure that can be
    automatically cleared when placing new buildings.

    Args:
        tileValue: Tile value to check

    Returns:
        1 if tile can be auto-bulldozed, 0 otherwise
    """
    tile_base = tileValue & types.LOMASK

    # Can bulldoze: rivers, trees, rubble, flood, radioactive waste, fire, roads
    bulldozable_ranges = [
        (types.FIRSTRIVEDGE, types.LASTRIVEDGE),  # Rivers and edges
        (types.TREEBASE, types.LASTTREE),  # Trees
        (types.RUBBLE, types.LASTRUBBLE),  # Rubble
        (types.FLOOD, types.LASTFLOOD),  # Flood water
        (types.RADTILE, types.RADTILE),  # Radioactive waste
        (types.FIRE, types.LASTFIRE),  # Fire
        (types.ROADBASE, types.LASTROAD),  # Roads
    ]

    # Check power lines (specific ranges)
    if (tile_base >= (types.POWERBASE + 2) and tile_base <= (types.POWERBASE + 12)) or (
        tile_base >= types.TINYEXP and tile_base <= (types.LASTTINYEXP + 2)
    ):
        return 1

    # Check bulldozable ranges
    for start, end in bulldozable_ranges:
        if tile_base >= start and tile_base <= end:
            return 1

    return 0


def checkSize(temp: int) -> int:
    """
    Check the size category of a building tile.

    Determines if a tile represents a 3x3 zone, 4x4 building, or other size.

    Args:
        temp: Tile base value

    Returns:
        3 for 3x3 zones, 4 for 4x4 buildings, 0 for other sizes
    """
    # 3x3 zones: residential, commercial, industrial, fire dept, police dept
    if (temp >= (types.RESBASE - 1) and temp <= (types.PORTBASE - 1)) or (
        temp >= (types.LASTPOWERPLANT + 1) and temp <= (types.POLICESTATION + 4)
    ):
        return 3

    # 4x4 buildings: seaports, coal/nuclear plants, stadium
    if (
        (temp >= types.PORTBASE and temp <= types.LASTPORT)
        or (temp >= types.COALBASE and temp <= types.LASTPOWERPLANT)
        or (temp >= types.STADIUMBASE and temp <= types.LASTZONE)
    ):
        return 4

    return 0


def checkBigZone(tile_id: int, deltaHPtr: list[int], deltaVPtr: list[int]) -> int:
    """
    Check if tile is part of a large building and get offset to center.

    For large buildings like airports and power plants, determines the size
    and offset from the clicked tile to the building center.

    Args:
        tile_id: Tile ID to check
        deltaHPtr: Modified to contain horizontal offset to center
        deltaVPtr: Modified to contain vertical offset to center

    Returns:
        Building size (4 or 6), or 0 if not a large building
    """
    deltaHPtr[0] = 0
    deltaVPtr[0] = 0

    # 4x4 buildings: coal plant, seaport, nuclear plant, stadium
    four_by_four = [
        (types.POWERPLANT, 0, 0),
        (types.PORT, 0, 0),
        (types.NUCLEAR, 0, 0),
        (types.STADIUM, 0, 0),
        # Additional tiles within 4x4 buildings
        (types.POWERPLANT + 1, -1, 0),
        (types.COALSMOKE3, -1, 0),  # Coal plant smoke
        (types.COALSMOKE3 + 1, -1, 0),
        (types.COALSMOKE3 + 2, -1, 0),
        (types.PORT + 1, -1, 0),
        (types.NUCLEAR + 1, -1, 0),
        (types.STADIUM + 1, -1, 0),
        (types.POWERPLANT + 4, 0, -1),
        (types.PORT + 4, 0, -1),
        (types.NUCLEAR + 4, 0, -1),
        (types.STADIUM + 4, 0, -1),
        (types.POWERPLANT + 5, -1, -1),
        (types.PORT + 5, -1, -1),
        (types.NUCLEAR + 5, -1, -1),
        (types.STADIUM + 5, -1, -1),
    ]

    for check_tile, dh, dv in four_by_four:
        if tile_id == check_tile:
            deltaHPtr[0] = dh
            deltaVPtr[0] = dv
            return 4

    # 6x6 airport
    airport_tiles = [
        # First row
        (types.AIRPORT, 0, 0),
        (types.AIRPORT + 1, -1, 0),
        (types.AIRPORT + 2, -2, 0),
        (types.AIRPORT + 3, -3, 0),
        # Second row
        (types.AIRPORT + 6, 0, -1),
        (types.AIRPORT + 7, -1, -1),
        (types.AIRPORT + 8, -2, -1),
        (types.AIRPORT + 9, -3, -1),
        # Third row
        (types.AIRPORT + 12, 0, -2),
        (types.AIRPORT + 13, -1, -2),
        (types.AIRPORT + 14, -2, -2),
        (types.AIRPORT + 15, -3, -2),
        # Fourth row
        (types.AIRPORT + 18, 0, -3),
        (types.AIRPORT + 19, -1, -3),
        (types.AIRPORT + 20, -2, -3),
        (types.AIRPORT + 21, -3, -3),
    ]

    for check_tile, dh, dv in airport_tiles:
        if tile_id == check_tile:
            deltaHPtr[0] = dh
            deltaVPtr[0] = dv
            return 6

    return 0


# ============================================================================
# Park and Network Utilities
# ============================================================================


def putDownPark(view: "micropolis.sim_view.SimView", mapH: int, mapV: int) -> int:
    """
    Place a park at the specified location.

    Parks can be fountains or wooded areas depending on random chance.

    Args:
        view: View placing the park
        mapH: X coordinate
        mapV: Y coordinate

    Returns:
        1 if successful, -1 if tile occupied, -2 if insufficient funds
    """
    if types.total_funds - CostOf[parkState] < 0:
        return -2

    value = random.Rand(4)
    if value == 3:
        tile = types.FOUNTAIN | types.BURNBIT | types.BULLBIT | types.ANIMBIT
    else:
        tile = (types.WOODS2 + value) | types.BURNBIT | types.BULLBIT

    if types.map_data[mapH][mapV] == 0:
        Spend(CostOf[parkState])
        types.UpdateFunds()
        types.map_data[mapH][mapV] = tile
        return 1

    return -1


def putDownNetwork(view: "micropolis.sim_view.SimView", mapH: int, mapV: int) -> int:
    """
    Place or remove a network/telecommunications tower.

    If the tile is empty, places a network tower.
    If the tile has a network tower, removes it and refunds some funds.

    Args:
        view: View placing the network
        mapH: X coordinate
        mapV: Y coordinate

    Returns:
        1 if placed, -1 if tile occupied, -2 if insufficient funds
    """
    tile = types.map_data[mapH][mapV] & types.LOMASK

    if (types.total_funds > 0) and tally(tile):
        types.map_data[mapH][mapV] = tile = 0
        Spend(1)

    if tile == 0:
        if (types.total_funds - CostOf[view.tool_state]) >= 0:
            types.map_data[mapH][mapV] = (
                types.TELEBASE
                | types.CONDBIT
                | types.BURNBIT
                | types.BULLBIT
                | types.ANIMBIT
            )
            Spend(CostOf[view.tool_state])
            return 1
        else:
            return -2
    else:
        return -1


# ============================================================================
# Size-Based Building Placement Functions
# ============================================================================


def check3x3border(xMap: int, yMap: int) -> None:
    """
    Update tile connections around a 3x3 building.

    Args:
        xMap: X coordinate of building center
        yMap: Y coordinate of building center
    """
    xPos = xMap
    yPos = yMap - 1

    # Update upper bordering row
    for cnt in range(3):
        if macros.TestBounds(xPos, yPos):
            ConnecTile(xPos, yPos, [types.map_data[xPos][yPos]], 0)
        xPos += 1

    xPos = xMap - 1
    yPos = yMap

    # Update left bordering row
    for cnt in range(3):
        if macros.TestBounds(xPos, yPos):
            ConnecTile(xPos, yPos, [types.map_data[xPos][yPos]], 0)
        yPos += 1

    xPos = xMap
    yPos = yMap + 3

    # Update bottom bordering row
    for cnt in range(3):
        if macros.TestBounds(xPos, yPos):
            ConnecTile(xPos, yPos, [types.map_data[xPos][yPos]], 0)
        xPos += 1

    xPos = xMap + 3
    yPos = yMap

    # Update right bordering row
    for cnt in range(3):
        if macros.TestBounds(xPos, yPos):
            ConnecTile(xPos, yPos, [types.map_data[xPos][yPos]], 0)
        yPos += 1


def check3x3(
    view: "micropolis.sim_view.SimView", mapH: int, mapV: int, base: int, tool: int
) -> int:
    """
    Check and place a 3x3 building.

    Args:
        view: View placing the building
        mapH: X coordinate (adjusted for building size)
        mapV: Y coordinate (adjusted for building size)
        base: Base tile ID for the building
        tool: Tool state for cost calculation

    Returns:
        1 if successful, -1 if area occupied or out of bounds
    """
    mapH -= 1
    mapV -= 1

    if (
        (mapH < 0)
        or (mapH > (micropolis.constants.WORLD_X - 3))
        or (mapV < 0)
        or (mapV > (micropolis.constants.WORLD_Y - 3))
    ):
        return -1

    xPos = holdMapH = mapH
    yPos = holdMapV = mapV

    flag = 1
    cost = 0

    # Check 3x3 area for occupancy and calculate bulldozing cost
    for rowNum in range(3):
        mapH = holdMapH
        for columnNum in range(3):
            tileValue = types.map_data[mapH][mapV] & types.LOMASK

            if types.auto_bulldoze:
                if tileValue != 0:
                    if tally(tileValue):
                        cost += 1
                    else:
                        flag = 0
            else:
                if tileValue != 0:
                    flag = 0
            mapH += 1
        mapV += 1

    if flag == 0:
        return -1

    cost += CostOf[tool]

    if (types.total_funds - cost) < 0:
        return -2

    if (
        (types.players > 1)
        and (types.over_ride == 0)
        and (cost >= types.expensive)
        and (view is not None)
        and (view.super_user == 0)
    ):
        return -3

    # Spend the money
    Spend(cost)
    types.UpdateFunds()

    mapV = holdMapV

    # Place the building tiles
    for rowNum in range(3):
        mapH = holdMapH
        for columnNum in range(3):
            if columnNum == 1 and rowNum == 1:
                types.map_data[mapH][mapV] = base + types.BNCNBIT + types.ZONEBIT
            else:
                types.map_data[mapH][mapV] = base + types.BNCNBIT
            base += 1
            mapH += 1
        mapV += 1

    check3x3border(xPos, yPos)
    return 1


def check4x4border(xMap: int, yMap: int) -> None:
    """
    Update tile connections around a 4x4 building.

    Args:
        xMap: X coordinate of building center
        yMap: Y coordinate of building center
    """
    xPos = xMap
    yPos = yMap - 1

    # Update upper bordering row
    for cnt in range(4):
        if macros.TestBounds(xPos, yPos):
            ConnecTile(xPos, yPos, [types.map_data[xPos][yPos]], 0)
        xPos += 1

    xPos = xMap - 1
    yPos = yMap

    # Update left bordering row
    for cnt in range(4):
        if macros.TestBounds(xPos, yPos):
            ConnecTile(xPos, yPos, [types.map_data[xPos][yPos]], 0)
        yPos += 1

    xPos = xMap
    yPos = yMap + 4

    # Update bottom bordering row
    for cnt in range(4):
        if macros.TestBounds(xPos, yPos):
            ConnecTile(xPos, yPos, [types.map_data[xPos][yPos]], 0)
        xPos += 1

    xPos = xMap + 4
    yPos = yMap

    # Update right bordering row
    for cnt in range(4):
        if macros.TestBounds(xPos, yPos):
            ConnecTile(xPos, yPos, [types.map_data[xPos][yPos]], 0)
        yPos += 1


def check4x4(
    view: "micropolis.sim_view.SimView",
    mapH: int,
    mapV: int,
    base: int,
    aniFlag: int,
    tool: int,
) -> int:
    """
    Check and place a 4x4 building.

    Args:
        view: View placing the building
        mapH: X coordinate (adjusted for building size)
        mapV: Y coordinate (adjusted for building size)
        base: Base tile ID for the building
        aniFlag: Whether building has animated center tile
        tool: Tool state for cost calculation

    Returns:
        1 if successful, -1 if area occupied or out of bounds
    """
    mapH -= 1
    mapV -= 1

    if (
        (mapH < 0)
        or (mapH > (micropolis.constants.WORLD_X - 4))
        or (mapV < 0)
        or (mapV > (micropolis.constants.WORLD_Y - 4))
    ):
        return -1

    h = xMap = holdMapH = mapH
    v = yMap = mapV

    flag = 1
    cost = 0

    # Check 4x4 area for occupancy and calculate bulldozing cost
    for rowNum in range(4):
        mapH = holdMapH
        for columnNum in range(4):
            tileValue = types.map_data[mapH][mapV] & types.LOMASK

            if types.auto_bulldoze:
                if tileValue != 0:
                    if tally(tileValue):
                        cost += 1
                    else:
                        flag = 0
            else:
                if tileValue != 0:
                    flag = 0
            mapH += 1
        mapV += 1

    if flag == 0:
        return -1

    cost += CostOf[tool]

    if (types.total_funds - cost) < 0:
        return -2

    if (
        (types.players > 1)
        and (types.over_ride == 0)
        and (cost >= types.expensive)
        and (view is not None)
        and (view.super_user == 0)
    ):
        return -3

    # Spend the money
    Spend(cost)
    types.UpdateFunds()

    mapV = v
    holdMapH = h

    # Place the building tiles
    for rowNum in range(4):
        mapH = holdMapH
        for columnNum in range(4):
            if columnNum == 1 and rowNum == 1:
                types.map_data[mapH][mapV] = base + types.BNCNBIT + types.ZONEBIT
            elif columnNum == 1 and rowNum == 2 and aniFlag:
                types.map_data[mapH][mapV] = base + types.BNCNBIT + types.ANIMBIT
            else:
                types.map_data[mapH][mapV] = base + types.BNCNBIT
            base += 1
            mapH += 1
        mapV += 1

    check4x4border(xMap, yMap)
    return 1


def check6x6border(xMap: int, yMap: int) -> None:
    """
    Update tile connections around a 6x6 building.

    Args:
        xMap: X coordinate of building center
        yMap: Y coordinate of building center
    """
    xPos = xMap
    yPos = yMap - 1

    # Update upper bordering row
    for cnt in range(6):
        if macros.TestBounds(xPos, yPos):
            ConnecTile(xPos, yPos, [types.map_data[xPos][yPos]], 0)
        xPos += 1

    xPos = xMap - 1
    yPos = yMap

    # Update left bordering row
    for cnt in range(6):
        if macros.TestBounds(xPos, yPos):
            ConnecTile(xPos, yPos, [types.map_data[xPos][yPos]], 0)
        yPos += 1

    xPos = xMap
    yPos = yMap + 6

    # Update bottom bordering row
    for cnt in range(6):
        if macros.TestBounds(xPos, yPos):
            ConnecTile(xPos, yPos, [types.map_data[xPos][yPos]], 0)
        xPos += 1

    xPos = xMap + 6
    yPos = yMap

    # Update right bordering row
    for cnt in range(6):
        if macros.TestBounds(xPos, yPos):
            ConnecTile(xPos, yPos, [types.map_data[xPos][yPos]], 0)
        yPos += 1


def check6x6(
    view: "micropolis.sim_view.SimView", mapH: int, mapV: int, base: int, tool: int
) -> int:
    """
    Check and place a 6x6 building.

    Args:
        view: View placing the building
        mapH: X coordinate (adjusted for building size)
        mapV: Y coordinate (adjusted for building size)
        base: Base tile ID for the building
        tool: Tool state for cost calculation

    Returns:
        1 if successful, -1 if area occupied or out of bounds
    """
    mapH -= 1
    mapV -= 1

    if (
        (mapH < 0)
        or (mapH > (micropolis.constants.WORLD_X - 6))
        or (mapV < 0)
        or (mapV > (micropolis.constants.WORLD_Y - 6))
    ):
        return -1

    h = xMap = holdMapH = mapH
    v = yMap = mapV

    flag = 1
    cost = 0

    # Check 6x6 area for occupancy and calculate bulldozing cost
    for rowNum in range(6):
        mapH = holdMapH
        for columnNum in range(6):
            tileValue = types.map_data[mapH][mapV] & types.LOMASK

            if types.auto_bulldoze:
                if tileValue != 0:
                    if tally(tileValue):
                        cost += 1
                    else:
                        flag = 0
            else:
                if tileValue != 0:
                    flag = 0
            mapH += 1
        mapV += 1

    if flag == 0:
        return -1

    cost += CostOf[tool]

    if (types.total_funds - cost) < 0:
        return -2

    if (
        (types.players > 1)
        and (types.over_ride == 0)
        and (cost >= types.expensive)
        and (view is not None)
        and (view.super_user == 0)
    ):
        return -3

    # Spend the money
    Spend(cost)
    types.UpdateFunds()

    mapV = v
    holdMapH = h

    # Place the building tiles
    for rowNum in range(6):
        mapH = holdMapH
        for columnNum in range(6):
            if columnNum == 1 and rowNum == 1:
                types.map_data[mapH][mapV] = base + types.BNCNBIT + types.ZONEBIT
            else:
                types.map_data[mapH][mapV] = base + types.BNCNBIT
            base += 1
            mapH += 1
        mapV += 1

    check6x6border(xMap, yMap)
    return 1


# ============================================================================
# Query Tool Functions
# ============================================================================

# Search table for zone status string match
idArray: list[int] = [
    types.DIRT,
    types.RIVER,
    types.TREEBASE,
    types.RUBBLE,
    types.FLOOD,
    types.RADTILE,
    types.FIRE,
    types.ROADBASE,
    types.POWERBASE,
    types.RAILBASE,
    types.RESBASE,
    types.COMBASE,
    types.INDBASE,
    types.PORTBASE,
    types.AIRPORTBASE,
    types.COALBASE,
    types.FIRESTBASE,
    types.POLICESTBASE,
    types.STADIUMBASE,
    types.NUCLEARBASE,
    827,
    832,
    types.FOUNTAIN,
    types.INDBASE2,
    types.FOOTBALLGAME1,
    types.VBRDG0,
    952,
    956,
]


def getDensityStr(catNo: int, mapH: int, mapV: int) -> int:
    """
    Get density string index for zone status display.

    Args:
        catNo: Category number (0=population, 1=land value, 2=crime, 3=pollution, 4=growth)
        mapH: X coordinate
        mapV: Y coordinate

    Returns:
        String index for the density display
    """
    if catNo == 0:  # Population density
        z = types.pop_density[mapH >> 1][mapV >> 1]
        z = z >> 6
        z = z & 3
        return z
    elif catNo == 1:  # Land value
        z = types.land_value_mem[mapH >> 1][mapV >> 1]
        if z < 30:
            return 4
        elif z < 80:
            return 5
        elif z < 150:
            return 6
        else:
            return 7
    elif catNo == 2:  # Crime
        z = types.crime_mem[mapH >> 1][mapV >> 1]
        z = z >> 6
        z = z & 3
        return z + 8
    elif catNo == 3:  # Pollution
        z = types.pollution_mem[mapH >> 1][mapV >> 1]
        if (z < 64) and (z > 0):
            return 13
        z = z >> 6
        z = z & 3
        return z + 12
    elif catNo == 4:  # Rate of growth
        z = types.rate_og_mem[mapH >> 3][mapV >> 3]
        if z < 0:
            return 16
        elif z == 0:
            return 17
        elif z > 100:
            return 19
        else:
            return 18

    return 0


def doZoneStatus(mapH: int, mapV: int) -> None:
    """
    Display zone status information for a tile.

    Shows population, land value, crime, pollution, and growth information
    for the selected zone.

    Args:
        mapH: X coordinate
        mapV: Y coordinate
    """
    tileNum = types.map_data[mapH][mapV] & types.LOMASK

    # Normalize coal smoke tiles to coal base
    if tileNum >= types.COALSMOKE1 and tileNum < types.FOOTBALLGAME1:
        tileNum = types.COALBASE

    found = 1
    for x in range(1, 29):
        if tileNum < idArray[x]:
            found = 0
            break
    x -= 1

    # Get localized string for tile type
    localStr = f"Tile_{x}"  # Placeholder for localized strings

    # Get density strings for each category
    statusStr = []
    for category in range(5):
        id_val = getDensityStr(category, mapH, mapV)
        id_val += 1
        if id_val <= 0:
            id_val = 1
        if id_val > 20:
            id_val = 20
        statusStr.append(f"Density_{id_val}")  # Placeholder for localized strings

    # Display zone status (placeholder for UI integration)
    DoShowZoneStatus(
        localStr,
        statusStr[0],
        statusStr[1],
        statusStr[2],
        statusStr[3],
        statusStr[4],
        mapH,
        mapV,
    )


def DoShowZoneStatus(
    str_arg: str, s0: str, s1: str, s2: str, s3: str, s4: str, x: int, y: int
) -> None:
    """
    Display zone status information in the UI.

    Args:
        str_arg: Tile type string
        s0: Population density string
        s1: Land value string
        s2: Crime density string
        s3: Pollution density string
        s4: Growth rate string
        x: X coordinate
        y: Y coordinate
    """
    # Placeholder for UI integration
    print(f"Zone Status at ({x},{y}): {str_arg}")
    print(f"  Population: {s0}")
    print(f"  Land Value: {s1}")
    print(f"  Crime: {s2}")
    print(f"  Pollution: {s3}")
    print(f"  Growth: {s4}")


# ============================================================================
# Tool Functions
# ============================================================================


def query_tool(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Query tool - show zone status information.

    Args:
        view: View performing the query
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    if (
        (x < 0)
        or (x > (micropolis.constants.WORLD_X - 1))
        or (y < 0)
        or (y > (micropolis.constants.WORLD_Y - 1))
    ):
        return -1

    doZoneStatus(x, y)
    DidTool(view, "Qry", x, y)
    return 1


def bulldozer_tool(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Bulldozer tool - destroy buildings and clear tiles.

    Args:
        view: View using the bulldozer
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    result = 0  # Initialize result
    currTile = types.map_data[x][y]
    temp = currTile & types.LOMASK

    if currTile & types.ZONEBIT:  # Zone center bit is set
        if types.total_funds > 0:
            Spend(1)
            zoneSize = checkSize(temp)

            if zoneSize == 3:
                MakeSound("city", "Explosion-High")
                put3x3Rubble(x, y)
            elif zoneSize == 4:
                put4x4Rubble(x, y)
                MakeSound("city", "Explosion-Low")
            elif zoneSize == 6:
                MakeSound("city", "Explosion-High")
                MakeSound("city", "Explosion-Low")
                put6x6Rubble(x, y)
            result = 1
    else:
        deltaH = [0]
        deltaV = [0]
        zoneSize = checkBigZone(temp, deltaH, deltaV)

        if zoneSize > 0:
            if types.total_funds > 0:
                Spend(1)

                if zoneSize == 3:
                    MakeSound("city", "Explosion-High")
                elif zoneSize == 4:
                    put4x4Rubble(x + deltaH[0], y + deltaV[0])
                    MakeSound("city", "Explosion-Low")
                elif zoneSize == 6:
                    MakeSound("city", "Explosion-High")
                    MakeSound("city", "Explosion-Low")
                    put6x6Rubble(x + deltaH[0], y + deltaV[0])
        else:
            # Handle rivers and other tiles
            if temp == types.RIVER or temp == types.REDGE or temp == types.CHANNEL:
                if types.total_funds >= 6:
                    result = ConnecTile(x, y, [types.map_data[x][y]], 1)
                    if temp != (types.map_data[x][y] & types.LOMASK):
                        Spend(5)
                else:
                    result = 0
            else:
                result = ConnecTile(x, y, [types.map_data[x][y]], 1)

    types.UpdateFunds()
    if result == 1:
        DidTool(view, "Dozr", x, y)
    return result


def road_tool(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Road tool - place road infrastructure.

    Args:
        view: View placing the road
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    if (
        (x < 0)
        or (x > (micropolis.constants.WORLD_X - 1))
        or (y < 0)
        or (y > (micropolis.constants.WORLD_Y - 1))
    ):
        return -1

    result = ConnecTile(x, y, [types.map_data[x][y]], 2)
    types.UpdateFunds()
    if result == 1:
        DidTool(view, "Road", x, y)
    return result


def rail_tool(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Rail tool - place rail infrastructure.

    Args:
        view: View placing the rail
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    if (
        (x < 0)
        or (x > (micropolis.constants.WORLD_X - 1))
        or (y < 0)
        or (y > (micropolis.constants.WORLD_Y - 1))
    ):
        return -1

    result = ConnecTile(x, y, [types.map_data[x][y]], 3)
    types.UpdateFunds()
    if result == 1:
        DidTool(view, "Rail", x, y)
    return result


def wire_tool(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Wire tool - place power line infrastructure.

    Args:
        view: View placing the wire
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    if (
        (x < 0)
        or (x > (micropolis.constants.WORLD_X - 1))
        or (y < 0)
        or (y > (micropolis.constants.WORLD_Y - 1))
    ):
        return -1

    result = ConnecTile(x, y, [types.map_data[x][y]], 4)
    types.UpdateFunds()
    if result == 1:
        DidTool(view, "Wire", x, y)
    return result


def park_tool(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Park tool - place parks and fountains.

    Args:
        view: View placing the park
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    if (
        (x < 0)
        or (x > (micropolis.constants.WORLD_X - 1))
        or (y < 0)
        or (y > (micropolis.constants.WORLD_Y - 1))
    ):
        return -1

    result = putDownPark(view, x, y)
    if result == 1:
        DidTool(view, "Park", x, y)
    return result


def residential_tool(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Residential zone tool - place residential buildings.

    Args:
        view: View placing the zone
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    if (
        (x < 0)
        or (x > (micropolis.constants.WORLD_X - 1))
        or (y < 0)
        or (y > (micropolis.constants.WORLD_Y - 1))
    ):
        return -1

    result = check3x3(view, x, y, types.RESBASE, residentialState)
    if result == 1:
        DidTool(view, "Res", x, y)
    return result


def commercial_tool(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Commercial zone tool - place commercial buildings.

    Args:
        view: View placing the zone
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    if (
        (x < 0)
        or (x > (micropolis.constants.WORLD_X - 1))
        or (y < 0)
        or (y > (micropolis.constants.WORLD_Y - 1))
    ):
        return -1

    result = check3x3(view, x, y, types.COMBASE, commercialState)
    if result == 1:
        DidTool(view, "Com", x, y)
    return result


def industrial_tool(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Industrial zone tool - place industrial buildings.

    Args:
        view: View placing the zone
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    if (
        (x < 0)
        or (x > (micropolis.constants.WORLD_X - 1))
        or (y < 0)
        or (y > (micropolis.constants.WORLD_Y - 1))
    ):
        return -1

    result = check3x3(view, x, y, types.INDBASE, industrialState)
    if result == 1:
        DidTool(view, "Ind", x, y)
    return result


def police_dept_tool(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Police department tool - place police stations.

    Args:
        view: View placing the police station
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    if (
        (x < 0)
        or (x > (micropolis.constants.WORLD_X - 1))
        or (y < 0)
        or (y > (micropolis.constants.WORLD_Y - 1))
    ):
        return -1

    result = check3x3(view, x, y, types.POLICESTBASE, policeState)
    if result == 1:
        DidTool(view, "Pol", x, y)
    return result


def fire_dept_tool(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Fire department tool - place fire stations.

    Args:
        view: View placing the fire station
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    if (
        (x < 0)
        or (x > (micropolis.constants.WORLD_X - 1))
        or (y < 0)
        or (y > (micropolis.constants.WORLD_Y - 1))
    ):
        return -1

    result = check3x3(view, x, y, types.FIRESTBASE, fireState)
    if result == 1:
        DidTool(view, "Fire", x, y)
    return result


def stadium_tool(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Stadium tool - place stadiums.

    Args:
        view: View placing the stadium
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    if (
        (x < 0)
        or (x > (micropolis.constants.WORLD_X - 1))
        or (y < 0)
        or (y > (micropolis.constants.WORLD_Y - 1))
    ):
        return -1

    result = check4x4(view, x, y, types.STADIUMBASE, 0, stadiumState)
    if result == 1:
        DidTool(view, "Stad", x, y)
    return result


def coal_power_plant_tool(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Coal power plant tool - place coal power plants.

    Args:
        view: View placing the power plant
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    if (
        (x < 0)
        or (x > (micropolis.constants.WORLD_X - 1))
        or (y < 0)
        or (y > (micropolis.constants.WORLD_Y - 1))
    ):
        return -1

    result = check4x4(view, x, y, types.COALBASE, 1, powerState)
    if result == 1:
        DidTool(view, "Coal", x, y)
    return result


def nuclear_power_plant_tool(
    view: "micropolis.sim_view.SimView", x: int, y: int
) -> int:
    """
    Nuclear power plant tool - place nuclear power plants.

    Args:
        view: View placing the power plant
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    if (
        (x < 0)
        or (x > (micropolis.constants.WORLD_X - 1))
        or (y < 0)
        or (y > (micropolis.constants.WORLD_Y - 1))
    ):
        return -1

    result = check4x4(view, x, y, types.NUCLEARBASE, 1, nuclearState)
    if result == 1:
        DidTool(view, "Nuc", x, y)
    return result


def seaport_tool(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Seaport tool - place seaports.

    Args:
        view: View placing the seaport
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    if (
        (x < 0)
        or (x > (micropolis.constants.WORLD_X - 1))
        or (y < 0)
        or (y > (micropolis.constants.WORLD_Y - 1))
    ):
        return -1

    result = check4x4(view, x, y, types.PORTBASE, 0, seaportState)
    if result == 1:
        DidTool(view, "Seap", x, y)
    return result


def airport_tool(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Airport tool - place airports.

    Args:
        view: View placing the airport
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    if (
        (x < 0)
        or (x > (micropolis.constants.WORLD_X - 1))
        or (y < 0)
        or (y > (micropolis.constants.WORLD_Y - 1))
    ):
        return -1

    result = check6x6(view, x, y, types.AIRPORTBASE, airportState)
    if result == 1:
        DidTool(view, "Airp", x, y)
    return result


def network_tool(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Network tool - place telecommunications networks.

    Args:
        view: View placing the network
        x: X coordinate
        y: Y coordinate

    Returns:
        1 if successful, -1 if out of bounds
    """
    if (
        (x < 0)
        or (x > (micropolis.constants.WORLD_X - 1))
        or (y < 0)
        or (y > (micropolis.constants.WORLD_Y - 1))
    ):
        return -1

    result = putDownNetwork(view, x, y)
    if result == 1:
        DidTool(view, "Net", x, y)
    return result


# ============================================================================
# Rubble Generation Functions
# ============================================================================


def put3x3Rubble(x: int, y: int) -> None:
    """
    Generate rubble from demolishing a 3x3 building.

    Args:
        x: X coordinate of building center
        y: Y coordinate of building center
    """
    for xx in range(x - 1, x + 2):
        for yy in range(y - 1, y + 2):
            if macros.TestBounds(xx, yy):
                zz = types.map_data[xx][yy] & types.LOMASK
                if (zz != types.RADTILE) and (zz != 0):
                    types.map_data[xx][yy] = (
                        (
                            (types.TINYEXP + random.Rand(2))
                            if types.do_animation
                            else types.SOMETINYEXP
                        )
                        | types.ANIMBIT
                        | types.BULLBIT
                    )


def put4x4Rubble(x: int, y: int) -> None:
    """
    Generate rubble from demolishing a 4x4 building.

    Args:
        x: X coordinate of building center
        y: Y coordinate of building center
    """
    for xx in range(x - 1, x + 3):
        for yy in range(y - 1, y + 3):
            if macros.TestBounds(xx, yy):
                zz = types.map_data[xx][yy] & types.LOMASK
                if (zz != types.RADTILE) and (zz != 0):
                    types.map_data[xx][yy] = (
                        (
                            (types.TINYEXP + random.Rand(2))
                            if types.do_animation
                            else types.SOMETINYEXP
                        )
                        | types.ANIMBIT
                        | types.BULLBIT
                    )


def put6x6Rubble(x: int, y: int) -> None:
    """
    Generate rubble from demolishing a 6x6 building.

    Args:
        x: X coordinate of building center
        y: Y coordinate of building center
    """
    for xx in range(x - 1, x + 5):
        for yy in range(y - 1, y + 5):
            if macros.TestBounds(xx, yy):
                zz = types.map_data[xx][yy] & types.LOMASK
                if (zz != types.RADTILE) and (zz != 0):
                    types.map_data[xx][yy] = (
                        (
                            (types.TINYEXP + random.Rand(2))
                            if types.do_animation
                            else types.SOMETINYEXP
                        )
                        | types.ANIMBIT
                        | types.BULLBIT
                    )


# ============================================================================
# Tool Management Functions
# ============================================================================


def DidTool(view: "micropolis.sim_view.SimView", name: str, x: int, y: int) -> None:
    """
    Notify the UI that a tool was used.

    Args:
        view: View that used the tool
        name: Tool name abbreviation
        x: X coordinate
        y: Y coordinate
    """
    # Placeholder for UI integration
    print(f"Tool {name} used at ({x},{y})")


def DoSetWandState(view: "micropolis.sim_view.SimView", state: int) -> None:
    """
    Set the current tool state in the UI.

    Args:
        view: View to update
        state: New tool state
    """
    # Placeholder for UI integration
    print(f"Tool state set to {state}")


def setWandState(view: "micropolis.sim_view.SimView", state: int) -> None:
    """
    Set the tool state for a view.

    Args:
        view: View to update
        state: New tool state
    """
    view.tool_state = state
    # DoUpdateHeads() - placeholder
    DoSetWandState(view, state)


# ============================================================================
# Main Tool Application Functions
# ============================================================================


def do_tool(
    view: "micropolis.sim_view.SimView", state: int, x: int, y: int, first: int
) -> int:
    """
    Apply a tool at the specified coordinates.

    Args:
        view: View applying the tool
        state: Tool state to apply
        x: X coordinate (in pixels)
        y: Y coordinate (in pixels)
        first: Whether this is the first application of a drag operation

    Returns:
        1 if successful, negative values for errors
    """
    result = 0

    # Tool state dispatch table
    tool_functions = {
        residentialState: residential_tool,
        commercialState: commercial_tool,
        industrialState: industrial_tool,
        fireState: fire_dept_tool,
        queryState: query_tool,
        policeState: police_dept_tool,
        wireState: wire_tool,
        dozeState: bulldozer_tool,
        rrState: rail_tool,
        roadState: road_tool,
        chalkState: lambda v, px, py: ChalkTool(
            v, px - 5, py + 11, micropolis.constants.COLOR_WHITE, first
        ),
        eraserState: lambda v, px, py: EraserTool(v, px, py, first),
        stadiumState: stadium_tool,
        parkState: park_tool,
        seaportState: seaport_tool,
        powerState: coal_power_plant_tool,
        nuclearState: nuclear_power_plant_tool,
        airportState: airport_tool,
        networkState: network_tool,
    }

    tool_func = tool_functions.get(state)
    if tool_func:
        # Convert pixel coordinates to tile coordinates
        tile_x = x >> 4
        tile_y = y >> 4
        result = tool_func(view, tile_x, tile_y)
    else:
        result = 0

    return result


def current_tool(
    view: "micropolis.sim_view.SimView", x: int, y: int, first: int
) -> int:
    """
    Apply the current tool of the view.

    Args:
        view: View with the current tool
        x: X coordinate (in pixels)
        y: Y coordinate (in pixels)
        first: Whether this is the first application

    Returns:
        1 if successful, negative values for errors
    """
    return do_tool(view, view.tool_state, x, y, first)


def ToolDown(view: "micropolis.sim_view.SimView", x: int, y: int) -> None:
    """
    Handle tool down event (mouse click).

    Args:
        view: View receiving the event
        x: X coordinate (in pixels)
        y: Y coordinate (in pixels)
    """
    # Convert screen coordinates to pixel coordinates
    pixel_x = x
    pixel_y = y

    view.last_x = pixel_x
    view.last_y = pixel_y

    result = current_tool(view, pixel_x, pixel_y, 1)

    if result == -1:
        messages.clear_mes()
        messages.send_mes(34)  # "That area is not in your jurisdiction"
        MakeSoundOn(view, "edit", "UhUh")
    elif result == -2:
        messages.clear_mes()
        messages.send_mes(33)  # "You are out of funds"
        MakeSoundOn(view, "edit", "Sorry")
    elif result == -3:
        DoPendTool(view, view.tool_state, pixel_x >> 4, pixel_y >> 4)

    types.sim_skip = 0
    view.skip = 0
    view.invalid = True
    # InvalidateEditors() - placeholder


def ToolUp(view: "micropolis.sim_view.SimView", x: int, y: int) -> int:
    """
    Handle tool up event (mouse release).

    Args:
        view: View receiving the event
        x: X coordinate (in pixels)
        y: Y coordinate (in pixels)

    Returns:
        Result of the tool operation
    """
    result = ToolDrag(view, x, y)
    return result


def ToolDrag(view: "micropolis.sim_view.SimView", px: int, py: int) -> int:
    """
    Handle tool drag event (mouse movement while tool is active).

    Args:
        view: View receiving the event
        px: X coordinate (in pixels)
        py: Y coordinate (in pixels)

    Returns:
        1 if successful, 0 otherwise
    """
    # Convert screen coordinates to pixel coordinates
    x = px
    y = py

    view.tool_x = x
    view.tool_y = y

    # Handle freeform tools (chalk, eraser) differently
    if (view.tool_state == chalkState) or (view.tool_state == eraserState):
        current_tool(view, x, y, 0)
        view.last_x = x
        view.last_y = y
    else:
        # Handle tile-based tools with interpolation
        dist = toolSize[view.tool_state]

        x >>= 4  # Convert to tile coordinates
        y >>= 4

        lx = view.last_x >> 4
        ly = view.last_y >> 4

        dx = x - lx
        dy = y - ly

        if dx == 0 and dy == 0:
            return 0

        adx = abs(dx)
        ady = abs(dy)

        if adx > ady:
            step = 0.3 / adx
        else:
            step = 0.3 / ady

        rx = 1 if dx < 0 else 0
        ry = 1 if dy < 0 else 0

        if dist == 1:
            # Single tile tool - interpolate path
            for i in range(0, int(1 + step), int(step)):
                tx = lx + i * dx
                ty = ly + i * dy
                dtx = abs(tx - lx)
                dty = abs(ty - ly)
                if dtx >= 1 or dty >= 1:
                    # Fill in corners
                    if dtx >= 1 and dty >= 1:
                        if dtx > dty:
                            current_tool(view, ((int(tx) + rx) << 4), ly << 4, 0)
                        else:
                            current_tool(view, lx << 4, ((int(ty) + ry) << 4), 0)
                    lx = int(tx) + rx
                    ly = int(ty) + ry
                    current_tool(view, lx << 4, ly << 4, 0)
        else:
            # Multi-tile tool - place at intervals
            for i in range(0, int(1 + step), int(step)):
                tx = lx + i * dx
                ty = ly + i * dy
                dtx = abs(tx - lx)
                dty = abs(ty - ly)
                lx = int(tx) + rx
                ly = int(ty) + ry
                current_tool(view, lx << 4, ly << 4, 0)

        view.last_x = (lx << 4) + 8
        view.last_y = (ly << 4) + 8

    types.sim_skip = 0  # Update editors overlapping this one
    view.skip = 0
    view.invalid = True
    return 1


def DoTool(view: "micropolis.sim_view.SimView", tool: int, x: int, y: int) -> None:
    """
    Apply a specific tool at tile coordinates.

    Args:
        view: View applying the tool
        tool: Tool state to apply
        x: X coordinate (in tiles)
        y: Y coordinate (in tiles)
    """
    result = do_tool(view, tool, x << 4, y << 4, 1)

    if result == -1:
        messages.clear_mes()
        messages.send_mes(34)
        MakeSoundOn(view, "edit", "UhUh")
    elif result == -2:
        messages.clear_mes()
        messages.send_mes(33)
        MakeSoundOn(view, "edit", "Sorry")

    types.sim_skip = 0
    view.skip = 0
    # InvalidateEditors() - placeholder


def DoPendTool(view: "micropolis.sim_view.SimView", tool: int, x: int, y: int) -> None:
    """
    Handle pending tool operations for multiplayer scenarios.

    Args:
        view: View requesting the tool
        tool: Tool state
        x: X coordinate (in tiles)
        y: Y coordinate (in tiles)
    """
    # Placeholder for multiplayer integration
    print(f"Pending tool {tool} at ({x},{y})")


# ============================================================================
# Drawing Tools (Chalk and Eraser)
# ============================================================================


# Ink structure for drawing tools
@dataclass
class Ink:
    """Ink stroke data for chalk and eraser tools."""

    x: int = 0
    y: int = 0
    color: int = 0
    length: int = 0
    points: list[tuple[int, int]] = None  # type: ignore
    left: int = 0
    top: int = 0
    right: int = 0
    bottom: int = 0
    next: "Ink|None" = None

    def __post_init__(self):
        if self.points is None:
            self.points = []


def NewInk() -> Ink:
    """
    Create a new ink stroke.

    Returns:
        New Ink object
    """
    return Ink()


def FreeInk(ink: Ink) -> None:
    """
    Free an ink stroke (placeholder for memory management).

    Args:
        ink: Ink object to free
    """
    pass


def StartInk(ink: Ink, x: int, y: int) -> None:
    """
    Start a new ink stroke.

    Args:
        ink: Ink object to initialize
        x: Starting X coordinate
        y: Starting Y coordinate
    """
    ink.x = x
    ink.y = y
    ink.length = 1
    ink.points = [(0, 0)]
    ink.left = ink.right = x
    ink.top = ink.bottom = y


def AddInk(ink: Ink, x: int, y: int) -> None:
    """
    Add a point to an ink stroke.

    Args:
        ink: Ink object to extend
        x: X coordinate to add
        y: Y coordinate to add
    """
    if ink.length >= len(ink.points):
        ink.points.append((x - ink.x, y - ink.y))
    else:
        ink.points[ink.length] = (x - ink.x, y - ink.y)

    ink.length += 1

    # Update bounding box
    if x < ink.left:
        ink.left = x
    if x > ink.right:
        ink.right = x
    if y < ink.top:
        ink.top = y
    if y > ink.bottom:
        ink.bottom = y


def ChalkTool(
    view: "micropolis.sim_view.SimView", x: int, y: int, color: int, first: int
) -> int:
    """
    Chalk drawing tool.

    Args:
        view: View using the chalk
        x: X coordinate
        y: Y coordinate
        color: Chalk color
        first: Whether this is the first point

    Returns:
        1 if successful
    """
    if first:
        ChalkStart(view, x, y, color)
    else:
        ChalkTo(view, x, y)
    DidTool(view, "Chlk", x, y)
    return 1


def ChalkStart(view: "micropolis.sim_view.SimView", x: int, y: int, color: int) -> None:
    """
    Start a chalk stroke.

    Args:
        view: View starting the stroke
        x: Starting X coordinate
        y: Starting Y coordinate
        color: Chalk color
    """
    ink = NewInk()
    ink.color = color
    StartInk(ink, x, y)
    view.track_info = str(id(ink))  # Placeholder for ink tracking
    view.last_x = x
    view.last_y = y
    # Set tool event time - placeholder


def ChalkTo(view: "micropolis.sim_view.SimView", x: int, y: int) -> None:
    """
    Continue a chalk stroke.

    Args:
        view: View continuing the stroke
        x: Current X coordinate
        y: Current Y coordinate
    """
    # Placeholder - would interpolate motion events
    AddInk(NewInk(), x, y)  # Placeholder
    view.last_x = x
    view.last_y = y


def EraserTool(view: "micropolis.sim_view.SimView", x: int, y: int, first: int) -> int:
    """
    Eraser tool for removing chalk strokes.

    Args:
        view: View using the eraser
        x: X coordinate
        y: Y coordinate
        first: Whether this is the first point

    Returns:
        1 if successful
    """
    if first:
        EraserStart(view, x, y)
    else:
        EraserTo(view, x, y)
    DidTool(view, "Eraser", x, y)
    return 1


def InkInBox(ink: Ink, left: int, top: int, right: int, bottom: int) -> bool:
    """
    Check if an ink stroke intersects a bounding box.

    Args:
        ink: Ink stroke to check
        left: Left edge of box
        top: Top edge of box
        right: Right edge of box
        bottom: Bottom edge of box

    Returns:
        True if ink intersects the box
    """
    if (
        (left <= ink.right)
        and (right >= ink.left)
        and (top <= ink.bottom)
        and (bottom >= ink.top)
    ):
        if ink.length == 1:
            return True

        x, y = ink.x, ink.y
        for i in range(1, ink.length):
            dx, dy = ink.points[i]
            lx, ly = x, y
            x += dx
            y += dy

            ileft = min(lx, x)
            iright = max(lx, x)
            itop = min(ly, y)
            ibottom = max(ly, y)

            if (
                (left <= iright)
                and (right >= ileft)
                and (top <= ibottom)
                and (bottom >= itop)
            ):
                return True

    return False


def EraserStart(view: "micropolis.sim_view.SimView", x: int, y: int) -> None:
    """
    Start an eraser operation.

    Args:
        view: View starting the eraser
        x: X coordinate
        y: Y coordinate
    """
    EraserTo(view, x, y)


def EraserTo(view: "micropolis.sim_view.SimView", x: int, y: int) -> None:
    """
    Continue an eraser operation.

    Args:
        view: View continuing the eraser
        x: Current X coordinate
        y: Current Y coordinate
    """
    # Placeholder for ink removal logic
    # Would iterate through overlay inks and remove intersecting ones
    pass
