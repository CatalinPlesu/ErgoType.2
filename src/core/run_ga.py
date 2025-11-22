""" Genetic Algorithm Runner Script
Run this to optimize keyboard layouts using the genetic algorithm
"""
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
from src.core.ga import GeneticAlgorithm
from src.helpers.layouts.visualization import LayoutVisualization
from src.helpers.keyboards.renderer import render_keyboard
from src.core.mapper import KeyType
from src.config.config import Config
import sys
import os
from datetime import datetime
import json
import pickle
from pathlib import Path

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
    print(f"Best Individual Name: {best_individual.name}")
    print(f"Fitness Score: {best_individual.fitness:.6f}")
    parent_names = [ga.get_individual_name(p) for p in best_individual.parents] if best_individual.parents else ['Initial Population']
    print(f"Parent Names: {', '.join(parent_names)}")
    print(f"\nOptimized Layout:")
    print(''.join(best_individual.chromosome))
    print()

    # Get the top 3 best individuals
    sorted_population = sorted(ga.population, key=lambda x: x.fitness)
    top_3_individuals = sorted_population[:3]

    # Generate timestamp for file naming
    timestamp = datetime.now().strftime("%Y-%m-%d--%H:%M:%S")

    # Create output directory with GA run info (using new format)
    output_dir = Path("output/ga_results")
    run_dir = output_dir / f"ga_run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Save GA run metadata
    ga_run_data = {
        "timestamp": timestamp,
        "keyboard_file": keyboard_file,
        "dataset_file": dataset_file,
        "dataset_name": dataset_name,
        "population_size": population_size,
        "max_iterations": max_iterations,
        "stagnant_limit": stagnant_limit,
        "best_fitness": best_individual.fitness,
        "best_layout_name": best_individual.name,
        "best_layout": ''.join(best_individual.chromosome),
        "total_individuals_evaluated": len(ga.evaluated_individuals)
    }

    ga_run_path = run_dir / "ga_run_metadata.json"
    with open(ga_run_path, 'w', encoding='utf-8') as f:
        json.dump(ga_run_data, f, indent=2, ensure_ascii=False)
    print(f"Saved GA run metadata: {ga_run_path}")

    # Save best 3 layouts to JSON and SVG
    print("="*80)
    print("SAVING BEST 3 LAYOUTS")
    print("="*80)

    for i, individual in enumerate(top_3_individuals, 1):
        # Use individual's name for file naming with rank prefix
        layout_name = individual.name
        file_name = f"rank{i}_{layout_name}"
        
        print(f"\nProcessing Layout {i}: {layout_name}")
        print(f"Fitness: {individual.fitness:.6f}")
        print(f"Layout: {''.join(individual.chromosome)}")
        
        # Get parent names
        parent_names = [ga.get_individual_name(p) for p in individual.parents] if individual.parents else []

        # Save JSON data
        json_data = {
            "timestamp": timestamp,
            "rank": i,
            "name": layout_name,
            "file_name": file_name,
            "fitness": individual.fitness,
            "chromosome": individual.chromosome,
            "parents": parent_names,
            "parent_ids": individual.parents,
            "generation": individual.generation,
            "layout_string": ''.join(individual.chromosome),
            "keyboard_file": keyboard_file,
            "dataset_file": dataset_file,
            "dataset_name": dataset_name
        }

        json_path = run_dir / f"{file_name}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"  Saved JSON: {json_path}")

        # Generate and save SVG for each layer
        try:
            # Apply the optimized layout directly using remap method
            from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
            ga.evaluator.layout.remap(
                LAYOUT_DATA["qwerty"], individual.chromosome)

            # Get all layers
            layers = []
            for key_id, layer_idx in ga.evaluator.layout.mapper.data.keys():
                if layer_idx not in layers:
                    layers.append(layer_idx)
            layers = sorted(layers) if layers else [0]

            # Save SVG for each layer
            for layer_idx in layers:
                # UPDATE KEYBOARD KEY LABELS FOR THIS LAYER
                for key_obj in ga.evaluator.keyboard.keys:
                    key_obj.clear_labels()

                for key_obj in ga.evaluator.keyboard.keys:
                    key_id = key_obj.id
                    if (key_id, layer_idx) in ga.evaluator.layout.mapper.data:
                        key_data = ga.evaluator.layout.mapper.data[(
                            key_id, layer_idx)]
                        if key_data.key_type == KeyType.CHAR:
                            key_obj.set_labels(key_data.value)
                        elif key_data.key_type in [KeyType.SPECIAL_CHAR, KeyType.CONTROL, KeyType.LAYER]:
                            if isinstance(key_data.value, tuple):
                                key_obj.set_labels((key_data.value[1],) if len(
                                    key_data.value) > 1 else (key_data.value[0],))
                            else:
                                key_obj.set_labels((key_data.value,))

                # Use the renderer directly for better control
                from src.helpers.keyboards.renderer import render_keyboard_with_heatmap

                # Generate SVG visualization (without heatmap for cleaner export)
                keyboard_svg = render_keyboard_with_heatmap(
                    ga.evaluator.keyboard,
                    {},
                    layer_idx=layer_idx,
                    freq_range=1.0,
                    min_freq=0.0,
                    layout=ga.evaluator.layout
                )

                # Extract SVG content from the IPython SVG object
                if hasattr(keyboard_svg, 'data'):
                    svg_content = keyboard_svg.data
                elif hasattr(keyboard_svg, '_repr_svg_'):
                    svg_content = keyboard_svg._repr_svg_()
                else:
                    svg_content = str(keyboard_svg)

                # Save SVG file with rank prefix and layout name
                svg_path = run_dir / f"{file_name}_layer_{layer_idx}.svg"
                with open(svg_path, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
                print(f"  Saved Layer {layer_idx}: {svg_path}")

        except Exception as e:
            print(f"  Error generating SVG: {e}")

    print(f"\nSaved {len(top_3_individuals)} layouts to {run_dir}")
    print("="*80)

    # Compare with known layouts
    print("="*80)
    print("COMPARISON WITH STANDARD LAYOUTS")
    print("="*80)

    # Create a FRESH evaluator for comparison (no state pollution)
    from src.core.evaluator import Evaluator

    comparison_evaluator = Evaluator(debug=False)
    comparison_evaluator.load_keyoard(keyboard_file)
    comparison_evaluator.load_distance()
    comparison_evaluator.load_layout()
    comparison_evaluator.load_dataset(dataset_file=dataset_file, dataset_name=dataset_name)
    comparison_evaluator.load_typer()

    # Add optimized layout to comparison
    comparison_layouts = LAYOUT_DATA.copy()
    comparison_layouts[best_individual.name] = best_individual.chromosome

    layout_scores = []
    for name, layout in comparison_layouts.items():
        # Remap layout
        comparison_evaluator.layout.remap(LAYOUT_DATA["qwerty"], layout)
        
        # Calculate fitness using Typer (fresh calculation)
        fitness_dict = comparison_evaluator.typer.fitness()
        
        # Combine using same formula as GA
        combined = Config.fitness.distance_weight * fitness_dict['distance_score'] + \
            Config.fitness.n_gram_weight * fitness_dict['distance_score'] * (1.0 - fitness_dict['ngram_score']) + \
            Config.fitness.homerow_weight * fitness_dict['distance_score'] * (1.0 - fitness_dict['homing_score'])
        
        layout_scores.append((name, combined, fitness_dict))

    # Sort by combined score (lower is better)
    layout_scores.sort(key=lambda x: x[1])

    print(f"\n{'Rank':<6} {'Layout':<20} {'Combined':<15} {'Distance':<15} {'N-gram':<12} {'Homing':<12}")
    print("-"*90)

    for rank, (name, combined, fitness) in enumerate(layout_scores, 1):
        print(f"{rank:<6} {name:<20} {combined:<15.2f} {fitness['distance_score']:<15.2f} {fitness['ngram_score']:<12.4f} {fitness['homing_score']:<12.4f}")
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
