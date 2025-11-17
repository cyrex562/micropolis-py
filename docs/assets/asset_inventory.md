# Asset Inventory (Section 9 · Step 1)

This document captures the final inventory of legacy Tcl/Tk UI resources and binary assets that now live under `assets/`. It fulfills Step 1 of the rollout checklist in `docs/pygame_ui_port_checklist.md` and provides the source data that will feed the pygame conversion pipeline.

## 1. High-Level Counts

| Category | Contents | Count | Size / Notes |
| --- | --- | --- | --- |
| Tcl/Tk window scripts (`w*.tcl`) | Head, editor, map, budget, evaluation, notice, help, player, file, ask, debug, scenario, splash windows | 18 | See §2 for module mapping (tracked in `docs/ui_port_tracker.md`). |
| Support Tcl scripts | `micropolis.tcl`, widget helpers (`button.tcl`, `menu.tcl`, `listbox.tcl`, `entry.tcl`, `text.tcl`, `help.tcl`, `sound.tcl`, `tclinit.tcl`, `tk.tcl`, `tkerror.tcl`, etc.) | 15 | Provide widget definitions, init glue, and sound routing logic. |
| XPM images (`assets/images/`) | Tool icons, palette sprites, scenario art, cursors | 341 files | ~5.1 MB total; to be converted to PNG atlases. |
| Audio samples (`assets/sounds/`) | Bulldozer, siren, UI click, warning, ambient effects | 49 WAV files | ~1.6 MB; routes through pygame mixer channels. |
| Fonts (`assets/dejavu-lgc/`) | Bitmap + TTF versions of DejaVu LGC family | 24 files (21 `.ttf`, extras `.alias/.dir/.scale`) | ~5.3 MB; Tk aliases must be mapped to pygame font sizes. |
| Hexa tables (`assets/hexa.*`) | Packed nibble atlases for minimap/overlay tiles | 9 files | Need decoding helpers in `graphics_setup`. |
| Sound routing tables (`assets/snro.*`) | Legacy `sound.tcl` definitions for volume & routing | 8 files | Feed pygame audio channel mapping. |
| String tables (`assets/stri.*`) | Scenario/help string banks | 4 files | Parsed into UTF-8 message catalogs. |
| Runtime metadata | `assets/asset_manifest.json` (generated) | 1 | Produced/consumed by `micropolis.asset_manager`. |

## 2. Tcl/Tk Window Inventory

Every legacy window script from §1.1 now appears in `docs/ui_port_tracker.md` with its pygame counterpart and acceptance criteria. Quick reference:

| Tcl/Tk Script | Responsibility | Pygame Module |
| --- | --- | --- |
| `micropolis.tcl` | Root launcher, Sugar IPC, timers, tool bindings | `micropolis.ui.app.AppController` |
| `whead.tcl` | Status bar (funds, date, speed, ticker) | `micropolis.ui.panels.head_panel.HeadPanel` |
| `weditor.tcl` | Main editor canvas + palettes | `micropolis.ui.panels.editor_panel.EditorPanel` |
| `wmap.tcl` | Overview/minimap viewer | `micropolis.ui.panels.map_panel.MapPanel` |
| `wgraph.tcl` | Graph history window | `micropolis.ui.panels.graph_panel.GraphPanel` |
| `wbudget.tcl` | Annual budget modal | `micropolis.ui.panels.budget_panel.BudgetPanel` |
| `weval.tcl` | Evaluation/advisor panel | `micropolis.ui.panels.evaluation_panel.EvaluationPanel` |
| `wnotice.tcl` | Notice/message stack | `micropolis.ui.panels.notice_panel.NoticePanel` |
| `wplayer.tcl` | Sugar chat/player list | `micropolis.ui.panels.player_panel.PlayerPanel` |
| `whelp.tcl` | Contextual help browser | `micropolis.ui.panels.help_panel.HelpPanel` |
| `wfile.tcl` | Load/save dialogs | `micropolis.ui.panels.file_panel.FilePanel` |
| `wask.tcl` | Confirmation/vote dialogs | `micropolis.ui.panels.dialogs.VoteDialog` |
| `wfrob.tcl` | Developer debug “frob” window | `micropolis.ui.panels.debug_panel.DebugPanel` |
| `wscen.tcl` | Scenario picker (current) | `micropolis.ui.panels.scenario_panel.ScenarioPanel` |
| `wscen_old.tcl` | Legacy scenario picker | `micropolis.ui.panels.scenario_panel.LegacyScenarioView` |
| `wscen_older.tcl` | Older scenario picker variant | `micropolis.ui.panels.scenario_panel.LegacyScenarioView` (mode flag) |
| `wsplash.tcl` | Splash / intro slideshow | `micropolis.ui.scenes.splash.SplashScene` |
| `wish.tcl` / `wishx.tcl` | Tk launcher wrappers | Superseded by pygame bootstrap but kept for parity tests |

Status for each row is marked “Inventoried” inside the tracker, signaling Step 1 completion. Future work will flip entries to “In Progress”, “Verified”, and “Retired” as pygame implementations land.

## 3. Support Scripts & Widget Helpers

The following Tcl sources do not correspond to standalone windows but define shared behaviors that require pygame equivalents:

- `button.tcl`, `menu.tcl`, `listbox.tcl`, `entry.tcl`, `text.tcl`: custom widget definitions (hover/press states, scrolling text, menu accelerators).
- `help.tcl`: topic loader and dispatcher for `whelp`/tooltip integration.
- `sound.tcl`: logical channel routing for mode/edit/fancy/warning/intercom sounds; references `.snro/.stri` tables.
- `tclinit.tcl`, `tk.tcl`, `tkerror.tcl`, `init.tcl`: runtime bootstrap and error handling.
- `micropolis.tcl`: orchestrates panel creation and maintains shared globals that must be mirrored in `sim_control`.

Each script’s responsibilities are summarized in `docs/ui_port_tracker.md → Notes` to guide pygame widget/toolkit work.

## 4. Binary Resource Families

### 4.1 Images (`assets/images/`)

- 341 XPM files grouped by palette/tool usage (toolbar icons, scenario thumbnails, cursor sprites).
- Conversion plan: batch convert to PNG (keeping alpha) and register them inside the manifest consumed by `micropolis.asset_manager`.
- Metadata requirements: hover/checked variants, palette indices, and hotspot coordinates for scenario buttons.

### 4.2 Fonts (`assets/dejavu-lgc/`)

- 21 `.ttf` files + `.alias/.dir/.scale` metadata from X11. Tk aliases (`Big`, `Medium`, `Ticker`) map to concrete TTF/size pairs.
- Pygame will load via `pygame.font.Font`, caching results inside the asset manager/Theme service.

### 4.3 Audio (`assets/sounds/` + `.snro/.stri` tables)

- 49 WAV files referenced by logical names inside `sound.tcl`.
- `.snro.*` contain channel routing instructions, `.stri.*` contain textual labels/descriptions.
- Need a translation script that emits a JSON manifest (sound → file → channel/default volume) for the pygame audio service.

### 4.4 Hexa Tables (`assets/hexa.*`)

- Packed nibble buffers used to generate the 4×4 minimap tiles (`SIM_GSMTILE`) and overlay masks.
- Loader lives in `graphics_setup.py`; Step 3 work (`src/micropolis/asset_manager.py`) provides canonical paths for these files.

## 5. Asset Manifest & Loader Hooks

- `src/micropolis/asset_manager.py` now loads `assets/asset_manifest.json` exclusively and exposes lookup helpers (`get_asset_path`, `iter_assets`) for the pygame stack.
- The runtime no longer performs ad-hoc directory scans—if the manifest is missing or stale the loader raises immediately so CI/local runs fail fast.
- `scripts/build_assets.py` is therefore the canonical way to refresh converted PNGs, font metadata, and sound routing tables before launching the pygame UI or running tests.

## 6. Automated Conversion Pipeline (Section 9 · Step 2)

Step 2 of the rollout checklist is now automated via `scripts/build_assets.py`:

- **Manual XPM renderer:** Handles legacy 16-bit-per-channel color specs (e.g., `#ffff00000000`), Tk gray aliases (`gray75`, `gray100`), and falls back to a transparent 1×1 placeholder when an asset file is empty (the lone case is `images/tiles-156.xpm`).
- **Fonts & aliases:** Parses `assets/dejavu-lgc/fonts.dir` and `fonts.alias` so every Tk font alias maps to a concrete TTF inside the manifest.
- **Sounds:** Reads `assets/sound.tcl` and records the canonical WAV backing file for each logical sound effect while still listing unreferenced samples.
- **Manifest output:** Emits `assets/asset_manifest.json`, which `micropolis.asset_manager` now loads directly. Running `uv run python scripts/build_assets.py --force-images` performs the conversions and refreshes the manifest; `--manifest-only` skips reconversion if PNGs are current.
- **CI enforcement:** `.github/workflows/tests.yml` runs `uv run python scripts/build_assets.py` ahead of pytest so every pull request produces a fresh manifest before tests.

Latest manifest snapshot (generated 2025-11-14T15:30:06.331545+00:00) reports:

| Metric | Count |
| --- | ---: |
| Converted PNGs | 341 |
| Fonts indexed | 21 |
| Sound effects | 49 |
| Other raw assets (hexa/snro/stri/tcl/etc.) | 405 |

These figures supersede the rough counts in §1 and will stay up to date each time the build script runs.

## 7. Next Steps

1. Use this inventory to drive Step 2 (“Convert every referenced XPM image, font alias, and sound definition”) by scripting conversions + manifest generation.
2. Feed the manifest into the planned Asset/Theme service (§§2.1 & 3.3) so pygame-side loaders no longer hardcode legacy file paths.
3. Keep `docs/assets/asset_inventory.md` updated as assets are converted or retired; when a Tcl script is removed, move its row in the tracker to “Retired” and record the commit/PR for traceability.
