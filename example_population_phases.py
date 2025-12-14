#!/usr/bin/env python3
"""
Minimal example demonstrating population phases feature
"""

import sys
from pathlib import Path

# Add src to import path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Example from the issue description
example_phases = [
    (30, 50),   # run 30 iterations, max population 50
    (1, 1000),  # then expand 1 iteration, 1000 population
    (10, 50),   # then again 10 iterations, 50 population
    (1, 2000),  # expand to 2K
    (20, 30),   # 20 iterations, 30 population
    (1, 3000),  # expand to 3k
    (10, 50)    # finish with 10 iterations, 50 population
]

print("\n" + "="*80)
print("POPULATION PHASES EXAMPLE")
print("="*80)
print("\nThis demonstrates the 'shake things up' approach from the issue:")
print()

total_iterations = 0
for i, (iters, pop) in enumerate(example_phases, 1):
    total_iterations += iters
    print(f"Phase {i}: {iters:3d} iterations, max population {pop:4d}")

avg_pop = sum(p[0] * p[1] for p in example_phases) / total_iterations
print(f"\nTotal max iterations: {total_iterations}")
print(f"Average population: {avg_pop:.1f}")

print("\n" + "="*80)
print("COMPATIBILITY METRICS FOR ANALYSIS")
print("="*80)
print(f"These would be saved to metadata for comparison with standard runs:")
print(f"  - mode: 'population_phases'")
print(f"  - population_phases: {example_phases}")
print(f"  - total_max_iterations: {total_iterations}")
print(f"  - average_population: {avg_pop:.1f}")
print(f"  - population_size: {avg_pop:.1f} (for compatibility)")
print(f"  - max_iterations: {total_iterations} (for compatibility)")
print(f"  - actual_iterations: <tracked during run>")

print("\n" + "="*80)
print("HOW TO USE")
print("="*80)
print("\nOption 1: From Python code")
print("-" * 40)
print("from core.run_ga import run_genetic_algorithm")
print()
print("best = run_genetic_algorithm(")
print("    keyboard_file='src/data/keyboards/ansi_60_percent.json',")
print("    text_file='src/data/text/raw/simple_wikipedia_dataset.txt',")
print(f"    population_phases={example_phases},")
print("    stagnant_limit=15,")
print("    max_concurrent_processes=4")
print(")")

print("\nOption 2: From main.py menu")
print("-" * 40)
print("1. Run: python main.py")
print("2. Select: '🚀 Run Genetic Algorithm (Master Mode)'")
print("3. Choose mode: '2' for Population Phases Mode")
print("4. Define your phases interactively")

print("\nOption 3: Using GA Runs Queue")
print("-" * 40)
print("from core.ga_runs_queue import GARunsQueue, create_run_config")
print()
print("queue = GARunsQueue()")
print("queue.add_run(create_run_config(")
print("    name='Shake_Things_Up',")
print(f"    population_phases={example_phases},")
print("    stagnant_limit=15")
print("))")
print("queue.execute()")

print("\n" + "="*80)
