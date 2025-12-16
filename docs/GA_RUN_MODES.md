# GA Run Modes

The Genetic Algorithm now supports three different run modes to provide flexibility in how the population is initialized and evolved.

## Run Modes

### 1. Run as Normal (Default)
**Menu Option**: `[1] Run as Normal - With heuristic layouts (QWERTY, Dvorak, etc.)`

This is the standard mode that has always existed. The population is initialized with:
- All heuristic layouts (QWERTY, Dvorak, Colemak, Workman, etc.) from `LAYOUT_DATA`
- Additional random individuals to fill up to the specified population size

**When to use**: 
- Standard GA runs
- When you want to leverage known good layouts as starting points
- For most optimization scenarios

**Example**:
```python
from core.run_ga import run_genetic_algorithm

best = run_genetic_algorithm(
    keyboard_file='src/data/keyboards/ansi_60_percent.json',
    text_file='src/data/text/raw/simple_wikipedia_dataset.txt',
    population_size=50,
    max_iterations=100
)
```

### 2. Random Only Mode
**Menu Option**: `[2] Random Only - Skip heuristic layouts, use only random individuals`

In this mode, the population is initialized with only random individuals, skipping all heuristic layouts.

**When to use**:
- Testing pure random evolution without bias from known layouts
- Exploring the solution space without heuristic guidance
- Comparing performance with and without heuristic initialization

**Example**:
```python
from core.run_ga import run_genetic_algorithm

best = run_genetic_algorithm(
    keyboard_file='src/data/keyboards/ansi_60_percent.json',
    text_file='src/data/text/raw/simple_wikipedia_dataset.txt',
    population_size=50,
    max_iterations=100,
    skip_heuristics=True  # Skip heuristic layouts
)
```

**Parameters**:
- `skip_heuristics=True`: Skips loading heuristic layouts from LAYOUT_DATA

### 3. Continue from Previous Run
**Menu Option**: `[3] Continue from Previous Run - Load and continue a previous GA run`

This mode allows you to load a previously saved GA run and continue evolution from where it left off.

**Features**:
- Loads entire population from the last generation
- Preserves all individual history and IDs
- Continues Individual ID counter from where it left off
- Saves results to a separate directory with `_continued_from_` prefix

**When to use**:
- Extending a run that may have ended early
- Adding more iterations to a completed run
- Exploring further evolution of a population

**Example**:
```python
from core.run_ga import run_genetic_algorithm

best = run_genetic_algorithm(
    keyboard_file='src/data/keyboards/ansi_60_percent.json',
    text_file='src/data/text/raw/simple_wikipedia_dataset.txt',
    max_iterations=50,  # Additional iterations to run
    continue_from_run='output/ga_results/ga_run_2025-12-16--10-00-00'
)
```

**Parameters**:
- `continue_from_run`: Path to the previous GA run directory (e.g., `output/ga_results/ga_run_2025-12-16--10-00-00`)

**Output Directory Naming**:
When continuing from a run, the output is saved to:
```
output/ga_results/ga_run_{new_timestamp}_continued_from_{original_run_name}
```

For example:
```
output/ga_results/ga_run_2025-12-16--12-00-00_continued_from_ga_run_2025-12-16--10-00-00
```

## Selecting Previous Runs

When you choose "Continue from Previous Run" in the menu, the system will:

1. Scan `output/ga_results/` for all previous GA runs
2. Display up to 20 most recent runs with their statistics:
   - Run name (timestamp)
   - Population size
   - Total individuals evaluated
   - Best fitness achieved
3. Allow you to select which run to continue

**Example Display**:
```
Available Previous Runs:

1. ga_run_2025-12-16--10-00-00 | Pop: 50 | Total Ind: 523 | Best Fitness: 0.234567
2. ga_run_2025-12-15--15-30-00 | Pop: 30 | Total Ind: 312 | Best Fitness: 0.345678
3. ga_run_2025-12-15--10-00-00 | Pop: 50 | Total Ind: 489 | Best Fitness: 0.256789
```

## How Continuation Works

When you continue from a previous run:

1. **Load Metadata**: The system loads `ga_run_metadata.json` from the selected run
2. **Load All Individuals**: All individuals from `ga_all_individuals.json` are loaded
3. **Restore Population**: The last generation's population becomes the current population
4. **Continue ID Counter**: Individual IDs continue from the highest ID in the loaded run
5. **Resume Evolution**: GA continues with crossover, mutation, and selection from this point

## Saved Metadata

When using any mode, the run metadata includes:
- `skip_heuristics`: Boolean indicating if heuristics were skipped
- `continued_from_run`: Path to the source run (if continuing), or `null`
- All standard metadata (fitness, population size, etc.)

## Use Cases

### Comparing Random vs Heuristic Initialization
Run two experiments with identical parameters but different initialization:

```python
# Run 1: With heuristics
run_genetic_algorithm(
    population_size=50,
    max_iterations=100,
    skip_heuristics=False
)

# Run 2: Without heuristics
run_genetic_algorithm(
    population_size=50,
    max_iterations=100,
    skip_heuristics=True
)
```

### Extending a Run
If a run completed but you want to see if more iterations help:

```python
# Original run already completed
# Load and continue for 50 more iterations
run_genetic_algorithm(
    max_iterations=50,
    continue_from_run='output/ga_results/ga_run_2025-12-16--10-00-00'
)
```

### Progressive Refinement
Run in phases with increasing iterations:

```python
# Phase 1: Quick exploration
run_genetic_algorithm(population_size=30, max_iterations=20)
# This creates: ga_run_2025-12-16--10-00-00

# Phase 2: Continue with more iterations
run_genetic_algorithm(
    max_iterations=30,
    continue_from_run='output/ga_results/ga_run_2025-12-16--10-00-00'
)
# This creates: ga_run_2025-12-16--10-30-00_continued_from_ga_run_2025-12-16--10-00-00

# Phase 3: Final refinement
run_genetic_algorithm(
    max_iterations=50,
    continue_from_run='output/ga_results/ga_run_2025-12-16--10-30-00_continued_from_ga_run_2025-12-16--10-00-00'
)
```

## Notes

- When continuing a run, you can change parameters like `max_iterations`, `stagnant_limit`, etc.
- The keyboard, text file, and Fitts's Law parameters from the original run are preserved
- Population phases mode can be used with all three run modes
- All modes are compatible with the distributed processing via RabbitMQ
