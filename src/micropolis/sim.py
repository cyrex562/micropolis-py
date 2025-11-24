from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from micropolis.context import AppContext
from micropolis.sim_sprite import SimSprite
from micropolis.sim_view import SimView


class Sim(BaseModel):
    """Main simulation structure containing all views and sprites"""

    editors: int = 0
    editor: SimView | None = None
    maps: int = 0
    map: SimView | None = None
    graphs: int = 0
    graph: Any | None = None  # SimGraph placeholder
    dates: int = 0
    date: Any | None = None  # SimDate placeholder
    sprites: int = 0
    sprite: SimSprite | None = None
    overlay: list[Any] = Field(default_factory=list[Any])  # Ink overlays
    context: "AppContext | None" = None


SimView.model_rebuild()


def MakeNewSim(context: "AppContext") -> Sim:  # noqa: N802 - legacy name
    """Create a new simulation instance with all required views.

    This creates:
    - Editor view for 16x16 tile editing
    - Map view for minimap display
    - Graph view for statistics
    - Date view for calendar display
    """
    from micropolis.sim_view import create_editor_view, create_map_view
    from micropolis.view_types import MakeNewSimDate, MakeNewSimGraph

    sim = Sim()
    sim.context = context

    # Create and initialize editor view
    sim.editor = create_editor_view(context)
    sim.editors = 1
    sim.editor.sim = sim

    # Create and initialize map view
    sim.map = create_map_view(context)
    sim.maps = 1
    sim.map.sim = sim

    # Create graph view
    sim.graph = MakeNewSimGraph()
    sim.graphs = 1

    # Create date view
    sim.date = MakeNewSimDate()
    sim.dates = 1

    return sim
