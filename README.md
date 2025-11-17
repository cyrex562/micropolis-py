# Micropolis (Python Port)

A Python 3.13 port of Micropolis (classic SimCity) from C/TCL/Tk to modern pygame-based UI.

## Quick Start

### Prerequisites

- Python 3.13+
- uv package manager
- pygame

### Installation & Running

```bash
# Clone the repository
git clone https://github.com/cyrex562/micropolis-py.git
cd micropolis-py

# Install dependencies
uv sync

# Build assets (required before first run)
uv run python scripts/build_assets.py

# Run the game (pygame UI - default)
uv run python -m micropolis.main

# Or use the installed script
uv run micropolis
```

## Pygame UI - Current Status

**The pygame-based UI is now the default interface.** All core panels (head, editor, map, graphs, budget, evaluation, dialogs) are implemented and functional. The original Tcl/Tk UI has been retired from the main workflow.

For implementation status and remaining work, see `docs/pygame_ui_port_checklist.md`.

## Legacy Tcl/Tk UI (Deprecated)

The original Tcl/Tk interface is no longer maintained and has been moved to `orig_src/` for historical reference. To access:

- **Legacy branch**: `git checkout legacy-tk-ui`
- **Build instructions**: See `docs/LEGACY_WRAPPERS.md`
- **Historical tags**: `git checkout tcl-<scriptname>-final`

**Note**: The legacy UI requires building C/Tcl/Tk components and is not supported in the current development workflow.

## Asset Preprocessing

The pygame UI and supporting tests expect the generated PNGs and
`assets/asset_manifest.json` produced by `scripts/build_assets.py`. Run the
conversion script whenever you clone the repo or touch files under `assets/`:

```bash
uv run python scripts/build_assets.py
```

The CI workflow runs the same command before executing pytest, so local runs that
mirror this step will behave identically.

## Asset Hot Reload (Development)

During UI development you can enable automatic cache invalidation whenever assets
or the manifest on disk change. Set the `MICROPOLIS_ASSET_HOT_RELOAD` environment
variable before launching the pygame UI (or running tests that exercise the UI):

```powershell
$env:MICROPOLIS_ASSET_HOT_RELOAD = "1"
uv run python -m micropolis.main
```

When enabled, the new `AssetHotReloadController` polls the generated manifest and
mapped asset files, clears the runtime `AssetService` caches, and refreshes the
manifest whenever the build output changes.

## Running Tests

The full pytest suite currently contains several hundred modules and exceeds
the automation timeout when executed in a single `uv run pytest` invocation.
Use the helper script to run the suite in manageable batches:

```bash
python3 scripts/run_pytest_chunks.py
```

Pass any extra pytest flags after the script arguments, e.g.:

```bash
python3 scripts/run_pytest_chunks.py --chunk-size 80 -k budget
```

This keeps each `uv run pytest` call under the harness limit while still
exercising the entire test set.

### Pygame Prototype Shortcuts

When running the pygame front-end, the following keys are recognized globally:

- `Space`/`P` toggles pause.
- `0`‑`3` set the simulation speed; `+`/`-` nudge the speed up or down.
- `B` opens the budget window (and pauses while it is open).
- `[` / `]` cycle through the available map overlays.
- `G` toggles the graph display flag, forcing a graph redraw.
- `E` refreshes the evaluation panel data.
