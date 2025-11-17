import threading
import time
from collections.abc import Callable
from queue import Queue

from .constants import (
    HWLDX,
    HWLDY,
    NMAPS,
    QWX,
    QWY,
    SM_X,
    SM_Y,
    WORLD_X,
    WORLD_Y,
    OBJN,
    PWRMAPSIZE,
    HISTORIES,
    PROBNUM,
    RESBASE,
    PWRSTKSIZE,
    SEP_3,
    randtbl,
    TYPE_3,
    DEG_3,
)
from .sim_sprite import SimSprite
from typing import TYPE_CHECKING, Any, ClassVar

# Avoid importing TerrainGenerator at module import time to prevent a
# circular import with terrain.py which imports AppContext. Use TYPE_CHECKING
# for type hints and keep the runtime annotation as Any.
if TYPE_CHECKING:
    from .terrain import TerrainGenerator
    from .view_types import XDisplay
    from .state_contract import LegacyStateContract

from pydantic import BaseModel, Field, ConfigDict, PrivateAttr

from .app_config import AppConfig

# Avoid importing Sim at module import time (it imports view modules which
# may import AppContext). Import for typing only.
if TYPE_CHECKING:
    from .sim import Sim

from .constants import (
    residentialState,
    commercialState,
    industrialState,
    fireState,
    queryState,
    policeState,
    wireState,
    DOZE_STATE,
    rrState,
    roadState,
    chalkState,
    eraserState,
    stadiumState,
    parkState,
    seaportState,
    powerState,
    nuclearState,
    airportState,
    networkState,
)


class AppContext(BaseModel):
    """Global application context."""

    # Allow arbitrary runtime types (threads, pygame surfaces, etc.)
    # This prevents pydantic from trying to generate schemas for types like
    # threading.Thread or pygame.Surface which are used as runtime-only
    # attributes on the context.
    model_config = ConfigDict(arbitrary_types_allowed=True)

    _state_contract: "LegacyStateContract | None" = PrivateAttr(default=None)
    _suspend_state_contract: bool = PrivateAttr(default=False)
    # Private attrs for evaluation UI compatibility
    _evaluation_panel_visible: bool = PrivateAttr(default=False)
    _evaluation_panel_dirty: bool = PrivateAttr(default=False)
    _evaluation_panel_size: tuple[int, int] = PrivateAttr(default=(320, 200))
    _evaluation_panel_surface: Any | None = PrivateAttr(default=None)

    def attach_state_contract(self, contract: "LegacyStateContract | None") -> None:
        self._state_contract = contract

    def detach_state_contract(self) -> None:
        self._state_contract = None

    def _suspend_contract_notifications(self) -> None:
        self._suspend_state_contract = True

    def _resume_contract_notifications(self) -> None:
        self._suspend_state_contract = False

    def __setattr__(self, name: str, value: Any) -> None:  # type: ignore[override]
        super().__setattr__(name, value)
        if (
            name.startswith("_")
            or self._state_contract is None
            or self._suspend_state_contract
        ):
            return
        self._state_contract.on_context_update(self, name, value)

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
    auto_goto: bool = Field(default=True)  # AutoGoto
    chalk_overlay: bool = Field(
        default=True
    )  # ChalkOverlay - show construction preview
    dynamic_filter: bool = Field(
        default=False
    )  # DynamicFilter - apply filtering to overlays
    city_tax: int = Field(default=7)  # CityTax
    city_time: int = Field(default=50)  # CityTime
    no_disasters: bool = Field(default=False)  # NoDisasters
    punish_cnt: int = Field(default=0)  # PunishCnt
    last_keys: str = Field(default="    ")  # Legacy keyboard last-keys buffer
    auto_bulldoze: bool = Field(default=True)  # AutoBulldoze
    auto_budget: bool = Field(default=True)  # AutoBudget
    mes_num: int = Field(default=0)  # MesNum
    last_mes_time: int = Field(default=0)  # LastMesTime
    flag_blink: int = Field(default=0)  # FlagBlink
    sim_speed: int = Field(default=3)  # SimSpeed
    start_time: float = Field(default_factory=time.time)  # StartTime
    beat_time: float = Field(default_factory=time.time)  # BeatTime
    # Use a runtime-agnostic type and avoid creating a Sim instance here to
    # prevent import cycles during package import. The sim can be created by
    # the application startup code and assigned to this field.
    sim: Any | None = Field(default=None)  # Global simulation object
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
    road_value: int = Field(default=0)
    police_value: int = Field(default=0)
    fire_value: int = Field(default=0)
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
    budget_timer: int = Field(default=0)  # BudgetTimer
    budget_timeout: int = Field(default=0)  # BudgetTimeout
    # city_tax: int = Field(default=7)

    # flag_blink
    tile_sync: int = Field(default=0)
    tiles_animated: int = Field(default=0)
    do_animation: int = Field(default=0)
    do_messages: int = Field(default=0)
    do_notices: int = Field(default=0)
    color_intensities: list[int] = Field(default_factory=lambda: [0] * 16)

    mes_x: int = Field(default=0)
    mes_y: int = Field(default=0)
    # mes_num: int = Field(default=0)
    message_port: int = Field(default=0)
    # last_mes_time: int = Field(default=0)
    last_city_pop: int = Field(default=0)
    last_category: int = Field(default=0)
    last_pic_num: int = Field(default=0)
    last_message: str = Field(default="")
    # have_last_message: bool = Field(default=False)

    # sim_speed: int = Field(default=0)
    sim_meta_speed: int = Field(default=0)
    # no_disasters: bool = Field(default=False)
    # auto_bulldoze: bool = Field(default=True)
    # auto_budget: bool = Field(default=True)
    # auto_go: bool = Field(default=True)
    # user_sound_on: bool = Field(default=True)
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

    # Evaluation panel UI settings
    auto_evaluation: bool = Field(default=False)  # Auto-run yearly evaluations
    eval_notifications: bool = Field(default=True)  # Show eval notifications

    pol_max_x: int = Field(default=0)
    pol_max_y: int = Field(default=0)
    traffic_average: int = Field(default=0)
    pos_stack_num: int = Field(default=0)
    s_map_x_stack: list[int] = Field(default_factory=list)
    s_map_y_stack: list[int] = Field(default_factory=list)
    l_dir: int = Field(default=5)

    z_source: int = Field(default=0)
    # have_last_message: int = Field(default=0)
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
    sugar_mode: bool = Field(default=False)
    sim_delay: int = Field(default=0)
    # sim_skips: int = Field(default=0)
    # sim_skip: int = Field(default=0)
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

    main_display: Any | None = Field(default=None)

    # Compatibility fields added to reduce test breakage during migration.
    # These cover legacy names used throughout tests and older modules.
    simcam_list: list[Any] = Field(default_factory=list)
    ComZPop: int = Field(default=0)
    com_his__max: int = Field(default=0)
    graph_panel_visible: bool = Field(default=False)
    # Provide surface registries similar to legacy global dicts used by
    # platform/view helpers. Tests may access these directly in some places.
    view_surfaces: dict[int, Any] = Field(default_factory=dict)
    view_overlay_surfaces: dict[int, Any] = Field(default_factory=dict)
    # Alias name used in some modules/tests for the main pygame display
    pygame_display: Any | None = Field(default=None)

    # Additional compatibility aliases frequently referenced by tests
    # and legacy modules. Keep these as simple fields or properties so
    # tests can access them directly without needing migration updates.
    next_cam_id: int = Field(default=0)
    must_draw_evaluation: bool = Field(default=False)

    # Provide a private holder for evaluation data used by the
    # evaluation UI. Use PrivateAttr so pydantic does not treat this as a
    # serializable model field but tests can still access it as
    # ``context._evaluation_data``.
    _evaluation_data: Any | None = PrivateAttr(default=None)

    # Generator alias - some modules reference `context.generator`.
    generator: Any | None = Field(default=None)

    # Backwards camel-case aliases commonly used in legacy code/tests
    # Provide simple property shims that map to the canonical snake_case
    # fields defined above so legacy callers succeed without migration.
    @property
    def CityTime(self) -> int:
        return getattr(self, "city_time", 0)

    @CityTime.setter
    def CityTime(self, value: int) -> None:
        self.city_time = value

    @property
    def StartingYear(self) -> int:
        return getattr(self, "starting_year", 1900)

    @StartingYear.setter
    def StartingYear(self, value: int) -> None:
        self.starting_year = value

    @property
    def CityPop(self) -> int:
        return getattr(self, "city_pop", 0)

    @CityPop.setter
    def CityPop(self, value: int) -> None:
        self.city_pop = value

    @property
    def deltaCityPop(self) -> int:
        return getattr(self, "delta_city_pop", 0)

    @deltaCityPop.setter
    def deltaCityPop(self, value: int) -> None:
        self.delta_city_pop = value

    @property
    def CityAssValue(self) -> int:
        return getattr(self, "city_ass_value", 0)

    @CityAssValue.setter
    def CityAssValue(self, value: int) -> None:
        self.city_ass_value = value

    @property
    def CityScore(self) -> int:
        return getattr(self, "city_score", 0)

    @CityScore.setter
    def CityScore(self, value: int) -> None:
        self.city_score = value

    @property
    def deltaCityScore(self) -> int:
        return getattr(self, "delta_city_score", 0)

    @deltaCityScore.setter
    def deltaCityScore(self, value: int) -> None:
        self.delta_city_score = value

    @property
    def CityYes(self) -> int:
        return getattr(self, "city_yes", 0)

    @CityYes.setter
    def CityYes(self, value: int) -> None:
        self.city_yes = value

    @property
    def CityNo(self) -> int:
        return getattr(self, "city_no", 0)

    @CityNo.setter
    def CityNo(self, value: int) -> None:
        self.city_no = value

    @property
    def ProblemVotes(self) -> list[int]:
        return getattr(self, "problem_votes", [])

    @ProblemVotes.setter
    def ProblemVotes(self, value: list[int]) -> None:
        self.problem_votes = value

    @property
    def ProblemOrder(self) -> list[int]:
        return getattr(self, "problem_order", [0, 1, 2, 3])

    @ProblemOrder.setter
    def ProblemOrder(self, value: list[int]) -> None:
        self.problem_order = value

    # pygame display alias used in some tests/code
    @property
    def PYGAME_DISPLAY(self) -> Any | None:
        return getattr(self, "pygame_display", None)

    @PYGAME_DISPLAY.setter
    def PYGAME_DISPLAY(self, value: Any | None) -> None:
        self.pygame_display = value

    # Backwards-compatible alias accessors
    @property
    def com_his(self) -> list[int]:
        return self.com_hist

    @com_his.setter
    def com_his(self, value: list[int]) -> None:
        self.com_hist = value

    @property
    def IndZPop(self) -> int:
        return getattr(self, "ind_z_pop", 0)

    @IndZPop.setter
    def IndZPop(self, value: int) -> None:
        self.ind_z_pop = value

    @property
    def TotalFunds(self) -> int:
        return getattr(self, "total_funds", 0)

    @TotalFunds.setter
    def TotalFunds(self, value: int) -> None:
        self.total_funds = value

    @property
    def generator(self) -> Any | None:
        # Prefer an explicitly-set generator field, otherwise fall back
        # to the module-level global_generator used by legacy code.
        if self.__dict__.get("generator") is not None:
            return self.__dict__.get("generator")
        return globals().get("global_generator")

    @generator.setter
    def generator(self, value: Any | None) -> None:
        # Keep both the explicit field and the legacy global in sync so
        # code that inspects either location behaves consistently.
        self.__dict__["generator"] = value
        globals()["global_generator"] = value

    # Legacy tool/state names expected by older modules and tests. Provide
    # explicit fields mapping to the canonical constants from
    # micropolis.constants so legacy callers can access them via the
    # AppContext during migration.
    residential_state: int = Field(default=residentialState)
    residental_state: int = Field(default=residentialState)  # common typo in tests
    commercial_state: int = Field(default=commercialState)
    industrial_state: int = Field(default=industrialState)
    fire_state: int = Field(default=fireState)
    query_state: int = Field(default=queryState)
    police_state: int = Field(default=policeState)
    bulldozer_state: int = Field(default=DOZE_STATE)
    rr_state: int = Field(default=rrState)
    rail_state: int = Field(default=rrState)
    road_state: int = Field(default=roadState)
    wire_state: int = Field(default=wireState)
    chalk_state: int = Field(default=chalkState)
    eraser_state: int = Field(default=eraserState)
    stadium_state: int = Field(default=stadiumState)
    park_state: int = Field(default=parkState)
    seaport_state: int = Field(default=seaportState)
    power_state: int = Field(default=powerState)
    nuclear_state: int = Field(default=nuclearState)
    airport_state: int = Field(default=airportState)
    network_state: int = Field(default=networkState)

    firstState: ClassVar[int] = residentialState
    lastState: ClassVar[int] = networkState
    # Backwards-compatible tool state names (some modules reference these
    # as attributes on the context object). Keep as ClassVar to avoid
    # including them in model serialization/state.
    dozeState: ClassVar[int] = DOZE_STATE
    rrState: ClassVar[int] = rrState
    roadState: ClassVar[int] = roadState
    wireState: ClassVar[int] = wireState

    # sim: Sim = Field(default_factory=Sim)

    sim_loops: int = Field(default=0)
    # sim_delay:int = Field(default=50)
    # sim_skips:int = Field(default=0)
    sim_pause: bool = Field(default=False)
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
    problem_taken: list[int] = [0] * PROBNUM
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

    x_start: int = 0
    y_start: int = 0
    map_x: int = 0
    map_y: int = 0
    dir: int = 0
    last_dir: int = 0

    # Generation parameters (can be set externally)
    # tree_level: int = -1  # Level for tree creation (-1 = random, 0 = none, >0 = amount)
    # lake_level: int = -1  # Level for lake creation (-1 = random, 0 = none, >0 = amount)
    # curve_level: int = -1  # Level for river curviness (-1 = random, 0 = none, >0 = amount)
    # create_island: int = -1  # Island creation (-1 = 10% chance, 0 = never, 1 = always)

    # History data arrays (120 months of data)
    # history_10: list[list[int]] = []  # 10-year view (120 months)
    # history_120: list[list[int]] = []  # 120-year view (120 months)
    history_initialized: bool = False

    # Graph scaling variables
    all_max: int = 0
    # graph_10_max: int = 0
    # graph_120_max: int = 0

    # Graph update flags
    # new_graph: bool = False

    # Forward declarations for map drawing functions
    mapProcs: list[Callable | None] = [None] * NMAPS

    # Message strings loaded from stri.301 file
    MESSAGE_STRINGS: list[str] = []

    # Global power grid state
    power_stack_num: int = 0
    power_stack_x: list[int] = [0] * PWRSTKSIZE
    power_stack_y: list[int] = [0] * PWRSTKSIZE
    max_power: int = 0
    num_power: int = 0
    # Print output destination (could be file, stdout, etc.)
    print_output: str | None = None
    print_file: str | None = None
    # Static variable from rand.c
    next: int = 1
    # Global state variables
    fptr_idx: int = SEP_3 + 1  # Front pointer index
    rptr_idx: int = 1  # Rear pointer index
    state: list[int] = randtbl[1:]  # State array (skip type byte)
    rand_type: int = TYPE_3
    rand_deg: int = DEG_3
    rand_sep: int = SEP_3
    end_ptr_idx: int = DEG_3  # Index of last element
    # Simulation speed and timing
    # sim_speed: int = 3  # Default simulation speed (0-7)
    # sim_paused: bool = False
    # sim_delay: int = 10  # Delay between simulation steps in milliseconds
    # sim_skips: int = 0  # Number of simulation steps to skip
    # sim_skip: int = 0  # Current skip counter

    # Game state
    game_started: bool = False
    # need_rest: bool = False

    # Performance timing
    # performance_timing: bool = False
    # flush_time: float = 0.0

    # Configuration options
    # auto_budget: bool = True
    # auto_goto: bool = True
    # auto_bulldoze: bool = True
    # no_disasters: bool = False
    # user_sound_on: bool = True
    # do_animation: bool = True
    # do_messages: bool = True
    # do_notices: bool = True

    # Multiplayer and platform settings

    # Animation cycle counter
    # cycle = 0

    # Crash locations (for message reporting)
    # crash_x = 0
    # crash_y = 0

    # Global sprite instances (one per type)
    global_sprites: list[SimSprite | None] = [None] * OBJN

    # Free sprite pool
    free_sprites: SimSprite | None = None

    # Financial variables
    # total_funds: int = 0

    # Game state variables
    # punish_cnt: int = 0
    # auto_bulldoze: int = 0
    # auto_budget: int = 0
    # last_mes_time: int = 0
    # GameLevel: int = 0
    # init_sim_load: int = 0
    # scenario_id: int = 0
    # SimSpeed: int = 0
    # SimMetaSpeed: int = 0
    # user_sound_on: int = 0
    # CityName: str = ""
    # no_disasters: int = 0
    # mes_num: int = 0
    # eval_changed: int = 0
    # flag_blink: int = 0

    # Game startup state
    # startup: int = 0
    # startup_name: str | None = None

    # Timing variables
    # start_time: float | None = None
    _tick_base: float = time.perf_counter()

    # Simulation control variables
    # sim_skips: int = 0
    # sim_skip: int = 0
    # sim_paused: int = 0
    # sim_paused_speed: int = 0
    # heat_steps: int = 0
    # Use a runtime-agnostic type to avoid importing TerrainGenerator here.
    global_generator: Any | None = None

    # sim = None  # Optional override for tests

    # Global state (equivalent to w_tk.c globals)
    tk_main_interp: Any | None = None  # Simplified - no TCL interpreter
    main_window: Any | None = None  # Pygame screen surface
    # update_delayed = False
    auto_scroll_edge: int = 16
    auto_scroll_step: int = 16
    auto_scroll_delay: int = 10

    # Timer management
    sim_timer_token: int | None = None  # pygame timer event ID
    sim_timer_idle: bool = False
    sim_timer_set: bool = False
    earthquake_timer_token: int | None = None  # pygame timer event ID
    earthquake_timer_set: bool = False
    earthquake_delay: int = 3000

    # Performance timing
    # performance_timing = False
    # flush_time = 0.0

    # Command system
    command_callbacks: dict[str, Callable] = {}
    stdin_thread: threading.Thread | None = None
    stdin_queue: Queue = Queue()
    running: bool = False

    # special_base: int = CHURCH
    # over_ride: int = 0
    # expensive: int = 1000
    # players: int = 1
    # votes: int = 0
    # pending_tool: int = -1
    # pending_x: int = 0
    # pending_y: int = 0

    # View flags
    VIEW_REDRAW_PENDING: ClassVar[int] = 1

    # View types
    X_Mem_View: ClassVar[int] = 1
    X_Wire_View: ClassVar[int] = 2

    # View classes
    Editor_Class: ClassVar[int] = 0
    Map_Class: ClassVar[int] = 1

    # Button event types
    Button_Press: ClassVar[int] = 0
    Button_Move: ClassVar[int] = 1
    Button_Release: ClassVar[int] = 2


# END OF FILE
