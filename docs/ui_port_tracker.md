# UI Port Tracker

This tracker links each legacy Tcl/Tk script to the pygame replacement module plus its acceptance criteria. Use it to measure progress while we complete the rollout checklist in `docs/pygame_ui_port_checklist.md`.

| Tcl/Tk Script | Pygame Replacement Module | Current Status | Acceptance Criteria | Notes |
| --- | --- | --- | --- | --- |
| `micropolis.tcl` | `micropolis.ui.app.AppController` | Inventoried | Launches all pygame panels, wires Sugar IPC, reproduces tool bindings and timers. | Owns Event Bus, Panel Manager, and Timer Service lifecycle. |
| `whead.tcl` | `micropolis.ui.panels.head_panel.HeadPanel` | Inventoried | Displays city name/date/funds/population, speed controls, ticker, demand meters. | Subscribes to `funds.updated`, `population.updated`, and sim speed events. |
| `weditor.tcl` | `micropolis.ui.panels.editor_panel.EditorPanel` | Inventoried | Provides 16×16 editor viewport, tool palettes, auto-goto, dynamic filter, chalk overlay. | Integrates `MapRenderer` and tool preview ghosts with sound hooks. |
| `wmap.tcl` | `micropolis.ui.panels.map_panel.MapPanel` | Inventoried | Renders minimap/overview with overlay selection, zoom, and click-to-center. | Shares data with `MiniMapRenderer` and exposes quick jump buttons. |
| `wgraph.tcl` | `micropolis.ui.panels.graph_panel.GraphPanel` | Inventoried | Shows population/money/pollution graphs with 10/120 year toggles and tooltips. | Plots data sourced from `graphs.py` history buffers. |
| `wbudget.tcl` | `micropolis.ui.panels.budget_panel.BudgetPanel` | Inventoried | Modal dialog with tax + funding sliders, countdown timer, vote prompts. | Pauses simulation, syncs with finance state, emits accept/cancel actions. |
| `weval.tcl` | `micropolis.ui.panels.evaluation_panel.EvaluationPanel` | Inventoried | Displays evaluation breakdown, recommendations, auto-eval toggle, quick actions. | Consumes evaluation data/model from `evaluation.py`. |
| `wnotice.tcl` | `micropolis.ui.panels.notice_panel.NoticePanel` | Inventoried | Scrollable notice stack with severity colors, filters, clear/mute controls. | Hooks into `messages.SendMes` output and Sugar notifications. |
| `wplayer.tcl` | `micropolis.ui.panels.player_panel.PlayerPanel` | Inventoried | Sugar chat/buddy list with messaging UI and presence indicators. | Uses Sugar bridge topics to reflect shared state. |
| `whelp.tcl` | `micropolis.ui.panels.help_panel.HelpPanel` | Inventoried | Contextual help browser with scrollable content and topic navigation. | Reacts to tooltip `SetHelp` events from other panels. |
| `wfile.tcl` | `micropolis.ui.panels.file_panel.FilePanel` | Inventoried | Load/save/new dialogs with recent cities, thumbnails, name entry. | Calls `file_io` helpers and updates `AppContext`. |
| `wask.tcl` | `micropolis.ui.panels.dialogs.VoteDialog` | Inventoried | Blocking yes/no prompt for budget votes and confirmation dialogs. | Integrates with Budget panel timer + `DoVote` callbacks. |
| `wfrob.tcl` | `micropolis.ui.panels.debug_panel.DebugPanel` | Inventoried | Developer diagnostics (frob toggles, disaster triggers). | Invokes debug hooks on `engine` and logs actions. |
| `wscen.tcl` | `micropolis.ui.panels.scenario_panel.ScenarioPanel` | Inventoried | Scenario picker with thumbnails/difficulty toggles. | Launches scenarios and difficulty settings, updates UI state. |
| `wscen_old.tcl` / `wscen_older.tcl` | `micropolis.ui.panels.scenario_panel.LegacyScenarioView` | Inventoried | Optional legacy layout toggle for parity documentation. | Shares backing data with ScenarioPanel; can be feature flagged. |
| `wsplash.tcl` | `micropolis.ui.scenes.splash.SplashScene` | Inventoried | Splash/intro slideshow that transitions into game start actions. | Uses Timer Service for timed slides and supports skip input. |
| Support scripts (`button.tcl`, `menu.tcl`, etc.) | `micropolis.ui.widgets` package | Inventoried | Provide widget toolkit (buttons, menus, sliders, scroll containers) with theming. | Widgets must expose accessibility metadata and event hooks. |

Progress for each module is tracked via linked issues, tests, and parity screenshots. Update the "Current Status" column as implementations land.
