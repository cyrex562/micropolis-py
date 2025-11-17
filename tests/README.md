# Micropolis Test Suite

This directory contains the comprehensive test suite for the Micropolis Python port.

## Test Organization

```
tests/
├── assertions.py          # Custom assertion helpers + snapshot utilities
├── conftest.py           # Pytest fixtures and configuration
├── test_*.py             # Unit tests for core modules
├── ui/                   # UI-specific tests
│   ├── test_snapshots.py    # Golden-image snapshot tests
│   ├── test_*_panel.py      # Panel-specific tests
│   └── ...
└── golden/               # Golden reference images for snapshot tests
    └── README.md         # Snapshot testing documentation
```

## Running Tests

### Run All Tests

```bash
# Using uv (recommended)
uv run pytest

# With coverage report
uv run pytest --cov=src/micropolis --cov-report=html

# Verbose output
uv run pytest -v
```

### Run Specific Test Suites

```bash
# UI tests only
uv run pytest tests/ui/

# Specific module
uv run pytest tests/test_simulation.py

# Specific test class or function
uv run pytest tests/test_simulation.py::TestSimulation::test_basic_init
```

### Snapshot Tests

Snapshot tests compare rendered UI against golden reference images using perceptual similarity (SSIM).

#### Running Snapshot Tests

```bash
# Run all snapshot tests
uv run pytest tests/ui/test_snapshots.py -v

# Run with headless SDL driver (required for CI)
SDL_VIDEODRIVER=dummy uv run pytest tests/ui/test_snapshots.py
```

#### Updating Golden Images

When you make intentional visual changes:

```bash
# Update all golden images
uv run python scripts/update_golden.py

# Update specific test file
uv run python scripts/update_golden.py test_snapshots.py

# Or use environment variable directly
UPDATE_GOLDEN=1 SDL_VIDEODRIVER=dummy uv run pytest tests/ui/test_snapshots.py
```

#### Understanding Snapshot Failures

When a snapshot test fails, three files are generated in `tests/golden/`:

1. `<name>.png` - Golden reference (unchanged)
2. `<name>_current.png` - Current rendering that failed
3. `<name>_diff.png` - Pixel-wise difference visualization

**Steps to handle failures:**

1. **Review the diff images** to understand what changed
2. **Determine if the change is:**
   - **A regression**: Fix the rendering code
   - **Intentional**: Update golden with `UPDATE_GOLDEN=1`
3. **Commit updated golden images** if changes are intentional

See `tests/golden/README.md` for detailed snapshot testing documentation.

## Test Fixtures

Common fixtures are defined in `conftest.py`:

- `pygame_init` - Initialize pygame in headless mode
- `mock_context` - Mock AppContext for isolated testing
- `sample_city` - Load a sample city for integration tests

## Custom Assertions

The `tests.assertions` module provides:

### Standard Assertions (Assertions class)

```python
from tests.assertions import Assertions

class TestExample(Assertions):
    def test_something(self):
        self.assertEqual(1 + 1, 2)
        self.assertTrue(condition)
        self.assertIn(item, collection)
```

### Snapshot Assertions

```python
from tests.assertions import assert_surface_matches_golden

def test_rendering():
    surface = render_something()
    assert_surface_matches_golden(surface, "test_name", tolerance=0.95)
```

## Writing Tests

### Unit Tests

Focus on testing individual functions/classes in isolation:

```python
import pytest
from micropolis.simulation import Zone

def test_zone_growth():
    zone = Zone(x=10, y=20, zone_type="residential")
    zone.grow()
    assert zone.population > 0
```

### Integration Tests

Test interactions between multiple components:

```python
from micropolis.engine import MicropolisEngine

def test_city_simulation():
    engine = MicropolisEngine()
    engine.load_city("cities/test.cty")
    engine.simulate_step()
    assert engine.total_population >= 0
```

### UI Tests

Test panel behavior and rendering:

```python
from tests.assertions import Assertions, assert_surface_matches_golden
import pygame

class TestHeadPanel(Assertions):
    def test_funds_display(self, mock_context):
        panel = HeadPanel(mock_context)
        panel.update_funds(50000)
        self.assertEqual(panel.funds_label.text, "$50,000")

    def test_snapshot_default_state(self, pygame_init):
        panel = HeadPanel(mock_context)
        surface = panel.render()
        assert_surface_matches_golden(surface, "head_panel_default")
```

## Continuous Integration

Tests run automatically on:

- Every push to main
- Every pull request
- Nightly builds

CI configuration:

- Headless rendering: `SDL_VIDEODRIVER=dummy`
- Coverage threshold: 80%
- Snapshot diffs uploaded as artifacts on failure

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.slow
def test_long_simulation():
    # Long-running test
    pass

@pytest.mark.skipif(not PYGAME_AVAILABLE, reason="Requires pygame")
def test_rendering():
    # Rendering test
    pass
```

Run marked tests:

```bash
# Run only slow tests
uv run pytest -m slow

# Skip slow tests
uv run pytest -m "not slow"
```

## Debugging Tests

### Run with verbose output

```bash
uv run pytest -v -s tests/test_simulation.py
```

### Run a single test with debugger

```bash
uv run pytest --pdb tests/test_simulation.py::test_function
```

### Check test coverage

```bash
uv run pytest --cov=src/micropolis --cov-report=html
# Open htmlcov/index.html in browser
```

## Best Practices

1. **Isolation**: Tests should not depend on each other
2. **Determinism**: Use seeds for random data; avoid timestamps
3. **Fast**: Keep unit tests under 100ms; use fixtures to cache expensive setup
4. **Clear names**: Use descriptive test names that explain what is tested
5. **One assertion focus**: Each test should verify one specific behavior
6. **Mock external dependencies**: Use fixtures to mock file I/O, network, etc.

## Troubleshooting

### Tests fail locally but pass in CI (or vice versa)

- Check for hardcoded paths (use `Path(__file__).parent` for relative paths)
- Ensure deterministic behavior (seed random, avoid timestamps)
- Verify pygame rendering consistency (`SDL_VIDEODRIVER=dummy`)

### Import errors

```bash
# Ensure src/ is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
uv run pytest
```

### Fixture not found

Check that fixtures are:

- Defined in `conftest.py` or the test file
- Imported correctly
- Spelled correctly in test function parameters

## Contributing

When adding new tests:

1. **Place in appropriate directory** (core tests in `tests/`, UI tests in `tests/ui/`)
2. **Follow naming convention** (`test_*.py` for files, `test_*` for functions)
3. **Add docstrings** explaining what the test validates
4. **Keep tests fast** - mock expensive operations
5. **Update this README** if adding new test categories or patterns

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pygame testing guide](https://www.pygame.org/wiki/testing)
- [Snapshot testing best practices](tests/golden/README.md)
- [Project testing checklist](../docs/PORTING_CHECKLIST.md)
