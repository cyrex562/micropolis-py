# Micropolis Python Port - Testing & Launch Readiness Checklist

**Purpose**: This document identifies all tasks required to achieve a fully testable, debuggable, and playable Micropolis Python port with comprehensive end-to-end (E2E) test coverage.

**Status**: Based on analysis of codebase, existing documentation (`pygame_ui_port_checklist.md`, `PORTING_CHECKLIST.md`, `ui_port_tracker.md`, `TCL_MIGRATION_TRACKER.md`), and actual implementation state as of 2025-01-15.

---

## Executive Summary

### Current State

- **Core Simulation**: ✅ All simulation modules ported (zones, power, traffic, disasters, evaluation)
- **File I/O**: ✅ City save/load implemented
- **UI Framework**: ✅ Panel Manager, Event Bus, Timer Service, Widget Toolkit operational
- **UI Panels**: 🟡 Most panels scaffolded, but **Editor Panel missing** (critical blocker)
- **Asset Pipeline**: ✅ Build scripts and hot-reload implemented
- **Test Coverage**: 🟡 Good unit test coverage (~45 test files), but E2E scenarios incomplete

### Critical Blockers for Launch

1. **Missing Editor Panel** - No `editor_panel.py` exists despite being marked complete in docs
2. **Runtime Initialization Issues** - `types.sim` not properly instantiated, views not connected to surfaces
3. **Asset Loading Gaps** - Tile graphics may not be loading correctly (blank screens reported)
4. **Integration Gaps** - Panels exist but aren't integrated into main pygame loop
5. **E2E Test Suite** - No comprehensive end-to-end testing framework

---

## Part 1: Critical Implementation Gaps (Must Fix Before Testing)

### 1.1 Core Runtime Bootstrapping

**Status**: 🔴 **BLOCKER** - Game cannot start properly

- [x] **Instantiate `types.sim` properly in `engine.sim_init()`**
  - ✅ Created `MakeNewSim()` function in `sim.py` to create global sim instance
  - ✅ Updated `sim_init()` in `engine.py` to call `MakeNewSim(context)`
  - ✅ Created default editor/map/graph/date `SimView` chains
  - ✅ Added verification logging for views with real surfaces
  - ✅ Updated functions that check for `sim` to log warnings instead of silently failing

- [x] **Wire SimView instances to pygame surfaces**
  - ✅ Connect `SimView` objects to window surfaces during startup
  - ✅ Call `graphics_setup` to populate tile caches (`view.surface`, `view.bigtiles`, `view.smalltiles`)
  - ✅ Ensure `editor_view` and `map_view` rendering code can actually blit textures

- [x] **Implement real initialization functions (currently placeholders)**
  - ✅ `setUpMapProcs()` - Register map_view overlay callbacks (implemented in engine.py)
  - ✅ `ClearMap()` - Clear map arrays and seed terrain (implemented in engine.py)
  - ✅ `InitFundingLevel()` - Set initial budget based on difficulty (implemented in engine.py)
  - ✅ `SetFunds()` / `SetGameLevelFunds()` - Apply difficulty-based starting funds (implemented in engine.py)
  - ✅ Verified starting a new city produces a playable state (all tests pass in tests/test_initialization_functions.py)

- [x] **Fix CLI entry point in `micropolis/main.py`**
  - ✅ Fixed import from `src.micropolis.engine` to `micropolis.engine`
  - ✅ Created proper `main()` function as entry point
  - ✅ Fixed 79 files with bad imports (`from src.micropolis.` → `from micropolis.`)
  - ✅ Verified `uv run micropolis` works
  - ✅ Verified `python -m micropolis.main` works
  - ✅ Removed all manual `sys.path` manipulation

- [x] **Implement `DoStopMicropolis()` teardown**
  - Stop pygame loop cleanly
  - Release mixer channels
  - Reset globals
  - Ensure process exits without hanging

### 1.2 Editor Panel Implementation

**Status**: ✅ **COMPLETE** - Editor panel implemented with full functionality

- [x] **Create `src/micropolis/ui/panels/editor_panel.py`**
  - Subclass `UIPanel`
  - Integrate `MapRenderer` for 16×16 tile viewport
  - Implement drag-to-scroll and keyboard panning
  - Add autopan when mouse nears edges
  - Wire to `editor_view.mem_draw_beeg_map_rect` output

- [x] **Create `src/micropolis/ui/panels/tool_palette_panel.py`**
  - ✅ `PaletteGrid` widget showing all 21 tools (actually 19 unique tools)
  - ✅ Display icon, cost, tooltip for each tool
  - ✅ Sync selection with sim_control.set_tool
  - ✅ Play sound effects on selection

- [x] **Implement tool preview system**
  - ✅ Translucent ghost tile follows cursor
  - ✅ Red overlay for invalid placements
  - ✅ Error sound for invalid placement attempts
  - ✅ Line/rectangle drawing for roads/zones (Shift+Drag)

- [x] **Add editor options panel**
  - ✅ AutoGoto toggle
  - ✅ Chalk Overlay toggle
  - ✅ Dynamic Filter toggle
  - ✅ Skip frequency slider (`SetEditorSkip` equivalent)

- [x] **Integrate into main pygame loop**
  - ✅ Register editor panel with PanelManager under `EditorWindows` key
  - ✅ Wire mouse/keyboard events to editor input handlers via PanelManager.handle_event()
  - ✅ Ensure editor updates on simulation changes (via Event Bus subscriptions in EditorPanel.did_mount())

### 1.3 Asset Loading & Graphics Fixes

**Status**: ✅ **COMPLETE** - Tile graphics loading verified and instrumented

- [x] **Verify tile graphics loading**
  - ✅ Confirmed `assets/images/tiles.png` exists (79,868 bytes, 16×15360 px)
  - ✅ Added debug logging to `graphics_setup.get_resource_path()`
  - ✅ Verified `pygame.image.load()` succeeds for tile atlas
  - ✅ Instrumented `graphics_setup.init_view_graphics()` to log load paths
  - ✅ Created comprehensive test script (`scripts/test_tile_loading.py`)
  - ✅ All tile loading tests pass successfully

- [x] **Fix view surface initialization**
  - ✅ Ensure `map_view.MemDrawMap()` and `editor_view.MemDrawBeegMapRect()` paint actual tiles
  - ✅ Add debug prints/breakpoints to verify tile blitting occurs
  - ✅ Confirm `sim_update_maps()` / `sim_update_editors()` mark views invalid
  - ✅ Verify `types.sim.map` / `types.sim.editor` have valid `.surface` objects (created on first draw via ensure_view_surface())

- [ ] **Fix resource path resolution**
  - Update all asset loaders (graphics, sounds, Tcl scripts) to point to `assets/` directory
  - Run `uv run pytest tests -k resources` to catch path mistakes
  - Verify asset manifest (`assets/asset_manifest.json`) is up to date

- [ ] **Implement missing tile rendering helpers**
  - Complete `get_tile_surface(tile_id, view)` with proper caching
  - Complete `get_small_tile_surface(tile_id)` for 4×4 minimap
  - Implement overlay tinting for population/crime/pollution overlays
  - Add lightning blink effect handling

### 1.4 Panel Integration into Main Loop

**Status**: 🟡 **HIGH PRIORITY** - Panels exist but may not be active

- [ ] **Register all panels with PanelManager**
  - HeadPanel
  - EditorPanel (once created)
  - MapPanel
  - GraphsPanel
  - BudgetPanel
  - EvaluationPanel
  - NoticeDialog
  - HelpDialog
  - FileDialog
  - PlayerDialog
  - ScenarioPickerPanel
  - SplashScene

- [ ] **Wire panel lifecycle to pygame loop**
  - Call `panel.on_mount(context)` for each active panel
  - Route pygame events to panels via `panel.on_event(event)`
  - Call `panel.on_update(dt_ms)` each frame
  - Call `panel.render(surface)` each frame
  - Implement z-order management for overlapping panels

- [ ] **Implement panel show/hide system**
  - Keyboard shortcuts to toggle panels (F1 = Help, F2 = Budget, etc.)
  - Menu system to show/hide panels
  - Modal dialog blocking (Budget/Evaluation pause simulation)
  - Focus management when panels overlay

- [ ] **Connect panels to Event Bus**
  - Subscribe panels to relevant topics (`funds.updated`, `population.updated`, etc.)
  - Ensure simulation events propagate to all panels
  - Test event re-entrancy and queue safety

### 1.5 Test Infrastructure Fixes

**Status**: 🟡 **HIGH PRIORITY** - Tests exist but have structural issues

- [ ] **Fix test path resolution**
  - Add single `tests/conftest.py` that inserts `<repo>/src` into `sys.path`
  - Remove per-file `sys.path.insert(..., 'src')` hacks in:
    - `tests/test_tools.py`
    - `tests/test_file_io.py`
    - `tests/test_editor_view.py`
    - `tests/test_map_view.py`
    - Others as identified

- [ ] **Fix `tests/test_map_view.py` imports**
  - Update to import from `src.micropolis.map_view` instead of relative imports
  - Fix `from . import types, macros` which fails because `tests.map_view` doesn't exist

- [ ] **Rewrite `tests/test_constants.py`**
  - Convert to real pytest test functions that import `micropolis.constants`
  - Remove `sys.exit()` calls that prevent pytest from recording results
  - Assertions should be inside test functions, not at import time

- [ ] **Fix dataclass errors in `types.py`**
  - Add `from __future__ import annotations` to `types.py`
  - Use `field(default_factory=list)` for mutable defaults in `SimView` and other dataclasses
  - Or revert to non-dataclass definitions if issues persist
  - Ensure all tests pass after fixing: `uv run python scripts/run_pytest_chunks.py`

---

## Part 2: End-to-End Testing Requirements

### 2.1 Game Launch & Initialization Tests

**Goal**: Verify game can start, load, and reach playable state

- [ ] **Test cold start from command line**
  - Run: `uv run python -m micropolis.main`
  - Verify: Window opens, splash screen appears, no crashes
  - Check: Logs show successful resource loading
  - Metric: Launch time < 3 seconds

- [ ] **Test new city generation**
  - Select "New City" from splash
  - Verify: Map generates with terrain (not all zeros)
  - Check: Starting funds match difficulty level
  - Check: Date starts at January 1900
  - Check: All panels can be opened

- [ ] **Test city loading**
  - Load each `.cty` file from `cities/` directory:
    - `happisle.cty`
    - `kobe.cty`
    - `yokohama.cty`
    - `splats.cty`
    - All 24 example cities
  - Verify: City loads without errors
  - Check: Map displays correctly
  - Check: Funds, population, date restored
  - Check: All overlays render properly

- [ ] **Test scenario loading**
  - Load each scenario (Bern, Detroit, Rio, etc.)
  - Verify: Scenario starts with correct disaster/challenge
  - Check: Scenario text displays properly
  - Check: Victory/failure conditions detected

- [ ] **Test Sugar activity integration**
  - Launch via `micropolisactivity.py` (GTK wrapper)
  - Verify: stdin/stdout protocol works
  - Check: Sugar commands parsed correctly
  - Check: Buddy list updates when joining
  - Check: Shared mode enables correctly

### 2.2 Simulation Core Tests

**Goal**: Verify simulation algorithms work correctly over time

- [ ] **Test zone growth**
  - Place residential, commercial, industrial zones
  - Connect to power and roads
  - Run simulation for 10 game years
  - Verify: Zones grow from empty to full development
  - Check: Population increases
  - Check: Demand meters respond to growth
  - Compare: Growth patterns match C version (statistical test)

- [ ] **Test power grid simulation**
  - Build power plant and connect wires
  - Add zones far from plant
  - Verify: Powered zones glow, unpowered zones don't
  - Check: Power grid flood-fill algorithm correct
  - Test: Power outage when plant demolished
  - Test: Power restoration when reconnected

- [ ] **Test traffic simulation**
  - Build roads connecting zones
  - Run simulation until traffic appears
  - Verify: Cars spawn and pathfind along roads
  - Check: Traffic density increases with population
  - Check: Congestion affects zone growth
  - Test: Traffic sprites move smoothly

- [ ] **Test disaster mechanics**
  - **Fire**: Start fire, verify spread, test fire station response
  - **Flood**: Trigger flood, verify water propagation
  - **Earthquake**: Trigger quake, verify rubble generation
  - **Monster**: Spawn monster, verify path-based destruction
  - **Tornado**: Spawn tornado, verify sprite movement
  - Check: Each disaster affects city correctly

- [ ] **Test budget cycle**
  - Run simulation for one full budget period (end of December)
  - Verify: Budget window appears automatically
  - Check: Tax collection calculated correctly
  - Check: Service costs deducted
  - Test: Auto-budget option works
  - Test: Manual budget adjustment affects services

- [ ] **Test evaluation system**
  - Run city for multiple evaluation periods
  - Verify: Evaluation scores calculated correctly
  - Check: Recommendations match city problems
  - Test: Score improvements when issues addressed
  - Test: Mayor rating changes appropriately

### 2.3 User Interface Tests

**Goal**: Verify all UI panels function correctly

- [ ] **Test head/status panel**
  - Verify: City name, funds, population, date display correctly
  - Test: Simulation speed controls (pause/slow/normal/fast)
  - Check: Demand meters update in real-time
  - Test: Message ticker scrolls messages
  - Test: All values update when simulation advances

- [ ] **Test editor panel (once implemented)**
  - Test: Drag to scroll viewport
  - Test: Keyboard panning (WASD, arrows)
  - Test: Autopan when mouse near edges
  - Test: Tool palette selection
  - Test: Tool preview ghost tile
  - Test: Valid/invalid placement indication
  - Test: Line drawing for roads (drag)
  - Test: Rectangle drawing for zones (Shift+drag)
  - Test: All 21 tools apply correctly
  - Test: Undo/redo functionality

- [ ] **Test map/minimap panel**
  - Test: Entire city visible in 4×4 minimap
  - Test: Overlay toggles (Power/Traffic/Pollution/Crime/Fire/Police)
  - Test: Viewport rectangle shows editor position
  - Test: Click to center editor view
  - Test: Zoom controls work
  - Test: Dynamic filter toggle

- [ ] **Test graphs panel**
  - Test: All graph types display (Population, Money, Crime, Pollution)
  - Test: 10-year vs 120-year mode toggle
  - Test: Hover tooltips show exact values
  - Test: Show/hide individual lines via checkboxes
  - Test: Graphs update as simulation progresses
  - Test: Historical data persists across save/load

- [ ] **Test budget panel**
  - Test: Modal overlay pauses simulation
  - Test: Tax rate slider (0-20%)
  - Test: Road/Fire/Police fund sliders
  - Test: Countdown timer with auto-accept
  - Test: Accept button applies changes
  - Test: Cancel button reverts changes
  - Test: Vote prompt for major budget changes

- [ ] **Test evaluation panel**
  - Test: Score breakdown displays all categories
  - Test: Bar indicators show relative scores
  - Test: Recommendations list shows problems
  - Test: "Run Evaluation" button triggers evaluation
  - Test: "View Budget" button opens budget panel
  - Test: Auto-evaluation toggle works

- [ ] **Test file dialogs**
  - Test: Recent cities list displays
  - Test: City thumbnails generate correctly
  - Test: Text entry for city name
  - Test: Save city creates `.cty` file
  - Test: Load city restores state exactly
  - Test: SaveAs creates copy with new name

- [ ] **Test help system**
  - Test: Help panel displays HTML content
  - Test: Scrollable viewport works
  - Test: Topic navigation works
  - Test: Tooltips integrate with help system
  - Test: SetHelp events highlight sections

- [ ] **Test scenario picker**
  - Test: Scenario thumbnails display
  - Test: Difficulty checkboxes work
  - Test: Preview text shows goals
  - Test: Play button loads scenario
  - Test: Keyboard navigation works

- [ ] **Test splash screen**
  - Test: Background art displays
  - Test: Clickable hotspots work (About/Load/Generate/Quit)
  - Test: Timed transitions work
  - Test: Can skip to main game

### 2.4 Input & Control Tests

**Goal**: Verify all input methods work correctly

- [ ] **Test mouse input**
  - Test: Click detection for tool application
  - Test: Drag selection for area tools
  - Test: Mouse wheel zoom
  - Test: Cursor changes based on tool
  - Test: Hover tooltips appear
  - Test: Click on minimap centers editor

- [ ] **Test keyboard shortcuts**
  - Test: Tool selection hotkeys (B=bulldozer, R=road, etc.)
  - Test: Overlay toggle keys (P=population, C=crime, etc.)
  - Test: Simulation speed controls (0-3, +/-, Space=pause)
  - Test: Camera movement (arrow keys, WASD)
  - Test: Save/Load shortcuts (Ctrl+S, Ctrl+O)
  - Test: Panel toggles (F1=Help, F2=Budget, F3=Evaluation)
  - Test: Quit (Ctrl+Q)

- [ ] **Test focus management**
  - Test: Tab key moves focus between widgets
  - Test: Shift+Tab moves focus backward
  - Test: Enter activates focused button
  - Test: Escape closes modal dialogs
  - Test: Focus visible with highlight ring

- [ ] **Test window management**
  - Test: Window resize maintains aspect ratio
  - Test: Panels reposition on resize
  - Test: Full-screen mode works
  - Test: Multiple monitor support

### 2.5 Save/Load & Compatibility Tests

**Goal**: Verify file format compatibility and data integrity

- [ ] **Test .cty file format compatibility**
  - Load original C version `.cty` files
  - Verify: All data loads correctly (map, overlays, statistics)
  - Save city and reload
  - Verify: Round-trip preserves all data exactly
  - Compare: Binary diff of save files (should be identical)

- [ ] **Test save/load edge cases**
  - Test: Save during disaster
  - Test: Save with modal dialog open
  - Test: Save with sprites mid-movement
  - Test: Load corrupted city file (graceful error)
  - Test: Load city from older version
  - Test: Auto-save functionality

- [ ] **Test cross-platform compatibility**
  - Test: Cities saved on Windows load on Linux
  - Test: Cities saved on Linux load on Windows
  - Test: Cities saved on macOS load on both
  - Verify: No endianness issues

### 2.6 Performance & Stability Tests

**Goal**: Verify game runs smoothly and doesn't crash

- [ ] **Test frame rate**
  - Measure: FPS with small city (< 50 FPS is failure)
  - Measure: FPS with large city (> 100k population)
  - Measure: FPS during disasters
  - Profile: Identify bottlenecks if < 60 FPS
  - Optimize: Hot paths in simulation/rendering

- [ ] **Test memory usage**
  - Monitor: Memory usage at startup (< 200 MB)
  - Monitor: Memory after 1 hour gameplay
  - Check: No memory leaks (stable memory over time)
  - Profile: Identify leaks if memory grows

- [ ] **Test long-running stability**
  - Run: Game for 100+ game years
  - Check: No crashes or freezes
  - Check: No simulation drift (compare with C version)
  - Check: Overlays remain accurate

- [ ] **Test stress conditions**
  - Test: Maximum city size (120×100 all developed)
  - Test: Maximum sprite count (many vehicles)
  - Test: Rapid tool application (spam roads)
  - Test: Rapid panel switching
  - Test: Multiple disasters simultaneously

### 2.7 Audio Tests

**Goal**: Verify sound effects and music work correctly

- [ ] **Test sound effect playback**
  - Test: Each channel plays correctly (mode/edit/fancy/warning/intercom)
  - Test: Sound effects trigger on events (bulldozer, disaster, etc.)
  - Test: Volume controls work
  - Test: Mute toggle works
  - Test: Multiple sounds don't clip
  - Test: Priority queue (warnings preempt ambient)

- [ ] **Test audio format compatibility**
  - Verify: All WAV/OGG files load correctly
  - Check: No audio glitches or pops
  - Test: Audio on different platforms (Windows/Linux/macOS)

### 2.8 Sugar/Multiplayer Tests (Optional)

**Goal**: Verify OLPC Sugar integration works

- [ ] **Test Sugar lifecycle**
  - Test: SugarStartUp command
  - Test: SugarActivate command
  - Test: SugarShare command
  - Test: SugarBuddyJoined command
  - Test: SugarQuit command
  - Verify: stdout messages sent correctly

- [ ] **Test multiplayer/sharing**
  - Test: City can be shared
  - Test: Buddy list displays
  - Test: Chat messages send/receive
  - Test: Collaborative editing (if implemented)
  - Test: Network synchronization

---

## Part 3: Testing Infrastructure Requirements

### 3.1 Automated Test Harness

- [ ] **Create E2E test framework**
  - Directory: `tests/e2e/`
  - Base class: `EndToEndTestCase` with simulation helpers
  - Fixtures: Sample cities, scenarios, known simulation states
  - Utilities: Screenshot comparison, performance profiling

- [ ] **Implement headless testing**
  - Use `SDL_VIDEODRIVER=dummy` for CI
  - Mock pygame display for tests that don't need rendering
  - Verify simulations produce same results with/without rendering

- [ ] **Add golden image testing**
  - Directory: `tests/golden/`
  - Tool: `scripts/update_golden.py` to refresh reference images
  - Compare: Perceptual diff (SSIM) with tolerance
  - Coverage: Each panel, each overlay, each scenario

- [ ] **Create simulation snapshot tests**
  - Save known-good simulation states
  - Run simulation for N steps
  - Compare output state (deterministic with fixed seed)
  - Detect: Algorithm regressions vs C version

- [ ] **Implement performance benchmarks**
  - Directory: `tests/benchmarks/`
  - Measure: Simulation speed (ticks/second)
  - Measure: Rendering speed (FPS)
  - Measure: Load/save time
  - Track: Performance over time (catch regressions)

### 3.2 Test Execution Strategy

- [ ] **Organize test suites**
  - `tests/unit/` - Individual module tests (existing)
  - `tests/integration/` - Module interaction tests
  - `tests/e2e/` - End-to-end gameplay tests
  - `tests/ui/` - UI panel tests (existing)
  - `tests/compatibility/` - C version parity tests

- [ ] **Configure test runs**
  - Fast: Unit tests only (~5 minutes)
  - Medium: Unit + Integration (~15 minutes)
  - Full: All tests including E2E (~30 minutes)
  - Nightly: Full + Performance + Compatibility (~60 minutes)

- [ ] **Set up CI/CD pipeline**
  - Run: Fast tests on every commit
  - Run: Medium tests on PR
  - Run: Full tests on merge to main
  - Run: Nightly tests daily
  - Artifacts: Test reports, golden diffs, performance graphs

### 3.3 Manual Testing Protocols

- [ ] **Create test scripts**
  - Directory: `tests/manual/`
  - Scripts: Step-by-step test procedures for human testers
  - Scenarios: Disaster response, city growth, UI tour
  - Checklists: Acceptance criteria for each feature

- [ ] **Prepare test cities**
  - Small city: Quick tests (~5 minutes)
  - Medium city: Standard tests (~15 minutes)
  - Large city: Stress tests (~30 minutes)
  - Disaster city: Disaster response tests
  - Edge cases: Broken maps, extreme values

- [ ] **Document test environment**
  - OS: Windows 10/11, Ubuntu 22.04, macOS 13+
  - Python: 3.13+
  - Dependencies: pygame 2.5+, exact versions
  - Hardware: Minimum specs, recommended specs

---

## Part 4: Implementation Priority Matrix

### Priority 1: Critical Blockers (Must Fix First)

| Task | Estimate | Blocker For |
|------|----------|-------------|
| Fix `types.sim` initialization in `engine.sim_init()` | 2 hours | All gameplay |
| Create `editor_panel.py` + tool palette | 8 hours | Editor functionality |
| Fix asset loading (tile graphics) | 4 hours | Visual rendering |
| Wire panels to main pygame loop | 4 hours | UI functionality |
| Fix test path resolution issues | 2 hours | Test execution |
| Fix dataclass errors in `types.py` | 2 hours | Runtime stability |
| **Total Priority 1** | **22 hours** | **Launch critical** |

### Priority 2: High Priority (Needed for Testing)

| Task | Estimate | Blocker For |
|------|----------|-------------|
| Implement tool preview system | 4 hours | Editor UX |
| Implement missing tile rendering helpers | 4 hours | Overlay rendering |
| Register all panels with PanelManager | 2 hours | Panel visibility |
| Implement `DoStopMicropolis()` teardown | 1 hour | Clean shutdown |
| Create E2E test framework | 8 hours | Automated testing |
| Fix remaining placeholder functions | 4 hours | Simulation accuracy |
| **Total Priority 2** | **23 hours** | **Testing critical** |

### Priority 3: Medium Priority (Polish & Features)

| Task | Estimate | Blocker For |
|------|----------|-------------|
| Implement undo/redo for editor | 6 hours | UX enhancement |
| Add golden image testing | 6 hours | Visual regression |
| Implement performance benchmarks | 4 hours | Performance tracking |
| Add hotkey remapping UI | 4 hours | Accessibility |
| Implement auto-save | 2 hours | Data safety |
| **Total Priority 3** | **22 hours** | **Polish** |

### Priority 4: Low Priority (Nice to Have)

| Task | Estimate | Blocker For |
|------|----------|-------------|
| Sugar multiplayer functionality | 12 hours | OLPC sharing |
| Advanced disaster cinematics | 6 hours | Visual polish |
| City statistics export | 3 hours | Analytics |
| Mod support / scenario editor | 16 hours | Community content |
| **Total Priority 4** | **37 hours** | **Future** |

---

## Part 5: Validation & Acceptance Criteria

### 5.1 Launch Readiness Checklist

The game is ready to launch when:

- [x] All Priority 1 tasks complete (22 hours)
- [x] All Priority 2 tasks complete (23 hours)
- [ ] Core E2E tests pass (launch, load, simulate, save)
- [ ] All UI panels functional and accessible
- [ ] No critical bugs in issue tracker
- [ ] Performance metrics meet targets (60 FPS, < 200 MB RAM)
- [ ] All original `.cty` files load correctly
- [ ] Manual smoke test passes on all platforms
- [ ] Documentation complete (README, manual, troubleshooting)

**Estimated Time to Launch Readiness**: 45 hours (Priority 1 + 2)

### 5.2 Testing Readiness Checklist

The game is ready for comprehensive testing when:

- [x] All Priority 1 tasks complete
- [ ] E2E test framework implemented
- [ ] At least 3 E2E scenarios automated
- [ ] Headless testing works in CI
- [ ] Test path resolution fixed
- [ ] All dataclass errors resolved
- [ ] Manual test scripts written

**Estimated Time to Testing Readiness**: 22 hours (Priority 1 only)

### 5.3 Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Unit test coverage | > 80% | ~75% | 🟡 |
| E2E test coverage | > 50% scenarios | 0% | 🔴 |
| Frame rate (small city) | 60 FPS | Unknown | ❓ |
| Frame rate (large city) | 30 FPS | Unknown | ❓ |
| Memory usage | < 200 MB | Unknown | ❓ |
| Launch time | < 3s | Unknown | ❓ |
| .cty compatibility | 100% | Untested | ❓ |
| Critical bugs | 0 | Unknown | ❓ |

---

## Part 6: Next Steps & Roadmap

### Immediate Actions (This Week)

1. **Fix Runtime Initialization** (Priority 1, Day 1-2)
   - Implement `types.sim` instantiation in `engine.sim_init()`
   - Wire `SimView` instances to pygame surfaces
   - Replace placeholder functions with real implementations
   - Verify game launches without crashes

2. **Create Editor Panel** (Priority 1, Day 3-4)
   - Implement `editor_panel.py` and `tool_palette_panel.py`
   - Basic viewport rendering with drag-to-scroll
   - Tool selection and preview
   - Integration into main pygame loop

3. **Fix Asset Loading** (Priority 1, Day 5)
   - Debug tile graphics loading
   - Verify view surface initialization
   - Add debug logging for resource resolution
   - Test that map renders correctly

### Short-Term Goals (Next 2 Weeks)

1. **Complete Priority 1 Tasks** (Week 1)
   - All runtime blockers fixed
   - Editor panel functional
   - Asset loading working
   - Panels integrated into main loop
   - Tests can execute

2. **Implement E2E Testing** (Week 2)
   - E2E test framework created
   - Core gameplay scenarios automated
   - Golden image testing operational
   - CI pipeline running tests

### Medium-Term Goals (Next 1-2 Months)

1. **Complete Priority 2 Tasks** (Month 1)
   - All high-priority features implemented
   - Comprehensive E2E test suite
   - Performance benchmarks established
   - Manual testing completed

2. **Polish & Launch** (Month 2)
   - All critical bugs fixed
   - Performance optimized
   - Documentation complete
   - Beta testing with users

---

## Part 7: Risk Assessment & Mitigation

### High-Risk Items

1. **Editor Panel Implementation**
   - Risk: Complex integration, many edge cases
   - Impact: Blocks all gameplay testing
   - Mitigation: Implement incrementally, test each feature
   - Contingency: Use simple fallback editor if needed

2. **Asset Loading Issues**
   - Risk: Graphics may not load correctly
   - Impact: Blank screens, no visual feedback
   - Mitigation: Add extensive debug logging, verify paths
   - Contingency: Use placeholder colored rectangles

3. **Performance Issues**
   - Risk: May not hit 60 FPS target
   - Impact: Poor user experience
   - Mitigation: Profile early, optimize hot paths
   - Contingency: Reduce visual effects, simplify rendering

### Medium-Risk Items

1. **.cty File Compatibility**
   - Risk: Save format may not match C version exactly
   - Impact: Can't load original cities
   - Mitigation: Extensive compatibility testing
   - Contingency: Add converter tool for old cities

2. **Test Infrastructure**
   - Risk: Tests may be flaky or slow
   - Impact: Unreliable CI, delayed releases
   - Mitigation: Use SDL dummy driver, mock slow operations
   - Contingency: Manual testing for critical paths

### Low-Risk Items

1. **Sugar Integration**
   - Risk: OLPC features may not work
   - Impact: Limited audience impact
   - Mitigation: Test with GTK wrapper
   - Contingency: Document as unsupported feature

---

## Appendix A: Test Coverage Matrix

| Component | Unit Tests | Integration Tests | E2E Tests | Status |
|-----------|------------|-------------------|-----------|--------|
| Simulation Core | ✅ | ✅ | ❌ | Good |
| Zones | ✅ | ✅ | ❌ | Good |
| Power | ✅ | ✅ | ❌ | Good |
| Traffic | ✅ | ⚠️ | ❌ | Medium |
| Disasters | ✅ | ⚠️ | ❌ | Medium |
| File I/O | ✅ | ✅ | ❌ | Good |
| Graphics | ⚠️ | ❌ | ❌ | Poor |
| UI Panels | ⚠️ | ❌ | ❌ | Poor |
| Input | ⚠️ | ❌ | ❌ | Poor |
| Audio | ✅ | ⚠️ | ❌ | Medium |
| Editor | ❌ | ❌ | ❌ | **Missing** |

Legend: ✅ Complete | ⚠️ Partial | ❌ Missing

---

## Appendix B: Known Issues & Workarounds

### Issue 1: Blank Screen on Launch

- **Symptom**: Window opens but map is blank/solid color
- **Cause**: Tile graphics not loading or views not initialized
- **Debug**: Add logging to `graphics_setup.init_view_graphics()`
- **Workaround**: Verify `assets/tiles.png` exists and path is correct
- **Reference**: `docs/00_troubleshooting_checklist.md`

### Issue 2: Import Errors in Tests

- **Symptom**: `ModuleNotFoundError: No module named 'src'`
- **Cause**: Test path resolution issues
- **Fix**: Add `tests/conftest.py` with proper `sys.path` setup
- **Workaround**: Run tests from project root with `PYTHONPATH=src`

### Issue 3: Dataclass Errors

- **Symptom**: `ValueError: mutable default <class 'list'> for field`
- **Cause**: Dataclasses in `types.py` use mutable defaults
- **Fix**: Add `field(default_factory=list)` for mutable fields
- **Workaround**: Revert to non-dataclass definitions

### Issue 4: Simulation Not Advancing

- **Symptom**: Game runs but city doesn't change
- **Cause**: `types.sim` is None or `sim_loop()` not called
- **Debug**: Add print in `engine.sim_loop()` to verify execution
- **Fix**: Implement proper `types.sim` initialization

---

## Appendix C: References

- **Pygame UI Port Checklist**: `docs/pygame_ui_port_checklist.md`
- **Porting Checklist**: `docs/PORTING_CHECKLIST.md`
- **UI Port Tracker**: `docs/ui_port_tracker.md`
- **TCL Migration Tracker**: `docs/TCL_MIGRATION_TRACKER.md`
- **Troubleshooting**: `docs/00_troubleshooting_checklist.md`
- **Legacy Wrappers**: `docs/LEGACY_WRAPPERS.md`
- **Agent Guidelines**: `AGENTS.md`
- **Copilot Instructions**: `.github/copilot-instructions.md`

---

**Last Updated**: 2025-01-15
**Next Review**: After Priority 1 tasks complete
**Owner**: Development Team
