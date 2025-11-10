"""
Power grid connectivity and management for Micropolis.

This module implements the power distribution system that manages connectivity
from power plants to zones throughout the city. It uses a flood-fill algorithm
to determine which areas receive power from coal and nuclear power plants.

Based on s_power.c from the original C codebase.
"""

from typing import List
import array
from . import types

# Power grid constants
POWERMAPROW = (types.WORLD_X + 15) // 16  # ((WORLD_X + 15) / 16)
PWRMAPSIZE = POWERMAPROW * types.WORLD_Y
PWRSTKSIZE = (types.WORLD_X * types.WORLD_Y) // 4  # ((WORLD_X * WORLD_Y) / 4)

# Power-related bit constants
PWRBIT = 32768  # 0x8000 - bit 15
CONDBIT = 16384  # 0x4000 - bit 14

# Global power grid state
PowerStackNum: int = 0
PowerStackX: List[int] = [0] * PWRSTKSIZE
PowerStackY: List[int] = [0] * PWRSTKSIZE
MaxPower: int = 0
NumPower: int = 0


def DoPowerScan() -> None:
    """
    Perform power grid connectivity scan.

    This function implements a flood-fill algorithm to determine which areas
    of the city receive power from power plants. It starts from all power
    plants and spreads power to connected conductive tiles.
    """
    global PowerStackNum, MaxPower, NumPower

    # Clear the power map
    types.PowerMap = array.array('H', [0] * PWRMAPSIZE)

    # Reset power statistics
    MaxPower = types.CoalPop * 700 + types.NuclearPop * 2000
    NumPower = 0

    # Find all power plants and add them to the stack
    PowerStackNum = 0
    for x in range(types.WORLD_X):
        for y in range(types.WORLD_Y):
            tile = types.Map[x][y]
            # Check if this is a power plant tile
            if tile & PWRBIT != 0:
                if PowerStackNum < PWRSTKSIZE:
                    PowerStackX[PowerStackNum] = x
                    PowerStackY[PowerStackNum] = y
                    PowerStackNum += 1
                # Mark this tile as powered
                SetPowerBit(x, y)

    # Process the power stack using flood-fill
    while PowerStackNum > 0:
        PowerStackNum -= 1
        x = PowerStackX[PowerStackNum]
        y = PowerStackY[PowerStackNum]

        # Spread power to adjacent conductive tiles
        for dir in range(4):  # 4 directions: north, east, south, west
            nx, ny = MoveMapSim(x, y, dir)
            if nx >= 0 and nx < types.WORLD_X and ny >= 0 and ny < types.WORLD_Y:
                if TestForCond(nx, ny):
                    if not TestPowerBit(nx, ny):
                        SetPowerBit(nx, ny)
                        if PowerStackNum < PWRSTKSIZE:
                            PowerStackX[PowerStackNum] = nx
                            PowerStackY[PowerStackNum] = ny
                            PowerStackNum += 1


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


def TestForCond(x: int, y: int) -> bool:
    """
    Test if a tile conducts power.

    A tile conducts power if it has the CONDBIT set, indicating it's
    part of the conductive infrastructure (power lines, etc.).

    Args:
        x: X coordinate of tile to test
        y: Y coordinate of tile to test

    Returns:
        True if the tile conducts power, False otherwise
    """
    tile = types.Map[x][y]
    return (tile & CONDBIT) != 0


def SetPowerBit(x: int, y: int) -> None:
    """
    Set the power bit for a tile in the power map.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    # Calculate the word index in the power map
    word = types.POWERWORD(x, y)
    # Calculate the bit position within the word
    bit = x & 15
    # Set the bit
    types.PowerMap[word] |= (1 << bit)


def TestPowerBit(x: int, y: int) -> bool:
    """
    Test if a tile has power in the power map.

    Args:
        x: X coordinate
        y: Y coordinate

    Returns:
        True if the tile has power, False otherwise
    """
    # Calculate the word index in the power map
    word = types.POWERWORD(x, y)
    # Calculate the bit position within the word
    bit = x & 15
    # Test the bit
    return (types.PowerMap[word] & (1 << bit)) != 0


def PushPowerStack() -> None:
    """
    Push current map position onto the power stack.

    Used by power plants to add themselves to the flood-fill stack.
    """
    global PowerStackNum

    if PowerStackNum < (PWRSTKSIZE - 2):
        PowerStackNum += 1
        PowerStackX[PowerStackNum] = types.SMapX
        PowerStackY[PowerStackNum] = types.SMapY


def ClearPowerBit(x: int, y: int) -> None:
    """
    Clear the power bit for a tile in the power map.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    # Calculate the word index in the power map
    word = types.POWERWORD(x, y)
    # Calculate the bit position within the word
    bit = x & 15
    # Clear the bit
    types.PowerMap[word] &= ~(1 << bit)