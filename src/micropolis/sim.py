from typing import Any

from pydantic import BaseModel, Field

from micropolis.engine import create_editor_view
from micropolis.sim_view import SimView
from micropolis.sim_sprite import SimSprite


class Sim(BaseModel):
    """Main simulation structure containing all views and sprites"""

    editors: int = 0
    editor: SimView = Field(default_factory=create_editor_view)
    maps: int = 0
    map: SimView | None = None
    graphs: int = 0
    graph: Any | None = None  # SimGraph placeholder
    dates: int = 0
    date: Any | None = None  # SimDate placeholder
    sprites: int = 0
    sprite: SimSprite | None = None
    overlay: list[Any] = Field(default_factory=list[Any])  # Ink overlays
