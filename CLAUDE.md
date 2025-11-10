# Micropolis Python Port - Claude Guidelines

## Mission
You are Claude, an AI assistant tasked with porting Micropolis (classic SimCity-style city simulation) from C/TCL/Tk to Python 3.13. Your goal is to create a fully functional Python implementation that maintains algorithmic compatibility with the original while leveraging modern Python patterns and pygame/pydsdl graphics.

## Project Context
Micropolis is a city simulation game originally developed by Will Wright. The current codebase consists of:

- **C simulation engine** (`src/sim/`) with core city mechanics
- **TCL/Tk GUI** (`res/*.tcl`) for user interface
- **Sugar activity wrapper** (`micropolisactivity.py`) for OLPC integration
- **Binary assets** (cities, graphics, sounds, documentation)

## Your Role in the Port

1. **Translate C algorithms** to Python while preserving exact behavior
2. **Replace TCL/Tk GUI** with pygame/pydsdl graphics and input handling
3. **Maintain Sugar compatibility** through the existing GTK wrapper
4. **Ensure .cty file compatibility** for city save/load operations
5. **Optimize for Python 3.13** using modern language features

## Critical Success Criteria

- **Algorithmic Fidelity**: Zone growth, traffic simulation, disaster mechanics must match C version exactly
- **File Format Compatibility**: Load/save `.cty` files identically to original
- **Performance**: Maintain 60 FPS simulation loop with smooth sprite animation
- **Sugar Integration**: Preserve stdin/stdout communication protocol

## Architecture Decisions

### Core Data Structures

```python
# Primary simulation state
class Micropolis:
    map: List[List[int]]  # 120x100 tile grid (WORLD_X=120, WORLD_Y=100)
    power_map: bytearray  # Power grid connectivity (PWRMAPLEN)
    overlays: Dict[str, bytearray]  # Population, crime, pollution, etc.
    sprites: List[SimSprite]  # Moving objects (cars, disasters)
    views: List[SimView]     # Editor and map display views
```

### Tile System Preservation

- **16-bit encoding**: Tile ID (0-959) + status bits (PWRBIT, CONDBIT, BURNBIT, etc.)
- **Bit manipulation**: Use bitwise operations for status flags
- **Zone constants**: RZB (249), CZB (436), IZB (625) for residential/commercial/industrial

### Simulation Loop Structure

```python
def simulate_step(self):
    self.update_power_grid()      # Flood-fill from power plants
    self.simulate_zones()         # Growth based on connectivity/density
    self.update_traffic()         # Pathfinding and congestion
    self.handle_disasters()       # Fire spread, flooding, sprites
    self.update_overlays()        # Population, crime, pollution calculations
```

## Development Workflow

### Phase 1: Core Engine Translation

1. **Data structures**: Port `sim.h`, `view.h` definitions to Python classes
2. **Core simulation**: Translate `s_sim.c`, `s_zone.c`, `s_traf.c`, `s_power.c`
3. **File I/O**: Implement `.cty` format loading/saving (`s_fileio.c`)
4. **Initialization**: Port `s_init.c` for proper state setup

### Phase 2: Graphics & Input

1. **Tile rendering**: Replace TCL canvas with pygame surfaces
2. **View management**: Implement editor (16x16 pixels/tile) and map (3x3 pixels/tile) views
3. **Input handling**: Tool selection (bulldozer, road, zones) and mouse/keyboard events
4. **Sprite animation**: Moving cars, disasters, helicopters

### Phase 3: Integration & Testing

1. **Sugar protocol**: Maintain stdin/stdout communication with GTK wrapper
2. **Asset loading**: Graphics, sounds, city files
3. **Compatibility testing**: Compare outputs with C version
4. **Performance optimization**: Ensure 60 FPS simulation

## Code Patterns & Conventions

### Pythonic Adaptations

- **Lists over arrays**: Use `List[List[int]]` instead of C multidimensional arrays
- **Properties over getters**: `@property` decorators for computed values
- **Enums over constants**: `Enum` classes for tool states, zone types
- **Context managers**: File I/O with `with` statements
- **Type hints**: Full type annotation for clarity

### Algorithm Preservation

- **Bit operations**: Maintain exact bitwise logic for tile status
- **Coordinate systems**: Preserve world (0-119,0-99) vs screen pixel coordinates
- **Random number generation**: Use same seed/PRNG algorithm for reproducibility
- **Lookup tables**: Preserve hardcoded arrays for tile transformations

### Performance Considerations

- **Avoid O(n²) operations**: 120x100 grid requires efficient algorithms
- **Downsampling**: Use efficient overlay calculations (4x4 → 1x1)
- **Viewport culling**: Only update visible sprites and tiles
- **Memory layout**: Consider numpy arrays for large grids if performance-critical

## Testing & Validation

### Unit Testing Priorities

1. **Tile manipulation**: Status bit operations, zone detection
2. **Zone growth**: Population requirements, connectivity checks
3. **Traffic simulation**: Pathfinding accuracy, congestion effects
4. **Disaster mechanics**: Fire spread probability, sprite movement
5. **File I/O**: `.cty` format parsing and generation

### Integration Testing

1. **City loading**: Verify all overlays and statistics load correctly
2. **Simulation steps**: Compare outputs with C version after each step
3. **Save/load cycle**: Ensure round-trip compatibility
4. **Performance benchmarks**: Maintain target frame rates

### Compatibility Checks

- **Algorithm validation**: Statistical comparison of growth rates
- **Visual verification**: Screenshot comparison with original
- **Behavioral testing**: Disaster effects, traffic patterns
- **Sugar integration**: Activity launch and communication

## Common Challenges & Solutions

### Algorithm Translation

- **Challenge**: C pointer arithmetic and bit manipulation
- **Solution**: Use Python's `ctypes` or manual bit operations with clear documentation

### Performance Optimization

- **Challenge**: Python overhead on 120x100 grid operations
- **Solution**: Profile hotspots, consider numpy for math-heavy operations, optimize inner loops

### Memory Management

- **Challenge**: C-style manual memory management
- **Solution**: Python garbage collection, but maintain explicit lifecycle management for sprites/views

### Graphics Integration

- **Challenge**: TCL canvas vs pygame surfaces
- **Solution**: Abstract rendering interface, implement pygame backend

## Decision Points

### Graphics Library Choice

- **pygame**: Mature, comprehensive, easier learning curve
- **pydsdl**: Modern, potentially better performance, steeper learning curve
- **Recommendation**: Start with pygame for rapid prototyping, consider pydsdl for optimization

### Algorithm Compatibility

- **Strict preservation**: Maintain exact C algorithms for authenticity
- **Python optimization**: Refactor for clarity while preserving behavior
- **Recommendation**: Preserve algorithms initially, optimize only after validation

### Sugar Integration

- **Full compatibility**: Maintain existing GTK wrapper and protocol
- **Modern approach**: Consider native GTK integration
- **Recommendation**: Preserve compatibility for OLPC deployment

## Success Metrics

- [ ] Core simulation engine runs without crashes
- [ ] Zone growth matches C version statistically
- [ ] Traffic simulation produces identical congestion patterns
- [ ] Disaster effects (fire, floods, sprites) behave identically
- [ ] `.cty` files load/save with 100% compatibility
- [ ] 60 FPS performance maintained
- [ ] Sugar activity launches and communicates properly
- [ ] All original city files work correctly

## Communication Protocol

When working on this project:

1. **Document algorithmic changes**: Explain any deviations from C version
2. **Performance impact**: Note any changes affecting simulation speed
3. **Compatibility concerns**: Flag any potential Sugar integration issues
4. **Testing results**: Share validation outcomes and discrepancies
5. **Design decisions**: Explain architectural choices and trade-offs

Remember: This is a preservation project. The goal is faithful reproduction of classic Micropolis in modern Python, not feature enhancement or redesign.
 
 