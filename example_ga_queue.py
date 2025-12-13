#!/usr/bin/env python3
"""
Example script showing how to programmatically create and execute a GA runs queue.

Users can modify this script to create custom queues with different parameters.
The Individual ID counter is automatically reset between runs.
"""

import sys
from pathlib import Path

# Add src to import path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.ga_runs_queue import GARunsQueue, create_run_config


def create_my_custom_queue():
    """
    Create a custom queue of GA runs.
    Modify this function to define your own sequence of runs.
    """
    queue = GARunsQueue()
    
    # Example 1: Quick test with small population
    queue.add_run(create_run_config(
        name="Quick Test Run",
        keyboard_file='src/data/keyboards/ansi_60_percent.json',
        text_file='src/data/text/raw/simple_wikipedia_dataset.txt',
        population_size=10,
        max_iterations=20,
        stagnant_limit=5,
        max_concurrent_processes=4,
        fitts_a=0.5,
        fitts_b=0.3
    ))
    
    # Example 2: Medium run with standard parameters
    # Using default values for most parameters
    queue.add_run(create_run_config(
        name="Medium Run - Standard",
        population_size=30,
        max_iterations=50,
        stagnant_limit=10
    ))
    
    # Example 3: Experiment with different Fitts's Law parameters
    queue.add_run(create_run_config(
        name="Fitts Experiment - Higher a",
        population_size=20,
        max_iterations=30,
        stagnant_limit=8,
        fitts_a=0.7,  # Higher 'a' parameter
        fitts_b=0.3
    ))
    
    # Example 4: Experiment with different finger coefficients
    custom_finger_coeffs = [0.1, 0.08, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06, 0.08, 0.1]
    queue.add_run(create_run_config(
        name="Finger Coefficients Experiment",
        population_size=20,
        max_iterations=30,
        stagnant_limit=8,
        finger_coefficients=custom_finger_coeffs
    ))
    
    # Example 5: Direct dictionary manipulation (for advanced users)
    # You can also directly create/modify dictionaries
    run_dict = {
        'name': 'Custom Dictionary Run',
        'population_size': 15,
        'max_iterations': 25,
        'fitts_a': 0.55
    }
    queue.add_run(run_dict)
    
    return queue


def main():
    print("=" * 80)
    print("CUSTOM GA RUNS QUEUE EXECUTION")
    print("=" * 80)
    
    # Create the queue
    queue = create_my_custom_queue()
    
    print(f"\nCreated queue with {len(queue.runs)} runs:")
    for i, run in enumerate(queue.runs, 1):
        print(f"\n{i}. {run['name']}")
        print(f"   Population: {run['population_size']}")
        print(f"   Iterations: {run['max_iterations']}")
        print(f"   Stagnation: {run['stagnant_limit']}")
        print(f"   Fitts a={run['fitts_a']}, b={run['fitts_b']}")
    
    # Save queue configuration for reference
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
    queue_file = f"output/ga_queues/custom_queue_{timestamp}.json"
    Path(queue_file).parent.mkdir(parents=True, exist_ok=True)
    queue.save_to_file(queue_file)
    print(f"\n✅ Queue configuration saved to: {queue_file}")
    
    # Ask for confirmation
    response = input("\nExecute this queue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Queue execution cancelled.")
        return
    
    # Execute the queue
    print("\n" + "=" * 80)
    print("STARTING QUEUE EXECUTION")
    print("=" * 80)
    
    results = queue.execute(verbose=True)
    
    # Save results
    results_file = f"output/ga_queue_results/queue_{timestamp}.json"
    queue.save_results(results_file)
    
    print("\n" + "=" * 80)
    print("QUEUE EXECUTION COMPLETE")
    print("=" * 80)
    print(f"Results saved to: {results_file}")


if __name__ == "__main__":
    main()
