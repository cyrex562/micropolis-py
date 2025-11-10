"""
graphs.py - Graph display system for Micropolis Python port

This module implements the graph display system ported from w_graph.c,
responsible for displaying historical data graphs for population, money,
pollution, crime, and other city statistics.
"""

from typing import List, Optional
import pygame
from . import types

# ============================================================================
# Graph History Data
# ============================================================================

# History data arrays (120 months of data)
History10: List[List[int]] = []  # 10-year view (120 months)
History120: List[List[int]] = []  # 120-year view (120 months)
HistoryInitialized: bool = False

# Graph scaling variables
AllMax: int = 0
Graph10Max: int = 0
Graph120Max: int = 0

# Graph update flags
NewGraph: bool = False

# ============================================================================
# Graph Configuration Constants
# ============================================================================

# History names and colors (for pygame rendering)
HIST_NAMES = [
    "Residential", "Commercial", "Industrial",
    "Cash Flow", "Crime", "Pollution"
]

HIST_COLORS = [
    (144, 238, 144),  # Light green for residential
    (0, 0, 139),      # Dark blue for commercial
    (255, 255, 0),    # Yellow for industrial
    (0, 100, 0),      # Dark green for cash flow
    (255, 0, 0),      # Red for crime
    (128, 128, 0),    # Olive for pollution
]

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
        self.mask: int = types.ALL_HISTORIES  # Which histories to show
        self.visible: bool = False
        self.w_x: int = 0
        self.w_y: int = 0
        self.w_width: int = 0
        self.w_height: int = 0

        # Pygame-specific attributes
        self.surface: Optional[pygame.Surface] = None
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
        self.mask = mask & types.ALL_HISTORIES
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
_graphs: List[SimGraph] = []

def create_graph() -> SimGraph:
    """
    Create a new graph instance.

    Returns:
        New SimGraph instance
    """
    graph = SimGraph()
    _graphs.append(graph)
    return graph

def get_graphs() -> List[SimGraph]:
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
# History Data Management
# ============================================================================

def init_history_data() -> None:
    """
    Initialize history data arrays.

    Ported from initGraphs() in w_graph.c.
    Called during game initialization.
    """
    global History10, History120, HistoryInitialized

    if not HistoryInitialized:
        HistoryInitialized = True
        History10 = [[0] * 120 for _ in range(types.HISTORIES)]
        History120 = [[0] * 120 for _ in range(types.HISTORIES)]

def init_graph_maxima() -> None:
    """
    Initialize graph scaling maxima.

    Ported from InitGraphMax() in w_graph.c.
    Called during game initialization.
    """
    global Graph10Max, Graph120Max

    # Initialize maxima for 10-year view (last 120 months)
    types.ResHisMax = 0
    types.ComHisMax = 0
    types.IndHisMax = 0

    for x in range(119, -1, -1):
        if x < len(types.ResHis) and types.ResHis[x] > types.ResHisMax:
            types.ResHisMax = types.ResHis[x]
        if x < len(types.ComHis) and types.ComHis[x] > types.ComHisMax:
            types.ComHisMax = types.ComHis[x]
        if x < len(types.IndHis) and types.IndHis[x] > types.IndHisMax:
            types.IndHisMax = types.IndHis[x]

        # Ensure non-negative values
        if x < len(types.ResHis) and types.ResHis[x] < 0:
            types.ResHis[x] = 0
        if x < len(types.ComHis) and types.ComHis[x] < 0:
            types.ComHis[x] = 0
        if x < len(types.IndHis) and types.IndHis[x] < 0:
            types.IndHis[x] = 0

    Graph10Max = max(types.ResHisMax, types.ComHisMax, types.IndHisMax)

    # Initialize maxima for 120-year view (months 120-239)
    types.Res2HisMax = 0
    types.Com2HisMax = 0
    types.Ind2HisMax = 0

    for x in range(239, 119, -1):
        if x < len(types.ResHis) and types.ResHis[x] > types.Res2HisMax:
            types.Res2HisMax = types.ResHis[x]
        if x < len(types.ComHis) and types.ComHis[x] > types.Com2HisMax:
            types.Com2HisMax = types.ComHis[x]
        if x < len(types.IndHis) and types.IndHis[x] > types.Ind2HisMax:
            types.Ind2HisMax = types.IndHis[x]

        # Ensure non-negative values
        if x < len(types.ResHis) and types.ResHis[x] < 0:
            types.ResHis[x] = 0
        if x < len(types.ComHis) and types.ComHis[x] < 0:
            types.ComHis[x] = 0
        if x < len(types.IndHis) and types.IndHis[x] < 0:
            types.IndHis[x] = 0

    Graph120Max = max(types.Res2HisMax, types.Com2HisMax, types.Ind2HisMax)

def draw_month(hist: List[int], dest: List[int], scale: float) -> None:
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

def do_all_graphs() -> None:
    """
    Update all graph history data.

    Ported from doAllGraphs() in w_graph.c.
    Called when census data changes.
    """
    global AllMax

    # Calculate scaling for population graphs (residential, commercial, industrial)
    AllMax = max(types.ResHisMax, types.ComHisMax, types.IndHisMax)
    if AllMax <= 128:
        AllMax = 0

    scale_value = 128.0 / AllMax if AllMax else 1.0

    # Scale 10-year view data
    draw_month(types.ResHis, History10[types.RES_HIST], scale_value)
    draw_month(types.ComHis, History10[types.COM_HIST], scale_value)
    draw_month(types.IndHis, History10[types.IND_HIST], scale_value)

    # Money, crime, pollution don't get scaled
    draw_month(types.MoneyHis, History10[types.MONEY_HIST], 1.0)
    draw_month(types.CrimeHis, History10[types.CRIME_HIST], 1.0)
    draw_month(types.PollutionHis, History10[types.POLLUTION_HIST], 1.0)

    # Calculate scaling for 120-year view
    AllMax = max(types.Res2HisMax, types.Com2HisMax, types.Ind2HisMax)
    if AllMax <= 128:
        AllMax = 0

    scale_value = 128.0 / AllMax if AllMax else 1.0

    # Scale 120-year view data (using months 120-239 from history)
    res_120 = types.ResHis[120:240] if len(types.ResHis) > 240 else types.ResHis[120:]
    com_120 = types.ComHis[120:240] if len(types.ComHis) > 240 else types.ComHis[120:]
    ind_120 = types.IndHis[120:240] if len(types.IndHis) > 240 else types.IndHis[120:]

    # Pad with zeros if necessary
    res_120.extend([0] * (120 - len(res_120)))
    com_120.extend([0] * (120 - len(com_120)))
    ind_120.extend([0] * (120 - len(ind_120)))

    draw_month(res_120, History120[types.RES_HIST], scale_value)
    draw_month(com_120, History120[types.COM_HIST], scale_value)
    draw_month(ind_120, History120[types.IND_HIST], scale_value)

    # Money, crime, pollution for 120-year view
    money_120 = types.MoneyHis[120:240] if len(types.MoneyHis) > 240 else types.MoneyHis[120:]
    crime_120 = types.CrimeHis[120:240] if len(types.CrimeHis) > 240 else types.CrimeHis[120:]
    pollution_120 = types.PollutionHis[120:240] if len(types.PollutionHis) > 240 else types.PollutionHis[120:]

    money_120.extend([0] * (120 - len(money_120)))
    crime_120.extend([0] * (120 - len(crime_120)))
    pollution_120.extend([0] * (120 - len(pollution_120)))

    draw_month(money_120, History120[types.MONEY_HIST], 1.0)
    draw_month(crime_120, History120[types.CRIME_HIST], 1.0)
    draw_month(pollution_120, History120[types.POLLUTION_HIST], 1.0)

# ============================================================================
# Graph Rendering (Adapted for pygame)
# ============================================================================

def update_graph(graph: SimGraph) -> None:
    """
    Update and render a graph.

    Ported from DoUpdateGraph() in w_graph.c.
    Adapted for pygame rendering.

    Args:
        graph: Graph instance to update
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

    # Select history data based on range
    hist_data = History10 if graph.range == 10 else History120

    # Calculate scaling
    sx = plot_width / 120.0
    sy = plot_height / 256.0

    # Draw each history line
    mask = graph.mask
    for i in range(types.HISTORIES):
        if mask & (1 << i):
            color = HIST_COLORS[i]
            points = []

            # Generate line points
            for j in range(120):
                x = plot_x + int(j * sx)
                y = plot_y + int(plot_height - (hist_data[i][j] * sy))
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
    pygame.draw.line(graph.surface, axis_color,
                    (plot_x, plot_y),
                    (plot_x + plot_width, plot_y), 1)
    pygame.draw.line(graph.surface, axis_color,
                    (plot_x, plot_y + plot_height),
                    (plot_x + plot_width, plot_y + plot_height), 1)

    # Vertical grid lines (time markers)
    current_year = (types.CityTime // 48) + types.StartingYear
    current_month = (types.CityTime // 4) % 12

    if graph.range == 10:
        # 10-year view: mark every 12 months (1 year)
        for x in range(120 - current_month, -1, -12):
            if x >= 0:
                line_x = plot_x + int(x * sx)
                pygame.draw.line(graph.surface, axis_color,
                               (line_x, plot_y), (line_x, plot_y + plot_height), 1)
    else:
        # 120-year view: mark every 120 months (10 years)
        year_marker = 10 * (current_year % 10)
        for x in range(1200 - year_marker, -1, -120):
            if x >= 0:
                line_x = plot_x + int((x / 10) * sx)  # Adjust for 10x scaling
                pygame.draw.line(graph.surface, axis_color,
                               (line_x, plot_y), (line_x, plot_y + plot_height), 1)

    graph.needs_redraw = False

def update_all_graphs() -> None:
    """
    Update all graph instances.

    Ported from graphDoer() in w_graph.c.
    Called from main game loop.
    """
    global NewGraph

    if types.CensusChanged:
        do_all_graphs()
        NewGraph = True
        types.CensusChanged = 0

    if NewGraph:
        for graph in _graphs:
            graph.needs_redraw = True
        NewGraph = False

# ============================================================================
# Graph Data Access Functions
# ============================================================================

def get_history_data(range_type: int, history_type: int) -> List[int]:
    """
    Get history data for a specific range and type.

    Args:
        range_type: 10 or 120 (year range)
        history_type: History type index (0-5)

    Returns:
        List of 120 data points
    """
    if range_type == 10:
        return History10[history_type].copy() if history_type < len(History10) else []
    elif range_type == 120:
        return History120[history_type].copy() if history_type < len(History120) else []
    else:
        return []

def get_history_names() -> List[str]:
    """
    Get list of history names.

    Returns:
        List of history type names
    """
    return HIST_NAMES.copy()

def get_history_colors() -> List[tuple]:
    """
    Get list of history colors.

    Returns:
        List of RGB color tuples
    """
    return HIST_COLORS.copy()

# ============================================================================
# Initialization
# ============================================================================

def initialize_graphs() -> None:
    """
    Initialize the graph system.

    Ported from initGraphs() in w_graph.c.
    Called during game initialization.
    """
    for graph in _graphs:
        graph.range = 10
        graph.mask = types.ALL_HISTORIES

    init_history_data()
    init_graph_maxima()