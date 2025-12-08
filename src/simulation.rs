use crate::{map::TileType, rendering::ChunkUpdateEvent, GameMap, GameState};
use bevy::prelude::*;
use rand::Rng;

#[derive(Resource)]
pub struct SimulationState {
    pub time: u64,    // Ticks (1 tick = 15 minutes)
    pub r_valve: i16, // Residential Demand (-2000 to 2000)
    pub c_valve: i16, // Commercial Demand
    pub i_valve: i16, // Industrial Demand
    pub total_pop: u32,
    pub num_jobs: u32,
    pub growth_rate: f32,
}

#[derive(Resource, Default)]
pub struct PowerGrid {
    pub powered_tiles: std::collections::HashSet<(i32, i32)>,
    pub net_power: i32, // Supply - Demand
}

impl Default for SimulationState {
    fn default() -> Self {
        Self {
            time: 0,
            r_valve: 0,
            c_valve: 0,
            i_valve: 0,
            total_pop: 0,
            num_jobs: 0,
            growth_rate: 1.0,
        }
    }
}

pub struct SimulationPlugin;

impl Plugin for SimulationPlugin {
    fn build(&self, app: &mut App) {
        app.init_resource::<SimulationState>()
            .init_resource::<PowerGrid>()
            .add_systems(
                FixedUpdate,
                (
                    simulation_tick,
                    census_system,
                    update_valves,
                    update_zones,
                    update_power_grid,
                )
                    .run_if(in_state(GameState::Game)),
            )
            .insert_resource(Time::<Fixed>::from_seconds(0.5));
    }
}

fn simulation_tick(mut sim_state: ResMut<SimulationState>) {
    sim_state.time += 1;
}

fn update_valves(mut sim_state: ResMut<SimulationState>) {
    let pop = sim_state.total_pop as i32;
    let jobs = sim_state.num_jobs as i32;

    let emp_ratio = if pop > 0 {
        jobs as f32 / pop as f32
    } else {
        1.0
    };

    if emp_ratio > 1.0 {
        sim_state.r_valve = ((emp_ratio - 1.0) * 2000.0).clamp(-2000.0, 2000.0) as i16;
        sim_state.c_valve = -500;
        sim_state.i_valve = -500;
    } else {
        sim_state.r_valve = -500;
        sim_state.c_valve = ((1.0 - emp_ratio) * 1500.0).clamp(-2000.0, 2000.0) as i16;
        sim_state.i_valve = ((1.0 - emp_ratio) * 1500.0).clamp(-2000.0, 2000.0) as i16;
    }

    if pop == 0 && jobs == 0 {
        sim_state.r_valve = 2000;
        sim_state.c_valve = 0;
        sim_state.i_valve = 0;
    }
}

fn update_zones(
    mut map: ResMut<GameMap>,
    sim_state: ResMut<SimulationState>,
    mut chunk_events: EventWriter<ChunkUpdateEvent>,
) {
    let width = map.width;
    let height = map.height;

    let mut rng = rand::thread_rng();

    let loops = (100.0 * sim_state.growth_rate) as usize;
    for _ in 0..loops {
        let x = rng.gen_range(0..width);
        let y = rng.gen_range(0..height);

        let idx = (y * width + x) as usize;

        if let Some(layers) = map.layers.get_mut(&0) {
            if idx < layers.len() {
                let tile_type = layers[idx];
                let mut new_tile = tile_type;
                let mut changed = false;

                match tile_type {
                    // Residential Growth
                    TileType::Residential => {
                        if sim_state.r_valve > 0
                            && has_road_neighbor(
                                layers,
                                width as i32,
                                height as i32,
                                x as i32,
                                y as i32,
                            )
                        {
                            if rng.gen_bool((0.1 * sim_state.growth_rate as f64).clamp(0.0, 1.0)) {
                                new_tile = TileType::ResidentialOccupied1;
                                changed = true;
                            }
                        }
                    }
                    TileType::ResidentialOccupied1 => {
                        if sim_state.r_valve > 500
                            && rng.gen_bool((0.05 * sim_state.growth_rate as f64).clamp(0.0, 1.0))
                        {
                            new_tile = TileType::ResidentialOccupied2;
                            changed = true;
                        } else if sim_state.r_valve < -500
                            && rng.gen_bool((0.05 * sim_state.growth_rate as f64).clamp(0.0, 1.0))
                        {
                            new_tile = TileType::Residential;
                            changed = true;
                        }
                    }
                    TileType::ResidentialOccupied2 => {
                        if sim_state.r_valve > 1000
                            && rng.gen_bool((0.05 * sim_state.growth_rate as f64).clamp(0.0, 1.0))
                        {
                            new_tile = TileType::ResidentialOccupied3;
                            changed = true;
                        } else if sim_state.r_valve < 0
                            && rng.gen_bool((0.05 * sim_state.growth_rate as f64).clamp(0.0, 1.0))
                        {
                            new_tile = TileType::ResidentialOccupied1;
                            changed = true;
                        }
                    }
                    TileType::ResidentialOccupied3 => {
                        if sim_state.r_valve < 500
                            && rng.gen_bool((0.05 * sim_state.growth_rate as f64).clamp(0.0, 1.0))
                        {
                            new_tile = TileType::ResidentialOccupied2;
                            changed = true;
                        }
                    }

                    // Commercial Growth
                    TileType::Commercial => {
                        if sim_state.c_valve > 0
                            && has_road_neighbor(
                                layers,
                                width as i32,
                                height as i32,
                                x as i32,
                                y as i32,
                            )
                        {
                            if rng.gen_bool((0.1 * sim_state.growth_rate as f64).clamp(0.0, 1.0)) {
                                new_tile = TileType::CommercialOccupied1;
                                changed = true;
                            }
                        }
                    }
                    TileType::CommercialOccupied1 => {
                        if sim_state.c_valve > 500
                            && rng.gen_bool((0.05 * sim_state.growth_rate as f64).clamp(0.0, 1.0))
                        {
                            new_tile = TileType::CommercialOccupied2;
                            changed = true;
                        } else if sim_state.c_valve < -500
                            && rng.gen_bool((0.05 * sim_state.growth_rate as f64).clamp(0.0, 1.0))
                        {
                            new_tile = TileType::Commercial;
                            changed = true;
                        }
                    }
                    TileType::CommercialOccupied2 => {
                        if sim_state.c_valve > 1000
                            && rng.gen_bool((0.05 * sim_state.growth_rate as f64).clamp(0.0, 1.0))
                        {
                            new_tile = TileType::CommercialOccupied3;
                            changed = true;
                        } else if sim_state.c_valve < 0
                            && rng.gen_bool((0.05 * sim_state.growth_rate as f64).clamp(0.0, 1.0))
                        {
                            new_tile = TileType::CommercialOccupied1;
                            changed = true;
                        }
                    }
                    TileType::CommercialOccupied3 => {
                        if sim_state.c_valve < 500
                            && rng.gen_bool((0.05 * sim_state.growth_rate as f64).clamp(0.0, 1.0))
                        {
                            new_tile = TileType::CommercialOccupied2;
                            changed = true;
                        }
                    }

                    // Industrial Growth
                    TileType::Industrial => {
                        if sim_state.i_valve > 0
                            && has_road_neighbor(
                                layers,
                                width as i32,
                                height as i32,
                                x as i32,
                                y as i32,
                            )
                        {
                            if rng.gen_bool((0.1 * sim_state.growth_rate as f64).clamp(0.0, 1.0)) {
                                new_tile = TileType::IndustrialOccupied1;
                                changed = true;
                            }
                        }
                    }
                    TileType::IndustrialOccupied1 => {
                        if sim_state.i_valve > 500
                            && rng.gen_bool((0.05 * sim_state.growth_rate as f64).clamp(0.0, 1.0))
                        {
                            new_tile = TileType::IndustrialOccupied2;
                            changed = true;
                        } else if sim_state.i_valve < -500
                            && rng.gen_bool((0.05 * sim_state.growth_rate as f64).clamp(0.0, 1.0))
                        {
                            new_tile = TileType::Industrial;
                            changed = true;
                        }
                    }
                    TileType::IndustrialOccupied2 => {
                        if sim_state.i_valve > 1000
                            && rng.gen_bool((0.05 * sim_state.growth_rate as f64).clamp(0.0, 1.0))
                        {
                            new_tile = TileType::IndustrialOccupied3;
                            changed = true;
                        } else if sim_state.i_valve < 0
                            && rng.gen_bool((0.05 * sim_state.growth_rate as f64).clamp(0.0, 1.0))
                        {
                            new_tile = TileType::IndustrialOccupied1;
                            changed = true;
                        }
                    }
                    TileType::IndustrialOccupied3 => {
                        if sim_state.i_valve < 500
                            && rng.gen_bool((0.05 * sim_state.growth_rate as f64).clamp(0.0, 1.0))
                        {
                            new_tile = TileType::IndustrialOccupied2;
                            changed = true;
                        }
                    }
                    _ => {}
                }

                if changed {
                    layers[idx] = new_tile;
                    chunk_events.send(ChunkUpdateEvent {
                        chunk_x: x as u32 / 32,
                        chunk_z: y as u32 / 32,
                    });
                }
            }
        }
    }
}

fn has_road_neighbor(tiles: &[TileType], w: i32, h: i32, x: i32, y: i32) -> bool {
    let radius = 3;
    for dy in -radius..=radius {
        for dx in -radius..=radius {
            if dx == 0 && dy == 0 {
                continue;
            }

            let nx = x + dx;
            let ny = y + dy;

            if nx >= 0 && nx < w && ny >= 0 && ny < h {
                let idx = (ny * w + nx) as usize;
                if tiles[idx] == TileType::Road {
                    return true;
                }
            }
        }
    }
    false
}

fn census_system(map: Res<GameMap>, mut sim_state: ResMut<SimulationState>) {
    // Run census every day (96 ticks)
    if sim_state.time % 96 != 0 {
        return;
    }

    let mut r_pop = 0;
    let mut jobs = 0;

    if let Some(layers) = map.layers.get(&0) {
        for tile in layers {
            match tile {
                TileType::ResidentialOccupied1 => r_pop += 8,
                TileType::ResidentialOccupied2 => r_pop += 16,
                TileType::ResidentialOccupied3 => r_pop += 24,
                TileType::CommercialOccupied1 => jobs += 8,
                TileType::CommercialOccupied2 => jobs += 16,
                TileType::CommercialOccupied3 => jobs += 24,
                TileType::IndustrialOccupied1 => jobs += 8,
                TileType::IndustrialOccupied2 => jobs += 16,
                TileType::IndustrialOccupied3 => jobs += 24,
                _ => {}
            }
        }
    }

    sim_state.total_pop = r_pop;
    sim_state.num_jobs = jobs;
}

fn update_power_grid(
    map: Res<GameMap>,
    mut power_grid: ResMut<PowerGrid>,
    sim_state: Res<SimulationState>,
) {
    if sim_state.time % 4 != 0 {
        return;
    } // Update every hour (4 ticks)

    let mut visited = std::collections::HashSet::new();
    let mut queue = std::collections::VecDeque::new();
    let mut supply = 0;
    let mut demand = 0;

    // 1. Find Power Sources (Plants)
    if let Some(surface) = map.layers.get(&0) {
        for (i, tile) in surface.iter().enumerate() {
            if *tile == TileType::PowerPlant {
                let x = (i as u32 % map.width) as i32;
                let y = (i as u32 / map.width) as i32;
                queue.push_back((x, y));
                visited.insert((x, y));
                supply += 500; // Each plant generates 500 units
            }
        }
    }

    // 2. BFS Network Propagation
    let mut network_nodes = std::collections::HashSet::new();
    while let Some((cx, cy)) = queue.pop_front() {
        network_nodes.insert((cx, cy));

        let neighbors = [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)];

        for (nx, ny) in neighbors {
            if nx >= 0 && nx < map.width as i32 && ny >= 0 && ny < map.height as i32 {
                if !visited.contains(&(nx, ny)) {
                    let idx = (ny as u32 * map.width + nx as u32) as usize;
                    let mut conducted = false;

                    // Check Surface (Buildings/Plants)
                    if let Some(surface) = map.layers.get(&0) {
                        let tile = surface[idx];
                        if is_conductor(tile) {
                            conducted = true;
                        }
                    }

                    // Check Air (Power Lines)
                    if !conducted {
                        if let Some(air) = map.layers.get(&1) {
                            if air[idx] == TileType::PowerLine {
                                conducted = true;
                            }
                        }
                    }

                    if conducted {
                        visited.insert((nx, ny));
                        queue.push_back((nx, ny));
                    }
                }
            }
        }
    }

    // 3. Calculate Demand & Power Status
    power_grid.powered_tiles.clear();

    // Check neighbors of network nodes for consumers (radius 1)
    // Actually, network nodes themselves are powered if they are buildings
    // AND adjacent buildings touching the network get power

    // Simplified: Any consumer touching a 'Network Node' or IS a 'Network Node' is potentially powered.
    // We already traversed conductors. Now let's calculate demand for all connected conductors.

    let mut consumers = std::collections::HashSet::new();

    if let Some(surface) = map.layers.get(&0) {
        for &(cx, cy) in &network_nodes {
            // Check self
            let idx = (cy as u32 * map.width + cx as u32) as usize;
            let tile_type = surface[idx];
            let cons = get_power_consumption(tile_type);
            if cons > 0 {
                consumers.insert((cx, cy));
                demand += cons;
            }

            // Check immediate neighbors (Buildings connect to lines)
            let neighbors = [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)];
            for (nx, ny) in neighbors {
                if nx >= 0 && nx < map.width as i32 && ny >= 0 && ny < map.height as i32 {
                    let nidx = (ny as u32 * map.width + nx as u32) as usize;
                    let ntile = surface[nidx];
                    let ncons = get_power_consumption(ntile);
                    if ncons > 0 {
                        consumers.insert((nx, ny));
                        // Note: We might double count if we iterate simplistically,
                        // but using a set for consumers solves uniqueness.
                        // However demand calculation needs to iterate the set AFTER finding all consumers.
                    }
                }
            }
        }
    }

    // Recalculate true demand from unique set
    demand = 0;
    if let Some(surface) = map.layers.get(&0) {
        for &(cx, cy) in &consumers {
            let idx = (cy as u32 * map.width + cx as u32) as usize;
            let tile = surface[idx];
            demand += get_power_consumption(tile);
        }
    }

    power_grid.net_power = supply - demand;

    // 4. Set Powered Status (Brownout Logic)
    if supply >= demand {
        power_grid.powered_tiles = consumers;
        // Also include the lines/plants themselves visual feedback?
        // Maybe separate? For now, powered_tiles tracks CONSUMERS with power.
        // Let's add network nodes too so lines glow?
        // User asked for "residental buildings should display wheteher they have power"
        // So tracking consumers is the priority.
    } else {
        // Brownout! Nobody gets power (or random subset? SimCity 1 just flickered brownouts)
        // For simplicity: No power if overloaded.
        power_grid.powered_tiles.clear();
    }
}

fn is_conductor(t: TileType) -> bool {
    matches!(
        t,
        TileType::PowerPlant
            | TileType::PowerLine
            | TileType::ResidentialOccupied1
            | TileType::ResidentialOccupied2
            | TileType::ResidentialOccupied3
            | TileType::CommercialOccupied1
            | TileType::CommercialOccupied2
            | TileType::CommercialOccupied3
            | TileType::IndustrialOccupied1
            | TileType::IndustrialOccupied2
            | TileType::IndustrialOccupied3
    )
}

pub fn get_power_consumption(t: TileType) -> i32 {
    match t {
        TileType::ResidentialOccupied1 => 1,
        TileType::ResidentialOccupied2 => 2,
        TileType::ResidentialOccupied3 => 3,
        TileType::CommercialOccupied1 => 2,
        TileType::CommercialOccupied2 => 4,
        TileType::CommercialOccupied3 => 6,
        TileType::IndustrialOccupied1 => 4,
        TileType::IndustrialOccupied2 => 8,
        TileType::IndustrialOccupied3 => 12,
        _ => 0,
    }
}
