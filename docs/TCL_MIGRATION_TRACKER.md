# Tcl/Tk to Pygame Migration Tracker

This document tracks the retirement of legacy Tcl/Tk scripts as their pygame replacements reach feature parity.

## Migration Status Legend

- ✅ **RETIRED** - Tcl script deleted, pygame replacement verified
- 🟢 **READY** - Pygame replacement complete, tests passing, pending final review
- 🟡 **IN PROGRESS** - Pygame implementation underway
- 🔴 **NOT STARTED** - No pygame replacement yet
- 📦 **KEEP** - Supporting library/helper, may be needed for reference

## Core Window Scripts

| Tcl Script | Status | Pygame Replacement | Tests | Notes | Retired Date |
|------------|--------|-------------------|-------|-------|--------------|
| `micropolis.tcl` | 🟢 READY | `src/micropolis/ui/app.py` + panel system | ✅ `tests/ui/test_app.py` | Root launcher with panel orchestration | - |
| `whead.tcl` | ✅ RETIRED | `src/micropolis/ui/panels/head_panel.py` | ✅ `tests/ui/test_head_panel.py` | Head/status panel with funds, date, speed controls | 2025-01-15 |
| `weditor.tcl` | 🟢 READY | `src/micropolis/ui/panels/editor_panel.py` + `editor_view.py` | ✅ `tests/ui/test_editor_panel.py` | Main editor canvas + tool palette | - |
| `wmap.tcl` | 🟢 READY | `src/micropolis/ui/panels/map_panel.py` | ✅ `tests/ui/test_map_panel.py` | Overview/minimap with overlay controls | - |
| `wgraph.tcl` | 🟢 READY | `src/micropolis/ui/panels/graph_panel.py` | ✅ `tests/ui/test_graph_panel.py` | Population, money, pollution graphs | - |
| `wbudget.tcl` | 🟢 READY | `src/micropolis/ui/panels/budget_panel.py` | ✅ `tests/ui/test_budget_panel.py` | Budget dialog with sliders and timer | - |
| `weval.tcl` | 🟢 READY | `src/micropolis/ui/panels/evaluation_panel.py` | ✅ `tests/ui/test_evaluation_panel.py` | Evaluation window with scores | - |
| `wnotice.tcl` | 🟢 READY | `src/micropolis/ui/panels/notice_panel.py` | ✅ `tests/ui/test_notice_panel.py` | Message/notice window stack | - |
| `wplayer.tcl` | 🟢 READY | `src/micropolis/ui/panels/player_panel.py` | ✅ `tests/ui/test_player_panel.py` | Player/chat window for Sugar networking | - |
| `whelp.tcl` | 🟢 READY | `src/micropolis/ui/panels/help_panel.py` | ✅ `tests/ui/test_help_panel.py` | Contextual help browser | - |
| `wfile.tcl` | 🟢 READY | `src/micropolis/ui/dialogs/file_dialog.py` | ✅ `tests/ui/test_file_dialog.py` | File/load/save dialog | - |
| `wask.tcl` | 🟢 READY | `src/micropolis/ui/dialogs/ask_dialog.py` | ✅ `tests/ui/test_ask_dialog.py` | Confirmation prompt (Yes/No/Ask) | - |
| `wfrob.tcl` | 🟡 IN PROGRESS | `src/micropolis/ui/panels/debug_panel.py` | ⏳ Planned | Developer frob controls/diagnostics | - |
| `wscen.tcl` | 🟢 READY | `src/micropolis/ui/scenes/scenario_scene.py` | ✅ `tests/ui/test_scenario_scene.py` | Scenario picker with difficulty | - |
| `wscen_old.tcl` | 🔴 DEPRECATED | N/A - superseded by wscen.tcl | N/A | Legacy scenario UI for reference only | - |
| `wscen_older.tcl` | 🔴 DEPRECATED | N/A - superseded by wscen.tcl | N/A | Older legacy scenario UI for reference | - |
| `wsplash.tcl` | 🟢 READY | `src/micropolis/ui/scenes/splash_scene.py` | ✅ `tests/ui/test_splash_scene.py` | Splash screen and intro slideshow | - |

## Widget/Helper Scripts

| Tcl Script | Status | Pygame Replacement | Tests | Notes | Retired Date |
|------------|--------|-------------------|-------|-------|--------------|
| `button.tcl` | 🟢 READY | `src/micropolis/ui/widgets/button.py` | ✅ `tests/ui/widgets/test_button.py` | Custom button widget with states | - |
| `menu.tcl` | 🟢 READY | `src/micropolis/ui/widgets/menu.py` | ✅ `tests/ui/widgets/test_menu.py` | Menu system with traversal | - |
| `listbox.tcl` | 🟢 READY | `src/micropolis/ui/widgets/listbox.py` | ✅ `tests/ui/widgets/test_listbox.py` | Listbox selection widget | - |
| `entry.tcl` | 🟢 READY | `src/micropolis/ui/widgets/entry.py` | ✅ `tests/ui/widgets/test_entry.py` | Text entry field | - |
| `text.tcl` | 🟢 READY | `src/micropolis/ui/widgets/text.py` | ✅ `tests/ui/widgets/test_text.py` | Multiline text display/editing | - |
| `help.tcl` | 🟢 READY | `src/micropolis/ui/help_system.py` | ✅ `tests/ui/test_help_system.py` | Help content loading and display | - |
| `sound.tcl` | ✅ RETIRED | `src/micropolis/audio.py` | ✅ `tests/test_audio.py` | Sound playback and channel routing | 2025-01-10 |
| `init.tcl` | 📦 KEEP | N/A - Tcl initialization | N/A | Tcl runtime initialization (archival) | - |
| `tk.tcl` | 📦 KEEP | N/A - Tk library | N/A | Standard Tk library (archival) | - |
| `tclinit.tcl` | 📦 KEEP | N/A - Tcl initialization | N/A | Tcl environment setup (archival) | - |
| `tkerror.tcl` | 📦 KEEP | N/A - Error handling | N/A | Tk error display (archival) | - |
| `wish.tcl` | 📦 KEEP | N/A - Wish shell | N/A | Wish interpreter setup (archival) | - |
| `wishx.tcl` | 📦 KEEP | N/A - Extended wish | N/A | Extended wish setup (archival) | - |
| `parray.tcl` | 📦 KEEP | N/A - Debug utility | N/A | Array printing helper (archival) | - |
| `mkindex.tcl` | 📦 KEEP | N/A - Build utility | N/A | Tcl package index builder (archival) | - |
| `buildidx.tcl` | 📦 KEEP | N/A - Build utility | N/A | Asset index builder (archival) | - |

## Retirement Process

When a pygame replacement reaches parity:

1. **Verify Tests Pass**

   ```bash
   uv run pytest tests/ui/test_<panel_name>.py -v
   uv run pytest tests/ui/test_integration.py -k <panel_name>
   ```

2. **Run Manual Parity Review**
   - Load reference screenshots from `docs/manual/parity/`
   - Execute scripted scenarios (see §7.4)
   - Document any intentional deviations

3. **Update Documentation**
   - Mark status as ✅ RETIRED in this tracker
   - Update `assets/README.md` to note pygame replacement
   - Update main `README.md` if entry point changed
   - Update `docs/PORTING_CHECKLIST.md`

4. **Archive and Delete**

   ```bash
   # Tag for archival access
   git tag -a tcl-ui-final-<script> -m "Last version before retiring <script>.tcl"
   
   # Remove the script
   git rm assets/<script>.tcl
   
   # Update tclindex if needed
   cd assets && tclsh mkindex.tcl
   ```

5. **Update References**
   - Remove from `micropolis.tcl` if applicable
   - Remove from build scripts
   - Add to legacy fallback branch if maintained

## Acceptance Criteria per Panel

### whead.tcl → head_panel.py

- ✅ Display city name (editable), funds, population, date
- ✅ Simulation speed controls (pause/slow/normal/fast)
- ✅ Demand meters (R/C/I) with color indicators
- ✅ Message ticker with marquee scrolling
- ✅ Sugar buddy badge when shared
- ✅ Event subscriptions for funds/population/date updates
- ✅ Legacy global synchronization via sim_control.types

### weditor.tcl → editor_panel.py

- ✅ 16×16 tile viewport with drag-to-scroll
- ✅ Tool palette with all 21 tools (icons, costs, tooltips)
- ✅ Tool preview ghosts (valid/invalid tinting)
- ✅ AutoGoto, Chalk overlay, Dynamic filter toggles
- ✅ Keyboard panning and autopan at edges
- ✅ Line/rectangle drawing for roads/zones
- ✅ Tool selection sync with sim_control.set_tool
- ✅ Sound effects for palette clicks and errors

### wmap.tcl → map_panel.py

- ✅ 4×4 minimap rendering entire city
- ✅ Overlay buttons (Power/Traffic/Pollution/etc.)
- ✅ Viewport rectangle showing editor position
- ✅ Click-to-center editor view
- ✅ Zoom controls (overall/city/district)
- ✅ Quick-jump buttons (Police/Fire coverage)
- ✅ Dynamic filter toggle

### wgraph.tcl → graph_panel.py

- ✅ Population, R/C/I demand, Money, Crime, Pollution graphs
- ✅ 10-year vs 120-year mode toggle
- ✅ Hover tooltips with exact values
- ✅ Show/hide individual lines via checkboxes
- ✅ Legend with color coding
- ✅ UpdateGraphs event subscription

### wbudget.tcl → budget_panel.py

- ✅ Modal overlay pausing simulation
- ✅ Tax rate slider (0-20%)
- ✅ Road/Fire/Police fund sliders with percentage labels
- ✅ Countdown timer with auto-accept
- ✅ Accept/Cancel buttons
- ✅ Vote prompt integration (wask functionality)
- ✅ Preview calculations (100% of $X = $Y)

### weval.tcl → evaluation_panel.py

- ✅ Multi-column score breakdown
- ✅ Bar indicators for each category
- ✅ Textual recommendations from evaluation.py
- ✅ "Run Evaluation" button
- ✅ "View Budget" button
- ✅ Auto-evaluation toggle
- ✅ Problems/issues list with suggested fixes

### wnotice.tcl → notice_panel.py

- ✅ Dismissible message cards with severity colors
- ✅ Auto-scroll for long text
- ✅ Clear All and Mute buttons
- ✅ Filters (finance/disasters/advisor)
- ✅ Integration with messages.SendMes
- ✅ DoMessages toggle respect

### wplayer.tcl → player_panel.py

- ✅ Chat input field and log display
- ✅ Buddy list from Sugar networking
- ✅ Connection status indicators
- ✅ Sugar IPC integration via stdin/stdout bridge
- ✅ ChatServer and ChannelName handling

### whelp.tcl → help_panel.py

- ✅ HTML-lite help content rendering
- ✅ Scrollable viewport
- ✅ SetHelp integration with tooltips
- ✅ Section highlighting and deep links
- ✅ Topic navigation

### wfile.tcl → file_dialog.py

- ✅ Recent cities list with thumbnails
- ✅ Scenario quick-load buttons
- ✅ Text entry for city name and location
- ✅ LoadCity/SaveCity/DoSaveCityAs integration
- ✅ CityDir path handling

### wask.tcl → ask_dialog.py

- ✅ Yes/No/Ask confirmation modal
- ✅ Vote tracking arrays
- ✅ Budget vote prompt integration
- ✅ Scenario prompt support

### wscen.tcl → scenario_scene.py

- ✅ Scenario thumbnail grid
- ✅ Difficulty checkboxes (Easy/Medium/Hard)
- ✅ Preview text with scenario goals
- ✅ Play button triggers engine.load_scenario
- ✅ DoPickScenario/DoPlay/DoGenerate/DoLevel integration
- ✅ Keyboard/controller navigation

### wsplash.tcl → splash_scene.py

- ✅ Full-screen background art
- ✅ Clickable hotspots (About/Load/Generate/Quit)
- ✅ Timed transitions via TimerService
- ✅ SplashScreenDelay handling
- ✅ DoPlay integration

## Git Archival Strategy

Before deleting each script, create preservation tags:

```bash
# One-time: create legacy UI branch point
git checkout -b legacy-tk-ui
git tag -a tcl-ui-complete -m "Complete Tcl/Tk UI before pygame migration"
git push origin legacy-tk-ui
git push origin tcl-ui-complete
git checkout main

# Per-script: tag before removal
git tag -a tcl-<scriptname>-final -m "Last version of <scriptname>.tcl"
git push origin tcl-<scriptname>-final
```

Users needing the old UI can access via:

- Branch: `git checkout legacy-tk-ui`
- Tag: `git checkout tcl-ui-complete`

## Fallback Documentation

Document in main README.md:

```markdown
### Legacy Tcl/Tk UI

The original Tcl/Tk UI has been replaced with a pygame-based interface.
To access the legacy UI:

git checkout legacy-tk-ui
cd src && make all && cd ..
python micropolisactivity.py
```

## Automation Script

See `scripts/retire_tcl_script.py` for automated retirement workflow.

## References

- §8.1 Legacy Script Retirement Plan: `docs/pygame_ui_port_checklist.md`
- Asset migration: `assets/README.md`
- Legacy wrappers: `docs/LEGACY_WRAPPERS.md`
- Parity reviews: `docs/manual/parity/`
