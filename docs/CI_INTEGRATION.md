# CI Integration for UI Tests and Snapshot Checks

## Overview

The Micropolis Python port includes comprehensive CI integration for UI test suites and visual snapshot regression testing. This document describes the CI pipeline, artifact management, and workflow for handling test failures.

## CI Workflow Structure

The CI pipeline is defined in `.github/workflows/tests.yml` and consists of three parallel jobs:

### 1. Core Pytest Suite (`pytest` job)

- **Purpose**: Run all core simulation and engine tests
- **Environment**: Standard Python environment with uv
- **Tests**: All non-UI tests via `scripts/run_pytest_chunks.py`
- **Caching**: uv dependencies cached by `pyproject.toml` and `uv.lock` hash

### 2. UI Test Suite (`ui-tests` job)

- **Purpose**: Run all pygame UI component tests in headless mode
- **Environment**: Ubuntu with SDL2 libraries and dummy video/audio drivers
- **Tests**: `tests/ui/` directory (excluding snapshot-specific tests)
- **Key Features**:
  - Installs SDL2 system dependencies
  - Uses `SDL_VIDEODRIVER=dummy` for headless rendering
  - Uses `SDL_AUDIODRIVER=dummy` to avoid audio device requirements
  - Validates widget behavior, panel state, event handling

**Artifact Upload on Failure**:

- Any diff images generated: `*_diff.png`, `*_current.png`
- Retained for 7 days
- Helps debug visual regressions without local reproduction

### 3. Snapshot Test Suite (`snapshot-tests` job)

- **Purpose**: Visual regression testing using golden reference images
- **Environment**: Ubuntu with SDL2, dummy video driver
- **Tests**: `tests/ui/test_snapshots.py`
- **Key Features**:
  - Compares rendered UI against golden baselines using SSIM
  - Generates diff images on mismatch
  - Runs deterministically with seeded data

**Artifact Upload**:

- **On Failure**: Diff images (`*_diff.png`, `*_current.png`) retained 14 days
- **Always**: Test cache and golden README retained 7 days for debugging

## Environment Variables

### Required for UI Tests

```yaml
SDL_VIDEODRIVER: dummy   # Headless rendering without X11/Wayland
SDL_AUDIODRIVER: dummy   # Disable audio device initialization
UV_CACHE_DIR: .uv-cache  # uv dependency cache location
```

### Optional for Snapshot Updates

```yaml
UPDATE_GOLDEN: 1         # Regenerate golden images (not used in CI)
```

## Artifact Management

### Uploaded Artifacts

| Artifact Name | Contents | Retention | Trigger |
|--------------|----------|-----------|---------|
| `ui-test-artifacts` | `*_diff.png`, `*_current.png` from UI tests | 7 days | On `ui-tests` job failure |
| `snapshot-diffs` | `*_diff.png`, `*_current.png` from snapshot tests | 14 days | On `snapshot-tests` job failure |
| `snapshot-report` | `.pytest_cache/`, `tests/golden/README.md` | 7 days | Always after snapshot tests |

### Downloading Artifacts

When a UI test or snapshot test fails in CI:

1. Navigate to the GitHub Actions run page
2. Scroll to "Artifacts" section at the bottom
3. Download the relevant artifact zip
4. Extract to review diff images and current renderings

Example:

```bash
# After downloading snapshot-diffs.zip
unzip snapshot-diffs.zip -d /tmp/snapshot-review
ls /tmp/snapshot-review/tests/golden/
# Review *_diff.png and *_current.png files
```

## Handling Test Failures

### UI Test Failures

**Symptoms**: `ui-tests` job fails with assertion errors

**Investigation Steps**:

1. Review test output in GitHub Actions logs
2. Download `ui-test-artifacts` if available
3. Check for:
   - Widget state transition issues
   - Event handling bugs
   - Panel lifecycle errors
4. Reproduce locally with `SDL_VIDEODRIVER=dummy`:

   ```bash
   SDL_VIDEODRIVER=dummy uv run pytest tests/ui/ -v
   ```

**Resolution**:

- Fix the underlying bug in UI code
- Update test expectations if behavior change is intentional
- Re-run tests locally before pushing

### Snapshot Test Failures

**Symptoms**: `snapshot-tests` job fails with SSIM score below threshold

**Investigation Steps**:

1. Download `snapshot-diffs` artifact
2. Review generated images:
   - `<name>.png` - Golden reference (baseline)
   - `<name>_current.png` - Current rendering that failed
   - `<name>_diff.png` - Pixel difference visualization
3. Determine if change is:
   - **Regression**: Unintended visual change → Fix code
   - **Intentional**: Expected visual update → Update golden

**Resolution for Regressions**:

```bash
# Fix the rendering bug
# Run tests locally to verify
SDL_VIDEODRIVER=dummy uv run pytest tests/ui/test_snapshots.py -v
```

**Resolution for Intentional Changes**:

```bash
# Update golden images locally
UPDATE_GOLDEN=1 uv run pytest tests/ui/test_snapshots.py

# Or use the helper script
uv run python scripts/update_golden.py

# Review changes
git diff tests/golden/

# Commit updated golden images
git add tests/golden/*.png
git commit -m "Update golden images for [feature/change]"
git push
```

## Local Development Workflow

### Running UI Tests Locally

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev

# Run UI tests with dummy driver (matches CI)
SDL_VIDEODRIVER=dummy uv run pytest tests/ui/ -v

# Run with visible window (for debugging)
uv run pytest tests/ui/ -v

# Run specific test file
SDL_VIDEODRIVER=dummy uv run pytest tests/ui/test_snapshots.py -v
```

### Updating Golden Images

```bash
# Update all golden images
uv run python scripts/update_golden.py

# Update specific test module
uv run python scripts/update_golden.py test_snapshots.py

# Update specific test class
UPDATE_GOLDEN=1 uv run pytest tests/ui/test_snapshots.py::TestEditorViewSnapshots -v

# Review changes before committing
git diff tests/golden/
open tests/golden/*.png  # Visual inspection
```

### Pre-Push Checklist

Before pushing UI changes:

1. ✅ Run UI tests locally with dummy driver
2. ✅ Run snapshot tests and verify SSIM scores pass
3. ✅ If visual changes are intentional, update golden images
4. ✅ Review `git diff tests/golden/` for unexpected changes
5. ✅ Commit golden image updates with descriptive message
6. ✅ Ensure all tests pass with `uv run pytest tests/`

## CI Optimization

### Caching Strategy

Each job uses dedicated cache keys to avoid conflicts:

- `pytest` job: `${{ runner.os }}-uv-${{ hashFiles(...) }}`
- `ui-tests` job: `${{ runner.os }}-uv-ui-${{ hashFiles(...) }}`
- `snapshot-tests` job: `${{ runner.os }}-uv-snapshot-${{ hashFiles(...) }}`

This ensures:

- Fast dependency installation (cache hit on matching lock file)
- Independent job execution without shared state
- Automatic cache invalidation on dependency changes

### System Dependency Installation

UI and snapshot jobs install SDL2 libraries via apt-get:

```yaml
- name: Install system dependencies
  run: |
    sudo apt-get update
    sudo apt-get install -y \
      libsdl2-dev \
      libsdl2-image-dev \
      libsdl2-mixer-dev \
      libsdl2-ttf-dev
```

These are required for pygame even in headless mode.

### Parallel Execution

All three jobs run in parallel for faster feedback:

- Total CI time ≈ max(pytest, ui-tests, snapshot-tests)
- Typical duration: 3-5 minutes per job
- Failures are isolated to their respective jobs

## Troubleshooting Common CI Issues

### Issue: UI tests pass locally but fail in CI

**Possible Causes**:

- Font rendering differences (system fonts vs bundled fonts)
- Timestamp or randomness not seeded
- Display/resolution assumptions

**Solutions**:

- Use bundled fonts explicitly in tests
- Seed all random number generators
- Use fixed surface sizes, avoid querying display info
- Test locally with `SDL_VIDEODRIVER=dummy` to match CI

### Issue: Snapshot SSIM scores vary between runs

**Possible Causes**:

- Non-deterministic rendering (timestamps, animations)
- Font antialiasing differences
- Floating-point precision in color calculations

**Solutions**:

- Use frozen time in tests (`freezegun` or manual mocks)
- Disable animations during snapshot tests
- Use integer color values, avoid float conversions
- Lower tolerance if needed (`tolerance=0.90`)

### Issue: Artifacts not uploaded on failure

**Check**:

- Verify `if: failure()` condition is present
- Ensure diff files are generated (check test output)
- Confirm paths match actual file locations
- Check artifact retention hasn't expired

**Debug**:

```yaml
- name: List generated files
  if: always()
  run: |
    find tests/golden -name "*_diff.png" -o -name "*_current.png"
```

### Issue: Cache not effective (slow dependency install)

**Check**:

- Cache key matches exactly (OS, hash of lock files)
- `.uv-cache` directory is created before use
- No cache pollution from previous failed runs

**Solution**:

```bash
# Clear GitHub Actions cache via UI or API
# Re-run workflow to generate fresh cache
```

## Future Enhancements

Planned improvements to CI integration:

- [ ] **Parallel snapshot testing**: Split snapshot tests into chunks
- [ ] **Visual diff reports**: Generate HTML reports with side-by-side comparisons
- [ ] **Performance benchmarks**: Track rendering performance over time
- [ ] **Cross-platform testing**: Add Windows and macOS CI runners
- [ ] **Incremental snapshots**: Only test snapshots affected by changed files
- [ ] **Automatic PR comments**: Post visual diff summary to PRs

## References

- **CI Workflow**: `.github/workflows/tests.yml`
- **Snapshot Tests**: `tests/ui/test_snapshots.py`
- **Assertion Helpers**: `tests/assertions.py`
- **Golden Images**: `tests/golden/`
- **Update Script**: `scripts/update_golden.py`
- **Checklist**: `docs/pygame_ui_port_checklist.md` §7.3

## Support

For CI-related issues:

1. Check this document first
2. Review GitHub Actions logs for error details
3. Download and inspect artifacts
4. Reproduce locally with `SDL_VIDEODRIVER=dummy`
5. Open issue with:
   - CI job link
   - Downloaded artifacts (if applicable)
   - Local reproduction steps attempted
   - Environment details (OS, Python version, pygame version)
