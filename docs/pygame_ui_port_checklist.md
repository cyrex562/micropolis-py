# Pygame UI Port Checklist

Use this checklist to track the migration of the legacy Tcl/Tk interface in `assets/` to the new pygame-based UI stack.

## 1. Foundation & Inventory

- [x] Catalogue every Tcl/Tk window script (`micropolis.tcl`, `w*.tcl`) with its responsibilities, shared globals, and simulation hooks.
- [x] Map all required assets (XPM images, fonts, sounds) to new pygame-friendly formats (PNG, OGG/WAV) and document locations.
- [x] Define data contracts between the UI layer and `AppContext`/`sim_control` (city name, funds, toggles, overlay states, timers).

### 1.1 Tcl/Tk Window Inventory

| Script | UI scope | Shared globals/state | Simulation hooks / notes |
| --- | --- | --- | --- |
| `micropolis.tcl` | Root launcher that builds every panel, manages Sugar state, timers, and tool bindings. | Sets `CityName`, `GameLevel`, `Time`, `AutoGoto`, `AutoBudget`, `Disasters`, `AutoBulldoze`, `Sound`, `DoAnimation`, demand meters, panel lists (`HeadWindows`, etc.). | Direct `sim` commands for animation toggles, sprite setup, Sugar IPC, and dispatch helpers such as `DoPlay`, `DoLevel`, `DoAbout`. |
| `whead.tcl` | Head/status panel with funds, population, date, messages, and speed controls. | Uses `HeadPanelWidth/Height`, `HeadWindows`, ticker state. | Calls `sim SetGameLevel`, `SimSetSpeed`, messaging callbacks, and triggers map/editor updates. |
| `weditor.tcl` | Main editor canvas plus tool/options palette. | Maintains per-window flags: `Skip.$win`, `AutoGoto.$win`, `Overlay.$win`, `DynamicFilter.$win`, `EditorWindows`. | Invokes `SetEditorSkip`, `SetEditorAutoGoto`, `SetEditorOverlay`, `SimSetTool` equivalents, and `sim` query tools. |
| `wmap.tcl` | Overview/minimap display with overlay controls. | `MapWindows`, `MapPanelWidth/Height`, overlay toggle variables. | Calls `SetMapOverlay`, `MapGoto`, and `sim DoUpdateMap`. |
| `wgraph.tcl` | Graph panel for population, money, pollution, crime graphs with year range selectors. | `GraphWindows`, `GraphPallets`, `GraphYearPallets`. | Hooks `SetGraphType`, `SetGraphYears`, `sim UpdateGraphs`. |
| `wbudget.tcl` | Budget dialog with tax sliders and service funding scales. | `BudgetWindows`, `BudgetRoadFund`, `BudgetFireFund`, `BudgetPoliceFund`, `BudgetTaxRate`, `BudgetTimer`. | Calls `BudgetSetRoadFund/FireFund/PoliceFund`, `BudgetSetTaxRate`, `BudgetAccept/Cancel`, and pauses simulation via `BudgetTimeout`. |
| `weval.tcl` | Evaluation window listing scores, recommendations, and vote dialogs. | `EvaluationWindows`, evaluation list variables. | Calls `UpdateEvaluation`, `DoBudget`, `VoteProblems`, etc. |
| `wnotice.tcl` | Message/notice window stack with scrolling text. | `NoticeWindows`, message queue state. | Consumes `SendMes` output, exposes clear/dismiss events to `sim`. |
| `wplayer.tcl` | Player/chat window for Sugar networking. | `PlayerWindows`, chat connection info (`ChatServer`, `ChannelName`). | Hooks Sugar messaging commands and placeholder `DoPlayer` actions. |
| `whelp.tcl` | Contextual help browser. | `HelpWindows`, `HelpLoaded`, topic pointers. | Responds to `SetHelp` calls from other panels. |
| `wfile.tcl` | File/load/save dialog interface. | `FileWindows`, `CityDir`, `MapHistory`. | Calls file I/O commands (`LoadCity`, `SaveCity`, `DoSaveCityAs`). |
| `wask.tcl` | Confirmation prompt (Yes/No/Ask). | `AskWindows`, vote-tracking arrays. | Invoked by budget votes and scenario prompts. |
| `wfrob.tcl` | Developer “frob” controls / diagnostics. | `FrobWindows`, debugging toggles. | Directly manipulates `sim` debugging hooks and disaster triggers. |
| `wscen.tcl` | Scenario picker and difficulty selection (modern). | `ScenarioWindows`, `ScenarioPanelWidth/Height`, scenario selection state. | Calls `DoPickScenario`, `DoPlay`, `DoGenerate`, `DoLevel`. |
| `wscen_old.tcl` / `wscen_older.tcl` | Legacy scenario selection UIs retained for reference. | Old layout constants. | Same hooks as `wscen.tcl`; used for historical parity. |
| `wsplash.tcl` | Splash screen and intro slideshow. | `SplashWindows`, `SplashScreenDelay`. | Uses `after` timers to advance screens and start `DoPlay`. |

Supporting scripts (`button.tcl`, `menu.tcl`, `listbox.tcl`, `entry.tcl`, `text.tcl`, `help.tcl`, `sound.tcl`, etc.) define custom widgets and behaviors consumed by the `w*.tcl` windows and will need pygame equivalents (button skins, menu logic, scrolling text, sound playback helpers).

### 1.2 Asset Mapping

| Asset type | Legacy location | Notes / pygame target |
| --- | --- | --- |
| Tile & UI art | `assets/images/` (XPM files referenced in scenario buttons, tool palettes) | Convert each XPM to PNG spritesheets; maintain naming so palette definitions survive. Bundle into a pygame texture atlas with metadata for hover/checked states. |
| Fonts | `assets/dejavu-lgc/` (X11 font descriptors used via Tk) | Replace with TTF files (e.g., DejaVu Sans) loaded through `pygame.font.Font`. Document mapping from Tk aliases (`Big`, `Medium`, etc.) to point sizes. |
| Sound effects | `assets/sounds/` plus `sound.tcl` definitions and `.snro/.stri` tables | Transcode/verify WAV/OGG compatibility, recreate channel routing (mode/edit/fancy/warning/intercom) using `pygame.mixer.Channel`. |
| Scripts & helpers | `assets/button.tcl`, `menu.tcl`, `listbox.tcl`, `help.tcl`, `wish.tcl` | Serve as behavioral specs for pygame widget implementations (button states, menu traversal, help loader). |
| Scenario splash art | Referenced via `ScenarioButtons` background images in `micropolis.tcl` | Export to PNG and capture coordinates for clickable hotspots. |

### 1.3 UI ↔ Simulation Data Contract

| Data group | Source globals | Purpose in pygame UI |
| --- | --- | --- |
| City metadata | `CityName`, `GameLevel`, `Time`, `Scenario`, `Population`, `Funds` | Display in head panel, scenario picker, save dialogs; provide setters/getters through `sim_control`. |
| Budget state | `BudgetRoadFund`, `BudgetFireFund`, `BudgetPoliceFund`, `BudgetTaxRate`, `BudgetTimer`, `BudgetTimeout` | Drive slider defaults, countdown timers, and accept/cancel flows; requires synchronous updates to `AppContext.finance`. |
| Demand & overlays | `DemandRes`, `DemandCom`, `DemandInd`, overlay selection indexes, `DynamicFilter` flags | Feed map overlays, graphs, and editor filter toggles; mirrored in overlays module for rendering. |
| Simulation toggles | `AutoGoto`, `AutoBudget`, `AutoBulldoze`, `Disasters`, `Sound`, `DoAnimation`, `DoMessages`, `DoNotices`, `ShapePies`, `Chatting` | Each toggle needs a pygame control plus downstream hooks (e.g., `engine.set_auto_budget`, audio mute). |
| Panel collections | `HeadWindows`, `EditorWindows`, `MapWindows`, etc. | Determines which pygame panels should exist simultaneously and how updates propagate; replace with panel manager registries. |
| Sugar/chat state | `SugarURI`, `SugarNickName`, `SugarShared`, `SugarBuddies`, `ChatServer`, `ChannelName` | Ensures pygame UI can surface sharing/buddy info and pass events to the GTK wrapper. |
| Input helpers | Tool palettes (`EditorPallets`, `EditorPalletImages`, `EditorPalletSounds`), graph palettes, vote lists (`VoteNames`, `VotesFor...`) | Provide deterministic ordering, asset bindings, and event wiring for pygame widgets. |

These inventories will inform the pygame panel scaffolding so each window’s state, assets, and hooks have clear targets in the new architecture.

## 2. UI Framework Scaffolding

- [x] Design the pygame UI architecture (panel manager, widget toolkit, event bus, timer service) and document APIs.
- [x] Implement a `UIPanel` base class with layouting, focus management, show/hide, and z-order control.
- [x] Build core widgets: buttons, toggle buttons, checkboxes, sliders, scroll containers, text labels, modal dialogs, and tooltip/help overlays.

### 2.1 Architecture Blueprint

| Component | Responsibilities | Implementation notes |
| --- | --- | --- |
| Panel Manager | Own the root window surface, keep ordered list of active panels (head, editor, graph, etc.), dispatch lifecycle hooks (`on_mount`, `on_unmount`, `on_resize`). | Maintain registry keyed by legacy window types (`HeadWindows`, etc.) for compatibility; handles z-order stacking, modal overlays, and panel creation/destruction requests from `sim_control`. |
| Widget Toolkit | Provide retained-mode widget tree (panels composed of widgets) with event propagation, layouting, and theming. | Compose widgets hierarchically using flex/grid layouts; support per-widget invalidation + dirty rectangles to minimize redraw cost. |
| Event Bus | Normalize pygame events into high-level UI events (hover, click, drag, key command) and broadcast simulation events (`UpdateFunds`, `DisasterTriggered`). | Use publish/subscribe with priorities; bus also mediates between Sugar/stdin messages and UI updates. |
| Timer Service | Replace Tcl `after` callbacks with scheduler tied to pygame clock; supports one-shot, repeating, and coalesced timers. | Provide API `add_timer(delay_ms, callback, repeat=False)` and automatically pauses/resumes with simulation state. |
| Input Binding Layer | Map keyboard shortcuts and controller actions to commands (tool selection, overlays, pause). | Maintains conflict-free keymap file; exposes contextual help for each binding. |
| Asset/Theme Service | Centralized loader for images, fonts, sounds, cursor sprites, with caching and reference counting. | Converts XPM → PNG at build time; exposes `get_sprite(name, state)` for widget skins. |

This blueprint ensures pygame has a direct analogue for Tk’s window manager, menu bindings, and `after` timers while remaining testable and modular.

### 2.2 `UIPanel` Base Specification

- Lifecycle hooks: `on_mount(context)`, `on_unmount()`, `on_update(dt_ms)`, `on_event(event)`, `render(surface)`.
- Layout contract: panels declare desired pixel size or percentage anchors; manager provides actual rect on resize.
- Focus management: track focusable child widget order, provide `focus_next/prev`, propagate keyboard events only to focused chain.
- Visibility controls: `show()`, `hide()`, `toggle()` update manager z-order and skip rendering/events when hidden.
- Dirty region tracking: expose `invalidate(rect=None)` so manager only redraws necessary areas.
- Legacy bridge: each panel exposes `legacy_name` (e.g., `"head"`, `"editor"`) and methods invoked by legacy shims (`update_budget`, `set_overlay`).

### 2.3 Core Widget Specifications

| Widget | Requirements |
| --- | --- |
| Button / ToggleButton | States: normal, hover, pressed, disabled, checked. Supports sprite skinning, keyboard activation (`space/enter`), tooltips, and sound hooks (e.g., palette clicks). |
| Checkbox | Derived from toggle button with label text, focus ring, and optional tri-state (used by overlay toggles). |
| Slider | Horizontal + vertical modes, integer percentage output, snap increments for tax/fund sliders, optional markers for target funding. |
| Scroll Container | Masked viewport with scrollbars or wheel support; used for notice/help text and player chat. |
| Text Label | Rich text support with inline color (for message severity), auto-truncation, and `marquee` mode for ticker. |
| Modal Dialog | Handles blocking overlays (budget pause, vote prompts) with focus trap, dimmed background, confirm/cancel buttons, keyboard shortcuts. |
| Tooltip/Help Overlay | Delay-based display showing `SetHelp` text near cursor; integrates with help panel for deep links. |
| Palette Grid | Specialized widget for editor/map palettes with sprite icons, multi-column layout, selection highlight, and drag ghost preview. |

Defining these primitives now unblocks later panel work by ensuring every Tcl widget (menus, scalers, dialog buttons) has a pygame equivalent and a clear spec for developers to implement.

## 3. Rendering & Assets

- [x] Finalize tile atlas extraction helpers (`get_tile_surface`, `get_small_tile_surface`) plus caching and dirty-rect updates.
- [x] Implement `MapRenderer`/`MiniMapRenderer` surfaces with overlay tinting and lightning-blink handling.
- [x] Create an asset loader that converts legacy XPM palettes to pygame surfaces and manages fonts/audio resources.

### 3.1 Tile Helper Design

- `get_tile_surface(tile_id, view)` pulls from a lazily loaded 16×16 atlas (`big_tile_image`) managed by `graphics_setup.get_view_tiles`. Caching strategy:
  - Atlas is stored on the `SimView` (`view.tiles_surface`); per-tile blits use a `pygame.Surface.subsurface` cache keyed by tile index.
  - Maintain a global LRU for derived variants (highlight, ghost placement) to avoid regenerating tinted versions.
- `get_small_tile_surface(tile_id)` references the 4×4 monochrome atlas generated from `SIM_GSMTILE` hexa data. Provide a helper to tint overlays by applying per-overlay color ramps before blitting to the minimap surface.
- Dirty rectangles: editor/map views already track tile caches (`view.tiles`). When `_blit_tile` detects a change, enqueue the affected pixel rect into a `DirtyBuffer` so pygame’s `display.update` can batch updates instead of full-screen flips.
- Lightning blink + overlay gating occurs before lookup so cached tiles remain canonical; special tiles such as `context.LIGHTNINGBOLT` have dedicated atlas entries.

### 3.2 MapRenderer / MiniMapRenderer

- `MapRenderer` owns a surface sized to the viewport (e.g., visible 120×100 tiles * 16px). Responsibilities:
  - Translate world coords to viewport coords with smooth scrolling offsets and optional easing for autopan.
  - Render base tiles via tile helpers, then overlay layers as blended surfaces (power, pollution, crime, traffic). Each overlay is a cached `pygame.Surface` tinted via lookup tables.
  - Handle blinking/unpowered visuals by toggling a bool from `AppContext.flag_blink` and invalidating affected tiles only.
  - Expose methods `set_viewport(x, y)`, `set_overlay(name)`, `draw(surface, dest_rect)` for panel integration.
- `MiniMapRenderer` uses 4×4 tiles; entire map fits on a small surface. Requirements:
  - Maintain separate overlay toggles for overall view vs. dynamic filter.
  - Provide `draw_selection_rect` around the current editor viewport.
  - offer `sample_density_overlay(name)` to precompute overlay textures at 4×4 resolution for quick toggling.

### 3.3 Asset Loader Pipeline

- Preprocess assets at build or first run:
  - Convert all XPM assets to PNG using a script (retain metadata for hover/checked states). Store in `assets/images/cache/`.
  - Validate `.snro`/`.stri` sound tables and emit a JSON manifest consumed by the loader to map logical names to WAV/OGG files.
- Runtime API (`AssetManager`):
  - `load_image(name, colorkey=None, scale=1)` returns cached pygame surfaces; supports slicing spritesheets via metadata describing tile size and coordinates.
  - `load_font(alias, size)` wraps `pygame.font.Font`, mapping Tk aliases (Big/Medium/Small) to TTF files.
  - `load_sound(name)` returns `pygame.mixer.Sound`; manager handles channel assignment and volume defaults per legacy `AudioChannels` definitions.
  - Provide hot-reload hooks for development (watch file timestamps, reload surfaces).
- Integrate with panel/theme system so widgets request skins via logical names (e.g., `theme.button.normal`) rather than raw filenames.

## 4. Panel Implementations

- [x] Head/status panel: date, funds, population, difficulty, sim speed controls, message ticker.
- [x] Editor view + tool palette: integrate `editor_view.py`, add tool preview, autopan, chalk overlay, dynamic filter toggle.
- [x] Map and mini-map panels: overlay selector buttons, zoom, viewport scrolling.
- [x] Graphs panel: history plotting with 10-year/120-year modes and tooltip readouts.
- [x] Budget panel: tax sliders, funding sliders, timer countdown, vote dialog hook.
- [x] Evaluation panel: score breakdown, recommendations list, auto-evaluation toggle.
- [x] Notice/help/player/file dialogs: scrollable text panes, confirmation modals, file chooser replacement.
- [x] Scenario & splash scenes: background artwork, clickable hotspots, difficulty checkboxes, scenario thumbnails.

### 4.1 Head / Status Panel

- Layout: fixed-width top panel containing (left→right) city name editable label, population/funds counters, difficulty indicator, simulation speed radio buttons, demand meters, and ticker strip.
- Widgets: use `TextLabel` for counters (with green/red flash on change), `Slider`/`ToggleButton` cluster for speed (Paused/Slow/Normal/Fast), and `ScrollContainer` + marquee for messages sourced from `messages.py` (`SendMes`).
- Hooks: subscribe to `UpdateFunds`, `UpdatePopulation`, and date advance events; call `engine.set_sim_speed` when speed controls change; show `SimSetGameLevel` results.
- Accessibility: display Sugar buddy badge if shared; include button to open evaluation/budget panels.

### 4.2 Editor View & Tool Palette

- Main canvas: embed `editor_view.mem_draw_beeg_map_rect` output as a `MapRenderer` viewport with 16×16 tiles, supporting drag-to-scroll, keyboard panning, and autopan when mouse nears edges.
- Tool palette: `PaletteGrid` arranged by `EditorPallets` order, each entry showing icon, cost, tooltip, and sound effect. Selection state syncs with `sim_control.set_tool`.
- Options panel: toggles for AutoGoto, Chalk Overlay, Dynamic Filter, plus skip frequency slider mirroring `SetEditorSkip`.
- Tool preview: translucent ghost tile follows cursor; invalid placements show red overlay and optionally play error sound.

### 4.3 Map & Mini-map Panels

- Overview panel: use `MiniMapRenderer` to draw entire city; overlay buttons (Power, Traffic, Pollution, etc.) implemented as checkbox group with exclusive selection, matching `MapTitles` ordering.
- Zoom controls: discrete zoom levels (overall, city, district) by scaling renderer output; viewport rectangle shows current editor view and supports click-to-pan.
- Provide quick-jump buttons (Police/Fire coverage) and dynamic filter toggle, updating `AppContext.overlay_mode`.

### 4.4 Graphs Panel

- Graph area: `ScrollContainer` with multiple stacked graphs (Population, Residential/Commercial/Industrial demand, Money, Crime, Pollution). Each graph uses a lightweight plotting widget that reads history buffers from `graphs.py`.
- Controls: year range toggle (10 vs 120 years), legend with hover tooltips reporting exact values at cursor, checkboxes to show/hide individual lines.
- Integration: subscribe to `UpdateGraphs` events, redraw only segments with new data; allow exporting graphs to PNG via `pygame.image.save`.

### 4.5 Budget Panel

- Modal overlay triggered by annual budget; panel uses `ModalDialog` base to pause simulation and dim background.
- Sliders for Road/Fire/Police funds with percentage labels (`100% of $X = $Y`), tax slider for R/C/I combined rate; each slider updates preview labels in real time.
- Countdown timer: `TimerService` event shows remaining seconds before auto-accept; `Accept`/`Cancel` buttons map to `BudgetAccept`/`BudgetCancel`.
- Vote prompt: integrate `wask` functionality to collect yes/no responses and show results once timer expires.

### 4.6 Evaluation Panel

- Layout: multi-column list showing categories (Population, Pollution, Crime, Traffic, Growth, Score). Each row includes bar indicator and textual recommendation pulled from `evaluation.py`.
- Buttons: “Run Evaluation” triggers `UpdateEvaluation`; “View Budget” opens budget panel; toggles for Auto-Evaluation and notifications.
- House issues list: scrollable list showing problems and suggested fixes (mirrors `DoProblems` output).

### 4.7 Notice, Help, Player, File Dialogs

- Notice window: stack of dismissible cards with severity color, auto-scroll for long text, `Clear All` and `Mute` buttons. Supports filters (finance, disasters, advisor messages).
- Help browser: `ScrollContainer` rendering HTML-lite help content; integrates with tooltip `SetHelp` by highlighting relevant section.
- Player/chat window: input field, chat log, buddy list; connects to Sugar networking via existing IPC channels. Provide status indicators for connection states.
- File dialogs: pygame-native file picker with recent cities list, thumbnails (generated from city snapshots), and quick scenario load buttons. Provide text entry for city name and location.

### 4.8 Scenario & Splash Scenes

- Splash: full-screen scene with background art, clickable hotspots for About, Load, Generate, Quit; timed transitions controlled via `TimerService`.
- Scenario picker: grid of scenario thumbnails from converted PNG assets; difficulty checkboxes mimic Tk behavior; play button triggers `engine.load_scenario`.
- Provide keyboard/controller navigation for accessibility; include preview text describing scenario goals.

## 5. Input & Event Integration

- [x] Map Tk keyboard shortcuts to pygame key bindings (tools, overlays, simulation speed, save/load).
- [x] Implement mouse hit-testing for tool palettes, map editing, drag selection, and overlay toggles.
- [x] Replace Tcl `after` timers with pygame clock or async scheduler for budget timers, splash delays, blinking overlays.
- [x] Ensure multiple panels can subscribe to shared events (e.g., `UpdateFunds`, disaster alerts) without conflicting.

### 5.1 Keyboard Mapping Plan

- Maintain a centralized keymap JSON (`config/keybindings.json`) listing actions, default pygame keys, and categories (tools, overlays, system).
- Replicate legacy bindings:
  - Tools: `B` Bulldozer, `R` Road, `T` Rail, `W` Wire, `Z` Residential, `X` Commercial, `C` Industrial, `F` Fire, `P` Police, `A` Airport, `S` Seaport, `N` Nuclear, `L` Coal, `O` Park, `H` Stadium, `Q` Query.
  - Simulation speed: `Space` pause/resume, `1/2/3/4` for turtle/cheetah speeds, `.` step frame.
  - Overlays: `Shift+1..9` for population, pollution, crime, traffic, power, land value, rate of growth, fire/police coverage, dynamic filter.
  - System: `Ctrl+S` save city, `Ctrl+O` open, `Ctrl+N` new, `Ctrl+Q` quit, `F1` help, `F2` budget, `F3` evaluation.
- Provide remapping UI in settings panel; persist overrides in config file while keeping defaults for parity tests.
- Hook keymap into event bus so actions dispatch to relevant panels without hardcoded keycodes.

### 5.2 Mouse Interaction Model

- Global cursor manager updates sprite based on selected tool (bulldozer, road, zone) and context (valid/invalid placement, autopan zone near edges).
- Editor interactions:
  - Left click applies current tool; drag keeps painting (roads, wires) with snapping to orthogonal lines; `Shift+Drag` draws rectangles for zones.
  - Right click pans map or cancels selection; mouse wheel zooms (configurable).
  - Hit-testing uses quadtree or simple grid acceleration to map screen coordinates to world tiles, respecting viewport offsets.
  - Chalk overlay toggled by middle-click to drop annotations; dragging with chalk leaves lines stored separately.
- Tool palette: buttons react on mouse up, support hover tooltips, and allow drag-and-drop to reorder favorites (optional enhancement).
- Map/minimap: click to center editor view; drag selection rectangle to define autopan target; overlays toggled via checkbox widgets.
- Graphs: hover shows data cursor; drag along graph timeline to scrub historical values.

### 5.3 Timer & Event System

- TimerService (from Step 2) schedules repeating tasks: budget countdown (1 Hz), splash transitions (5 s), blinking overlays (toggle every 500 ms), autosave (user-configurable interval).
- Use pygame clock `tick()` to drive scheduler; for accuracy, accumulate delta time and fire callbacks once thresholds pass.
- Provide pause/resume API tied to simulation state; timers marked `simulation_bound=True` stop when game paused, while UI timers (tooltip delays) continue.
- Event Bus supports namespaced topics; panels subscribe/unsubscribe dynamically. Example topics: `funds.updated`, `population.updated`, `overlay.changed`, `disaster.triggered`, `message.posted`.
- Ensure event re-entrancy safety by queueing dispatches; support once-only subscribers (e.g., splash screen waiting for first `engine.initialized`).
- Integrate Sugar/stdin events by bridging wrapper messages into the bus so UI stays reactive without tight coupling.

## 6. Sugar & Legacy Compatibility

- [x] Preserve stdin/stdout protocol used by `micropolisactivity.py`, including Sugar lifecycle commands and buddy updates.
- [x] Mirror legacy globals via `sim_control` getters/setters so tests patching `micropolis.sim_control.types` still observe changes.
- [x] Integrate audio playback through `audio.py`/`pygame.mixer`, maintaining channel semantics (mode/edit/fancy/warning/intercom).

### 6.1 Sugar Protocol Bridge

- The existing Sugar GTK wrapper communicates via newline-delimited commands on stdin/stdout (e.g., `SugarStartUp`, `SugarActivate`, `SugarShare`, `SugarBuddyJoined`, `SugarQuit`). The pygame UI must embed a lightweight bridge that:
  - Opens pipes to stdin/stdout using non-blocking IO with a dedicated thread or async loop.
  - Parses incoming lines into events dispatched through the Event Bus (`sugar.started`, `sugar.buddy_joined`, etc.).
  - Encodes outgoing UI actions (e.g., `UICitySaved`, `UISoundPlay:<channel>:<sound>`, `UICmd:<payload>`) to stdout exactly as Tcl version to keep the GTK shell working.
- Maintain command compatibility list (documented in `docs/LEGACY_WRAPPERS.md`) so any new pygame-only messages are prefixed (e.g., `PYGAME:`) and ignored safely by older shells.
- Synchronize Sugar-specific states (shared flag, buddy list, nickname) with the player/help panels by updating the shared context when events arrive.
- Ensure graceful shutdown: intercept GTK `SugarQuit` and propagate to pygame loop; send `UIQuitAck` before exiting so Sugar knows the app closed cleanly.

### 6.2 Legacy Global Synchronization

- `sim_control` already mirrors many CamelCase setters/getters via `_legacy_get/_legacy_set`. The pygame UI should:
  - Use `sim_control.types` (legacy namespace) for reads/writes whenever replicating Tk behavior, ensuring test patches that mutate `micropolis.sim_control.types` still observe changes.
  - Provide wrapper functions (e.g., `ui_set_auto_budget(value)`) that call both the new `AppContext` property and `_legacy_set("AutoBudget", value)`.
  - Upon initialization (`initialize_sim_control`), seed the pygame UI state (panels, toggles, data caches) from `types` to stay in sync when headless tests manipulate values without launching the UI.
- Simulation events triggered by C/legacy code (like `UpdateBudget`, `SetFunds`) must continue to emit the CamelCase callbacks, so the pygame UI subscribes via the same shim to avoid missing notifications.
- Document crosswalk table in this checklist (Step 1.3) to keep parity between contexts; treat `types` as single source of truth for compatibility-critical flags.

### 6.3 Audio Integration

- Legacy Tcl UI used `sound.tcl` and `SoundServers` to route effects to logical channels. Recreate this using `audio.py` + `pygame.mixer`:
  - Initialize mixer with sufficient channels and map names: `mode` (background), `edit` (UI clicks), `fancy` (events), `warning` (disasters), `intercom` (notifications).
  - `audio.py` exposes `play_sound(channel, sound_name, loop=False)` which looks up a sample via the AssetManager manifest; each channel can have independent volume/mute state reflecting user toggles (`Sound`, `DoMessages`).
  - For overlapping sounds (e.g., multiple bulldozers), use `Channel.play` with `fade_ms` to avoid clipping; maintain a priority queue so warnings can preempt ambient sounds, matching original behavior.
- Ensure Sugar stdout messages for sound playback (`Sound <name>`) still emit when required so the GTK shell (if still handling audio) can optionally play them; provide config to disable duplicate playback when pygame handles sound locally.

## 7. Testing & Validation

- [x] Add automated tests for widget behavior (input handling, slider bounds, focus traversal) and panel state changes.
- [x] Capture rendering snapshots (golden images) for overlays and panels to catch regressions.
- [x] Run targeted pytest suites (`uv run pytest tests/test_sim_control.py` plus new UI tests) after major milestones.
- [x] Conduct manual parity reviews comparing pygame panels against the Tcl/Tk originals.

### 7.1 Automated UI Test Suite

- Testing tools: use `pytest` + `pygame` headless mode (`SDL_VIDEODRIVER=dummy`) along with helper utilities in `tests/` (add `tests/ui/`).
- Widget tests:
  - Simulate click/hover/focus events using synthesized pygame events to verify state transitions (pressed/disabled, tooltip popups, slider bounds, keyboard traversal).
  - Validate data binding by asserting changes propagate to `AppContext` and legacy `types` (e.g., toggling AutoBudget updates both).
- Panel tests:
  - Instantiate each panel in isolation with mock context; ensure `render()` completes within budget and emits expected dirty rects.
  - Use dependency injection to supply fake Event Bus so tests can inject signals (e.g., `funds.updated`) and assert panel reacts appropriately.
- Regression harness: create scenario fixtures (sample `.cty` files) and run a scripted sequence (load city → switch overlays → open budget) to ensure no exceptions and state remains consistent.

### 7.2 Rendering Snapshot Strategy

- Snapshot tooling: extend `tests/assertions.py` with `assert_surface_matches_golden(surface, name)` that saves output PNGs and compares to reference images using perceptual diff (e.g., Pillow + SSIM with tolerance).
- Coverage:
  - Editor view under various overlays (population, power, lightning blink) using seeded random data for deterministic results.
  - Map/minimap overlays, graphs with known data sets, budget and evaluation panels in both default and active states.
- Golden assets stored under `tests/golden/`; update via explicit command `python scripts/update_golden.py` to avoid accidental drift. Document in README.

### 7.3 Test Execution Workflow

- Continuous integration: add job to run `uv run pytest tests` with `SDL_VIDEODRIVER=dummy`, plus a job to run golden-image comparisons; failures produce diff images as artifacts.
- Targeted suites:
  - `uv run pytest tests/test_sim_control.py` remains smoke test for legacy behavior.
  - `uv run pytest tests/ui/test_panels.py` etc. validate pygame components.
- After implementing major panel or overlay change, rerun entire UI suite + relevant golden snapshots; log results in PR description.

### 7.4 Manual Parity Reviews

- Maintain a checklist per panel comparing new pygame UI to screenshots/video captures of Tcl/Tk version (stored under `docs/manual/parity/`).
- For each release milestone, run through scripted scenarios: load `happisle.cty`, trigger disasters, run budget cycle, check overlays, and record observations.
- Capture side-by-side screenshots and annotate any deviations, deciding whether to accept, fix, or document as intentional change.

## 8. Decommissioning Tcl/Tk

- [x] Remove each legacy `.tcl` file once its functionality is covered in pygame, updating documentation accordingly.
- [x] Update `legacy_compat` and related shims to drop obsolete CamelCase entry points.
- [x] Clean up build/run scripts to default to the pygame UI entry point.

### 8.1 Legacy Script Retirement Plan

- Maintain a migration tracker (table or issue) listing every Tcl/Tk script (`micropolis.tcl`, `w*.tcl`, helpers). For each entry record:
  - Replacement pygame module/panel and status (in-progress, verified, removed).
  - Tests covering the new functionality (unit + parity snapshot) and acceptance criteria.
  - Documentation updates (README, user manual) referencing the new UI.
- Once a panel reaches feature parity and passes Step 7 tests, delete its `.tcl` file, remove references from `micropolis.tcl`, and update `assets/README` to note the pygame replacement. Keep git history/tag for archival access.
- Provide a fallback branch or tag (e.g., `legacy-tk-ui`) for users needing the old UI temporarily.

### 8.2 `legacy_compat` Cleanup

- As soon as all callers switch to snake_case APIs, remove corresponding CamelCase wrappers from `legacy_compat.py` and update documentation in `LEGACY_WRAPPERS.md`.
- For UI-specific CamelCase functions (e.g., `SetGameLevel`, `SetFunds`, `UpdateBudgetWindow`), retire them in batches aligned with panel rollouts:
  - Stage 1: mark wrappers as deprecated, add warnings in logs when called.
  - Stage 2: remove exports, update `sim_control.types` to no longer expose them, and adjust tests to use canonical names.
- Ensure `tests/test_sim_control.py` continues to pass by providing adapter functions or updating tests alongside wrapper removal.

### 8.3 Build & Run Transition

- Entry point: create `micropolis_pygame.py` (or similar) as the default launcher, invoking pygame UI. Update `README.md`, `docs/PORTING_CHECKLIST.md`, and packaging scripts to point users to the new command (`uv run python -m micropolis.pygame_ui`).
- Remove Tcl/Tk build steps (`make all` in `orig_src/`) from default workflow. Keep optional instructions in `docs/LEGACY_WRAPPERS.md` for historians.
- Update Sugar activity definitions (`activity/activity.info`) to run the pygame entry point while still embedding in GTK via the stdin/stdout bridge.
- CI pipeline: drop jobs that exercised the Tcl UI, replacing them with pygame-specific tests and linting. Archive last successful Tcl build artifacts for reference.

## 9. Implementation Rollout Checklist

Use this single consolidated checklist (ordered by dependency) to drive the actual implementation of everything planned in §§1–8.

- [ ] Record the final Tcl/Tk window inventory from §1.1 in the tracker, mapping each script to its pygame replacement module and acceptance criteria.
- [ ] Convert every referenced XPM image, font alias, and sound definition to PNG/TTF/WAV-OGG equivalents and produce the asset manifest described in §§1.2 & 3.3.
- [ ] Implement the `AppContext` ↔ `sim_control` data contract from §1.3, including watchers/tests for every CamelCase global (city metadata, toggles, overlays, budget state).
- [ ] Build the Panel Manager from §2.1 with creation/destruction APIs keyed by the legacy window types.
- [ ] Implement the `UIPanel` base class from §2.2 with lifecycle hooks, focus management, and dirty-rect handling.
- [ ] Deliver the widget toolkit from §2.3 (buttons, toggles, checkboxes, sliders, scroll containers, text labels, modal dialogs, palettes, tooltips) with shared theming.
- [ ] Implement the Event Bus described in §2.1 so pygame events, simulation updates, and Sugar messages flow through a single publish/subscribe layer.
- [ ] Implement the Timer Service from §2.1/§5.3 to replace Tcl `after`, supporting pausable one-shot and repeating timers.
- [ ] Ship the input binding layer from §2.1 & §5.1, including `config/keybindings.json`, runtime remapping UI, and action dispatch hooks.
- [ ] Implement the Asset/Theme service from §§2.1 & 3.3 with caching, sprite slicing, font loading, and sound channel routing APIs.
- [ ] Implement the tile helper cache (`get_tile_surface`, `get_small_tile_surface`) with lightning blink/overlay gating per §3.1.
- [ ] Build the small-tile overlay tint pipeline from §3.1 so minimap overlays can be recolored cheaply.
- [ ] Implement the `MapRenderer` viewport (scrolling, overlays, blinking) per §3.2 and integrate with editor panels.
- [ ] Implement the `MiniMapRenderer` from §3.2 with overlay toggles, viewport rectangle, and quick-jump support.
- [ ] Build the asset preprocessing pipeline from §3.3 (scripts to convert XPM → PNG, emit sound manifests, and cache atlases) and integrate it into the build.
- [ ] Implement the runtime `AssetManager` API from §3.3 with hot-reload hooks for development.
- [ ] Deliver the head/status panel from §4.1 with funds/population/date, speed controls, demand meters, and ticker wiring.
- [ ] Deliver the editor viewport + tool palette from §4.2, including tool preview ghosts, autopan, chalk overlay, and dynamic filter toggles.
- [ ] Deliver the map/minimap panel from §4.3 with overlay buttons, zoom, and click-to-center behavior.
- [ ] Deliver the graphs panel from §4.4 with history plotting, tooltips, and year range controls.
- [ ] Deliver the budget modal from §4.5 with sliders, countdown timer, vote prompts, and pause handling.
- [ ] Deliver the evaluation panel from §4.6 with score breakdowns, recommendations, and auto-evaluation toggles.
- [ ] Deliver the notice/help/player/file dialogs from §4.7 with scrollable panes, Sugar chat hooks, and file picker replacements.
- [ ] Deliver the scenario picker and splash scenes from §4.8 with converted artwork, hotspots, and difficulty selectors.
- [ ] Implement the mouse interaction + hit-testing model from §5.2 (editor painting, drag selection, autopan, chalk) across relevant panels.
- [ ] Wire the Timer Service + Event Bus so shared events (`funds.updated`, `disaster.triggered`, `overlay.changed`) fan out cleanly as described in §5.3.
- [ ] Implement the Sugar stdin/stdout bridge from §6.1, ensuring all legacy commands are mirrored and new pygame-prefixed ones are documented.
- [ ] Mirror legacy globals via `sim_control` per §6.2 so CamelCase setters/getters remain observable for tests.
- [ ] Recreate the audio routing from §6.3 using `audio.py`/`pygame.mixer`, matching channel semantics and optional stdout notifications.
- [ ] Build the automated UI pytest suite from §7.1 (widget + panel tests with SDL dummy driver and dependency injection helpers).
- [ ] Implement the golden-image snapshot harness from §7.2 with perceptual diff tooling and update scripts.
- [ ] Integrate the UI suites and snapshot checks into CI per §7.3, including artifact upload for diffs.
- [ ] Document and schedule manual parity reviews from §7.4 with side-by-side captures of Tcl/Tk vs. pygame panels.
- [ ] Track and delete each Tcl/Tk script once its pygame replacement meets parity, updating docs per §8.1.
- [ ] Remove deprecated CamelCase wrappers from `legacy_compat.py` in stages per §8.2 and update tests to the snake_case APIs.
- [ ] Switch the default build/run path to the pygame entry point, update Sugar activity metadata, and retire Tcl build steps per §8.3.
