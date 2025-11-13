"""
messages.py - In-game messages and notifications system for Micropolis Python port

This module implements the message system ported from s_msg.c,
providing in-game notifications, scenario messages, and UI communication.

The system handles:
- Informational messages (need residential, commercial zones, etc.)
- Problem alerts (pollution, crime, traffic)
- Scenario messages and win/lose conditions
- Sound effects for different message types
- Auto-goto functionality for location-based messages
- Message timing and display management

Ported from s_msg.c.
"""

import os
import time

from src.micropolis.context import AppContext
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # For type checkers only; avoid importing simulation at runtime to
    # prevent circular imports (simulation imports messages).
    from src.micropolis.simulation import rand
from src.micropolis.ui_utilities import eval_cmd_str


def load_message_strings(context: AppContext) -> None:
    """
    Load message strings from the stri.301 resource file.

    This reads the message strings that correspond to message numbers 1-60
    used throughout the game for notifications and alerts.
    """
    # global MESSAGE_STRINGS

    if context.MESSAGE_STRINGS:  # Already loaded
        return

    # Path to the message strings file
    stri_file = os.path.join(
        os.path.dirname(__file__), "..", "..", "assets", "stri.301"
    )

    try:
        with open(stri_file, "r", encoding="utf-8") as f:
            context.MESSAGE_STRINGS = [line.rstrip("\n") for line in f.readlines()]
    except FileNotFoundError:
        # Fallback: create empty strings if file not found
        context.MESSAGE_STRINGS = [""] * 61
        print(f"Warning: Could not load message strings from {stri_file}")


def get_message_string(context: AppContext, message_num: int) -> str:
    """
    Get a message string by message number.

    Args:
        message_num: Message number (1-60)

    Returns:
        The message string, or empty string if not found
        :param context:
    """
    if not context.MESSAGE_STRINGS:
        load_message_strings(context)

    if 1 <= message_num <= len(context.MESSAGE_STRINGS):
        return context.MESSAGE_STRINGS[message_num - 1]  # 1-indexed to 0-indexed
    return ""


def tick_count() -> int:
    """
    Get current tick count (milliseconds since epoch).

    This replaces the Macintosh TickCount() function.
    In the original, TickCount was used for timing message display.

    Returns:
        Current time in milliseconds
    """
    return int(time.time() * 1000)


def make_sound(context: AppContext, channel: str, sound_name: str) -> None:
    """
    Play a sound effect.

    Now uses the pygame audio system for actual sound playback.

    Args:
        channel: Sound channel (e.g., "city")
        sound_name: Name of the sound to play
        :param context:
    """
    # Minimal implementation: delegate to UI/audio subsystem lazily
    if not (context.sound and context.user_sound_on):
        return
    try:
        from src.micropolis.audio import play_sound

        play_sound(context, channel, sound_name)
    except Exception:
        # If audio backend isn't ready or circular imports occur, skip sound.
        return


def send_messages(context: AppContext) -> None:
    """
    Send messages based on current city conditions.

    Called from the simulation loop to check for various conditions
    that warrant displaying messages to the player.

    Ported from SendMessages() in s_msg.c.
    :param context:
    """
    if context.scenario_id and context.score_type and context.score_wait:
        context.score_wait -= 1
        if not context.score_wait:
            do_scenario_score(context, context.score_type)

    check_growth(context)

    total_z_pop = context.res_z_pop + context.com_z_pop + context.ind_z_pop
    power_pop = context.nuclear_pop + context.coal_pop

    z = context.city_time & 63

    # Check various conditions based on city time
    if z == 1:
        if (total_z_pop >> 2) >= context.res_z_pop:
            send_mes(context, 1)  # need Res
    elif z == 5:
        if (total_z_pop >> 3) >= context.com_z_pop:
            send_mes(context, 2)  # need Com
    elif z == 10:
        if (total_z_pop >> 3) >= context.ind_z_pop:
            send_mes(context, 3)  # need Ind
    elif z == 14:
        if (total_z_pop > 10) and ((total_z_pop << 1) > context.road_total):
            send_mes(context, 4)  # need roads
    elif z == 18:
        if (total_z_pop > 50) and (total_z_pop > context.rail_total):
            send_mes(context, 5)  # need rail
    elif z == 22:
        if (total_z_pop > 10) and (power_pop == 0):
            send_mes(context, 6)  # need Power
    elif z == 26:
        if (context.res_pop > 500) and (context.stadium_pop == 0):
            send_mes(context, 7)  # need Stad
            context.res_cap = 1
        else:
            context.res_cap = 0
    elif z == 28:
        if (context.ind_pop > 70) and (context.port_pop == 0):
            send_mes(context, 8)  # need Seaport
            context.ind_cap = 1
        else:
            context.ind_cap = 0
    elif z == 30:
        if (context.com_pop > 100) and (context.airport_pop == 0):
            send_mes(context, 9)  # need Airport
            context.com_cap = 1
        else:
            context.com_cap = 0
    elif z == 32:
        # dec score for unpowered zones
        tm = context.un_pwrd_z_cnt + context.pwrd_z_cnt
        if tm:
            if (context.pwrd_z_cnt / tm) < 0.7:
                send_mes(context, 15)  # brownouts
    elif z == 35:
        if context.pollute_average > 60:  # Note: was 80, but adjusted for gameplay
            send_mes(context, -10)  # pollution alert
    elif z == 42:
        if context.crime_average > 100:
            send_mes(context, -11)  # crime alert
    elif z == 45:
        if (context.total_pop > 60) and (context.fire_st_pop == 0):
            send_mes(context, 13)  # need fire station
    elif z == 48:
        if (context.total_pop > 60) and (context.police_pop == 0):
            send_mes(context, 14)  # need police station
    elif z == 51:
        if context.city_tax > 12:
            send_mes(context, 16)  # high taxes
    elif z == 54:
        if (context.road_effect < 20) and (context.road_total > 30):
            send_mes(context, 17)  # road deterioration
    elif z == 57:
        if (context.fire_effect < 700) and (context.total_pop > 20):
            send_mes(context, 18)  # fire funding needed
    elif z == 60:
        if (context.police_effect < 700) and (context.total_pop > 20):
            send_mes(context, 19)  # police funding needed
    elif z == 63:
        if context.traffic_average > 60:
            send_mes(context, -12)  # traffic jam


def check_growth(context: AppContext) -> None:
    """
    Check for population growth milestones and send appropriate messages.

    Tracks when the city reaches certain population thresholds
    and sends congratulatory messages.

    Ported from CheckGrowth() in s_msg.c.
    :param context:
    """
    if not (context.city_time & 3):
        z = 0
        this_city_pop = (
            context.res_pop + (context.com_pop * 8) + (context.ind_pop * 8)
        ) * 20

        if context.last_city_pop:
            if (context.last_city_pop < 2000) and (this_city_pop >= 2000):
                z = 35  # Town
            elif (context.last_city_pop < 10000) and (this_city_pop >= 10000):
                z = 36  # City
            elif (context.last_city_pop < 50000) and (this_city_pop >= 50000):
                z = 37  # Capital
            elif (context.last_city_pop < 100000) and (this_city_pop >= 100000):
                z = 38  # Metropolis
            elif (context.last_city_pop < 500000) and (this_city_pop >= 500000):
                z = 39  # Megalopolis

        if z and (z != context.last_category):
            send_mes(context, -z)  # Negative for picture messages
            context.last_category = z

        context.last_city_pop = this_city_pop


def do_scenario_score(context: AppContext, type_val: int) -> None:
    """
    Handle scenario scoring and win/lose conditions.

    Args:
        type_val: Scenario type identifier

    Ported from DoScenarioScore() in s_msg.c.
    :param context:
    """
    z = -200  # you lose

    if type_val == 1:  # Dullsville
        if context.city_class >= 4:
            z = -100  # you win
    elif type_val == 2:  # San Francisco
        if context.city_class >= 4:
            z = -100
    elif type_val == 3:  # Hamburg
        if context.city_class >= 4:
            z = -100
    elif type_val == 4:  # Bern
        if context.traffic_average < 80:
            z = -100
    elif type_val == 5:  # Tokyo
        if context.city_score > 500:
            z = -100
    elif type_val == 6:  # Detroit
        if context.crime_average < 60:
            z = -100
    elif type_val == 7:  # Boston
        if context.city_score > 500:
            z = -100
    elif type_val == 8:  # Rio de Janeiro
        if context.city_score > 500:
            z = -100

    clear_mes(context)
    send_mes(context, z)

    if z == -200:
        do_lose_game(context)


def clear_mes(context: AppContext) -> None:
    """
    Clear message state.

    Resets message port and coordinates.

    Ported from ClearMes() in s_msg.c.
    :param context:
    """
    context.message_port = 0
    context.mes_x = 0
    context.mes_y = 0
    context.last_pic_num = 0


def send_mes(context: AppContext, mnum: int) -> int:
    """
    Send a message.

    Args:
        mnum: Message number (positive for text, negative for pictures)

    Returns:
        1 if message was sent, 0 if not

    Ported from SendMes() in s_msg.c.
    :param context:
    """
    if mnum < 0:
        if mnum != context.last_pic_num:
            context.message_port = mnum
            context.mes_x = 0
            context.mes_y = 0
            context.last_pic_num = mnum
            return 1
    else:
        if not context.message_port:
            context.message_port = mnum
            context.mes_x = 0
            context.mes_y = 0
            return 1
    return 0


def send_mes_at(context: AppContext, mnum: int, x: int, y: int) -> None:
    """
    Send a message at a specific location.

    Args:
        mnum: Message number
        x: X coordinate
        y: Y coordinate

    Ported from SendMesAt() in s_msg.c.
    :param context:
    """
    if send_mes(context, mnum):
        context.mes_x = x
        context.mes_y = y


def do_message(context: AppContext) -> None:
    """
    Main message processing function.

    Handles displaying messages, playing sounds, and managing message timing.
    This is called regularly to update the message display.

    Ported from doMessage() in s_msg.c.
    :param context:
    """
    message_str = ""
    pict_id = 0
    first_time = False

    if context.message_port:
        context.mes_num = context.message_port
        context.message_port = 0
        context.last_mes_time = tick_count()
        first_time = True
    else:
        first_time = False
        if context.mes_num == 0:
            return
        if context.mes_num < 0:
            context.mes_num = -context.mes_num
            context.last_mes_time = tick_count()
        elif (tick_count() - context.last_mes_time) > (
            60 * 30 * 1000
        ):  # 30 minutes in ms
            context.mes_num = 0
            return

    if first_time:
        # Play sound effects based on message type
        abs_mes_num = abs(context.mes_num)
        if abs_mes_num == 12:
            # avoid importing simulation at module import time
            from src.micropolis.simulation import rand

            if rand(context, 5) == 1:
                make_sound(context, "city", "HonkHonk-Med")
            elif rand(context, 5) == 1:
                make_sound(context, "city", "HonkHonk-Low")
            elif rand(context, 5) == 1:
                make_sound(context, "city", "HonkHonk-High")
        elif abs_mes_num in (11, 20, 22, 23, 24, 25, 26, 27):
            make_sound(context, "city", "Siren")
        elif abs_mes_num == 21:
            make_sound(context, "city", f"Monster -speed {monster_speed(context)}")
        elif abs_mes_num == 30:
            make_sound(context, "city", "Explosion-Low")
            make_sound(context, "city", "Siren")
        elif abs_mes_num == 43:
            make_sound(context, "city", "Explosion-High")
            make_sound(context, "city", "Explosion-Low")
            make_sound(context, "city", "Siren")
        elif abs_mes_num == 44:
            make_sound(context, "city", "Siren")

    if context.mes_num >= 0:
        if context.mes_num == 0:
            return

        if context.mes_num > 60:
            context.mes_num = 0
            return

        message_str = get_message_string(context, context.mes_num)

        if context.mes_x or context.mes_y:
            # TODO: draw goto button
            pass

        if context.auto_go and (context.mes_x or context.mes_y):
            do_auto_goto(context, context.mes_x, context.mes_y, message_str)
            context.mes_x = 0
            context.mes_y = 0
        else:
            set_message_field(context, message_str)

    else:  # picture message
        pict_id = -context.mes_num

        if pict_id < 43:
            message_str = get_message_string(context, pict_id)
        else:
            message_str = ""

        do_show_picture(context, pict_id)

        context.message_port = pict_id  # resend text message

        if context.auto_go and (context.mes_x or context.mes_y):
            do_auto_goto(context, context.mes_x, context.mes_y, message_str)
            context.mes_x = 0
            context.mes_y = 0


def do_auto_goto(context: AppContext, x: int, y: int, msg: str) -> None:
    """
    Automatically go to a location when a message is displayed.

    Args:
        x: X coordinate
        y: Y coordinate
        msg: Message text

    Ported from DoAutoGoto() in s_msg.c.
    :param context:
    """
    set_message_field(context, msg)
    cmd = f"UIAutoGoto {x} {y}"
    eval_cmd_str(context, cmd)


def set_message_field(context: AppContext, msg: str) -> None:
    """
    Set the message field in the UI.

    Args:
        msg: Message text to display

    Ported from SetMessageField() in s_msg.c.
    :param context:
    """
    # global HaveLastMessage, LastMessage

    # if not hasattr(types, "HaveLastMessage"):
    #     context.have_last_message = 0
    #     context.last_message = ""

    if not context.have_last_message or context.last_message != msg:
        context.last_message = msg
        context.have_last_message = True
        cmd = f"UISetMessage {{{msg}}}"
        eval_cmd_str(context, cmd)


def do_show_picture(context: AppContext, pict_id: int) -> None:
    """
    Show a picture/message dialog.

    Args:
        pict_id: Picture/message identifier

    Ported from DoShowPicture() in s_msg.c.
    :param context:
    """
    cmd = f"UIShowPicture {pict_id}"
    eval_cmd_str(context, cmd)


def do_lose_game(context: AppContext) -> None:
    """
    Handle game loss scenario.

    Ported from DoLoseGame() in s_msg.c.
    :param context:
    """
    eval_cmd_str(context, "UILoseGame")


def do_win_game(context: AppContext) -> None:
    """
    Handle game win scenario.

    Ported from DoWinGame() in s_msg.c.
    :param context:
    """
    eval_cmd_str(context, "UIWinGame")


def monster_speed(context: AppContext) -> int:
    """
    Calculate monster movement speed.

    Returns:
        Speed value for monster sprite

    Ported from MonsterSpeed() in s_msg.c.
    """
    from src.micropolis.simulation import rand

    return rand(context, 40) + 70
