use bevy::{prelude::*, utils::HashMap};
use noise::{NoiseFn, Perlin};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum TileType {
    #[default]
    Empty,
    Dirt,
    Water,
    Road,
    Residential,
    ResidentialOccupied1, // House (Level 1)
    ResidentialOccupied2, // House (Level 2)
    ResidentialOccupied3, // House (Level 3)
    Commercial,
    CommercialOccupied1, // Office (Level 1)
    CommercialOccupied2, // Office (Level 2)
    CommercialOccupied3, // Office (Level 3)
    Industrial,
    IndustrialOccupied1, // Factory (Level 1)
    IndustrialOccupied2, // Factory (Level 2)
    IndustrialOccupied3, // Factory (Level 3)
    PowerLine,
    PowerPlant,
}

#[derive(Resource)]
pub struct GameMap {
    pub width: u32,
    pub height: u32,
    pub layers: HashMap<i32, Vec<TileType>>,
}

impl Default for GameMap {
    fn default() -> Self {
        let mut layers = HashMap::new();
        layers.insert(0, vec![TileType::Dirt; 64 * 64]);
        Self {
            width: 64,
            height: 64,
            layers,
        }
    }
}

impl GameMap {
    pub fn new(width: u32, height: u32, water_threshold: f32) -> Self {
        let mut layers = HashMap::new();
        let area = (width * height) as usize;

        // Layer 0: Surface
        let mut surface = Vec::with_capacity(area);

        // Layer -1: Underground
        let underground = vec![TileType::Empty; area];

        let perlin = Perlin::new(rand::random());
        let scale = 0.1;

        for y in 0..height {
            for x in 0..width {
                let val = perlin.get([x as f64 * scale, y as f64 * scale]);
                let normalized = (val + 1.0) / 2.0;

                if normalized < water_threshold as f64 {
                    surface.push(TileType::Water);
                } else {
                    surface.push(TileType::Dirt);
                }
            }
        }

        layers.insert(0, surface);
        layers.insert(-1, underground);
        layers.insert(1, vec![TileType::Empty; area]); // Air Layer (Power Lines)

        Self {
            width,
            height,
            layers,
        }
    }
}

pub struct MapPlugin;

impl Plugin for MapPlugin {
    fn build(&self, app: &mut App) {
        app.init_resource::<GameMap>();
    }
}
