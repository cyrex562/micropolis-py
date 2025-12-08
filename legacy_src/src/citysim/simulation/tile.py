from enum import IntEnum, auto
from typing import Type, TypeVar, Optional
from citysim.simulation.components import (
    Component,
    Cost,
    Growth,
    RenderInfo,
    Description,
    PowerSource,
    PowerConsumer,
    PowerConductor,
    WaterSource,
    WaterConsumer,
    WaterConductor,
    SewerSource,
    SewerSink,
    SewerConductor,
    Population,
    Jobs,
    RoadStats,
)

T = TypeVar("T", bound=Component)


class TileType(IntEnum):
    EMPTY = 0
    DIRT = 1
    WATER = 2
    ROAD = 3
    RESIDENTIAL = 4
    COMMERCIAL = 5
    INDUSTRIAL = 6
    POWER_PLANT = 7
    POWER_LINE = 8
    WATER_PUMP = 9
    WATER_PIPE = 10
    SEWER_PIPE = 14  # Jump ID? Or keep sequential? Let's use 14 to avoid developed zones overlap if needed, or re-ID. Developed starts at 11.

    # Developed Zones
    RESIDENTIAL_LVL1 = 11
    COMMERCIAL_LVL1 = 12
    INDUSTRIAL_LVL1 = 13


class TileDef:
    """
    Component-based definition for a tile type.
    """

    def __init__(self, *components: Component):
        self._components = {type(c): c for c in components}

    def get_component(self, component_type: Type[T]) -> Optional[T]:
        return self._components.get(component_type)

    def has_component(self, component_type: Type[T]) -> bool:
        return component_type in self._components

    # Helper properties for backward compatibility / ease of use during refactor
    # (Optional: can remove these later to enforce strict component usage)
    @property
    def name(self) -> str:
        desc = self.get_component(Description)
        return desc.name if desc else "Unknown"

    @property
    def cost(self) -> int:
        c = self.get_component(Cost)
        return c.value if c else 0

    @property
    def color(self):
        r = self.get_component(RenderInfo)
        return r.color if r else (1.0, 0.0, 1.0)

    @property
    def height(self) -> float:
        r = self.get_component(RenderInfo)
        return r.height if r else 0.1

    @property
    def growth_target(self) -> int:
        g = self.get_component(Growth)
        return g.target_id if g else 0


# Definitions for rendering and logic
TILE_DEFINITIONS = {
    # TileType.EMPTY: Removed to prevent rendering. Implicitly None.
    TileType.DIRT: TileDef(
        Description("Dirt"), RenderInfo((0.4, 0.3, 0.2), 0.1), Cost(0)
    ),
    TileType.WATER: TileDef(
        Description("Water"), RenderInfo((0.2, 0.4, 0.8), 0.1), Cost(0)
    ),
    TileType.ROAD: TileDef(
        Description("Road"),
        RenderInfo((0.2, 0.2, 0.2), 0.15),
        Cost(10),
        RoadStats(capacity=100, speed_limit=1.0),
    ),
    TileType.POWER_LINE: TileDef(
        Description("Power Line"),
        RenderInfo((0.9, 0.9, 0.4), 0.4),
        Cost(5),
        PowerConductor(),
    ),
    TileType.WATER_PUMP: TileDef(
        Description("Water Pump"),
        RenderInfo((0.2, 0.6, 1.0), 0.8),
        Cost(500),
        WaterSource(),
        PowerConsumer(demand=50),
        PowerConductor(),
    ),
    TileType.WATER_PIPE: TileDef(
        Description("Water Pipe"),
        RenderInfo((0.2, 0.6, 1.0), 0.2),
        Cost(5),
        WaterConductor(),
    ),
    TileType.SEWER_PIPE: TileDef(
        Description("Sewer Pipe"),
        RenderInfo((0.4, 0.3, 0.1), 0.2),
        Cost(5),
        SewerConductor(),
    ),
    # Zones (Undeveloped)
    TileType.RESIDENTIAL: TileDef(
        Description("Residential (Zone)"),
        RenderInfo((0.0, 0.4, 0.0), 0.1),
        Growth(TileType.RESIDENTIAL_LVL1),
        Cost(100),
        PowerConductor(),
        WaterConductor(),
        SewerConductor(),
        Population(capacity=5),
    ),
    TileType.COMMERCIAL: TileDef(
        Description("Commercial (Zone)"),
        RenderInfo((0.0, 0.0, 0.4), 0.1),
        Growth(TileType.COMMERCIAL_LVL1),
        Cost(100),
        PowerConductor(),
        WaterConductor(),
        SewerConductor(),
        Jobs(capacity=5),
    ),
    TileType.INDUSTRIAL: TileDef(
        Description("Industrial (Zone)"),
        RenderInfo((0.4, 0.4, 0.0), 0.1),
        Growth(TileType.INDUSTRIAL_LVL1),
        Cost(100),
        PowerConductor(),
        WaterConductor(),
        SewerConductor(),
        Jobs(capacity=8),
    ),
    # Developed
    TileType.RESIDENTIAL_LVL1: TileDef(
        Description("Small House"),
        RenderInfo((0.0, 0.8, 0.0), 0.5),
        Cost(0),
        PowerConsumer(),
        PowerConductor(),
        WaterConsumer(),
        WaterConductor(),
        SewerSource(),
        SewerConductor(),
        Population(capacity=20),
    ),
    TileType.COMMERCIAL_LVL1: TileDef(
        Description("Small Shop"),
        RenderInfo((0.0, 0.0, 0.8), 0.6),
        Cost(0),
        PowerConsumer(),
        PowerConductor(),
        WaterConsumer(),
        WaterConductor(),
        SewerSource(),
        SewerConductor(),
        Jobs(capacity=15),
    ),
    TileType.INDUSTRIAL_LVL1: TileDef(
        Description("Factory"),
        RenderInfo((0.8, 0.8, 0.0), 0.7),
        Cost(0),
        PowerConsumer(),
        PowerConductor(),
        WaterConsumer(),
        WaterConductor(),
        SewerSource(),
        SewerConductor(),
        Jobs(capacity=30),
    ),
    TileType.POWER_PLANT: TileDef(
        Description("Power Plant"),
        RenderInfo((0.8, 0.2, 0.2), 2.0),
        Cost(1000),
        PowerSource(),
        PowerConductor(),
    ),
}
