import dataclasses
from typing import Tuple


@dataclasses.dataclass
class GameConfig:
    """Holds all configuration for the game engine."""

    # Window settings
    window_width: int = 1280
    window_height: int = 720
    window_title: str = "CitySim 3D"
    fullscreen: bool = False

    # Rendering settings
    vsync: bool = True
    target_fps: int = 60

    # OpenGL settings
    gl_major_version: int = 3
    gl_minor_version: int = 3

    # Background color (Clean Slate)
    clear_color: Tuple[float, float, float, float] = (0.2, 0.3, 0.3, 1.0)

    @classmethod
    def default(cls) -> "GameConfig":
        return cls()
