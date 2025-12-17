# How It works

read_physical_keyborad (with qwerty on it) 
|> create a layout phenotype (with quwerty)
|> map a differnet layout in relationship with query
|> create a symbol - key that need pressed map
|> evaluate fintness functin basd on input data.

## GA Run Modes

The Genetic Algorithm now supports three different initialization and continuation modes:

1. **Run as Normal** - Initialize with heuristic layouts (QWERTY, Dvorak, etc.) plus random individuals
2. **Random Only** - Skip heuristics and use only random individuals for pure evolutionary exploration
3. **Continue from Previous Run** - Load and continue evolution from a previously saved GA run

Each mode is designed for specific use cases, from standard optimization to experimental comparisons and progressive refinement.

See [docs/GA_RUN_MODES.md](docs/GA_RUN_MODES.md) for detailed documentation, examples, and use cases.

## GA Runs Queue

The project now supports executing multiple GA runs sequentially with different parameters. This is useful for:
- Parameter sweeps (testing different Fitts's Law constants, population sizes, etc.)
- Running multiple experiments overnight
- Comparing results across different configurations

### Quick Start

1. **Through the menu**: Run `python3 main.py` and select "📋 Execute GA Runs Queue"
2. **Parameter Exploration**: Run `python3 run_parameter_exploration.py` for 25 predefined configs (~3 hours)
3. **Programmatically**: Use the example script: `python3 example_ga_queue.py`
4. **Demonstration**: See how it works: `python3 demo_ga_queue.py`

### Key Features

- **Automatic Individual ID Reset**: The Individual counter is reset between runs for consistent naming
- **Queue Management**: Save/load queue configurations as JSON files
- **Results Tracking**: Automatic saving of results for all runs
- **Flexible Configuration**: Each run can have different parameters
- **Parameter Exploration**: Predefined 25-config matrix for systematic parameter space exploration

### Parameter Exploration

Run a comprehensive parameter space exploration with 25 carefully selected configurations:

```bash
python3 run_parameter_exploration.py
```

This executes a matrix covering:
- 10 iteration levels (5 to 300)
- 7 population levels (5 to 300)
- ~223,525 total evaluations
- ~3 hours runtime

See [docs/PARAMETER_EXPLORATION.md](docs/PARAMETER_EXPLORATION.md) for details.

### Documentation

- [docs/GA_RUNS_QUEUE.md](docs/GA_RUNS_QUEUE.md) - Complete queue documentation
- [docs/PARAMETER_EXPLORATION.md](docs/PARAMETER_EXPLORATION.md) - Parameter exploration guide
