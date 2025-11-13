# City evaluation
# city_score: int = 0
# delta_city_score: int = 0
# score_type: int = 0
# score_wait: int = 0
# city_class: int = 0

# Problem tracking
# pol_max_x: int = 0
# pol_max_y: int = 0
# traffic_average: int = 0
# pos_stack_num: int = 0
# s_map_x_stack: list[int] = []
# s_map_y_stack: list[int] = []
# l_dir: int = 5  # Last direction for traffic pathfinding

# Sprite control
# z_source: int = 0
# have_last_message: int = 0
# p_dest_x: int = 0
# p_dest_y: int = 0
# c_dest_x: int = 0
# c_dest_y: int = 0
# abs_dist: int = 0
# cop_flt_cnt: int = 0
# god_cnt: int = 0
# gdest_x: int = 0
# gdest_y: int = 0
# god_control: int = 0
# cop_control: int = 0
# traf_max_x: int = 0
# traf_max_y: int = 0
# crime_max_x: int = 0
# crime_max_y: int = 0

# Disaster locations
# flood_x: int = 0
# flood_y: int = 0
# crash_x: int = 0
# crash_y: int = 0
# cc_x: int = 0
# cc_y: int = 0

# City population (64-bit)
# city_pop: int = 0
# delta_city_pop: int = 0

# City class strings
# city_class_str: list[str] = ["", "", "", "", "", ""]

# City evaluation
# city_yes: int = 0
# city_no: int = 0
# problem_table: list[int] = [0] * PROBNUM
# problem_votes: list[int] = [0] * PROBNUM
# problem_order: list[int] = [0, 0, 0, 0]
# city_ass_value: int = 0

# Initialization flags
# init_sim_load: int = 0
# do_initial_eval: int = 0
# startup: int = 0
# startup_game_level: int = 0
# performance_timing: int = 0
# flush_time: float = 0.0

# System state
# wire_mode: int = 0
# multi_player_mode: int = 0
# sugar_mode: int = 0
# sim_delay: int = 0
# sim_skips: int = 0
# sim_skip: int = 0
# sim_paused: int = 0
# sim_paused_speed: int = 0
# sim_tty: int = 0
# update_delayed: int = 0

# Dynamic data
# dynamic_data: list[int] = [0] * 32

# Multiplayer
# players: int = 0
# votes: int = 0

# Graphics settings
# bob_height: int = 0
# over_ride: int = 0
# expensive: int = 0

# Tool system
# pending_tool: int = 0
# pending_x: int = 0
# pending_y: int = 0

# Terrain generation
# tree_level: int = 0
# lake_level: int = 0
# curve_level: int = 0
# create_island: int = 0

# Special features
# special_base: int = 0
# punish_cnt: int = 0
# dozing: int = 0

# Tool configuration
# tool_size: list[int] = []
# tool_offset: list[int] = []
# tool_colors: list[int] = []

# Display system
# displays: str = ""
# first_display: str = ""

# Date strings
# date_str: list[str] = [""] * 12

# Map update flags
# new_map: int = 0
# new_map_flags: list[int] = [0] * NMAPS
# new_graph: int = 0

# UI update flags
# valve_flag: int = 0
# must_update_funds: int = 0
# must_update_options: int = 0
# census_changed: int = 0
# eval_changed: int = 0

# Special effects
# melt_x: int = 0
# melt_y: int = 0

# System control
# need_rest: int = 0
# exit_return: int = 0

# ============================================================================
# Graphics System
# ============================================================================

# Main display for graphics
# main_display: view_types.XDisplay | None = None

# ============================================================================
# Utility Functions
# ============================================================================


# Avoid importing heavy package symbols at module import time to prevent
# circular import issues (e.g. AppContext). Do local/lazy imports inside
# functions below when a concrete class is needed.


def Rand(*args) -> int:
    """Compatibility wrapper for random generation.

    Supports both signatures:
      - Rand(range_val)
      - Rand(context, range_val)

    If a context is provided we delegate to `src.micropolis.random.Rand`.
    Otherwise fall back to Python's random module to preserve previous
    context-free behavior.
    """
    if len(args) == 1:
        range_val = args[0]
        import random as _pyrandom

        return _pyrandom.randint(0, range_val - 1) if range_val > 0 else 0
    elif len(args) == 2:
        context, range_val = args
        from src.micropolis import random as _random

        return _random.Rand(context, range_val)
    else:
        raise TypeError("Rand() expected 1 or 2 arguments")


def Rand16(*args) -> int:
    """Compatibility wrapper for 16-bit random numbers.

    Supports optional context: Rand16() or Rand16(context)
    """
    if len(args) == 0:
        import random as _pyrandom

        return _pyrandom.randint(0, 65535)
    elif len(args) == 1:
        context = args[0]
        from src.micropolis import random as _random

        return _random.Rand16(context)
    else:
        raise TypeError("Rand16() expected 0 or 1 arguments")


def sim_rand(*args) -> int:
    """Compatibility wrapper for sim_rand.

    Supports optional context: sim_rand() or sim_rand(context)
    """
    if len(args) == 0:
        import random as _pyrandom

        return _pyrandom.randint(0, 0xFFFF)
    elif len(args) == 1:
        context = args[0]
        from src.micropolis import random as _random

        return _random.sim_rand(context)
    else:
        raise TypeError("sim_rand() expected 0 or 1 arguments")


def sim_srand(*args) -> None:
    """Seed wrapper: sim_srand(seed) or sim_srand(context, seed).

    If called with a context, delegates to random.sim_srand(context, seed).
    Otherwise seeds the local Python RNG for context-free usage.
    """
    if len(args) == 1:
        seed = args[0]
        import random as _pyrandom

        _pyrandom.seed(seed)
    elif len(args) == 2:
        context, seed = args
        from src.micropolis import random as _random

        return _random.sim_srand(context, seed)
    else:
        raise TypeError("sim_srand() expected 1 or 2 arguments")


def sim_srandom(*args) -> None:
    """Alias for sim_srand to match older API.

    Accepts same signatures as sim_srand.
    """
    return sim_srand(*args)


# ============================================================================
# Factory Functions
# ============================================================================

# def MakeNewSim() -> Sim:
#     """Create a new simulation instance"""
#     return Sim()

# def MakeNewView() -> SimView:
#     """Create a new view instance"""
#     return SimView()


def GetSprite(*args):
    """Compatibility wrapper for getting the global sprite.

    Supports signatures:
      - GetSprite() -> None (legacy placeholder)
      - GetSprite(context, sprite_type) -> SimSprite | None
    """
    if len(args) == 0:
        return None
    elif len(args) >= 2:
        context = args[0]
        sprite_type = args[1]
        from src.micropolis import sprite_manager

        return sprite_manager.get_sprite(context, sprite_type)
    else:
        raise TypeError("GetSprite() expected 0 or >=2 arguments")


def MakeSprite(*args):
    """Create or get a sprite.

    Supports:
      - MakeSprite() -> new SimSprite (fallback)
      - MakeSprite(context, sprite_type, x=0, y=0)
    """
    if len(args) == 0:
        # Lazy import to avoid import-time cycles
        from src.micropolis.sim_sprite import SimSprite

        return SimSprite()
    elif len(args) >= 2:
        context = args[0]
        sprite_type = args[1]
        x = args[2] if len(args) > 2 else 0
        y = args[3] if len(args) > 3 else 0
        from src.micropolis import sprite_manager

        return sprite_manager.make_sprite(context, sprite_type, x, y)
    else:
        raise TypeError("MakeSprite() expected 0 or >=2 arguments")


def MakeNewSprite(*args):
    """Alias for creating a new sprite instance.

    Supports:
      - MakeNewSprite() -> SimSprite()
      - MakeNewSprite(context, sprite_type, x=0, y=0)
    """
    if len(args) == 0:
        # Lazy import to avoid import-time cycles
        from src.micropolis.sim_sprite import SimSprite

        return SimSprite()
    elif len(args) >= 2:
        context = args[0]
        sprite_type = args[1]
        x = args[2] if len(args) > 2 else 0
        y = args[3] if len(args) > 3 else 0
        from src.micropolis import sprite_manager

        return sprite_manager.make_new_sprite(context, sprite_type, x, y)
    else:
        raise TypeError("MakeNewSprite() expected 0 or >=2 arguments")
