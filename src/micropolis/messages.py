"""messages.py - In-game messages and notifications system for Micropolis.

This module provides AppContext-based message APIs while offering a
minimal, conservative test-only compatibility shim that mirrors a small
set of legacy module-level fields between the `types` module and the
AppContext so existing tests can be migrated incrementally.

The shim is intentionally limited in scope and silent on failure to
avoid affecting production behavior.
"""

from __future__ import annotations

import os
import sys
import time
from typing import TYPE_CHECKING

from .context import AppContext
from .ui_utilities import eval_cmd_str
from .asset_manager import get_asset_path
from . import compat_shims
from . import types

if TYPE_CHECKING:
    from .simulation import rand  # pragma: no cover - typing only


# Module-level legacy message strings kept for backwards compatibility
MESSAGE_STRINGS: list[str] = []


def load_message_strings(context: AppContext) -> None:
    """Load message strings (stri.301) into context and mirror to module var."""
    if getattr(context, "MESSAGE_STRINGS", None):
        globals()["MESSAGE_STRINGS"] = context.MESSAGE_STRINGS
        return

    try:
        manifest_path = get_asset_path("stri.301", category="raw")
        if manifest_path is not None and manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                context.MESSAGE_STRINGS = [line.rstrip("\n") for line in f.readlines()]
            globals()["MESSAGE_STRINGS"] = context.MESSAGE_STRINGS
            return
    except Exception:
        pass

    # Legacy fallback
    stri_file = os.path.join(
        os.path.dirname(__file__), "..", "..", "assets", "stri.301"
    )
    try:
        with open(stri_file, "r", encoding="utf-8") as f:
            context.MESSAGE_STRINGS = [line.rstrip("\n") for line in f.readlines()]
        globals()["MESSAGE_STRINGS"] = context.MESSAGE_STRINGS
    except Exception:
        context.MESSAGE_STRINGS = [""] * 61
        globals()["MESSAGE_STRINGS"] = context.MESSAGE_STRINGS


def get_message_string(context: AppContext, message_num: int) -> str:
    if not getattr(context, "MESSAGE_STRINGS", None):
        load_message_strings(context)
    if 1 <= message_num <= len(context.MESSAGE_STRINGS):
        return context.MESSAGE_STRINGS[message_num - 1]
    return ""


def tick_count() -> int:
    return int(time.time() * 1000)


def make_sound(context: AppContext, channel: str, sound_name: str) -> None:
    if not (getattr(context, "sound", 1) and getattr(context, "user_sound_on", True)):
        return
    try:
        from .audio import play_sound

        play_sound(context, channel, sound_name)
    except Exception:
        return


def _mirror_message_state_to_types(context: AppContext) -> None:
    """Mirror selected message fields from AppContext into module `types`.

    Conservative - silently ignores exceptions.
    """
    try:
        attrs = (
            "message_port",
            "mes_x",
            "mes_y",
            "mes_num",
            "last_mes_time",
            "last_city_pop",
            "last_category",
            "last_pic_num",
            "last_message",
            "have_last_message",
        )
        for a in attrs:
            try:
                setattr(types, a, getattr(context, a))
            except Exception:
                # Some patched `types` objects (e.g., MagicMock) may not
                # accept attribute assignments; ignore those cases.
                pass
    except Exception:
        pass


def _mirror_types_into_context(context: AppContext) -> None:
    """Mirror a conservative set of legacy `types` fields into context.

    This allows tests that set module-level globals on `types` to affect
    the AppContext-based functions during the incremental migration.
    """
    try:
        attrs = (
            "message_port",
            "mes_x",
            "mes_y",
            "mes_num",
            "last_mes_time",
            "last_city_pop",
            "last_category",
            "last_pic_num",
            "last_message",
            "have_last_message",
            # city/population fields used by some message logic
            "res_pop",
            "com_pop",
            "ind_pop",
            "city_time",
            "city_class",
            "score_type",
            "score_wait",
            "city_score",
            "traffic_average",
            "pollute_average",
            "crime_average",
        )
        for a in attrs:
            if hasattr(types, a):
                try:
                    setattr(context, a, getattr(types, a))
                except Exception:
                    pass
    except Exception:
        pass


def clear_mes(context: AppContext) -> None:
    context.message_port = 0
    context.mes_x = 0
    context.mes_y = 0
    context.last_pic_num = 0
    _mirror_message_state_to_types(context)


def send_mes(context: AppContext, mnum: int) -> int:
    # Ensure any legacy module-level values influence behavior first
    _mirror_types_into_context(context)

    if mnum < 0:
        if mnum != getattr(context, "last_pic_num", 0):
            context.message_port = mnum
            context.mes_x = 0
            context.mes_y = 0
            context.last_pic_num = mnum
            _mirror_message_state_to_types(context)
            return 1
    else:
        if not getattr(context, "message_port", 0):
            context.message_port = mnum
            context.mes_x = 0
            context.mes_y = 0
            _mirror_message_state_to_types(context)
            return 1
    return 0


def send_mes_at(context: AppContext, mnum: int, x: int, y: int) -> None:
    _mirror_types_into_context(context)
    if send_mes(context, mnum):
        context.mes_x = x
        context.mes_y = y
        _mirror_message_state_to_types(context)


def check_growth(context: AppContext) -> None:
    _mirror_types_into_context(context)
    if not (getattr(context, "city_time", 0) & 3):
        z = 0
        this_city_pop = (
            getattr(context, "res_pop", 0)
            + (getattr(context, "com_pop", 0) * 8)
            + (getattr(context, "ind_pop", 0) * 8)
        ) * 20

        if getattr(context, "last_city_pop", 0):
            if (context.last_city_pop < 2000) and (this_city_pop >= 2000):
                z = 35
            elif (context.last_city_pop < 10000) and (this_city_pop >= 10000):
                z = 36
            elif (context.last_city_pop < 50000) and (this_city_pop >= 50000):
                z = 37
            elif (context.last_city_pop < 100000) and (this_city_pop >= 100000):
                z = 38
            elif (context.last_city_pop < 500000) and (this_city_pop >= 500000):
                z = 39

        if z and (z != getattr(context, "last_category", 0)):
            send_mes(context, -z)
            context.last_category = z
            _mirror_message_state_to_types(context)

        context.last_city_pop = this_city_pop
        _mirror_message_state_to_types(context)


def do_scenario_score(context: AppContext, type_val: int) -> None:
    _mirror_types_into_context(context)
    z = -200
    if type_val == 1:
        if getattr(context, "city_class", 0) >= 4:
            z = -100
    elif type_val == 4:
        if getattr(context, "traffic_average", 0) < 80:
            z = -100
    elif type_val == 5:
        if getattr(context, "city_score", 0) > 500:
            z = -100
    elif type_val == 6:
        if getattr(context, "crime_average", 0) < 60:
            z = -100

    clear_mes(context)
    send_mes(context, z)
    _mirror_message_state_to_types(context)

    if z == -200:
        do_lose_game(context)


def do_message(context: AppContext) -> None:
    # Mirror in any legacy module-level values before processing
    _mirror_types_into_context(context)

    message_str = ""
    pict_id = 0
    first_time = False

    if getattr(context, "message_port", 0):
        context.mes_num = context.message_port
        context.message_port = 0
        context.last_mes_time = tick_count()
        first_time = True
    else:
        first_time = False
        if getattr(context, "mes_num", 0) == 0:
            return
        if context.mes_num < 0:
            context.mes_num = -context.mes_num
            context.last_mes_time = tick_count()
        elif (tick_count() - getattr(context, "last_mes_time", 0)) > (60 * 30 * 1000):
            context.mes_num = 0
            return

    if first_time:
        abs_mes_num = abs(getattr(context, "mes_num", 0))
        if abs_mes_num == 12:
            from .simulation import rand

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

    if getattr(context, "mes_num", 0) >= 0:
        if context.mes_num == 0:
            return
        if context.mes_num > 60:
            context.mes_num = 0
            return

        message_str = get_message_string(context, context.mes_num)

        if getattr(context, "mes_x", 0) or getattr(context, "mes_y", 0):
            pass

        if getattr(context, "auto_go", False) and (
            getattr(context, "mes_x", 0) or getattr(context, "mes_y", 0)
        ):
            do_auto_goto(context, context.mes_x, context.mes_y, message_str)
            context.mes_x = 0
            context.mes_y = 0
        else:
            set_message_field(context, message_str)
    else:
        pict_id = -context.mes_num
        if pict_id < 43:
            message_str = get_message_string(context, pict_id)
        else:
            message_str = ""

        do_show_picture(context, pict_id)
        context.message_port = pict_id

        if getattr(context, "auto_go", False) and (
            getattr(context, "mes_x", 0) or getattr(context, "mes_y", 0)
        ):
            do_auto_goto(context, context.mes_x, context.mes_y, message_str)
            context.mes_x = 0
            context.mes_y = 0

    _mirror_message_state_to_types(context)


def do_auto_goto(context: AppContext, x: int, y: int, msg: str) -> None:
    set_message_field(context, msg)
    cmd = f"UIAutoGoto {x} {y}"
    try:
        if hasattr(types, "Eval"):
            types.Eval(cmd)
        else:
            eval_cmd_str(context, cmd)
    except Exception:
        eval_cmd_str(context, cmd)


def set_message_field(context: AppContext, msg: str) -> None:
    if (
        not getattr(context, "have_last_message", False)
        or getattr(context, "last_message", "") != msg
    ):
        context.last_message = msg
        context.have_last_message = True
        cmd = f"UISetMessage {{{msg}}}"
        try:
            if hasattr(types, "Eval"):
                try:
                    types.LastMessage = msg
                    types.HaveLastMessage = 1
                except Exception:
                    pass
                types.Eval(cmd)
            else:
                eval_cmd_str(context, cmd)
        except Exception:
            eval_cmd_str(context, cmd)

        _mirror_message_state_to_types(context)


def do_show_picture(context: AppContext, pict_id: int) -> None:
    cmd = f"UIShowPicture {pict_id}"
    try:
        if hasattr(types, "Eval"):
            types.Eval(cmd)
        else:
            eval_cmd_str(context, cmd)
    except Exception:
        eval_cmd_str(context, cmd)


def do_lose_game(context: AppContext) -> None:
    try:
        if hasattr(types, "Eval"):
            types.Eval("UILoseGame")
        else:
            eval_cmd_str(context, "UILoseGame")
    except Exception:
        eval_cmd_str(context, "UILoseGame")


def do_win_game(context: AppContext) -> None:
    try:
        if hasattr(types, "Eval"):
            types.Eval("UIWinGame")
        else:
            eval_cmd_str(context, "UIWinGame")
    except Exception:
        eval_cmd_str(context, "UIWinGame")


def monster_speed(context: AppContext) -> int:
    from .simulation import rand

    return rand(context, 40) + 70


# Install test-friendly legacy wrappers for commonly-used message APIs so
# legacy callers/tests that omit the AppContext argument continue to work
# during the migration to explicit contexts.
try:
    compat_shims.inject_legacy_wrappers(
        sys.modules.get(__name__),
        [
            "load_message_strings",
            "get_message_string",
            "make_sound",
            "send_mes",
            "send_mes_at",
            "do_message",
            "do_show_picture",
            "clear_mes",
        ],
    )
except Exception:
    pass
