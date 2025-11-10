# Micropolis Python Port - AI Coding Guidelines

## Project Overview
This is a port of Micropolis (classic SimCity-style city simulation game) from C/TCL/Tk to Python 3.13 using pygame or pydsdl. The original C codebase implements the core city simulation engine with TCL/Tk GUI, wrapped in a Sugar activity for OLPC laptops.

## Architecture Overview

### Core Components
- **Simulation Engine** (`src/sim/`): City simulation logic, map management, zoning, disasters, traffic, power grids
- **Data Structures**: 120x100 tile map with bit-encoded status flags, multiple overlay layers (population, pollution, crime, etc.)
- **Assets**: City save files (`.cty`), tile graphics, sounds, HTML manual
- **Sugar Integration**: GTK wrapper for OLPC educational platform

### Key Data Structures
```python
# Main simulation state (from sim.h)
class Sim:
    editors: List[SimView]  # Map editor views
    maps: List[SimView]     # Overview map views
    sprites: List[SimSprite]  # Moving objects (cars, disasters)

# Map representation
Map: List[List[int]]  # 120x100 grid, each cell is 16-bit tile ID + status bits
PowerMap: bytearray   # Power grid connectivity
PopulationMem: bytearray  # Population density overlay
CrimeMem: bytearray   # Crime rate overlay
# ... additional overlays for pollution, traffic, land value
```

### Porting Strategy
- Replace C simulation engine with Python classes
- Use pygame/pydsdl for graphics and input handling
- Maintain Sugar activity compatibility
- Preserve core simulation algorithms (zoning, traffic, disasters)

## Development Workflow

- when running python code in the terminal this is a 'uv' based project: always run code within the virtualenv context with `uv run`

### Build & Run (Current C Version)
```bash
cd src
make all        # Builds TCL, TK, TCLX, then sim binary
make install    # Copies binary to ../res/sim
cd ..
python micropolisactivity.py  # Launches Sugar activity
```

### Python Port Setup
```bash
pip install pygame  # or pydsdl
python -m pip install sugar3  # For Sugar activity compatibility
```

### Testing Approach
- Compare simulation outputs between C and Python versions
- Validate city save file compatibility (`.cty` format)
- Test disaster scenarios, zoning algorithms, traffic simulation
- Verify overlay calculations (population density, crime rates, etc.)

## Code Patterns & Conventions

### Simulation Loop Structure
```python
class MicropolisEngine:
    def __init__(self):
        self.map = [[0 for _ in range(100)] for _ in range(120)]
        self.power_map = bytearray(120 * 100 // 8)
        self.population_overlay = bytearray(120 * 50)  # 2x2 downsampled
        
    def simulate_step(self):
        self.update_power_grid()
        self.simulate_zones()
        self.update_traffic()
        self.handle_disasters()
        self.update_overlays()
```

### Tile System
- **Tile IDs**: 0-959 representing terrain, buildings, infrastructure
- **Status Bits**: PWRBIT, CONDBIT, BURNBIT, etc. stored in high bits
- **Zone Types**: Residential (RZB), Commercial (CZB), Industrial (IZB)
- **Transportation**: Roads, rails, power lines with connectivity logic

### File I/O Patterns
```python
def load_city_file(filename: str) -> dict:
    """Load .cty file format"""
    with open(filename, 'rb') as f:
        # Binary format with header, map data, overlays
        header = f.read(4)  # 'CTY1' magic
        # Parse map tiles, overlays, city statistics
        return city_data

def save_city_file(filename: str, city_data: dict):
    """Save .cty file format"""
    # Mirror load format for compatibility
```

### GUI Integration
- **Sugar Activity**: GTK-based wrapper communicating via stdin/stdout
- **Event Handling**: Tool selection (bulldozer, road, residential zone, etc.)
- **View Management**: Editor view (16x16 pixels/tile), map view (3x3 pixels/tile)

## Critical Implementation Details

### Zone Simulation Algorithm
Residential/commercial/industrial zones grow based on:
- Adjacent road/rail/power connectivity
- Population density requirements
- Pollution and crime thresholds
- Distance from city center

### Traffic Simulation
- **Pathfinding**: A* algorithm for vehicle routing
- **Congestion**: Traffic density affects zone growth
- **Sprites**: Moving cars, trains, helicopters as SimSprite objects

### Disaster System
- **Fire Spread**: Probabilistic based on adjacent flammable tiles
- **Flooding**: Water propagation from rivers/ocean
- **Earthquakes**: Random tile destruction with rubble generation
- **Monster/Tornado**: Path-based sprite movement with destruction

### Power Grid Simulation
- **Connectivity**: Flood-fill algorithm from power plants
- **Consumption**: Zones require power to function
- **Outages**: Unpowered zones don't grow, show graphically

## Common Pitfalls

### Performance Considerations
- **120x100 grid operations**: Avoid O(n²) algorithms in simulation loop
- **Overlay calculations**: Use efficient downsampling (4x4 → 1x1)
- **Sprite updates**: Limit to visible viewport only

### Data Type Handling
- **Bit operations**: Preserve 16-bit tile encoding with status bits
- **Coordinate systems**: World coords (0-119, 0-99) vs screen pixels
- **Array indexing**: Row-major order, careful with bounds checking

### Compatibility Requirements
- **City files**: Must load/save `.cty` format identically
- **Simulation results**: Growth rates, disaster effects must match C version
- **Sugar integration**: Maintain stdin/stdout protocol for activity wrapper

## Key Files for Reference

### Core Simulation
- `src/sim/sim.c`: Main simulation loop and state management
- `src/sim/s_sim.c`: Core simulation step logic
- `src/sim/s_zone.c`: Zone growth and management
- `src/sim/s_traf.c`: Traffic simulation
- `src/sim/s_power.c`: Power grid connectivity

### Data Structures
- `src/sim/headers/sim.h`: Core data structures and constants
- `src/sim/headers/view.h`: View and sprite definitions
- `src/sim/headers/macros.h`: Bit manipulation macros

### GUI Integration
- `micropolisactivity.py`: Sugar activity wrapper
- `res/micropolis.tcl`: Main TCL GUI code
- `res/weditor.tcl`: Map editor interface

### Assets
- `cities/*.cty`: Example city save files
- `res/`: Graphics, sounds, scenarios
- `manual/`: HTML documentation

## Testing Priorities

1. **Basic simulation**: City loads, runs without crashes
2. **Zone growth**: Residential/commercial/industrial development matches C version
3. **Infrastructure**: Road/rail/power connectivity works correctly
4. **Disasters**: Fire spread, flooding, monster movement accurate
5. **Save/load**: `.cty` files compatible with original game
6. **Performance**: 60 FPS simulation loop, smooth sprite animation

## Questions for Clarification

1. Which graphics library to prioritize: pygame vs pydsdl?
2. Should we maintain exact C algorithm compatibility or optimize for Python?
3. How to handle Sugar-specific features (multiplayer, journaling)?
4. Target platform requirements beyond basic functionality?</content>
<parameter name="filePath">c:\Users\cyrex\files\projects\micropolis\.github\copilot-instructions.md