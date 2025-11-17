# GitHub Actions Workflows

## Overview

This directory contains CI/CD workflows for the Micropolis Python port project.

## Active Workflows

### tests.yml

Comprehensive test suite with three parallel jobs:

#### 1. pytest (Core Tests)

- Runs all non-UI simulation and engine tests
- Uses chunked test execution via `scripts/run_pytest_chunks.py`
- Includes asset manifest build step
- Caches uv dependencies for fast execution

#### 2. ui-tests (UI Component Tests)

- Tests pygame UI widgets, panels, and event handling
- Runs in headless mode with `SDL_VIDEODRIVER=dummy`
- Installs SDL2 system dependencies
- **Uploads artifacts on failure**: diff images for debugging
- Retention: 7 days

#### 3. snapshot-tests (Visual Regression Tests)

- Compares rendered UI against golden reference images
- Uses SSIM (Structural Similarity Index) for perceptual comparison
- Generates diff images for mismatches
- **Uploads artifacts**:
  - On failure: diff images (14 days retention)
  - Always: test cache and reports (7 days retention)

## Artifact Downloads

When tests fail, download artifacts from the GitHub Actions run page:

1. Navigate to Actions → Failed Run
2. Scroll to "Artifacts" section
3. Download relevant artifact zip:
   - `ui-test-artifacts` - UI test failures
   - `snapshot-diffs` - Visual regression diffs
   - `snapshot-report` - Test cache and metadata

## Environment Variables

Standard environment for all jobs:

```yaml
UV_CACHE_DIR: .uv-cache          # uv dependency cache
SDL_VIDEODRIVER: dummy           # Headless rendering (UI tests)
SDL_AUDIODRIVER: dummy           # Disable audio (UI tests)
```

## Cache Strategy

Each job uses independent caches to avoid conflicts:

- `pytest`: `${{ runner.os }}-uv-${{ hashFiles(...) }}`
- `ui-tests`: `${{ runner.os }}-uv-ui-${{ hashFiles(...) }}`
- `snapshot-tests`: `${{ runner.os }}-uv-snapshot-${{ hashFiles(...) }}`

## Documentation

For detailed CI integration information, see:

- **[CI_INTEGRATION.md](../../docs/CI_INTEGRATION.md)** - Comprehensive CI guide
- **[pygame_ui_port_checklist.md](../../docs/pygame_ui_port_checklist.md)** - UI porting progress

## Local Development

Match CI environment locally:

```bash
# Run UI tests with dummy SDL driver
SDL_VIDEODRIVER=dummy uv run pytest tests/ui/ -v

# Run snapshot tests
SDL_VIDEODRIVER=dummy uv run pytest tests/ui/test_snapshots.py -v

# Update golden images
UPDATE_GOLDEN=1 uv run pytest tests/ui/test_snapshots.py
# or
uv run python scripts/update_golden.py
```

## Maintenance

### Adding New Tests

1. Add tests to appropriate directory (`tests/` or `tests/ui/`)
2. For snapshot tests, generate golden images with `UPDATE_GOLDEN=1`
3. Commit golden images to `tests/golden/`
4. CI automatically picks up new tests

### Updating Golden Images

If CI snapshot tests fail due to intentional visual changes:

```bash
# Locally update golden images
uv run python scripts/update_golden.py

# Review changes
git diff tests/golden/

# Commit updates
git add tests/golden/*.png
git commit -m "Update golden images for [change description]"
git push
```

### Troubleshooting CI Failures

1. **Check job logs** in GitHub Actions UI
2. **Download artifacts** for visual inspection
3. **Reproduce locally** with same environment:

   ```bash
   SDL_VIDEODRIVER=dummy uv run pytest tests/ui/ -v
   ```

4. **Fix code** or **update expectations** as needed
5. **Re-run** via commit or manual workflow dispatch

## Workflow Triggers

Workflows run on:

- **Push** to `main` or `master` branches
- **Pull requests** targeting any branch

## Permissions

All jobs use minimal permissions:

```yaml
permissions:
  contents: read
```

This follows security best practices for CI workflows.

## Future Enhancements

Planned improvements:

- [ ] Cross-platform testing (Windows, macOS)
- [ ] Performance benchmarking
- [ ] Automatic PR comments with visual diffs
- [ ] Coverage reporting with codecov
- [ ] Docker-based test environments
