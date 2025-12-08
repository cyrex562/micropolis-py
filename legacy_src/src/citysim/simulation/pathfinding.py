from heapq import heappush, heappop
from citysim.simulation.world import GameMap
from citysim.simulation.tile import TileType, TILE_DEFINITIONS
from citysim.simulation.components import RoadStats


class Pathfinder:
    def __init__(self, world: GameMap):
        self.world = world

    def find_path(
        self, start: tuple[int, int], end: tuple[int, int]
    ) -> list[tuple[int, int]] | None:
        """
        A* pathfinding on the Road Network.
        Returns a list of coordinates (x, y) including start and end, or None if no path.
        """
        if start == end:
            return [start]

        # Priority Queue: (f_score, x, y)
        open_set = []
        heappush(open_set, (0, start[0], start[1]))

        came_from = {}

        # g_score: cost from start
        g_score = {start: 0.0}

        # f_score: g_score + heuristic
        f_score = {start: self.heuristic(start, end)}

        while open_set:
            _, cx, cy = heappop(open_set)
            current = (cx, cy)

            if current == end:
                return self.reconstruct_path(came_from, current)

            for nx, ny in self.get_neighbors(cx, cy):
                # Calculate cost (distance / speed_limit)
                # For now, distance is always 1. Speed limit could vary.
                # Avoid congestion? Maybe later.

                # Check if it's a road
                tile = self.world.get_tile(nx, ny, 0)
                tile_def = TILE_DEFINITIONS.get(tile)

                # Special case: Start/End might not be roads (they are buildings adjacent to roads)
                # But we traverse ROADS.
                # So we allow moving FROM start (building) TO adjacent Road
                # And FROM Road TO end (building).
                # Intermediate steps MUST be Roads.

                is_road = tile == TileType.ROAD
                is_start_or_end = (nx, ny) == start or (nx, ny) == end

                if not is_road and not is_start_or_end:
                    continue

                stats = tile_def.get_component(RoadStats) if tile_def else None
                speed = stats.speed_limit if stats else 1.0
                move_cost = 1.0 / speed

                tentative_g = g_score[current] + move_cost

                if (nx, ny) not in g_score or tentative_g < g_score[(nx, ny)]:
                    came_from[(nx, ny)] = current
                    g_score[(nx, ny)] = tentative_g
                    f = tentative_g + self.heuristic((nx, ny), end)
                    f_score[(nx, ny)] = f
                    heappush(open_set, (f, nx, ny))

        return None

    def heuristic(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        # Manhattan distance
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        valid = []
        for nx, ny in candidates:
            if 0 <= nx < self.world.width and 0 <= ny < self.world.height:
                valid.append((nx, ny))
        return valid

    def reconstruct_path(self, came_from, current):
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.append(current)
        return total_path[::-1]
