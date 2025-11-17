"""Panel manager for the pygame UI stack."""

from __future__ import annotations

import itertools
from collections import defaultdict
from collections.abc import Iterable
from typing import Any, Protocol, cast, runtime_checkable

from micropolis.context import AppContext

from .event_bus import EventBus, get_default_event_bus
from .timer_service import TimerService, get_default_timer_service


class PanelRegistrationError(ValueError):
    """Raised when a panel type cannot be registered."""


class PanelLookupError(KeyError):
    """Raised when an unknown panel identifier is requested."""


@runtime_checkable
class PanelProtocol(Protocol):
    """Lightweight protocol describing the expected panel surface API."""

    legacy_name: str
    panel_id: str

    def on_mount(self) -> None:
        """Panel lifecycle hook invoked after being added to the manager."""

    def on_unmount(self) -> None:
        """Panel lifecycle hook prior to removal."""

    def on_resize(self, size: tuple[int, int]) -> None:
        """Receive notifications whenever the root surface is resized."""

    def render(self, surface: Any) -> None:
        """Draw this panel onto the provided surface."""

    def handle_event(self, event: Any) -> bool:
        """Process an input/event payload; return True if consumed."""


class PanelFactory(Protocol):
    """Callable protocol for constructing panels."""

    def __call__(
        self,
        manager: PanelManager,
        context: AppContext,
        **factory_kwargs: Any,
    ) -> PanelProtocol: ...


class PanelManager:
    """Central coordinator for pygame UI panels.

    Responsibilities:
    - Register panel factories keyed by legacy window collection names
    - Create/destroy panels while tracking z-order and modal overlays
    - Dispatch events to the correct panel chain
    - Provide a snapshot of legacy window collections (HeadWindows, etc.)
    """

    def __init__(
        self,
        context: AppContext,
        surface: Any | None = None,
        event_bus: EventBus | None = None,
        timer_service: TimerService | None = None,
    ) -> None:
        self.context = context
        self._surface = surface
        self._registry: dict[str, PanelFactory] = {}
        self._panels: dict[str, PanelProtocol] = {}
        self._panels_by_type: dict[str, dict[str, PanelProtocol]] = defaultdict(dict)
        self._z_order: list[str] = []
        self._modal_stack: list[str] = []
        self._id_counter = itertools.count(1)
        self._size: tuple[int, int] = (0, 0)
        resolved_bus = event_bus or getattr(context, "event_bus", None)
        if resolved_bus is None:
            resolved_bus = get_default_event_bus()
        self._event_bus = resolved_bus
        # Attempt to expose the resolved bus on the context for other systems.
        if getattr(context, "event_bus", None) is None:
            try:
                object.__setattr__(context, "event_bus", resolved_bus)
            except Exception:
                pass
        resolved_timer = timer_service or getattr(context, "timer_service", None)
        if resolved_timer is None:
            resolved_timer = get_default_timer_service()
        self._timer_service = resolved_timer
        if getattr(context, "timer_service", None) is None:
            try:
                object.__setattr__(context, "timer_service", resolved_timer)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register_panel_type(
        self,
        legacy_name: str,
        factory: PanelFactory,
        *,
        replace: bool = False,
    ) -> None:
        """Register a factory for a legacy window collection."""

        if not legacy_name:
            raise PanelRegistrationError("legacy_name must be a non-empty string")
        normalized = legacy_name.strip()
        if normalized in self._registry and not replace:
            raise PanelRegistrationError(
                f"Panel type '{normalized}' already registered"
            )
        self._registry[normalized] = factory

    def unregister_panel_type(self, legacy_name: str) -> None:
        """Remove a previously registered factory (no active panels allowed)."""

        if self._panels_by_type.get(legacy_name):
            raise PanelRegistrationError(
                f"Cannot unregister '{legacy_name}' while panels are active"
            )
        self._registry.pop(legacy_name, None)

    # ------------------------------------------------------------------
    # Panel lifecycle
    # ------------------------------------------------------------------
    def create_panel(
        self,
        legacy_name: str,
        *,
        panel_id: str | None = None,
        factory: PanelFactory | None = None,
        **factory_kwargs: Any,
    ) -> PanelProtocol:
        """Instantiate a panel for the specified legacy collection."""

        factory_fn = factory or self._registry.get(legacy_name)
        if factory_fn is None:
            raise PanelRegistrationError(
                f"Panel type '{legacy_name}' is not registered"
            )

        panel_id = panel_id or self._generate_panel_id(legacy_name)
        if panel_id in self._panels:
            raise PanelRegistrationError(f"Panel id '{panel_id}' already exists")

        panel = factory_fn(self, self.context, **factory_kwargs)
        self._initialize_panel_metadata(panel, panel_id, legacy_name)
        self._panels[panel_id] = panel
        self._panels_by_type[legacy_name][panel_id] = panel
        self._z_order.append(panel_id)
        panel.on_mount()
        if self._size != (0, 0):
            panel.on_resize(self._size)
        return panel

    def destroy_panel(self, panel_id: str) -> None:
        panel = self._panels.pop(panel_id, None)
        if panel is None:
            raise PanelLookupError(panel_id)
        panel.on_unmount()
        self._z_order = [pid for pid in self._z_order if pid != panel_id]
        legacy_mapping = self._panels_by_type.get(panel.legacy_name)
        if legacy_mapping and panel_id in legacy_mapping:
            del legacy_mapping[panel_id]
            if not legacy_mapping:
                del self._panels_by_type[panel.legacy_name]
        if panel_id in self._modal_stack:
            self._modal_stack = [pid for pid in self._modal_stack if pid != panel_id]

    def get_panel(self, panel_id: str) -> PanelProtocol:
        try:
            return self._panels[panel_id]
        except KeyError as exc:
            raise PanelLookupError(panel_id) from exc

    def panels_for_type(self, legacy_name: str) -> Iterable[PanelProtocol]:
        return tuple(self._panels_by_type.get(legacy_name, {}).values())

    # ------------------------------------------------------------------
    # Z-order & modal helpers
    # ------------------------------------------------------------------
    def bring_to_front(self, panel_id: str) -> None:
        self._relocate_z_order(panel_id, to_front=True)

    def send_to_back(self, panel_id: str) -> None:
        self._relocate_z_order(panel_id, to_front=False)

    def set_modal(self, panel_id: str, *, modal: bool) -> None:
        if panel_id not in self._panels:
            raise PanelLookupError(panel_id)
        if modal:
            if panel_id not in self._modal_stack:
                self._modal_stack.append(panel_id)
                self.bring_to_front(panel_id)
        else:
            self._modal_stack = [pid for pid in self._modal_stack if pid != panel_id]

    # ------------------------------------------------------------------
    # Event + rendering
    # ------------------------------------------------------------------
    def handle_event(self, event: Any) -> bool:
        """Dispatch an event, respecting modal overlays and z-order."""

        if event is not None and getattr(self, "_event_bus", None) is not None:
            self._event_bus.publish_pygame_event(event, tags=("panel-manager",))
        targets = (
            self._modal_stack[-1:] if self._modal_stack else reversed(self._z_order)
        )
        for panel_id in targets:
            panel = self._panels.get(panel_id)
            if panel and self._panel_accepts_input(panel) and panel.handle_event(event):
                return True
        return False

    def render(self, surface: Any | None = None) -> None:
        target = surface or self._surface
        if target is None:
            raise RuntimeError("PanelManager.render requires a surface")
        for panel_id in self._z_order:
            panel = self._panels.get(panel_id)
            if panel and self._panel_is_visible(panel):
                panel.render(target)

    def attach_surface(self, surface: Any) -> None:
        self._surface = surface
        self.resize(self._infer_surface_size(surface))

    # ------------------------------------------------------------------
    # Sizing & bookkeeping
    # ------------------------------------------------------------------
    def resize(self, size: tuple[int, int]) -> None:
        if size == self._size:
            return
        self._size = size
        for panel in self._panels.values():
            panel.on_resize(size)

    def legacy_window_snapshot(self) -> dict[str, tuple[str, ...]]:
        return {
            legacy: tuple(panels.keys())
            for legacy, panels in self._panels_by_type.items()
        }

    @property
    def timer_service(self) -> TimerService:
        return self._timer_service

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _generate_panel_id(self, legacy_name: str) -> str:
        return f"{legacy_name}-{next(self._id_counter)}"

    def _initialize_panel_metadata(
        self, panel: PanelProtocol, panel_id: str, legacy_name: str
    ) -> None:
        if not getattr(panel, "panel_id", None):
            setattr(panel, "panel_id", panel_id)
        if not getattr(panel, "legacy_name", None):
            setattr(panel, "legacy_name", legacy_name)

    def _relocate_z_order(self, panel_id: str, *, to_front: bool) -> None:
        if panel_id not in self._panels:
            raise PanelLookupError(panel_id)
        try:
            self._z_order.remove(panel_id)
        except ValueError:
            pass
        if to_front:
            self._z_order.append(panel_id)
        else:
            self._z_order.insert(0, panel_id)

    def _infer_surface_size(self, surface: Any) -> tuple[int, int]:
        getter = getattr(surface, "get_size", None)
        if callable(getter):
            width, height = cast(tuple[int, int], getter())
            return int(width), int(height)
        width = getattr(surface, "width", 0)
        height = getattr(surface, "height", 0)
        if width and height:
            return int(width), int(height)
        return self._size

    def _panel_is_visible(self, panel: PanelProtocol) -> bool:
        return bool(getattr(panel, "visible", True))

    def _panel_accepts_input(self, panel: PanelProtocol) -> bool:
        if not self._panel_is_visible(panel):
            return False
        return bool(getattr(panel, "enabled", True))


__all__ = [
    "PanelManager",
    "PanelFactory",
    "PanelProtocol",
    "PanelRegistrationError",
    "PanelLookupError",
]
