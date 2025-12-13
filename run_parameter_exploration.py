#!/usr/bin/env python3
"""
Parameter Exploration Script - Execute 25 predefined GA configurations.

This script runs a carefully selected matrix of 25 configurations that explore
the iteration/population parameter space, optimized for ~3 hours runtime.

All configurations use:
- stagnant_limit: 3
- max_concurrent_processes: 1

Parameter coverage:
- Iterations: 5 to 300 (10 levels)
- Population: 5 to 300 (7 levels)
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to import path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.ga_runs_queue import create_parameter_exploration_queue


def main():
    print("=" * 80)
    print("PARAMETER EXPLORATION - 25 Configuration Matrix")
    print("=" * 80)
    
    # Create the exploration queue
    queue = create_parameter_exploration_queue()
    
    print(f"\nTotal configurations: {len(queue.runs)}")
    print(f"Estimated runtime: ~3 hours")
    print(f"All runs use: stagnant_limit=3, max_concurrent_processes=1")
    print()
    
    # Display configuration matrix
    print("Configuration Matrix:")
    print("-" * 80)
    print(f"{'#':<4} {'Iter':<6} {'Pop':<6} {'Purpose':<50}")
    print("-" * 80)
    
    for i, run in enumerate(queue.runs, 1):
        iterations = run['max_iterations']
        population = run['population_size']
        purpose = run['name'].split('_', 3)[-1].replace('_', ' ')
        print(f"{i:<4} {iterations:<6} {population:<6} {purpose:<50}")
    
    print("-" * 80)
    print(f"\nTotal evaluations: ~{sum(r['max_iterations'] * r['population_size'] for r in queue.runs):,}")
    print()
    
    # Ask for confirmation
    response = input("Execute all 25 configurations? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Execution cancelled.")
        return
    
    # Execute the queue
    print("\n" + "=" * 80)
    print("STARTING PARAMETER EXPLORATION")
    print("=" * 80)
    
    results = queue.execute(verbose=True)
    
    # Save results
    timestamp = datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
    results_file = f"output/ga_queue_results/param_exploration_{timestamp}.json"
    queue.save_results(results_file)
    
    print("\n" + "=" * 80)
    print("PARAMETER EXPLORATION COMPLETE")
    print("=" * 80)
    print(f"Results saved to: {results_file}")
    
    # Print summary
    successful = sum(1 for r in results if r.get('success', False))
    failed = len(results) - successful
    
    print(f"\nSummary:")
    print(f"  Total runs: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    
    if successful > 0:
        print(f"\nBest fitness achieved:")
        best_result = min(
            (r for r in results if r.get('success', False) and r.get('best_fitness')),
            key=lambda x: x['best_fitness'],
            default=None
        )
        if best_result:
            print(f"  Configuration: {best_result['name']}")
            print(f"  Fitness: {best_result['best_fitness']:.6f}")


if __name__ == "__main__":
    main()
