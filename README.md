# How It works

read_physical_keyborad (with qwerty on it) 
|> create a layout phenotype (with quwerty)
|> map a differnet layout in relationship with query
|> create a symbol - key that need pressed map
|> evaluate fintness functin basd on input data.

## GA Runs Queue

The project now supports executing multiple GA runs sequentially with different parameters. This is useful for:
- Parameter sweeps (testing different Fitts's Law constants, population sizes, etc.)
- Running multiple experiments overnight
- Comparing results across different configurations

### Quick Start

1. **Through the menu**: Run `python3 main.py` and select "📋 Execute GA Runs Queue"
2. **Programmatically**: Use the example script: `python3 example_ga_queue.py`
3. **Demonstration**: See how it works: `python3 demo_ga_queue.py`

### Key Features

- **Automatic Individual ID Reset**: The Individual counter is reset between runs for consistent naming
- **Queue Management**: Save/load queue configurations as JSON files
- **Results Tracking**: Automatic saving of results for all runs
- **Flexible Configuration**: Each run can have different parameters

See [docs/GA_RUNS_QUEUE.md](docs/GA_RUNS_QUEUE.md) for complete documentation.
