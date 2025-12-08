"""Tool palette panel implementation for the pygame UI stack.

This panel provides a visual tool selector displaying all 21 tools with:
- Icon display for each tool
- Tool cost display
- Tooltip with tool name and description
- Selection synchronization with sim_control
- Sound effects on tool selection
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from micropolis.constants import (
    DOZE_STATE,
    CostOf,
    airportState,
    chalkState,
    commercialState,
    eraserState,
    fireState,
    industrialState,
    networkState,
    nuclearState,
    parkState,
    policeState,
    powerState,
    queryState,
    residentialState,
    roadState,
    rrState,
    seaportState,
    stadiumState,
    wireState,
)
from micropolis.context import AppContext
from micropolis.ui.event_bus import EventBus, get_default_event_bus
from micropolis.ui.uipanel import UIPanel
from micropolis.ui.widgets import PaletteGrid, PaletteItem

if TYPE_CHECKING:
    from micropolis.ui.panel_manager import PanelManager

try:
    import pygame

    _HAVE_PYGAME = True
except Exception:  # pragma: no cover - pygame optional in tests
    pygame = None  # type: ignore
    _HAVE_PYGAME = False


# Tool metadata: (state_id, name, tooltip, icon_name)
_TOOL_DEFINITIONS = [
    (
        residentialState,
        "Residential",
        "Build residential zones where citizens can live",
        "tool_residential",
    ),
    (
        commercialState,
        "Commercial",
        "Build commercial zones for shops and businesses",
        "tool_commercial",
    ),
    (
        industrialState,
        "Industrial",
        "Build industrial zones for factories",
        "tool_industrial",
    ),
    (fireState, "Fire Dept", "Build a fire station to fight fires", "tool_fire"),
    (queryState, "Query", "Get information about a zone", "tool_query"),
    (
        policeState,
        "Police Dept",
        "Build a police station to fight crime",
        "tool_police",
    ),
    (wireState, "Power Lines", "Build power lines to connect buildings", "tool_wire"),
    (DOZE_STATE, "Bulldozer", "Clear land and demolish buildings", "tool_bulldozer"),
    (rrState, "Rail", "Build rail lines for transportation", "tool_rail"),
    (roadState, "Road", "Build roads to connect zones", "tool_road"),
    (chalkState, "Chalk", "Draw annotations on the map", "tool_chalk"),
    (eraserState, "Eraser", "Erase chalk annotations", "tool_eraser"),
    (stadiumState, "Stadium", "Build a stadium for entertainment", "tool_stadium"),
    (parkState, "Park", "Build parks to increase land value", "tool_park"),
    (seaportState, "Seaport", "Build a seaport for cargo shipping", "tool_seaport"),
    (
        powerState,
        "Coal Plant",
        "Build a coal power plant to generate electricity",
        "tool_coal",
    ),
    (
        nuclearState,
        "Nuclear Plant",
        "Build a nuclear power plant (high output, meltdown risk)",
        "tool_nuclear",
    ),
    (airportState, "Airport", "Build an airport for air travel", "tool_airport"),
    (
        networkState,
        "Network",
        "Build telecommunications infrastructure",
        "tool_network",
    ),
]


class ToolPalettePanel(UIPanel):
    """Tool palette panel displaying all available tools."""

    def __init__(self, manager: PanelManager, context: AppContext) -> None:
        super().__init__(manager, context)
        self.panel_id = "tool_palette"
        self.legacy_name = "ToolPalette"

        # Create palette items from tool definitions
        self._palette_items: list[PaletteItem] = []
        for state_id, name, tooltip, icon in _TOOL_DEFINITIONS:
            cost = CostOf[state_id] if state_id < len(CostOf) else 0
            cost_str = f"${cost}" if cost > 0 else "Free"
            item = PaletteItem(
                item_id=f"tool_{state_id}",
                label=f"{name}\n{cost_str}",
                icon=icon,
                tooltip=f"{name}: {tooltip}\nCost: {cost_str}",
                enabled=True,
            )
            self._palette_items.append(item)

        # Create the palette grid widget
        self._palette_grid: PaletteGrid | None = None
        self._current_tool_state: int | None = None

        # Event bus subscription
        self._event_bus: EventBus = get_default_event_bus()
        self._subscriptions: list[Any] = []

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------
    def did_mount(self) -> None:
        """Initialize the tool palette panel after mounting."""
        # Subscribe to tool change events
        self._subscriptions.append(
            self._event_bus.subscribe("tool.changed", self._on_tool_changed)
        )
        self._subscriptions.append(
            self._event_bus.subscribe("funds.updated", self._on_funds_updated)
        )

        # Initialize the palette grid
        self._init_palette_grid()

        # Set initial tool selection
        if self.context.sim:
            initial_tool = getattr(
                self.context.sim, "current_tool_state", residentialState
            )
            self._update_selection(initial_tool)

    def did_unmount(self) -> None:
        """Clean up when panel is removed."""
        for sub in self._subscriptions:
            self._event_bus.unsubscribe(sub)
        self._subscriptions.clear()
        self._palette_grid = None

    def did_resize(self, size: tuple[int, int]) -> None:
        """Update widget layout when window resizes."""
        if self._palette_grid:
            # Recalculate palette position/size
            self._init_palette_grid()
        self.invalidate()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def draw(self, surface: Any) -> None:
        """Render the tool palette."""
        if not _HAVE_PYGAME or not self.visible:
            return

        if self._palette_grid is None:
            self._init_palette_grid()

        x, y, w, h = self.rect

        # Draw background panel
        pygame.draw.rect(surface, (50, 50, 55), (x, y, w, h))  # type: ignore
        pygame.draw.rect(surface, (80, 80, 85), (x, y, w, h), 2)  # type: ignore

        # Draw title
        if _HAVE_PYGAME:
            font = pygame.font.SysFont("dejavusans", 14, bold=True)  # type: ignore
            title_text = font.render("Tools", True, (200, 200, 200))
            surface.blit(title_text, (x + 10, y + 8))

        # Render the palette grid
        if self._palette_grid:
            from micropolis.ui.widgets.renderer import RecordingRenderer

            renderer = RecordingRenderer()
            self._palette_grid.on_render(renderer)

            # Execute rendering commands
            for cmd in renderer.commands:
                if cmd.name == "rect":
                    rect = cmd.payload["rect"]
                    color = cmd.payload["color"]
                    pygame.draw.rect(surface, color, rect)  # type: ignore
                    if cmd.payload.get("border") and cmd.payload.get("border_color"):
                        pygame.draw.rect(  # type: ignore
                            surface, cmd.payload["border_color"], rect, 1
                        )
                elif cmd.name == "text":
                    font = pygame.font.SysFont(  # type: ignore
                        cmd.payload.get("font") or "dejavusans", 10
                    )
                    lines = cmd.payload["text"].split("\n")
                    for i, line in enumerate(lines):
                        text_surf = font.render(line, True, cmd.payload["color"])
                        text_rect = text_surf.get_rect(
                            center=(
                                cmd.payload["position"][0],
                                cmd.payload["position"][1] + i * 12,
                            )
                        )
                        surface.blit(text_surf, text_rect)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def handle_panel_event(self, event: Any) -> bool:
        """Handle pygame events for palette interaction."""
        if not _HAVE_PYGAME or not self.enabled or not self._palette_grid:
            return False

        # Convert pygame event to UIEvent
        ui_event = self._pygame_to_ui_event(event)
        if ui_event and self._palette_grid.on_event(ui_event):
            return True

        return False

    def _pygame_to_ui_event(self, event: Any) -> Any:
        """Convert pygame event to UIEvent format."""
        if not _HAVE_PYGAME:
            return None

        from micropolis.ui.widgets.base import UIEvent

        if event.type == pygame.MOUSEMOTION:  # type: ignore
            return UIEvent(type="mouse_move", position=event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:  # type: ignore
            return UIEvent(type="mouse_down", button=event.button, position=event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:  # type: ignore
            return UIEvent(type="mouse_up", button=event.button, position=event.pos)

        return None

    # ------------------------------------------------------------------
    # Palette management
    # ------------------------------------------------------------------
    def _init_palette_grid(self) -> None:
        """Initialize or reinitialize the palette grid widget."""
        if not _HAVE_PYGAME:
            return

        x, y, w, h = self.rect

        # Calculate grid layout (4 columns, 5 rows for 19 tools)
        columns = 4
        item_width = 56
        item_height = 56
        gap = 8
        padding = 10
        title_height = 30

        grid_x = x + padding
        grid_y = y + title_height
        grid_w = (item_width + gap) * columns - gap
        grid_h = h - title_height - padding * 2

        self._palette_grid = PaletteGrid(
            widget_id="tool_palette_grid",
            rect=(grid_x, grid_y, grid_w, grid_h),
            items=self._palette_items,
            columns=columns,
            item_size=(item_width, item_height),
            gap=gap,
            on_select=self._on_tool_selected,
        )

        # Set initial selection if we have a current tool
        if self._current_tool_state is not None:
            self._palette_grid.selected_id = f"tool_{self._current_tool_state}"

    def _on_tool_selected(self, item: PaletteItem) -> None:
        """Handle tool selection from the palette."""
        # Extract tool state from item ID
        tool_state = int(item.item_id.split("_")[1])

        # Check if player has enough funds
        cost = CostOf[tool_state] if tool_state < len(CostOf) else 0
        if cost > 0 and self.context.total_funds < cost:
            # Play error sound
            self._play_sound("edit", "Sorry")
            # Could show a message here
            return

        # Update the tool state
        self._set_tool_state(tool_state)

        # Play selection sound
        self._play_sound("edit", "Click")

    def _set_tool_state(self, tool_state: int) -> None:
        """Set the current tool state in the simulation."""
        self._current_tool_state = tool_state

        # Update context
        if hasattr(self.context, "current_tool_state"):
            self.context.current_tool_state = tool_state

        # Update sim if available
        if self.context.sim and hasattr(self.context.sim, "current_tool_state"):
            self.context.sim.current_tool_state = tool_state

        # Publish tool change event
        self._event_bus.publish("tool.changed", {"tool_state": tool_state})

        # Update palette selection
        if self._palette_grid:
            self._palette_grid.selected_id = f"tool_{tool_state}"
            self.invalidate()

    def _update_selection(self, tool_state: int) -> None:
        """Update the visual selection without triggering callbacks."""
        self._current_tool_state = tool_state
        if self._palette_grid:
            self._palette_grid.selected_id = f"tool_{tool_state}"
            self.invalidate()

    # ------------------------------------------------------------------
    # Event bus callbacks
    # ------------------------------------------------------------------
    def _on_tool_changed(self, data: Any) -> None:
        """Handle external tool change events."""
        if not self.visible:
            return

        tool_state = data.get("tool_state")
        if tool_state is not None and tool_state != self._current_tool_state:
            self._update_selection(tool_state)

    def _on_funds_updated(self, data: Any) -> None:
        """Handle fund updates to enable/disable expensive tools."""
        if not self.visible:
            return

        # Update tool affordability
        total_funds = self.context.total_funds
        for item in self._palette_items:
            tool_state = int(item.item_id.split("_")[1])
            cost = CostOf[tool_state] if tool_state < len(CostOf) else 0
            item.enabled = cost == 0 or total_funds >= cost

        self.invalidate()

    # ------------------------------------------------------------------
    # Audio helpers
    # ------------------------------------------------------------------
    def _play_sound(self, channel: str, sound_name: str) -> None:
        """Play a sound effect."""
        try:
            from micropolis.ui.asset_service import get_default_asset_service

            asset_service = get_default_asset_service()
            if asset_service:
                asset_service.play_sound(channel, sound_name)
        except Exception:
            # Silently fail if audio not available
            pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_current_tool(self) -> int | None:
        """Get the currently selected tool state."""
        return self._current_tool_state

    def set_tool(self, tool_state: int) -> None:
        """Programmatically set the current tool."""
        self._set_tool_state(tool_state)


__all__ = ["ToolPalettePanel"]
