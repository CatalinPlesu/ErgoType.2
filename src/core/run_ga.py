""" Genetic Algorithm Runner Script
Run this to optimize keyboard layouts using the genetic algorithm
"""
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
from src.core.ga import GeneticAlgorithm
from src.helpers.layouts.visualization import LayoutVisualization
from src.helpers.keyboards.renderer import render_keyboard
from src.core.mapper import KeyType
from src.config.config import Config
from src.core.ga import Individual
from src.core.evaluator import Evaluator
import sys
import os
import time
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
    print("Starting genetic algorithm optimization...")
    ga_start_time = time.time()
    
    best_individual = ga.run(
        max_iterations=max_iterations,
        stagnant=stagnant_limit
    )
    
    ga_total_time = time.time() - ga_start_time
    print(f"\n⏱️  GA execution completed in {ga_total_time:.2f} seconds")

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
    
    # Create subdirectories for organized output
    predefined_dir = run_dir / "predefined_layouts"
    predefined_dir.mkdir(exist_ok=True)
    
    winning_dir = run_dir / "winning_layouts" 
    winning_dir.mkdir(exist_ok=True)
    
    discarded_dir = run_dir / "discarded_layouts"
    discarded_dir.mkdir(exist_ok=True)

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
    print("SAVING WINNING LAYOUTS")
    print("="*80)

    winning_layouts_data = []

    for i, individual in enumerate(top_3_individuals, 1):
        # Use individual's name for file naming with rank prefix
        layout_name = individual.name
        file_name = f"rank{i}_{layout_name}"
        
        print(f"\nProcessing Winning Layout {i}: {layout_name}")
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
            "dataset_name": dataset_name,
            "type": "winning"
        }

        json_path = winning_dir / f"{file_name}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"  Saved JSON: {json_path}")
        
        # Store data for summary
        winning_layouts_data.append({
            'rank': i,
            'name': layout_name,
            'fitness': individual.fitness,
            'generation': individual.generation
        })

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

                # Generate SVG visualization
                try:
                    keyboard_svg = render_keyboard(
                        ga.evaluator.keyboard,
                        layer_idx=layer_idx,
                        layout=ga.evaluator.layout
                    )

                    # Extract SVG content
                    if hasattr(keyboard_svg, 'data'):
                        svg_content = keyboard_svg.data
                    elif hasattr(keyboard_svg, '_repr_svg_'):
                        svg_content = keyboard_svg._repr_svg_()
                    else:
                        svg_content = str(keyboard_svg)

                    # Save SVG file with rank prefix and layout name
                    svg_path = winning_dir / f"{file_name}_layer_{layer_idx}.svg"
                    with open(svg_path, 'w', encoding='utf-8') as f:
                        f.write(svg_content)
                    print(f"  Saved Layer {layer_idx}: {svg_path}")
                    
                except Exception as svg_e:
                    print(f"  Error generating SVG: {svg_e}")
                    # Create a simple placeholder SVG
                    placeholder_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="200" fill="#f0f0f0"/>
  <text x="400" y="100" text-anchor="middle" font-family="monospace" font-size="16">
    SVG generation failed for {layout_name} (Rank {i})
  </text>
</svg>'''
                    
                    svg_path = winning_dir / f"{file_name}_layer_{layer_idx}.svg"
                    with open(svg_path, 'w', encoding='utf-8') as f:
                        f.write(placeholder_svg)

        except Exception as e:
            print(f"  Error generating SVG: {e}")

    print(f"\nSaved {len(top_3_individuals)} winning layouts to {winning_dir}")
    print("="*80)
    
    # Save winning layouts summary
    winning_summary_data = {
        "timestamp": timestamp,
        "keyboard_file": keyboard_file,
        "dataset_file": dataset_file,
        "dataset_name": dataset_name,
        "winning_layouts": winning_layouts_data
    }
    
    winning_summary_path = winning_dir / "winning_layouts_summary.json"
    with open(winning_summary_path, 'w', encoding='utf-8') as f:
        json.dump(winning_summary_data, f, indent=2, ensure_ascii=False)
    print(f"Saved winning layouts summary: {winning_summary_path}")

    # Evaluate predefined layouts with fitness values
    print("="*80)
    print("EVALUATING PREDEFINED LAYOUTS WITH FITNESS VALUES")
    print("="*80)
    
    # Create a comparison evaluator for predefined layouts
    comparison_evaluator = Evaluator(debug=False)
    comparison_evaluator.load_keyoard(keyboard_file)
    comparison_evaluator.load_distance()
    comparison_evaluator.load_layout()
    comparison_evaluator.load_dataset(dataset_file=dataset_file, dataset_name=dataset_name)
    comparison_evaluator.load_typer()
    
    # Create a top-level directory for layout comparison
    layouts_dir = Path("layouts_comparison")
    layouts_dir.mkdir(parents=True, exist_ok=True)
    
    predefined_layouts_data = []
    
    # Save each predefined layout as JSON and SVG with fitness evaluation
    for layout_name, layout_genotype in LAYOUT_DATA.items():
        print(f"\nProcessing predefined layout: {layout_name}")
        
        # Create individual for this layout
        layout_individual = Individual(
            chromosome=list(layout_genotype),
            generation=0,
            name=layout_name
        )
        
        # Evaluate fitness for this layout
        try:
            fitness_result = ga.evaluator.evaluate(layout_individual)
            if isinstance(fitness_result, tuple) and len(fitness_result) == 3:
                fitness, distance, time_taken = fitness_result
            else:
                fitness = fitness_result
                distance = None
                time_taken = None
            
            print(f"  Fitness: {fitness:.6f}")
            if distance is not None:
                print(f"  Distance: {distance:.2f} mm")
            if time_taken is not None:
                print(f"  Time: {time_taken:.3f} seconds")
                
        except Exception as e:
            print(f"  Error evaluating fitness: {e}")
            fitness = None
            distance = None
            time_taken = None
        
        # Save JSON data with fitness values
        layout_json_data = {
            "timestamp": timestamp,
            "name": layout_name,
            "file_name": layout_name,
            "chromosome": layout_genotype,
            "layout_string": ''.join(layout_genotype),
            "keyboard_file": keyboard_file,
            "dataset_file": dataset_file,
            "dataset_name": dataset_name,
            "type": "predefined",
            "fitness": fitness,
            "distance": distance,
            "time": time_taken
        }
        
        # Save to both locations - GA run specific and general comparison
        layout_json_path = predefined_dir / f"{layout_name}.json"
        with open(layout_json_path, 'w', encoding='utf-8') as f:
            json.dump(layout_json_data, f, indent=2, ensure_ascii=False)
        print(f"  Saved JSON (GA run): {layout_json_path}")
        
        # Also save to general comparison directory
        general_layout_json_path = layouts_dir / f"{layout_name}.json"
        with open(general_layout_json_path, 'w', encoding='utf-8') as f:
            json.dump(layout_json_data, f, indent=2, ensure_ascii=False)
        print(f"  Saved JSON (general): {general_layout_json_path}")
        
        # Generate and save SVG
        try:
            # Apply the layout using a fresh evaluator
            comparison_evaluator.layout.remap(LAYOUT_DATA["qwerty"], layout_genotype)
            
            # Get all layers
            layers = []
            for key_id, layer_idx in comparison_evaluator.layout.mapper.data.keys():
                if layer_idx not in layers:
                    layers.append(layer_idx)
            layers = sorted(layers) if layers else [0]
            
            # Save SVG for each layer
            for layer_idx in layers:
                # Update keyboard key labels for this layer
                for key_obj in comparison_evaluator.keyboard.keys:
                    key_obj.clear_labels()
                
                for key_obj in comparison_evaluator.keyboard.keys:
                    key_id = key_obj.id
                    if (key_id, layer_idx) in comparison_evaluator.layout.mapper.data:
                        key_data = comparison_evaluator.layout.mapper.data[(
                            key_id, layer_idx)]
                        if key_data.key_type == KeyType.CHAR:
                            key_obj.set_labels(key_data.value)
                        elif key_data.key_type in [KeyType.SPECIAL_CHAR, KeyType.CONTROL, KeyType.LAYER]:
                            if isinstance(key_data.value, tuple):
                                key_obj.set_labels((key_data.value[1],) if len(
                                    key_data.value) > 1 else (key_data.value[0],))
                            else:
                                key_obj.set_labels((key_data.value,))
                
                # Generate SVG visualization
                try:
                    # Use our mock svgwrite to generate basic SVG
                    keyboard_svg = render_keyboard(
                        comparison_evaluator.keyboard,
                        layer_idx=layer_idx,
                        layout=comparison_evaluator.layout
                    )
                    
                    # Extract SVG content
                    if hasattr(keyboard_svg, 'data'):
                        svg_content = keyboard_svg.data
                    elif hasattr(keyboard_svg, '_repr_svg_'):
                        svg_content = keyboard_svg._repr_svg_()
                    else:
                        svg_content = str(keyboard_svg)
                    
                    # Save SVG file in both locations
                    layer_svg_path = predefined_dir / f"{layout_name}_layer_{layer_idx}.svg"
                    with open(layer_svg_path, 'w', encoding='utf-8') as f:
                        f.write(svg_content)
                    print(f"  Saved Layer {layer_idx} (GA run): {layer_svg_path}")
                    
                    # Also save to general comparison directory
                    general_layer_svg_path = layouts_dir / f"{layout_name}_layer_{layer_idx}.svg"
                    with open(general_layer_svg_path, 'w', encoding='utf-8') as f:
                        f.write(svg_content)
                    print(f"  Saved Layer {layer_idx} (general): {general_layer_svg_path}")
                    
                except Exception as svg_e:
                    print(f"  Error generating SVG: {svg_e}")
                    # Create a simple placeholder SVG
                    placeholder_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="200" fill="#f0f0f0"/>
  <text x="400" y="100" text-anchor="middle" font-family="monospace" font-size="16">
    SVG generation failed for {layout_name}
  </text>
</svg>'''
                    
                    layer_svg_path = predefined_dir / f"{layout_name}_layer_{layer_idx}.svg"
                    with open(layer_svg_path, 'w', encoding='utf-8') as f:
                        f.write(placeholder_svg)
                    
                    general_layer_svg_path = layouts_dir / f"{layout_name}_layer_{layer_idx}.svg"
                    with open(general_layer_svg_path, 'w', encoding='utf-8') as f:
                        f.write(placeholder_svg)
                    
        except Exception as e:
            print(f"  Error generating SVG for {layout_name}: {e}")
        
        # Store data for summary
        predefined_layouts_data.append({
            'name': layout_name,
            'fitness': fitness,
            'distance': distance,
            'time': time_taken
        })
    
    print(f"\nSaved predefined layouts to {predefined_dir} and {layouts_dir}")
    print("="*80)
    
    # Save summary of predefined layouts
    summary_data = {
        "timestamp": timestamp,
        "keyboard_file": keyboard_file,
        "dataset_file": dataset_file,
        "dataset_name": dataset_name,
        "predefined_layouts": predefined_layouts_data
    }
    
    summary_path = predefined_dir / "predefined_layouts_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    print(f"Saved predefined layouts summary: {summary_path}")
    
    general_summary_path = layouts_dir / "predefined_layouts_summary.json"
    with open(general_summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    print(f"Saved general predefined layouts summary: {general_summary_path}")
    
    # Save discarded layouts (all except top 3)
    print("="*80)
    print("SAVING DISCARDED LAYOUTS")
    print("="*80)
    
    # Get all individuals except the top 3
    discarded_individuals = [ind for ind in ga.population if ind not in top_3_individuals]
    
    print(f"Processing {len(discarded_individuals)} discarded layouts...")
    
    discarded_layouts_data = []
    
    for i, individual in enumerate(discarded_individuals, 1):
        layout_name = individual.name
        file_name = f"discarded_{i}_{layout_name}"
        
        print(f"\nProcessing Discarded Layout {i}/{len(discarded_individuals)}: {layout_name}")
        print(f"Fitness: {individual.fitness:.6f}")
        
        # Get parent names
        parent_names = [ga.get_individual_name(p) for p in individual.parents] if individual.parents else []

        # Save JSON data
        json_data = {
            "timestamp": timestamp,
            "discarded_rank": i,
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
            "dataset_name": dataset_name,
            "type": "discarded"
        }

        json_path = discarded_dir / f"{file_name}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"  Saved JSON: {json_path}")
        
        # Store data for summary
        discarded_layouts_data.append({
            'discarded_rank': i,
            'name': layout_name,
            'fitness': individual.fitness,
            'generation': individual.generation
        })

        # Generate and save SVG for each layer
        try:
            # Apply the layout using remap method
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

                # Generate SVG visualization
                try:
                    keyboard_svg = render_keyboard(
                        ga.evaluator.keyboard,
                        layer_idx=layer_idx,
                        layout=ga.evaluator.layout
                    )

                    # Extract SVG content
                    if hasattr(keyboard_svg, 'data'):
                        svg_content = keyboard_svg.data
                    elif hasattr(keyboard_svg, '_repr_svg_'):
                        svg_content = keyboard_svg._repr_svg_()
                    else:
                        svg_content = str(keyboard_svg)

                    # Save SVG file
                    svg_path = discarded_dir / f"{file_name}_layer_{layer_idx}.svg"
                    with open(svg_path, 'w', encoding='utf-8') as f:
                        f.write(svg_content)
                    print(f"  Saved Layer {layer_idx}: {svg_path}")
                    
                except Exception as svg_e:
                    print(f"  Error generating SVG: {svg_e}")
                    # Create a simple placeholder SVG
                    placeholder_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="200" fill="#f0f0f0"/>
  <text x="400" y="100" text-anchor="middle" font-family="monospace" font-size="16">
    SVG generation failed for {layout_name} (Discarded)
  </text>
</svg>'''
                    
                    svg_path = discarded_dir / f"{file_name}_layer_{layer_idx}.svg"
                    with open(svg_path, 'w', encoding='utf-8') as f:
                        f.write(placeholder_svg)

        except Exception as e:
            print(f"  Error generating SVG: {e}")

    print(f"\nSaved {len(discarded_individuals)} discarded layouts to {discarded_dir}")
    print("="*80)
    
    # Save discarded layouts summary
    discarded_summary_data = {
        "timestamp": timestamp,
        "keyboard_file": keyboard_file,
        "dataset_file": dataset_file,
        "dataset_name": dataset_name,
        "total_discarded": len(discarded_individuals),
        "discarded_layouts": discarded_layouts_data[:10]  # Save first 10 for overview
    }
    
    discarded_summary_path = discarded_dir / "discarded_layouts_summary.json"
    with open(discarded_summary_path, 'w', encoding='utf-8') as f:
        json.dump(discarded_summary_data, f, indent=2, ensure_ascii=False)
    print(f"Saved discarded layouts summary: {discarded_summary_path}")

    return best_individual


if __name__ == "__main__":
    # Configuration
    CONFIG = {
        'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
        'dataset_file': 'src/data/text/processed/frequency_analysis.pkl',
        'dataset_name': 'newsgroup',  # Changed from simple_wikipedia to newsgroup
        'population_size': 30,  # Smaller for faster testing
        'max_iterations': 50,
        'stagnant_limit': 10
    }

    # Run GA
    best = run_genetic_algorithm(**CONFIG)

    print("\nTo use different parameters, modify the CONFIG dictionary or call:")
    print("run_genetic_algorithm(population_size=100, max_iterations=200, stagnant_limit=20)")
