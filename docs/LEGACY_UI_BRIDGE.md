# Legacy UI Bridge - Data Contract Documentation

## Overview

The Legacy UI Bridge (`src/micropolis/ui/legacy_ui_bridge.py`) implements §6.2 of the pygame UI port checklist by providing wrapper functions that synchronize state between:

1. **Modern AppContext** - Pydantic model with type-safe properties used by pygame UI
2. **Legacy sim_control.types** - CamelCase global namespace used by existing tests and TCL shims
3. **UI Components** - Pygame panels, widgets, and event handlers

This ensures backward compatibility while allowing the pygame UI to use modern Python conventions.

## Architecture

```
┌─────────────────────┐
│  Pygame UI Panel    │
│  (e.g., HeadPanel)  │
└──────────┬──────────┘
           │ calls ui_set_auto_budget(context, True)
           ↓
┌─────────────────────────────────────────────┐
│  legacy_ui_bridge.py                        │
│  ┌─────────────────────────────────────┐   │
│  │ ui_set_auto_budget(ctx, enabled)    │   │
│  │   ctx.auto_budget = enabled         │◄──┼─── Updates AppContext
│  │   _legacy_set("AutoBudget", enabled)│   │
│  │   kick()                             │   │
│  └─────────────────────────────────────┘   │
└──────────┬────────────────────┬─────────────┘
           │                    │
           ↓                    ↓
┌──────────────────┐  ┌────────────────────┐
│  AppContext      │  │ sim_control.types  │
│  .auto_budget    │  │ .AutoBudget        │
└──────────────────┘  └────────────────────┘
           │                    │
           │                    ↓
           │          ┌────────────────────┐
           │          │  Legacy Tests      │
           │          │  (observe types)   │
           │          └────────────────────┘
           ↓
┌──────────────────┐
│  Pygame Widgets  │
│  (render state)  │
└──────────────────┘
```

## Data Contract Crosswalk

### Simulation Toggles

| AppContext Property | Legacy Global (types) | UI Component | Default | Description |
|---------------------|----------------------|--------------|---------|-------------|
| `auto_budget` | `AutoBudget` | Head panel toggle | `True` | Auto-approve annual budgets |
| `auto_goto` | `AutoGoto`, `AutoGo` | Editor panel toggle | `True` | Auto-pan to disasters/events |
| `auto_bulldoze` | `AutoBulldoze` | Editor panel toggle | `True` | Auto-remove rubble/wreckage |
| `no_disasters` | `noDisasters` | Options panel toggle | `False` | Disable random disasters (inverted) |
| `user_sound_on` | `UserSoundOn` | Options panel toggle | `True` | Enable sound effects |
| `do_animation` | `doAnimation` | Options panel toggle | `True` | Enable tile animations |
| `do_messages` | `doMessages` | Head panel toggle | `True` | Show message ticker |
| `do_notices` | `doNotices` | Notice panel toggle | `True` | Show popup notices |

### City Metadata

| AppContext Property | Legacy Global (types) | UI Component | Default | Description |
|---------------------|----------------------|--------------|---------|-------------|
| `city_name` | `CityName` | Head panel editable label | `"New City"` | Current city name |
| `game_level` | `GameLevel` | Scenario picker | `0` | Difficulty (0=Easy, 1=Med, 2=Hard) |
| `total_funds` | `TotalFunds` | Head panel counter | `0` | Total city treasury |
| `city_tax` | `CityTax` | Budget panel slider | `7` | Tax rate (0-20%) |

### Simulation Speed

| AppContext Property | Legacy Global (types) | UI Component | Default | Description |
|---------------------|----------------------|--------------|---------|-------------|
| `sim_speed` | `SimSpeed` | Head panel speed controls | `3` | Speed setting (0=Pause, 1-7) |
| `sim_paused` | - | Head panel pause button | `False` | Paused state (boolean) |
| `sim_delay` | `sim_delay` | - | `10` | Delay between steps (ms) |
| `sim_skips` | `sim_skips` | - | `0` | Frames to skip per step |

### Budget & Finance

| AppContext Property | Legacy Global (types) | UI Component | Default | Description |
|---------------------|----------------------|--------------|---------|-------------|
| `fire_percent` | `firePercent` | Budget panel slider | `1.0` | Fire dept funding (0.0-1.0) |
| `police_percent` | `policePercent` | Budget panel slider | `1.0` | Police dept funding (0.0-1.0) |
| `road_percent` | `roadPercent` | Budget panel slider | `1.0` | Road dept funding (0.0-1.0) |
| `fire_spend` | `fireSpend` | Budget panel label | `0` | Fire dept actual spending |
| `police_spend` | `policeSpend` | Budget panel label | `0` | Police dept actual spending |
| `road_spend` | `roadSpend` | Budget panel label | `0` | Road dept actual spending |

### Display & Overlays

| AppContext Property | Legacy Global (types) | UI Component | Default | Description |
|---------------------|----------------------|--------------|---------|-------------|
| `do_overlay` | `DoOverlay` | Map/editor overlay select | `0` | Active overlay (0=None, 1=Pop, 2=Pol, etc.) |
| `don_dither` | `DonDither` | - | `0` | Dithering mode |

### Event Flags

| AppContext Property | Legacy Global (types) | Triggered By | Description |
|---------------------|----------------------|--------------|-------------|
| `must_update_funds` | `MustUpdateFunds` | Fund changes | Trigger fund display refresh |
| `must_update_options` | `MustUpdateOptions` | Toggle changes | Trigger options display refresh |

## API Reference

### Toggle Wrappers

#### `ui_set_auto_budget(context: AppContext, enabled: bool) -> None`

Set auto-budget toggle from UI. Updates both `AppContext.auto_budget` and `sim_control.types.AutoBudget`.

**Usage in pygame panels:**

```python
from src.micropolis.ui.legacy_ui_bridge import ui_set_auto_budget

def on_auto_budget_toggle(self, enabled: bool):
    ui_set_auto_budget(self.context, enabled)
    # Both contexts are now synchronized
```

#### `ui_get_auto_budget(context: AppContext) -> bool`

Get auto-budget state. Reads from legacy types first for test compatibility.

**Usage:**

```python
from src.micropolis.ui.legacy_ui_bridge import ui_get_auto_budget

current_state = ui_get_auto_budget(self.context)
```

*Similar getters/setters exist for all toggles listed in the crosswalk table.*

### City Metadata Wrappers

#### `ui_set_city_name(context: AppContext, name: str) -> None`

Set city name from UI. Updates `AppContext.city_name`, `sim_control.types.CityName`, and calls legacy `setCityName` callback if registered.

**Usage:**

```python
from src.micropolis.ui.legacy_ui_bridge import ui_set_city_name

def on_city_name_edited(self, new_name: str):
    ui_set_city_name(self.context, new_name)
```

#### `ui_set_game_level(context: AppContext, level: int) -> None`

Set game difficulty. Updates `GameLevel` and calls `SetGameLevelFunds` to adjust starting funds.

**Usage:**

```python
from src.micropolis.ui.legacy_ui_bridge import ui_set_game_level

def on_difficulty_selected(self, level: int):
    ui_set_game_level(self.context, level)  # 0=Easy, 1=Med, 2=Hard
```

### Budget Wrappers

#### `ui_set_fire_fund_percentage(context: AppContext, percent: int) -> None`

Set fire department funding (0-100%). Updates `fire_percent`, `fire_spend`, and calls `UpdateFundEffects`.

**Usage:**

```python
from src.micropolis.ui.legacy_ui_bridge import ui_set_fire_fund_percentage

def on_fire_slider_changed(self, value: int):
    ui_set_fire_fund_percentage(self.context, value)
```

*Similar wrappers exist for police and road funding.*

### Initialization

#### `ui_seed_from_legacy_types(context: AppContext) -> None`

Seed pygame UI state from `sim_control.types` namespace. Call once after creating AppContext but before mounting panels.

**Usage during startup:**

```python
from src.micropolis.ui.legacy_ui_bridge import ui_seed_from_legacy_types
from src.micropolis.context import AppContext
from src.micropolis.app_config import AppConfig

# Create context
context = AppContext(config=AppConfig())

# Seed from any values set by tests/legacy code
ui_seed_from_legacy_types(context)

# Now mount pygame panels - they will see synchronized state
panel_manager.mount_head_panel(context)
```

## Integration with Existing Code

### Pygame UI Panels

Panels should:

1. Import bridge functions instead of directly accessing `sim_control`
2. Use `ui_get_*` functions to read state on mount
3. Use `ui_set_*` functions to update state from user input
4. Subscribe to Event Bus for external changes

**Example (Head Panel):**

```python
from src.micropolis.ui.legacy_ui_bridge import (
    ui_get_auto_budget,
    ui_set_auto_budget,
    ui_get_city_name,
    ui_set_city_name,
)

class HeadPanel(UIPanel):
    def on_mount(self, context: AppContext):
        self.context = context
        
        # Seed widget states from synchronized context
        self.auto_budget_toggle.set_checked(ui_get_auto_budget(context))
        self.city_name_label.set_text(ui_get_city_name(context))
        
        # Subscribe to external changes
        self.event_bus.subscribe("funds.updated", self.on_funds_updated)
    
    def on_auto_budget_toggled(self, enabled: bool):
        # User clicked toggle - update both contexts
        ui_set_auto_budget(self.context, enabled)
    
    def on_city_name_edited(self, new_name: str):
        # User edited city name - update both contexts
        ui_set_city_name(self.context, new_name)
```

### Legacy Tests

Tests that patch `micropolis.sim_control.types` continue to work without modification:

**Example (Existing Test):**

```python
def test_auto_budget_toggle(monkeypatch):
    from micropolis import sim_control
    
    # Patch legacy global
    monkeypatch.setattr(sim_control.types, "AutoBudget", False)
    
    # UI reads from legacy types via ui_get_auto_budget
    assert ui_get_auto_budget(context) == False
    
    # UI updates via ui_set_auto_budget
    ui_set_auto_budget(context, True)
    
    # Test can observe change in legacy namespace
    assert sim_control.types.AutoBudget == True
```

### Event Bus Integration

When external code (disasters, evaluation, etc.) updates state, emit events so UI panels can react:

**Example:**

```python
# In disaster handler
from src.micropolis.ui.legacy_ui_bridge import ui_set_auto_goto

def trigger_disaster(context: AppContext):
    # ... disaster logic ...
    
    if ui_get_auto_goto(context):
        # Pan to disaster location
        event_bus.publish("view.goto", x=disaster_x, y=disaster_y)
```

## Testing Strategy

### Unit Tests

Test each wrapper function to verify dual updates:

**Example (`tests/ui/test_legacy_ui_bridge.py`):**

```python
import pytest
from src.micropolis.context import AppContext
from src.micropolis.app_config import AppConfig
from src.micropolis.ui.legacy_ui_bridge import (
    ui_set_auto_budget,
    ui_get_auto_budget,
)
from src.micropolis import sim_control

def test_ui_set_auto_budget_updates_both_contexts():
    context = AppContext(config=AppConfig())
    
    # Set via UI wrapper
    ui_set_auto_budget(context, False)
    
    # Verify AppContext updated
    assert context.auto_budget == False
    
    # Verify legacy types updated
    assert sim_control._legacy_get("AutoBudget") == False

def test_ui_get_auto_budget_prefers_legacy():
    context = AppContext(config=AppConfig())
    context.auto_budget = True
    
    # Override with legacy value
    sim_control._legacy_set("AutoBudget", False)
    
    # Getter prefers legacy for test compatibility
    assert ui_get_auto_budget(context) == False
```

### Integration Tests

Verify panels using bridge functions remain compatible with legacy tests:

**Example:**

```python
def test_head_panel_respects_patched_globals(monkeypatch):
    from micropolis import sim_control
    
    # Existing test pattern
    monkeypatch.setattr(sim_control.types, "AutoBudget", False)
    
    # Create panel
    panel = HeadPanel(manager, context)
    panel.on_mount(context)
    
    # Verify panel reflects patched value
    assert panel.auto_budget_toggle.is_checked() == False
```

## Migration Path

### Phase 1: Bridge Creation ✅ (Current)

- [x] Create `legacy_ui_bridge.py` with wrapper functions
- [x] Document data contract crosswalk
- [x] Implement initialization seeding function

### Phase 2: Panel Integration (Next)

- [ ] Update head panel to use bridge functions
- [ ] Update editor panel to use bridge functions
- [ ] Update budget panel to use bridge functions
- [ ] Update options/settings panel to use bridge functions

### Phase 3: Test Verification

- [ ] Create unit tests for all bridge functions
- [ ] Run existing test suite to verify compatibility
- [ ] Add integration tests for panel + bridge interaction

### Phase 4: Documentation

- [ ] Update panel implementation guides to reference bridge
- [ ] Add code examples to pygame UI documentation
- [ ] Document Event Bus integration patterns

## Troubleshooting

### Issue: Tests fail after panel changes

**Symptom:** Tests that patch `sim_control.types` no longer observe UI changes.

**Solution:** Ensure panels use `ui_set_*` functions instead of direct context assignment:

```python
# ❌ Wrong - bypasses legacy sync
self.context.auto_budget = True

# ✅ Correct - updates both contexts
ui_set_auto_budget(self.context, True)
```

### Issue: UI state out of sync with legacy code

**Symptom:** Headless code sets `types.AutoBudget` but UI doesn't reflect it.

**Solution:** Call `ui_seed_from_legacy_types` during initialization:

```python
# During app startup, after context creation
context = AppContext(config=config)
ui_seed_from_legacy_types(context)  # ← Add this
panel_manager.initialize(context)
```

### Issue: kick() not triggering UI updates

**Symptom:** Changes to context don't immediately update UI panels.

**Solution:** Ensure Event Bus subscriptions are active and `kick()` publishes events:

```python
# In sim_control.kick() or equivalent
def kick():
    _legacy_call("Kick")
    # Publish to Event Bus
    event_bus.publish("state.changed")
```

## References

- [Pygame UI Port Checklist §6.2](../pygame_ui_port_checklist.md)
- [Legacy Wrappers Documentation](./LEGACY_WRAPPERS.md)
- [AppContext Definition](../src/micropolis/context.py)
- [sim_control Module](../src/micropolis/sim_control.py)
- [Event Bus Documentation](./EVENT_BUS_TIMER_INTEGRATION.md)

## Changelog

- **2024-11-15**: Initial implementation of legacy UI bridge per §6.2
  - Created wrapper functions for all UI-relevant toggles and settings
  - Documented data contract crosswalk table
  - Implemented seeding function for initialization
  - Added comprehensive API documentation and usage examples
