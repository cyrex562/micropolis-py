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

import time
import os
from typing import Optional

from . import types
from . import random


# Message strings loaded from stri.301 file
MESSAGE_STRINGS: list[str] = []


def load_message_strings() -> None:
    """
    Load message strings from the stri.301 resource file.

    This reads the message strings that correspond to message numbers 1-60
    used throughout the game for notifications and alerts.
    """
    global MESSAGE_STRINGS

    if MESSAGE_STRINGS:  # Already loaded
        return

    # Path to the message strings file
    stri_file = os.path.join(os.path.dirname(__file__), '..', '..', 'res', 'stri.301')

    try:
        with open(stri_file, 'r', encoding='utf-8') as f:
            MESSAGE_STRINGS = [line.rstrip('\n') for line in f.readlines()]
    except FileNotFoundError:
        # Fallback: create empty strings if file not found
        MESSAGE_STRINGS = [''] * 61
        print(f"Warning: Could not load message strings from {stri_file}")


def get_message_string(message_num: int) -> str:
    """
    Get a message string by message number.

    Args:
        message_num: Message number (1-60)

    Returns:
        The message string, or empty string if not found
    """
    if not MESSAGE_STRINGS:
        load_message_strings()

    if 1 <= message_num <= len(MESSAGE_STRINGS):
        return MESSAGE_STRINGS[message_num - 1]  # 1-indexed to 0-indexed
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


def make_sound(channel: str, sound_name: str) -> None:
    """
    Play a sound effect.

    Now uses the pygame audio system for actual sound playback.

    Args:
        channel: Sound channel (e.g., "city")
        sound_name: Name of the sound to play
    """
    # Import audio module here to avoid circular imports
    from . import audio

    if types.Sound and types.UserSoundOn:
        audio.make_sound(channel, sound_name)


def send_messages() -> None:
    """
    Send messages based on current city conditions.

    Called from the simulation loop to check for various conditions
    that warrant displaying messages to the player.

    Ported from SendMessages() in s_msg.c.
    """
    if types.ScenarioID and types.ScoreType and types.ScoreWait:
        types.ScoreWait -= 1
        if not types.ScoreWait:
            do_scenario_score(types.ScoreType)

    check_growth()

    total_z_pop = types.ResZPop + types.ComZPop + types.IndZPop
    power_pop = types.NuclearPop + types.CoalPop

    z = types.CityTime & 63

    # Check various conditions based on city time
    if z == 1:
        if (total_z_pop >> 2) >= types.ResZPop:
            send_mes(1)  # need Res
    elif z == 5:
        if (total_z_pop >> 3) >= types.ComZPop:
            send_mes(2)  # need Com
    elif z == 10:
        if (total_z_pop >> 3) >= types.IndZPop:
            send_mes(3)  # need Ind
    elif z == 14:
        if (total_z_pop > 10) and ((total_z_pop << 1) > types.RoadTotal):
            send_mes(4)  # need roads
    elif z == 18:
        if (total_z_pop > 50) and (total_z_pop > types.RailTotal):
            send_mes(5)  # need rail
    elif z == 22:
        if (total_z_pop > 10) and (power_pop == 0):
            send_mes(6)  # need Power
    elif z == 26:
        if (types.ResPop > 500) and (types.StadiumPop == 0):
            send_mes(7)  # need Stad
            types.ResCap = 1
        else:
            types.ResCap = 0
    elif z == 28:
        if (types.IndPop > 70) and (types.PortPop == 0):
            send_mes(8)  # need Seaport
            types.IndCap = 1
        else:
            types.IndCap = 0
    elif z == 30:
        if (types.ComPop > 100) and (types.APortPop == 0):
            send_mes(9)  # need Airport
            types.ComCap = 1
        else:
            types.ComCap = 0
    elif z == 32:
        # dec score for unpowered zones
        tm = types.unPwrdZCnt + types.PwrdZCnt
        if tm:
            if (types.PwrdZCnt / tm) < 0.7:
                send_mes(15)  # brownouts
    elif z == 35:
        if types.PolluteAverage > 60:  # Note: was 80, but adjusted for gameplay
            send_mes(-10)  # pollution alert
    elif z == 42:
        if types.CrimeAverage > 100:
            send_mes(-11)  # crime alert
    elif z == 45:
        if (types.TotalPop > 60) and (types.FireStPop == 0):
            send_mes(13)  # need fire station
    elif z == 48:
        if (types.TotalPop > 60) and (types.PolicePop == 0):
            send_mes(14)  # need police station
    elif z == 51:
        if types.CityTax > 12:
            send_mes(16)  # high taxes
    elif z == 54:
        if (types.RoadEffect < 20) and (types.RoadTotal > 30):
            send_mes(17)  # road deterioration
    elif z == 57:
        if (types.FireEffect < 700) and (types.TotalPop > 20):
            send_mes(18)  # fire funding needed
    elif z == 60:
        if (types.PoliceEffect < 700) and (types.TotalPop > 20):
            send_mes(19)  # police funding needed
    elif z == 63:
        if types.TrafficAverage > 60:
            send_mes(-12)  # traffic jam


def check_growth() -> None:
    """
    Check for population growth milestones and send appropriate messages.

    Tracks when the city reaches certain population thresholds
    and sends congratulatory messages.

    Ported from CheckGrowth() in s_msg.c.
    """
    if not (types.CityTime & 3):
        z = 0
        this_city_pop = ((types.ResPop) + (types.ComPop * 8) + (types.IndPop * 8)) * 20

        if types.LastCityPop:
            if (types.LastCityPop < 2000) and (this_city_pop >= 2000):
                z = 35  # Town
            elif (types.LastCityPop < 10000) and (this_city_pop >= 10000):
                z = 36  # City
            elif (types.LastCityPop < 50000) and (this_city_pop >= 50000):
                z = 37  # Capital
            elif (types.LastCityPop < 100000) and (this_city_pop >= 100000):
                z = 38  # Metropolis
            elif (types.LastCityPop < 500000) and (this_city_pop >= 500000):
                z = 39  # Megalopolis

        if z and (z != types.LastCategory):
            send_mes(-z)  # Negative for picture messages
            types.LastCategory = z

        types.LastCityPop = this_city_pop


def do_scenario_score(type_val: int) -> None:
    """
    Handle scenario scoring and win/lose conditions.

    Args:
        type_val: Scenario type identifier

    Ported from DoScenarioScore() in s_msg.c.
    """
    z = -200  # you lose

    if type_val == 1:  # Dullsville
        if types.CityClass >= 4:
            z = -100  # you win
    elif type_val == 2:  # San Francisco
        if types.CityClass >= 4:
            z = -100
    elif type_val == 3:  # Hamburg
        if types.CityClass >= 4:
            z = -100
    elif type_val == 4:  # Bern
        if types.TrafficAverage < 80:
            z = -100
    elif type_val == 5:  # Tokyo
        if types.CityScore > 500:
            z = -100
    elif type_val == 6:  # Detroit
        if types.CrimeAverage < 60:
            z = -100
    elif type_val == 7:  # Boston
        if types.CityScore > 500:
            z = -100
    elif type_val == 8:  # Rio de Janeiro
        if types.CityScore > 500:
            z = -100

    clear_mes()
    send_mes(z)

    if z == -200:
        do_lose_game()


def clear_mes() -> None:
    """
    Clear message state.

    Resets message port and coordinates.

    Ported from ClearMes() in s_msg.c.
    """
    types.MessagePort = 0
    types.MesX = 0
    types.MesY = 0
    types.LastPicNum = 0


def send_mes(mnum: int) -> int:
    """
    Send a message.

    Args:
        mnum: Message number (positive for text, negative for pictures)

    Returns:
        1 if message was sent, 0 if not

    Ported from SendMes() in s_msg.c.
    """
    if mnum < 0:
        if mnum != types.LastPicNum:
            types.MessagePort = mnum
            types.MesX = 0
            types.MesY = 0
            types.LastPicNum = mnum
            return 1
    else:
        if not types.MessagePort:
            types.MessagePort = mnum
            types.MesX = 0
            types.MesY = 0
            return 1
    return 0


def send_mes_at(mnum: int, x: int, y: int) -> None:
    """
    Send a message at a specific location.

    Args:
        mnum: Message number
        x: X coordinate
        y: Y coordinate

    Ported from SendMesAt() in s_msg.c.
    """
    if send_mes(mnum):
        types.MesX = x
        types.MesY = y


def do_message() -> None:
    """
    Main message processing function.

    Handles displaying messages, playing sounds, and managing message timing.
    This is called regularly to update the message display.

    Ported from doMessage() in s_msg.c.
    """
    message_str = ""
    pict_id = 0
    first_time = False

    if types.MessagePort:
        types.MesNum = types.MessagePort
        types.MessagePort = 0
        types.LastMesTime = tick_count()
        first_time = True
    else:
        first_time = False
        if types.MesNum == 0:
            return
        if types.MesNum < 0:
            types.MesNum = -types.MesNum
            types.LastMesTime = tick_count()
        elif (tick_count() - types.LastMesTime) > (60 * 30 * 1000):  # 30 minutes in ms
            types.MesNum = 0
            return

    if first_time:
        # Play sound effects based on message type
        abs_mes_num = abs(types.MesNum)
        if abs_mes_num == 12:
            if random.Rand(5) == 1:
                make_sound("city", "HonkHonk-Med")
            elif random.Rand(5) == 1:
                make_sound("city", "HonkHonk-Low")
            elif random.Rand(5) == 1:
                make_sound("city", "HonkHonk-High")
        elif abs_mes_num in (11, 20, 22, 23, 24, 25, 26, 27):
            make_sound("city", "Siren")
        elif abs_mes_num == 21:
            make_sound("city", f"Monster -speed {monster_speed()}")
        elif abs_mes_num == 30:
            make_sound("city", "Explosion-Low")
            make_sound("city", "Siren")
        elif abs_mes_num == 43:
            make_sound("city", "Explosion-High")
            make_sound("city", "Explosion-Low")
            make_sound("city", "Siren")
        elif abs_mes_num == 44:
            make_sound("city", "Siren")

    if types.MesNum >= 0:
        if types.MesNum == 0:
            return

        if types.MesNum > 60:
            types.MesNum = 0
            return

        message_str = get_message_string(types.MesNum)

        if types.MesX or types.MesY:
            # TODO: draw goto button
            pass

        if types.autoGo and (types.MesX or types.MesY):
            do_auto_goto(types.MesX, types.MesY, message_str)
            types.MesX = 0
            types.MesY = 0
        else:
            set_message_field(message_str)

    else:  # picture message
        pict_id = -types.MesNum

        if pict_id < 43:
            message_str = get_message_string(pict_id)
        else:
            message_str = ""

        do_show_picture(pict_id)

        types.MessagePort = pict_id  # resend text message

        if types.autoGo and (types.MesX or types.MesY):
            do_auto_goto(types.MesX, types.MesY, message_str)
            types.MesX = 0
            types.MesY = 0


def do_auto_goto(x: int, y: int, msg: str) -> None:
    """
    Automatically go to a location when a message is displayed.

    Args:
        x: X coordinate
        y: Y coordinate
        msg: Message text

    Ported from DoAutoGoto() in s_msg.c.
    """
    set_message_field(msg)
    cmd = f"UIAutoGoto {x} {y}"
    types.Eval(cmd)


def set_message_field(msg: str) -> None:
    """
    Set the message field in the UI.

    Args:
        msg: Message text to display

    Ported from SetMessageField() in s_msg.c.
    """
    global HaveLastMessage, LastMessage

    if not hasattr(types, 'HaveLastMessage'):
        types.HaveLastMessage = 0
        types.LastMessage = ""

    if (not types.HaveLastMessage or
        types.LastMessage != msg):
        types.LastMessage = msg
        types.HaveLastMessage = 1
        cmd = f"UISetMessage {{{msg}}}"
        types.Eval(cmd)


def do_show_picture(pict_id: int) -> None:
    """
    Show a picture/message dialog.

    Args:
        pict_id: Picture/message identifier

    Ported from DoShowPicture() in s_msg.c.
    """
    cmd = f"UIShowPicture {pict_id}"
    types.Eval(cmd)


def do_lose_game() -> None:
    """
    Handle game loss scenario.

    Ported from DoLoseGame() in s_msg.c.
    """
    types.Eval("UILoseGame")


def do_win_game() -> None:
    """
    Handle game win scenario.

    Ported from DoWinGame() in s_msg.c.
    """
    types.Eval("UIWinGame")


def monster_speed() -> int:
    """
    Calculate monster movement speed.

    Returns:
        Speed value for monster sprite

    Ported from MonsterSpeed() in s_msg.c.
    """
    return (random.Rand(40) + 70)