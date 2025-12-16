# Quick Reference: GA Run Modes

## How to Access

```bash
python3 main.py
# Select: "🚀 Run Genetic Algorithm (Master Mode)"
# At Step 3, choose your run mode
```

## The Three Modes

### 📝 Mode 1: Run as Normal
**Use when**: Standard optimization, leveraging known good layouts
```
Includes heuristic layouts (QWERTY, Dvorak, Colemak, etc.) + random individuals
```

### 🎲 Mode 2: Random Only  
**Use when**: Testing pure evolution, avoiding bias from known layouts
```
Only random individuals, no heuristics
Great for comparing evolutionary performance
```

### ♻️ Mode 3: Continue from Previous Run
**Use when**: Extending a run, progressive refinement
```
Loads complete population from last generation
Preserves all history and IDs
Saves to new directory with "_continued_from_" prefix
```

## Quick Examples

### Compare Heuristic vs Random
```python
# With heuristics
run_genetic_algorithm(population_size=50, max_iterations=100)

# Without heuristics  
run_genetic_algorithm(population_size=50, max_iterations=100, skip_heuristics=True)
```

### Extend a Completed Run
```python
# Original run already saved
run_genetic_algorithm(
    max_iterations=50,
    continue_from_run='output/ga_results/ga_run_2025-12-16--10-00-00'
)
```

## What Gets Saved

**Standard Run:**
```
output/ga_results/ga_run_2025-12-16--10-00-00/
├── ga_run_metadata.json       # Run configuration and stats
├── ga_all_individuals.json    # All individuals with history
├── rank1_gen_X-Y.json         # Top 3 layouts with details
├── rank1_gen_X-Y_stats.json
└── fitness_evolution.png      # Fitness graph
```

**Continued Run:**
```
output/ga_results/ga_run_2025-12-16--12-00-00_continued_from_ga_run_2025-12-16--10-00-00/
└── (same structure as above, but preserves original run separately)
```

## Previous Run Browser

When selecting "Continue from Previous Run", you'll see:

```
Available Previous Runs:

ga_run_2025-12-16--10-00-00                        Pop:    50  Individuals:    523  Fitness: 0.234567
ga_run_2025-12-15--15-30-00                        Pop:    30  Individuals:    312  Fitness: 0.345678
ga_run_2025-12-15--10-00-00                        Pop:    50  Individuals:    489  Fitness: 0.256789
```

Simply select the run you want to continue!

## Metadata Tracking

All runs now include:
```json
{
  "skip_heuristics": false,
  "continued_from_run": null,
  "population_size": 50,
  "best_fitness": 0.234567,
  "total_unique_individuals": 523
}
```

## Progressive Refinement Example

```bash
# Phase 1: Quick 20 iterations
python3 main.py → Run as Normal → 20 iterations
# Creates: ga_run_2025-12-16--10-00-00

# Phase 2: Continue for 30 more
python3 main.py → Continue from Previous → Select run above → 30 iterations  
# Creates: ga_run_2025-12-16--10-30-00_continued_from_ga_run_2025-12-16--10-00-00

# Phase 3: Final 50 iterations
python3 main.py → Continue from Previous → Select phase 2 run → 50 iterations
```

## Tips

✅ **Do**: Use continue mode to extend promising runs
✅ **Do**: Compare random-only vs heuristic initialization
✅ **Do**: Use standard mode for most optimization tasks

❌ **Don't**: Delete source runs if you want to continue them later
❌ **Don't**: Manually edit ga_all_individuals.json (IDs must be unique)

## Need More Info?

📖 Full documentation: `docs/GA_RUN_MODES.md`
📖 Implementation details: `IMPLEMENTATION_GA_MODES.md`
📖 General info: `README.md`
