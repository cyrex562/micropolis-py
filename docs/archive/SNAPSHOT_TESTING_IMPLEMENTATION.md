# Golden-Image Snapshot Harness Implementation

This document describes the golden-image snapshot testing harness implemented for the Micropolis Python port.

## Overview

The snapshot harness provides automated visual regression testing for pygame UI components using perceptual image comparison (SSIM - Structural Similarity Index).

## Components Implemented

### 1. Core Snapshot Utility (`tests/assertions.py`)

**Functions:**

- `compute_ssim(img1, img2)` - Calculates SSIM score between two images
- `assert_surface_matches_golden(surface, name, tolerance, golden_dir)` - Main assertion function

**Features:**

- Perceptual comparison using SSIM algorithm
- Automatic golden image creation when `UPDATE_GOLDEN=1`
- Diff generation on test failure (`*_diff.png`, `*_current.png`)
- Configurable tolerance threshold (default 0.95)
- Clear error messages with SSIM scores and file paths

### 2. Update Script (`scripts/update_golden.py`)

**Purpose:** Regenerate all golden reference images after intentional visual changes

**Usage:**

```bash
# Update all golden images
python scripts/update_golden.py

# Update specific test pattern
python scripts/update_golden.py test_snapshots.py
```

**Features:**

- Sets `UPDATE_GOLDEN=1` and `SDL_VIDEODRIVER=dummy` automatically
- Filters for snapshot tests using `-k snapshot`
- Clear success/failure reporting
- Git workflow guidance

### 3. Example Snapshot Tests (`tests/ui/test_snapshots.py`)

**Test Classes:**

- `TestEditorViewSnapshots` - Editor rendering tests
- `TestMapViewSnapshots` - Minimap rendering tests
- `TestBudgetPanelSnapshots` - Budget panel UI tests
- `TestGraphPanelSnapshots` - Graph rendering tests
- `TestComprehensiveSnapshots` - Full overlay suite (UPDATE_GOLDEN only)

**Test Coverage:**

- Empty map rendering
- Population overlay
- Power grid overlay
- Traffic heatmap
- Budget panel states (default, low funds)
- Population graph plotting
- All overlay types (comprehensive suite)

### 4. Golden Image Directory (`tests/golden/`)

**Structure:**

```
tests/golden/
├── README.md              # Comprehensive documentation
├── .gitkeep              # Ensures directory is tracked
├── *.png                 # Golden reference images (committed)
├── *_diff.png           # Diff images (gitignored)
└── *_current.png        # Failed test outputs (gitignored)
```

**Documentation:** Includes usage guide, troubleshooting, CI integration, and best practices

### 5. Test Suite Documentation (`tests/README.md`)

**Sections:**

- Test organization overview
- Running snapshot tests
- Updating golden images
- Understanding snapshot failures
- Writing new snapshot tests
- CI integration details
- Troubleshooting guide

### 6. Git Configuration (`.gitignore`)

**Additions:**

```gitignore
# Test artifacts
htmlcov/
.coverage
.pytest_cache/

# Snapshot test diffs (commit golden images, not diffs)
tests/golden/*_diff.png
tests/golden/*_current.png
```

### 7. Dependencies (`pyproject.toml`)

**Added:** `numpy>=1.26.0` for SSIM computation

## Workflow

### Creating Snapshot Tests

1. **Write test function:**

```python
def test_snapshot_something(self):
    surface = render_component()
    assert_surface_matches_golden(surface, "component_state", tolerance=0.95)
```

2. **Generate golden image:**

```bash
UPDATE_GOLDEN=1 pytest tests/ui/test_snapshots.py::test_snapshot_something
```

3. **Verify golden image:**
Review `tests/golden/component_state.png` and commit if correct

4. **Run normally:**

```bash
pytest tests/ui/test_snapshots.py::test_snapshot_something
```

### Handling Test Failures

When a snapshot test fails:

1. **Check generated files:**
   - `tests/golden/<name>_diff.png` - Shows pixel differences
   - `tests/golden/<name>_current.png` - Current rendering

2. **Determine cause:**
   - **Regression:** Fix rendering code
   - **Intentional change:** Update golden with `UPDATE_GOLDEN=1`

3. **Update if intentional:**

```bash
python scripts/update_golden.py
git diff tests/golden/  # Review changes
git add tests/golden/*.png
git commit -m "Update golden images for <reason>"
```

## CI Integration (Ready)

The harness is designed for CI integration with:

- Headless rendering (`SDL_VIDEODRIVER=dummy`)
- Deterministic font rendering
- Artifact upload for diffs on failure
- Clear pass/fail reporting

## Technical Details

### SSIM Algorithm

The implementation uses a simplified SSIM calculation:

1. Convert images to grayscale
2. Compute means (μ₁, μ₂)
3. Compute variances (σ₁², σ₂²) and covariance (σ₁₂)
4. Apply SSIM formula with stability constants (c₁, c₂)

**Advantages:**

- Perceptual similarity (not just pixel-by-pixel)
- Robust to minor rendering variations
- Standard metric (well-understood thresholds)

### Tolerance Levels

- **0.99+**: Very strict - catches tiny differences
- **0.95 (default)**: Balanced - allows minor anti-aliasing variations
- **0.90**: Lenient - for tests with random elements

### Performance Considerations

- Snapshot tests are slower than unit tests
- Mark comprehensive tests with `skipif` to run only on update
- Use `SDL_VIDEODRIVER=dummy` for faster headless rendering

## Best Practices

1. **Descriptive names:** Use clear, hierarchical names like `editor_population_overlay.png`
2. **Minimal coverage:** Only snapshot-test critical visual states
3. **Deterministic data:** Seed random generators for reproducible tests
4. **Group updates:** Update related golden images together
5. **Document changes:** Commit messages should explain visual changes

## Example Test

```python
def test_snapshot_head_panel_default(self):
    """Test head panel rendering with default city state."""
    # Setup
    context = create_mock_context(
        funds=10000,
        population=5000,
        date="January 1900"
    )
    panel = HeadPanel(context)
    
    # Render
    surface = panel.render()
    
    # Compare
    assert_surface_matches_golden(
        surface,
        "head_panel_default",
        tolerance=0.95
    )
```

## Troubleshooting

### "Golden image not found"

**Solution:** Run with `UPDATE_GOLDEN=1` to create initial baseline

### SSIM varies across machines

**Solution:** Use `SDL_VIDEODRIVER=dummy` and bundled fonts for consistency

### Tests pass locally but fail in CI

**Solution:** Check font rendering, seeded randomness, and surface dimensions

## Next Steps (§7.3)

The snapshot harness is complete. Next phase is CI integration:

1. Add GitHub Actions workflow for snapshot tests
2. Configure artifact upload for diff images
3. Add status checks for visual regressions
4. Document CI workflow in project README

## References

- Checklist: `docs/pygame_ui_port_checklist.md` §7.2
- Test docs: `tests/README.md`
- Golden docs: `tests/golden/README.md`
- Update script: `scripts/update_golden.py`
- Core implementation: `tests/assertions.py`
