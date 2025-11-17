from __future__ import annotations

from dataclasses import dataclass, field

from .base import Color


@dataclass(frozen=True)
class ThemePalette:
    """Color palette entries consumed by widgets."""

    background: Color = (24, 26, 27, 255)
    surface: Color = (36, 41, 46, 255)
    surface_alt: Color = (45, 51, 57, 255)
    border: Color = (64, 72, 79, 255)
    border_focus: Color = (102, 153, 255, 255)
    text: Color = (236, 239, 244, 255)
    text_muted: Color = (189, 195, 199, 255)
    accent: Color = (0, 174, 255, 255)
    accent_hover: Color = (64, 196, 255, 255)
    accent_active: Color = (0, 140, 210, 255)
    danger: Color = (255, 91, 87, 255)
    success: Color = (138, 226, 52, 255)
    warning: Color = (255, 165, 0, 255)
    tooltip_bg: Color = (15, 15, 15, 240)
    tooltip_text: Color = (245, 245, 245, 255)


@dataclass(frozen=True)
class ThemeMetrics:
    """Spacing, fonts, and sizing guidelines for widgets."""

    padding: int = 8
    gutter: int = 6
    border_radius: int = 4
    focus_width: int = 2
    font_name: str = "DejaVuSans"
    font_size: int = 15
    font_size_small: int = 13
    font_size_large: int = 18
    icon_size: int = 18
    tooltip_delay_ms: int = 300


@dataclass
class Theme:
    name: str
    palette: ThemePalette = field(default_factory=ThemePalette)
    metrics: ThemeMetrics = field(default_factory=ThemeMetrics)

    def derive(
        self,
        *,
        name: str | None = None,
        palette: ThemePalette | None = None,
        metrics: ThemeMetrics | None = None,
    ) -> Theme:
        return Theme(
            name=name or self.name,
            palette=palette or self.palette,
            metrics=metrics or self.metrics,
        )


class ThemeManager:
    """Registry of named themes to share across UI components."""

    def __init__(self) -> None:
        self._themes: dict[str, Theme] = {}
        self._active_theme: Theme
        self.register_theme(Theme(name="MicropolisDark"))
        self._active_theme = self._themes["MicropolisDark"]

    @property
    def current(self) -> Theme:
        return self._active_theme

    def register_theme(self, theme: Theme) -> None:
        self._themes[theme.name] = theme

    def set_active(self, name: str) -> Theme:
        if name not in self._themes:
            raise KeyError(f"Unknown theme '{name}'")
        self._active_theme = self._themes[name]
        return self._active_theme

    def get(self, name: str | None = None) -> Theme:
        if name is None:
            return self._active_theme
        try:
            return self._themes[name]
        except KeyError as exc:  # pragma: no cover - defensive
            raise KeyError(f"Theme '{name}' is not registered") from exc


# Shared singleton theme manager for convenience
THEME_MANAGER = ThemeManager()
