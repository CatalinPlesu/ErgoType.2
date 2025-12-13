# Parameter Exploration Queue

## Overview

The parameter exploration feature provides a predefined 25-configuration matrix designed to systematically explore the iteration/population parameter space with optimal coverage in approximately 3 hours of runtime.

## Configuration Matrix

All 25 configurations use the following fixed parameters:
- **Stagnation Limit**: 3
- **Max Concurrent Processes**: 1

### Parameter Coverage

**Iterations**: 10 levels from 5 to 300
- 5, 50, 75, 100, 150, 175, 200, 250, 275, 300

**Population**: 7 levels from 5 to 300
- 5, 30, 50, 70, 110, 150, 300

### Complete Configuration List

| # | Iterations | Population | Est. Time | Purpose |
|---|------------|------------|-----------|---------|
| 1 | 5 | 5 | 8s | Sanity check |
| 2 | 5 | 150 | 4m | Wide shallow search |
| 3 | 5 | 300 | 8m | Max width minimal depth |
| 4 | 50 | 5 | 1m | Narrow deep search |
| 5 | 50 | 30 | 8m | Small balanced |
| 6 | 50 | 70 | 18m | Reference baseline |
| 7 | 50 | 150 | 38m | Wide quick search |
| 8 | 50 | 300 | 75m | Max population test |
| 9 | 75 | 50 | 19m | Balanced small-medium |
| 10 | 75 | 110 | 41m | Sweet spot candidate |
| 11 | 100 | 30 | 15m | Reference point |
| 12 | 100 | 70 | 35m | Medium balanced |
| 13 | 100 | 150 | 75m | Large pop moderate iter |
| 14 | 150 | 30 | 23m | Deep narrow |
| 15 | 150 | 70 | 53m | Balanced medium-large |
| 16 | 150 | 110 | 83m | Sweet spot |
| 17 | 175 | 50 | 44m | Deep moderate width |
| 18 | 200 | 30 | 30m | Very deep narrow |
| 19 | 200 | 70 | 70m | Deep balanced |
| 20 | 200 | 110 | 110m | Large thorough |
| 21 | 250 | 50 | 63m | Very deep moderate |
| 22 | 250 | 70 | 88m | Max depth moderate pop |
| 23 | 275 | 30 | 41m | Extreme depth narrow |
| 24 | 300 | 50 | 75m | Max depth moderate |
| 25 | 300 | 70 | 105m | Max depth good pop |

**Total Evaluations**: ~223,525 (vs 2.1M for full matrix)
**Estimated Total Runtime**: ~3 hours

## Usage

### Method 1: Through the Menu

```bash
python3 main.py
# Select option #2: "📋 Execute GA Runs Queue"
# Then select: "2️⃣ Run Parameter Exploration (25 configs, ~3 hours)"
```

### Method 2: Standalone Script

```bash
python3 run_parameter_exploration.py
```

### Method 3: Programmatically

```python
from core.ga_runs_queue import create_parameter_exploration_queue

# Create the predefined queue
queue = create_parameter_exploration_queue()

# Optional: View configurations
for i, run in enumerate(queue.runs, 1):
    print(f"{i}. Iter={run['max_iterations']}, Pop={run['population_size']}")

# Optional: Modify specific configurations
queue.runs[0]['population_size'] = 10  # Adjust first config

# Optional: Add more configurations
queue.add_run({
    'name': 'Custom Config',
    'population_size': 100,
    'max_iterations': 120,
    'stagnant_limit': 3,
    'max_concurrent_processes': 1
})

# Execute the queue
results = queue.execute(verbose=True)

# Save results
queue.save_results("output/param_exploration_results.json")
```

## Design Rationale

### Why These Configurations?

1. **Sanity Check** (5x5): Quick validation that the system works
2. **Extreme Cases**: Tests both ends of the parameter space
3. **Sweet Spot Search**: Multiple configurations around likely optimal regions
4. **Balanced Coverage**: Systematic exploration of the full parameter space
5. **Resource Optimization**: ~3 hours vs 7.4 days for full grid search

### Strategic Sampling

The 25 configurations provide:
- Coverage across 10 iteration levels (5 to 300)
- Coverage across 7 population levels (5 to 300)
- Multiple "sweet spot" candidates (e.g., 75x110, 150x110)
- Extreme case testing (5x5, 300x300 equivalent coverage)
- Balanced exploration vs exploitation

### Runtime Estimation

Estimates assume:
- ~1 second per individual evaluation
- Stagnation at iteration 3 for early termination
- Sequential execution (1 process)

Actual runtime may vary based on:
- Hardware performance
- Text corpus size
- Early stagnation frequency

## Benefits

✅ **No Interactive Input**: Runs unattended for 3 hours
✅ **Reproducible**: Same configurations every time
✅ **Comprehensive**: Covers full parameter space systematically
✅ **Resource Efficient**: ~10% of full grid search evaluations
✅ **Sweet Spot Discovery**: Multiple candidates around optimal regions
✅ **Extreme Case Testing**: Validates behavior at boundaries

## Output

Results are saved in JSON format with:
- Configuration parameters for each run
- Best fitness achieved
- Runtime statistics
- Success/failure status
- Best layout for each configuration

Example results file: `output/ga_queue_results/param_exploration_2025-12-13--12-00-00.json`

## Analysis

After execution, you can analyze results to:
1. Identify the best performing configuration
2. Plot fitness vs iteration/population heatmaps
3. Determine the "sweet spot" for your specific problem
4. Understand convergence behavior across parameter space

## Customization

To create your own exploration matrix:

```python
from core.ga_runs_queue import GARunsQueue, create_run_config

queue = GARunsQueue()

# Define your custom matrix
for iterations in [10, 50, 100, 200]:
    for population in [20, 50, 100]:
        queue.add_run(create_run_config(
            name=f"Custom_I{iterations}_P{population}",
            max_iterations=iterations,
            population_size=population,
            stagnant_limit=5,
            max_concurrent_processes=2
        ))

# Execute
results = queue.execute()
```

## Notes

- All runs execute **sequentially** to avoid resource conflicts
- Individual ID counter is reset between runs for consistent naming
- Each run is independent (no state carries over)
- Failed runs don't stop the queue (execution continues)
