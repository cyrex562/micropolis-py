import numpy as np
from citysim.simulation.tile import TileType


class GameMap:
    def __init__(self, width: int = 64, height: int = 64, water_threshold: float = 0.1):
        self.width = width
        self.height = height
        self.water_threshold = water_threshold
        # Layers:
        #  1: Air (Power Lines)
        #  0: Surface (Roads, Buildings, Zones)
        # -1: Water (Pipes)
        # -2: Sewer (Pipes)
        self.layers = {
            1: np.full((width, height), TileType.EMPTY, dtype=np.int32),
            0: np.full((width, height), TileType.DIRT, dtype=np.int32),
            -1: np.full((width, height), TileType.EMPTY, dtype=np.int32),
            -2: np.full((width, height), TileType.EMPTY, dtype=np.int32),
        }
        self.generate_terrain()

    def generate_terrain(self):
        """Procedurally generate water bodies."""
        # Simple Cellular Automata for Water
        # 1. Random seeding
        water_seeds = np.random.random((self.width, self.height)) < self.water_threshold
        self.layers[0][water_seeds] = TileType.WATER

        # 2. Grow/Smooth (Iterate a few times)
        for _ in range(3):
            new_grid = self.layers[0].copy()
            for x in range(self.width):
                for y in range(self.height):
                    # Count water neighbors
                    water_count = 0
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                if self.layers[0][nx, ny] == TileType.WATER:
                                    water_count += 1

                    if self.layers[0][x, y] == TileType.WATER:
                        if water_count >= 2:  # Keep
                            new_grid[x, y] = TileType.WATER
                        else:  # Die (too isolated)
                            new_grid[x, y] = TileType.DIRT
                    else:
                        if water_count >= 5:  # Born (surrounded)
                            new_grid[x, y] = TileType.WATER
            self.layers[0] = new_grid

        # 3. Ensure Minimum Water
        if np.sum(self.layers[0] == TileType.WATER) == 0:
            # Force a small lake in the center
            cx, cy = self.width // 2, self.height // 2
            for x in range(cx - 2, cx + 3):
                for y in range(cy - 2, cy + 3):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        self.layers[0][x, y] = TileType.WATER

    def get_tile(self, x: int, y: int, layer: int = 0) -> int:
        if layer not in self.layers:
            return TileType.EMPTY
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.layers[layer][x, y]
        return TileType.EMPTY

    def set_tile(self, x: int, y: int, type_id: int, layer: int = 0):
        if layer not in self.layers:
            # Create layer if it implies a new valid layer?
            # For now restrict to 0 and -1 defined in init or explicitly allow expansion
            # Let's auto-create for robustness if needed, or strictly enforce
            self.layers[layer] = np.full(
                (self.width, self.height), TileType.EMPTY, dtype=np.int32
            )

        if 0 <= x < self.width and 0 <= y < self.height:
            self.layers[layer][x, y] = type_id

    def to_dict(self) -> dict:
        """Serialize map data to dictionary."""
        # Serialize all layers
        layers_data = {}
        for l_id, grid in self.layers.items():
            layers_data[str(l_id)] = grid.flatten().tolist()

        return {"width": self.width, "height": self.height, "layers": layers_data}

    @staticmethod
    def from_dict(data: dict) -> "GameMap":
        """Create GameMap from serialized data."""
        width = data["width"]
        height = data["height"]
        game_map = GameMap(width, height)

        # Restore layers
        if "layers" in data:
            layers_data = data["layers"]
            game_map.layers = {}
            for l_id_str, grid_list in layers_data.items():
                l_id = int(l_id_str)
                game_map.layers[l_id] = np.array(grid_list, dtype=np.int32).reshape(
                    (width, height)
                )
        elif "grid" in data:
            # Backward compatibility
            game_map.layers[0] = np.array(data["grid"], dtype=np.int32).reshape(
                (width, height)
            )

        return game_map
