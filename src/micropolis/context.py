import time

from .constants import (
    HWLDX,
    HWLDY,
    NMAPS,
    QWX,
    QWY,
    SM_X,
    SM_Y,
    WORLD_X,
    WORLD_Y, OBJN, PWRMAPSIZE, HISTORIES, PROBNUM, RESBASE,
)

from .view_types import XDisplay
from pydantic import BaseModel, Field

from .app_config import AppConfig
from .sim import Sim

from src.micropolis.constants import residentialState, networkState


class AppContext(BaseModel):
    """Global application context."""

    last_now_time: float = Field(default_factory=time.time)
    config: AppConfig
    user_sound_on: bool = Field(default=True)  # UserSoundOn
    must_update_options: bool = Field(default=True)  # MustUpdateOptions
    have_last_message: bool = Field(default=False)  # HaveLastMessage
    scenario_id: int = Field(default=0)  # ScenarioID
    starting_year: int = Field(default=1900)  # StartingYear
    tile_synch: int = Field(default=0x01)  # TileSynch
    sim_skips: int = Field(default=0)  # SimSkips
    sim_skip: int = Field(default=0)  # SimSkip
    auto_go: bool = Field(default=True)  # AutoGo
    city_tax: int = Field(default=7)  # CityTax
    city_time: int = Field(default=50)  # CityTime
    no_disasters: bool = Field(default=False)  # NoDisasters
    punish_cnt: int = Field(default=0)  # PunishCnt
    auto_bulldoze: bool = Field(default=True)  # AutoBulldoze
    auto_budget: bool = Field(default=True)  # AutoBudget
    mes_num: int = Field(default=0)  # MesNum
    last_mes_time: int = Field(default=0)  # LastMesTime
    flag_blink: int = Field(default=0)  # FlagBlink
    sim_speed: int = Field(default=3)  # SimSpeed
    start_time: float = Field(default_factory=time.time)  # StartTime
    beat_time: float = Field(default_factory=time.time)  # BeatTime
    sim: Sim = Field(default=Sim())  # Global simulation object
    sound_initialized: bool = Field(default=False)  # SoundInitialized
    map_data: list[list[int]] = Field(
        default_factory=lambda: [[0 for _ in range(WORLD_Y)] for _ in range(WORLD_X)]
    )  # Main map data
    pop_density: list[list[int]] = Field(
        default_factory=lambda: [[0 for _ in range(HWLDY)] for _ in range(HWLDX)]
    )  # Population density overlay
    trf_density: list[list[int]] = Field(
        default_factory=lambda: [[0 for _ in range(HWLDY)] for _ in range(HWLDX)]
    )  # Traffic density overlay
    pollution_mem: list[list[int]] = Field(
        default_factory=lambda: [[0 for _ in range(HWLDY)] for _ in range(HWLDX)]
    )  # Pollution overlay
    land_value_mem: list[list[int]] = Field(
        default_factory=lambda: [[0 for _ in range(HWLDY)] for _ in range(HWLDX)]
    )  # Land value overlay
    crime_mem: list[list[int]] = Field(
        default_factory=lambda: [[0 for _ in range(HWLDY)] for _ in range(HWLDX)]
    )  # Crime overlay
    tem: list[list[int]] = Field(
        default_factory=lambda: [[0 for _ in range(HWLDY)] for _ in range(HWLDX)]
    )  # Temporary overlays
    tem2: list[list[int]] = Field(
        default_factory=lambda: [[0 for _ in range(HWLDY)] for _ in range(HWLDX)]
    )  # Temporary overlays 2
    terrain_mem: list[list[int]] = Field(
        default_factory=lambda: [[0 for _ in range(QWY)] for _ in range(QWX)]
    )  # Terrain memory
    rate_og_mem: list[list[int]] = Field(
        default_factory=lambda: [[0 for _ in range(SM_Y)] for _ in range(SM_X)]
    )  # Rate of growth
    fire_st_map: list[list[int]] = Field(
        default_factory=lambda: [[0 for _ in range(SM_Y)] for _ in range(SM_X)]
    )  # Fire station coverage
    police_map: list[list[int]] = Field(
        default_factory=lambda: [[0 for _ in range(SM_Y)] for _ in range(SM_X)]
    )  # Police station coverage
    police_map_effect: list[list[int]] = Field(
        default_factory=lambda: [[0 for _ in range(SM_Y)] for _ in range(SM_X)]
    )  # Police station coverage effect
    com_rate: list[list[int]] = Field(
        default_factory=lambda: [[0 for _ in range(SM_Y)] for _ in range(SM_X)]
    )
    fire_rate: list[list[int]] = Field(
        default_factory=lambda: [[0 for _ in range(SM_Y)] for _ in range(SM_X)]
    )  # Fire rate
    stem: list[list[int]] = Field(
        default_factory=lambda: [[0 for _ in range(SM_Y)] for _ in range(SM_X)]
    )  # Temporary storage
    sprite_x_offset: list[int] = Field(
        default_factory=lambda: [0] * OBJN
    )  # Sprite X offsets
    sprite_y_offset: list[int] = Field(
        default_factory=lambda: [0] * OBJN
    )  # Sprite Y offsets
    s_map_x: int = Field(default=0)  # Map position X
    s_map_y: int = Field(default=0)  # Map position Y
    cchr: int = Field(default=0)  # Character display
    cchr9: int = Field(default=0)  # Character display 9

    road_total: int = Field(default=0)  # Infrastructure totals
    rail_total: int = Field(default=0)

    # population statistics
    fire_pop: int = Field(default=0)
    com_pop: int = Field(default=0)
    ind_pop: int = Field(default=0)
    res_pop: int = Field(default=0)
    total_pop: int = Field(default=0)
    last_total_pop: int = Field(default=0)

    # zoned population
    res_z_pop: int = Field(default=0)
    com_z_pop: int = Field(default=0)
    ind_z_pop: int = Field(default=0)
    total_z_pop: int = Field(default=0)

    # service populations
    hosp_pop: int = Field(default=0)
    church_pop: int = Field(default=0)
    stadium_pop: int = Field(default=0)
    police_pop: int = Field(default=0)
    fire_st_pop: int = Field(default=0)

    # special facility populations
    coal_pop: int = Field(default=0)
    nuclear_pop: int = Field(default=0)
    port_pop: int = Field(default=0)
    airport_pop: int = Field(default=0)

    need_hosp: int = Field(default=0)
    need_church: int = Field(default=0)

    # city statistics
    crime_average: int = Field(default=0)
    pollute_average: int = Field(default=0)
    lv_average: int = Field(default=0)

    # city information
    micropolis_version: str = Field(default="1.0")
    city_name: str = Field(default="New City")
    city_file_name: str = Field(default="untitled.micropolis")
    startup_name: str = Field(default="")

    # starting_year: int = Field(default=1900)
    # city_time: int = Field(default=0)
    last_city_time: int = Field(default=0)
    last_city_month: int = Field(default=0)
    last_city_year: int = Field(default=0)

    last_funds: int = Field(default=0)
    total_funds: int = Field(default=0)

    last_r: int = Field(default=0)
    last_c: int = Field(default=0)
    last_i: int = Field(default=0)

    game_level: int = Field(default=0)
    cycle: int = Field(default=0)
    # scenario_id: int = Field(default=0)
    shake_now: int = Field(default=0)
    flood_count: int = Field(default=0)
    don_dither: int = Field(default=0)
    do_overlay: int = Field(default=0)

    res_his: list[int] = Field(default_factory=list)
    res_his_max: int = Field(default=0)
    com_hist: list[int] = Field(default_factory=list)
    com_his_max: int = Field(default=0)
    ind_his: list[int] = Field(default_factory=list)
    ind_his_max: int = Field(default=0)
    money_his: list[int] = Field(default_factory=list)
    crime_his: list[int] = Field(default_factory=list)
    pollution_his: list[int] = Field(default_factory=list)
    misc_his: list[int] = Field(default_factory=list)

    power_map: list[int] = Field(
        default_factory=lambda: [0] * (PWRMAPSIZE)
    )  # Power grid map

    road_percent: float = Field(default=0.0)
    police_percent: float = Field(default=0.0)
    fire_percent: float = Field(default=0.0)
    road_spend: int = Field(default=0)
    police_spend: int = Field(default=0)
    fire_spend: int = Field(default=0)
    road_max_value: int = Field(default=0)
    police_max_value: int = Field(default=0)
    fire_max_value: int = Field(default=0)
    tax_fund: int = Field(default=0)
    road_fund: int = Field(default=0)
    police_fund: int = Field(default=0)
    fire_fund: int = Field(default=0)
    road_effect: int = Field(default=0)
    police_effect: int = Field(default=0)
    fire_effect: int = Field(default=0)
    tax_flag: int = Field(default=0)
    city_tax: int = Field(default=7)

    flag_blink
    tile_sync: int = Field(default=0)
    tiles_animated: int = Field(default=0)
    do_animation: int = Field(default=0)
    do_messages: int = Field(default=0)
    do_notices: int = Field(default=0)
    color_intensities: list[int] = Field(default_factory=lambda: [0] * 16)

    mes_x: int = Field(default=0)
    mes_y: int = Field(default=0)
    mes_num: int = Field(default=0)
    message_port: int = Field(default=0)
    last_mes_time: int = Field(default=0)
    last_city_pop: int = Field(default=0)
    last_category: int = Field(default=0)
    last_pic_num: int = Field(default=0)
    last_message: str = Field(default="")
    have_last_message: bool = Field(default=False)

    sim_speed: int = Field(default=0)
    sim_meta_speed: int = Field(default=0)
    no_disasters: bool = Field(default=False)
    auto_bulldoze: bool = Field(default=True)
    auto_budget: bool = Field(default=True)
    auto_go: bool = Field(default=True)
    user_sound_on: bool = Field(default=True)
    sound: int = Field(default=1)

    disaster_event: int = Field(default=0)
    disaster_wait: int = Field(default=0)

    res_cap: int = Field(default=0)
    com_cap: int = Field(default=0)
    ind_cap: int = Field(default=0)

    r_value: int = Field(default=0)
    c_value: int = Field(default=0)
    i_value: int = Field(default=0)

    pwrd_z_cnt: int = Field(default=0)

    un_pwrd_z_cnt: int = Field(default=0)

    homd_dir: str = Field(default="")
    resource_dir: str = Field(default="")
    host_name: str = Field(default="")

    graph_10_max: int = Field(default=0)
    graph_120_max: int = Field(default=0)
    res_2_his_max: int = Field(default=0)
    com_2_his_max: int = Field(default=0)
    ind_2_his_max: int = Field(default=0)

    history_10: list[list[int]] = Field(
        default_factory=lambda: [[] for _ in range(HISTORIES)]
    )
    history_120: list[list[int]] = Field(
        default_factory=lambda: [[] for _ in range(HISTORIES)]
    )

    city_score: int = Field(default=0)
    delta_city_score: int = Field(default=0)
    score_type: int = Field(default=0)
    score_wait: int = Field(default=0)
    city_class: int = Field(default=0)

    pol_max_x: int = Field(default=0)
    pol_max_y: int = Field(default=0)
    traffic_average: int = Field(default=0)
    pos_stack_num: int = Field(default=0)
    s_map_x_stack: list[int] = Field(default_factory=list)
    s_map_y_stack: list[int] = Field(default_factory=list)
    l_dir: int = Field(default=5)

    z_source: int = Field(default=0)
    have_last_message: int = Field(default=0)
    p_dest_x: int = Field(default=0)
    p_dest_y: int = Field(default=0)
    c_dest_x: int = Field(default=0)
    c_dest_y: int = Field(default=0)
    abs_dist: int = Field(default=0)
    cop_flt_cnt: int = Field(default=0)
    god_cnt: int = Field(default=0)
    gdest_x: int = Field(default=0)
    gdest_y: int = Field(default=0)
    god_control: int = Field(default=0)
    cop_control: int = Field(default=0)
    traf_max_x: int = Field(default=0)
    traf_max_y: int = Field(default=0)
    crime_max_x: int = Field(default=0)
    crime_max_y: int = Field(default=0)

    flood_x: int = Field(default=0)
    flood_y: int = Field(default=0)
    crash_x: int = Field(default=0)
    crash_y: int = Field(default=0)
    cc_x: int = Field(default=0)
    cc_y: int = Field(default=0)

    city_pop: int = Field(default=0)
    delta_city_pop: int = Field(default=0)
    city_class_str: list[str] = Field(default_factory=lambda: ["", "", "", "", "", ""])
    city_yes: int = Field(default=0)
    city_no: int = Field(default=0)
    problem_table: list[int] = Field(default_factory=lambda: [0] * PROBNUM)
    problem_votes: list[int] = Field(default_factory=lambda: [0] * PROBNUM)
    city_ass_value: int = Field(default=0)
    init_sim_load: int = Field(default=0)
    do_initial_eval: int = Field(default=0)
    startup: int = Field(default=0)
    startup_game_level: int = Field(default=0)
    performance_timing: int = Field(default=0)
    flush_time: float = Field(default=0.0)

    wire_mode: int = Field(default=0)
    multi_player_mode: int = Field(default=0)
    sim_delay: int = Field(default=0)
    sim_skips: int = Field(default=0)
    sim_skip: int = Field(default=0)
    sim_paused: int = Field(default=0)
    sim_paused_speed: int = Field(default=0)
    sim_tty: int = Field(default=0)
    update_delayed: int = Field(default=0)

    dynamic_data: list[int] = Field(default_factory=list)

    players: int = Field(default=0)
    votes: int = Field(default=0)

    bob_height: int = Field(default=0)
    over_ride: int = Field(default=0)
    expensive: int = Field(default=0)
    pending_tool: int = Field(default=0)
    pending_x: int = Field(default=0)
    pending_y: int = Field(default=0)
    tree_level: int = Field(default=0)
    lake_level: int = Field(default=0)
    curve_level: int = Field(default=0)
    create_island: int = Field(default=0)
    special_base: int = Field(default=0)
    # punish_cnt: int = Field(default=0)
    dozing: int = Field(default=0)
    tool_size: list[int] = Field(default_factory=list)
    tool_offset: list[int] = Field(default_factory=list)
    tool_colors: list[int] = Field(default_factory=list)
    displays: str = Field(default="")
    first_display: str = Field(default="")
    date_str: list[str] = Field(default_factory=lambda: [""] * 12)
    new_map: int = Field(default=0)
    new_map_flags: list[int] = Field(default_factory=lambda: [0] * NMAPS)
    new_graph: int = Field(default=0)
    valve_flags: int = Field(default=0)
    must_update_funds: int = Field(default=0)
    # must_update_options: int = Field(default=0)
    census_changed: int = Field(default=0)
    eval_changed: int = Field(default=0)
    melt_x: int = Field(default=0)
    melt_y: int = Field(default=0)
    need_rest: int = Field(default=0)
    exit_return: int = Field(default=0)
    tk_must_exit: bool = Field(default=False)


    main_display: XDisplay | None = Field(default=None)

    firstState = residentialState
    lastState = networkState

    sim: Sim = Field(default_factory=Sim)

    sim_loops:int = Field(default=0)
    # sim_delay:int = Field(default=50)
    # sim_skips:int = Field(default=0)
    sim_pause:bool = Field(default=False)
    # sim_paused_speed:int = Field(default=3)
    # sim_tty:int = 0

    heat_steps: int = 0
    heat_flow: int = -7
    heat_rule: int = 0
    heat_wrap: int = 3
    current_tool_tile: int = RESBASE
    editor_viewport_size: tuple[int, int] = (0, 0)

    cell_src: list[int] = Field(default_factory=list)
    cell_dst: list[int] = Field(default_factory=list)

    must_draw_curr_percents: bool = False
    must_draw_budget_window: bool = False

    # start_time: float = 0.0
    # beat_time: float = 0.0
    # last_now_time: float = 0.0

    # city_file_name: str | None = None
    # startup: int = 0
    # startup_game_level: int = 0

    # Valve control
    valve_flag: int = 0
    crime_ramp: int = 0
    pollute_ramp: int = 0
    r_valve: int = 0
    c_valve: int = 0
    i_valve: int = 0

    # Capacity limits
    # res_cap: int = 0
    # com_cap: int = 0
    # ind_cap: int = 0

    # Financial
    cash_flow: int = 0
    e_market: float = 4.0

    # Disaster control
    # disaster_event: int = 0
    # disaster_wait: int = 0

    # Scoring
    # score_type: int = 0
    # score_wait: int = 0

    # Power statistics
    # pwrd_z_cnt: int = 0
    # un_pwrd_z_cnt: int = 0
    new_power: int = 0

    # Tax averaging
    av_city_tax: int = 0

    # Cycle counters
    scycle: int = 0
    fcycle: int = 0
    spdcycle: int = 0

    # Initial evaluation flag
    # do_initial_eval: int = 0

    # Melt down coordinates
    # melt_x: int = 0
    # melt_y: int = 0

    eval_valid: int = 0
    # city_yes: int = 0
    # city_no: int = 0
    # problem_table: list[int] = [0] * types.PROBNUM
    problem_taken: list[int] = [0] * types.PROBNUM
    # problem_votes: list[int] = [0] * types.PROBNUM  # votes for each problem
    problem_order: list[int] = [0] * 4  # sorted index to above
    # city_pop: int = 0
    # delta_city_pop: int = 0
    # city_ass_value: int = 0
    # city_class: int = 0  # 0..5
    # city_score: int = 0
    # delta_city_score: int = 0
    average_city_score: int = 0
    # traffic_average: int = 0
# END OF FILE
