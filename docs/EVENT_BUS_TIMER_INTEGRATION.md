# Event Bus + Timer Service Integration Guide

This document describes how the Timer Service and Event Bus work together to enable clean fan-out of shared events across multiple UI panels, as specified in §5.3 of the pygame UI port checklist.

## Architecture Overview

The integration of the Timer Service and Event Bus provides:

1. **Decoupled Communication**: Panels subscribe to events without direct references to publishers
2. **Priority-based Dispatch**: Critical handlers (e.g., simulation state) execute before UI updates
3. **Simulation-aware Timers**: Timers can pause when simulation pauses while UI timers continue
4. **Re-entrant Safety**: Events published during handling are queued and dispatched in order
5. **Flexible Subscriptions**: One-time, filtered, and wildcard subscriptions for various use cases

## Core Components

### Event Bus (`src/micropolis/ui/event_bus.py`)

Thread-safe publish/subscribe system with:

- **Namespaced topics**: `funds.updated`, `simulation.paused`, `sugar.buddy_joined`
- **Priority ordering**: High-priority subscribers execute first
- **Wildcard patterns**: Subscribe to `overlay.*` to catch all overlay events
- **Predicate filtering**: Conditional subscription based on event payload
- **Once-only subscriptions**: Automatic unsubscribe after first delivery

### Timer Service (`src/micropolis/ui/timer_service.py`)

Frame-driven scheduler replacing Tcl `after` with:

- **One-shot timers**: `call_later(delay_ms, callback)`
- **Repeating timers**: `call_every(interval_ms, callback)`
- **Simulation binding**: Timers pause when `set_simulation_paused(True)`
- **Tag-based cancellation**: Cancel all timers with specific tags
- **Event integration**: Timer events automatically published to Event Bus

## Common Event Topics

### Simulation Events

| Topic | Payload | Description |
|-------|---------|-------------|
| `funds.updated` | `{"value": int, "change": int}` | City treasury changed |
| `population.updated` | `{"value": int, "change": int}` | Population changed |
| `date.tick` | `{"month": int, "year": int}` | Game date advanced |
| `disaster.triggered` | `{"type": str, "x": int, "y": int}` | Disaster occurred |
| `overlay.changed` | `{"overlay": str, "enabled": bool}` | Map overlay toggled |
| `simulation.paused` | `{"reason": str}` | Simulation paused |
| `simulation.resumed` | `{}` | Simulation resumed |

### Timer Events

| Topic | Payload | Description |
|-------|---------|-------------|
| `timer.fired` | `{"timer_id": str, "run_count": int, ...}` | Timer callback executed |

### Sugar Events

| Topic | Payload | Description |
|-------|---------|-------------|
| `sugar.buddy_joined` | `{"name": str, "color": str}` | Buddy joined activity |
| `sugar.activate` | `{}` | Activity activated |
| `sugar.quit` | `{}` | Activity quit requested |

## Usage Examples

### Multiple Panels Subscribing to Funds Updates

```python
from src.micropolis.ui.event_bus import EventBus, BusEvent

# Initialize bus (typically done once at startup)
bus = EventBus()

# Head panel updates display
def head_panel_funds_handler(event: BusEvent) -> None:
    new_funds = event.payload["value"]
    update_display(f"${new_funds:,}")

# Budget panel updates projections
def budget_panel_funds_handler(event: BusEvent) -> None:
    new_funds = event.payload["value"]
    recalculate_budget_projections(new_funds)

# Evaluation panel checks thresholds
def eval_panel_funds_handler(event: BusEvent) -> None:
    new_funds = event.payload["value"]
    if new_funds < 0:
        trigger_bankruptcy_warning()

# Subscribe all three panels
bus.subscribe("funds.updated", head_panel_funds_handler)
bus.subscribe("funds.updated", budget_panel_funds_handler)
bus.subscribe("funds.updated", eval_panel_funds_handler)

# When funds change, publish once
bus.publish("funds.updated", {"value": 50000, "change": -1500})
# All three handlers execute automatically
```

### Priority-based Disaster Handling

```python
# High-priority: Update simulation state first
bus.subscribe(
    "disaster.triggered",
    simulation_disaster_handler,
    priority=100  # Higher executes first
)

# Low-priority: Update UI after simulation
bus.subscribe(
    "disaster.triggered",
    ui_disaster_notification,
    priority=0
)

# Publish disaster event
bus.publish("disaster.triggered", {"type": "fire", "x": 50, "y": 60})
# simulation_disaster_handler runs first, then ui_disaster_notification
```

### Wildcard Subscriptions for Overlay Management

```python
# Subscribe to all overlay events
def overlay_manager_handler(event: BusEvent) -> None:
    overlay_name = event.topic.split(".")[-1]  # Extract overlay type
    enabled = event.payload["enabled"]
    update_overlay_state(overlay_name, enabled)

bus.subscribe("overlay.*", overlay_manager_handler)

# Publish specific overlay changes
bus.publish("overlay.power", {"enabled": True})
bus.publish("overlay.traffic", {"enabled": False})
# overlay_manager_handler receives both
```

### Budget Countdown Timer with Event Notifications

```python
from src.micropolis.ui.timer_service import TimerService, TimerEvent

# Initialize timer service (connected to event bus)
timer_service = TimerService(event_bus=bus)

# Timer callback publishes countdown events
def budget_countdown_callback(event: TimerEvent) -> None:
    remaining = 10 - event.run_count
    bus.publish(
        "budget.countdown",
        {"remaining_seconds": remaining},
        defer=False  # Immediate notification
    )
    if remaining == 0:
        trigger_auto_accept()

# Subscribe to countdown notifications
def ui_countdown_display(event: BusEvent) -> None:
    remaining = event.payload["remaining_seconds"]
    update_countdown_label(f"{remaining}s")

bus.subscribe("budget.countdown", ui_countdown_display)

# Schedule 1-second repeating timer
timer_service.call_every(
    1000,  # 1000ms = 1 second
    budget_countdown_callback,
    simulation_bound=True,  # Pauses when simulation pauses
    tags=("budget",),
    max_runs=10  # Auto-cancel after 10 seconds
)

# Advance time in main loop
def game_loop():
    while running:
        dt_ms = clock.tick(60)  # 60 FPS
        timer_service.tick(dt_ms)
        # ... render, handle input, etc.
```

### Blinking Overlay Timer (500ms Toggle)

```python
# State for blinking
current_blink_state = False

def blink_callback(event: TimerEvent) -> None:
    global current_blink_state
    current_blink_state = not current_blink_state
    bus.publish("overlay.blink", {"state": current_blink_state})

# Subscribe to blink events
def renderer_blink_handler(event: BusEvent) -> None:
    state = event.payload["state"]
    set_lightning_visible(state)

bus.subscribe("overlay.blink", renderer_blink_handler)

# Schedule repeating blink timer
blink_timer_id = timer_service.call_every(
    500,  # Toggle every 500ms
    blink_callback,
    tags=("blink", "overlay")
)

# Cancel blinking when needed
timer_service.cancel_by_tag("blink")
```

### Simulation Pause Behavior

```python
# Create simulation-bound and UI timers
autosave_timer = timer_service.call_every(
    60000,  # 1 minute
    autosave_callback,
    simulation_bound=True  # Pauses with simulation
)

tooltip_timer = timer_service.call_later(
    500,  # 500ms delay
    show_tooltip_callback,
    simulation_bound=False  # Never pauses
)

# When opening budget dialog, pause simulation
timer_service.set_simulation_paused(True)
# autosave_timer stops firing, tooltip_timer continues

# When closing budget dialog, resume
timer_service.set_simulation_paused(False)
# autosave_timer resumes from where it paused
```

### Once-Only Subscription for Initialization

```python
# Splash screen waits for engine initialization
def splash_ready_handler(event: BusEvent) -> None:
    transition_to_main_menu()

bus.subscribe(
    "engine.initialized",
    splash_ready_handler,
    once=True  # Auto-unsubscribe after first call
)

# Publish multiple times (e.g., during init sequence)
bus.publish("engine.initialized", {"ready": False})
bus.publish("engine.initialized", {"ready": True})
bus.publish("engine.initialized", {"ready": True})
# splash_ready_handler only called once (first time)
```

### Filtered Subscriptions with Predicates

```python
# Only handle warning-level messages
def warning_predicate(event: BusEvent) -> bool:
    return event.payload.get("level") == "warning"

bus.subscribe(
    "sugar.*",
    sugar_warning_handler,
    predicate=warning_predicate
)

# Publish various events
bus.publish("sugar.buddy_joined", {"level": "info"})
bus.publish("sugar.alert", {"level": "warning", "message": "Low funds"})
# sugar_warning_handler only receives the warning
```

### Re-entrant Event Publishing Safety

```python
# Handler that publishes another event
def primary_handler(event: BusEvent) -> None:
    process_primary_event(event)
    # Publish secondary event during handling
    bus.publish("secondary.event", {"from": "primary"})

def secondary_handler(event: BusEvent) -> None:
    process_secondary_event(event)

bus.subscribe("primary.event", primary_handler)
bus.subscribe("secondary.event", secondary_handler)

# Publish primary event
bus.publish("primary.event", {"data": "test"})
# Events processed in order:
# 1. primary_handler executes fully
# 2. secondary_handler executes after (queued during primary_handler)
```

## Integration with Panel Lifecycle

### Panel Initialization

```python
from src.micropolis.ui.uipanel import UIPanel

class ExamplePanel(UIPanel):
    def on_mount(self, context) -> None:
        """Called when panel is added to panel manager."""
        super().on_mount(context)
        
        # Get default event bus
        from src.micropolis.ui.event_bus import get_default_event_bus
        self._bus = get_default_event_bus()
        
        # Subscribe to relevant events
        self._funds_sub_id = self._bus.subscribe(
            "funds.updated",
            self._handle_funds_update
        )
        self._disaster_sub_id = self._bus.subscribe(
            "disaster.triggered",
            self._handle_disaster,
            priority=10
        )
    
    def on_unmount(self) -> None:
        """Called when panel is removed."""
        # Clean up subscriptions
        self._bus.unsubscribe(self._funds_sub_id)
        self._bus.unsubscribe(self._disaster_sub_id)
        super().on_unmount()
    
    def _handle_funds_update(self, event: BusEvent) -> None:
        """Update display when funds change."""
        self.funds_label.set_text(f"${event.payload['value']:,}")
        self.invalidate()  # Request redraw
    
    def _handle_disaster(self, event: BusEvent) -> None:
        """Show disaster notification."""
        disaster_type = event.payload["type"]
        self.show_notification(f"{disaster_type.capitalize()} disaster!")
```

### Panel Publishing Events

```python
class HeadPanel(UIPanel):
    def _handle_speed_button_click(self, new_speed: int) -> None:
        """Called when user changes simulation speed."""
        # Update simulation
        self.context.engine.set_sim_speed(new_speed)
        
        # Publish event for other panels
        self._bus.publish(
            "simulation.speed_changed",
            {"speed": new_speed},
            source="head-panel",
            tags=("simulation", "ui")
        )
```

## Best Practices

### 1. Use Namespaced Topics

```python
# Good: Namespaced and descriptive
"funds.updated"
"simulation.paused"
"overlay.power.enabled"

# Avoid: Flat, ambiguous names
"update"
"changed"
"event"
```

### 2. Include Relevant Context in Payloads

```python
# Good: Complete information
bus.publish("disaster.triggered", {
    "type": "fire",
    "x": 50,
    "y": 60,
    "severity": 3
})

# Avoid: Missing context
bus.publish("disaster.triggered", {"type": "fire"})
```

### 3. Use Priorities for Critical Ordering

```python
# Simulation state updates: high priority
bus.subscribe("disaster.triggered", sim_handler, priority=100)

# Analytics/logging: medium priority
bus.subscribe("disaster.triggered", analytics_handler, priority=50)

# UI updates: low priority (default)
bus.subscribe("disaster.triggered", ui_handler, priority=0)
```

### 4. Always Clean Up Subscriptions

```python
class MyPanel(UIPanel):
    def on_mount(self, context) -> None:
        self._subscription_ids = []
        self._subscription_ids.append(
            self._bus.subscribe("event.a", self._handler_a)
        )
        self._subscription_ids.append(
            self._bus.subscribe("event.b", self._handler_b)
        )
    
    def on_unmount(self) -> None:
        for sub_id in self._subscription_ids:
            self._bus.unsubscribe(sub_id)
        self._subscription_ids.clear()
```

### 5. Use `defer=True` for Batch Updates

```python
# Publishing many events in a tight loop
for i in range(100):
    bus.publish(
        "tile.updated",
        {"x": i, "y": 0},
        defer=True  # Queue without immediate dispatch
    )

# Dispatch all queued events at once
bus.flush()
```

### 6. Tag Timers for Bulk Management

```python
# Schedule related timers with tags
timer_service.call_every(1000, autosave_callback, tags=("autosave", "io"))
timer_service.call_every(5000, backup_callback, tags=("backup", "io"))

# Cancel all I/O timers at once
timer_service.cancel_by_tag("io")
```

## Testing

### Mock Event Bus for Unit Tests

```python
import pytest
from src.micropolis.ui.event_bus import EventBus

@pytest.fixture
def mock_bus() -> EventBus:
    """Provide isolated bus for each test."""
    bus = EventBus()
    yield bus
    bus.clear()  # Clean up after test

def test_panel_subscribes_to_funds(mock_bus):
    panel = ExamplePanel()
    panel._bus = mock_bus
    panel.on_mount(context)
    
    # Verify subscription registered
    assert mock_bus.subscriber_count("funds.updated") == 1
    
    # Publish test event
    mock_bus.publish("funds.updated", {"value": 12345})
    
    # Verify panel updated
    assert panel.funds_label.text == "$12,345"
```

### Mock Timer Service for Testing

```python
from src.micropolis.ui.timer_service import TimerService

def test_budget_countdown():
    bus = EventBus()
    timer_service = TimerService(event_bus=bus)
    
    notifications = []
    bus.subscribe(
        "budget.countdown",
        lambda e: notifications.append(e.payload["remaining_seconds"])
    )
    
    # Schedule countdown
    timer_service.call_every(1000, countdown_callback, max_runs=10)
    
    # Simulate 10 seconds
    for _ in range(10):
        timer_service.tick(1000)
    
    # Verify all notifications received
    assert len(notifications) == 10
    assert notifications == [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
```

## Performance Considerations

1. **Event Payload Size**: Keep payloads lightweight; pass IDs instead of large objects
2. **Subscription Count**: Hundreds of subscribers per topic is fine; thousands may impact performance
3. **Re-entrant Depth**: Avoid deep re-entrant chains (A publishes B publishes C publishes D...)
4. **Timer Granularity**: Use reasonable intervals (≥16ms for 60 FPS); avoid scheduling thousands of timers
5. **Deferred Publishing**: Use `defer=True` for bulk operations to batch event dispatch

## See Also

- [pygame_ui_port_checklist.md](./pygame_ui_port_checklist.md) - §5.3 Timer & Event System
- [src/micropolis/ui/event_bus.py](../src/micropolis/ui/event_bus.py) - Event Bus implementation
- [src/micropolis/ui/timer_service.py](../src/micropolis/ui/timer_service.py) - Timer Service implementation
- [tests/test_event_bus_timer_integration.py](../tests/test_event_bus_timer_integration.py) - Integration tests
