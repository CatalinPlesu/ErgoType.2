# Population Phases Feature

## Overview

The Population Phases feature provides an alternative way to define population size with dynamic phases during genetic algorithm execution. Instead of running with a fixed population size for all iterations, you can now "shake things up" by expanding and contracting the population at different phases of the evolution.

## Motivation

From the original issue:
> "add a alternative way to define the population size, keep curent max population size as default, but add this second one which is a list of tuples. (how many iterations to use this setup, max population). actulaly this approach replaces population size and max iterations. it is with purpose of shaking things up..."

This feature allows you to explore different population dynamics:
- **Expansion phases**: Temporarily increase population to explore more of the search space
- **Contraction phases**: Return to smaller populations for focused exploitation
- **Dynamic exploration**: Alternate between wide exploration and narrow refinement

## Usage

### Data Structure

Population phases are defined as a list of tuples:
```python
population_phases = [
    (iterations, max_population),
    (iterations, max_population),
    ...
]
```

Example from the issue:
```python
population_phases = [
    (30, 50),   # Run 30 iterations with max population 50
    (1, 1000),  # Then expand 1 iteration with 1000 population
    (10, 50),   # Then again 10 iterations with 50 population
    (1, 2000),  # Expand to 2K
    (20, 30),   # 20 iterations with 30 population
    (1, 3000),  # Expand to 3K
    (10, 50)    # Finish with 10 iterations, 50 population
]
```

### Method 1: Python Code

```python
from core.run_ga import run_genetic_algorithm

best = run_genetic_algorithm(
    keyboard_file='src/data/keyboards/ansi_60_percent.json',
    text_file='src/data/text/raw/simple_wikipedia_dataset.txt',
    population_phases=[
        (30, 50),
        (1, 1000),
        (10, 50)
    ],
    stagnant_limit=15,
    max_concurrent_processes=4
)
```

### Method 2: Interactive Menu (main.py)

1. Run: `python main.py`
2. Select: `🚀 Run Genetic Algorithm (Master Mode)`
3. Choose mode: `2` for Population Phases Mode
4. Define your phases interactively:
   - Enter iterations and max population for each phase
   - Enter 0 for iterations to finish

The menu will save your phases configuration for future use.

### Method 3: GA Runs Queue

```python
from core.ga_runs_queue import GARunsQueue, create_run_config

queue = GARunsQueue()

# Add a run with population phases
queue.add_run(create_run_config(
    name='Shake_Things_Up',
    population_phases=[
        (30, 50),
        (1, 1000),
        (10, 50)
    ],
    stagnant_limit=15
))

# Execute the queue
results = queue.execute()
queue.save_results('output/results.json')
```

## How It Works

### Phase Execution

When using population phases, the GA:

1. **Initializes** with the first phase's max population
2. For each phase:
   - **Adjusts population** to the phase's max population
     - If shrinking: Keeps the best individuals
     - If expanding: Creates variations of the best individuals
   - **Runs iterations** for the specified number in that phase
   - **Tracks progress** showing current phase information
3. **Completes** when all phases finish or stagnation limit is reached

### Population Adjustment

When transitioning between phases:

- **Shrinking**: The population is sorted by fitness, and only the best individuals are kept
- **Expanding**: New individuals are created by mutating copies of the top performers

This ensures smooth transitions while maintaining evolutionary pressure.

## Metadata and Compatibility

The feature is designed to be fully compatible with existing analysis tools.

### Saved Metadata

For population phases mode, the following is saved to `ga_run_metadata.json`:

```json
{
  "mode": "population_phases",
  "population_phases": [[30, 50], [1, 1000], [10, 50]],
  "total_max_iterations": 41,
  "average_population": 122.0,
  "population_size": 122.0,
  "max_iterations": 41,
  "actual_iterations": 41,
  ...
}
```

### Compatibility Metrics

For compatibility with tools that analyze GA runs:

- **`population_size`**: Set to the average population across all phases (weighted by iterations)
- **`max_iterations`**: Set to the sum of iterations across all phases
- **`actual_iterations`**: Tracked during execution (may be less if stagnation occurs)
- **`total_max_iterations`**: Same as max_iterations (total possible iterations)
- **`average_population`**: Weighted average population size

These metrics allow population phases runs to be compared with standard runs in analysis tools.

### Analysis Tools

Both `ga_run_loader.py` and `multi_run_comparator.py` have been updated to:

- Display the mode (standard vs phases)
- Show phase information when available
- Use compatibility metrics for comparison
- Display average population with `~` prefix in comparisons

Example comparison output:
```
#  Run                    Mode    Pop Size  Max Iter  Gens  Best Fitness  Total Inds
1  ga_run_2025-01-15...  std     50        100       45    0.123456      2250
2  ga_run_2025-01-15...  phases  ~122      41        38    0.118234      2150
```

## Examples

### Example Scripts

Three example scripts are provided:

1. **`example_population_phases.py`**
   - Demonstrates the concept with the example from the issue
   - Shows how to calculate compatibility metrics
   - Provides usage examples for all three methods

2. **`example_ga_queue_with_phases.py`**
   - Creates a comparison queue with 4 runs:
     - Standard baseline
     - Expansion/contraction pattern
     - "Shake things up" pattern
     - Progressive growth pattern
   - Can save and execute the queue

3. **`test_population_phases.py`**
   - Test suite for the feature
   - Tests standard mode (backward compatibility)
   - Tests population phases mode
   - Verifies metadata saving

### Running Examples

```bash
# See the concept and metrics
python example_population_phases.py

# Create and optionally save a comparison queue
python example_ga_queue_with_phases.py

# Run tests
python test_population_phases.py
```

## Design Decisions

### Why List of Tuples?

The `(iterations, max_population)` tuple format is:
- Simple and intuitive
- Easy to read and write
- Natural for defining sequential phases
- Compatible with JSON serialization for queues

### Why "Max Population"?

Each phase specifies a **maximum** population, not a fixed population. This allows:
- Natural handling of stagnation (population may shrink if convergence occurs)
- Compatibility with the existing survivor selection mechanism
- Flexibility in how the population evolves within each phase

### Backward Compatibility

The feature maintains full backward compatibility:
- Standard mode is the default
- Existing code works without changes
- Metadata includes compatibility fields
- Analysis tools work with both modes

### Mode Exclusivity

Population phases mode replaces `population_size` and `max_iterations`:
- These parameters are mutually exclusive
- In phases mode, they're calculated from the phases
- This prevents confusion about which parameters control the run

## Future Enhancements

Potential improvements:
- Preset phase patterns (e.g., "expansion", "shake", "progressive")
- Phase strategies based on fitness improvement
- Adaptive phase duration based on convergence rate
- Visual editor for defining complex phase patterns
- Phase analysis tools to compare different strategies

## References

- Original Issue: "add alternative population input"
- Implementation PR: #[PR_NUMBER]
- Related Files:
  - `src/core/ga.py` - Core GA implementation
  - `src/core/run_ga.py` - GA runner with metadata
  - `src/core/ga_runs_queue.py` - Queue system
  - `main.py` - Interactive menu
  - `src/analysis/ga_run_loader.py` - Analysis loader
  - `src/analysis/multi_run_comparator.py` - Comparison tool
