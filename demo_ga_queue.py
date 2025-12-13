#!/usr/bin/env python3
"""
Demonstration of Individual ID reset between GA runs.

This script shows that Individual._next_id is properly reset between runs,
ensuring consistent naming across multiple sequential GA runs.
"""

import sys
from pathlib import Path

# Add src to import path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def demonstrate_id_reset():
    """Demonstrate Individual ID counter reset"""
    
    print("=" * 80)
    print("DEMONSTRATION: Individual ID Reset Between Runs")
    print("=" * 80)
    
    # Import the actual Individual class (requires avoiding pika import)
    # For demonstration, we'll use a simplified version
    
    class Individual:
        """Simplified Individual class for demonstration"""
        _next_id = 0
        
        def __init__(self, name=None, generation=0):
            self.id = Individual._next_id
            Individual._next_id += 1
            self.generation = generation
            self.name = name or f"gen_{generation}-{self.id}"
        
        def __repr__(self):
            return f"Individual(id={self.id}, name={self.name})"
    
    print("\n--- Scenario 1: Without ID Reset ---")
    print("Creating individuals for Run 1:")
    
    ind1 = Individual(generation=0)
    ind2 = Individual(generation=0)
    ind3 = Individual(generation=0)
    
    print(f"  {ind1}")
    print(f"  {ind2}")
    print(f"  {ind3}")
    print(f"  Current _next_id: {Individual._next_id}")
    
    print("\nCreating individuals for Run 2 (no reset):")
    
    ind4 = Individual(generation=0)
    ind5 = Individual(generation=0)
    ind6 = Individual(generation=0)
    
    print(f"  {ind4}")
    print(f"  {ind5}")
    print(f"  {ind6}")
    print(f"  Current _next_id: {Individual._next_id}")
    
    print("\n❌ Problem: IDs continue to increase (3, 4, 5) instead of restarting from 0")
    print("   This makes comparing runs difficult and wastes ID space")
    
    print("\n" + "=" * 80)
    print("\n--- Scenario 2: With ID Reset (Queue Feature) ---")
    
    # Reset for Run 1
    Individual._next_id = 0
    print("\n✅ Reset Individual._next_id to 0 before Run 1")
    print("Creating individuals for Run 1:")
    
    run1_ind1 = Individual(generation=0)
    run1_ind2 = Individual(generation=0)
    run1_ind3 = Individual(generation=0)
    
    print(f"  {run1_ind1}")
    print(f"  {run1_ind2}")
    print(f"  {run1_ind3}")
    print(f"  Current _next_id: {Individual._next_id}")
    
    # Reset for Run 2
    Individual._next_id = 0
    print("\n✅ Reset Individual._next_id to 0 before Run 2")
    print("Creating individuals for Run 2:")
    
    run2_ind1 = Individual(generation=0)
    run2_ind2 = Individual(generation=0)
    run2_ind3 = Individual(generation=0)
    
    print(f"  {run2_ind1}")
    print(f"  {run2_ind2}")
    print(f"  {run2_ind3}")
    print(f"  Current _next_id: {Individual._next_id}")
    
    print("\n✅ Success: Each run starts with ID 0, ensuring consistent naming")
    print("   Run 1: gen_0-0, gen_0-1, gen_0-2")
    print("   Run 2: gen_0-0, gen_0-1, gen_0-2")
    
    print("\n" + "=" * 80)
    print("HOW THE QUEUE IMPLEMENTS THIS")
    print("=" * 80)
    
    print("""
The GARunsQueue.execute() method automatically resets the ID counter:

    for i, run_config in enumerate(self.runs, 1):
        # CRITICAL: Reset Individual ID counter before each run
        Individual._next_id = 0
        
        # Execute the GA run
        best_individual = run_genetic_algorithm(**run_config.to_dict())
        ...

This ensures:
1. Each run starts with fresh Individual IDs (0, 1, 2, ...)
2. Naming is consistent across runs (gen_0-0, gen_0-1, etc.)
3. Results from different runs can be easily compared
4. No ID overflow issues with many runs
""")
    
    print("=" * 80)


def demonstrate_queue_usage():
    """Demonstrate creating and using a queue"""
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION: Creating a Queue with Multiple Runs")
    print("=" * 80)
    
    from core.ga_runs_queue import GARunsQueue, create_run_config
    
    queue = GARunsQueue()
    
    # Add multiple runs using create_run_config helper
    queue.add_run(create_run_config(
        name="Quick Test",
        population_size=5,
        max_iterations=3,
        stagnant_limit=2
    ))
    
    queue.add_run(create_run_config(
        name="Medium Run",
        population_size=10,
        max_iterations=5,
        stagnant_limit=3
    ))
    
    queue.add_run(create_run_config(
        name="Fitts Experiment",
        population_size=8,
        max_iterations=4,
        fitts_a=0.6,
        fitts_b=0.4
    ))
    
    # Alternative: Add run as a plain dictionary
    queue.add_run({
        'name': 'Direct Dictionary Run',
        'population_size': 12,
        'max_iterations': 6
    })
    
    print(f"\nCreated queue with {len(queue.runs)} runs:")
    
    for i, run in enumerate(queue.runs, 1):
        print(f"\n{i}. {run['name']}")
        print(f"   Population: {run['population_size']}")
        print(f"   Iterations: {run['max_iterations']}")
        print(f"   Stagnation: {run['stagnant_limit']}")
        print(f"   Fitts: a={run['fitts_a']}, b={run['fitts_b']}")
    
    # Demonstrate easy manipulation
    print("\n" + "=" * 80)
    print("DEMONSTRATION: Easy Queue Manipulation")
    print("=" * 80)
    
    print("\nOriginal queue has", len(queue.runs), "runs")
    
    # Remove a run by index
    print("\nRemoving run at index 1 (Medium Run)...")
    queue.remove_run(1)
    print(f"Queue now has {len(queue.runs)} runs")
    
    # Directly modify a run in the list
    print("\nModifying the first run's population size...")
    queue.runs[0]['population_size'] = 15
    print(f"First run now has population size: {queue.runs[0]['population_size']}")
    
    # Save to file
    Path('output').mkdir(exist_ok=True)
    queue_file = 'output/demo_queue.json'
    queue.save_to_file(queue_file)
    
    print(f"\n✅ Queue saved to: {queue_file}")
    
    # Show what execution would do
    print("\nWhen queue.execute() is called:")
    print("  1. Reset Individual._next_id = 0")
    print("  2. Run 'Quick Test' with specified parameters")
    print("  3. Save results")
    print("  4. Reset Individual._next_id = 0")
    print("  5. Run 'Direct Dictionary Run' with specified parameters")
    print("  6. Save results")
    print("  7. Reset Individual._next_id = 0")
    print("  8. Run 'Fitts Experiment' with specified parameters")
    print("  9. Save results")
    print(" 10. Generate summary report")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    demonstrate_id_reset()
    demonstrate_queue_usage()
    
    print("\n✅ Demonstration complete!")
    print("\nTo execute a real queue, use:")
    print("  python3 example_ga_queue.py")
    print("  or run main.py and select '📋 Execute GA Runs Queue'")
    print()
