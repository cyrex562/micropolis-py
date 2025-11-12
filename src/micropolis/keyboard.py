"""
keyboard.py - Keyboard input handling for Micropolis Python port
"""
from src.micropolis.audio import make_sound
from src.micropolis.constants import WORLD_Y, WORLD_X, LOMASK, RUBBLE, CHURCH, HBRIDGE, VBRIDGE, BRWH, LTRFBASE, BRWV, \
    BRWXXX1, BRWXXX2, BRWXXX3, BRWXXX4, BRWXXX5, BRWXXX6, BRWXXX7, RIVER, TINYEXP, ANIMBIT, BULLBIT
from src.micropolis.context import AppContext
from src.micropolis.disasters import trigger_earthquake_disaster, create_fire_disaster, start_flood_disaster, spawn_tornado_disaster, spawn_monster_disaster
from src.micropolis.sim_control import set_heat_steps, set_heat_flow, set_heat_rule
from src.micropolis.sim_view import SimView
from src.micropolis.simulation import rand
from src.micropolis.tools import Spend, setWandState
from src.micropolis.ui_utilities import kick, eval_cmd_str


# Import simulation modules



# ============================================================================
# Global State
# ============================================================================

# Last 4 keys pressed buffer (plus null terminator)
# last_keys: str = "    "


# ============================================================================
# Keyboard Functions
# ============================================================================


def reset_last_keys(context: AppContext) -> None:
    """
    Reset the last keys buffer.

    Ported from ResetLastKeys() in w_keys.c.
    :param context: 
    """
    # global last_keys
    context.last_keys = "    "
    context.punish_cnt = 0


def do_key_down(context: AppContext, view: SimView, char_code: str) -> None:
    """
    Handle key down events.

    Ported from doKeyDown() in w_keys.c.
    Processes cheat codes and tool switching.

    Args:
        view: View that received the key event
        char_code: Character code of the pressed key
        :param context: 
    """
    # global LastKeys

    # Shift the last keys buffer
    context.last_keys = context.last_keys[1:] + char_code.lower()

    # Check for cheat codes
    if context.last_keys == "fund":
        Spend(-10000)
        context.punish_cnt += 1  # punish for cheating
        if context.punish_cnt == 5:
            context.punish_cnt = 0
            trigger_earthquake_disaster(context)
        context.last_keys = ""
        return

    elif context.last_keys == "fart":
        make_sound(context, "city", "Explosion-High")
        make_sound(context, "city", "Explosion-Low")
        create_fire_disaster(context)
        start_flood_disaster(context)
        spawn_tornado_disaster()
        trigger_earthquake_disaster(context)
        spawn_monster_disaster(context)
        context.last_keys = ""
        return

    elif context.last_keys == "nuke":
        make_sound(context,"city", "Explosion-High")
        make_sound(context, "city", "Explosion-Low")
        for i in range(WORLD_X):
            for j in range(WORLD_Y):
                tile = context.map_data[i][j] & LOMASK
                if (tile >= RUBBLE) and (
                    (tile < CHURCH - 4) or (tile > CHURCH + 4)
                ):
                    if (
                        (HBRIDGE <= tile <= VBRIDGE)
                        or (BRWH <= tile <= LTRFBASE + 1)
                        or (BRWV <= tile <= BRWV + 2)
                        or (BRWXXX1 <= tile <= BRWXXX1 + 2)
                        or (BRWXXX2 <= tile <= BRWXXX2 + 2)
                        or (BRWXXX3 <= tile <= BRWXXX3 + 2)
                        or (BRWXXX4 <= tile <= BRWXXX4 + 2)
                        or (BRWXXX5 <= tile <= BRWXXX5 + 2)
                        or (BRWXXX6 <= tile <= BRWXXX6 + 2)
                        or (BRWXXX7 <= tile <= BRWXXX7 + 2)
                    ):
                        context.map_data[i][j] = RIVER
                    else:
                        context.map_data[i][j] = (
                                TINYEXP
                                + ANIMBIT
                                + BULLBIT
                                + rand(context, 2)
                        )
        context.last_keys = ""
        return

    elif context.last_keys == "stop":
        set_heat_steps(context, 0)
        context.last_keys = ""
        kick(context)
        return

    elif context.last_keys == "will":
        # Copy the map so external references (e.g., tests) can observe changes.
        context.map_data = [row[:] for row in context.map_data]
        n = 500
        for _ in range(n):
            try:
                x1 = rand(context, WORLD_X - 1)
                y1 = rand(context, WORLD_Y - 1)
                x2 = rand(context, WORLD_X - 1)
                y2 = rand(context, WORLD_Y - 1)
            except StopIteration:
                break

            temp = context.map_data[x1][y1]
            context.map_data[x1][y1] = context.map_data[x2][y2]
            context.map_data[x2][y2] = temp
        kick(context)
        context.last_keys = ""
        return

    elif context.last_keys == "bobo":
        set_heat_steps(context, 1)
        set_heat_flow(context, -1)
        set_heat_rule(context, 0)
        context.last_keys = ""
        kick(context)
        return

    elif context.last_keys == "boss":
        set_heat_steps(context, 1)
        set_heat_flow(context, 1)
        set_heat_rule(context, 0)
        context.last_keys = ""
        kick(context)
        return

    elif context.last_keys == "mack":
        set_heat_steps(context, 1)
        set_heat_flow(context, 0)
        set_heat_rule(context, 0)
        context.last_keys = ""
        kick(context)
        return

    elif context.last_keys == "donh":
        set_heat_steps(context, 1)
        set_heat_flow(context, -1)
        set_heat_rule(context, 1)
        context.last_keys = ""
        kick(context)
        return

    elif context.last_keys == "patb":
        set_heat_steps(context, 1)
        set_heat_flow(context, rand(context, 40) - 20)
        set_heat_rule(context, 0)
        context.last_keys = ""
        kick(context)
        return

    elif context.last_keys == "lucb":
        set_heat_steps(context, 1)
        set_heat_flow(context, rand(context, 1000) - 500)
        set_heat_rule(context, 0)
        context.last_keys = ""
        kick(context)
        return

    elif context.last_keys == "olpc":
        Spend(-1000000)
        return

    # Handle tool switching keys
    if char_code.upper() == "X":
        # Cycle to next tool
        s = view.tool_state
        s += 1
        if s > context.lastState:
            s = context.firstState
        setWandState(view, s)

    elif char_code.upper() == "Z":
        # Cycle to previous tool
        s = view.tool_state
        s -= 1
        if s < context.firstState:
            s = context.lastState
        setWandState(view, s)

    elif char_code.upper() == "B" or char_code == chr(ord("B") - ord("@")):
        # Switch to bulldozer
        if view.tool_state_save == -1:
            view.tool_state_save = view.tool_state
        setWandState(view, context.dozeState)

    elif char_code.upper() == "R" or char_code == chr(ord("R") - ord("@")):
        # Switch to roads
        if view.tool_state_save == -1:
            view.tool_state_save = view.tool_state
        setWandState(view, context.roadState)

    elif char_code.upper() == "P" or char_code == chr(ord("P") - ord("@")):
        # Switch to power
        if view.tool_state_save == -1:
            view.tool_state_save = view.tool_state
        setWandState(view, context.wireState)

    elif char_code.upper() == "T" or char_code == chr(ord("T") - ord("@")):
        # Switch to transit (rail)
        if view.tool_state_save == -1:
            view.tool_state_save = view.tool_state
        setWandState(view, context.rrState)

    elif char_code == chr(27):  # ESC key
        # Turn off sound
        eval_cmd_str(context, "UISoundOff")
        context.dozing = 0


def do_key_up(view: "SimView", char_code: str) -> None:
    """
    Handle key up events.

    Ported from doKeyUp() in w_keys.c.
    Restores previous tool state when modifier keys are released.

    Args:
        view: View that received the key event
        char_code: Character code of the released key
    """
    # Check if this is a tool modifier key being released
    if (
        char_code.lower() in ["b", "r", "p", "t"]
        or char_code == chr(ord("B") - ord("@"))
        or char_code == chr(ord("R") - ord("@"))
        or char_code == chr(ord("P") - ord("@"))
        or char_code == chr(ord("T") - ord("@"))
        or char_code.lower() in ["q"]
        or char_code == chr(ord("Q") - ord("@"))
    ):
        if view.tool_state_save != -1:
            setWandState(view, view.tool_state_save)
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
    def handle_command(context: AppContext, command: str, *args: str) -> str:
        """
        Handle TCL keyboard commands.

        Args:
            command: TCL command name
            *args: Command arguments

        Returns:
            TCL command result
            :param context:
        """
        if command == "resetlastkeys":
            if len(args) != 0:
                raise ValueError("Usage: resetlastkeys")
            reset_last_keys(context)
            return ""

        elif command == "getlastkeys":
            if len(args) != 0:
                raise ValueError("Usage: getlastkeys")
            return get_last_keys(context)

        else:
            raise ValueError(f"Unknown keyboard command: {command}")


# ============================================================================
# Utility Functions
# ============================================================================


def get_last_keys(context: AppContext) -> str:
    """
    Get the current last keys buffer.

    Returns:
        Last 4 keys pressed as string
        :param context:
    """
    return context.last_keys.strip()
