use bevy::prelude::*;
use bevy_egui::EguiPlugin;

mod map;
mod rendering;
mod simulation;
mod ui;

use map::MapPlugin;
use rendering::{ChunkUpdateEvent, CursorMapPosition, RenderingPlugin};
use simulation::SimulationPlugin;
use std::collections::HashSet;
use ui::{ToolState, UiPlugin};

pub use map::GameMap;

#[derive(States, Debug, Clone, Copy, Eq, PartialEq, Hash, Default)]
pub enum GameState {
    #[default]
    Menu,
    Game,
}

#[derive(Resource, Default)]
struct DragState {
    start: Option<[i32; 2]>,
    current: Option<[i32; 2]>,
}

fn main() {
    App::new()
        .add_plugins(DefaultPlugins.set(WindowPlugin {
            primary_window: Some(Window {
                title: "Micropolis Rust".into(),
                resolution: (1280., 720.).into(),
                ..default()
            }),
            ..default()
        }))
        .add_plugins(EguiPlugin)
        .add_plugins((
            bevy::diagnostic::FrameTimeDiagnosticsPlugin,
            bevy::diagnostic::EntityCountDiagnosticsPlugin,
        ))
        .init_state::<GameState>()
        .init_resource::<DragState>() // DragState
        .add_plugins((MapPlugin, UiPlugin, SimulationPlugin, RenderingPlugin))
        .add_systems(Update, exit_on_esc)
        .add_systems(
            Update,
            (handle_interaction, draw_preview_gizmos).run_if(in_state(GameState::Game)),
        )
        .run();
}

fn exit_on_esc(mut exit: EventWriter<AppExit>, keyboard_input: Res<ButtonInput<KeyCode>>) {
    if keyboard_input.just_pressed(KeyCode::Escape) {
        exit.send(AppExit::Success);
    }
}

// Draw Preview Gizmos for Dragging
fn draw_preview_gizmos(drag: Res<DragState>, tool: Res<ToolState>, mut gizmos: Gizmos) {
    if let (Some(start), Some(curr)) = (drag.start, drag.current) {
        let sx = start[0];
        let sz = start[1];
        let cx = curr[0];
        let cz = curr[1];

        let color = match *tool {
            ToolState::Road => Color::srgb(0.5, 0.5, 0.5), // Grey
            ToolState::Residential => Color::srgb(0.0, 1.0, 0.0), // Green
            ToolState::Commercial => Color::srgb(0.0, 0.0, 1.0), // Blue
            ToolState::Industrial => Color::srgb(1.0, 1.0, 0.0), // Yellow
            ToolState::PowerPlant => Color::srgb(1.0, 0.0, 0.0), // Red
            ToolState::PowerLine => Color::srgb(0.0, 1.0, 1.0), // Cyan
            ToolState::Bulldozer => Color::srgb(1.0, 0.0, 0.0), // Red
            _ => Color::WHITE,
        };

        if *tool == ToolState::Road {
            // Straight Line Logic: Horizontal or Vertical based on major axis
            let dx = (cx - sx).abs();
            let dz = (cz - sz).abs();

            if dx > dz {
                // Horizontal (vary X)
                let min_x = sx.min(cx);
                let max_x = sx.max(cx);
                for x in min_x..=max_x {
                    gizmos.cuboid(
                        Transform::from_xyz(x as f32 + 0.5, 1.1, sz as f32 + 0.5),
                        color,
                    );
                }
            } else {
                // Vertical (vary Z)
                let min_z = sz.min(cz);
                let max_z = sz.max(cz);
                for z in min_z..=max_z {
                    gizmos.cuboid(
                        Transform::from_xyz(sx as f32 + 0.5, 1.1, z as f32 + 0.5),
                        color,
                    );
                }
            }
        } else {
            // Rectangular Area
            let min_x = sx.min(cx);
            let max_x = sx.max(cx);
            let min_z = sz.min(cz);
            let max_z = sz.max(cz);

            for z in min_z..=max_z {
                for x in min_x..=max_x {
                    gizmos.cuboid(
                        Transform::from_xyz(x as f32 + 0.5, 1.1, z as f32 + 0.5),
                        color,
                    );
                }
            }
        }
    }
}

fn handle_interaction(
    mouse: Res<ButtonInput<MouseButton>>,
    cursor: Res<CursorMapPosition>,
    tool: Res<ToolState>,
    mut map: ResMut<GameMap>,
    mut chunk_events: EventWriter<ChunkUpdateEvent>,
    mut drag: ResMut<DragState>,
    mut inspector: ResMut<ui::InspectorState>,
    power_grid: Res<simulation::PowerGrid>,
    sim_state: Res<simulation::SimulationState>,
    window_query: Query<&Window>,
) {
    let cursor_coord = if let (Some(x), Some(z)) = (cursor.x, cursor.z) {
        Some([x, z])
    } else {
        None
    };

    // 4. Right Click -> Inspector / Cancel Drag
    if mouse.just_pressed(MouseButton::Right) {
        if drag.start.is_some() {
            // Cancel Drag
            drag.start = None;
            drag.current = None;
        } else {
            // Open Inspector
            if let Some([x, z]) = cursor_coord {
                if x >= 0 && x < map.width as i32 && z >= 0 && z < map.height as i32 {
                    let idx = (z * map.width as i32 + x) as usize;

                    // Prioritize Air Layer if Power Line tool? No, general inspector.
                    // Check surface first.
                    let mut tile = map::TileType::Empty;
                    let mut layer_name = "Surface";

                    if let Some(surface) = map.layers.get(&0) {
                        tile = surface[idx];
                    }

                    // If surface is empty or dirt, check air?
                    if tile == map::TileType::Empty || tile == map::TileType::Dirt {
                        if let Some(air) = map.layers.get(&1) {
                            if air[idx] != map::TileType::Empty {
                                tile = air[idx];
                                layer_name = "Air (Layer 1)";
                            }
                        }
                    }

                    // Build Details String
                    let mut details = format!("Type: {:?}\nLayer: {}\n", tile, layer_name);

                    // Population / Jobs (Approximate based on tile type)
                    // ... (This logic is in census_system, repeated slightly here or just static info)
                    // Status
                    let cons = simulation::get_power_consumption(tile);
                    if cons > 0 {
                        details.push_str(&format!("Power Usage: {} units\n", cons));
                        let is_powered = power_grid.powered_tiles.contains(&(x, z));
                        details.push_str(&format!(
                            "Powered: {}\n",
                            if is_powered { "YES" } else { "NO" }
                        ));
                    } else if tile == map::TileType::PowerPlant {
                        details.push_str("Generates: 500 units\n");
                        details.push_str(&format!("Grid Net Power: {}\n", power_grid.net_power));
                    }

                    inspector.tile_info = Some((format!("Inspector ({}, {})", x, z), details));
                    inspector.visible = true;

                    if let Ok(window) = window_query.get_single() {
                        if let Some(pos) = window.cursor_position() {
                            inspector.screen_pos = pos;
                        }
                    }
                }
            }
        }
    }

    // 1. Mouse Down -> Start Drag (Only if inspector not just opened? Right click handles that)
    // ... Left click logic follows ...
    if mouse.just_pressed(MouseButton::Left) {
        if let Some(coord) = cursor_coord {
            drag.start = Some(coord);
            drag.current = Some(coord);
            // Close inspector on interaction
            inspector.visible = false;
        }
    }

    // 2. Mouse Hold -> Update Drag
    if mouse.pressed(MouseButton::Left) {
        if let Some(coord) = cursor_coord {
            drag.current = Some(coord);
        }
    }

    // 3. Mouse Up -> Apply
    if mouse.just_released(MouseButton::Left) {
        if let (Some(start), Some(curr)) = (drag.start, drag.current) {
            apply_tool(start, curr, &*tool, &mut *map, &mut chunk_events);
        }
        drag.start = None;
        drag.current = None;
    }
}

fn apply_tool(
    start: [i32; 2],
    end: [i32; 2],
    tool: &ToolState,
    map: &mut GameMap,
    chunk_events: &mut EventWriter<ChunkUpdateEvent>,
) {
    let mut affected_chunks = HashSet::new();
    let sx = start[0];
    let sz = start[1];
    let ex = end[0];
    let ez = end[1];

    // Helper closure removed to avoid borrow issues
    // Using inline logic

    if *tool == ToolState::Road {
        // Straight Line Logic
        let dx = (ex - sx).abs();
        let dz = (ez - sz).abs();

        if dx > dz {
            // Horizontal
            let min_x = sx.min(ex);
            let max_x = sx.max(ex);
            for x in min_x..=max_x {
                // Inline set_tile
                if x >= 0 && x < map.width as i32 && sz >= 0 && sz < map.height as i32 {
                    let idx = (sz * map.width as i32 + x) as usize;
                    if let Some(layer) = map.layers.get_mut(&0) {
                        if layer[idx] != map::TileType::Road {
                            layer[idx] = map::TileType::Road;
                            affected_chunks.insert(((x as u32) / 32, (sz as u32) / 32));
                        }
                    }
                }
            }
        } else {
            // Vertical
            let min_z = sz.min(ez);
            let max_z = sz.max(ez);
            for z in min_z..=max_z {
                if sx >= 0 && sx < map.width as i32 && z >= 0 && z < map.height as i32 {
                    let idx = (z * map.width as i32 + sx) as usize;
                    if let Some(layer) = map.layers.get_mut(&0) {
                        if layer[idx] != map::TileType::Road {
                            layer[idx] = map::TileType::Road;
                            affected_chunks.insert(((sx as u32) / 32, (z as u32) / 32));
                        }
                    }
                }
            }
        }
    } else {
        // Rectangle
        let min_x = sx.min(ex);
        let max_x = sx.max(ex);
        let min_z = sz.min(ez);
        let max_z = sz.max(ez);

        let tile_type = match tool {
            ToolState::Bulldozer => map::TileType::Dirt,
            ToolState::Residential => map::TileType::Residential,
            ToolState::Commercial => map::TileType::Commercial,
            ToolState::Industrial => map::TileType::Industrial,
            ToolState::PowerPlant => map::TileType::PowerPlant,
            ToolState::PowerLine => map::TileType::PowerLine, // Handled specifically below for Air Layer
            _ => return,
        };

        for z in min_z..=max_z {
            for x in min_x..=max_x {
                if *tool == ToolState::PowerLine {
                    if x >= 0 && x < map.width as i32 && z >= 0 && z < map.height as i32 {
                        let idx = (z * map.width as i32 + x) as usize;
                        // Determine target layer: Air for lines, Surface for others
                        if let Some(layers) = map.layers.get_mut(&1) {
                            // Need to check surface layer (0) but also accessing layer 1
                            // map.layers borrows map. We need disjoint borrows or just clone tile type?
                            // Since we are inside `layers` mutable borrow, we can't easily get reference to layer 0.
                            // Solution: Check layer 0 first, get bool, then mutate layer 1.

                            let is_blocked = false;
                            // Just check map.layers.get(&0) is complicated by borrow checker if we hold a mut ref to layers(&1) from same HashMap
                            // Wait, `map.layers` is `HashMap`. `get_mut` borrows the map. We can't query it again.
                            // We should get both layers out if possible or iterate differently.
                            // Or just assume empty if we can't check?
                            // Actually, since we are doing one tile at a time, we *could* do it but it's inefficient.
                            // Better: Split the scope.

                            // 1. Check blockage
                            // We need to release `map.layers` borrow to check layer 0.
                        }

                        // Revised Logic:
                        let mut blocked = false;
                        if let Some(surface) = map.layers.get(&0) {
                            let s_idx = (z * map.width as i32 + x) as usize;
                            let surface_tile = surface[s_idx];
                            if matches!(
                                surface_tile,
                                map::TileType::ResidentialOccupied1
                                    | map::TileType::ResidentialOccupied2
                                    | map::TileType::ResidentialOccupied3
                                    | map::TileType::CommercialOccupied1
                                    | map::TileType::CommercialOccupied2
                                    | map::TileType::CommercialOccupied3
                                    | map::TileType::IndustrialOccupied1
                                    | map::TileType::IndustrialOccupied2
                                    | map::TileType::IndustrialOccupied3
                                    | map::TileType::PowerPlant
                            ) {
                                blocked = true;
                            }
                        }

                        if !blocked {
                            if let Some(air) = map.layers.get_mut(&1) {
                                let s_idx = (z * map.width as i32 + x) as usize;
                                air[s_idx] = map::TileType::PowerLine;
                                affected_chunks.insert(((x as u32) / 32, (z as u32) / 32));
                            }
                        }
                    }
                } else {
                    if x >= 0 && x < map.width as i32 && z >= 0 && z < map.height as i32 {
                        let idx = (z * map.width as i32 + x) as usize;
                        if let Some(layer) = map.layers.get_mut(&0) {
                            if layer[idx] != tile_type {
                                layer[idx] = tile_type;
                                affected_chunks.insert(((x as u32) / 32, (z as u32) / 32));
                            }
                        }
                    }
                }
            }
        }
    }

    for (cx, cz) in affected_chunks {
        chunk_events.send(ChunkUpdateEvent {
            chunk_x: cx,
            chunk_z: cz,
        });
    }
}
