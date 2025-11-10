# Micropolis C to Python Porting Checklist

This checklist outlines the sequence for porting C headers and source files from `src/sim/` to Python modules in `src/micropolis/`. Files are ordered by dependency - foundational components first, then dependent systems.

## Phase 1: Core Constants and Types

### Headers (Foundation)

- [x] `headers/mac.h` → `constants.py` (Macintosh emulation constants)
- [x] `headers/macros.h` → `macros.py` (Core macros and utility functions)
- [x] `headers/animtab.h` → `animation.py` (Animation tables)
- [x] `headers/sim.h` → `types.py` (Core data structures and constants)
- [x] `headers/view.h` → `view_types.py` (View and sprite definitions)

### Basic Utilities

- [x] `rand.c` + `random.c` → `random.py` (Random number generation)
- [x] `s_alloc.c` → `allocation.py` (Memory allocation utilities)

## Phase 2: Core Simulation Engine

### Initialization and Setup

- [x] `s_init.c` → `initialization.py` (Simulation initialization)
- [x] `g_setup.c` → `graphics_setup.py` (Graphics initialization - adapt for pygame)

### Main Simulation Loop

- [x] `s_sim.c` → `simulation.py` (Core simulation step logic)
- [x] `sim.c` → `engine.py` (Main simulation engine and state management)

### Zone System

- [x] `s_zone.c` → `zones.py` (Residential/commercial/industrial zone growth)
- [x] `s_scan.c` → `scanner.py` (Zone scanning and analysis)

### Infrastructure Systems

- [x] `s_power.c` → `power.py` (Power grid connectivity and management)
- [x] `s_traf.c` → `traffic.py` (Traffic simulation and pathfinding)

### Disaster System

- [x] `s_disast.c` → `disasters.py` (Fire, flood, earthquake, monster mechanics)

## Phase 3: Data Management

### File I/O

- [x] `s_fileio.c` → `file_io.py` (City save/load - .cty format compatibility)

### Evaluation and Statistics

- [x] `s_eval.c` → `evaluation.py` (City evaluation and scoring)
- [x] `s_gen.c` → `generation.py` (City generation algorithms)

### Messaging and Communication

- [x] `s_msg.c` → `messages.py` (In-game messages and notifications)

## Phase 4: Graphics and Views (Adapt for pygame)

### View Management

- [x] `g_map.c` → `map_view.py` (Map overview rendering)
- [x] `g_bigmap.c` → `editor_view.py` (Editor view with 16x16 pixel tiles)
- [x] `g_smmaps.c` → `mini_maps.py` (Small overview maps)

### Graphics Utilities

- [x] `g_ani.c` → `animations.py` (Animation handling)
- [x] `terrain/` → `terrain.py` (Terrain generation and management)

## Phase 5: User Interface Components (Replace TCL/Tk with pygame)

### Widget Implementations (High Priority - Core Gameplay)

- [x] `w_tool.c` → `tools.py` (Tool selection and application)
- [x] `w_editor.c` → `editor.py` (Map editor interface)
- [x] `w_sim.c` → `sim_control.py` (Simulation control and speed)

### Widget Implementations (Medium Priority - UI Polish)

- [x] `w_budget.c` → `budget.py` (Budget and finance management)
- [x] `w_eval.c` → `evaluation_ui.py` (City evaluation display)
- [x] `w_graph.c` → `graphs.py` (Population, money, pollution graphs)
- [x] `w_date.c` → `date_display.py` (Date and time display)

### Widget Implementations (Lower Priority - Advanced Features)

- [x] `w_sprite.c` → `sprite_manager.py` (Moving sprite management)
- [x] `w_piem.c` → `pie_menu.py` (Pie menu interface)
- [x] `w_net.c` → `network.py` (Multiplayer networking - if needed)

### Utility Widgets

- [x] `w_util.c` → `ui_utilities.py` (UI utility functions)
- [x] `w_keys.c` → `keyboard.py` (Keyboard input handling)
- [x] `w_resrc.c` → `resources.py` (Resource management)

## Phase 6: Platform Integration

### Sound and Media

- [x] `w_sound.c` → `audio.py` (Sound effect management - adapt for pygame mixer)

### External Interfaces

- [x] `w_x.c` → `platform.py` (Platform-specific code - adapt for pygame)
- [x] `w_tk.c` → `tkinter_bridge.py` (TK integration - replace with pygame event loop)

### Stubs and Compatibility

- [x] `w_stubs.c` → `stubs.py` (Stub implementations for unused features)

## Phase 7: Advanced Features (Optional)

### Camera and Viewport

- [x] `w_cam.c` + `g_cam.c` + `cam.h` → `camera.py` (Camera controls - if implemented)

### Printing and Export

- [x] `w_print.c` → `printing.py` (Print functionality - if needed)

### Interactivity

- [x] `w_inter.c` → `interactions.py` (Interactive elements)

### Update Management

- [x] `w_update.c` → `updates.py` (UI update management)

## Phase 8: Testing and Validation

### Test Files (Create alongside porting)

- [ ] `test_constants.py` - Verify constants match C version
- [ ] `test_simulation.py` - Compare simulation outputs with C version
- [ ] `test_zones.py` - Validate zone growth algorithms
- [ ] `test_file_io.py` - Ensure .cty file compatibility
- [ ] `test_power.py` - Verify power grid connectivity
- [ ] `test_traffic.py` - Validate traffic simulation

## Porting Guidelines

### For Each File

1. **Read C source** and understand algorithm/logic
2. **Identify dependencies** on other modules
3. **Create Python equivalent** with proper type hints
4. **Preserve algorithmic fidelity** - match C behavior exactly
5. **Add comprehensive tests** before moving to next file
6. **Document deviations** from C version (if any)

### Key Considerations

- **Bit operations**: Maintain exact bitwise logic for tile status flags
- **Coordinate systems**: Preserve world (0-119,0-99) vs screen pixel coordinates
- **Memory layout**: Use appropriate Python data structures (lists, bytearrays, etc.)
- **Performance**: Avoid O(n²) operations on 120x100 grid
- **Randomness**: Use same PRNG algorithm for reproducible results

### Testing Strategy

- **Unit tests**: Test individual functions against known C outputs
- **Integration tests**: Compare full simulation steps with C version
- **Compatibility tests**: Load/save .cty files and verify identical results
- **Performance tests**: Maintain 60 FPS simulation loop target

## Success Criteria

- [ ] All core simulation algorithms ported and tested
- [ ] City files (.cty) load/save identically to C version
- [ ] Zone growth, traffic, disasters behave identically
- [ ] Basic pygame UI functional for core gameplay
- [ ] 60 FPS performance maintained
- [ ] Sugar activity integration working

---

# Phase 9: Complete Pygame UI Integration (Current Priority)

## Map Rendering Implementation

### Tile Graphics Loading
- [x] Load tile graphics from `res/tiles.png` or equivalent
- [ ] Implement `get_tile_surface()` function for extracting 16x16 editor tiles
- [ ] Implement `get_small_tile_surface()` function for 3x3 map view tiles
- [ ] Create tile cache system for performance optimization
- [ ] Handle tile transparency and alpha blending

### Map Display System
- [ ] Create `MapRenderer` class for managing map display
- [ ] Implement editor view rendering (16x16 pixels per tile, 120x100 tiles)
- [ ] Implement map view rendering (3x3 pixels per tile, scaled overview)
- [ ] Add viewport scrolling and panning functionality
- [ ] Implement zoom levels (editor vs map view)
- [ ] Add smooth scrolling animation

### Overlay Rendering
- [ ] Implement population density overlay rendering
- [ ] Implement crime rate overlay rendering
- [ ] Implement pollution overlay rendering
- [ ] Implement traffic density overlay rendering
- [ ] Implement power grid connectivity overlay
- [ ] Add overlay toggle controls (keyboard shortcuts)

## Input Handling System

### Mouse Input
- [ ] Implement mouse position tracking in world coordinates
- [ ] Add mouse click detection for tool application
- [ ] Implement drag selection for area tools
- [ ] Add mouse wheel zoom functionality
- [ ] Handle mouse cursor changes based on selected tool

### Keyboard Input
- [ ] Implement tool selection hotkeys (B=bull-dozer, R=road, etc.)
- [ ] Add simulation speed controls (pause, slow, normal, fast)
- [ ] Implement overlay toggle keys (P=population, C=crime, etc.)
- [ ] Add camera movement keys (arrow keys, WASD)
- [ ] Implement save/load keyboard shortcuts

### Tool System Integration
- [ ] Connect tool selection to mouse input handling
- [ ] Implement tool application logic (tile modification)
- [ ] Add tool preview (ghost tiles showing placement)
- [ ] Handle tool restrictions (can't build on water, etc.)
- [ ] Add undo/redo functionality for tools

## Simulation Loop Integration

### Game Loop Architecture
- [ ] Refactor `pygame_main_loop()` to use proper game loop structure
- [ ] Implement fixed timestep for simulation updates (60 FPS target)
- [ ] Add variable simulation speed controls
- [ ] Separate rendering from simulation updates
- [ ] Add frame rate limiting and vsync support

### Simulation State Management
- [ ] Connect simulation step calls to game loop
- [ ] Implement pause/resume functionality
- [ ] Add simulation speed controls (1x, 2x, 4x, paused)
- [ ] Handle simulation state persistence
- [ ] Add simulation statistics tracking

### Event-Driven Updates
- [ ] Implement event queue for simulation events
- [ ] Add disaster event triggering and handling
- [ ] Handle population growth notifications
- [ ] Implement budget cycle updates
- [ ] Add evaluation period triggers

## UI Panels Implementation

### Core UI Framework
- [ ] Create `UIPanel` base class for all UI components
- [ ] Implement panel positioning and layout system
- [ ] Add panel show/hide toggle functionality
- [ ] Create font loading and text rendering system
- [ ] Implement button and control widgets

### Budget Panel
- [ ] Create budget display panel with current funds
- [ ] Implement tax rate sliders (residential, commercial, industrial)
- [ ] Add budget allocation controls (police, fire, education)
- [ ] Display budget history and trends
- [ ] Add budget help and tooltips

### Evaluation Panel
- [ ] Implement city evaluation scoring display
- [ ] Add population, pollution, and crime statistics
- [ ] Create problem/solution recommendation system
- [ ] Add evaluation history tracking
- [ ] Implement auto-evaluation toggle

### Graph Panels
- [ ] Create population growth graph over time
- [ ] Implement money/funds graph display
- [ ] Add pollution trend graphs
- [ ] Create crime rate historical graphs
- [ ] Add graph time scale controls (1 year, 10 years, etc.)

### Date and Status Display
- [ ] Implement game date display (year/month/day)
- [ ] Add city name display and editing
- [ ] Create population counter display
- [ ] Add funds display with formatting
- [ ] Implement difficulty level indicator

## Sugar Protocol Integration

### Communication Protocol
- [ ] Implement stdin/stdout message parsing in `Micropolis.py`
- [ ] Add Sugar command handling (SugarStartUp, SugarActivate, etc.)
- [ ] Implement sound playback via stdout messages
- [ ] Add buddy presence notifications
- [ ] Handle Sugar quit and cleanup commands

### Activity Integration
- [ ] Connect pygame window to Sugar activity embedding
- [ ] Implement proper window focus handling
- [ ] Add Sugar activity lifecycle management
- [ ] Handle Sugar activity sharing features
- [ ] Implement Sugar journaling integration

### Multiplayer Support (Optional)
- [ ] Add network message handling for multiplayer
- [ ] Implement buddy list integration
- [ ] Add collaborative city editing
- [ ] Handle network synchronization
- [ ] Add multiplayer chat integration

## Asset Loading and Management

### Graphics Assets
- [ ] Load and validate tile graphics from `res/` directory
- [ ] Implement sprite loading for moving objects (cars, disasters)
- [ ] Add font loading for UI text rendering
- [ ] Create asset validation and error handling
- [ ] Implement asset hot-reloading for development

### Audio Assets
- [ ] Load sound effects from `res/sounds/` directory
- [ ] Implement pygame mixer integration
- [ ] Add sound playback queue system
- [ ] Handle audio format compatibility
- [ ] Add volume controls and muting

### Scenario and City Assets
- [ ] Load city files from `cities/` directory
- [ ] Implement scenario loading and validation
- [ ] Add city thumbnail generation
- [ ] Create city browser interface
- [ ] Handle corrupted city file recovery

## Performance Optimization

### Rendering Optimization
- [ ] Implement dirty rectangle rendering updates
- [ ] Add viewport culling for off-screen tiles
- [ ] Create sprite batching for moving objects
- [ ] Optimize overlay rendering performance
- [ ] Add level-of-detail rendering for distant areas

### Simulation Optimization
- [ ] Profile and optimize simulation bottleneck functions
- [ ] Implement multi-threading for simulation steps
- [ ] Add spatial indexing for zone queries
- [ ] Optimize power grid connectivity calculations
- [ ] Cache frequently accessed simulation data

### Memory Management
- [ ] Implement texture atlas for tile graphics
- [ ] Add memory usage monitoring and limits
- [ ] Create object pooling for sprites
- [ ] Optimize data structure memory usage
- [ ] Add garbage collection tuning

## Testing and Validation

### UI Integration Tests
- [ ] Create tests for map rendering accuracy
- [ ] Add input handling validation tests
- [ ] Implement UI panel interaction tests
- [ ] Add graphics asset loading tests
- [ ] Create performance benchmark tests

### End-to-End Testing
- [ ] Test complete game launch sequence
- [ ] Validate Sugar activity integration
- [ ] Test city save/load round-trip compatibility
- [ ] Add multiplayer functionality tests
- [ ] Create automated gameplay scenario tests

### Compatibility Testing
- [ ] Test with original city files from `cities/` directory
- [ ] Validate against C version behavior
- [ ] Test on different screen resolutions
- [ ] Add cross-platform compatibility testing
- [ ] Validate with different pygame versions

## Documentation and Deployment

### User Documentation
- [ ] Create gameplay tutorial and help system
- [ ] Add keyboard shortcuts reference
- [ ] Document configuration options
- [ ] Create troubleshooting guide
- [ ] Add developer documentation

### Packaging and Distribution
- [ ] Create standalone executable with PyInstaller
- [ ] Package for Sugar activity distribution
- [ ] Add Windows/macOS/Linux build scripts
- [ ] Implement auto-update system
- [ ] Create installer packages

### Final Validation
- [ ] Complete full test suite pass rate >95%
- [ ] Validate 60 FPS performance on target hardware
- [ ] Test Sugar activity full integration
- [ ] Confirm .cty file 100% compatibility
- [ ] Final user acceptance testing

## Launch & Test Readiness

### Runtime Bootstrapping
- [ ] Instantiate the global `types.sim` via `types.MakeNewSim()` and create the default editor/map/graph/date `SimView` chains in `engine.sim_init()` so `sim_update_*` has real views to walk instead of immediately returning when `sim` is `None`.
- [ ] Wire those `SimView` instances to pygame/window surfaces (tile caches, `view.surface`, `view.bigtiles`, etc.) by calling into `graphics_setup` during startup so editor/map rendering code can actually blit textures.
- [ ] Replace the placeholder implementations of `setUpMapProcs()`, `ClearMap()`, `InitFundingLevel()`, `SetFunds()`, and `SetGameLevelFunds()` with the real logic for registering `map_view` overlay callbacks, clearing map arrays, seeding terrain, and applying difficulty-based budgets so starting a new city produces a playable state.
- [ ] Fix the CLI entry point in `micropolis/main.py` to resolve the project root (instead of appending `micropolis/src` to `sys.path`) so running `uv run micropolis` or `python -m micropolis.main` from the repository actually imports `micropolis.engine` without manual tweaks.
- [ ] Implement `DoStopMicropolis()` teardown to stop the pygame loop, release mixer channels, and reset globals so the process exits cleanly when the user closes the window.

### Test Harness Stabilization
- [ ] Add a single `tests/conftest.py` (or equivalent helper) that inserts `<repo>/src` into `sys.path`, then remove the per-file `sys.path.insert(..., 'src')` hacks in tests such as `tests/test_tools.py`, `tests/test_file_io.py`, `tests/test_editor_view.py`, etc.
- [ ] Update `tests/test_map_view.py` to import `src.micropolis.map_view`, `types`, and `macros` from the actual package instead of `from . import ...`, which currently fails because `tests.map_view` does not exist.
- [ ] Rewrite `tests/test_constants.py` into real pytest test functions that import `micropolis.constants`; today it executes assertions at import time and calls `sys.exit`, so pytest never records any test results.
