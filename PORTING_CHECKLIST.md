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
- [ ] `w_resrc.c` → `resources.py` (Resource management)

## Phase 6: Platform Integration

### Sound and Media

- [ ] `w_sound.c` → `audio.py` (Sound effect management - adapt for pygame mixer)

### External Interfaces

- [ ] `w_x.c` → `platform.py` (Platform-specific code - adapt for pygame)
- [ ] `w_tk.c` → `tkinter_bridge.py` (TK integration - replace with pygame event loop)

### Stubs and Compatibility

- [ ] `w_stubs.c` → `stubs.py` (Stub implementations for unused features)

## Phase 7: Advanced Features (Optional)

### Camera and Viewport

- [ ] `w_cam.c` + `g_cam.c` + `cam.h` → `camera.py` (Camera controls - if implemented)

### Printing and Export

- [ ] `w_print.c` → `printing.py` (Print functionality - if needed)

### Interactivity

- [ ] `w_inter.c` → `interactions.py` (Interactive elements)

### Update Management

- [ ] `w_update.c` → `updates.py` (UI update management)

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
