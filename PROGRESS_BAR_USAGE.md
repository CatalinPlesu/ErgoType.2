# Progress Bar Feature

## Overview

A comprehensive progress tracking system has been added to the Genetic Algorithm to provide real-time feedback during optimization runs.

## Features

The progress bar displays:

1. **Iteration Progress**: Shows completion of N out of M total iterations
2. **Job Batch Progress**: Shows fitness evaluation jobs being processed
3. **Average Iteration Time**: Mean time taken per iteration
4. **Estimated Time Remaining**: Calculated based on average iteration time
5. **Total Elapsed Time**: Time since GA started
6. **Stagnation Count**: Current stagnation count vs limit (color-coded)
7. **Average Job Time**: Mean time per job (not per process)
8. **Jobs Complete**: Current job batch completion status

## How It Works

The progress bar uses the Rich library's Live display feature to update in place at the top of the console without hindering other log output. This means:

- The progress display remains visible and updates automatically
- Console logs from the GA continue to print normally below
- No scrollback or terminal clearing issues
- Clean, professional appearance with colors and formatting

## Display Example

```
╭─────────────────────────── 🚀 Genetic Algorithm Progress ───────────────────────────╮
│ ⠦ Iterations (25/50) ━━━━━━━━━━━━━━━━━━━━━━╺━━━━━━━━━━━━━━━━━━━━━━━ 50.0% 0:05:23 │
│ ⠴ Jobs (45/100)      ━━━━━━━━━━━━━━━━━━━━━╺━━━━━━━━━━━━━━━━━━━━━━━ 45.0% 0:01:12 │
│                                                                                     │
│  ⏱️  Avg Iteration        4.2s             🕐 Total Elapsed        1m 45s          │
│  ⏳ Est. Remaining       1m 45s           🔄 Stagnation           3/10             │
│  ⚡ Avg Job Time         0.3s             📦 Jobs Complete        45/100           │
╰─────────────────────────────────────────────────────────────────────────────────────╯
```

## Integration

The progress tracker is automatically initialized when you run the GA through the main menu:

1. Select "🚀 Run Genetic Algorithm (Master Mode)" from the main menu
2. Configure your GA parameters
3. The progress bar will appear automatically during execution

## Technical Details

### Implementation

- **Module**: `src/ui/progress_tracker.py`
- **Class**: `GAProgressTracker`
- **Integration Point**: `src/core/ga.py` in the `run()` method

### Time Calculations

- **Average Iteration Time**: Sum of all completed iteration times divided by number of iterations
- **Estimated Remaining**: (max_iterations - current_iteration) × average_iteration_time
- **Average Job Time**: Total time for job batch divided by total jobs in batch
- **Note**: Job time is per-job, not per-process, as requested in the issue

### Lifecycle

1. **Initialization**: Tracker created at start of `run()` method
2. **Iteration Tracking**: 
   - `start_iteration()` called at beginning of each iteration
   - `complete_iteration()` called at end of each iteration
3. **Job Tracking**:
   - `start_job_batch()` called when fitness evaluation begins
   - `update_job_progress()` called as jobs complete
   - `complete_job_batch()` called when all jobs are done
4. **Cleanup**: Tracker stopped in `finally` block to ensure proper shutdown

## Testing

A test script is included for development testing:

```bash
python3 test_progress_bar.py
```

This demonstrates the progress bar with simulated GA iterations and job processing.

## Requirements

The progress bar requires the `rich` library, which is already included in the project dependencies:

```toml
dependencies = [
    # ... other dependencies ...
    "rich>=13.0.0",
]
```

## Performance Impact

The progress bar has minimal performance impact:

- Updates are rate-limited to 4 times per second
- Display updates are asynchronous and non-blocking
- No significant CPU or memory overhead
- Can be safely used with large populations and many iterations

## Customization

To modify the progress display:

1. Edit `src/ui/progress_tracker.py`
2. Modify the `_create_stats_table()` method to change displayed metrics
3. Modify the `_create_display()` method to change layout
4. Adjust refresh rate in the `Live()` constructor (default: 4 Hz)

## Troubleshooting

**Progress bar not showing**: Ensure Rich library is installed with `pip install rich>=13.0.0`

**Garbled output**: Your terminal may not support Rich formatting. Try a modern terminal emulator.

**Timing seems off**: Ensure `complete_iteration()` and `complete_job_batch()` are called properly.

## Future Enhancements

Possible improvements for future versions:

- Add more detailed job statistics (success rate, failures, retries)
- Show worker distribution in distributed mode
- Add memory usage monitoring
- Export timing statistics to file
- Configurable display format options
