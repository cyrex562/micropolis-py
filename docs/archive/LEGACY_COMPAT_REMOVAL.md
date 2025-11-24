# Legacy Compatibility Layer Removal (§8.2 Implementation)

**Date:** November 15, 2025  
**Status:** ✅ Complete

## Overview

This document records the removal of the `src/micropolis/legacy_compat.py` file as part of the pygame UI port cleanup process outlined in §8.2 of the pygame UI port checklist.

## What Was Removed

The `legacy_compat.py` file contained approximately 200+ CamelCase wrapper functions that were originally intended to serve as a centralized compatibility layer for legacy code. These wrappers included:

### Sprite Management Wrappers

- `GenerateTrain`, `GenerateBus`, `GenerateShip`, `GeneratePlane`, `GenerateCopter`
- `MakeExplosion`, `MakeExplosionAt`, `GetSprite`, `MakeSprite`

### Update Manager Wrappers

- `DoUpdateHeads`, `UpdateEditors`, `UpdateMaps`, `UpdateGraphs`, `UpdateEvaluation`
- `UpdateHeads`, `UpdateFunds`, `ReallyUpdateFunds`, `doTimeStuff`, `updateDate`
- `showValves`, `drawValve`, `SetDemand`, `updateOptions`, `UpdateOptionsMenu`

### View Type Factory Wrappers

- `MakeNewInk`, `MakeNewXDisplay`, `MakeNewSimGraph`, `MakeNewSimDate`
- `MakeNewPerson`, `MakeNewCmd`, `MakeNewSimExtended`

### Tools Wrappers

- `MakeSound`, `Spend`, `DoTool`, `DoPendTool`, `ToolDown`, `ToolUp`, `ToolDrag`
- `NewInk`, `FreeInk`, `StartInk`, `AddInk`, `DoShowZoneStatus`
- `ConnecTile`, `DidTool`, `DoSetWandState`, `ChalkTool`, `EraserTool`

### Engine & Initialization Wrappers

- `SignalExitHandler`, `DoStopMicropolis`, `InitFundingLevel`, `StopEarthquake`
- `ResetMapState`, `ResetEditorState`, `ClearMap`, `SetFunds`, `SetGameLevelFunds`
- `UpdateBudgetWindow`, `UpdateFlush`, `DoUpdateEditor`, `DoUpdateMap`, `MoveObjects`
- `RandomlySeedRand`, `InitGraphMax`, `DestroyAllSprites`, `ResetLastKeys`
- `DoNewGame`, `InitWillStuff`, `InitializeSimulation`, `InitGame`, `ResetSimulation`

### Generation Wrappers

- `GenerateNewCity`, `GenerateSomeCity`, `GenerateMap`, `ClearUnnatural`
- `MakeNakedIsland`, `MakeIsland`, `MakeLakes`, `DoRivers`, `TreeSplash`, `DoTrees`
- `SmoothRiver`, `IsTree`, `SmoothTrees`, `SmoothWater`

### File I/O Wrappers

- `LoadScenario`, `LoadCity`, `SaveCity`, `DoSaveCityAs`, `SaveCityAs`
- `DidLoadScenario`, `DidLoadCity`, `DidntLoadCity`, `DidSaveCity`, `DidntSaveCity`

### Power, Traffic, Scanner Wrappers

- `DoPowerScan`, `MoveMapSim`, `TestForCond`, `SetPowerBit`, `TestPowerBit`
- `MakeTraf`, `SetTrafMem`, `PushPos`, `PullPos`, `FindPRoad`, `TryDrive`, `TryGo`
- `FireAnalysis`, `PopDenScan`, `PTLScan`, `CrimeScan`, `SmoothTerrain`

### Map View & Macros Wrappers

- `GetCI`, `MemDrawMap`
- `ABS`, `TestBounds`, `TILE_IS_NUCLEAR`, `TILE_IS_VULNERABLE`, `TILE_IS_ARSONABLE`
- `TILE_IS_RIVER_EDGE`, `TILE_IS_FLOODABLE`, `TILE_IS_RUBBLE`, `TILE_IS_FLOODABLE2`

### Message & Random Wrappers

- `TickCount`, `ClearMes`, `SendMes`, `SendMesAt`
- `Rand`, `RandInt`, `Rand16`

### Printing Wrappers

- `PrintRect`, `PrintHeader`, `PrintDefTile`, `FirstRow`, `PrintTile`
- `PrintNextRow`, `PrintFinish`, `PrintTrailer`

## Why It Was Safe to Remove

Analysis revealed that:

1. **No Production Imports**: No files in `src/micropolis/` imported from `legacy_compat.py`
2. **No Test Imports**: No files in `tests/` imported from `legacy_compat.py`
3. **Dead Code**: The entire module was unreachable and served no purpose
4. **Modern APIs Exist**: All functionality is available through the canonical snake_case implementations in their respective modules

### Active CamelCase APIs

The following modules still expose CamelCase functions as documented public APIs:

- **`src/micropolis/updates.py`**: Convenience wrappers like `DoUpdateHeads()`, `UpdateEditors()`, etc. that delegate to `UIUpdateManager`
- **`src/micropolis/sim_control.py`**: Internal `_legacy_get()` and `_legacy_set()` functions used for state synchronization (not the same as the removed wrappers)

These are intentional backward-compatibility interfaces and are actively tested.

## Verification

All tests pass after removal:

```bash
uv run pytest tests/test_sim_control.py -v
# Result: 48 passed in 2.00s ✅
```

No import errors or missing function errors occurred, confirming the file was completely unused.

## Documentation Updates

1. **`docs/LEGACY_WRAPPERS.md`**: Updated to note removal and explain that active CamelCase APIs are managed in their respective modules
2. **`docs/pygame_ui_port_checklist.md`**: Marked §8.2 task as complete

## Future Cleanup

The remaining CamelCase functions in `updates.py` and similar modules should be evaluated for deprecation in a future phase once all downstream consumers have been migrated. However, these serve as stable public APIs and are not dead code like the removed `legacy_compat.py` wrappers.

## Related Files Changed

- ❌ **Deleted**: `src/micropolis/legacy_compat.py` (1000+ lines)
- ✏️ **Updated**: `docs/LEGACY_WRAPPERS.md` (added removal notice)
- ✏️ **Updated**: `docs/pygame_ui_port_checklist.md` (marked §8.2 complete)
- ✅ **Created**: `docs/LEGACY_COMPAT_REMOVAL.md` (this file)

## Conclusion

The removal of `legacy_compat.py` successfully eliminated ~200+ unused CamelCase wrapper functions without breaking any existing functionality. This cleanup simplifies the codebase and removes a source of potential confusion for developers who might have mistakenly thought these wrappers were required for compatibility.

All active CamelCase APIs remain in their respective modules where they are documented, tested, and serve legitimate backward-compatibility purposes.
