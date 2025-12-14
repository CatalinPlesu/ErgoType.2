#!/usr/bin/env python3
"""
Example GA Queue with Population Phases
Demonstrates using population phases in a queue configuration
"""

import sys
from pathlib import Path

# Add src to import path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.ga_runs_queue import GARunsQueue, create_run_config

def create_population_phases_comparison_queue():
    """
    Create a queue comparing standard mode vs population phases mode.
    Uses small sizes for quick testing.
    """
    queue = GARunsQueue()
    
    # Run 1: Standard mode baseline
    queue.add_run(create_run_config(
        name="Standard_Baseline",
        population_size=20,
        max_iterations=10,
        stagnant_limit=5,
        max_concurrent_processes=2
    ))
    
    # Run 2: Population phases - expansion/contraction pattern
    queue.add_run(create_run_config(
        name="Phases_Expansion_Contraction",
        population_phases=[
            (5, 20),   # Start with 5 iterations, 20 population
            (1, 40),   # Expand to 40
            (5, 20),   # Contract back to 20
            (1, 60),   # Expand to 60
            (3, 20)    # Finish with 20
        ],
        stagnant_limit=5,
        max_concurrent_processes=2
    ))
    
    # Run 3: Population phases - shake things up (mini version)
    queue.add_run(create_run_config(
        name="Phases_Shake_Things_Up",
        population_phases=[
            (5, 15),   # Start narrow
            (1, 50),   # Brief expansion
            (3, 15),   # Back to narrow
            (1, 100),  # Large expansion
            (5, 15)    # Finish narrow
        ],
        stagnant_limit=5,
        max_concurrent_processes=2
    ))
    
    # Run 4: Population phases - progressive growth
    queue.add_run(create_run_config(
        name="Phases_Progressive_Growth",
        population_phases=[
            (3, 10),
            (3, 20),
            (3, 30),
            (3, 40)
        ],
        stagnant_limit=5,
        max_concurrent_processes=2
    ))
    
    return queue


if __name__ == "__main__":
    print("="*80)
    print("POPULATION PHASES QUEUE EXAMPLE")
    print("="*80)
    
    queue = create_population_phases_comparison_queue()
    
    print(f"\nCreated queue with {len(queue.runs)} runs:")
    for i, run in enumerate(queue.runs, 1):
        print(f"\n{i}. {run['name']}")
        if run.get('population_phases'):
            print(f"   Mode: Population Phases")
            for j, (iters, pop) in enumerate(run['population_phases'], 1):
                print(f"     Phase {j}: {iters} iterations, {pop} max pop")
            total_iters = sum(p[0] for p in run['population_phases'])
            avg_pop = sum(p[0] * p[1] for p in run['population_phases']) / total_iters
            print(f"   Total: {total_iters} iterations, avg pop: {avg_pop:.1f}")
        else:
            print(f"   Mode: Standard")
            print(f"   Population: {run['population_size']}")
            print(f"   Iterations: {run['max_iterations']}")
    
    print("\n" + "="*80)
    print("To save this queue configuration:")
    print("-" * 80)
    print("queue.save_to_file('output/ga_queues/phases_comparison.json')")
    
    print("\nTo execute the queue:")
    print("-" * 80)
    print("results = queue.execute(verbose=True)")
    print("queue.save_results('output/ga_queue_results/phases_comparison_results.json')")
    
    print("\n" + "="*80)
    print("SAVE QUEUE? (y/n)")
    print("="*80)
    
    response = input("Save queue configuration? [y/N]: ").strip().lower()
    
    if response == 'y':
        output_file = "output/ga_queues/example_phases_comparison.json"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        queue.save_to_file(output_file)
        print(f"\n✅ Queue saved to: {output_file}")
        
        print("\nTo execute this queue later, use:")
        print(f"  python -c \"from core.ga_runs_queue import GARunsQueue; q = GARunsQueue(); q.load_from_file('{output_file}'); q.execute()\"")
        print("\nOr from main.py menu:")
        print("  1. Select: '📋 Execute GA Runs Queue'")
        print("  2. Select: '2️⃣  Load Queue from File'")
        print(f"  3. Enter path: {output_file}")
    else:
        print("\n❌ Queue not saved")
    
    print()
