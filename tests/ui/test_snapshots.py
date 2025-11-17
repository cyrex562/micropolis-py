"""
Example snapshot tests for pygame UI panels.

These tests demonstrate the golden-image snapshot testing workflow.
Run with UPDATE_GOLDEN=1 to regenerate reference images.
"""

from __future__ import annotations

import os

import pygame
import pytest

from tests.assertions import assert_surface_matches_golden


# Mark all tests as needing pygame initialization
pytestmark = pytest.mark.skipif(
    os.environ.get("SDL_VIDEODRIVER") != "dummy",
    reason="Snapshot tests require SDL_VIDEODRIVER=dummy for consistency",
)


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    """Initialize pygame in headless mode for all tests in this module."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    yield
    pygame.quit()


class TestEditorViewSnapshots:
    """Snapshot tests for editor view rendering."""

    def test_snapshot_empty_map(self):
        """Test rendering of an empty map with default overlay."""
        # Create a simple test surface
        surface = pygame.Surface((640, 480))
        surface.fill((0, 128, 0))  # Green background

        # Draw some test content (placeholder for actual editor rendering)
        pygame.draw.rect(surface, (255, 255, 255), (100, 100, 200, 200), 2)
        font = pygame.font.Font(None, 36)
        text = font.render("Editor View", True, (255, 255, 255))
        surface.blit(text, (150, 180))

        # Compare with golden image
        assert_surface_matches_golden(surface, "editor_empty_map", tolerance=0.95)

    def test_snapshot_population_overlay(self):
        """Test rendering of population density overlay."""
        surface = pygame.Surface((640, 480))
        surface.fill((0, 0, 128))  # Blue background

        # Draw population overlay representation
        pygame.draw.circle(surface, (255, 200, 0), (320, 240), 100)
        font = pygame.font.Font(None, 36)
        text = font.render("Population Overlay", True, (255, 255, 255))
        surface.blit(text, (200, 220))

        assert_surface_matches_golden(
            surface, "editor_population_overlay", tolerance=0.95
        )

    def test_snapshot_power_overlay(self):
        """Test rendering of power grid overlay with lightning blink."""
        surface = pygame.Surface((640, 480))
        surface.fill((40, 40, 40))  # Dark background

        # Draw power grid representation
        pygame.draw.line(surface, (255, 255, 0), (100, 240), (540, 240), 3)
        pygame.draw.line(surface, (255, 255, 0), (320, 100), (320, 380), 3)
        font = pygame.font.Font(None, 36)
        text = font.render("Power Grid", True, (255, 255, 0))
        surface.blit(text, (240, 200))

        assert_surface_matches_golden(surface, "editor_power_overlay", tolerance=0.95)


class TestMapViewSnapshots:
    """Snapshot tests for minimap rendering."""

    def test_snapshot_minimap_default(self):
        """Test minimap rendering with no overlay."""
        surface = pygame.Surface((200, 200))
        surface.fill((100, 150, 100))  # Greenish for terrain

        # Draw simple city representation
        pygame.draw.rect(surface, (128, 128, 128), (50, 50, 100, 100))
        pygame.draw.rect(surface, (200, 200, 200), (80, 80, 40, 40))

        assert_surface_matches_golden(surface, "minimap_default", tolerance=0.95)

    def test_snapshot_minimap_traffic_overlay(self):
        """Test minimap with traffic density overlay."""
        surface = pygame.Surface((200, 200))
        surface.fill((50, 50, 50))  # Dark background

        # Draw traffic heatmap
        colors = [(0, 255, 0), (255, 255, 0), (255, 128, 0), (255, 0, 0)]
        for i, color in enumerate(colors):
            x = 40 + i * 30
            pygame.draw.circle(surface, color, (x, 100), 15)

        assert_surface_matches_golden(
            surface, "minimap_traffic_overlay", tolerance=0.95
        )


class TestBudgetPanelSnapshots:
    """Snapshot tests for budget panel UI."""

    def test_snapshot_budget_panel_default(self):
        """Test budget panel with default values."""
        surface = pygame.Surface((400, 300))
        surface.fill((200, 200, 200))  # Gray background

        # Draw mock budget panel
        font = pygame.font.Font(None, 24)
        title = font.render("Budget Panel", True, (0, 0, 0))
        surface.blit(title, (120, 20))

        # Draw sliders
        slider_y = 80
        for label in ["Roads", "Fire", "Police"]:
            text = font.render(f"{label}:", True, (0, 0, 0))
            surface.blit(text, (50, slider_y))
            pygame.draw.rect(surface, (100, 100, 100), (150, slider_y, 200, 20))
            pygame.draw.rect(surface, (0, 128, 255), (150, slider_y, 150, 20))
            slider_y += 50

        assert_surface_matches_golden(surface, "budget_panel_default", tolerance=0.95)

    def test_snapshot_budget_panel_low_funds(self):
        """Test budget panel with low funding warnings."""
        surface = pygame.Surface((400, 300))
        surface.fill((200, 200, 200))  # Gray background

        # Draw warning indicator
        font = pygame.font.Font(None, 24)
        warning = font.render("LOW FUNDS!", True, (255, 0, 0))
        surface.blit(warning, (120, 20))

        # Draw depleted sliders
        slider_y = 80
        for label in ["Roads", "Fire", "Police"]:
            text = font.render(f"{label}:", True, (0, 0, 0))
            surface.blit(text, (50, slider_y))
            pygame.draw.rect(surface, (100, 100, 100), (150, slider_y, 200, 20))
            pygame.draw.rect(surface, (255, 0, 0), (150, slider_y, 50, 20))
            slider_y += 50

        assert_surface_matches_golden(surface, "budget_panel_low_funds", tolerance=0.95)


class TestGraphPanelSnapshots:
    """Snapshot tests for graph panel rendering."""

    def test_snapshot_population_graph(self):
        """Test population history graph rendering."""
        surface = pygame.Surface((500, 300))
        surface.fill((255, 255, 255))  # White background

        # Draw axes
        pygame.draw.line(surface, (0, 0, 0), (50, 250), (450, 250), 2)
        pygame.draw.line(surface, (0, 0, 0), (50, 50), (50, 250), 2)

        # Draw sample data line
        points = [(50, 250), (100, 220), (150, 180), (200, 150), (250, 160)]
        points += [(300, 130), (350, 110), (400, 100), (450, 90)]
        pygame.draw.lines(surface, (0, 128, 255), False, points, 3)

        # Label
        font = pygame.font.Font(None, 24)
        title = font.render("Population Growth", True, (0, 0, 0))
        surface.blit(title, (150, 20))

        assert_surface_matches_golden(surface, "graph_population", tolerance=0.95)


@pytest.mark.skipif(
    not os.environ.get("UPDATE_GOLDEN"),
    reason="Only run full suite when updating golden images",
)
class TestComprehensiveSnapshots:
    """
    Comprehensive snapshot tests that cover all major UI states.

    These tests are only run when UPDATE_GOLDEN is set to avoid
    long test times during normal development.
    """

    def test_snapshot_all_overlays(self):
        """Test all overlay types for regression detection."""
        overlays = [
            "population",
            "crime",
            "pollution",
            "traffic",
            "power",
            "fire_coverage",
            "police_coverage",
            "land_value",
        ]

        for overlay_name in overlays:
            surface = pygame.Surface((640, 480))
            surface.fill((64, 64, 64))

            # Simple representation of each overlay type
            font = pygame.font.Font(None, 48)
            text = font.render(overlay_name.title(), True, (255, 255, 255))
            text_rect = text.get_rect(center=(320, 240))
            surface.blit(text, text_rect)

            assert_surface_matches_golden(
                surface, f"overlay_{overlay_name}", tolerance=0.95
            )
