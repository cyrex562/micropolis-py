from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from micropolis.pie_menu import EntryType, PieMenu


@dataclass
class PieMenuEntry:
    """Individual entry in a pie menu."""

    type: EntryType
    piemenu: PieMenu
    label: str = ""
    bitmap: pygame.Surface | None = None

    # Display information
    width: int = 0
    height: int = 0
    x: int = 0
    y: int = 0
    x_offset: int = 0
    y_offset: int = 0
    label_x: int = 0
    label_y: int = 0

    # Pie slice information
    slice_size: float = 1.0  # Relative slice size
    angle: float = 0.0  # Angle through center of slice
    dx: float = 0.0  # Cosine of angle
    dy: float = 0.0  # Sine of angle
    subtend: float = 0.0  # Angle subtended by slice
    quadrant: int = 0  # Quadrant of leading edge
    slope: float = 0.0  # Slope of leading edge

    # Commands
    command: str | None = None
    preview: str | None = None
    name: str | None = None

    # State
    flags: int = 0

    def __post_init__(self):
        """Initialize after dataclass creation."""
        if not self.label:
            self.label = ""
