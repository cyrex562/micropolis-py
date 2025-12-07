# CitySim 3D Project Roadmap

This document tracks the completed milestones, current focus, and planned future features for the CitySim 3D project.

## ✅ Completed Milestones

### Core Engine & Architecture
- [x] **Project Structure**: Setup `src/citysim` and test environment.
- [x] **Core Engine**: Game loop, Event handling, and Config management.
- [x] **Rendering**: OpenGL integration with Pygame, Basic Camera (Pan/Zoom/Rotate), Instanced Meshes.

### Game World & Simulation
- [x] **Grid System**: 64x64 Tile map with multiple layers (Surface, Underground, Air).
- [x] **Layer Management**:
  - `Layer 1`: Air (Power Lines)
  - `Layer 0`: Surface (Roads, Buildings, Zones)
  - `Layer -1`: Underground (Water Pipes)
  - `Layer -2`: Deep Underground (Sewer Pipes)
- [x] **Utilities Logic**:
  - **Power**: Flood-fill propagation (Sources -> Conductors -> Consumers).
  - **Water**: Propagation through pipes and zones; Groundwater pumping logic.
  - **Sewage**: Drainage logic from sources to Map Edge sinks.
  - **Zone Propagation**: RCI Zones conduct utilities internally.

### Traffic & Labor System
- [x] **Labor Exchange**: Residents (Seekers) assigned to Jobs (Employers) daily.
- [x] **Pathfinding**: A* algorithm finding routes through the road network.
- [x] **Traffic Traffic**: Road usage tracking based on commute paths.
- [x] **Traffic Overlay**: Visual heat map (Green/Yellow/Red) toggled via 'T'.

### User Interface
- [x] **HUD**: Tool selection bar, Top info bar (Population, Time).
- [x] **Inspector**: Tile details on Right-Click.
- [x] **Controls**:
  - Orthogonal dragging (Straight lines).
  - Camera Zoom (Mouse Wheel).
  - Layer Toggling (Surface/Underground).

---

## 🚧 Current Phase: Refinements & Polish

- [x] **Data Inspector**: Improve inspector to show detailed Traffic/Pop/Job stats. <!-- id: 74 -->
- [x] **Visual Constraints**: Enforce straight road building logic strictly. <!-- id: 75 -->

---

## 🔮 Future / Planned Features

### Game Configuration
- [ ] **New Game Wizard**: Main menu screen to configure map generation.
  - Water Percentage slider.
  - Map Size options.

### Visual Aids
- [ ] **Map Bounds**: Visually indicate map edges in underground views.
- [ ] **Grid Overlay**: Toggleable grid lines for precise placement.

### Simulation Depth
- [ ] **Advanced Fluids**: Treat pipes as networks with flow rate and capacity limits.
- [ ] **Pollution**: Generate pollution based on Traffic and Industrial density.
- [ ] **Service Coverage**: Fire/Police station radius logic.

### Interaction & Controls
- [ ] **Camera Tilt**: Middle-mouse button interactions for tilting/rotating.

### Traffic & Transport
- [ ] **Road Networks**: Allow building roads at angles and curves.
- [ ] **Intersections**: Support complex intersections and roundabouts.

### New Service Systems
- [ ] **Safety Services**: Police (Crime logic), Fire (Fire hazard logic), Medical (Health logic).
- [ ] **Civic Services**: Education (Schools/Universities), Recreation (Parks/Stadiums).

### Supply Chain Logic
- [ ] **Resource Management**: Tracking of Goods, Raw Materials, and Food.
- [ ] **Truck Logistics**:
  - Industrial requires Raw Materials (imported from Map Edge via road).
  - Commercial requires Supplies (produced by Industrial or imported).
  - Residential requires Groceries (from Commercial).
- [ ] **Agent Logic**: Population must travel to Commercial zones for supplies.

### Advanced Infrastructure
- [ ] **Power Generation**:
  - Types: Coal, Gas, Oil, Solar, Wind, Geothermal, Nuclear Fission/Fusion, Beamed Solar.
  - Resource consumption (Coal, Oil) and pollution output.
- [ ] **Water Treatment**: Sewage treatment plants to clean output before dumping (reduces pollution).

### Waste Management
- [ ] **Collection**: Trash trucks, collection routes, and way stations.
- [ ] **Disposal**:
  - **Landfills**: Zoning for trash storage; fills up over time; generates pollution.
  - **Incinerators**: Burn trash for energy (bonus) but high pollution.
- [ ] **Recycling**:
  - **Centers**: Sort trash for recyclable materials.
  - **Processing**: Industries that convert recycling/trash into Raw Materials.
- [ ] **Logistics & Economy**:
  - Export excess trash/recycling off-map (cost).
  - Import trash/recycling (revenue source, but higher pollution/traffic).
