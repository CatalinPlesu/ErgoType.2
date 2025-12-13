# GA Runs Queue

This feature allows you to programmatically define and execute a queue of GA (Genetic Algorithm) runs with different parameters. All runs are executed sequentially, and the Individual ID counter is automatically reset between runs to ensure consistent naming.

## Features

- **Sequential Execution**: Execute multiple GA runs one after another
- **Automatic ID Reset**: Individual ID counter is reset before each run
- **Flexible Configuration**: Define runs with different parameters (population size, iterations, Fitts's Law constants, etc.)
- **Queue Management**: Save and load queue configurations from JSON files
- **Results Tracking**: Automatic saving of results for all runs in the queue

## Usage

### 1. Through the Menu (Interactive)

Run the main application and select:
```
📋 Execute GA Runs Queue
```

Then choose one of the options:
- **Run Example Queue**: Execute 3 preconfigured runs for demonstration
- **Load Queue from File**: Load and execute a saved queue configuration
- **Create Custom Queue Interactively**: Build a custom queue step-by-step

### 2. Programmatically (Python Script)

Use the provided example script or create your own:

```bash
python3 example_ga_queue.py
```

Or create your own script:

```python
from core.ga_runs_queue import GARunsQueue, GARunConfig

# Create a queue
queue = GARunsQueue()

# Add runs with different configurations
queue.add_run(GARunConfig(
    name="Quick Test",
    population_size=10,
    max_iterations=20,
    stagnant_limit=5
))

queue.add_run(GARunConfig(
    name="Production Run",
    population_size=50,
    max_iterations=100,
    stagnant_limit=15,
    fitts_a=0.6,
    fitts_b=0.4
))

# Execute the queue
results = queue.execute(verbose=True)

# Save results
queue.save_results("output/my_results.json")
```

### 3. Queue Configuration Files

Save and reuse queue configurations:

```python
# Save queue to file
queue.save_to_file("output/ga_queues/my_queue.json")

# Load queue from file
queue2 = GARunsQueue()
queue2.load_from_file("output/ga_queues/my_queue.json")
queue2.execute()
```

## Configuration Parameters

Each run can be configured with:

- **name**: Descriptive name for the run
- **keyboard_file**: Path to keyboard layout JSON
- **text_file**: Path to text file for simulation
- **population_size**: Number of individuals in population
- **max_iterations**: Maximum number of generations
- **stagnant_limit**: Stop after N iterations without improvement
- **max_concurrent_processes**: Number of parallel processes
- **fitts_a**: Fitts's Law constant 'a'
- **fitts_b**: Fitts's Law constant 'b'
- **finger_coefficients**: List of 10 finger coefficients (optional)
- **use_rabbitmq**: Whether to use RabbitMQ for distributed processing
- **save_heuristics**: Whether to save heuristic layouts

## Output Files

### Queue Configuration
Saved to `output/ga_queues/`:
```json
{
  "runs": [
    {
      "name": "Run 1",
      "population_size": 30,
      "max_iterations": 50,
      ...
    }
  ]
}
```

### Queue Results
Saved to `output/ga_queue_results/`:
```json
{
  "total_runs": 3,
  "successful_runs": 3,
  "failed_runs": 0,
  "results": [
    {
      "run_number": 1,
      "name": "Run 1",
      "start_time": "2025-12-13T10:00:00",
      "duration_seconds": 150.5,
      "success": true,
      "best_fitness": 0.123456,
      "best_layout": "qwertyuiop...",
      "config": {...}
    }
  ]
}
```

### Individual Run Results
Each run creates its own directory in `output/ga_results/` with:
- `ga_run_metadata.json` - Run configuration and statistics
- `ga_all_individuals.json` - All individuals evaluated
- `fitness_evolution.png` - Fitness plot over generations
- `rank1_*.json`, `rank2_*.json`, `rank3_*.json` - Top 3 layouts
- SVG visualizations for top 3 layouts

## Example Use Cases

### 1. Parameter Sweep
Test different Fitts's Law parameters:
```python
queue = GARunsQueue()
for a in [0.3, 0.5, 0.7]:
    for b in [0.2, 0.3, 0.4]:
        queue.add_run(GARunConfig(
            name=f"Fitts_a{a}_b{b}",
            fitts_a=a,
            fitts_b=b,
            population_size=20,
            max_iterations=30
        ))
```

### 2. Overnight Batch
Run multiple long experiments overnight:
```python
queue = GARunsQueue()
queue.add_run(GARunConfig(
    name="Large Population 1",
    population_size=100,
    max_iterations=200
))
queue.add_run(GARunConfig(
    name="Large Population 2",
    population_size=100,
    max_iterations=200,
    fitts_a=0.6
))
```

### 3. Different Datasets
Test the same configuration on different text files:
```python
text_files = [
    'src/data/text/raw/simple_wikipedia_dataset.txt',
    'src/data/text/raw/code_dataset.txt',
    'src/data/text/raw/literary_dataset.txt'
]

for text_file in text_files:
    queue.add_run(GARunConfig(
        name=f"Test on {Path(text_file).stem}",
        text_file=text_file,
        population_size=30
    ))
```

## Important Notes

1. **Individual ID Reset**: The `Individual._next_id` counter is automatically reset to 0 before each run. This ensures consistent naming across runs.

2. **Sequential Execution**: Runs execute one at a time. For parallel execution of independent experiments, use multiple worker nodes instead.

3. **Resource Management**: Each run uses the specified number of concurrent processes. Ensure your system has sufficient resources.

4. **Error Handling**: If a run fails, the queue continues with the next run. Check the results JSON for success/failure status.

5. **Queue Persistence**: Save queue configurations to reuse them later or share with others.

## Troubleshooting

- **Import Errors**: Ensure you're running from the project root and the `src/` directory is in the Python path
- **File Not Found**: Use relative paths from project root (e.g., `src/data/keyboards/...`)
- **RabbitMQ Issues**: Set `use_rabbitmq=False` if RabbitMQ is not available
- **Memory Issues**: Reduce `population_size` or `max_concurrent_processes` if running out of memory
