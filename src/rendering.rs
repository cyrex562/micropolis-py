use crate::{map::TileType, GameMap, GameState};
use bevy::{
    input::mouse::{MouseMotion, MouseWheel},
    prelude::*,
    render::{
        mesh::{Indices, PrimitiveTopology, VertexAttributeValues},
        render_asset::RenderAssetUsages,
    },
};

#[derive(Event)]
pub struct ChunkUpdateEvent {
    pub chunk_x: u32,
    pub chunk_z: u32,
}

pub struct RenderingPlugin;

impl Plugin for RenderingPlugin {
    fn build(&self, app: &mut App) {
        app.init_resource::<ViewMode>()
            .init_resource::<CursorMapPosition>()
            .init_resource::<GridState>()
            .add_event::<ChunkUpdateEvent>()
            .add_systems(Startup, setup_camera)
            .add_systems(OnEnter(GameState::Game), spawn_all_chunks)
            .add_systems(
                Update,
                (
                    camera_controller,
                    update_layer_visibility,
                    grid_visibility_system,
                    raycast_system,
                    draw_cursor_gizmo,
                    update_chunks,
                )
                    .run_if(in_state(GameState::Game)),
            );
    }
}

#[derive(Resource, Default, Debug, Clone, Copy)]
pub struct CursorMapPosition {
    pub x: Option<i32>,
    pub z: Option<i32>,
}

#[derive(Resource, Default, PartialEq, Eq, Clone, Copy, Debug)]
pub enum ViewMode {
    #[default]
    Surface,
    Underground,
}

#[derive(Component)]
pub struct MapLayer(pub i32);

#[derive(Component)]
pub struct CameraController {
    pub scroll_speed: f32,
    pub rotate_speed: f32,
    pub zoom_speed: f32,
    pub pitch: f32,
    pub yaw: f32,
    pub distance: f32,
    pub target: Vec3,
}

impl Default for CameraController {
    fn default() -> Self {
        Self {
            scroll_speed: 20.0,
            rotate_speed: 2.0,
            zoom_speed: 5.0,
            pitch: -std::f32::consts::FRAC_PI_4,
            yaw: 0.0,
            distance: 50.0,
            target: Vec3::new(32.0, 0.0, 32.0),
        }
    }
}

// --- Chunking Logic ---
const CHUNK_SIZE: u32 = 32;

struct MeshBuilder {
    positions: Vec<[f32; 3]>,
    normals: Vec<[f32; 3]>,
    uvs: Vec<[f32; 2]>,
    indices: Vec<u32>,
}

impl MeshBuilder {
    fn new() -> Self {
        Self {
            positions: Vec::new(),
            normals: Vec::new(),
            uvs: Vec::new(),
            indices: Vec::new(),
        }
    }

    fn add_block(&mut self, x: f32, y: f32, z: f32, w: f32, h: f32, sides: [bool; 4]) {
        // sides: [Left, Right, Back, Front]

        // Top Face (Always)
        self.add_quad(
            [
                [x, y + h, z],
                [x, y + h, z + w],
                [x + w, y + h, z + w],
                [x + w, y + h, z],
            ],
            [0.0, 1.0, 0.0],
        );

        // Front (Z+)
        if sides[3] {
            self.add_quad(
                [
                    [x, y, z + w],
                    [x + w, y, z + w],
                    [x + w, y + h, z + w],
                    [x, y + h, z + w],
                ],
                [0.0, 0.0, 1.0],
            );
        }

        // Back (Z-)
        if sides[2] {
            self.add_quad(
                [[x + w, y, z], [x, y, z], [x, y + h, z], [x + w, y + h, z]],
                [0.0, 0.0, -1.0],
            );
        }

        // Left (X-)
        if sides[0] {
            self.add_quad(
                [[x, y, z], [x, y, z + w], [x, y + h, z + w], [x, y + h, z]],
                [-1.0, 0.0, 0.0],
            );
        }

        // Right (X+)
        if sides[1] {
            self.add_quad(
                [
                    [x + w, y, z + w],
                    [x + w, y, z],
                    [x + w, y + h, z],
                    [x + w, y + h, z + w],
                ],
                [1.0, 0.0, 0.0],
            );
        }
    }

    fn add_quad(&mut self, verts: [[f32; 3]; 4], normal: [f32; 3]) {
        let start_idx = self.positions.len() as u32;
        self.positions.extend_from_slice(&verts);
        for _ in 0..4 {
            self.normals.push(normal);
            self.uvs.push([0.0, 0.0]); // Placeholder UVs
        }
        // CCW Indices
        self.indices.extend_from_slice(&[
            start_idx,
            start_idx + 1,
            start_idx + 2,
            start_idx,
            start_idx + 2,
            start_idx + 3,
        ]);
    }

    fn build(self) -> Mesh {
        let mut mesh = Mesh::new(
            PrimitiveTopology::TriangleList,
            RenderAssetUsages::default(),
        );
        mesh.insert_attribute(Mesh::ATTRIBUTE_POSITION, self.positions);
        mesh.insert_attribute(Mesh::ATTRIBUTE_NORMAL, self.normals);
        mesh.insert_attribute(Mesh::ATTRIBUTE_UV_0, self.uvs);
        mesh.insert_indices(Indices::U32(self.indices));
        mesh
    }
}

#[derive(Component)]
pub struct MapRoot;

#[derive(Component)]
struct ChunkCoord {
    x: u32,
    z: u32,
}

#[derive(Component)]
struct GridPlane;

#[derive(Resource)]
pub struct GridState {
    pub visible: bool,
}

impl Default for GridState {
    fn default() -> Self {
        Self { visible: true }
    }
}

fn spawn_all_chunks(
    mut commands: Commands,
    map: Res<GameMap>,
    mut meshes: ResMut<Assets<Mesh>>,
    mut materials: ResMut<Assets<StandardMaterial>>,
    mut images: ResMut<Assets<Image>>,
    mut events: EventWriter<ChunkUpdateEvent>,
) {
    let underground_mat = materials.add(Color::srgb(0.3, 0.3, 0.3));

    // Create Procedural Grid Texture
    const GRID_SIZE: u32 = 64;
    let mut pixel_data = Vec::with_capacity((GRID_SIZE * GRID_SIZE * 4) as usize);
    for y in 0..GRID_SIZE {
        for x in 0..GRID_SIZE {
            // White lines at edges, transparent inside
            // Thinner lines: checking against 1 pixel
            let is_line = x < 2 || y < 2; // Thicker lines (2px)
            if is_line {
                pixel_data.extend_from_slice(&[255, 255, 255, 150]); // More opaque
            } else {
                pixel_data.extend_from_slice(&[255, 255, 255, 0]); // Transparent White (better blending)
            }
        }
    }

    let mut image = Image::new_fill(
        bevy::render::render_resource::Extent3d {
            width: GRID_SIZE,
            height: GRID_SIZE,
            depth_or_array_layers: 1,
        },
        bevy::render::render_resource::TextureDimension::D2,
        &pixel_data,
        bevy::render::render_resource::TextureFormat::Rgba8Unorm,
        RenderAssetUsages::RENDER_WORLD,
    );

    image.sampler = bevy::image::ImageSampler::Descriptor(bevy::image::ImageSamplerDescriptor {
        address_mode_u: bevy::image::ImageAddressMode::Repeat,
        address_mode_v: bevy::image::ImageAddressMode::Repeat,
        mag_filter: bevy::image::ImageFilterMode::Nearest,
        min_filter: bevy::image::ImageFilterMode::Nearest,
        mipmap_filter: bevy::image::ImageFilterMode::Nearest,
        ..default()
    });

    let grid_texture_handle = images.add(image);

    let grid_mat = materials.add(StandardMaterial {
        base_color_texture: Some(grid_texture_handle),
        alpha_mode: AlphaMode::Blend,
        unlit: true,
        ..default()
    });

    // Create Grid Mesh and Scale UVs
    let mut plane = Plane3d::default();
    plane.half_size = Vec2::new(map.width as f32 / 2.0, map.height as f32 / 2.0);
    let mut mesh = Mesh::from(plane);

    if let Some(VertexAttributeValues::Float32x2(uvs)) = mesh.attribute_mut(Mesh::ATTRIBUTE_UV_0) {
        for uv in uvs {
            uv[0] *= map.width as f32;
            uv[1] *= map.height as f32;
        }
    }
    let grid_mesh = meshes.add(mesh);

    commands
        .spawn((
            Transform::default(),
            Visibility::default(),
            MapRoot,
            Name::new("MapRoot"),
        ))
        .with_children(|parent| {
            // Layer -1: Underground Map (Floor Plane)
            let floor_size_x = map.width as f32;
            let floor_size_z = map.height as f32;
            let floor_mesh = meshes.add(Cuboid::new(floor_size_x, 0.1, floor_size_z));

            parent.spawn((
                Mesh3d(floor_mesh),
                MeshMaterial3d(underground_mat.clone()),
                Transform::from_xyz(
                    (map.width as f32) / 2.0 - 0.5,
                    -1.0,
                    (map.height as f32) / 2.0 - 0.5,
                ),
                MapLayer(-1),
            ));

            // Grid Plane (Layer 0, slightly above)
            parent.spawn((
                Mesh3d(grid_mesh),
                MeshMaterial3d(grid_mat),
                Transform::from_xyz(
                    floor_size_x / 2.0, // Center X aligned with tiles
                    1.05,               // Just above tiles (which end at y=1.0)
                    floor_size_z / 2.0, // Center Z
                ),
                GridPlane,
                Visibility::Inherited, // Visible by default
            ));
        });

    // Initial Chunk Spawning via Events
    let chunks_x = (map.width as f32 / CHUNK_SIZE as f32).ceil() as u32;
    let chunks_z = (map.height as f32 / CHUNK_SIZE as f32).ceil() as u32;

    for cz in 0..chunks_z {
        for cx in 0..chunks_x {
            events.send(ChunkUpdateEvent {
                chunk_x: cx,
                chunk_z: cz,
            });
        }
    }
}

fn update_chunks(
    mut commands: Commands,
    mut events: EventReader<ChunkUpdateEvent>,
    map: Res<GameMap>,
    mut meshes: ResMut<Assets<Mesh>>,
    mut materials: ResMut<Assets<StandardMaterial>>,
    root_query: Query<Entity, With<MapRoot>>,
    chunk_query: Query<(Entity, &ChunkCoord)>,
) {
    let dirt_mat = materials.add(Color::srgb(0.4, 0.3, 0.2));
    let water_mat = materials.add(Color::srgb(0.2, 0.4, 0.8));
    let road_mat = materials.add(Color::srgb(0.2, 0.2, 0.2));

    // Transparent Base Materials
    let res_mat = materials.add(StandardMaterial {
        base_color: Color::srgba(0.2, 0.8, 0.2, 0.5),
        alpha_mode: AlphaMode::Blend,
        ..default()
    });
    let com_mat = materials.add(StandardMaterial {
        base_color: Color::srgba(0.2, 0.2, 0.8, 0.5),
        alpha_mode: AlphaMode::Blend,
        ..default()
    });
    let ind_mat = materials.add(StandardMaterial {
        base_color: Color::srgba(0.8, 0.8, 0.2, 0.5),
        alpha_mode: AlphaMode::Blend,
        ..default()
    });

    // Solid Building Materials
    let res_build_mat = materials.add(Color::srgb(0.4, 1.0, 0.4));
    let com_build_mat = materials.add(Color::srgb(0.4, 0.4, 1.0));
    let ind_build_mat = materials.add(Color::srgb(1.0, 1.0, 0.4));
    let power_plant_mat = materials.add(Color::srgb(1.0, 0.2, 0.2)); // Red Plant

    // Power Line (Yellow-ish, Unlit)
    let power_line_mat = materials.add(StandardMaterial {
        base_color: Color::srgba(1.0, 1.0, 0.0, 0.8),
        alpha_mode: AlphaMode::Blend,
        unlit: true,
        cull_mode: None, // Double sided
        ..default()
    });

    let root_entity = match root_query.get_single() {
        Ok(e) => e,
        Err(_) => return, // MapRoot not ready
    };

    // 1. Identify Dirty Chunks
    let mut dirty_chunks = std::collections::HashSet::new();
    for event in events.read() {
        dirty_chunks.insert((event.chunk_x, event.chunk_z));
    }

    if dirty_chunks.is_empty() {
        return;
    }

    // 2. Despawn Old Chunks
    for (entity, coord) in chunk_query.iter() {
        if dirty_chunks.contains(&(coord.x, coord.z)) {
            commands.entity(entity).despawn_recursive();
        }
    }

    // 3. Spawn New Chunks
    commands.entity(root_entity).with_children(|parent| {
        let surface_tiles_opt = map.layers.get(&0);
        let air_tiles_opt = map.layers.get(&1);

        if let Some(surface_tiles) = surface_tiles_opt {
            for (cx, cz) in dirty_chunks {
                let mut dirt_builder = MeshBuilder::new();
                let mut water_builder = MeshBuilder::new();
                let mut road_builder = MeshBuilder::new();

                let mut res_builder = MeshBuilder::new();
                let mut com_builder = MeshBuilder::new();
                let mut ind_builder = MeshBuilder::new();

                let mut res_build_builder = MeshBuilder::new();
                let mut com_build_builder = MeshBuilder::new();
                let mut ind_build_builder = MeshBuilder::new();

                let mut power_plant_builder = MeshBuilder::new();
                let mut power_line_builder = MeshBuilder::new();

                let start_x = cx * CHUNK_SIZE;
                let start_z = cz * CHUNK_SIZE;
                let end_x = (start_x + CHUNK_SIZE).min(map.width);
                let end_z = (start_z + CHUNK_SIZE).min(map.height);

                let map_w = map.width as i32;
                let map_h = map.height as i32;

                // Helper: Get Height
                let get_height = |tx: i32, tz: i32| -> f32 {
                    if tx < 0 || tz < 0 || tx >= map_w || tz >= map_h {
                        return -100.0;
                    }
                    let idx = (tz * map_w + tx) as usize;
                    match surface_tiles[idx] {
                        TileType::Empty => -100.0,
                        TileType::Water => 0.6,
                        TileType::Road => 1.05,
                        _ => 1.0,
                    }
                };

                for z in start_z..end_z {
                    for x in start_x..end_x {
                        let idx = (z * map.width + x) as usize;
                        let fx = x as f32;
                        let fz = z as f32;

                        // --- Layer 0: Surface ---
                        if let Some(tile) = surface_tiles.get(idx) {
                            if *tile != TileType::Empty {
                                let ix = x as i32;
                                let iz = z as i32;
                                let my_height = get_height(ix, iz);
                                let sides = [
                                    get_height(ix - 1, iz) < my_height,
                                    get_height(ix + 1, iz) < my_height,
                                    get_height(ix, iz - 1) < my_height,
                                    get_height(ix, iz + 1) < my_height,
                                ];

                                match *tile {
                                    TileType::Water => {
                                        water_builder.add_block(fx, -0.2, fz, 1.0, 0.8, sides)
                                    }
                                    TileType::Road => {
                                        road_builder.add_block(fx, 0.0, fz, 1.0, 1.05, sides)
                                    }
                                    TileType::Residential => {
                                        res_builder.add_block(fx, 0.0, fz, 1.0, 1.0, sides)
                                    }
                                    TileType::ResidentialOccupied1 => {
                                        res_builder.add_block(fx, 0.0, fz, 1.0, 1.0, sides);
                                        res_build_builder.add_block(
                                            fx + 0.2,
                                            1.0,
                                            fz + 0.2,
                                            0.6,
                                            1.0,
                                            [true; 4],
                                        );
                                    }
                                    TileType::ResidentialOccupied2 => {
                                        res_builder.add_block(fx, 0.0, fz, 1.0, 1.0, sides);
                                        res_build_builder.add_block(
                                            fx + 0.1,
                                            1.0,
                                            fz + 0.1,
                                            0.8,
                                            2.0,
                                            [true; 4],
                                        );
                                    }
                                    TileType::ResidentialOccupied3 => {
                                        res_builder.add_block(fx, 0.0, fz, 1.0, 1.0, sides);
                                        res_build_builder.add_block(
                                            fx + 0.1,
                                            1.0,
                                            fz + 0.1,
                                            0.8,
                                            3.0,
                                            [true; 4],
                                        );
                                    }
                                    TileType::Commercial => {
                                        com_builder.add_block(fx, 0.0, fz, 1.0, 1.0, sides)
                                    }
                                    TileType::CommercialOccupied1 => {
                                        com_builder.add_block(fx, 0.0, fz, 1.0, 1.0, sides);
                                        com_build_builder.add_block(
                                            fx + 0.1,
                                            1.0,
                                            fz + 0.1,
                                            0.8,
                                            1.0,
                                            [true; 4],
                                        );
                                    }
                                    TileType::CommercialOccupied2 => {
                                        com_builder.add_block(fx, 0.0, fz, 1.0, 1.0, sides);
                                        com_build_builder.add_block(
                                            fx + 0.1,
                                            1.0,
                                            fz + 0.1,
                                            0.8,
                                            2.0,
                                            [true; 4],
                                        );
                                    }
                                    TileType::CommercialOccupied3 => {
                                        com_builder.add_block(fx, 0.0, fz, 1.0, 1.0, sides);
                                        com_build_builder.add_block(
                                            fx + 0.1,
                                            1.0,
                                            fz + 0.1,
                                            0.8,
                                            3.0,
                                            [true; 4],
                                        );
                                    }
                                    TileType::Industrial => {
                                        ind_builder.add_block(fx, 0.0, fz, 1.0, 1.0, sides)
                                    }
                                    TileType::IndustrialOccupied1 => {
                                        ind_builder.add_block(fx, 0.0, fz, 1.0, 1.0, sides);
                                        ind_build_builder
                                            .add_block(fx, 1.0, fz, 1.0, 1.0, [true; 4]);
                                    }
                                    TileType::IndustrialOccupied2 => {
                                        ind_builder.add_block(fx, 0.0, fz, 1.0, 1.0, sides);
                                        ind_build_builder
                                            .add_block(fx, 1.0, fz, 1.0, 2.0, [true; 4]);
                                    }
                                    TileType::IndustrialOccupied3 => {
                                        ind_builder.add_block(fx, 0.0, fz, 1.0, 1.0, sides);
                                        ind_build_builder
                                            .add_block(fx, 1.0, fz, 1.0, 3.0, [true; 4]);
                                    }
                                    TileType::PowerPlant => {
                                        // Foundation
                                        ind_builder.add_block(fx, 0.0, fz, 1.0, 1.0, sides);
                                        // Plant Block
                                        power_plant_builder.add_block(
                                            fx + 0.1,
                                            1.0,
                                            fz + 0.1,
                                            0.8,
                                            0.8,
                                            [true; 4],
                                        );
                                    }
                                    _ => dirt_builder.add_block(fx, 0.0, fz, 1.0, 1.0, sides),
                                }
                            }
                        }

                        // --- Layer 1: Air (Power Lines) ---
                        if let Some(air_tiles) = air_tiles_opt {
                            if let Some(tile) = air_tiles.get(idx) {
                                if *tile == TileType::PowerLine {
                                    // Draw a floating quad at Y=1.2
                                    // Checking neighbors could help draw nice connections, but for now just a "plus" or "square"
                                    // Let's draw a small cable cross
                                    let h = 1.2;
                                    let w = 0.2;
                                    let L = 0.5 - w / 2.0;
                                    let R = 0.5 + w / 2.0;

                                    // Center Hub
                                    power_line_builder.add_quad(
                                        [
                                            [fx + L, h, fz + L],
                                            [fx + L, h, fz + R],
                                            [fx + R, h, fz + R],
                                            [fx + R, h, fz + L],
                                        ],
                                        [0.0, 1.0, 0.0],
                                    );

                                    // Arms (to edges) - Ideally check if neighbor has power line, but for now fill simple cross
                                    power_line_builder.add_quad(
                                        [
                                            [fx, h, fz + L],
                                            [fx, h, fz + R],
                                            [fx + L, h, fz + R],
                                            [fx + L, h, fz + L],
                                        ],
                                        [0.0, 1.0, 0.0],
                                    ); // Left
                                    power_line_builder.add_quad(
                                        [
                                            [fx + R, h, fz + L],
                                            [fx + R, h, fz + R],
                                            [fx + 1.0, h, fz + R],
                                            [fx + 1.0, h, fz + L],
                                        ],
                                        [0.0, 1.0, 0.0],
                                    ); // Right
                                    power_line_builder.add_quad(
                                        [
                                            [fx + L, h, fz],
                                            [fx + L, h, fz + L],
                                            [fx + R, h, fz + L],
                                            [fx + R, h, fz],
                                        ],
                                        [0.0, 1.0, 0.0],
                                    ); // Back
                                    power_line_builder.add_quad(
                                        [
                                            [fx + L, h, fz + R],
                                            [fx + L, h, fz + 1.0],
                                            [fx + R, h, fz + 1.0],
                                            [fx + R, h, fz + R],
                                        ],
                                        [0.0, 1.0, 0.0],
                                    ); // Front
                                }
                            }
                        }
                    }
                }

                // Spawn Meshes Helper
                let mut spawn_mesh = |builder: MeshBuilder,
                                      mat: Handle<StandardMaterial>,
                                      name: &str,
                                      layer: i32| {
                    if !builder.positions.is_empty() {
                        parent.spawn((
                            Mesh3d(meshes.add(builder.build())),
                            MeshMaterial3d(mat),
                            Transform::default(),
                            MapLayer(layer),
                            ChunkCoord { x: cx, z: cz },
                            Name::new(format!("{}_{}_{}", name, cx, cz)),
                        ));
                    }
                };

                spawn_mesh(dirt_builder, dirt_mat.clone(), "Chunk_Dirt", 0);
                spawn_mesh(water_builder, water_mat.clone(), "Chunk_Water", 0);
                spawn_mesh(road_builder, road_mat.clone(), "Chunk_Road", 0);
                spawn_mesh(res_builder, res_mat.clone(), "Chunk_Res", 0);
                spawn_mesh(com_builder, com_mat.clone(), "Chunk_Com", 0);
                spawn_mesh(ind_builder, ind_mat.clone(), "Chunk_Ind", 0);

                spawn_mesh(
                    res_build_builder,
                    res_build_mat.clone(),
                    "Chunk_Res_Build",
                    0,
                );
                spawn_mesh(
                    com_build_builder,
                    com_build_mat.clone(),
                    "Chunk_Com_Build",
                    0,
                );
                spawn_mesh(
                    ind_build_builder,
                    ind_build_mat.clone(),
                    "Chunk_Ind_Build",
                    0,
                );
                spawn_mesh(
                    power_plant_builder,
                    power_plant_mat.clone(),
                    "Chunk_PowerPlant",
                    0,
                );

                spawn_mesh(
                    power_line_builder,
                    power_line_mat.clone(),
                    "Chunk_PowerLine",
                    1,
                ); // Layer 1
            }
        }
    });
}

fn setup_camera(mut commands: Commands) {
    commands.spawn((
        Camera3d::default(),
        Transform::default(),
        CameraController::default(),
    ));

    commands.spawn((
        DirectionalLight::default(),
        Transform::from_rotation(Quat::from_rotation_x(-std::f32::consts::FRAC_PI_4)),
    ));
}

fn camera_controller(
    time: Res<Time>,
    mut mouse_motion_events: EventReader<MouseMotion>,
    mut mouse_wheel_events: EventReader<MouseWheel>,
    mouse_button_input: Res<ButtonInput<MouseButton>>,
    key_input: Res<ButtonInput<KeyCode>>,
    mut query: Query<(&mut Transform, &mut CameraController)>,
) {
    let dt = time.delta_secs();

    for (mut transform, mut controller) in query.iter_mut() {
        // --- 1. Keyboard Panning (WASD / Arrows) ---
        let mut panning = Vec3::ZERO;
        let forward = Vec3::new(controller.yaw.sin(), 0.0, controller.yaw.cos());
        let right = Vec3::new(controller.yaw.cos(), 0.0, -controller.yaw.sin());

        if key_input.pressed(KeyCode::KeyW) || key_input.pressed(KeyCode::ArrowUp) {
            panning -= forward;
        }
        if key_input.pressed(KeyCode::KeyS) || key_input.pressed(KeyCode::ArrowDown) {
            panning += forward;
        }
        if key_input.pressed(KeyCode::KeyA) || key_input.pressed(KeyCode::ArrowLeft) {
            panning -= right;
        }
        if key_input.pressed(KeyCode::KeyD) || key_input.pressed(KeyCode::ArrowRight) {
            panning += right;
        }

        if panning != Vec3::ZERO {
            panning = panning.normalize() * controller.scroll_speed * dt;
            controller.target += panning;
        }

        // --- 2. Rotation (Q/E) ---
        if key_input.pressed(KeyCode::KeyQ) {
            controller.yaw -= controller.rotate_speed * dt;
        }
        if key_input.pressed(KeyCode::KeyE) {
            controller.yaw += controller.rotate_speed * dt;
        }

        // --- 3. Zoom (Mouse Wheel) ---
        for event in mouse_wheel_events.read() {
            controller.distance -= event.y * controller.zoom_speed;
            controller.distance = controller.distance.clamp(5.0, 200.0);
        }

        // --- 4. Mouse Pan/Rotate (Optional, Middle Click?) ---
        if mouse_button_input.pressed(MouseButton::Middle) {
            for event in mouse_motion_events.read() {
                // Rotate with Mouse Drag
                controller.yaw -= event.delta.x * 0.01;
                // Pitch? (Optional)
            }
        }

        // Update Transform
        let rotation = Quat::from_euler(EulerRot::YXZ, controller.yaw, controller.pitch, 0.0);
        let offset = rotation * Vec3::new(0.0, 0.0, controller.distance);
        transform.translation = controller.target + offset;
        transform.look_at(controller.target, Vec3::Y);
    }
}

fn update_layer_visibility(
    view_mode: Res<ViewMode>,
    mut query: Query<(&mut Visibility, &MapLayer)>,
) {
    // Note: GridPlane has MapLayer(0) assigned in spawn_all_chunks
    // So it will be handled by the main query loop below.

    // Logic:
    // ViewMode::Surface: Show Layer 0, Hide Layer -1 (Underground)
    // ViewMode::Underground: Hide Layer 0, Show Layer -1

    let target_layer = match *view_mode {
        ViewMode::Surface => 0,
        ViewMode::Underground => -1,
    };

    for (mut vis, layer) in query.iter_mut() {
        if layer.0 == target_layer {
            *vis = Visibility::Inherited;
        } else {
            *vis = Visibility::Hidden;
        }
    }
}

fn raycast_system(
    camera_query: Query<(&Camera, &GlobalTransform)>,
    window_query: Query<&Window>,
    map: Res<GameMap>,
    mut cursor_pos: ResMut<CursorMapPosition>,
) {
    let (camera, camera_transform) = camera_query.single();
    let window = window_query.single();

    if let Some(cursor_position) = window.cursor_position() {
        if let Ok(ray) = camera.viewport_to_world(camera_transform, cursor_position) {
            // Intersect with Plane at Y=0
            let distance = ray.intersect_plane(Vec3::ZERO, InfinitePlane3d::new(Vec3::Y));

            if let Some(dist) = distance {
                let world_point = ray.origin + ray.direction * dist;
                let x = world_point.x.round() as i32;
                let z = world_point.z.round() as i32;

                if x >= 0 && x < map.width as i32 && z >= 0 && z < map.height as i32 {
                    cursor_pos.x = Some(x);
                    cursor_pos.z = Some(z);
                } else {
                    cursor_pos.x = None;
                    cursor_pos.z = None;
                }
                return;
            }
        }
    }
    cursor_pos.x = None;
    cursor_pos.z = None;
}

fn draw_cursor_gizmo(cursor_pos: Res<CursorMapPosition>, mut gizmos: Gizmos) {
    if let (Some(x), Some(z)) = (cursor_pos.x, cursor_pos.z) {
        gizmos.cuboid(
            Transform::from_xyz(x as f32 + 0.5, 0.5, z as f32 + 0.5)
                .with_scale(Vec3::new(1.0, 1.1, 1.0)),
            Color::srgba(1.0, 1.0, 0.0, 0.5),
        );
    }
}

fn grid_visibility_system(
    input: Res<ButtonInput<KeyCode>>,
    mut grid_state: ResMut<GridState>,
    mut query: Query<&mut Visibility, With<GridPlane>>,
    view_mode: Res<ViewMode>,
) {
    if input.just_pressed(KeyCode::KeyG) {
        grid_state.visible = !grid_state.visible;
    }

    if grid_state.is_changed() || view_mode.is_changed() {
        if *view_mode == ViewMode::Underground {
            for mut vis in query.iter_mut() {
                *vis = Visibility::Hidden;
            }
            return;
        }

        for mut vis in query.iter_mut() {
            *vis = if grid_state.visible {
                Visibility::Inherited
            } else {
                Visibility::Hidden
            };
        }
    }
}
