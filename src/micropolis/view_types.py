"""
view_types.py - View and display structures for Micropolis Python port

This module contains view-related data structures and constants ported from view.h,
adapted for pygame graphics instead of X11/TCL-Tk.
"""

from dataclasses import dataclass
from typing import Any, Callable

from src.micropolis.context import AppContext

# Re-export context-defined view constants so other modules can import them here.
Editor_Class = AppContext.Editor_Class
Map_Class = AppContext.Map_Class
X_Mem_View = AppContext.X_Mem_View
X_Wire_View = AppContext.X_Wire_View


# ============================================================================
# View Constants
# ============================================================================


# ============================================================================
# Data Structure Classes
# ============================================================================


@dataclass
class Ink:
    """Ink structure for drawing operations"""

    next: "Ink|None" = None
    x: int = 0
    y: int = 0
    color: int = 0
    length: int = 0
    maxlength: int = 0
    points: list[Any] | None = None  # XPoint equivalent for pygame
    left: int = 0
    top: int = 0
    right: int = 0
    bottom: int = 0
    last_x: int = 0
    last_y: int = 0


@dataclass
class XDisplay:
    """Display structure adapted for pygame (originally X11)"""

    next: "XDisplay|None" = None
    references: int = 0
    display: str = ""
    tkDisplay: Any | None = None  # TK display (not used in pygame)
    dpy: Any | None = None  # X11 display (not used in pygame)
    screen: Any | None = None  # X11 screen (not used in pygame)
    root: Any | None = None  # X11 root window (not used in pygame)
    visual: Any | None = None  # X11 visual (not used in pygame)
    depth: int = 0
    color: int = 0
    colormap: Any | None = None  # X11 colormap (not used in pygame)
    pixels: list[int] | None = None
    gc: Any | None = None  # X11 graphics context (not used in pygame)
    shared: int = 0
    last_request_read: int = 0
    request: int = 0
    big_tile_image: Any | None = None  # X11 image (replaced with pygame surface)
    small_tile_image: Any | None = None  # X11 image (replaced with pygame surface)
    big_tile_pixmap: Any | None = None  # X11 pixmap (replaced with pygame surface)
    objects: list[list[Any] | None] | None = (
        None  # X11 pixmaps (replaced with pygame surfaces)
    )
    overlay_gc: Any | None = None  # X11 graphics context (not used in pygame)
    gray25_stipple: Any | None = None  # X11 stipple (replaced with pygame surface)
    gray50_stipple: Any | None = None  # X11 stipple (replaced with pygame surface)
    gray75_stipple: Any | None = None  # X11 stipple (replaced with pygame surface)
    vert_stipple: Any | None = None  # X11 stipple (replaced with pygame surface)
    horiz_stipple: Any | None = None  # X11 stipple (replaced with pygame surface)
    diag_stipple: Any | None = None  # X11 stipple (replaced with pygame surface)


@dataclass
class SimGraph:
    """Graph display structure"""

    next: "SimGraph|None" = None
    range: int = 0
    mask: int = 0
    tkwin: Any | None = None  # TK window (replaced with pygame surface)
    interp: Any | None = None  # TCL interpreter (not used in pygame)
    flags: int = 0
    x: XDisplay | None = None
    visible: bool = False
    w_x: int = 0
    w_y: int = 0
    w_width: int = 0
    w_height: int = 0
    pixmap: Any | None = None  # X11 pixmap (replaced with pygame surface)
    pixels: list[int] | None = None
    fontPtr: Any | None = None  # X11 font (replaced with pygame font)
    border: Any | None = None  # TK border (not used in pygame)
    borderWidth: int = 0
    relief: int = 0
    draw_graph_token: Any | None = None  # TK timer token (replaced with pygame timer)


@dataclass
class SimDate:
    """Date display structure"""

    next: "SimDate|None" = None
    reset: int = 0
    month: int = 0
    year: int = 0
    lastmonth: int = 0
    lastyear: int = 0
    tkwin: Any | None = None  # TK window (replaced with pygame surface)
    interp: Any | None = None  # TCL interpreter (not used in pygame)
    flags: int = 0
    x: XDisplay | None = None
    visible: bool = False
    w_x: int = 0
    w_y: int = 0
    w_width: int = 0
    w_height: int = 0
    pixmap: Any | None = None  # X11 pixmap (replaced with pygame surface)
    pixels: list[int] | None = None
    fontPtr: Any | None = None  # X11 font (replaced with pygame font)
    border: Any | None = None  # TK border (not used in pygame)
    borderWidth: int = 0
    padX: int = 0
    padY: int = 0
    width: int = 0
    monthTab: int = 0
    monthTabX: int = 0
    yearTab: int = 0
    yearTabX: int = 0
    draw_date_token: Any | None = None  # TK timer token (replaced with pygame timer)


@dataclass
class Person:
    """Person structure"""

    id: int = 0
    name: str = ""


@dataclass
class Cmd:
    """Command structure"""

    name: str = ""
    cmd: Callable[[], int] | None = None


# ============================================================================
# Extended Sim Structure (from view.h)
# ============================================================================


@dataclass
class SimExtended:
    """Extended Sim structure with additional view components from view.h"""

    # Basic counts and pointers (from original Sim in types.py)
    editors: int = 0
    editor: list[Any] | None = None  # SimView
    maps: int = 0
    map: list[Any] | None = None  # SimView
    graphs: int = 0
    graph: list[SimGraph] | None = None
    dates: int = 0
    date: list[SimDate] | None = None
    sprites: int = 0
    sprite: list[Any] | None = None  # SimSprite
    # Camera support (conditional in original)
    scams: int = 0
    scam: Any | None = None  # SimCam (placeholder)

    # Overlay/ink system
    overlay: Ink | None = None


# ============================================================================
# Utility Functions
# ============================================================================


def MakeNewInk() -> Ink:
    """Create a new ink instance"""
    return Ink()


def MakeNewXDisplay() -> XDisplay:
    """Create a new display instance"""
    return XDisplay()


def MakeNewSimGraph() -> SimGraph:
    """Create a new graph instance"""
    return SimGraph()


def MakeNewSimDate() -> SimDate:
    """Create a new date display instance"""
    return SimDate()


def MakeNewPerson() -> Person:
    """Create a new person instance"""
    return Person()


def MakeNewCmd() -> Cmd:
    """Create a new command instance"""
    return Cmd()


def MakeNewSimExtended() -> SimExtended:
    """Create a new extended simulation instance"""
    return SimExtended()


# ============================================================================
# View Management Functions (placeholders for pygame integration)
# ============================================================================


def ViewRedrawPending(context: AppContext, view: Any) -> bool:
    """Check if view needs redrawing"""
    return bool(view.flags & context.VIEW_REDRAW_PENDING)


def SetViewRedrawPending(context: AppContext, view: Any, pending: bool = True) -> None:
    """Set view redraw pending flag"""
    if pending:
        view.flags |= context.VIEW_REDRAW_PENDING
    else:
        view.flags &= ~context.VIEW_REDRAW_PENDING


def GetViewClass(context: AppContext, view: Any) -> int:
    """Get view class (Editor or Map)"""
    return getattr(view, "class_id", 0)


def IsEditorView(context: AppContext, view: Any) -> bool:
    """Check if view is an editor view"""
    return GetViewClass(context, view) == context.Editor_Class


def IsMapView(context: AppContext, view: Any) -> bool:
    """Check if view is a map view"""
    return GetViewClass(context, view) == context.Map_Class


# ============================================================================
# Pygame Integration Helpers
# ============================================================================


def UpdateViewDisplay(view: Any) -> None:
    """Update pygame display for a view (placeholder)"""
    # This will be implemented when pygame graphics are added
    pass


def HandleViewEvent(view: Any, event: Any) -> bool:
    """Handle pygame event for a view (placeholder)"""
    # This will be implemented when pygame event handling is added
    return False


def DrawViewOverlay(view: Any) -> None:
    """Draw overlay on view (placeholder)"""
    # This will be implemented when overlay rendering is added
    pass
