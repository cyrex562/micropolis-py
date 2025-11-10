"""
keyboard.py - Keyboard input handling for Micropolis Python port
"""

# Import simulation modules
from . import types, tools, disasters, messages, sim_control


# ============================================================================
# Global State
# ============================================================================

# Last 4 keys pressed buffer (plus null terminator)
LastKeys: str = "    "


# ============================================================================
# Keyboard Functions
# ============================================================================

def reset_last_keys() -> None:
    """
    Reset the last keys buffer.

    Ported from ResetLastKeys() in w_keys.c.
    """
    global LastKeys
    LastKeys = "    "
    types.PunishCnt = 0


def do_key_down(view: 'types.SimView', char_code: str) -> None:
    """
    Handle key down events.

    Ported from doKeyDown() in w_keys.c.
    Processes cheat codes and tool switching.

    Args:
        view: View that received the key event
        char_code: Character code of the pressed key
    """
    global LastKeys

    # Shift the last keys buffer
    LastKeys = LastKeys[1:] + char_code.lower()

    # Check for cheat codes
    if LastKeys == "fund":
        tools.Spend(-10000)
        types.PunishCnt += 1  # punish for cheating
        if types.PunishCnt == 5:
            types.PunishCnt = 0
            disasters.MakeEarthquake()
        LastKeys = ""
        return

    elif LastKeys == "fart":
        messages.make_sound("city", "Explosion-High")
        messages.make_sound("city", "Explosion-Low")
        disasters.MakeFire()
        disasters.MakeFlood()
        disasters.MakeTornado()
        disasters.MakeEarthquake()
        disasters.MakeMonster()
        LastKeys = ""
        return

    elif LastKeys == "nuke":
        messages.make_sound("city", "Explosion-High")
        messages.make_sound("city", "Explosion-Low")
        for i in range(types.WORLD_X):
            for j in range(types.WORLD_Y):
                tile = types.Map[i][j] & types.LOMASK
                if ((tile >= types.RUBBLE) and
                    ((tile < types.CHURCH - 4) or
                     (tile > types.CHURCH + 4))):
                    if ((tile >= types.HBRIDGE and tile <= types.VBRIDGE) or
                        (tile >= types.BRWH and tile <= types.LTRFBASE + 1) or
                        (tile >= types.BRWV and tile <= types.BRWV + 2) or
                        (tile >= types.BRWXXX1 and tile <= types.BRWXXX1 + 2) or
                        (tile >= types.BRWXXX2 and tile <= types.BRWXXX2 + 2) or
                        (tile >= types.BRWXXX3 and tile <= types.BRWXXX3 + 2) or
                        (tile >= types.BRWXXX4 and tile <= types.BRWXXX4 + 2) or
                        (tile >= types.BRWXXX5 and tile <= types.BRWXXX5 + 2) or
                        (tile >= types.BRWXXX6 and tile <= types.BRWXXX6 + 2) or
                        (tile >= types.BRWXXX7 and tile <= types.BRWXXX7 + 2)):
                        types.Map[i][j] = types.RIVER
                    else:
                        types.Map[i][j] = types.TINYEXP + types.ANIMBIT + types.BULLBIT + types.Rand(2)
        LastKeys = ""
        return

    elif LastKeys == "stop":
        sim_control.set_heat_steps(0)
        LastKeys = ""
        types.Kick()
        return

    elif LastKeys == "will":
        # Copy the map so external references (e.g., tests) can observe changes.
        types.Map = [row[:] for row in types.Map]
        n = 500
        for _ in range(n):
            try:
                x1 = types.Rand(types.WORLD_X - 1)
                y1 = types.Rand(types.WORLD_Y - 1)
                x2 = types.Rand(types.WORLD_X - 1)
                y2 = types.Rand(types.WORLD_Y - 1)
            except StopIteration:
                break

            temp = types.Map[x1][y1]
            types.Map[x1][y1] = types.Map[x2][y2]
            types.Map[x2][y2] = temp
        types.Kick()
        LastKeys = ""
        return

    elif LastKeys == "bobo":
        sim_control.set_heat_steps(1)
        sim_control.set_heat_flow(-1)
        sim_control.set_heat_rule(0)
        LastKeys = ""
        types.Kick()
        return

    elif LastKeys == "boss":
        sim_control.set_heat_steps(1)
        sim_control.set_heat_flow(1)
        sim_control.set_heat_rule(0)
        LastKeys = ""
        types.Kick()
        return

    elif LastKeys == "mack":
        sim_control.set_heat_steps(1)
        sim_control.set_heat_flow(0)
        sim_control.set_heat_rule(0)
        LastKeys = ""
        types.Kick()
        return

    elif LastKeys == "donh":
        sim_control.set_heat_steps(1)
        sim_control.set_heat_flow(-1)
        sim_control.set_heat_rule(1)
        LastKeys = ""
        types.Kick()
        return

    elif LastKeys == "patb":
        sim_control.set_heat_steps(1)
        sim_control.set_heat_flow(types.Rand(40) - 20)
        sim_control.set_heat_rule(0)
        LastKeys = ""
        types.Kick()
        return

    elif LastKeys == "lucb":
        sim_control.set_heat_steps(1)
        sim_control.set_heat_flow(types.Rand(1000) - 500)
        sim_control.set_heat_rule(0)
        LastKeys = ""
        types.Kick()
        return

    elif LastKeys == "olpc":
        tools.Spend(-1000000)
        return

    # Handle tool switching keys
    if char_code.upper() == 'X':
        # Cycle to next tool
        s = view.tool_state
        s += 1
        if s > tools.lastState:
            s = tools.firstState
        tools.setWandState(view, s)

    elif char_code.upper() == 'Z':
        # Cycle to previous tool
        s = view.tool_state
        s -= 1
        if s < tools.firstState:
            s = tools.lastState
        tools.setWandState(view, s)

    elif char_code.upper() == 'B' or char_code == chr(ord('B') - ord('@')):
        # Switch to bulldozer
        if view.tool_state_save == -1:
            view.tool_state_save = view.tool_state
        tools.setWandState(view, tools.dozeState)

    elif char_code.upper() == 'R' or char_code == chr(ord('R') - ord('@')):
        # Switch to roads
        if view.tool_state_save == -1:
            view.tool_state_save = view.tool_state
        tools.setWandState(view, tools.roadState)

    elif char_code.upper() == 'P' or char_code == chr(ord('P') - ord('@')):
        # Switch to power
        if view.tool_state_save == -1:
            view.tool_state_save = view.tool_state
        tools.setWandState(view, tools.wireState)

    elif char_code.upper() == 'T' or char_code == chr(ord('T') - ord('@')):
        # Switch to transit (rail)
        if view.tool_state_save == -1:
            view.tool_state_save = view.tool_state
        tools.setWandState(view, tools.rrState)

    elif char_code == chr(27):  # ESC key
        # Turn off sound
        types.Eval("UISoundOff")
        types.Dozing = 0


def do_key_up(view: 'types.SimView', char_code: str) -> None:
    """
    Handle key up events.

    Ported from doKeyUp() in w_keys.c.
    Restores previous tool state when modifier keys are released.

    Args:
        view: View that received the key event
        char_code: Character code of the released key
    """
    # Check if this is a tool modifier key being released
    if (char_code.lower() in ['b', 'r', 'p', 't'] or
        char_code == chr(ord('B') - ord('@')) or
        char_code == chr(ord('R') - ord('@')) or
        char_code == chr(ord('P') - ord('@')) or
        char_code == chr(ord('T') - ord('@')) or
        char_code.lower() in ['q'] or
        char_code == chr(ord('Q') - ord('@'))):

        if view.tool_state_save != -1:
            tools.setWandState(view, view.tool_state_save)
            view.tool_state_save = -1


# ============================================================================
# TCL Command Interface
# ============================================================================

class KeyboardCommand:
    """
    TCL command interface for keyboard functions.

    Provides TCL commands for keyboard input handling.
    """

    @staticmethod
    def handle_command(command: str, *args: str) -> str:
        """
        Handle TCL keyboard commands.

        Args:
            command: TCL command name
            *args: Command arguments

        Returns:
            TCL command result
        """
        if command == "resetlastkeys":
            if len(args) != 0:
                raise ValueError("Usage: resetlastkeys")
            reset_last_keys()
            return ""

        elif command == "getlastkeys":
            if len(args) != 0:
                raise ValueError("Usage: getlastkeys")
            return get_last_keys()

        else:
            raise ValueError(f"Unknown keyboard command: {command}")


# ============================================================================
# Utility Functions
# ============================================================================

def get_last_keys() -> str:
    """
    Get the current last keys buffer.

    Returns:
        Last 4 keys pressed as string
    """
    return LastKeys.strip()
