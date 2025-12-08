use crate::{rendering::ViewMode, GameMap, GameState};
use bevy::prelude::*;
use bevy_egui::{egui, EguiContexts};

#[derive(Resource, Default)]
pub struct MenuState {
    pub map_size_idx: usize,
    pub water_percent: f32,
    pub show_config: bool,
}

#[derive(Resource, Default, PartialEq, Eq, Clone, Copy, Debug)]
pub enum ToolState {
    #[default]
    Select,
    Bulldozer,
    Road,
    Residential,
    Commercial,
    Industrial,
    PowerLine,
    PowerPlant,
}

pub struct UiPlugin;

impl Plugin for UiPlugin {
    fn build(&self, app: &mut App) {
        app.init_resource::<MenuState>()
            .init_resource::<ToolState>()
            .init_resource::<InspectorState>()
            .add_systems(Update, main_menu_system.run_if(in_state(GameState::Menu)))
            .add_systems(
                Update,
                (game_hud_system, inspector_system).run_if(in_state(GameState::Game)),
            );
    }
}

// Resource to store inspector state
#[derive(Resource, Default)]
pub struct InspectorState {
    pub visible: bool,
    pub tile_info: Option<(String, String)>, // (Title, Details)
    pub screen_pos: Vec2,
}

fn inspector_system(
    mut contexts: EguiContexts,
    mut inspector: ResMut<InspectorState>,
    mouse: Res<ButtonInput<MouseButton>>,
) {
    if mouse.just_pressed(MouseButton::Right) && !inspector.visible {
        // This is handled in main.rs -> handle_interaction to calculate tile info
        // We just verify visibility here or close it
    }

    if inspector.visible {
        let mut open = inspector.visible;
        egui::Window::new(
            inspector
                .tile_info
                .as_ref()
                .map(|(t, _)| t.as_str())
                .unwrap_or("Inspector"),
        )
        .open(&mut open)
        .default_pos([inspector.screen_pos.x, inspector.screen_pos.y])
        .show(contexts.ctx_mut(), |ui| {
            if let Some((_, details)) = &inspector.tile_info {
                ui.label(details);
            }
        });
        inspector.visible = open;
    }
}

fn game_hud_system(
    mut contexts: EguiContexts,
    mut view_mode: ResMut<ViewMode>,
    mut tool_state: ResMut<ToolState>,
    mut grid_state: ResMut<crate::rendering::GridState>,
    mut sim_state: ResMut<crate::simulation::SimulationState>,
    diagnostics: Res<bevy::diagnostic::DiagnosticsStore>,
) {
    // Status Panel
    egui::Window::new("City Status")
        .anchor(egui::Align2::RIGHT_TOP, [-10.0, 10.0])
        .show(contexts.ctx_mut(), |ui| {
            ui.heading("Status");
            // Time Calculation
            let total_ticks = sim_state.time;
            let year = 1900 + (total_ticks / 34560);
            let month_idx = (total_ticks % 34560) / 2880;
            let day = ((total_ticks % 2880) / 96) + 1;
            let hour = (total_ticks % 96) / 4;
            let minute = (total_ticks % 4) * 15;

            let months = [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
            ];
            let month_name = months[month_idx as usize];

            ui.label(format!("Date: {} {} {}", day, month_name, year));
            ui.label(format!("Time: {:02}:{:02}", hour, minute));
            ui.separator();

            // Performance
            if let Some(fps) = diagnostics.get(&bevy::diagnostic::FrameTimeDiagnosticsPlugin::FPS) {
                if let Some(avg) = fps.average() {
                    ui.label(format!("FPS: {:.1}", avg));
                }
            }
            if let Some(entities) =
                diagnostics.get(&bevy::diagnostic::EntityCountDiagnosticsPlugin::ENTITY_COUNT)
            {
                if let Some(count) = entities.value() {
                    ui.label(format!("Entities: {:.0}", count));
                }
            }
        });

    // Tools Panel
    egui::Window::new("Tools")
        .anchor(egui::Align2::LEFT_TOP, [10.0, 10.0])
        .show(contexts.ctx_mut(), |ui| {
            ui.label("Simulation");
            ui.add(egui::Slider::new(&mut sim_state.growth_rate, 0.0..=10.0).text("Growth Rate"));
            ui.separator();

            ui.label("View Layers");
            ui.horizontal(|ui| {
                ui.radio_value(&mut *view_mode, ViewMode::Surface, "Surface");
                ui.radio_value(&mut *view_mode, ViewMode::Underground, "Underground");
            });
            ui.checkbox(&mut grid_state.visible, "Show Grid (G)");
            ui.separator();

            ui.label("Tools");
            ui.horizontal_wrapped(|ui| {
                ui.selectable_value(&mut *tool_state, ToolState::Select, "👆 Select");
                ui.selectable_value(&mut *tool_state, ToolState::Bulldozer, "🚜 Doze");
                ui.selectable_value(&mut *tool_state, ToolState::Road, "🛣️ Road");
            });
            ui.horizontal_wrapped(|ui| {
                ui.selectable_value(&mut *tool_state, ToolState::Residential, "🏠 Res");
                ui.selectable_value(&mut *tool_state, ToolState::Commercial, "🏢 Com");
                ui.selectable_value(&mut *tool_state, ToolState::Industrial, "🏭 Ind");
            });
            ui.horizontal_wrapped(|ui| {
                ui.selectable_value(&mut *tool_state, ToolState::PowerPlant, "⚡ Plant");
                ui.selectable_value(&mut *tool_state, ToolState::PowerLine, "🔌 Line");
            });
        });
}

fn main_menu_system(
    mut contexts: EguiContexts,
    mut menu_state: ResMut<MenuState>,
    mut next_state: ResMut<NextState<GameState>>,
    mut game_map: ResMut<GameMap>,
) {
    egui::CentralPanel::default().show(contexts.ctx_mut(), |ui| {
        ui.vertical_centered(|ui| {
            ui.heading("Micropolis Rust");
            ui.add_space(20.0);

            if !menu_state.show_config {
                // Main Menu Buttons
                if ui.button("New Game").clicked() {
                    menu_state.show_config = true;
                }

                if ui.button("Load Game").clicked() {
                    // TODO: Load Logic
                }

                if ui.button("Exit").clicked() {
                    std::process::exit(0);
                }
            } else {
                // Config Panel
                ui.group(|ui| {
                    ui.label("New Game Settings");
                    ui.add_space(10.0);

                    // Map Size Dropdown
                    let sizes = [64, 128, 256];
                    let size_names = ["64x64", "128x128", "256x256"];

                    ui.horizontal(|ui| {
                        ui.label("Map Size:");
                        // Unique ID for ComboBox
                        egui::ComboBox::from_id_salt("map_size")
                            .selected_text(size_names[menu_state.map_size_idx])
                            .show_ui(ui, |ui| {
                                for (i, name) in size_names.iter().enumerate() {
                                    ui.selectable_value(&mut menu_state.map_size_idx, i, *name);
                                }
                            });
                    });

                    // Water Slider
                    ui.horizontal(|ui| {
                        ui.label("Water:");
                        ui.add(
                            egui::Slider::new(&mut menu_state.water_percent, 0.0..=1.0).text("%"),
                        );
                    });

                    ui.add_space(20.0);

                    ui.horizontal(|ui| {
                        if ui.button("Start Simulation").clicked() {
                            let size = sizes[menu_state.map_size_idx];
                            *game_map = GameMap::new(size, size, menu_state.water_percent);
                            next_state.set(GameState::Game);
                            menu_state.show_config = false; // Reset for next time
                        }

                        if ui.button("Back").clicked() {
                            menu_state.show_config = false;
                        }
                    });
                });
            }
        });
    });
}
