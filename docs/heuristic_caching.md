# Heuristic Layout Caching

## Overview

The heuristic caching system improves GA startup performance by generating and caching heatmaps for standard layouts (QWERTY, Dvorak, Colemak, etc.) once, then reusing them across multiple GA runs.

## Benefits

- **Faster GA Startup**: Heuristic layouts are generated once and cached for reuse
- **Organized Cache Structure**: Clear folder hierarchy for easy management
- **Separation of Concerns**: One-time generation separated from iterative GA runs
- **Automatic Cache Detection**: GA automatically uses cached heuristics when available

## Cache Structure

Heuristics are stored in the following structure:

```
output/
  {dataset_name}/
    {keyboard_name}/
      press_heatmap/
        qwerty.svg
        dvorak.svg
        colemak.svg
        ...
      hover_heatmap/
        qwerty.svg
        dvorak.svg
        ...
      layout/
        qwerty.svg
        dvorak.svg
        ...
      {layout_name}_stats.json
```

## Usage

### Option 1: Pre-generate All Heuristics (Recommended)

Use the menu option to generate all heuristics upfront:

1. Run the main application: `python3 main.py`
2. Select: **"🎯 Generate All Heuristic Heatmaps"**
3. Configure Fitts's law parameters (should match your GA parameters)
4. Confirm generation

This will generate heuristics for all combinations of:
- Keyboards in `src/data/keyboards/`
- Datasets in `src/data/text/raw/` or `src/data/text/processed/`
- Standard layouts (QWERTY, Dvorak, Colemak, Workman, Norman, Asset, Minimak)

### Option 2: Automatic Generation During GA Run

When running the GA, heuristics are automatically:
1. Checked in cache
2. Copied to run directory if cached
3. Generated only if missing

No manual intervention required!

## Technical Details

### Module: `src/helpers/layouts/heuristic_generator.py`

Key functions:

- `generate_heuristic_layout()`: Generate heatmaps for a single layout
- `generate_all_heuristics()`: Generate for all keyboard × dataset × layout combinations
- `check_heuristic_cached()`: Check if heuristics exist in cache
- `get_heuristic_cache_path()`: Get path to cached heuristic file

### Security

All filenames are sanitized to prevent path traversal attacks:
- Dataset names, keyboard names, and layout names are sanitized
- Invalid characters are replaced with underscores
- Path separators and parent directory references (`..`) are removed

### Performance

The system uses **efficient parallel processing** with `ProcessPoolExecutor` and `max_tasks_per_child=1` to generate heuristics on multiple CPU cores simultaneously. This approach prevents resource exhaustion by recycling worker processes after each task, ensuring stable performance even for large batches.

**Implementation details:**
- Uses `concurrent.futures.ProcessPoolExecutor` (same pattern as `ga.py`)
- `max_tasks_per_child=1` ensures processes are recycled after each task
- Prevents memory leaks and resource exhaustion
- Stable performance for extended generation sessions

Typical generation times:
- Single heuristic layout: 2-5 seconds
- All 7 layouts for one keyboard/dataset: 15-30 seconds (sequential)
- All 7 layouts for one keyboard/dataset: 5-10 seconds (parallel with 4+ cores)
- Full generation (4 keyboards × 1 dataset × 7 layouts): 2-4 minutes (sequential)
- Full generation (4 keyboards × 1 dataset × 7 layouts): 30-90 seconds (parallel with 4+ cores)

Once cached, loading from cache is nearly instantaneous.

**Parallel Processing Configuration:**
- Default: Uses all available CPU cores
- Configurable via menu: "Max parallel workers" parameter
- Best performance: 4-8 workers for typical systems
- Safe for long-running generation sessions (no resource exhaustion)

## Testing

Run the test suites to verify functionality:

```bash
# Unit tests
python3 test_heuristic_cache.py

# Integration test
python3 test_integration.py
```

## Troubleshooting

### Cache Not Being Used

1. Check cache exists: `ls -la output/{dataset}/{keyboard}/`
2. Verify all three heatmap types exist for each layout
3. Check logs during GA run for cache usage messages

### Force Regeneration

To regenerate cached heuristics:
1. Use the menu option: "Generate All Heuristic Heatmaps"
2. When prompted, answer "Yes" to "Regenerate heatmaps that already exist?"

Or manually delete the cache directory for specific combinations:
```bash
rm -rf output/{dataset_name}/{keyboard_name}/
```

## Future Enhancements

Potential improvements:
- Cache metadata with generation parameters
- Cache invalidation based on parameter changes
- Progress bars for long-running generations
- Configurable generation priority/ordering
