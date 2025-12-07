import pytest
from citysim.simulation.world import GameMap
from citysim.simulation.tile import TileType
from citysim.simulation.simulation import Simulation


def test_residential_growth():
    # Setup
    world = GameMap(10, 10)
    sim = Simulation(world)

    # Place Road at (5, 5)
    world.set_tile(5, 5, TileType.ROAD)

    # Place Residential Zone at (5, 6) (Connected)
    world.set_tile(5, 6, TileType.RESIDENTIAL)

    # Place Residential Zone at (0, 0) (Disconnected)
    world.set_tile(0, 0, TileType.RESIDENTIAL)

    # Tick simulation until growth happens (random chance)
    # 10% chance per tick. 100 ticks should be enough to be almost certain.
    grew = False
    for _ in range(100):
        if sim.tick(1.0):  # 1.0 second per tick
            if world.get_tile(5, 6) == TileType.RESIDENTIAL_LVL1:
                grew = True
                break

    assert grew, "Connected Residential zone should have grown"
    assert world.get_tile(0, 0) == TileType.RESIDENTIAL, (
        "Disconnected zone should NOT grow"
    )


def test_commercial_growth():
    world = GameMap(10, 10)
    sim = Simulation(world)

    world.set_tile(5, 5, TileType.ROAD)
    world.set_tile(5, 6, TileType.COMMERCIAL)

    grew = False
    for _ in range(100):
        if sim.tick(1.0):
            if world.get_tile(5, 6) == TileType.COMMERCIAL_LVL1:
                grew = True
                break

    assert grew, "Connected Commercial zone should have grown"
