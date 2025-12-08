import pygame
import pygame_gui
from pygame_gui.elements import (
    UIPanel,
    UILabel,
    UIButton,
    UIDropDownMenu,
    UIHorizontalSlider,
)


class MainMenu:
    def __init__(self, manager: pygame_gui.UIManager, width: int, height: int):
        self.manager = manager
        self.width = width
        self.height = height
        self.active = True

        # Output Config
        self.start_game_requested = False
        self.load_game_requested = False
        self.game_config = {
            "width": 64,  # Default
            "height": 64,
            "water_threshold": 0.1,
        }

        self.panel = None
        self._setup_ui()

    def _setup_ui(self):
        # Full Screen Panel
        self.panel = UIPanel(
            relative_rect=pygame.Rect((0, 0), (self.width, self.height)),
            manager=self.manager,
            starting_height=1,
        )

        # Title
        UILabel(
            relative_rect=pygame.Rect((self.width // 2 - 150, 50), (300, 50)),
            text="CitySim 3D",
            manager=self.manager,
            container=self.panel,
            object_id="#main_menu_title",
        )

        # Buttons
        self.btn_new = UIButton(
            relative_rect=pygame.Rect((self.width // 2 - 100, 150), (200, 50)),
            text="New Game",
            manager=self.manager,
            container=self.panel,
        )

        self.btn_load = UIButton(
            relative_rect=pygame.Rect((self.width // 2 - 100, 220), (200, 50)),
            text="Load Game",
            manager=self.manager,
            container=self.panel,
        )

        self.btn_exit = UIButton(
            relative_rect=pygame.Rect((self.width // 2 - 100, 290), (200, 50)),
            text="Exit",
            manager=self.manager,
            container=self.panel,
        )

        # --- Config Panel (Hidden Initially) ---
        self.config_panel = UIPanel(
            relative_rect=pygame.Rect((self.width // 2 - 150, 150), (300, 300)),
            manager=self.manager,
            visible=False,
            starting_height=2,
        )

        # Sub-Elements of Config Panel
        UILabel(
            pygame.Rect((20, 20), (260, 30)),
            "New Game Settings",
            self.manager,
            container=self.config_panel,
        )

        UILabel(
            pygame.Rect((20, 60), (100, 30)),
            "Map Size:",
            self.manager,
            container=self.config_panel,
        )
        self.dd_size = UIDropDownMenu(
            options_list=["64x64", "128x128", "256x256"],
            starting_option="64x64",
            relative_rect=pygame.Rect((130, 60), (150, 30)),
            manager=self.manager,
            container=self.config_panel,
        )

        UILabel(
            pygame.Rect((20, 110), (100, 30)),
            "Water %:",
            self.manager,
            container=self.config_panel,
        )
        self.slider_water = UIHorizontalSlider(
            relative_rect=pygame.Rect((130, 110), (150, 30)),
            start_value=10.0,
            value_range=(0.0, 100.0),
            manager=self.manager,
            container=self.config_panel,
        )
        self.lbl_water_val = UILabel(
            pygame.Rect((130, 140), (150, 20)),
            "10%",
            self.manager,
            container=self.config_panel,
        )

        self.btn_start = UIButton(
            relative_rect=pygame.Rect((50, 230), (200, 40)),
            text="Start Simulation",
            manager=self.manager,
            container=self.config_panel,
        )
        self.btn_back = UIButton(
            relative_rect=pygame.Rect((50, 275), (200, 20)),
            text="Back",
            manager=self.manager,
            container=self.config_panel,
        )

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_new:
                self.config_panel.show()
                # Hide main buttons? Or just cover them

            elif event.ui_element == self.btn_load:
                self.load_game_requested = True

            elif event.ui_element == self.btn_exit:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

            elif event.ui_element == self.btn_start:
                # Read Config
                size_str = self.dd_size.selected_option
                # selected_option might be a tuple (text, value) or just text depending on version/config
                if isinstance(size_str, tuple):
                    size_str = size_str[0]

                size = int(size_str.split("x")[0])
                water = self.slider_water.get_current_value() / 100.0

                self.game_config["width"] = size
                self.game_config["height"] = size
                self.game_config["water_threshold"] = water
                self.start_game_requested = True

            elif event.ui_element == self.btn_back:
                self.config_panel.hide()

        elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == self.slider_water:
                val = int(event.value)
                self.lbl_water_val.set_text(f"{val}%")

    def resize(self, width, height):
        self.width = width
        self.height = height
        # Recreate UI or just ignore for prototype?
        # Ideally update rects, but for now recreation is safer to keep centered.
        self.panel.kill()
        self.config_panel.kill()
        self._setup_ui()

    def hide(self):
        self.active = False
        self.panel.hide()
        self.config_panel.hide()

    def show(self):
        self.active = True
        self.panel.show()
        # Startup state: Main buttons visible, config hidden
        self.config_panel.hide()
