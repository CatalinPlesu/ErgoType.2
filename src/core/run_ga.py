"""
Genetic Algorithm Runner Script
Run this to optimize keyboard layouts using the genetic algorithm
"""

from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
from src.core.ga import GeneticAlgorithm
import sys
import os
from datetime import datetime

# Add parent directory to path if needed
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


def run_genetic_algorithm(
    keyboard_file='src/data/keyboards/ansi_60_percent.json',
    dataset_file='src/data/text/processed/frequency_analysis.pkl',
    dataset_name='simple_wikipedia',
    population_size=50,
    max_iterations=100,
    stagnant_limit=15
):
    """
    Run the genetic algorithm with specified parameters

    Args:
        keyboard_file: Path to keyboard JSON file
        dataset_file: Path to frequency analysis pickle file
        dataset_name: Name of dataset to use from pickle file
        population_size: Size of population
        max_iterations: Maximum number of iterations
        stagnant_limit: Number of iterations without improvement before stopping
    """

    print("="*80)
    print("KEYBOARD LAYOUT GENETIC ALGORITHM")
    print("="*80)
    print(f"Keyboard: {keyboard_file}")
    print(f"Dataset: {dataset_name}")
    print(f"Population size: {population_size}")
    print(f"Max iterations: {max_iterations}")
    print(f"Stagnation limit: {stagnant_limit}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()

    # Initialize GA
    ga = GeneticAlgorithm(
        keyboard_file=keyboard_file,
        dataset_file=dataset_file,
        dataset_name=dataset_name
    )

    # Adjust population size if needed
    if len(ga.population) != population_size:
        ga.population_initialization(size=population_size)

    # Run GA
    best_individual = ga.run(
        max_iterations=max_iterations,
        stagnant=stagnant_limit
    )

    # Print final results
    print("\n" + "="*80)
    print("OPTIMIZATION COMPLETE")
    print("="*80)
    print(f"Best Individual ID: {best_individual.id}")
    print(f"Fitness Score: {best_individual.fitness:.6f}")
    print(f"""Parent IDs: {
          best_individual.parents if best_individual.parents else 'Initial Population'}""")
    print(f"\nOptimized Layout:")
    print(''.join(best_individual.chromosome))
    print()

    # Compare with known layouts
    print("="*80)
    print("COMPARISON WITH STANDARD LAYOUTS")
    print("="*80)

    # Re-evaluate some standard layouts for comparison
    comparison_layouts = {
        'QWERTY': LAYOUT_DATA['qwerty'],
        'Dvorak': LAYOUT_DATA['dvorak'],
        'Colemak': LAYOUT_DATA['colemak'],
        'Optimized': best_individual.chromosome
    }

    layout_scores = []
    for name, layout in comparison_layouts.items():
        ga.evaluator.layout.querty_based_remap(layout)
        fitness_dict = ga.evaluator.typer.fitness()
        combined = fitness_dict['distance_score'] * (
            2.0 - fitness_dict['ngram_score']) * (2.0 - fitness_dict['homing_score'])
        layout_scores.append((name, combined, fitness_dict))

    # Sort by combined score
    layout_scores.sort(key=lambda x: x[1])

    print(f"""\n{'Rank':<6} {'Layout':<15} {'Combined':<15} {
          'Distance':<15} {'N-gram':<12} {'Homing':<12}""")
    print("-"*80)
    for rank, (name, combined, fitness) in enumerate(layout_scores, 1):
        print(f"""{rank:<6} {name:<15} {combined:<15.2f} {fitness['distance_score']:<15.2f} {
              fitness['ngram_score']:<12.4f} {fitness['homing_score']:<12.4f}""")

    print("="*80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    return best_individual


if __name__ == "__main__":
    # Configuration
    CONFIG = {
        'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
        'dataset_file': 'src/data/text/processed/frequency_analysis.pkl',
        'dataset_name': 'simple_wikipedia',
        'population_size': 30,  # Smaller for faster testing
        'max_iterations': 50,
        'stagnant_limit': 10
    }

    # Run GA
    best = run_genetic_algorithm(**CONFIG)

    print("\nTo use different parameters, modify the CONFIG dictionary or call:")
    print("run_genetic_algorithm(population_size=100, max_iterations=200, stagnant_limit=20)")
