import pytest
from citysim.simulation.world import GameMap
from citysim.simulation.simulation import Simulation
from citysim.simulation.tile import TileType, TILE_DEFINITIONS


def test_power_propagation():
    world = GameMap(10, 10)
    sim = Simulation(world)

    # 0,0: Power Plant
    # 0,1: Road (Not a conductor unless explicit? TileDef says Road is NOT conductor in my update?)
    # Wait, did I add PowerConductor to Road?
    # Checking TileDef... Road has Cost(10) but NO PowerConductor in my edit.
    # So Road does NOT conduct power.

    world.set_tile(0, 0, TileType.POWER_PLANT)
    world.set_tile(1, 0, TileType.POWER_LINE)
    world.set_tile(2, 0, TileType.RESIDENTIAL_LVL1)  # Consumer

    # Run simulation power update
    sim.update_power_grid()

    # Verify Plant is powered (Source)
    assert (0, 0) in sim.powered_tiles

    # Verify Line is powered
    assert (1, 0) in sim.powered_tiles

    # Verify House is powered
    assert (2, 0) in sim.powered_tiles

    # Verify disconnected house
    world.set_tile(5, 5, TileType.RESIDENTIAL_LVL1)
    sim.update_power_grid()
    assert (5, 5) not in sim.powered_tiles


def test_power_through_zones():
    world = GameMap(10, 10)
    sim = Simulation(world)

    # Plant -> House -> House
    world.set_tile(0, 0, TileType.POWER_PLANT)
    world.set_tile(0, 1, TileType.RESIDENTIAL_LVL1)
    world.set_tile(0, 2, TileType.RESIDENTIAL_LVL1)

    sim.update_power_grid()

    assert (0, 0) in sim.powered_tiles
    assert (0, 1) in sim.powered_tiles
    assert (0, 2) in sim.powered_tiles
