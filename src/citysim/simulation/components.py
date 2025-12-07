from typing import Optional
import dataclasses


class Component:
    """Base class/marker for components."""

    pass


@dataclasses.dataclass
class Cost(Component):
    value: int


@dataclasses.dataclass
class Growth(Component):
    target_id: int
    chance: float = 1.0


@dataclasses.dataclass
class RenderInfo(Component):
    color: tuple[float, float, float]
    height: float = 0.1


@dataclasses.dataclass
class Description(Component):
    name: str
    info: str = ""


@dataclasses.dataclass
class PowerSource(Component):
    """Generates power."""

    capacity: int = 1000
    radius: int = 4


@dataclasses.dataclass
class PowerConsumer(Component):
    """Consumes power."""

    demand: int = 10


class PowerConductor(Component):
    """Conducts power (Lines, Buildings)."""

    pass


@dataclasses.dataclass
class WaterSource(Component):
    """Generates water (Pumps)."""

    capacity: int = 1000
    radius: int = 6


@dataclasses.dataclass
class WaterConsumer(Component):
    """Consumes water."""

    demand: int = 10


class WaterConductor(Component):
    """Conducts water (Pipes)."""

    pass


@dataclasses.dataclass
class SewerSource(Component):
    """Produces sewage."""

    output: int = 10


class SewerSink(Component):
    """Accepts sewage (Map Edge / Treatment)."""

    pass


@dataclasses.dataclass
class SewerConductor(Component):
    """Conducts sewage (Pipes)."""

    pass


@dataclasses.dataclass
class Population(Component):
    """Residents and Workers."""

    capacity: int = 0
    residents: int = 0
    workers: int = 0


@dataclasses.dataclass
class Jobs(Component):
    """Workplaces."""

    capacity: int = 0
    filled: int = 0


@dataclasses.dataclass
class RoadStats(Component):
    """Traffic info."""

    capacity: int = 100
    speed_limit: float = 1.0
    congestion: float = 0.0  # 0.0 to 1.0
