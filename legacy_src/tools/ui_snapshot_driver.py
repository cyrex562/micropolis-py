import sys
import os
from pathlib import Path
import pygame

# Ensure src/ is in python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from micropolis.context import AppContext
from micropolis.app_config import AppConfig
from micropolis.ui.panel_manager import PanelManager
from micropolis.ui.panels.head_panel import HeadPanel
from micropolis.ui.panels.budget_panel import BudgetPanel
from micropolis.ui.panels.evaluation_panel import EvaluationPanel

OUTPUT_DIR = PROJECT_ROOT / "ui_snapshots"
OUTPUT_DIR.mkdir(exist_ok=True)


def setup_pygame_headless():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()


def create_mock_context():
    config = AppConfig()
    context = AppContext(config=config)
    context.city_name = "Snapshot City"
    context.total_funds = 20000
    context.total_pop = 123456
    context.game_level = 1  # Medium
    context.city_time = 100
    # Add other mock data as needed
    return context


def render_panel(panel_class, name, context, width, height, **kwargs):
    print(f"Rendering {name}...")
    surface = pygame.Surface((width, height))
    surface.fill((0, 0, 0))  # Background

    manager = PanelManager(context=context, surface=surface)

    # Manually instantiate panel to control isolation
    panel = panel_class(manager, context, **kwargs)
    panel.did_mount()
    panel.on_resize((width, height))  # Force layout

    # Mock some data if needed (refresh from context mainly)
    if hasattr(panel, "refresh_from_context"):
        panel.refresh_from_context()

    panel.render(surface)

    output_path = OUTPUT_DIR / f"{name}.png"
    pygame.image.save(surface, str(output_path))
    print(f"Saved {output_path}")


def main():
    setup_pygame_headless()
    context = create_mock_context()

    # Head Panel
    render_panel(HeadPanel, "head_panel", context, 1024, 150)

    # Budget Panel
    # Budget panel usually expects to be a certain size or responsive
    render_panel(BudgetPanel, "budget_panel", context, 400, 300)

    # Evaluation Panel
    render_panel(EvaluationPanel, "evaluation_panel", context, 400, 300)

    print("Snapshot generation complete.")


if __name__ == "__main__":
    main()
