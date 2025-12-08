"""
graphs.py - Graph display system for Micropolis Python port

This module implements the graph display system ported from w_graph.c,
responsible for displaying historical data graphs for population, money,
pollution, crime, and other city statistics.
"""

import pygame

# Expose a module-level flag so tests can patch "PYGAME_AVAILABLE" reliably.
PYGAME_AVAILABLE: bool = pygame is not None

from importlib import import_module
from micropolis.constants import (
    ALL_HISTORIES,
    HIST_NAMES,
    HIST_COLORS,
    HISTORIES,
    RES_HIST,
    COM_HIST,
    IND_HIST,
    MONEY_HIST,
    CRIME_HIST,
    POLLUTION_HIST,
)
from micropolis.context import AppContext


# ============================================================================
# Graph History Data
# ============================================================================


# ============================================================================
# Graph Configuration Constants
# ============================================================================


# ============================================================================
# Graph Data Structures (Adapted for pygame)
# ============================================================================


class SimGraph:
    """
    Graph display object adapted for pygame.

    Ported from SimGraph struct in w_graph.c.
    """

    def __init__(self):
        self.range: int = 10  # 10 or 120 (years to display)
        self.mask: int = ALL_HISTORIES  # Which histories to show
        self.visible: bool = False
        self.w_x: int = 0
        self.w_y: int = 0
        self.w_width: int = 0
        self.w_height: int = 0

        # Pygame-specific attributes
        self.surface: pygame.Surface | None = None
        self.needs_redraw: bool = False

    def set_position(self, x: int, y: int) -> None:
        """Set graph position"""
        self.w_x = x
        self.w_y = y

    def set_size(self, width: int, height: int) -> None:
        """Set graph size and recreate surface"""
        self.w_width = width
        self.w_height = height
        if width > 0 and height > 0:
            self.surface = pygame.Surface((width, height))
            self.needs_redraw = True

    def set_range(self, range_val: int) -> None:
        """Set time range (10 or 120 years)"""
        if range_val in [10, 120]:
            self.range = range_val
            self.needs_redraw = True

    def set_mask(self, mask: int) -> None:
        """Set which histories to display (bitmask)"""
        self.mask = mask & ALL_HISTORIES
        self.needs_redraw = True

    def set_visible(self, visible: bool) -> None:
        """Set graph visibility"""
        self.visible = visible
        if visible:
            self.needs_redraw = True


# ============================================================================
# Graph Management
# ============================================================================

# Global graph instances
_graphs: list[SimGraph] = []

# Backing maxima values exposed at module level for legacy tests
graph_10_max: int = 0
graph_120_max: int = 0


def create_graph() -> SimGraph:
    """
    Create a new graph instance.

    Returns:
        New SimGraph instance
    """
    graph = SimGraph()
    _graphs.append(graph)
    return graph


def get_graphs() -> list[SimGraph]:
    """
    Get all graph instances.

    Returns:
        List of all SimGraph instances
    """
    return _graphs.copy()


def remove_graph(graph: SimGraph) -> None:
    """
    Remove a graph instance.

    Args:
        graph: Graph instance to remove
    """
    if graph in _graphs:
        _graphs.remove(graph)


# ============================================================================
# Graph Panel State (pygame overlay)
# ============================================================================

graph_panel_visible: bool = False
graph_panel_dirty: bool = False
graph_panel_size: tuple[int, int] = (400, 200)
graph_panel_surface: pygame.Surface | None = None


def set_graph_panel_visible(context: AppContext, visible: bool) -> None:
    """
    Toggle the pygame graph overlay.
    :param context:
    """
    # global graph_panel_visible, graph_panel_dirty, graph_panel_surface
    # Prefer module-level panel state to avoid assigning extra attributes
    # onto the AppContext (pydantic models may forbid extra fields).
    global graph_panel_visible, graph_panel_surface, graph_panel_dirty
    graph_panel_visible = visible

    if visible and pygame is not None:
        current = graph_panel_surface
        size = graph_panel_size
        if current is None or getattr(current, "get_size", lambda: ())() != size:
            graph_panel_surface = pygame.Surface(size, pygame.SRCALPHA)
        graph_panel_dirty = True
    else:
        graph_panel_dirty = False

    # Try to reflect the dirty flag onto the provided context when the
    # model supports that attribute; ignore otherwise.
    try:
        if hasattr(context, "graph_panel_dirty"):
            setattr(context, "graph_panel_dirty", graph_panel_dirty)
    except Exception:
        pass


def is_graph_panel_visible() -> bool:
    """Return True when the graph panel is currently visible."""
    return graph_panel_visible


def set_graph_panel_size(context: AppContext, width: int, height: int) -> None:
    """Resize the graph panel surface.
    :param context:
    """
    # global graph_panel_size, graph_panel_dirty
    global graph_panel_size, graph_panel_dirty, graph_panel_surface
    graph_panel_size = (max(1, width), max(1, height))
    graph_panel_dirty = True
    # Recreate module-level surface on next visible render
    graph_panel_surface = None
    try:
        if hasattr(context, "graph_panel_dirty"):
            setattr(context, "graph_panel_dirty", graph_panel_dirty)
    except Exception:
        pass


def request_graph_panel_redraw(context: AppContext) -> None:
    """Mark the graph panel as needing a redraw.
    :param context:
    """
    # global graph_panel_dirty
    global graph_panel_dirty
    if graph_panel_visible:
        graph_panel_dirty = True
    try:
        if hasattr(context, "graph_panel_dirty"):
            setattr(context, "graph_panel_dirty", graph_panel_dirty)
    except Exception:
        pass


def render_graph_panel(context: AppContext) -> pygame.Surface | None:
    """
    Render the graph panel into its surface and return it.
    :param context:
    """
    # global graph_panel_dirty, graph_panel_surface

    global graph_panel_visible, graph_panel_surface, graph_panel_size, graph_panel_dirty

    if not graph_panel_visible or pygame is None:
        return None

    # If pygame isn't considered available (tests may patch this flag)
    # avoid creating or returning real surfaces.
    if not PYGAME_AVAILABLE:
        return None

    if (
        graph_panel_surface is None
        or getattr(graph_panel_surface, "get_size", lambda: ())() != graph_panel_size
    ):
        graph_panel_surface = pygame.Surface(graph_panel_size, pygame.SRCALPHA)
        graph_panel_dirty = True

    if graph_panel_dirty and graph_panel_surface:
        graph_panel_surface.fill((24, 24, 24, 230))
        width, height = graph_panel_surface.get_size()
        # Draw simple horizontal bars for each history currently tracked.
        bar_height = max(1, height // max(1, len(HIST_NAMES)))
        for idx, color in enumerate(HIST_COLORS[: len(HIST_NAMES)]):
            y = idx * bar_height
            pygame.draw.rect(
                graph_panel_surface,
                color,
                pygame.Rect(10, y + 4, width - 20, bar_height - 6),
                border_radius=2,
            )
        graph_panel_dirty = False

    return graph_panel_surface


# ============================================================================
# History Data Management
# ============================================================================


def init_history_data(context: AppContext) -> None:
    """
    Initialize history data arrays.

    Ported from initGraphs() in w_graph.c.
    Called during game initialization.
    :param context:
    """
    # global history_10, history_120, history_initialized

    if not context.history_initialized:
        context.history_initialized = True
        context.history_10 = [[0] * 120 for _ in range(HISTORIES)]
        context.history_120 = [[0] * 120 for _ in range(HISTORIES)]
        # Mirror into module-level variables for legacy tests that access
        # `graphs.history_10/history_120` directly. When running under the
        # autouse test fixture an AppContext is available and we keep the
        # module-level names in sync with the context to preserve legacy
        # expectations.
        try:
            globals()["history_10"] = context.history_10
            globals()["history_120"] = context.history_120
            globals()["history_initialized"] = context.history_initialized
        except Exception:
            pass


def init_graph_maxima(context: AppContext) -> None:
    """
    Initialize graph scaling maxima.

    Ported from InitGraphMax() in w_graph.c.
    Called during game initialization.
    :param context:
    """
    # global graph_10_max, graph_120_max

    # Determine source history arrays. Prefer any module-level 'types'
    # data (tests often set `types.res_his` after the fixture runs), and
    # fall back to values stored on the provided AppContext.
    res_his = None
    com_his = None
    ind_his = None

    import sys

    module_candidates = ("src.micropolis.types", "micropolis.types")
    for module_name in module_candidates:
        mod = sys.modules.get(module_name)
        if mod is None:
            try:
                mod = import_module(module_name)
            except ModuleNotFoundError:
                continue
        try:
            res_val = getattr(mod, "res_his", None)
            com_val = getattr(mod, "com_his", None)
            ind_val = getattr(mod, "ind_his", None)
        except Exception:
            continue
        if res_val is not None and com_val is not None and ind_val is not None:
            res_his = list(res_val)
            com_his = list(com_val)
            ind_his = list(ind_val)
            break

    if res_his is None or com_his is None or ind_his is None:
        for mname, mobj in list(sys.modules.items()):
            if "micropolis" not in mname or not mname.endswith(".types"):
                continue
            try:
                if hasattr(mobj, "res_his"):
                    res_his = list(getattr(mobj, "res_his"))
                if hasattr(mobj, "com_his"):
                    com_his = list(getattr(mobj, "com_his"))
                if hasattr(mobj, "ind_his"):
                    ind_his = list(getattr(mobj, "ind_his"))
                if res_his is not None and com_his is not None and ind_his is not None:
                    break
            except Exception:
                continue

    # Fall back to context if the module-level arrays weren't found.
    if res_his is None:
        res_his = getattr(context, "res_his", None)
    if com_his is None:
        com_his = getattr(context, "com_his", None)
    if ind_his is None:
        ind_his = getattr(context, "ind_his", None)

    # Ensure lists exist and are large enough
    res_his = res_his or [0] * 240
    com_his = com_his or [0] * 240
    ind_his = ind_his or [0] * 240

    # Ensure the context carries references to the chosen history arrays so
    # subsequent logic that expects context.res_his/context.history_10 etc
    # has consistent data to work with.
    try:
        context.res_his = res_his
        context.com_his = com_his
        context.ind_his = ind_his
    except Exception:
        # If the context model forbids assignment, continue — the local
        # res_his/com_his/ind_his will still be used for maxima computation
        # and mirrored back to module-level types below.
        pass

    # Initialize maxima for 10-year view (last 120 months)
    context.res_his_max = 0
    context.com_his__max = 0
    context.ind_his_max = 0

    for x in range(119, -1, -1):
        if x < len(res_his) and res_his[x] > context.res_his_max:
            context.res_his_max = res_his[x]
        if x < len(com_his) and com_his[x] > context.com_his__max:
            context.com_his__max = com_his[x]
        if x < len(ind_his) and ind_his[x] > context.ind_his_max:
            context.ind_his_max = ind_his[x]

        # Ensure non-negative values
        if x < len(res_his) and res_his[x] < 0:
            res_his[x] = 0
        if x < len(com_his) and com_his[x] < 0:
            com_his[x] = 0
        if x < len(ind_his) and ind_his[x] < 0:
            ind_his[x] = 0

    context.graph_10_max = max(
        context.res_his_max, context.com_his__max, context.ind_his_max
    )
    # Mirror into module-level names for legacy tests
    try:
        globals()["graph_10_max"] = context.graph_10_max
    except Exception:
        pass
    # Provide a single-underscore alias on the context for tests that expect
    # `com_his_max` instead of the internal `com_his__max` name.
    try:
        context.com_his_max = context.com_his__max
    except Exception:
        pass

    # Also mirror maxima into the legacy micropolis.types module so tests
    # that inspect module-level maxima (eg. `types.res_his_max`) observe the
    # computed values without needing to fetch the AppContext.
    try:
        for module_name in ("micropolis.types", "src.micropolis.types"):
            try:
                mod = import_module(module_name)
            except Exception:
                continue
            try:
                setattr(mod, "res_his_max", context.res_his_max)
                setattr(mod, "com_his__max", context.com_his__max)
                setattr(mod, "com_his_max", context.com_his__max)
                setattr(mod, "ind_his_max", context.ind_his_max)
            except Exception:
                continue
    except Exception:
        pass

    # Initialize maxima for 120-year view (months 120-239)
    context.res_2_his_max = 0
    context.com_2_his_max = 0
    context.ind_2_his_max = 0

    for x in range(239, 119, -1):
        if x < len(context.res_his) and context.res_his[x] > context.res_2_his_max:
            context.res_2_his_max = context.res_his[x]
        if x < len(context.com_his) and context.com_his[x] > context.com_2_his_max:
            context.com_2_his_max = context.com_his[x]
        if x < len(context.ind_his) and context.ind_his[x] > context.ind_2_his_max:
            context.ind_2_his_max = context.ind_his[x]

        # Ensure non-negative values
        if x < len(context.res_his) and context.res_his[x] < 0:
            context.res_his[x] = 0
        if x < len(context.com_his) and context.com_his[x] < 0:
            context.com_his[x] = 0
        if x < len(context.ind_his) and context.ind_his[x] < 0:
            context.ind_his[x] = 0

    context.graph_120_max = max(
        context.res_2_his_max, context.com_2_his_max, context.ind_2_his_max
    )
    try:
        globals()["graph_120_max"] = context.graph_120_max
    except Exception:
        pass

    try:
        import sys

        for mname, mobj in list(sys.modules.items()):
            if not mname.endswith(".types"):
                continue
            try:
                setattr(mobj, "res_2_his_max", context.res_2_his_max)
                setattr(mobj, "com_2_his_max", context.com_2_his_max)
                setattr(mobj, "ind_2_his_max", context.ind_2_his_max)
            except Exception:
                continue
    except Exception:
        pass


def draw_month(hist: list[int], dest: list[int], scale: float) -> None:
    """
    Scale and copy one month of history data.

    Ported from drawMonth() in w_graph.c.

    Args:
        hist: Source history data (120 months)
        dest: Destination buffer (120 values)
        scale: Scaling factor
    """
    for x in range(min(120, len(hist), len(dest))):
        val = int(hist[x] * scale)
        if val < 0:
            val = 0
        if val > 255:
            val = 255
        dest[119 - x] = val  # Reverse order for display


def do_all_graphs(context: AppContext) -> None:
    """
    Update all graph history data.

    Ported from doAllGraphs() in w_graph.c.
    Called when census data changes.
    :param context:
    """
    # global all_max

    # Calculate scaling for population graphs (residential, commercial, industrial)
    context.all_max = max(
        context.res_his_max, context.com_his__max, context.ind_his_max
    )
    if context.all_max <= 128:
        context.all_max = 0

    scale_value = 128.0 / context.all_max if context.all_max else 1.0

    # Scale 10-year view data
    draw_month(context.res_his, context.history_10[RES_HIST], scale_value)
    draw_month(context.com_his, context.history_10[COM_HIST], scale_value)
    draw_month(context.ind_his, context.history_10[IND_HIST], scale_value)

    # Money, crime, pollution don't get scaled
    draw_month(context.money_his, context.history_10[MONEY_HIST], 1.0)
    draw_month(context.crime_his, context.history_10[CRIME_HIST], 1.0)
    draw_month(context.pollution_his, context.history_10[POLLUTION_HIST], 1.0)

    # Calculate scaling for 120-year view
    context.all_max = max(
        context.res_2_his_max, context.com_2_his_max, context.ind_2_his_max
    )
    if context.all_max <= 128:
        context.all_max = 0

    scale_value = 128.0 / context.all_max if context.all_max else 1.0

    # Scale 120-year view data (using months 120-239 from history)
    res_120 = (
        context.res_his[120:240]
        if len(context.res_his) > 240
        else context.res_his[120:]
    )
    com_120 = (
        context.com_his[120:240]
        if len(context.com_his) > 240
        else context.com_his[120:]
    )
    ind_120 = (
        context.ind_his[120:240]
        if len(context.ind_his) > 240
        else context.ind_his[120:]
    )

    # Pad with zeros if necessary
    res_120.extend([0] * (120 - len(res_120)))
    com_120.extend([0] * (120 - len(com_120)))
    ind_120.extend([0] * (120 - len(ind_120)))

    draw_month(res_120, context.history_120[RES_HIST], scale_value)
    draw_month(com_120, context.history_120[COM_HIST], scale_value)
    draw_month(ind_120, context.history_120[IND_HIST], scale_value)

    # Money, crime, pollution for 120-year view
    money_120 = (
        context.money_his[120:240]
        if len(context.money_his) > 240
        else context.money_his[120:]
    )
    crime_120 = (
        context.crime_his[120:240]
        if len(context.crime_his) > 240
        else context.crime_his[120:]
    )
    pollution_120 = (
        context.pollution_his[120:240]
        if len(context.pollution_his) > 240
        else context.pollution_his[120:]
    )

    money_120.extend([0] * (120 - len(money_120)))
    crime_120.extend([0] * (120 - len(crime_120)))
    pollution_120.extend([0] * (120 - len(pollution_120)))

    draw_month(money_120, context.history_120[MONEY_HIST], 1.0)
    draw_month(crime_120, context.history_120[CRIME_HIST], 1.0)
    draw_month(pollution_120, context.history_120[POLLUTION_HIST], 1.0)


# ============================================================================
# Graph Rendering (Adapted for pygame)
# ============================================================================


def update_graph(context: AppContext, graph: SimGraph) -> None:
    """
    Update and render a graph.

    Ported from DoUpdateGraph() in w_graph.c.
    Adapted for pygame rendering.

    Args:
        graph: Graph instance to update
        :param context:
    """
    if not graph.visible or graph.surface is None:
        return

    # Clear surface
    graph.surface.fill((176, 176, 176))  # Light gray background

    width = graph.w_width
    height = graph.w_height

    # Border calculations
    border = 5
    plot_x = border
    plot_y = border
    plot_width = width - 2 * border
    plot_height = height - 2 * border

    if plot_width < 1:
        plot_width = 1
    if plot_height < 1:
        plot_height = 1

    # Select history data based on range. Prefer context-provided history
    # arrays but fall back to module-level `history_10`/`history_120` so
    # tests that set module globals directly continue to work.
    if graph.range == 10:
        hist_data = getattr(
            context,
            "history_10",
            globals().get("history_10", [[0] * 120 for _ in range(HISTORIES)]),
        )
    else:
        hist_data = getattr(
            context,
            "history_120",
            globals().get("history_120", [[0] * 120 for _ in range(HISTORIES)]),
        )

    # Calculate scaling
    sx = plot_width / 120.0
    sy = plot_height / 256.0

    # Draw each history line
    mask = graph.mask
    for i in range(HISTORIES):
        if mask & (1 << i):
            color = HIST_COLORS[i]
            points = []

            # Generate line points
            for j in range(120):
                x = plot_x + int(j * sx)
                # Access history values defensively: some tests may provide
                # shorter lists so default to 0 when index out of range.
                val = (
                    hist_data[i][j]
                    if (i < len(hist_data) and j < len(hist_data[i]))
                    else 0
                )
                y = plot_y + int(plot_height - (val * sy))
                points.append((x, y))

            # Draw the line
            if len(points) > 1:
                pygame.draw.lines(graph.surface, color, False, points, 2)

            # Draw history label on the right
            if len(points) > 0:
                label_x = plot_x + plot_width + 4
                label_y = points[-1][1] + 5

                # Create label surface
                font = pygame.font.SysFont(None, 16)
                label_surface = font.render(HIST_NAMES[i], True, (0, 0, 0))
                graph.surface.blit(label_surface, (label_x, label_y))

    # Draw axes
    axis_color = (0, 0, 0)

    # Horizontal axis
    pygame.draw.line(
        graph.surface, axis_color, (plot_x, plot_y), (plot_x + plot_width, plot_y), 1
    )
    pygame.draw.line(
        graph.surface,
        axis_color,
        (plot_x, plot_y + plot_height),
        (plot_x + plot_width, plot_y + plot_height),
        1,
    )

    # Vertical grid lines (time markers)
    current_year = (context.city_time // 48) + context.starting_year
    current_month = (context.city_time // 4) % 12

    if graph.range == 10:
        # 10-year view: mark every 12 months (1 year)
        for x in range(120 - current_month, -1, -12):
            if x >= 0:
                line_x = plot_x + int(x * sx)
                pygame.draw.line(
                    graph.surface,
                    axis_color,
                    (line_x, plot_y),
                    (line_x, plot_y + plot_height),
                    1,
                )
    else:
        # 120-year view: mark every 120 months (10 years)
        year_marker = 10 * (current_year % 10)
        for x in range(1200 - year_marker, -1, -120):
            if x >= 0:
                line_x = plot_x + int((x / 10) * sx)  # Adjust for 10x scaling
                pygame.draw.line(
                    graph.surface,
                    axis_color,
                    (line_x, plot_y),
                    (line_x, plot_y + plot_height),
                    1,
                )

    graph.needs_redraw = False


def update_all_graphs(context: AppContext) -> None:
    """
    Update all graph instances.

    Ported from graphDoer() in w_graph.c.
    Called from main game loop.
    :param context:
    """
    # global new_graph

    census_changed = getattr(context, "census_changed", 0)
    # Also check legacy module-level types.census_changed when present.
    if not census_changed:
        import sys

        for mname, mobj in list(sys.modules.items()):
            if mname.endswith(".types") and hasattr(mobj, "census_changed"):
                try:
                    if getattr(mobj, "census_changed"):
                        census_changed = getattr(mobj, "census_changed")
                        break
                except Exception:
                    continue

    if census_changed:
        do_all_graphs(context)
        context.new_graph = True
        # reset both context and any legacy module flag we found
        try:
            context.census_changed = 0
        except Exception:
            pass
        try:
            import sys

            for mname, mobj in list(sys.modules.items()):
                if mname.endswith(".types") and hasattr(mobj, "census_changed"):
                    try:
                        setattr(mobj, "census_changed", 0)
                    except Exception:
                        continue
        except Exception:
            pass

    if context.new_graph:
        for graph in _graphs:
            graph.needs_redraw = True
        context.new_graph = False


# ============================================================================
# Graph Data Access Functions
# ============================================================================


def get_history_data(
    context: AppContext, range_type: int, history_type: int
) -> list[int]:
    """
    Get history data for a specific range and type.

    Args:
        range_type: 10 or 120 (year range)
        history_type: History type index (0-5)

    Returns:
        List of 120 data points
        :param context:
    """
    if range_type == 10:
        return (
            context.history_10[history_type].copy()
            if history_type < len(context.history_10)
            else []
        )
    elif range_type == 120:
        return (
            context.history_120[history_type].copy()
            if history_type < len(context.history_120)
            else []
        )
    else:
        return []


def get_history_names() -> list[str]:
    """
    Get list of history names.

    Returns:
        List of history type names
    """
    return HIST_NAMES.copy()


def get_history_colors() -> list[tuple]:
    """
    Get list of history colors.

    Returns:
        List of RGB color tuples
    """
    return HIST_COLORS.copy()


# ============================================================================
# Initialization
# ============================================================================


def initialize_graphs(context: AppContext) -> None:
    """
    Initialize the graph system.

    Ported from initGraphs() in w_graph.c.
    Called during game initialization.
    :param context:
    """
    for graph in _graphs:
        graph.range = 10
        graph.mask = ALL_HISTORIES

    init_history_data(context)
    init_graph_maxima(context)
