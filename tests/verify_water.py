from citysim.simulation.world import GameMap
from citysim.simulation.tile import TileType


def verify_water_generation():
    print("Testing Water Generation...")
    water_found = False
    for i in range(10):  # Try 10 maps
        gmap = GameMap(64, 64)
        water_count = 0
        for x in range(64):
            for y in range(64):
                if gmap.get_tile(x, y) == TileType.WATER:
                    water_count += 1

        print(f"Map {i}: {water_count} water tiles")
        if water_count > 0:
            water_found = True

    if water_found:
        print("SUCCESS: Water tiles generated.")
    else:
        print("FAILURE: No water tiles generated in 10 attempts.")
        exit(1)


if __name__ == "__main__":
    verify_water_generation()
