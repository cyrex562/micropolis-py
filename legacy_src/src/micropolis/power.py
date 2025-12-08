"""
Power grid connectivity and management for Micropolis.

This module implements the power distribution system that manages connectivity
from power plants to zones throughout the city. It uses a flood-fill algorithm
to determine which areas receive power from coal and nuclear power plants.

Based on s_power.c from the original C codebase.
"""

import array

from micropolis.constants import (
    CONDBIT,
    PWRBIT,
    PWRMAPSIZE,
    PWRSTKSIZE,
    POWERMAPROW,
    WORLD_X,
    WORLD_Y,
)
from micropolis.context import AppContext

power_stack_num = 0
max_power = 0
num_power = 0


def DoPowerScan(context: AppContext) -> None:
    """
    Perform power grid connectivity scan.

    This function implements a flood-fill algorithm to determine which areas
    of the city receive power from power plants. It starts from all power
    plants and spreads power to connected conductive tiles.
    :param context:
    """
    # AppContext is now the authoritative source for all state

    # Clear the power map
    # context.power_map = array.array("H", [0] * PWRMAPSIZE)
    context.power_map = [0] * PWRMAPSIZE

    # Reset power statistics
    context.max_power = context.coal_pop * 700 + context.nuclear_pop * 2000
    context.num_power = 0
    # Find all power plants and add them to the stack
    context.power_stack_num = 0
    for x in range(WORLD_X):
        for y in range(WORLD_Y):
            tile = context.map_data[x][y]
            # Check if this is a power plant tile
            if tile & PWRBIT != 0:
                if context.power_stack_num < PWRSTKSIZE:
                    context.power_stack_x[context.power_stack_num] = x
                    context.power_stack_y[context.power_stack_num] = y
                    context.power_stack_num += 1
                # Mark this tile as powered
                SetPowerBit(context, x, y)

    # Process the power stack using flood-fill
    while context.power_stack_num > 0:
        context.power_stack_num -= 1
        x = context.power_stack_x[context.power_stack_num]
        y = context.power_stack_y[context.power_stack_num]

        # Spread power to adjacent conductive tiles
        for dir in range(4):  # 4 directions: north, east, south, west
            nx, ny = MoveMapSim(x, y, dir)
            if (
                    nx >= 0
                    and nx < WORLD_X
                    and ny >= 0
                    and ny < WORLD_Y
            ):
                if TestForCond(context, nx, ny):
                    if not TestPowerBit(context, nx, ny):
                        SetPowerBit(context, nx, ny)
                        if context.power_stack_num < PWRSTKSIZE:
                            context.power_stack_x[context.power_stack_num] = nx
                            context.power_stack_y[context.power_stack_num] = ny
                            context.power_stack_num += 1

    global power_stack_num, max_power, num_power
    power_stack_num = context.power_stack_num
    max_power = context.max_power
    num_power = context.num_power
def MoveMapSim(x: int, y: int, dir: int) -> tuple[int, int]:
    """
    Move to adjacent tile in specified direction.

    Args:
        x: Current x coordinate
        y: Current y coordinate
        dir: Direction (0=north, 1=east, 2=south, 3=west)

    Returns:
        Tuple of (new_x, new_y) coordinates
    """
    if dir == 0:  # North
        return x, y - 1
    elif dir == 1:  # East
        return x + 1, y
    elif dir == 2:  # South
        return x, y + 1
    elif dir == 3:  # West
        return x - 1, y
    else:
        return x, y  # Invalid direction


def TestForCond(context: AppContext, x: int, y: int) -> bool:
    """
    Test if a tile conducts power.

    A tile conducts power if it has the CONDBIT set, indicating it's
    part of the conductive infrastructure (power lines, etc.).

    Args:
        context: Application context
        x: X coordinate of tile to test
        y: Y coordinate of tile to test

    Returns:
        True if the tile conducts power, False otherwise
    """
    tile = context.map_data[x][y]
    return (tile & CONDBIT) != 0


# ============================================================================
# Power Grid Constants
# ============================================================================


# Power grid bit operations
def powerword(x: int, y: int) -> int:
    """Calculate power map word index for coordinates"""
    return ((x) >> 4) + ((y) << 3)


def SetPowerBit(context: AppContext, x: int, y: int) -> None:
    """
    Set the power bit for a tile in the power map.

    Args:
        x: X coordinate
        y: Y coordinate
        :param context:
    """
    # Calculate the word index in the power map
    word = powerword(x, y)
    # Calculate the bit position within the word
    bit = x & 15
    # Set the bit
    context.power_map[word] |= 1 << bit


def TestPowerBit(context: AppContext, x: int, y: int) -> bool:
    """
    Test if a tile has power in the power map.

    Args:
        x: X coordinate
        y: Y coordinate

    Returns:
        True if the tile has power, False otherwise
        :param context:
    """
    # Calculate the word index in the power map
    word = powerword(x, y)
    # Calculate the bit position within the word
    bit = x & 15
    # Test the bit
    return (context.power_map[word] & (1 << bit)) != 0


def PushPowerStack(context: AppContext) -> None:
    """
    Push current map position onto the power stack.

    Used by power plants to add themselves to the flood-fill stack.
    :param context:
    """
    # global power_stack_num

    if context.power_stack_num < (PWRSTKSIZE - 2):
        context.power_stack_num += 1
        context.power_stack_x[context.power_stack_num] = context.s_map_x
        context.power_stack_y[context.power_stack_num] = context.s_map_y


def ClearPowerBit(context: AppContext, x: int, y: int) -> None:
    """
    Clear the power bit for a tile in the power map.

    Args:
        x: X coordinate
        y: Y coordinate
        :param context:
    """
    # Calculate the word index in the power map
    word = powerword(x, y)
    # Calculate the bit position within the word
    bit = x & 15
    # Clear the bit
    context.power_map[word] &= ~(1 << bit)


def setpowerbit(x: int, y: int, power_map: array.array) -> None:
    """Set power bit at coordinates in power map"""
    power_map[powerword(x, y)] |= 1 << ((x) & 15)
