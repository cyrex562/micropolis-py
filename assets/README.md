# Micropolis Assets Directory

This directory contains the legacy Tcl/Tk UI scripts and supporting assets for Micropolis.

## Current Status: Migration to Pygame

**The Tcl/Tk UI is being replaced with a pygame-based interface.** See `docs/TCL_MIGRATION_TRACKER.md` for detailed migration status.

## Legacy Tcl/Tk Scripts

### Core Window Scripts (Being Migrated)

These scripts define the main UI windows and are being replaced by pygame panels:

- `micropolis.tcl` - Root launcher → `src/micropolis/ui/app.py`
- `whead.tcl` - Head/status panel → `src/micropolis/ui/panels/head_panel.py`
- `weditor.tcl` - Editor canvas → `src/micropolis/ui/panels/editor_panel.py`
- `wmap.tcl` - Minimap panel → `src/micropolis/ui/panels/map_panel.py`
- `wgraph.tcl` - Graphs panel → `src/micropolis/ui/panels/graph_panel.py`
- `wbudget.tcl` - Budget dialog → `src/micropolis/ui/panels/budget_panel.py`
- `weval.tcl` - Evaluation panel → `src/micropolis/ui/panels/evaluation_panel.py`
- `wnotice.tcl` - Notice panel → `src/micropolis/ui/panels/notice_panel.py`
- `wplayer.tcl` - Player/chat panel → `src/micropolis/ui/panels/player_panel.py`
- `whelp.tcl` - Help browser → `src/micropolis/ui/panels/help_panel.py`
- `wfile.tcl` - File dialog → `src/micropolis/ui/dialogs/file_dialog.py`
- `wask.tcl` - Confirmation dialog → `src/micropolis/ui/dialogs/ask_dialog.py`
- `wfrob.tcl` - Debug controls → `src/micropolis/ui/panels/debug_panel.py`
- `wscen.tcl` - Scenario picker → `src/micropolis/ui/scenes/scenario_scene.py`
- `wsplash.tcl` - Splash screen → `src/micropolis/ui/scenes/splash_scene.py`

### Widget Helper Scripts (Being Migrated)

- `button.tcl` → `src/micropolis/ui/widgets/button.py`
- `menu.tcl` → `src/micropolis/ui/widgets/menu.py`
- `listbox.tcl` → `src/micropolis/ui/widgets/listbox.py`
- `entry.tcl` → `src/micropolis/ui/widgets/entry.py`
- `text.tcl` → `src/micropolis/ui/widgets/text.py`
- `help.tcl` → `src/micropolis/ui/help_system.py`
- `sound.tcl` → `src/micropolis/audio.py` ✅ **RETIRED**

### Supporting/Library Scripts (Archived)

These scripts are kept for historical reference and Tcl/Tk runtime support:

- `init.tcl`, `tclinit.tcl` - Tcl initialization
- `tk.tcl`, `tkerror.tcl` - Tk library and error handling
- `wish.tcl`, `wishx.tcl` - Wish interpreter setup
- `parray.tcl` - Debug utility
- `mkindex.tcl`, `buildidx.tcl` - Build utilities

### Legacy Scenario Scripts (Superseded)

- `wscen_old.tcl`, `wscen_older.tcl` - Replaced by `wscen.tcl`

## Asset Files

### Graphics

- `images/` - Tile sprites, UI elements, scenario art (XPM → PNG conversion in progress)
- `hexa.*` - Hexadecimal tile data tables
- `stri.*` - String/text resource tables

### Fonts

- `dejavu-lgc/` - DejaVu LGC fonts (converting to TTF for pygame)

### Audio

- `sounds/` - Sound effects (WAV/OGG)
- `snro.*` - Sound resource tables for channel routing

### Metadata

- `asset_manifest.json` - Generated manifest mapping logical names to files
- `tclindex`, `*.tdx`, `*.tlb` - Tcl package indexes

## Using the Legacy Tcl/Tk UI

To run the original Tcl/Tk interface (for reference/testing):

```bash
# Build the C simulation engine with Tcl/Tk support
cd orig_src
make all
cd ..

# Run with Tcl/Tk UI
python micropolisactivity.py
```

**Note:** The default entry point now uses the pygame UI. See the main README for instructions.

## Accessing Historical Versions

The legacy Tcl/Tk UI is preserved in git:

```bash
# Access the complete legacy UI
git checkout legacy-tk-ui

# Access specific script before retirement
git checkout tcl-<scriptname>-final
```

## Migration Tools

Use `scripts/retire_tcl_script.py` to manage the retirement of Tcl scripts:

```bash
# Check if a script is ready to retire
uv run python scripts/retire_tcl_script.py check whead.tcl

# Retire a script (with parity checks)
uv run python scripts/retire_tcl_script.py retire whead.tcl

# List all scripts and their status
uv run python scripts/retire_tcl_script.py list
```

## Documentation

- **Migration Tracker:** `docs/TCL_MIGRATION_TRACKER.md` - Detailed status of each script
- **Port Checklist:** `docs/pygame_ui_port_checklist.md` - Implementation plan
- **Legacy Wrappers:** `docs/LEGACY_WRAPPERS.md` - Compatibility layer documentation

## Contributing

When working on the pygame migration:

1. Reference the Tcl scripts for behavioral specifications
2. Update `docs/TCL_MIGRATION_TRACKER.md` with your progress
3. Ensure tests pass before marking a script as READY
4. Use the retirement script to safely remove legacy files

See `docs/pygame_ui_port_checklist.md` for detailed implementation guidance.
