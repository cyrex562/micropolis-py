import random
from citysim.simulation.world import GameMap
from citysim.simulation.tile import TileType, TILE_DEFINITIONS
from citysim.simulation.components import (
    Growth,
    PowerSource,
    PowerConductor,
    PowerConsumer,
    WaterSource,
    WaterConductor,
    SewerConductor,  # Sinks are implicit map edges for now
    Population,
    Jobs,
    RoadStats,
)
from citysim.simulation.pathfinding import Pathfinder


class Simulation:
    def __init__(self, world: GameMap):
        self.world = world
        self.tick_timer = 0.0
        self.tick_rate = 1.0  # Seconds per tick
        self.day = 0
        self.population = 0
        self.powered_tiles = set()
        self.watered_tiles = set()
        self.drained_tiles = set()
        self.pathfinder = Pathfinder(self.world)
        self.road_usage = {}  # (x, y) -> int (trip count)

    def tick(self, dt: float) -> bool:
        """
        Advance simulation. Returns True if the map was modified.
        """
        self.tick_timer += dt
        if self.tick_timer >= self.tick_rate:
            self.tick_timer = 0.0
            changes = self.perform_tick()
            self.day += 1
            self.update_stats()
            return changes
        return False

    def perform_tick(self) -> bool:
        """
        Execute one simulation step (Day/Week).
        """
        changes = False

        for x in range(self.world.width):
            for y in range(self.world.height):
                tile_id = self.world.get_tile(x, y)
                tile_def = TILE_DEFINITIONS.get(tile_id)

                # Check for Growth
                growth = tile_def.get_component(Growth)
                if tile_def and growth:
                    # RCI Zone found. Check if connected to Road.
                    if self.is_connected_to_road(x, y):
                        # Chance to grow
                        if (
                            random.random() < 0.1 * growth.chance
                        ):  # 10% base chance * component chance
                            self.world.set_tile(x, y, growth.target_id)
                            changes = True

        # Update Utility Grids
        self.update_power_grid()
        self.update_water_grid()
        self.update_power_grid()
        self.update_water_grid()
        self.update_sewer_grid()

        # Update Traffic/Labor once per day
        if self.tick_timer == 0.0:  # Start of day (roughly)
            self.update_labor_exchange()
            self.update_traffic()

        return changes

    def update_power_grid(self):
        """Propagate power from sources through conductors (Layer 1)."""
        self.powered_tiles.clear()

        # 1. Find all sources (Layer 0)
        sources = []
        for x in range(self.world.width):
            for y in range(self.world.height):
                tile_id = self.world.get_tile(x, y, 0)
                tile_def = TILE_DEFINITIONS.get(tile_id)
                if tile_def and tile_def.has_component(PowerSource):
                    sources.append((x, y))
                    self.powered_tiles.add((x, y))

        # 2. BFS Flood Fill
        queue = list(sources)
        visited = set(sources)

        while queue:
            curr_x, curr_y = queue.pop(0)
            neighbors = [
                (curr_x + 1, curr_y),
                (curr_x - 1, curr_y),
                (curr_x, curr_y + 1),
                (curr_x, curr_y - 1),
            ]

            for nx, ny in neighbors:
                if 0 <= nx < self.world.width and 0 <= ny < self.world.height:
                    if (nx, ny) not in visited:
                        # Check Layer 1 (Air) for Lines
                        t1 = self.world.get_tile(nx, ny, 1)
                        td1 = TILE_DEFINITIONS.get(t1)
                        is_conductor = td1 and td1.has_component(PowerConductor)

                        # Also Check Layer 0 (Buildings that conduct? e.g., Zones)
                        # Zones conduct power.
                        t0 = self.world.get_tile(nx, ny, 0)
                        td0 = TILE_DEFINITIONS.get(t0)
                        is_conductor_0 = td0 and td0.has_component(PowerConductor)

                        if is_conductor or is_conductor_0:
                            self.powered_tiles.add((nx, ny))
                            visited.add((nx, ny))
                            queue.append((nx, ny))
                        else:
                            # Not a conductor, but maybe a Consumer adjacent to power?
                            # e.g. Building touching a line.
                            t_cons = self.world.get_tile(nx, ny, 0)
                            td_cons = TILE_DEFINITIONS.get(t_cons)
                            if td_cons and td_cons.has_component(PowerConsumer):
                                self.powered_tiles.add((nx, ny))

    def update_water_grid(self):
        """Propagate water from Pumps (near water) through Pipes (-1) and Buildings."""
        self.watered_tiles.clear()

        sources = []
        for x in range(self.world.width):
            for y in range(self.world.height):
                tile_id = self.world.get_tile(x, y, 0)  # Layer 0
                tile_def = TILE_DEFINITIONS.get(tile_id)

                # Check for Water Source
                if tile_def and tile_def.has_component(WaterSource):
                    # Groundwater Logic: Pumps always work (Groundwater Table)
                    # Future: Reduce output if not near surface water

                    sources.append((x, y))
                    self.watered_tiles.add((x, y))

        # BFS
        queue = list(sources)
        visited = set(sources)

        while queue:
            curr_x, curr_y = queue.pop(0)
            neighbors = [
                (curr_x + 1, curr_y),
                (curr_x - 1, curr_y),
                (curr_x, curr_y + 1),
                (curr_x, curr_y - 1),
            ]

            for nx, ny in neighbors:
                if 0 <= nx < self.world.width and 0 <= ny < self.world.height:
                    if (nx, ny) not in visited:
                        # Check Layer -1 (Pipes)
                        t_pipe = self.world.get_tile(nx, ny, -1)
                        td_pipe = TILE_DEFINITIONS.get(t_pipe)

                        # Also Layer 0 (Buildings?) - if buildings conduct water
                        t_surf = self.world.get_tile(nx, ny, 0)
                        td_surf = TILE_DEFINITIONS.get(t_surf)

                        c_pipe = td_pipe and td_pipe.has_component(WaterConductor)
                        c_surf = td_surf and td_surf.has_component(WaterConductor)

                        if c_pipe or c_surf:
                            self.watered_tiles.add((nx, ny))
                            visited.add((nx, ny))
                            queue.append((nx, ny))

    def update_sewer_grid(self):
        """Propagate drainage from Map Edges (Sinks) back through pipes (-2)."""
        self.drained_tiles.clear()

        sinks = []
        # Find Sewer Pipes at Map Edges on Layer -2

        # Top/Bottom
        for x in range(self.world.width):
            for y in [0, self.world.height - 1]:
                t = self.world.get_tile(x, y, -2)
                td = TILE_DEFINITIONS.get(t)
                if td and td.has_component(SewerConductor):
                    sinks.append((x, y))
                    self.drained_tiles.add((x, y))

        # Left/Right
        for y in range(self.world.height):
            for x in [0, self.world.width - 1]:
                if (x, y) in self.drained_tiles:
                    continue
                t = self.world.get_tile(x, y, -2)
                td = TILE_DEFINITIONS.get(t)
                if td and td.has_component(SewerConductor):
                    sinks.append((x, y))
                    self.drained_tiles.add((x, y))

        # BFS
        queue = list(sinks)
        visited = set(sinks)

        while queue:
            curr_x, curr_y = queue.pop(0)
            neighbors = [
                (curr_x + 1, curr_y),
                (curr_x - 1, curr_y),
                (curr_x, curr_y + 1),
                (curr_x, curr_y - 1),
            ]

            for nx, ny in neighbors:
                if 0 <= nx < self.world.width and 0 <= ny < self.world.height:
                    if (nx, ny) not in visited:
                        # Check Layer -2 (Sewer Pipes)
                        t = self.world.get_tile(nx, ny, -2)
                        td = TILE_DEFINITIONS.get(t)

                        if td and td.has_component(SewerConductor):
                            self.drained_tiles.add((nx, ny))
                            visited.add((nx, ny))
                            queue.append((nx, ny))

    def update_stats(self):
        """Recalculate statistics like population."""
        pop = 0
        for x in range(self.world.width):
            for y in range(self.world.height):
                tile_id = self.world.get_tile(x, y)
                # Simple rules:
                # RES_LVL1 = 5 people
                if tile_id == TileType.RESIDENTIAL_LVL1:
                    pop += 5
                # TODO: Commercial/Industrial jobs
        self.population = pop

    def is_connected_to_road(self, x: int, y: int) -> bool:
        """Check if any adjacent tile is a road."""
        neighbors = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

        for nx, ny in neighbors:
            if 0 <= nx < self.world.width and 0 <= ny < self.world.height:
                if self.world.get_tile(nx, ny) == TileType.ROAD:
                    return True
        return False

    def update_labor_exchange(self):
        """Assign residents to jobs and calculate road usage."""
        self.road_usage.clear()

        seekers = []  # ((x,y), resident_count)
        employers = []  # ((x,y), open_slots)

        # 1. Census & Immigration
        for x in range(self.world.width):
            for y in range(self.world.height):
                tile = self.world.get_tile(x, y)
                td = TILE_DEFINITIONS.get(tile)
                if not td:
                    continue

                # POPULATION
                pop_def = td.get_component(Population)
                if pop_def:
                    # Get instance data
                    if not hasattr(self, "tile_data"):
                        self.tile_data = {}
                    data = self.tile_data.get(
                        (x, y), {"residents": 0, "workers": 0, "filled_jobs": 0}
                    )

                    # Immigration (Simple: Fill to capacity)
                    if data["residents"] < pop_def.capacity:
                        data["residents"] += 1  # 1 person per day immigration
                        self.tile_data[(x, y)] = data

                    if data["residents"] > 0:
                        seekers.append(((x, y), data["residents"]))

                # JOBS
                job_def = td.get_component(Jobs)
                if job_def:
                    if not hasattr(self, "tile_data"):
                        self.tile_data = {}
                    data = self.tile_data.get(
                        (x, y), {"residents": 0, "workers": 0, "filled_jobs": 0}
                    )

                    open_slots = job_def.capacity - data["filled_jobs"]
                    if open_slots > 0:
                        employers.append(((x, y), open_slots))

        # 2. Match & Pathfind
        for start_pos, count in seekers:
            best_job_pos = None
            min_dist = float("inf")

            for end_pos, capacity in employers:
                dist = abs(start_pos[0] - end_pos[0]) + abs(start_pos[1] - end_pos[1])
                if dist < min_dist:
                    min_dist = dist
                    best_job_pos = end_pos

            if best_job_pos:
                path = self.pathfinder.find_path(start_pos, best_job_pos)
                if path:
                    for px, py in path:
                        self.road_usage[(px, py)] = (
                            self.road_usage.get((px, py), 0) + count
                        )

    def update_traffic(self):
        """Update RoadStats.congestion based on road_usage."""
        # This is used by the Overlay system which reads self.road_usage
        pass
