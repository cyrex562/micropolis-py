## Running Tests

The full pytest suite currently contains several hundred modules and exceeds
the automation timeout when executed in a single `uv run pytest` invocation.
Use the helper script to run the suite in manageable batches:

```bash
python3 scripts/run_pytest_chunks.py
```

Pass any extra pytest flags after the script arguments, e.g.:

```bash
python3 scripts/run_pytest_chunks.py --chunk-size 80 -k budget
```

This keeps each `uv run pytest` call under the harness limit while still
exercising the entire test set.

### Pygame Prototype Shortcuts

When running the pygame front-end, the following keys are recognized globally:

- `Space`/`P` toggles pause.
- `0`‑`3` set the simulation speed; `+`/`-` nudge the speed up or down.
- `B` opens the budget window (and pauses while it is open).
- `[` / `]` cycle through the available map overlays.
- `G` toggles the graph display flag, forcing a graph redraw.
- `E` refreshes the evaluation panel data.
