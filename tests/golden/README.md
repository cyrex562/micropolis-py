# Golden Reference Images

This directory contains golden reference images for snapshot testing.

## Purpose

Golden images serve as visual baselines for UI regression testing. Each test compares the current rendering against its corresponding golden image using perceptual similarity metrics (SSIM).

## Directory Structure

```
golden/
├── README.md               # This file
├── editor_*.png           # Editor view snapshots
├── minimap_*.png          # Minimap view snapshots
├── budget_panel_*.png     # Budget panel snapshots
├── graph_*.png            # Graph panel snapshots
├── overlay_*.png          # Overlay mode snapshots
└── *_diff.png             # Diff images (generated on test failure)
```

## Usage

### Running Snapshot Tests

```bash
# Run all snapshot tests (uses existing golden images)
uv run pytest tests/ui/test_snapshots.py -v

# Run with headless SDL driver (for CI)
SDL_VIDEODRIVER=dummy uv run pytest tests/ui/test_snapshots.py
```

### Updating Golden Images

When you make intentional visual changes, update the golden images:

```bash
# Update all golden images
uv run python scripts/update_golden.py

# Update specific test
uv run python scripts/update_golden.py test_snapshots.py::TestEditorViewSnapshots

# Update using environment variable directly
UPDATE_GOLDEN=1 uv run pytest tests/ui/test_snapshots.py
```

### Understanding Test Failures

When a snapshot test fails, three images are generated:

1. `<name>.png` - The golden reference (unchanged)
2. `<name>_current.png` - The current rendering that failed
3. `<name>_diff.png` - Pixel-wise difference visualization

Review these images to determine if:

- The change is a **regression** → Fix the code
- The change is **intentional** → Update golden with `UPDATE_GOLDEN=1`

## SSIM Tolerance

Tests use Structural Similarity Index (SSIM) with a default tolerance of 0.95 (95% similarity). This allows for minor rendering variations while catching significant changes.

To adjust tolerance for specific tests:

```python
assert_surface_matches_golden(surface, "test_name", tolerance=0.98)
```

## Git Management

- **Commit golden images**: Always commit `.png` files in this directory
- **Ignore diffs**: `*_diff.png` and `*_current.png` are gitignored
- **Review changes**: Use `git diff tests/golden/` to review visual changes before committing

## CI Integration

Snapshot tests run automatically in CI with:

- `SDL_VIDEODRIVER=dummy` for headless rendering
- Deterministic font/rendering for consistency
- Diff artifacts uploaded on failure for review

## Best Practices

1. **Descriptive names**: Use clear, hierarchical names like `editor_population_overlay.png`
2. **Minimal tests**: Only snapshot-test critical UI states to keep the suite fast
3. **Deterministic rendering**: Use seeded random data for reproducible results
4. **Update in batches**: Group related visual changes and update golden images together
5. **Document intent**: Add test docstrings explaining what each snapshot validates

## Troubleshooting

### "Golden image not found"

Run with `UPDATE_GOLDEN=1` to create the initial baseline.

### SSIM scores vary across machines

Ensure consistent rendering by:

- Using `SDL_VIDEODRIVER=dummy`
- Loading fonts explicitly (don't rely on system fonts)
- Using the same pygame version

### Tests pass locally but fail in CI

Check for:

- Font rendering differences (use bundled fonts)
- Timestamp/random data (seed all randomness)
- Resolution/DPI variations (use fixed surface sizes)
