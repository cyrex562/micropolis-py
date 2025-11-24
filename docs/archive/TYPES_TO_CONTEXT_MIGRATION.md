# Migration: types.py to AppContext

This document tracks the migration of mutable globals from `micropolis.types` to `AppContext`.

## Overview

The `micropolis.types` module was a legacy compatibility layer that re-exported constants and provided mutable global state. This migration moves all mutable state to `AppContext` and updates all code to use the context directly.

## Migration Checklist

### Source Files

- [x] `src/micropolis/audio.py` - Sound system (removed legacy_types import, uses AppContext directly)
- [x] `src/micropolis/budget.py` - Budget management (removed types import, all sync functions are no-ops)
- [x] `src/micropolis/date_display.py` - Date/time display (removed types import, _sync_time_context is no-op)
- [x] `src/micropolis/editor.py` - Map editor (removed types import, uses context.sim directly)
- [x] `src/micropolis/evaluation_ui.py` - City evaluation UI (removed types import, uses context directly)
- [x] `src/micropolis/messages.py` - Message system (removed types import, mirror functions are no-ops, uses eval_cmd_str directly)
- [x] `src/micropolis/power.py` - Power grid simulation (removed legacy_types import, uses context.map_data directly)
- [x] `src/micropolis/stubs.py` - Legacy stubs (removed types import, uses set_city_name and ui_utilities directly)
- [x] `src/micropolis/tkinter_bridge.py` - Tkinter compatibility (removed _types import, uses context directly)
- [x] `src/micropolis/tools.py` - Building tools (removed types import from getDensityStr, uses context buffers directly)

### Test Files

- [ ] `tests/test_mini_maps.py`
- [ ] `tests/test_editor_view.py`
- [ ] `tests/test_file_io.py`
- [ ] `tests/types.py` (test helper)

### Final Cleanup

- [ ] Remove synchronization code from migrated files
- [ ] Deprecate or remove `micropolis.types` module
- [ ] Run full test suite
- [ ] Update documentation

## Mutable Globals to Migrate

### Map/Overlay Buffers
- `map_data` -> `context.map_data`
- `power_map` -> `context.power_map`
- `land_value_mem` -> `context.land_value_mem`
- `pollution_mem` -> `context.pollution_mem`
- `pop_density` -> `context.pop_density`
- `crime_mem` -> `context.crime_mem`
- `com_rate` -> `context.com_rate`
- `rate_og_mem` -> `context.rate_og_mem`
- `trf_density` -> `context.trf_density`
- `tem` -> `context.tem`
- `tem2` -> `context.tem2`
- `terrain_mem` -> `context.terrain_mem`

### Population Counters
- `res_pop` -> `context.res_pop`
- `com_pop` -> `context.com_pop`
- `ind_pop` -> `context.ind_pop`
- `hosp_pop` -> `context.hosp_pop`
- `church_pop` -> `context.church_pop`
- `pwrd_z_cnt` -> `context.pwrd_z_cnt`
- `un_pwrd_z_cnt` -> `context.un_pwrd_z_cnt`
- `need_hosp` -> `context.need_hosp`
- `need_church` -> `context.need_church`

### Financial
- `TotalFunds` / `total_funds` -> `context.total_funds`
- `CityTax` / `city_tax` -> `context.city_tax`
- `firePercent` -> `context.fire_percent`
- `policePercent` -> `context.police_percent`
- `roadPercent` -> `context.road_percent`
- `fireMaxValue` -> `context.fire_max_value`
- `policeMaxValue` -> `context.police_max_value`
- `roadMaxValue` -> `context.road_max_value`

### City State
- `city_time` -> `context.city_time`
- `starting_year` -> `context.starting_year`
- `city_name` -> `context.city_name`
- `SimSpeed` -> `context.sim_speed`
- `SimMetaSpeed` -> `context.sim_meta_speed`
- `sim_paused_speed` -> `context.sim_paused_speed`
- `sim_delay` -> `context.sim_delay`
- `sim_skips` -> `context.sim_skips`
- `sim_skip` -> `context.sim_skip`

### Coordinates
- `s_map_x` -> `context.s_map_x`
- `s_map_y` -> `context.s_map_y`
- `CCx` / `CCy` -> `context.cc_x` / `context.cc_y`
- `PolMaxX` / `PolMaxY` -> `context.pol_max_x` / `context.pol_max_y`
- `CrimeMaxX` / `CrimeMaxY` -> `context.crime_max_x` / `context.crime_max_y`
- `TrafMaxX` / `TrafMaxY` -> `context.traf_max_x` / `context.traf_max_y`
- `FloodX` / `FloodY` -> `context.flood_x` / `context.flood_y`
- `CrashX` / `CrashY` -> `context.crash_x` / `context.crash_y`
- `MeltX` / `MeltY` -> `context.melt_x` / `context.melt_y`

### Game State
- `autoBudget` -> `context.auto_budget`
- `MustUpdateOptions` -> `context.must_update_options`
- `MustUpdateFunds` -> `context.must_update_funds`
- `doAnimation` -> `context.do_animation`
- `doMessages` -> `context.do_messages`
- `doNotices` -> `context.do_notices`
- `NeedRest` -> `context.need_rest`
- `eval_changed` -> `context.eval_changed`
- `shake_now` -> `context.shake_now`

## Migration Log

### 2024-XX-XX - Initial Setup
- Created migration checklist document

