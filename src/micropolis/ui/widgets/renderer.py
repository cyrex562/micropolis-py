from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import Color, Point, Rect, WidgetRenderer


@dataclass(slots=True)
class RenderCommand:
    name: str
    payload: dict[str, Any]


class RecordingRenderer(WidgetRenderer):
    """Renderer implementation that records draw commands for testing."""

    def __init__(self) -> None:
        self.commands: list[RenderCommand] = []

    def draw_rect(
        self,
        rect: Rect,
        color: Color,
        border: bool = False,
        border_color: Color | None = None,
        radius: int = 0,
    ) -> None:
        self.commands.append(
            RenderCommand(
                "rect",
                {
                    "rect": rect,
                    "color": color,
                    "border": border,
                    "border_color": border_color,
                    "radius": radius,
                },
            )
        )

    def draw_text(
        self,
        text: str,
        position: Point,
        color: Color,
        font: str | None = None,
        size: int | None = None,
    ) -> None:
        self.commands.append(
            RenderCommand(
                "text",
                {
                    "text": text,
                    "position": position,
                    "color": color,
                    "font": font,
                    "size": size,
                },
            )
        )

    def draw_line(
        self,
        start: Point,
        end: Point,
        color: Color,
        width: int = 1,
    ) -> None:
        self.commands.append(
            RenderCommand(
                "line",
                {
                    "start": start,
                    "end": end,
                    "color": color,
                    "width": width,
                },
            )
        )

    def draw_image(
        self,
        image_id: str,
        dest: Rect,
        tint: Color | None = None,
    ) -> None:
        self.commands.append(
            RenderCommand(
                "image",
                {
                    "image_id": image_id,
                    "dest": dest,
                    "tint": tint,
                },
            )
        )


class NullRenderer(WidgetRenderer):
    """Renderer that silently ignores draw calls (default headless mode)."""

    def draw_rect(
        self,
        rect: Rect,
        color: Color,
        border: bool = False,
        border_color: Color | None = None,
        radius: int = 0,
    ) -> None:  # pragma: no cover - intentionally empty
        return None

    def draw_text(
        self,
        text: str,
        position: Point,
        color: Color,
        font: str | None = None,
        size: int | None = None,
    ) -> None:  # pragma: no cover - intentionally empty
        return None

    def draw_line(
        self,
        start: Point,
        end: Point,
        color: Color,
        width: int = 1,
    ) -> None:  # pragma: no cover - intentionally empty
        return None

    def draw_image(
        self,
        image_id: str,
        dest: Rect,
        tint: Color | None = None,
    ) -> None:  # pragma: no cover - intentionally empty
        return None


__all__ = ["RenderCommand", "RecordingRenderer", "NullRenderer"]
