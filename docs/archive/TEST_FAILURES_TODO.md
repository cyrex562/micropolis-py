# Test Failures TODO

Ran `uv run pytest` (timed out after ~300 seconds with the suite reaching roughly 39% before the process was killed). See `pytest.log` for the raw output. The following tests failed before the timeout:

- [x] `tests/test_camera.py::TestSystemLifecycle::test_initialize_camera_system`
- [x] `tests/test_camera.py::TestSystemLifecycle::test_cleanup_camera_syst
- [x] `tests/test_editor_view.py::TestEditorView::test_DoUpdateEditor`
- [x] `tests/test_editor_view.py::TestEditorView::test_DoUpdateEditor_invisible`
- [x] `tests/test_editor_view.py::TestEditorView::test_cleanup_editor_tiles`
- [x] `tests/test_editor_view.py::TestEditorView::test_dynamic_filtering`
- [x] `tests/test_file_io.py::test_file_io` (passes under `uv run pytest tests/test_file_io.py`)
- [x] `tests/test_graphs.py::TestHistoryData::test_init_graph_maxima` (passes under `uv run pytest tests/test_graphs.py`)
- [x] `tests/test_input_bindings.py::test_input_action_dispatcher_routes_actions` (passes under `uv run pytest tests/test_input_bindings.py`)
- [x] `tests/test_mini_maps.py::TestMiniMaps::test_drawRes_filtering` (passes under `uv run pytest tests/test_mini_maps.py`)
- [x] `tests/test_mini_maps.py::TestMiniMaps::test_drawCom_filtering` (passes under `uv run pytest tests/test_mini_maps.py`)
- [x] `tests/test_mini_maps.py::TestMiniMaps::test_drawInd_filtering` (passes under `uv run pytest tests/test_mini_maps.py`)
- [x] `tests/test_mini_maps.py::TestMiniMaps::test_drawLilTransMap_filtering` (passes under `uv run pytest tests/test_mini_maps.py`)
- [x] `tests/test_mini_maps.py::TestMiniMaps::test_dynamicFilter_population` (passes under `uv run pytest tests/test_mini_maps.py`)
- [x] `tests/test_mini_maps.py::TestMiniMaps::test_dynamicFilter_out_of_range` (passes under `uv run pytest tests/test_mini_maps.py`)
- [x] `tests/test_mini_maps.py::TestMiniMaps::test_drawDynamic` (passes under `uv run pytest tests/test_mini_maps.py`)
- [x] `tests/test_network.py::TestNetworkCommand::test_listen_command` (passes under `uv run pytest tests/test_network.py`)
- [x] `tests/test_network.py::TestNetworkCommand::test_stop_command` (passes under `uv run pytest tests/test_network.py`)
- [x] `tests/test_network.py::TestNetworkCommand::test_send_command` (passes under `uv run pytest tests/test_network.py`)
- [x] `tests/test_network.py::TestNetworkCommand::test_send_command_invalid_data` (passes under `uv run pytest tests/test_network.py`)
- [x] `tests/test_network.py::TestNetworkCommand::test_status_command` (passes under `uv run pytest tests/test_network.py`)
- [x] `tests/test_network.py::TestNetworkCommand::test_invalid_command` (passes under `uv run pytest tests/test_network.py`)
- [ ] Rerun the full test suite (with a longer timeout) so we can capture the remaining failures from the ~61% of tests that did not start before the timeout.

- [x] `tests/test_pie_menu.py` suite (passes under `uv run pytest tests/test_pie_menu.py`)
- [x] `tests/test_power.py` suite (passes under `uv run pytest tests/test_power.py`)
- [x] FAILED tests/test_stubs.py::TestMacCompatibility::test_tick_count - AttributeError: 'AppContext' object has no attribute '_tick_base'
- [x] FAILED tests/test_teardown.py::TestDoStopMicropolis::test_cleans_up_graphics - AssertionError: Expected 'cleanup_graphics' to have been called once. Called 0 times.
- [x] FAILED tests/test_teardown.py::TestDoStopMicropolis::test_clears_event_bus - AssertionError: Expected 'clear' to have been called once. Called 0 times.
- [x] FAILED tests/test_teardown.py::TestDoStopMicropolis::test_full_teardown_sequence - AssertionError: Expected 'cleanup_graphics' to have been called once. Called 0 times.
- [ ] FAILED tests/test_tkinter_bridge.py::TestTkinterBridge::test_invalidate_maps - ValueError: "SimView" object has no field "needs_redraw"
FAILED tests/test_tkinter_bridge.py::TestTkinterBridge::test_invalidate_editors - ValueError: "SimView" object has no field "needs_redraw"
FAILED tests/test_tkinter_bridge.py::TestTkinterBridge::test_redraw_maps - ValueError: "SimView" object has no field "needs_redraw"
FAILED tests/test_tkinter_bridge.py::TestTkinterBridge::test_redraw_editors - ValueError: "SimView" object has no field "needs_redraw"
FAILED tests/test_tools.py::TestBuildingPlacement::test_check3x3_insufficient_funds - AssertionError: 1 != -2
FAILED tests/test_tools.py::TestIntegration::test_large_building_placement - AssertionError: -2 != 1
FAILED tests/test_updates.py::TestUIUpdateManager::test_make_dollar_decimal_str - TypeError: object of type 'int' has no len()
FAILED tests/test_widget_toolkit.py::test_slider_changes_value_with_mouse_and_keys - assert False   
FAILED tests/ui/test_budget_panel.py::test_budget_panel_open_dialog - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_budget_panel.py::test_budget_panel_close_dialog - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_budget_panel.py::test_budget_panel_financial_calculations - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_budget_panel.py::test_budget_panel_refresh_from_context - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_budget_panel.py::test_budget_panel_accepts_funding_changes - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_budget_panel.py::test_budget_panel_unmount_cleanup - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_editor_options_panel.py::test_panel_loads_context_values - AssertionError: assert True is False
FAILED tests/ui/test_evaluation_panel.py::test_evaluation_panel_open - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_evaluation_panel.py::test_evaluation_panel_close - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_evaluation_panel.py::test_evaluation_panel_toggle - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_evaluation_panel.py::test_evaluation_panel_data_refresh - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_evaluation_panel.py::test_evaluation_panel_problem_list - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_evaluation_panel.py::test_evaluation_panel_auto_evaluation_toggle - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_evaluation_panel.py::test_evaluation_panel_render_without_pygame - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_evaluation_panel.py::test_evaluation_panel_unmount_cleanup - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_evaluation_panel.py::test_evaluation_panel_state_snapshot - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_graphs_panel.py::test_graphs_panel_set_range - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'publish'
FAILED tests/ui/test_panel_data_binding.py::TestBudgetPanelDataBinding::test_auto_budget_toggle_updates_context - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_panel_data_binding.py::TestBudgetPanelDataBinding::test_tax_rate_slider_updates_context - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_panel_data_binding.py::TestBudgetPanelDataBinding::test_budget_allocation_emits_event - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_panel_data_binding.py::TestEvaluationPanelScores::test_evaluation_triggered_on_demand - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
FAILED tests/ui/test_panel_data_binding.py::TestEvaluationPanelScores::test_evaluation_results_displayed - AttributeError: module 'micropolis.ui.event_bus' has no attribute 'subscribe'
ERROR tests/test_head_panel.py::test_head_panel_refresh_from_context_updates_state_and_events - AttributeError: 'module' object at src.micropolis.ui.panels.head_panel has no attribute 'get_si...      
ERROR tests/test_head_panel.py::test_head_panel_speed_and_pause_requests_dispatch - AttributeError: 'module' object at src.micropolis.ui.panels.head_panel has no attribute 'get_si...
ERROR tests/test_zones.py::TestZoneIntegration::test_population_calculations_residential - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_population_calculations_commercial - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_population_calculations_industrial - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_get_cr_val_land_value_rating - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_zone_power_detection - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_zone_type_routing - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_hospital_church_processing - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_evaluation_functions - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_zone_placement_residential - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_zone_placement_commercial - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_zone_placement_industrial - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_free_zone_population_counting - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_zone_plop_blocked_by_disaster - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_zone_plop_success - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_eval_lot_scoring - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_residential_growth_logic - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_commercial_growth_logic - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_industrial_growth_logic - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
ERROR tests/test_zones.py::TestZoneIntegration::test_zone_shrinkage_logic - AttributeError: <module 'src.micropolis.simulation' from 'C:\\Users\\cyrex\\files\\projects\\mi...
