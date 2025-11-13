"""
legacy_compat.py

Centralized compatibility layer for legacy CamelCase APIs.
This file exposes CamelCase function names as thin wrappers around the
canonical snake_case implementations. The goal is to centralize wrappers
so they can be removed or migrated cleanly during a larger refactor.

Only include trivial delegators here. More complex legacy functions should be
reviewed and ported carefully.
"""

from __future__ import annotations

from typing import Any

# Sprite API compatibility wrappers ------------------------------------------------


def GenerateTrain(context: Any, x: int, y: int) -> None:
    from src.micropolis import sprite_manager

    return sprite_manager.generate_train(context, x, y)


def GenerateBus(context: Any, x: int, y: int) -> None:
    from src.micropolis import sprite_manager

    return sprite_manager.generate_bus(context, x, y)


def GenerateShip(context: Any) -> None:
    from src.micropolis import sprite_manager

    return sprite_manager.generate_ship(context)


def GeneratePlane(context: Any, x: int, y: int) -> None:
    from src.micropolis import sprite_manager

    return sprite_manager.generate_plane(context, x, y)


def GenerateCopter(context: Any, x: int, y: int) -> None:
    from src.micropolis import sprite_manager

    return sprite_manager.generate_copter(context, x, y)


def MakeExplosion(context: Any, x: int, y: int) -> None:
    from src.micropolis import sprite_manager

    return sprite_manager.make_explosion(context, x, y)


def MakeExplosionAt(context: Any, x: int, y: int) -> None:
    from src.micropolis import sprite_manager

    return sprite_manager.make_explosion_at(context, x, y)


def GetSprite(context: Any, sprite_type: int) -> Any:
    from src.micropolis import sprite_manager

    return sprite_manager.get_sprite(context, sprite_type)


def MakeSprite(context: Any, sprite_type: int, x: int, y: int) -> Any:
    from src.micropolis import sprite_manager

    return sprite_manager.make_sprite(context, sprite_type, x, y)


# Update manager compatibility --------------------------------------------------
def DoUpdateHeads() -> None:
    from src.micropolis import updates

    return updates.DoUpdateHeads()


def UpdateEditors() -> None:
    from src.micropolis import updates

    return updates.UpdateEditors()


def UpdateMaps() -> None:
    from src.micropolis import updates

    return updates.UpdateMaps()


def UpdateGraphs() -> None:
    from src.micropolis import updates

    return updates.UpdateGraphs()


def UpdateEvaluation() -> None:
    from src.micropolis import updates

    return updates.UpdateEvaluation()


def UpdateHeads() -> None:
    from src.micropolis import updates

    return updates.UpdateHeads()


def UpdateFunds() -> None:
    from src.micropolis import updates

    return updates.UpdateFunds()


def ReallyUpdateFunds() -> None:
    from src.micropolis import updates

    return updates.ReallyUpdateFunds()


def doTimeStuff() -> None:
    from src.micropolis import updates

    return updates.doTimeStuff()


def updateDate() -> None:
    from src.micropolis import updates

    return updates.updateDate()


def showValves() -> None:
    from src.micropolis import updates

    return updates.showValves()


def drawValve() -> None:
    from src.micropolis import updates

    return updates.drawValve()


def SetDemand(r: float, c: float, i: float) -> None:
    from src.micropolis import updates

    return updates.SetDemand(r, c, i)


def updateOptions() -> None:
    from src.micropolis import updates

    return updates.updateOptions()


def UpdateOptionsMenu(options: int) -> None:
    from src.micropolis import updates

    return updates.UpdateOptionsMenu(options)


# View types compatibility (factory wrappers) ----------------------------------
def MakeNewInk() -> view_types.Ink:
    from src.micropolis import view_types

    return view_types.Ink()


def MakeNewXDisplay() -> view_types.XDisplay:
    from src.micropolis import view_types

    return view_types.XDisplay()


def MakeNewSimGraph() -> view_types.SimGraph:
    from src.micropolis import view_types

    return view_types.SimGraph()


def MakeNewSimDate() -> view_types.SimDate:
    from src.micropolis import view_types

    return view_types.SimDate()


def MakeNewPerson() -> view_types.Person:
    from src.micropolis import view_types

    return view_types.Person()


def MakeNewCmd() -> view_types.Cmd:
    from src.micropolis import view_types

    return view_types.Cmd()


def MakeNewSimExtended() -> view_types.SimExtended:
    from src.micropolis import view_types

    return view_types.SimExtended()


# Tools compatibility ----------------------------------------------------------
def MakeSound(context: Any, channel: str, sound_name: str) -> None:
    from src.micropolis import tools

    return tools.MakeSound(context, channel, sound_name)


# Small re-exports for other common legacy names: keep these minimal and
# add more later as we identify trivial wrappers across the codebase.

# Example: if other modules use a CamelCase name that is a trivial wrapper
# to a snake_case implementation, add it here to centralize compatibility.


# Printing compatibility wrappers -------------------------------------------


def PrintRect(context: Any, x: int, y: int, w: int, h: int) -> None:
    from src.micropolis import printing

    return printing.PrintRect(context, x, y, w, h)


def PrintHeader(context: Any, x: int, y: int, w: int, h: int) -> None:
    from src.micropolis import printing

    return printing.PrintHeader(context, x, y, w, h)


def PrintDefTile(context: Any, tile: int) -> None:
    from src.micropolis import printing

    return printing.PrintDefTile(context, tile)


def FirstRow(context: Any) -> None:
    from src.micropolis import printing

    return printing.FirstRow(context)


def PrintTile(context: Any, tile: int) -> None:
    from src.micropolis import printing

    return printing.PrintTile(context, tile)


def PrintNextRow(context: Any) -> None:
    from src.micropolis import printing

    return printing.PrintNextRow(context)


def PrintFinish(context: Any, x: int, y: int, w: int, h: int) -> None:
    from src.micropolis import printing

    return printing.PrintFinish(context, x, y, w, h)


def PrintTrailer(context: Any, x: int, y: int, w: int, h: int) -> None:
    from src.micropolis import printing

    return printing.PrintTrailer(context, x, y, w, h)


# Export the compatibility names. Keep this list in sync with functions above.
__all__ = [
    # sprite API
    "GenerateTrain",
    "GenerateBus",
    "GenerateShip",
    "GeneratePlane",
    "GenerateCopter",
    "MakeExplosion",
    "MakeExplosionAt",
    "GetSprite",
    "MakeSprite",
    # update manager
    "DoUpdateHeads",
    "UpdateEditors",
    "UpdateMaps",
    "UpdateGraphs",
    "UpdateEvaluation",
    "UpdateHeads",
    "UpdateFunds",
    "ReallyUpdateFunds",
    "doTimeStuff",
    "updateDate",
    "showValves",
    "drawValve",
    "SetDemand",
    "updateOptions",
    "UpdateOptionsMenu",
    # view factories
    "MakeNewInk",
    "MakeNewXDisplay",
    "MakeNewSimGraph",
    "MakeNewSimDate",
    "MakeNewPerson",
    "MakeNewCmd",
    "MakeNewSimExtended",
    # tools
    "MakeSound",
    # printing
    "PrintRect",
    "PrintHeader",
    "PrintDefTile",
    "FirstRow",
    "PrintTile",
    "PrintNextRow",
    "PrintFinish",
    "PrintTrailer",
]


# Random compatibility -------------------------------------------------------


def Rand(context: Any, range_val: int) -> int:
    from src.micropolis import random as _random

    return _random.Rand(context, range_val)


def RandInt(context: Any) -> int:
    from src.micropolis import random as _random

    return _random.RandInt(context)


def Rand16(context: Any) -> int:
    from src.micropolis import random as _random

    return _random.Rand16(context)


# Messages compatibility -----------------------------------------------------


def TickCount() -> int:
    from src.micropolis import messages

    return messages.tick_count()


def ClearMes(context: Any) -> None:
    from src.micropolis import messages

    return messages.clear_mes(context)


def SendMes(context: Any, mnum: int) -> int:
    from src.micropolis import messages

    return messages.send_mes(context, mnum)


def SendMesAt(context: Any, mnum: int, x: int, y: int) -> None:
    from src.micropolis import messages

    return messages.send_mes_at(context, mnum, x, y)


# Add message wrappers to exports for discoverability
__all__ += [
    "Rand",
    "RandInt",
    "Rand16",
    "TickCount",
    "ClearMes",
    "SendMes",
    "SendMesAt",
]


# Macros compatibility -------------------------------------------------------
def ABS(x: int) -> int:
    from src.micropolis import macros

    return macros.ABS(x)


def TestBounds(x: int, y: int) -> bool:
    from src.micropolis import macros

    return macros.TestBounds(x, y)


def TILE_IS_NUCLEAR(tile: int) -> bool:
    from src.micropolis import macros

    return macros.TILE_IS_NUCLEAR(tile)


def TILE_IS_VULNERABLE(tile: int) -> bool:
    from src.micropolis import macros

    return macros.TILE_IS_VULNERABLE(tile)


def TILE_IS_ARSONABLE(tile: int) -> bool:
    from src.micropolis import macros

    return macros.TILE_IS_ARSONABLE(tile)


def TILE_IS_RIVER_EDGE(tile: int) -> bool:
    from src.micropolis import macros

    return macros.TILE_IS_RIVER_EDGE(tile)


def TILE_IS_FLOODABLE(tile: int) -> bool:
    from src.micropolis import macros

    return macros.TILE_IS_FLOODABLE(tile)


def TILE_IS_RUBBLE(tile: int) -> bool:
    from src.micropolis import macros

    return macros.TILE_IS_RUBBLE(tile)


def TILE_IS_FLOODABLE2(tile: int) -> bool:
    from src.micropolis import macros

    return macros.TILE_IS_FLOODABLE2(tile)


# Map view compatibility ----------------------------------------------------
def GetCI(x: int) -> int:
    from src.micropolis import map_view

    return map_view.GetCI(x)


def MemDrawMap(context: Any, view: Any) -> None:
    from src.micropolis import map_view

    return map_view.MemDrawMap(context, view)


# Tools convenience wrappers (low-risk re-exports) --------------------------
def Spend(context: Any, amount: int) -> None:
    from src.micropolis import tools

    return tools.Spend(context, amount)


def DoTool(context: Any, view: Any, tool: int, x: int, y: int) -> None:
    from src.micropolis import tools

    return tools.DoTool(context, view, tool, x, y)


def DoPendTool(context: Any, view: Any, tool: int, x: int, y: int) -> None:
    from src.micropolis import tools

    return tools.DoPendTool(context, view, tool, x, y)


def NewInk() -> Any:
    from src.micropolis import tools

    return tools.NewInk()


def FreeInk(ink: Any) -> None:
    from src.micropolis import tools

    return tools.FreeInk(ink)


def StartInk(ink: Any, x: int, y: int) -> None:
    from src.micropolis import tools

    return tools.StartInk(ink, x, y)


def AddInk(ink: Any, x: int, y: int) -> None:
    from src.micropolis import tools

    return tools.AddInk(ink, x, y)


def DoShowZoneStatus(
    str_arg: str, s0: str, s1: str, s2: str, s3: str, s4: str, x: int, y: int
) -> None:
    from src.micropolis import tools

    return tools.DoShowZoneStatus(str_arg, s0, s1, s2, s3, s4, x, y)


def ToolDown(context: Any, view: Any, x: int, y: int) -> None:
    from src.micropolis import tools

    return tools.ToolDown(context, view, x, y)


def ToolUp(context: Any, view: Any, x: int, y: int) -> int:
    from src.micropolis import tools

    return tools.ToolUp(context, view, x, y)


def ToolDrag(context: Any, view: Any, px: int, py: int) -> int:
    from src.micropolis import tools

    return tools.ToolDrag(context, view, px, py)


# Export the new wrappers
__all__ += [
    # macros
    "ABS",
    "TestBounds",
    "TILE_IS_NUCLEAR",
    "TILE_IS_VULNERABLE",
    "TILE_IS_ARSONABLE",
    "TILE_IS_RIVER_EDGE",
    "TILE_IS_FLOODABLE",
    "TILE_IS_RUBBLE",
    "TILE_IS_FLOODABLE2",
    # map view
    "GetCI",
    "MemDrawMap",
    # tools
    "Spend",
    "DoTool",
    "DoPendTool",
    "NewInk",
    "FreeInk",
    "StartInk",
    "AddInk",
    "DoShowZoneStatus",
    "ToolDown",
    "ToolUp",
    "ToolDrag",
]


# More tools wrappers (delegators to src.micropolis.tools) -------------------
def MakeSoundOn(context: Any, view: Any, channel: str, sound_name: str) -> None:
    from src.micropolis import tools

    return tools.MakeSoundOn(context, view, channel, sound_name)


def ConnecTile(context: Any, x: int, y: int, tile_ptr: list[int], command: int) -> int:
    from src.micropolis import tools

    return tools.ConnecTile(context, x, y, tile_ptr, command)


def DidTool(context: Any, view: Any, name: str, x: int, y: int) -> None:
    from src.micropolis import tools

    return tools.DidTool(context, view, name, x, y)


def DoSetWandState(context: Any, view: Any, state: int) -> None:
    from src.micropolis import tools

    return tools.DoSetWandState(context, view, state)


def ChalkTool(context: Any, view: Any, x: int, y: int, color: int, first: int) -> int:
    from src.micropolis import tools

    return tools.ChalkTool(context, view, x, y, color, first)


def ChalkStart(context: Any, view: Any, x: int, y: int, color: int) -> None:
    from src.micropolis import tools

    return tools.ChalkStart(context, view, x, y, color)


def ChalkTo(view: Any, x: int, y: int) -> None:
    from src.micropolis import tools

    return tools.ChalkTo(view, x, y)


def EraserTool(context: Any, view: Any, x: int, y: int, first: int) -> int:
    from src.micropolis import tools

    return tools.EraserTool(context, view, x, y, first)


def EraserStart(view: Any, x: int, y: int) -> None:
    from src.micropolis import tools

    return tools.EraserStart(view, x, y)


def EraserTo(view: Any, x: int, y: int) -> None:
    from src.micropolis import tools

    return tools.EraserTo(view, x, y)


def InkInBox(ink: Any, left: int, top: int, right: int, bottom: int) -> bool:
    from src.micropolis import tools

    return tools.InkInBox(ink, left, top, right, bottom)


__all__ += [
    "MakeSoundOn",
    "ConnecTile",
    "DidTool",
    "DoSetWandState",
    "ChalkTool",
    "ChalkStart",
    "ChalkTo",
    "EraserTool",
    "EraserStart",
    "EraserTo",
    "InkInBox",
]


# Engine compatibility wrappers ----------------------------------------------
def SignalExitHandler(context: Any, signum: int, frame) -> None:
    from src.micropolis import engine

    return engine.SignalExitHandler(context, signum, frame)


def DoStopMicropolis(context: Any) -> None:
    from src.micropolis import engine

    return engine.DoStopMicropolis(context)


def InitFundingLevel(context: Any) -> None:
    from src.micropolis import engine

    return engine.InitFundingLevel(context)


def StopEarthquake(context: Any) -> None:
    # engine.StopEarthquake is defined as a no-arg function in the
    # engine module. Call it without passing the context to avoid
    # a signature mismatch.
    from src.micropolis import engine

    return engine.StopEarthquake()


def ResetMapState(context: Any) -> None:
    # The canonical implementation for resetting view state lives in
    # initialization.ResetMapState(context).
    from src.micropolis import initialization

    return initialization.ResetMapState(context)


def ResetEditorState(context: Any) -> None:
    # Delegate to the initialization module which provides the
    # context-aware ResetEditorState implementation.
    from src.micropolis import initialization

    return initialization.ResetEditorState(context)


def ClearMap(context: Any) -> None:
    # Map clearing is implemented in generation.ClearMap(context).
    from src.micropolis import generation

    return generation.ClearMap(context)


def SetFunds(context: Any, amount: int) -> None:
    # Use the stubs module's SetFunds which updates context.total_funds
    # and triggers UI updates.
    from src.micropolis import stubs

    return stubs.SetFunds(context, amount)


def SetGameLevelFunds(context: Any, level: int) -> None:
    from src.micropolis import engine

    return engine.SetGameLevelFunds(context, level)


def UpdateBudgetWindow() -> None:
    from src.micropolis import engine

    return engine.UpdateBudgetWindow()


def UpdateFlush() -> None:
    from src.micropolis import engine

    return engine.UpdateFlush()


def DoUpdateEditor(context: Any, view: Any) -> None:
    from src.micropolis import engine

    return engine.DoUpdateEditor(context, view)


def DoUpdateMap(view: Any) -> bool:
    from src.micropolis import engine

    return engine.DoUpdateMap(view)


def MoveObjects() -> None:
    from src.micropolis import engine

    return engine.MoveObjects()


def DoTimeoutListen() -> None:
    from src.micropolis import engine

    return engine.DoTimeoutListen()


__all__ += [
    # engine
    "SignalExitHandler",
    "DoStopMicropolis",
    "InitFundingLevel",
    "StopEarthquake",
    "ResetMapState",
    "ResetEditorState",
    "ClearMap",
    "SetFunds",
    "SetGameLevelFunds",
    "UpdateBudgetWindow",
    "UpdateFlush",
    "DoUpdateEditor",
    "DoUpdateHeads",
    "DoUpdateMap",
    "MoveObjects",
    "DoTimeoutListen",
]


# Initialization compatibility wrappers --------------------------------------
def RandomlySeedRand() -> None:
    from src.micropolis import initialization

    return initialization.RandomlySeedRand()


def InitGraphMax(context: Any) -> None:
    from src.micropolis import initialization

    return initialization.InitGraphMax(context)


def DestroyAllSprites(context: Any) -> None:
    from src.micropolis import initialization

    return initialization.DestroyAllSprites(context)


def ResetLastKeys() -> None:
    from src.micropolis import initialization

    return initialization.ResetLastKeys()


def DoNewGame(context: Any) -> None:
    from src.micropolis import initialization

    return initialization.DoNewGame(context)


def InitWillStuff(context: Any) -> None:
    from src.micropolis import initialization

    return initialization.InitWillStuff(context)


def InitializeSimulation(context: Any) -> bool:
    from src.micropolis import initialization

    return initialization.InitializeSimulation(context)


def InitGame(context: Any) -> None:
    from src.micropolis import initialization

    return initialization.InitGame(context)


def ResetSimulation(context: Any) -> None:
    from src.micropolis import initialization

    return initialization.ResetSimulation(context)


__all__ += [
    # initialization
    "RandomlySeedRand",
    "InitGraphMax",
    "DestroyAllSprites",
    "ResetLastKeys",
    "DoNewGame",
    "InitWillStuff",
    "InitializeSimulation",
    "InitGame",
    "ResetSimulation",
    # ResetMapState/ResetEditorState also exposed earlier via engine wrappers
]


# Generation compatibility wrappers -----------------------------------------
def GenerateNewCity(context: Any) -> None:
    from src.micropolis import generation

    return generation.GenerateNewCity(context)


def GenerateSomeCity(context: Any, r: int) -> None:
    from src.micropolis import generation

    return generation.GenerateSomeCity(context, r)


def ERand(limit: int) -> int:
    from src.micropolis import generation

    return generation.ERand(limit)


def GenerateMap(context: Any, r: int) -> None:
    from src.micropolis import generation

    return generation.GenerateMap(context, r)


def ClearUnnatural(context: Any) -> None:
    from src.micropolis import generation

    return generation.ClearUnnatural(context)


def MakeNakedIsland(context: Any) -> None:
    from src.micropolis import generation

    return generation.MakeNakedIsland(context)


def MakeIsland(context: Any) -> None:
    from src.micropolis import generation

    return generation.MakeIsland(context)


def MakeLakes(context: Any) -> None:
    from src.micropolis import generation

    return generation.MakeLakes(context)


def GetRandStart(context: Any) -> None:
    from src.micropolis import generation

    return generation.GetRandStart(context)


def MoveMap(context: Any, direction: int) -> None:
    from src.micropolis import generation

    return generation.MoveMap(context, direction)


def DoRivers(context: Any) -> None:
    from src.micropolis import generation

    return generation.DoRivers(context)


def DoBRiv(context: Any) -> None:
    from src.micropolis import generation

    return generation.DoBRiv(context)


def DoSRiv(context: Any) -> None:
    from src.micropolis import generation

    return generation.DoSRiv(context)


def PutOnMap(context: Any, Mchar: int, Xoff: int, Yoff: int) -> None:
    from src.micropolis import generation

    return generation.PutOnMap(context, Mchar, Xoff, Yoff)


def BRivPlop(context: Any) -> None:
    from src.micropolis import generation

    return generation.BRivPlop(context)


def SRivPlop(context: Any) -> None:
    from src.micropolis import generation

    return generation.SRivPlop(context)


def TreeSplash(context: Any, xloc: int, yloc: int) -> None:
    from src.micropolis import generation

    return generation.TreeSplash(context, xloc, yloc)


def DoTrees(context: Any) -> None:
    from src.micropolis import generation

    return generation.DoTrees(context)


def SmoothRiver(context: Any) -> None:
    from src.micropolis import generation

    return generation.SmoothRiver(context)


def IsTree(cell: int) -> bool:
    from src.micropolis import generation

    return generation.IsTree(cell)


def SmoothTrees(context: Any) -> None:
    from src.micropolis import generation

    return generation.SmoothTrees(context)


def SmoothWater(context: Any) -> None:
    from src.micropolis import generation

    return generation.SmoothWater(context)


__all__ += [
    # generation
    "GenerateNewCity",
    "GenerateSomeCity",
    "ERand",
    "GenerateMap",
    "ClearUnnatural",
    "MakeNakedIsland",
    "MakeIsland",
    "MakeLakes",
    "GetRandStart",
    "MoveMap",
    "DoRivers",
    "DoBRiv",
    "DoSRiv",
    "PutOnMap",
    "BRivPlop",
    "SRivPlop",
    "TreeSplash",
    "DoTrees",
    "SmoothRiver",
    "IsTree",
    "SmoothTrees",
    "SmoothWater",
]


# File I/O compatibility wrappers -------------------------------------------
def LoadScenario(context: Any, scenario_id: int) -> None:
    from src.micropolis import file_io

    return file_io.LoadScenario(context, scenario_id)


def LoadCity(context: Any, filename: str) -> int:
    from src.micropolis import file_io

    return file_io.LoadCity(context, filename)


def SaveCity(context: Any) -> None:
    from src.micropolis import file_io

    return file_io.SaveCity(context)


def DoSaveCityAs(context: Any) -> None:
    from src.micropolis import file_io

    return file_io.DoSaveCityAs(context)


def SaveCityAs(context: Any, filename: str) -> None:
    from src.micropolis import file_io

    return file_io.SaveCityAs(context, filename)


def DidLoadScenario(context: Any) -> None:
    from src.micropolis import file_io

    return file_io.DidLoadScenario(context)


def DidLoadCity(context: Any) -> None:
    from src.micropolis import file_io

    return file_io.DidLoadCity(context)


def DidntLoadCity(context: Any, msg: str) -> None:
    from src.micropolis import file_io

    return file_io.DidntLoadCity(context, msg)


def DidSaveCity(context: Any) -> None:
    from src.micropolis import file_io

    return file_io.DidSaveCity(context)


def DidntSaveCity(context: Any, msg: str) -> None:
    from src.micropolis import file_io

    return file_io.DidntSaveCity(context, msg)


__all__ += [
    # file I/O
    "LoadScenario",
    "LoadCity",
    "SaveCity",
    "DoSaveCityAs",
    "SaveCityAs",
    "DidLoadScenario",
    "DidLoadCity",
    "DidntLoadCity",
    "DidSaveCity",
    "DidntSaveCity",
]


# Power compatibility wrappers ----------------------------------------------
def DoPowerScan(context: Any) -> None:
    from src.micropolis import power

    return power.DoPowerScan(context)


def MoveMapSim(x: int, y: int, dir: int) -> tuple[int, int]:
    from src.micropolis import power

    return power.MoveMapSim(x, y, dir)


def TestForCond(context: Any, x: int, y: int) -> bool:
    from src.micropolis import power

    return power.TestForCond(context, x, y)


def SetPowerBit(context: Any, x: int, y: int) -> None:
    from src.micropolis import power

    return power.SetPowerBit(context, x, y)


def TestPowerBit(context: Any, x: int, y: int) -> bool:
    from src.micropolis import power

    return power.TestPowerBit(context, x, y)


def PushPowerStack(context: Any) -> None:
    from src.micropolis import power

    return power.PushPowerStack(context)


def ClearPowerBit(context: Any, x: int, y: int) -> None:
    from src.micropolis import power

    return power.ClearPowerBit(context, x, y)


__all__ += [
    # power
    "DoPowerScan",
    "MoveMapSim",
    "TestForCond",
    "SetPowerBit",
    "TestPowerBit",
    "PushPowerStack",
    "ClearPowerBit",
]


# Traffic compatibility wrappers -------------------------------------------
def MakeTraf(context: Any, x: int, y: int) -> None:
    from src.micropolis import traffic

    return traffic.MakeTraf(context, x, y)


def SetTrafMem(context: Any, x: int, y: int, val: int) -> None:
    from src.micropolis import traffic

    return traffic.SetTrafMem(context, x, y, val)


def PushPos(context: Any, x: int, y: int) -> None:
    from src.micropolis import traffic

    return traffic.PushPos(context, x, y)


def PullPos(context: Any) -> tuple[int, int]:
    from src.micropolis import traffic

    return traffic.PullPos(context)


def FindPRoad(context: Any, x: int, y: int) -> bool:
    from src.micropolis import traffic

    return traffic.FindPRoad(context, x, y)


def FindPTele(context: Any, x: int, y: int) -> bool:
    from src.micropolis import traffic

    return traffic.FindPTele(context, x, y)


def TryDrive(context: Any, sx: int, sy: int, ex: int, ey: int) -> bool:
    from src.micropolis import traffic

    return traffic.TryDrive(context, sx, sy, ex, ey)


def TryGo(context: Any, sx: int, sy: int, ex: int, ey: int) -> bool:
    from src.micropolis import traffic

    return traffic.TryGo(context, sx, sy, ex, ey)


def GetFromMap(context: Any, x: int, y: int) -> int:
    from src.micropolis import traffic

    return traffic.GetFromMap(context, x, y)


def DriveDone(context: Any) -> None:
    from src.micropolis import traffic

    return traffic.DriveDone(context)


def RoadTest(context: Any, x: int, y: int) -> bool:
    from src.micropolis import traffic

    return traffic.RoadTest(context, x, y)


def AverageTrf(context: Any) -> int:
    from src.micropolis import traffic

    return traffic.AverageTrf(context)


__all__ += [
    # traffic
    "MakeTraf",
    "SetTrafMem",
    "PushPos",
    "PullPos",
    "FindPRoad",
    "FindPTele",
    "TryDrive",
    "TryGo",
    "GetFromMap",
    "DriveDone",
    "RoadTest",
    "AverageTrf",
]


# Scanner compatibility wrappers -------------------------------------------
def FireAnalysis(context: Any) -> None:
    from src.micropolis import scanner

    return scanner.FireAnalysis(context)


def PopDenScan(context: Any) -> None:
    from src.micropolis import scanner

    return scanner.PopDenScan(context)


def GetPDen(context: Any, Ch9: int) -> int:
    from src.micropolis import scanner

    return scanner.GetPDen(context, Ch9)


def PTLScan(context: Any) -> None:
    from src.micropolis import scanner

    return scanner.PTLScan(context)


def GetPValue(loc: int) -> int:
    from src.micropolis import scanner

    return scanner.GetPValue(loc)


def GetDisCC(x: int, y: int) -> int:
    from src.micropolis import scanner

    return scanner.GetDisCC(x, y)


def CrimeScan(context: Any) -> None:
    from src.micropolis import scanner

    return scanner.CrimeScan(context)


def SmoothTerrain(context: Any) -> None:
    from src.micropolis import scanner

    return scanner.SmoothTerrain(context)


def DoSmooth(context: Any) -> None:
    from src.micropolis import scanner

    return scanner.DoSmooth(context)


def DoSmooth2(context: Any) -> None:
    from src.micropolis import scanner

    return scanner.DoSmooth2(context)


def ClrTemArray(context: Any) -> None:
    from src.micropolis import scanner

    return scanner.ClrTemArray(context)


def SmoothFSMap(context: Any) -> None:
    from src.micropolis import scanner

    return scanner.SmoothFSMap(context)


def SmoothPSMap(context: Any) -> None:
    from src.micropolis import scanner

    return scanner.SmoothPSMap(context)


def DistIntMarket(context: Any) -> None:
    from src.micropolis import scanner

    return scanner.DistIntMarket(context)


__all__ += [
    # scanner
    "FireAnalysis",
    "PopDenScan",
    "GetPDen",
    "PTLScan",
    "GetPValue",
    "GetDisCC",
    "CrimeScan",
    "SmoothTerrain",
    "DoSmooth",
    "DoSmooth2",
    "ClrTemArray",
    "SmoothFSMap",
    "SmoothPSMap",
    "DistIntMarket",
]
