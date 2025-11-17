"""Scenario picker panel for Micropolis pygame UI."""

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


# Scenario definitions matching file_io.py
SCENARIOS = [
    {
        "id": 1,
        "name": "Dullsville",
        "subtitle": "USA 1900 - Boredom",
        "description": "Can you bring life to this sleepy town?",
    },
    {
        "id": 2,
        "name": "San Francisco",
        "subtitle": "CA 1906 - Earthquake",
        "description": "Rebuild after the devastating earthquake.",
    },
    {
        "id": 3,
        "name": "Hamburg",
        "subtitle": "Germany 1944 - Bombing",
        "description": "Recover from WWII devastation.",
    },
    {
        "id": 4,
        "name": "Bern",
        "subtitle": "Switzerland 1965 - Traffic",
        "description": "Solve the growing traffic crisis.",
    },
    {
        "id": 5,
        "name": "Tokyo",
        "subtitle": "Japan 1957 - Monster Attack",
        "description": "Defend against monster attacks!",
    },
    {
        "id": 6,
        "name": "Detroit",
        "subtitle": "MI 1972 - Crime",
        "description": "Combat rising crime rates.",
    },
    {
        "id": 7,
        "name": "Boston",
        "subtitle": "MA 2010 - Nuclear Meltdown",
        "description": "Handle a nuclear disaster.",
    },
    {
        "id": 8,
        "name": "Rio de Janeiro",
        "subtitle": "Brazil 2047 - Coastal Flooding",
        "description": "Manage flooding and climate issues.",
    },
]


@dataclass
class ScenarioButton:
    """Clickable scenario selection button."""

    scenario_id: int
    rect: pygame.Rect
    name: str
    thumbnail: pygame.Surface | None = None
    highlight: pygame.Surface | None = None
    hovered: bool = False


@dataclass
class DifficultyCheckbox:
    """Difficulty level checkbox."""

    level: int
    name: str
    rect: pygame.Rect
    checked_img: pygame.Surface | None = None
    unchecked_img: pygame.Surface | None = None
    highlight_img: pygame.Surface | None = None
    hovered: bool = False


class ScenarioPickerPanel(UIPanel):
    """Grid of scenario thumbnails with difficulty selection."""

    def __init__(self, manager: PanelManager, context: AppContext) -> None:
        super().__init__(manager, context)
        self.panel_id = "scenario_picker"
        self.legacy_name = "scenario"
        self._background: pygame.Surface | None = None
        self._scenario_buttons: list[ScenarioButton] = []
        self._difficulty_checkboxes: list[DifficultyCheckbox] = []
        self._selected_difficulty = 0  # 0=Easy, 1=Medium, 2=Hard

    def did_mount(self) -> None:
        """Load resources and create UI elements."""
        logger.info("Mounting scenario picker")
        self._load_background()
        self._create_scenario_buttons()
        self._create_difficulty_checkboxes()

    def did_unmount(self) -> None:
        """Clean up resources."""
        logger.info("Unmounting scenario picker")

    def draw(self, surface: pygame.Surface) -> None:
        """Render scenario picker."""
        if not self.visible:
            return

        # Draw background
        if self._background:
            surface.blit(self._background, (0, 0))
        else:
            surface.fill((0, 0, 0))

        # Draw scenario button highlights
        for btn in self._scenario_buttons:
            if btn.hovered and btn.highlight:
                surface.blit(btn.highlight, btn.rect.topleft)

        # Draw difficulty checkboxes
        for cb in self._difficulty_checkboxes:
            # Draw checked/unchecked state
            if cb.level == self._selected_difficulty and cb.checked_img:
                surface.blit(cb.checked_img, cb.rect.topleft)
            elif cb.level != self._selected_difficulty and cb.unchecked_img:
                surface.blit(cb.unchecked_img, cb.rect.topleft)

            # Draw highlight if hovered
            if cb.hovered and cb.highlight_img:
                surface.blit(cb.highlight_img, cb.rect.topleft)

        # Draw difficulty labels if needed
        self._draw_difficulty_labels(surface)

    def handle_panel_event(self, event: Any) -> bool:
        """Handle input events."""
        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            # Update hover states for scenario buttons
            for btn in self._scenario_buttons:
                was_hovered = btn.hovered
                btn.hovered = btn.rect.collidepoint(pos)
                if btn.hovered != was_hovered:
                    self.invalidate()

            # Update hover states for difficulty checkboxes
            for cb in self._difficulty_checkboxes:
                was_hovered = cb.hovered
                cb.hovered = cb.rect.collidepoint(pos)
                if cb.hovered != was_hovered:
                    self.invalidate()
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            # Check scenario button clicks
            for btn in self._scenario_buttons:
                if btn.rect.collidepoint(pos):
                    self._on_scenario_selected(btn.scenario_id)
                    return True

            # Check difficulty checkbox clicks
            for cb in self._difficulty_checkboxes:
                if cb.rect.collidepoint(pos):
                    self._on_difficulty_selected(cb.level)
                    return True

        # Keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            # Number keys for scenarios
            if pygame.K_1 <= event.key <= pygame.K_8:
                scenario_id = event.key - pygame.K_0
                self._on_scenario_selected(scenario_id)
                return True

            # Difficulty shortcuts
            if event.key == pygame.K_e:
                self._on_difficulty_selected(0)  # Easy
                return True
            elif event.key == pygame.K_m:
                self._on_difficulty_selected(1)  # Medium
                return True
            elif event.key == pygame.K_h:
                self._on_difficulty_selected(2)  # Hard
                return True

            # Escape to go back
            if event.key == pygame.K_ESCAPE:
                self._on_back()
                return True

        return False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_background(self) -> None:
        """Load scenario picker background."""
        try:
            if hasattr(self.context, "resource_dir"):
                bg_path = (
                    Path(self.context.resource_dir)
                    / "assets"
                    / "images"
                    / "background-micropolis.png"
                )
                if bg_path.exists():
                    self._background = pygame.image.load(str(bg_path))
                    logger.info("Loaded scenario picker background")
        except Exception as e:
            logger.error(f"Error loading scenario picker background: {e}")

    def _create_scenario_buttons(self) -> None:
        """Create clickable scenario buttons."""
        # Layout matching micropolis.tcl:
        # Row 1: scenarios 1-4 at y=451
        # Row 2: scenarios 5-8 at y=639
        # Each button: 209x188
        # X positions: 310, 519, 727, 936

        positions = [
            (310, 451),  # scenario 1
            (519, 451),  # scenario 2
            (727, 450),  # scenario 3
            (936, 450),  # scenario 4
            (310, 639),  # scenario 5
            (519, 639),  # scenario 6 (Rio, mapped to id 8)
            (728, 638),  # scenario 7
            (937, 638),  # scenario 8 (actually Detroit, id 6)
        ]

        # Note: Legacy TCL has swapped ordering for scenarios 6 and 8
        scenario_map = [1, 2, 3, 4, 5, 8, 7, 6]

        for idx, (x, y) in enumerate(positions):
            scenario_id = scenario_map[idx]
            rect = pygame.Rect(x, y, 209, 188)
            name = SCENARIOS[scenario_id - 1]["name"]

            # Load highlight image
            highlight = self._load_image(f"scenario{idx + 1}hilite.png")

            btn = ScenarioButton(scenario_id, rect, name, None, highlight, False)
            self._scenario_buttons.append(btn)

    def _create_difficulty_checkboxes(self) -> None:
        """Create difficulty selection checkboxes."""
        # Coordinates matching micropolis.tcl
        # Easy: x=982, y=106
        # Medium: x=982, y=176
        # Hard: x=982, y=246
        # Each: 190x70

        difficulty_defs = [
            (0, "Easy", 982, 106),
            (1, "Medium", 982, 176),
            (2, "Hard", 982, 246),
        ]

        for level, name, x, y in difficulty_defs:
            rect = pygame.Rect(x, y, 190, 70)

            # Load checkbox images
            checked = self._load_image(f"checkbox{level + 1}checked.png")
            unchecked = self._load_image(f"checkbox{level + 1}hilite.png")
            highlight = self._load_image(f"checkbox{level + 1}hilitechecked.png")

            cb = DifficultyCheckbox(
                level, name, rect, checked, unchecked, highlight, False
            )
            self._difficulty_checkboxes.append(cb)

    def _load_image(self, img_name: str) -> pygame.Surface | None:
        """Load an image from assets."""
        try:
            if hasattr(self.context, "resource_dir"):
                img_path = (
                    Path(self.context.resource_dir) / "assets" / "images" / img_name
                )
                if img_path.exists():
                    return pygame.image.load(str(img_path))
        except Exception as e:
            logger.debug(f"Could not load image {img_name}: {e}")
        return None

    def _draw_difficulty_labels(self, surface: pygame.Surface) -> None:
        """Draw difficulty level text labels."""
        try:
            font = pygame.font.Font(None, 24)
            labels = ["Easy", "Medium", "Hard"]
            y_positions = [106, 176, 246]

            for label, y in zip(labels, y_positions):
                # Highlight selected difficulty
                is_selected = labels.index(label) == self._selected_difficulty
                color = (255, 255, 0) if is_selected else (255, 255, 255)
                text_surf = font.render(label, True, color)
                # Position label to the right of checkbox
                surface.blit(text_surf, (1000, y + 25))
        except Exception as e:
            logger.debug(f"Could not draw labels: {e}")

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_scenario_selected(self, scenario_id: int) -> None:
        """Handle scenario selection."""
        logger.info(
            f"Scenario {scenario_id} selected "
            f"with difficulty {self._selected_difficulty}"
        )

        # Load the scenario
        from src.micropolis import file_io

        try:
            file_io.LoadScenario(self.context, scenario_id)

            # Set difficulty (game_level attribute)
            self.context.game_level = self._selected_difficulty

            # Emit game start event
            if hasattr(self.manager, "_event_bus"):
                self.manager._event_bus.publish(
                    "game.start",
                    {"mode": "scenario", "scenario_id": scenario_id},
                )

            # Hide picker
            self.hide()
        except Exception as e:
            logger.error(f"Failed to load scenario {scenario_id}: {e}")

    def _on_difficulty_selected(self, level: int) -> None:
        """Handle difficulty selection."""
        logger.info(f"Difficulty {level} selected")
        self._selected_difficulty = level
        self.invalidate()

    def _on_back(self) -> None:
        """Handle back navigation."""
        logger.info("Going back from scenario picker")
        if hasattr(self.manager, "_event_bus"):
            self.manager._event_bus.publish("splash.show", {})
        self.hide()
