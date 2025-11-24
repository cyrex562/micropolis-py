# Legacy CamelCase functions report

This report tracks the remaining CamelCase entry points that the port is still gradually migrating to snake_case.

**Note (2025-11-15):** The `src/micropolis/legacy_compat.py` file has been removed as part of the pygame UI port cleanup (§8.2). It contained unused CamelCase wrapper functions that were never imported by any production code or tests. All active CamelCase APIs are now managed directly within their respective modules (e.g., `updates.py`, `sim_control.py`) where they serve as documented backward-compatibility interfaces.

## Legacy Tcl/Tk Build Instructions (Deprecated)

**WARNING: The Tcl/Tk UI is no longer maintained and has been fully replaced by the pygame-based interface. These instructions are preserved for historical reference only.**

The original Micropolis C/Tcl/Tk implementation resides in `orig_src/` and is no longer part of the default build workflow. To build the legacy system:

### Prerequisites

- C compiler (gcc or clang)
- Tcl 8.x development headers
- Tk 8.x development headers
- X11 libraries (for Unix/Linux)
- Make

### Build Steps

```bash
cd orig_src

# Build Tcl, Tk, TclX, and sim binary
make all

# Copy binary to resource directory
make install

# Return to project root
cd ..

# Run legacy Tcl/Tk UI via GTK wrapper
python orig_src/micropolisactivity.py
```

### Makefile Targets

- `make all`: Builds all components (tcl, tk, tclx, sim)
- `make clean`: Removes build artifacts
- `make install`: Copies built binary to `../res/sim`

### Legacy File Structure

- `orig_src/sim/`: C simulation engine source
- `orig_src/tcl/`: Tcl interpreter source
- `orig_src/tk/`: Tk GUI toolkit source
- `orig_src/tclx/`: Extended Tcl commands
- `orig_src/micropolisactivity.py`: Sugar GTK wrapper (Python 2)
- `assets/*.tcl`: Legacy UI scripts (micropolis.tcl, w*.tcl)

### Known Issues

- Requires Python 2.7 for Sugar wrapper
- Not compatible with modern Sugar Desktop versions
- Build process may fail on recent Linux distributions
- No Windows or macOS support

### Migration Path

For access to archived Tcl/Tk versions:

- **Branch**: `git checkout legacy-tk-ui`
- **Tags**: `git checkout tcl-<scriptname>-final` (per-script retirement tags)
- **Snapshots**: See `docs/manual/parity/` for screenshots

All users should migrate to the pygame UI (`uv run micropolis`) for ongoing development and bug fixes.

## Sugar Protocol Bridge Commands

The new pygame-based UI implements a non-blocking bridge for Sugar activity stdin/stdout communication through `src/micropolis/ui/sugar_bridge.py`. This bridge maintains compatibility with the legacy Tcl/Tk interface protocol.

### Incoming Commands (stdin → pygame)

Commands received from the Sugar GTK wrapper via stdin, published to Event Bus under `sugar.*` namespace:

- `SugarStartUp <uri>`: Initialize activity with given URI (e.g., city file path or config parameters)
  - Event: `sugar.startup` with payload `{"uri": "..."}`
  - Updates bridge state: `uri` property

- `SugarNickName <nickname>`: Set player's display name from Sugar profile
  - Event: `sugar.nickname` with payload `{"nickname": "..."}`
  - Updates bridge state: `nickname` property

- `SugarActivate`: Activity window gained focus
  - Event: `sugar.activate` with payload `{"activated": True}`
  - Updates bridge state: `activated = True`

- `SugarDeactivate`: Activity window lost focus
  - Event: `sugar.deactivate` with payload `{"activated": False}`
  - Updates bridge state: `activated = False`

- `SugarShare`: Activity was shared with other Sugar buddies
  - Event: `sugar.share` with payload `{"shared": True}`
  - Updates bridge state: `shared = True`

- `SugarBuddyAdd <key> <nick> <color> <address>`: Buddy joined shared session
  - Event: `sugar.buddy_add` with payload `{"key": "...", "nick": "...", "color": "...", "address": "..."}`
  - Updates bridge state: appends to `buddies` list

- `SugarBuddyDel <key> <nick> <color> <address>`: Buddy left shared session
  - Event: `sugar.buddy_del` with payload `{"key": "...", "nick": "...", "color": "...", "address": "..."}`
  - Updates bridge state: removes from `buddies` list

- `SugarQuit`: Graceful shutdown request from GTK shell
  - Event: `sugar.quit`
  - Updates bridge state: `shutdown_requested = True`
  - Application must call `bridge.send_quit_ack()` before exiting

### Outgoing Notifications (pygame → stdout)

Notifications sent from pygame UI to Sugar GTK wrapper via stdout:

- `UIHeadPanelReady`: Signals head panel initialization complete
- `UICitySaved <filename>`: City file saved successfully
- `UISoundPlay:<channel>:<sound>`: Play sound effect (for hybrid audio setups)
  - Channels: `mode`, `edit`, `fancy`, `warning`, `intercom`
- `UICmd:<payload>`: Custom command for GTK shell extensions
- `UIQuitAck`: Acknowledge quit request and confirm clean shutdown
- `PYGAME:<message>`: pygame-specific messages (prefixed, safely ignored by older shells)

### Bridge API Usage

```python
from micropolis.ui import get_default_sugar_bridge, get_default_event_bus

# Initialize bridge with event bus
bridge = get_default_sugar_bridge()
bus = get_default_event_bus()

# Subscribe to Sugar events
bus.subscribe("sugar.quit", lambda e: handle_shutdown())
bus.subscribe("sugar.buddy_add", lambda e: show_buddy_notification(e.payload))

# Start reader thread
bridge.start()

# Main game loop
while running:
    # Process queued commands (call from main thread)
    bridge.process_commands()
    
    # Check shutdown request
    if bridge.shutdown_requested:
        bridge.send_quit_ack()
        running = False
    
    # Send notifications
    bridge.send_ui_ready("EditorPanel")
    bridge.send_city_saved("test.cty")

# Clean shutdown
bridge.stop()
```

### Testing Sugar Protocol

The bridge is fully tested in `tests/ui/test_sugar_bridge.py` with:

- Mock stdin/stdout streams for command injection
- Event Bus verification for all published events
- Full lifecycle simulation (startup → share → quit)
- Thread safety and graceful shutdown handling

For manual testing with actual Sugar wrapper:

1. Ensure `micropolisactivity.py` sends commands via stdin
2. Monitor pygame stdout for expected notifications
3. Verify state synchronization through bridge properties

## Consolidated compatibility wrappers

The CamelCase functions defined in the following modules are now re-exported via `legacy_compat.py`. Because each wrapper simply delegates to the canonical snake_case implementation, these modules no longer show up in the active port queue:

- `engine.py`
- `file_io.py`
- `generation.py`
- `initialization.py`
- `macros.py`
- `map_view.py`
- `power.py`
- `printing.py`
- `random.py`
- `scanner.py`
- `sprite_manager.py`
- `tools.py`
- `traffic.py`
- `updates.py`
- `view_types.py`

Once callers switch to the snake_case exports, these wrappers can be retired and the functions will naturally drop out of future reports.

## Remaining CamelCase implementations to port

### `evaluation.py` (15 functions)

- CityEvaluation
- EvalInit
- GetAssValue
- DoPopNum
- DoProblems
- VoteProblems
- AverageTrf
- GetUnemployment
- GetFire
- GetScore
- DoVotes
- ChangeEval
- UpdateBudget
- DoBudget
- DoBudgetFromMenu

### `interactions.py` (1 function)

- Tk_IntervalCmd *(stub that currently returns `None`; replace with a real command factory once the interval widget is fully integrated)*

### `mac_compat.py` (5 functions)

- NewPtr
- GetResource
- ResourceSize
- ResourceName
- ResourceID

### `stubs.py` (33 functions)

- Spend
- SetFunds
- TickCount
- NewPtr
- GameStarted
- DoPlayNewCity
- DoReallyStartGame
- DoStartLoad
- DoStartScenario
- DropFireBombs
- InitGame
- ReallyQuit
- GetGameLevel
- SetGameLevel
- GetSimSpeed
- SetSimSpeed
- GetNoDisasters
- SetNoDisasters
- GetAutoBulldoze
- SetAutoBulldoze
- GetAutoBudget
- SetAutoBudget
- GetUserSoundOn
- SetUserSoundOn
- GetCityName
- SetCityName
- GetScenarioID
- SetScenarioID
- GetStartupMode
- SetStartupMode
- GetStartupName
- SetStartupName
- PlaceholderFunction

### `terrain.py` (5 functions)

- ClearMap
- ClearUnnatural
- SmoothTrees
- SmoothWater
- SmoothRiver

### `utilities.py` (5 functions)

- Rand
- Rand16
- GetSprite
- MakeSprite
- MakeNewSprite

### `zones.py` (30 functions)

- DoZone
- DoHospChur
- SetSmoke
- DoIndustrial
- DoCommercial
- DoResidential
- MakeHosp
- GetCRVal
- DoResIn
- DoComIn
- DoIndIn
- IncROG
- DoResOut
- DoComOut
- DoIndOut
- RZPop
- CZPop
- IZPop
- BuildHouse
- ResPlop
- ComPlop
- IndPlop
- EvalLot
- ZonePlop
- EvalRes
- EvalCom
- EvalInd
- DoFreePop
- SetZPower
- MakeTraf

## Next steps

1. Port the functions in `evaluation.py` to snake_case (e.g., `city_evaluation`, `get_assessed_value`) and update the simulation/evaluation hooks to use the canonical names. These routines still contain the evaluation logic and will likely stay in that module.
2. Replace the stubbed `Tk_IntervalCmd` with a real factory or drop it once the TCL/Tk integration is no longer needed in the UI layer.
3. Migrate or wrap the `mac_compat.py` and `stubs.py` APIs so their CamelCase entry points can be retired in favor of lower-case helpers; consider funneling the minimal wrappers through `legacy_compat.py` during the transition.
4. Decide on canonical names for the `terrain.py`, `utilities.py`, and `zones.py` functions and expose snake_case versions alongside compatibility shims as needed so the CamelCase definitions drop out.

Total CamelCase functions remaining: 94.

Generated by autogen scan. These are remaining CamelCase functions across src/micropolis.

## engine.py

- SignalExitHandler
- DoStopMicropolis
- InitFundingLevel
- StopEarthquake
- ResetMapState
- ResetEditorState
- ClearMap
- SetFunds
- SetGameLevelFunds
- UpdateBudgetWindow
- UpdateFlush
- DoUpdateEditor
- DoUpdateHeads
- DoUpdateMap
- MoveObjects
- DoTimeoutListen

## evaluation.py

- CityEvaluation
- EvalInit
- GetAssValue
- DoPopNum
- DoProblems
- VoteProblems
- AverageTrf
- GetUnemployment
- GetFire
- GetScore
- DoVotes
- ChangeEval
- UpdateBudget
- DoBudget
- DoBudgetFromMenu

## file_io.py

- LoadScenario
- LoadCity
- SaveCity
- DoSaveCityAs
- SaveCityAs
- DidLoadScenario
- DidLoadCity
- DidntLoadCity
- DidSaveCity
- DidntSaveCity

## generation.py

- GenerateNewCity
- GenerateSomeCity
- ERand
- GenerateMap
- ClearMap
- ClearUnnatural
- MakeNakedIsland
- MakeIsland
- MakeLakes
- GetRandStart
- MoveMap
- DoRivers
- DoBRiv
- DoSRiv
- PutOnMap
- BRivPlop
- SRivPlop
- TreeSplash
- DoTrees
- SmoothRiver
- IsTree
- SmoothTrees
- SmoothWater

## initialization.py

- RandomlySeedRand
- InitGraphMax
- DestroyAllSprites
- ResetLastKeys
- DoNewGame
- DoUpdateHeads
- InitWillStuff
- ResetMapState
- ResetEditorState
- InitializeSimulation
- InitGame
- ResetSimulation
- InitFundingLevel

## interactions.py

- Tk_IntervalCmd

## legacy_compat.py

- GenerateTrain
- GenerateBus
- GenerateShip
- GeneratePlane
- GenerateCopter
- MakeExplosion
- MakeExplosionAt
- GetSprite
- MakeSprite
- DoUpdateHeads
- UpdateEditors
- UpdateMaps
- UpdateGraphs
- UpdateEvaluation
- UpdateHeads
- UpdateFunds
- ReallyUpdateFunds
- SetDemand
- UpdateOptionsMenu
- MakeNewInk
- MakeNewXDisplay
- MakeNewSimGraph
- MakeNewSimDate
- MakeNewPerson
- MakeNewCmd
- MakeNewSimExtended
- MakeSound
- PrintRect
- PrintHeader
- PrintDefTile
- FirstRow
- PrintTile
- PrintNextRow
- PrintFinish
- PrintTrailer
- Rand
- RandInt
- Rand16
- TickCount
- ClearMes
- SendMes
- SendMesAt

## mac_compat.py

- NewPtr
- GetResource
- ResourceSize
- ResourceName
- ResourceID

## macros.py

- ABS
- TestBounds
- TILE_IS_NUCLEAR
- TILE_IS_VULNERABLE
- TILE_IS_ARSONABLE
- TILE_IS_RIVER_EDGE
- TILE_IS_FLOODABLE
- TILE_IS_RUBBLE
- TILE_IS_FLOODABLE2

## map_view.py

- GetCI
- MemDrawMap

## power.py

- DoPowerScan
- MoveMapSim
- TestForCond
- SetPowerBit
- TestPowerBit
- PushPowerStack
- ClearPowerBit

## printing.py

- PrintRect
- PrintHeader
- PrintDefTile
- FirstRow
- PrintTile
- PrintNextRow
- PrintFinish
- PrintTrailer

## random.py

- Rand
- RandInt
- Rand16

## scanner.py

- FireAnalysis
- PopDenScan
- GetPDen
- PTLScan
- GetPValue
- GetDisCC
- CrimeScan
- SmoothTerrain
- DoSmooth
- DoSmooth2
- ClrTemArray
- SmoothFSMap
- SmoothPSMap
- DistIntMarket

## sprite_manager.py

- GenerateTrain
- GenerateBus
- GenerateShip
- GeneratePlane
- GenerateCopter
- MakeExplosion
- MakeExplosionAt
- GetSprite
- MakeSprite

## stubs.py

- Spend
- SetFunds
- TickCount
- NewPtr
- GameStarted
- DoPlayNewCity
- DoReallyStartGame
- DoStartLoad
- DoStartScenario
- DropFireBombs
- InitGame
- ReallyQuit
- GetGameLevel
- SetGameLevel
- GetSimSpeed
- SetSimSpeed
- GetNoDisasters
- SetNoDisasters
- GetAutoBulldoze
- SetAutoBulldoze
- GetAutoBudget
- SetAutoBudget
- GetUserSoundOn
- SetUserSoundOn
- GetCityName
- SetCityName
- GetScenarioID
- SetScenarioID
- GetStartupMode
- SetStartupMode
- GetStartupName
- SetStartupName
- PlaceholderFunction

## terrain.py

- ClearMap
- ClearUnnatural
- SmoothTrees
- SmoothWater
- SmoothRiver

## tools.py

- Spend
- MakeSound
- MakeSoundOn
- ConnecTile
- DoShowZoneStatus
- DidTool
- DoSetWandState
- ToolDown
- ToolUp
- ToolDrag
- DoTool
- DoPendTool
- NewInk
- FreeInk
- StartInk
- AddInk
- ChalkTool
- ChalkStart
- ChalkTo
- EraserTool
- InkInBox
- EraserStart
- EraserTo

## traffic.py

- MakeTraf
- SetTrafMem
- PushPos
- PullPos
- FindPRoad
- FindPTele
- TryDrive
- TryGo
- GetFromMap
- MoveMapSim
- DriveDone
- RoadTest
- AverageTrf

## updates.py

- DoUpdateHeads
- UpdateEditors
- UpdateMaps
- UpdateGraphs
- UpdateEvaluation
- UpdateHeads
- UpdateFunds
- ReallyUpdateFunds
- SetDemand
- UpdateOptionsMenu

## utilities.py

- Rand
- Rand16
- GetSprite
- MakeSprite
- MakeNewSprite

## view_types.py

- MakeNewInk
- MakeNewXDisplay
- MakeNewSimGraph
- MakeNewSimDate
- MakeNewPerson
- MakeNewCmd
- MakeNewSimExtended
- ViewRedrawPending
- SetViewRedrawPending
- GetViewClass
- IsEditorView
- IsMapView
- UpdateViewDisplay
- HandleViewEvent
- DrawViewOverlay

## zones.py

- DoZone
- DoHospChur
- SetSmoke
- DoIndustrial
- DoCommercial
- DoResidential
- MakeHosp
- GetCRVal
- DoResIn
- DoComIn
- DoIndIn
- IncROG
- DoResOut
- DoComOut
- DoIndOut
- RZPop
- CZPop
- IZPop
- BuildHouse
- ResPlop
- ComPlop
- IndPlop
- EvalLot
- ZonePlop
- EvalRes
- EvalCom
- EvalInd
- DoFreePop
- SetZPower
- MakeTraf

Total CamelCase functions: 311
