# GA Queue Refactoring Summary

## Changes Made

Refactored the GA runs queue to use a simpler list-based approach with dictionaries instead of the GARunConfig class.

### Before (Class-based)

```python
from core.ga_runs_queue import GARunsQueue, GARunConfig

queue = GARunsQueue()

# Had to use GARunConfig class
queue.add_run(GARunConfig(
    name="Test Run",
    population_size=30,
    max_iterations=50
))

# No easy way to remove runs
# No direct list manipulation
```

### After (Dict-based)

```python
from core.ga_runs_queue import GARunsQueue, create_run_config

queue = GARunsQueue()

# Method 1: Plain dictionaries (easiest)
queue.add_run({
    'name': 'Test Run',
    'population_size': 30,
    'max_iterations': 50
})

# Method 2: Helper function (with defaults)
queue.add_run(create_run_config(
    name='Test Run',
    population_size=30
))

# Method 3: Direct list manipulation
queue.runs.append({'name': 'Run 3', 'fitts_a': 0.6})

# Easy removal
queue.remove_run(1)  # Remove by index

# Direct modification
queue.runs[0]['population_size'] = 100
```

## Benefits

1. **Simpler**: No need to import or learn GARunConfig class
2. **Flexible**: Can use plain dicts, helper function, or direct list access
3. **Easy Manipulation**: Direct access to `queue.runs` list
4. **Remove Support**: Added `remove_run(index)` method
5. **JSON-friendly**: Dictionaries serialize naturally to JSON
6. **Pythonic**: List of dicts is a common Python pattern

## API Reference

### Creating Run Configurations

```python
# Plain dictionary (minimum)
config = {'name': 'My Run'}

# With specific parameters
config = {
    'name': 'My Run',
    'population_size': 50,
    'max_iterations': 100,
    'fitts_a': 0.6
}

# Using helper (merges with defaults)
config = create_run_config(
    name='My Run',
    population_size=50
)
```

### Queue Operations

```python
queue = GARunsQueue()

# Add runs
queue.add_run({'name': 'Run 1'})
queue.add_run(create_run_config(name='Run 2'))
queue.runs.append({'name': 'Run 3'})

# Remove runs
queue.remove_run(0)  # Remove first run
del queue.runs[1]    # Also works

# Modify runs
queue.runs[0]['population_size'] = 200

# Access runs
for i, run in enumerate(queue.runs):
    print(f"{i}. {run['name']}: pop={run['population_size']}")

# Clear all
queue.clear()
```

### Default Parameters

All parameters have defaults defined in `DEFAULT_PARAMS`:

```python
DEFAULT_PARAMS = {
    'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
    'text_file': 'src/data/text/raw/simple_wikipedia_dataset.txt',
    'population_size': 30,
    'max_iterations': 50,
    'stagnant_limit': 10,
    'max_concurrent_processes': 4,
    'fitts_a': 0.5,
    'fitts_b': 0.3,
    'finger_coefficients': [0.07, 0.06, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.06, 0.07],
    'use_rabbitmq': True,
    'save_heuristics': True
}
```

## Migration Guide

If you have existing code using GARunConfig, update it as follows:

### Old Code
```python
from core.ga_runs_queue import GARunsQueue, GARunConfig

queue = GARunsQueue()
queue.add_run(GARunConfig(
    name="Run 1",
    population_size=30,
    max_iterations=50
))

# Accessing properties
for run in queue.runs:
    print(run.name, run.population_size)
```

### New Code
```python
from core.ga_runs_queue import GARunsQueue, create_run_config

queue = GARunsQueue()

# Option 1: Use helper
queue.add_run(create_run_config(
    name="Run 1",
    population_size=30,
    max_iterations=50
))

# Option 2: Use plain dict
queue.add_run({
    'name': 'Run 1',
    'population_size': 30,
    'max_iterations': 50
})

# Accessing properties (now dictionary keys)
for run in queue.runs:
    print(run['name'], run['population_size'])
```

## Tests

All 12 tests updated and passing:

- `TestCreateRunConfig` (3 tests) - Helper function
- `TestGARunsQueue` (7 tests) - Queue operations
- `TestIndividualIDReset` (1 test) - ID reset mechanism
- `TestQueueConfigSerialization` (1 test) - JSON serialization

## Files Changed

- `src/core/ga_runs_queue.py` - Core refactoring
- `main.py` - Menu integration updates
- `example_ga_queue.py` - Example script updates
- `demo_ga_queue.py` - Demo script updates
- `tests/ga_runs_queue_test.py` - All tests rewritten

## Backward Compatibility

⚠️ **Breaking Change**: The `GARunConfig` class has been removed. Existing code using it needs to be updated to use dictionaries or the `create_run_config()` helper function.

However, the queue JSON file format remains compatible - files saved with the old version can be loaded with the new version.
