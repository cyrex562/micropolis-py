import pygame
from pygame.locals import *
import pygame_gui
import numpy as np

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
except ImportError:
    print("PyOpenGL is not installed.")
    raise

from citysim.core.config import GameConfig
from citysim.rendering.renderer import Renderer
from citysim.rendering.camera import Camera
from citysim.rendering.mesh import MeshBuilder, InstancedMesh
from citysim.rendering.ui_overlay import UIOverlay
from citysim.simulation.world import GameMap
from citysim.simulation.tile import TILE_DEFINITIONS, TileType
from citysim.simulation.simulation import Simulation


class Engine:
    """
    The core engine class responsible for initializing the game,
    handling the main loop, events, and rendering.
    """

    def __init__(self, config: GameConfig = None):
        if config is None:
            config = GameConfig.default()
        self.config = config
        self.running = False
        self.clock = pygame.time.Clock()

        self.screen = None
        self._init_pygame()

        # Rendering (Must be after context creation)
        self.renderer = Renderer()
        self._init_opengl()

        self.camera = Camera(position=(32, 20, 32), yaw=-135, pitch=-30)
        self.meshes = {}

        # Game World
        self.world = GameMap(64, 64)

        # Simulation
        self.simulation = Simulation(self.world)

        # Use InstancedMesh instead of standard mesh
        base_cube = MeshBuilder.create_cube()
        self.cube_mesh = InstancedMesh(
            base_cube.vertices, base_cube.indices, max_instances=64 * 64 * 2
        )
        self.preview_mesh = base_cube  # Use base cube for drag preview

        self.world_dirty = True  # Flag to trigger instance update
        self.current_instance_count = 0

        # Traffic Overlay
        base_plane = MeshBuilder.create_plane()
        self.traffic_mesh = InstancedMesh(base_plane.vertices, max_instances=64 * 64)
        self.view_mode = "NORMAL"  # NORMAL, TRAFFIC
        self.traffic_current_instances = 0

        # Gameplay State
        self.selected_tool = TileType.ROAD
        self.layer_view = 0  # 0 = Surface, -1 = Underground

        # Interaction State
        self.is_dragging = False
        self.drag_start = (0, 0)
        self.drag_current = (0, 0)

        # User Interface
        self.ui_manager = pygame_gui.UIManager(
            (self.config.window_width, self.config.window_height)
        )
        self.ui_overlay = UIOverlay(self.config.window_width, self.config.window_height)
        self.ui_surface = pygame.Surface(
            (self.config.window_width, self.config.window_height), flags=pygame.SRCALPHA
        )

        self._setup_ui()

    def _setup_ui(self):
        """Create initial UI elements."""

        # --- Top Bar ---
        self.top_bar = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((0, 0), (self.config.window_width, 40)),
            manager=self.ui_manager,
            starting_height=1,
        )

        self.lbl_title = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 5), (250, 30)),
            text="CitySim 3D - Alpha",
            manager=self.ui_manager,
            container=self.top_bar,
        )

        self.lbl_pop = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((300, 5), (150, 30)),
            text="Population: 0",
            manager=self.ui_manager,
            container=self.top_bar,
        )

        self.lbl_date = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((460, 5), (150, 30)),
            text="Day: 0",
            manager=self.ui_manager,
            container=self.top_bar,
        )

        self.btn_view_mode = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((620, 5), (150, 30)),
            text="View: Normal",
            manager=self.ui_manager,
            container=self.top_bar,
        )

        # --- Toolbox ---
        self.toolbar_window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect((10, 50), (200, 600)),
            manager=self.ui_manager,
            window_display_title="Toolbox",
        )

        # Helper to create buttons
        y_offset = 10

        def create_tool_btn(text, tool_type):
            nonlocal y_offset
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((10, y_offset), (150, 30)),
                text=text,
                manager=self.ui_manager,
                container=self.toolbar_window,
            )
            # Store tool type via a custom attribute for easy checking
            btn.tool_type = tool_type
            y_offset += 40
            return btn

        # Helper for generic buttons
        def create_action_btn(text):
            nonlocal y_offset
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((10, y_offset), (150, 30)),
                text=text,
                manager=self.ui_manager,
                container=self.toolbar_window,
            )
            y_offset += 40
            return btn

        self.btn_road = create_tool_btn("Build Road", TileType.ROAD)
        self.btn_power = create_tool_btn("Power Line", TileType.POWER_LINE)
        self.btn_plant = create_tool_btn("Power Plant", TileType.POWER_PLANT)
        self.btn_res = create_tool_btn("Residential", TileType.RESIDENTIAL)
        self.btn_com = create_tool_btn("Commercial", TileType.COMMERCIAL)
        self.btn_ind = create_tool_btn("Industrial", TileType.INDUSTRIAL)
        self.btn_pump = create_tool_btn("Water Pump", TileType.WATER_PUMP)
        self.btn_pipe = create_tool_btn("Water Pipe", TileType.WATER_PIPE)
        self.btn_sewer = create_tool_btn("Sewer Pipe", TileType.SEWER_PIPE)
        self.btn_bulldoze = create_tool_btn("Bulldoze", TileType.DIRT)

        y_offset += 10  # Spacer
        self.btn_layer = create_action_btn("Layer: Surface")
        self.btn_save = create_action_btn("Save Game")
        self.btn_load = create_action_btn("Load Game")

        # --- Inspector Panel ---
        self.inspector_window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect((self.config.window_width - 210, 50), (200, 200)),
            manager=self.ui_manager,
            window_display_title="Inspector",
            visible=False,  # Hidden by default
        )

        self.lbl_inspector_info = pygame_gui.elements.UITextBox(
            html_text="Select a tile...",
            relative_rect=pygame.Rect((10, 10), (180, 150)),
            manager=self.ui_manager,
            container=self.inspector_window,
        )

    def _init_pygame(self):
        pygame.init()
        flags = DOUBLEBUF | OPENGL | RESIZABLE
        if self.config.fullscreen:
            flags |= FULLSCREEN

        pygame.display.set_caption(self.config.window_title)

        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
        )

        self.screen = pygame.display.set_mode(
            (self.config.window_width, self.config.window_height), flags
        )
        print(
            f"Display initialized: {self.config.window_width}x{self.config.window_height}"
        )

    def _init_opengl(self):
        print(f"OpenGL Renderer: {glGetString(GL_RENDERER).decode()}")
        print(f"OpenGL Version: {glGetString(GL_VERSION).decode()}")

        glViewport(0, 0, self.config.window_width, self.config.window_height)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glClearColor(*self.config.clear_color)

    def handle_events(self, dt: float):
        for event in pygame.event.get():
            # Pass event to UI
            if self.ui_manager.process_events(event):
                # If UI consumed it, make sure we don't process world clicks for tools
                # But allow tool selection
                if event.type == MOUSEBUTTONDOWN:
                    # Very simple check: if we clicked UI, don't drag world
                    continue

            if event.type == QUIT:
                self.running = False
            elif event.type == MOUSEWHEEL:
                self.camera.process_zoom(event.y)
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if self.is_dragging:
                        self.is_dragging = False
                        print("Drag cancelled.")
                    else:
                        self.running = False
                elif event.key == K_t:
                    self.toggle_view_mode()
            elif event.type == VIDEORESIZE:
                self.config.window_width, self.config.window_height = event.size
                self.renderer.update_viewport(event.w, event.h)
                self.camera.aspect_ratio = event.w / event.h

                # Resize UI
                self.ui_manager.set_window_resolution((event.w, event.h))
                self.ui_overlay.resize(event.w, event.h)
                self.ui_surface = pygame.Surface(
                    (event.w, event.h), flags=pygame.SRCALPHA
                )

                # Update Top Bar size
                self.top_bar.set_dimensions((event.w, 40))

            # UI Events
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                # Check if the button has a tool_type attribute
                if hasattr(event.ui_element, "tool_type"):
                    print(f"Tool Selection: {event.ui_element.text}")
                    self.selected_tool = event.ui_element.tool_type

                    # Auto-switch layer based on tool
                    if self.selected_tool in [TileType.WATER_PIPE, TileType.SEWER_PIPE]:
                        if self.layer_view == 0:
                            self.layer_view = -1
                            self.btn_layer.set_text("Layer: Underground")
                            self.world_dirty = True
                    elif self.selected_tool in [TileType.WATER_PUMP]:
                        # Ensure Surface
                        if self.layer_view == -1:
                            self.layer_view = 0
                            self.btn_layer.set_text("Layer: Surface")
                            self.world_dirty = True

                # Check for Save/Load/Layer
                elif event.ui_element == self.btn_layer:
                    if self.layer_view == 0:
                        self.layer_view = -1
                        self.btn_layer.set_text("Layer: Underground")
                    else:
                        self.layer_view = 0
                        self.btn_layer.set_text("Layer: Surface")
                    self.world_dirty = True

                elif event.ui_element == self.btn_save:
                    self.save_game()
                elif event.ui_element == self.btn_load:
                    self.load_game()
                elif event.ui_element == self.btn_view_mode:
                    self.toggle_view_mode()

            # Mouse Interaction
            elif event.type == MOUSEBUTTONDOWN:
                # Raycast
                # Only if not clicking inside a window (simple check)
                if not self.toolbar_window.rect.collidepoint(event.pos) and (
                    not self.inspector_window.visible
                    or not self.inspector_window.rect.collidepoint(event.pos)
                ):
                    origin, direction = self.camera.get_mouse_ray(
                        event.pos[0],
                        event.pos[1],
                        self.config.window_width,
                        self.config.window_height,
                    )

                    if abs(direction[1]) > 0.0001:
                        t = -origin[1] / direction[1]
                        if t > 0:
                            hit_point = origin + t * direction
                            gx = int(round(hit_point[0]))
                            gy = int(round(hit_point[2]))

                            if event.button == 1:  # Left Click: Tool / Drag
                                self.is_dragging = True
                                self.drag_start = (gx, gy)
                                self.drag_current = (gx, gy)

                            elif event.button == 3:  # Right Click
                                if self.is_dragging:
                                    self.is_dragging = False
                                    print("Drag cancelled.")
                                else:
                                    self.show_inspector(gx, gy)

            elif event.type == MOUSEMOTION:
                if self.is_dragging:
                    # Update current drag pos
                    origin, direction = self.camera.get_mouse_ray(
                        event.pos[0],
                        event.pos[1],
                        self.config.window_width,
                        self.config.window_height,
                    )

                    if abs(direction[1]) > 0.0001:
                        t = -origin[1] / direction[1]
                        if t > 0:
                            hit_point = origin + t * direction
                            gx = int(round(hit_point[0]))
                            gy = int(round(hit_point[2]))
                            self.drag_current = (gx, gy)

                            # Orthogonal Constraint for Linear Tools
                            is_linear_tool = self.selected_tool in [
                                TileType.ROAD,
                                TileType.POWER_LINE,
                                TileType.WATER_PIPE,
                                TileType.SEWER_PIPE,
                            ]
                            if is_linear_tool:
                                dx = abs(self.drag_current[0] - self.drag_start[0])
                                dy = abs(self.drag_current[1] - self.drag_start[1])
                                if dx > dy:
                                    # Horizontal
                                    self.drag_current = (
                                        self.drag_current[0],
                                        self.drag_start[1],
                                    )
                                else:
                                    # Vertical
                                    self.drag_current = (
                                        self.drag_start[0],
                                        self.drag_current[1],
                                    )

            elif event.type == MOUSEBUTTONUP:
                if event.button == 1 and self.is_dragging:
                    self.is_dragging = False
                    # Apply Tool to all affected tiles
                    tiles = self.get_affected_tiles(self.drag_start, self.drag_current)
                    for tx, ty in tiles:
                        self.apply_tool(tx, ty)

        # Camera Input
        keys = pygame.key.get_pressed()
        if keys[K_w]:
            self.camera.process_keyboard("FORWARD", dt)
        if keys[K_s]:
            self.camera.process_keyboard("BACKWARD", dt)
        if keys[K_a]:
            self.camera.process_keyboard("LEFT", dt)
        if keys[K_d]:
            self.camera.process_keyboard("RIGHT", dt)
        if keys[K_q]:
            self.camera.yaw -= 90 * dt
            self.camera.update_vectors()
        if keys[K_e]:
            self.camera.yaw += 90 * dt
            self.camera.update_vectors()

    def get_affected_tiles(self, start, end):
        """Calculate list of tiles based on tool type (Line vs Rect)."""
        tiles = []
        x1, y1 = start
        x2, y2 = end

        # Clamp to world bounds
        x1 = max(0, min(x1, self.world.width - 1))
        y1 = max(0, min(y1, self.world.height - 1))
        x2 = max(0, min(x2, self.world.width - 1))
        y2 = max(0, min(y2, self.world.height - 1))

        if self.selected_tool == TileType.ROAD:
            # Line Calculation (Bresenham-like or just iterate)
            # For simplicity: Bresenham
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            sx = 1 if x1 < x2 else -1
            sy = 1 if y1 < y2 else -1
            err = dx - dy

            curr_x, curr_y = x1, y1
            while True:
                tiles.append((curr_x, curr_y))
                if curr_x == x2 and curr_y == y2:
                    break
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    curr_x += sx
                if e2 < dx:
                    err += dx
                    curr_y += sy
        else:
            # Rectangle (Zones, Bulldoze)
            min_x, max_x = min(x1, x2), max(x1, x2)
            min_y, max_y = min(y1, y2), max(y1, y2)

            for x in range(min_x, max_x + 1):
                for y in range(min_y, max_y + 1):
                    tiles.append((x, y))

        return tiles

    def apply_tool(self, x: int, y: int):
        """Apply the currently selected tool to the grid."""
        if 0 <= x < self.world.width and 0 <= y < self.world.height:
            layer = 0
            if self.selected_tool == TileType.POWER_LINE:
                layer = 1  # Air
            elif self.selected_tool == TileType.WATER_PIPE:
                layer = -1  # Underground
            elif self.selected_tool == TileType.SEWER_PIPE:
                layer = -2  # Deep Underground
            elif self.layer_view == -1 and self.selected_tool == TileType.DIRT:
                # Bulldoze in underground view clears the deepest pipe or just water?
                # User expectations: Bulldoze clears what I see.
                # If we see both pipes, maybe we clear both? Or default to -1.
                layer = -1
            elif self.layer_view == 0 and self.selected_tool == TileType.DIRT:
                # Smart Bulldoze on Surface: Check Air Layer (1) first (Power Lines)
                air_tile = self.world.get_tile(x, y, 1)
                if air_tile and air_tile != 0:
                    layer = 1
                else:
                    layer = 0
            elif self.layer_view == -1:
                # Restrict other tools
                print("Cannot build surface structures underground!")
                return

            # Reduce spam
            # print(f"Applying {self.selected_tool.name} at ({x}, {y}) Layer {layer}")
            self.world.set_tile(x, y, self.selected_tool, layer=layer)
            self.world_dirty = True
        else:
            print("Out of bounds")

    def show_inspector(self, x, y):
        """Show inspector window with details for tile at x,y."""
        if 0 <= x < self.world.width and 0 <= y < self.world.height:
            # Recreate Logic if killed
            if not self.inspector_window or not self.inspector_window.alive():
                self.inspector_window = pygame_gui.elements.UIWindow(
                    rect=pygame.Rect((self.config.window_width - 210, 50), (200, 200)),
                    manager=self.ui_manager,
                    window_display_title="Inspector",
                    visible=False,
                )

                self.lbl_inspector_info = pygame_gui.elements.UITextBox(
                    html_text="Select a tile...",
                    relative_rect=pygame.Rect((10, 10), (180, 150)),
                    manager=self.ui_manager,
                    container=self.inspector_window,
                )

            # Inspect active layer
            tile_id = self.world.get_tile(x, y, self.layer_view)
            tile_def = TILE_DEFINITIONS.get(tile_id)

            if tile_def:
                info = f"<b>{tile_def.name}</b><br><br>"
                info += f"Pos: ({x}, {y})<br>"
                info += f"Layer: {self.layer_view}<br>"
                info += f"Cost: ${tile_def.cost}<br>"

                # Power Status
                from citysim.simulation.components import (
                    PowerConsumer,
                    WaterConsumer,
                    SewerSource,
                )

                if tile_def.has_component(PowerConsumer):
                    is_powered = (x, y) in self.simulation.powered_tiles
                    status = (
                        "<font color='#00FF00'>Yes</font>"
                        if is_powered
                        else "<font color='#FF0000'>No</font>"
                    )
                    info += f"Powered: {status}<br>"

                # Water Status
                if tile_def.has_component(WaterConsumer):
                    is_watered = (x, y) in self.simulation.watered_tiles
                    status = (
                        "<font color='#00FF00'>Yes</font>"
                        if is_watered
                        else "<font color='#FF0000'>No</font>"
                    )
                    info += f"Water: {status}<br>"

                # Sewer Status
                if tile_def.has_component(SewerSource):
                    is_drained = (x, y) in self.simulation.drained_tiles
                    status = (
                        "<font color='#00FF00'>Yes</font>"
                        if is_drained
                        else "<font color='#FF0000'>No</font>"
                    )
                    info += f"Sewage: {status}<br>"

                self.lbl_inspector_info.set_text(info)
                self.inspector_window.show()

    def save_game(self):
        """Save the current city to savegame.json."""
        print("Saving game...")
        try:
            data = self.world.to_dict()
            import json

            with open("savegame.json", "w") as f:
                json.dump(data, f)
            print("Game saved!")
        except Exception as e:
            print(f"Failed to save game: {e}")

    def load_game(self):
        """Load the city from savegame.json."""
        print("Loading game...")
        try:
            import json
            import os

            if os.path.exists("savegame.json"):
                with open("savegame.json", "r") as f:
                    data = json.load(f)
                    self.world.from_dict(data)
                self.world_dirty = True
                print("Game loaded!")
            else:
                print("No savegame found.")
        except Exception as e:
            print(f"Failed to load game: {e}")

    def update(self, dt: float):
        self.ui_manager.update(dt)

        # Run Simulation
        sim_changed = self.simulation.tick(dt)
        if sim_changed:
            self.world_dirty = True

        # Update Info Bar
        self.lbl_pop.set_text(f"Population: {self.simulation.population}")
        self.lbl_date.set_text(f"Day: {self.simulation.day}")

        # Update FPS in title
        fps = self.clock.get_fps()
        pygame.display.set_caption(f"{self.config.window_title} - FPS: {fps:.1f}")

    def render(self):
        # 1. 3D Pass
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.renderer.set_camera(
            self.camera.get_view_matrix(),
            self.camera.get_projection_matrix(
                self.config.window_width, self.config.window_height
            ),
            self.camera.position,
        )

        # Update Instances if dirty
        if self.world_dirty:
            instance_data = []
            for x in range(self.world.width):
                for y in range(self.world.height):
                    # Iterate over relevant layers to support visibility
                    visible_layers = []
                    if self.layer_view == -1:
                        # Underground View
                        # 1. Deep Sewer (Layer -2) -> Y = -0.2
                        visible_layers.append((-2, -0.2))
                        # 2. Water (Layer -1) -> Y = -0.1
                        visible_layers.append((-1, -0.1))
                        # 3. Surface Ghosts -> Handled specially below
                    else:
                        # Surface View
                        # 1. Surface (Layer 0) -> Y = 0.0
                        visible_layers.append((0, 0.0))
                        # 2. Air (Layer 1) -> Y = +0.3 (Power Lines)
                        visible_layers.append((1, 0.3))

                    for l_id, y_offset in visible_layers:
                        tile_id = self.world.get_tile(x, y, l_id)
                        tile_def = TILE_DEFINITIONS.get(tile_id)
                        if tile_def:
                            # Construct per-instance data
                            instance_data.extend([1.0, 0.0, 0.0, 0.0])
                            instance_data.extend([0.0, tile_def.height, 0.0, 0.0])
                            instance_data.extend([0.0, 0.0, 1.0, 0.0])
                            instance_data.extend([float(x), y_offset, float(y), 1.0])
                            instance_data.extend(tile_def.color)

                    # Ghost Rendering (Surface Footprints in Underground View)
                    if self.layer_view == -1:
                        surface_id = self.world.get_tile(x, y, 0)  # Surface Layer 0

                        # Show Water Pumps fully to allow connection
                        if surface_id == TileType.WATER_PUMP:
                            s_def = TILE_DEFINITIONS.get(surface_id)
                            if s_def:
                                instance_data.extend([1.0, 0.0, 0.0, 0.0])
                                instance_data.extend([0.0, s_def.height, 0.0, 0.0])
                                instance_data.extend([0.0, 0.0, 1.0, 0.0])
                                instance_data.extend([float(x), 0.0, float(y), 1.0])
                                instance_data.extend(s_def.color)

                        # Show other buildings as Ghosts
                        elif surface_id and surface_id not in [
                            TileType.DIRT,
                            TileType.WATER,
                        ]:
                            s_def = TILE_DEFINITIONS.get(surface_id)
                            if s_def:
                                # Ghost: Flat, Inset, Native Color
                                instance_data.extend([0.8, 0.0, 0.0, 0.0])
                                instance_data.extend([0.0, 0.05, 0.0, 0.0])
                                instance_data.extend([0.0, 0.0, 0.8, 0.0])
                                # Translation: Center the 0.8 scale (offset by 0.1)
                                # Y offset = 0.15 (Above the 0.1 floor height)
                                instance_data.extend(
                                    [float(x) + 0.1, 0.15, float(y) + 0.1, 1.0]
                                )
                                instance_data.extend(s_def.color)

            if instance_data:
                data_np = np.array(instance_data, dtype=np.float32)
                self.cube_mesh.update_instances(data_np)
                self.current_instance_count = len(instance_data) // 19
            else:
                self.current_instance_count = 0

            self.world_dirty = False

        # Draw Instanced
        if self.current_instance_count > 0:
            self.renderer.use_instanced()
            self.cube_mesh.draw(self.current_instance_count)

        # Traffic Overlay
        if self.view_mode == "TRAFFIC":
            self.update_traffic_overlay()  # Optimize: only when dirty?
            if self.traffic_current_instances > 0:
                self.renderer.use_instanced()
                self.traffic_mesh.draw(self.traffic_current_instances)

        # 2. Draw Preview if Dragging
        if self.is_dragging:
            self.renderer.use()  # Basic shader
            tiles = self.get_affected_tiles(self.drag_start, self.drag_current)

            # Preview color
            preview_color = (1.0, 1.0, 1.0)
            if self.selected_tool in TILE_DEFINITIONS:
                preview_color = TILE_DEFINITIONS[self.selected_tool].color

            # Draw elevated preview cubes
            for tx, ty in tiles:
                model = np.identity(4, dtype=np.float32)
                model[1][1] = 0.5  # constant height for preview
                model[0][3] = float(tx)
                model[1][3] = 0.5  # Hoist up a bit
                model[2][3] = float(ty)

                self.renderer.set_model_matrix(model)
                glUniform3f(self.renderer.color_mod_loc, *preview_color)
                self.preview_mesh.draw()

        # 3. UI Pass
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)

        self.ui_surface.fill((0, 0, 0, 0))
        self.ui_manager.draw_ui(self.ui_surface)
        self.ui_overlay.render(self.ui_surface)

        pygame.display.flip()

    def run(self):
        print("Starting engine loop...")
        self.running = True
        while self.running:
            dt = self.clock.tick(self.config.target_fps) / 1000.0
            # dt is in seconds
            self.handle_events(dt)
            self.update(dt)
            self.render()
        self.quit()

    def toggle_view_mode(self):
        if self.view_mode == "NORMAL":
            self.view_mode = "TRAFFIC"
            self.btn_view_mode.set_text("View: Traffic")
        else:
            self.view_mode = "NORMAL"
            self.btn_view_mode.set_text("View: Normal")

    def update_traffic_overlay(self):
        """Rebuild traffic mesh instances."""
        instance_data = []

        # Max capacity for coloring (100 is default road cap)
        MAX_CAP = 100.0

        for pos, count in self.simulation.road_usage.items():
            x, y = pos
            # If not in bounds or view range, skip?

            # Color
            ratio = count / MAX_CAP
            if ratio < 0.5:
                color = (0.0, 1.0, 0.0)  # Green
            elif ratio < 0.9:
                color = (1.0, 1.0, 0.0)  # Yellow
            else:
                color = (1.0, 0.0, 0.0)  # Red

            # Construct Matrix
            # Pos x, y, z. Y needs to be slightly above road (Road is at Y=0 ?)
            # Actually Road definition in render loop says: Y=0.0
            # Height of Road block is 0.15 (RenderInfo).
            # So we draw at Y = 0.2

            instance_data.extend([1.0, 0.0, 0.0, 0.0])
            instance_data.extend([0.0, 1.0, 0.0, 0.0])
            instance_data.extend([0.0, 0.0, 1.0, 0.0])
            instance_data.extend([float(x), 0.25, float(y), 1.0])
            instance_data.extend(color)

        if instance_data:
            data_np = np.array(instance_data, dtype=np.float32)
            self.traffic_mesh.update_instances(data_np)
            self.traffic_current_instances = len(instance_data) // 19
        else:
            self.traffic_current_instances = 0

    def quit(self):
        print("Engine shutting down.")
        self.cube_mesh.delete()
        self.traffic_mesh.delete()
        pygame.quit()
