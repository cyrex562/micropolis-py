"""Splash screen scene for Micropolis pygame UI."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame

from micropolis.ui.uipanel import UIPanel

if TYPE_CHECKING:
    from micropolis.context import AppContext
    from micropolis.ui.panel_manager import PanelManager

logger = logging.getLogger(__name__)


@dataclass
class Hotspot:
    """Clickable hotspot on splash background."""

    name: str
    rect: pygame.Rect
    callback: Any
    highlight_surf: pygame.Surface | None = None
    hovered: bool = False


class SplashScene(UIPanel):
    """Full-screen splash scene with clickable hotspots."""

    def __init__(self, manager: PanelManager, context: AppContext) -> None:
        super().__init__(manager, context)
        self.panel_id = "splash"
        self.legacy_name = "splash"
        self._background: pygame.Surface | None = None
        self._hotspots: list[Hotspot] = []
        self._timer_id: str | None = None

    def did_mount(self) -> None:
        """Load resources and set up hotspots."""
        logger.info("Mounting splash scene")
        self._load_background()
        self._create_hotspots()
        self._schedule_transition()

    def did_unmount(self) -> None:
        """Clean up resources."""
        logger.info("Unmounting splash scene")
        if self._timer_id and hasattr(self.manager, "timer_service"):
            try:
                self.manager.timer_service.cancel(self._timer_id)
            except Exception as e:
                logger.debug(f"Could not cancel timer: {e}")
        self._timer_id = None

    def draw(self, surface: pygame.Surface) -> None:
        """Render splash screen."""
        if not self.visible:
            return

        # Draw background
        if self._background:
            surface.blit(self._background, (0, 0))
        else:
            surface.fill((0, 0, 0))

        # Draw hotspot highlights when hovered
        for hotspot in self._hotspots:
            if hotspot.hovered and hotspot.highlight_surf:
                surface.blit(hotspot.highlight_surf, hotspot.rect.topleft)

    def handle_panel_event(self, event: Any) -> bool:
        """Handle input events."""
        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            for hotspot in self._hotspots:
                was_hovered = hotspot.hovered
                hotspot.hovered = hotspot.rect.collidepoint(pos)
                if hotspot.hovered != was_hovered:
                    self.invalidate()
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for hotspot in self._hotspots:
                if hotspot.rect.collidepoint(pos):
                    hotspot.callback()
                    return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_l:
                self._on_load()
                return True
            elif event.key in (pygame.K_g, pygame.K_n):
                self._on_generate()
                return True
            elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                self._on_quit()
                return True
            elif event.key == pygame.K_a:
                self._on_about()
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._on_auto_advance()
                return True

        return False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_background(self) -> None:
        """Load splash background image."""
        try:
            # Try to load from asset manager
            if hasattr(self.context, "resource_dir"):
                bg_path = (
                    Path(self.context.resource_dir)
                    / "assets"
                    / "images"
                    / "background-micropolis.png"
                )
                if bg_path.exists():
                    self._background = pygame.image.load(str(bg_path))
                    logger.info(f"Loaded splash background from {bg_path}")
                    return
            logger.warning("Could not load splash background")
        except Exception as e:
            logger.error(f"Error loading splash background: {e}")

    def _create_hotspots(self) -> None:
        """Create clickable hotspots matching legacy layout."""
        # These coords match micropolis.tcl for 1200x900 background
        # Coordinates: (x, y, width, height)
        hotspot_defs = [
            ("load", 70, 238, 157, 90, self._on_load, "button1hilite.png"),
            ("generate", 62, 392, 157, 90, self._on_generate, "button2hilite.png"),
            ("quit", 68, 544, 157, 90, self._on_quit, "button3hilite.png"),
            ("about", 101, 705, 157, 90, self._on_about, "button4hilite.png"),
        ]

        for name, x, y, w, h, callback, img_name in hotspot_defs:
            rect = pygame.Rect(x, y, w, h)
            highlight = self._load_highlight(img_name)
            hotspot = Hotspot(name, rect, callback, highlight, False)
            self._hotspots.append(hotspot)

    def _load_highlight(self, img_name: str) -> pygame.Surface | None:
        """Load a highlight image for a hotspot."""
        try:
            if hasattr(self.context, "resource_dir"):
                img_path = (
                    Path(self.context.resource_dir) / "assets" / "images" / img_name
                )
                if img_path.exists():
                    return pygame.image.load(str(img_path))
        except Exception as e:
            logger.debug(f"Could not load highlight {img_name}: {e}")
        return None

    def _schedule_transition(self) -> None:
        """Schedule auto-advance to scenario picker."""
        if hasattr(self.manager, "timer_service"):
            try:
                self._timer_id = self.manager.timer_service.schedule(
                    delay_ms=5000,
                    callback=lambda _: self._on_auto_advance(),
                    repeating=False,
                )
            except Exception as e:
                logger.debug(f"Could not schedule timer: {e}")

    # ------------------------------------------------------------------
    # Hotspot callbacks
    # ------------------------------------------------------------------

    def _on_load(self) -> None:
        """Handle Load button."""
        logger.info("Load city clicked")
        if hasattr(self.manager, "_event_bus"):
            self.manager._event_bus.publish("file_dialog.show", {"mode": "load"})
        self.hide()

    def _on_generate(self) -> None:
        """Handle Generate button."""
        logger.info("Generate new city clicked")
        from src.micropolis import sim_control

        sim_control.generate_new_city(self.context)
        if hasattr(self.manager, "_event_bus"):
            self.manager._event_bus.publish("game.start", {"mode": "new"})
        self.hide()

    def _on_quit(self) -> None:
        """Handle Quit button."""
        logger.info("Quit clicked")
        if hasattr(self.manager, "_event_bus"):
            self.manager._event_bus.publish("app.quit", {})

    def _on_about(self) -> None:
        """Handle About button."""
        logger.info("About clicked")
        from src.micropolis import file_io

        try:
            about_path = Path(self.context.resource_dir) / "cities" / "about.cty"
            if about_path.exists():
                file_io.LoadCity(self.context, str(about_path))
                if hasattr(self.manager, "_event_bus"):
                    self.manager._event_bus.publish("game.start", {"mode": "about"})
                self.hide()
        except Exception as e:
            logger.error(f"Failed to load about city: {e}")

    def _on_auto_advance(self) -> None:
        """Auto-advance to scenario picker."""
        logger.info("Auto-advancing to scenario picker")
        if hasattr(self.manager, "_event_bus"):
            self.manager._event_bus.publish("scenario_picker.show", {})
        self.hide()
