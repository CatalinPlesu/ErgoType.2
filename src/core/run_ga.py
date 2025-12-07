"""
Updated run_ga.py - Using the clean visualization module
"""
from data.layouts.keyboard_genotypes import LAYOUT_DATA
from core.ga import GeneticAlgorithmSimulation
from core.map_json_exporter import CSharpFitnessConfig
from core.evaluator import Evaluator
from src.helpers.layouts.visualization import generate_all_visualizations
import sys
import os
from datetime import datetime
import json
from pathlib import Path

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def save_layout_visualizations(stats_json, keyboard, layout, run_dir, layout_name, layer_idx=0):
    """
    Generate and save all visualizations from C# ComputeStats output.
    """
    print(f"\n🎨 Generating visualizations for {layout_name}, Layer {layer_idx}...")
    
    try:
        # Generate all three visualizations in one call
        layout_svg, press_svg, hover_svg = generate_all_visualizations(
            stats_json=stats_json,
            keyboard=keyboard,
            layout=layout,
            layout_name=layout_name,
            layer_idx=layer_idx,
            save_dir=run_dir
        )
        
        print(f"✅ All visualizations saved successfully!")
        
        # Optional: Print efficiency analysis
        stats = json.loads(stats_json)
        char_mappings = stats.get('char_mappings', {})
        
        if char_mappings:
            print(f"\n📊 Efficiency Analysis:")
            
            # Calculate press/hover ratios
            comparison_data = []
            for char, char_data in char_mappings.items():
                press_count = char_data.get('press_count', 0)
                hover_count = char_data.get('hover_count', 0)
                
                if press_count > 0 and hover_count > 0:
                    ratio = press_count / hover_count
                    comparison_data.append((char, ratio))
            
            comparison_data.sort(key=lambda x: x[1], reverse=True)
            
            if len(comparison_data) >= 3:
                print(f"  Most efficient (high press/hover):")
                for char, ratio in comparison_data[:3]:
                    print(f"    '{char}': {ratio:.2f}x")
                
                print(f"  Least efficient (low press/hover):")
                for char, ratio in comparison_data[-3:]:
                    print(f"    '{char}': {ratio:.2f}x")
        
    except Exception as e:
        print(f"❌ Error generating visualizations: {e}")
        import traceback
        traceback.print_exc()


def save_heuristic_layouts(ga, run_dir):
    """
    Save visualizations for all initial heuristic layouts (QWERTY, Dvorak, Colemak, etc.)
    """
    print("\n" + "="*80)
    print("SAVING INITIAL HEURISTIC LAYOUTS")
    print("="*80)
    
    # Initialize C# for stats generation
    try:
        from pythonnet import set_runtime
        from clr_loader import get_coreclr
        set_runtime(get_coreclr())
        import clr
        
        dll_dir = os.path.join(PROJECT_ROOT, "cs", "bin", "Release", "net9.0")
        if dll_dir not in sys.path:
            sys.path.insert(0, dll_dir)
        clr.AddReference("KeyboardFitness")
        from FitnessNet import Fitness
    except Exception as e:
        print(f"❌ Error loading C# library: {e}")
        return
    
    for layout_name, genotype in LAYOUT_DATA.items():
        print(f"\n{'='*80}")
        print(f"Processing heuristic layout: {layout_name}")
        print(f"{'='*80}")
        
        try:
            # Remap to this heuristic layout
            ga.evaluator.layout.remap(LAYOUT_DATA["qwerty"], list(genotype))
            
            # Generate C# configuration
            config_gen = CSharpFitnessConfig(
                keyboard=ga.evaluator.keyboard,
                layout=ga.evaluator.layout
            )
            
            json_string = config_gen.generate_json_string(
                text_file_path=ga.text_file,
                finger_coefficients=ga.finger_coefficients,
                fitts_a=ga.fitts_a,
                fitts_b=ga.fitts_b
            )
            
            # Compute stats
            print(f"📊 Computing statistics...")
            fitness_calculator = Fitness(json_string)
            stats_json = fitness_calculator.ComputeStats()
            
            # Save stats JSON
            stats_path = run_dir / f"heuristic_{layout_name}_stats.json"
            with open(stats_path, 'w', encoding='utf-8') as f:
                f.write(stats_json)
            print(f"✅ Saved stats: {stats_path.name}")
            
            # Generate visualizations for layer 0
            save_layout_visualizations(
                stats_json=stats_json,
                keyboard=ga.evaluator.keyboard,
                layout=ga.evaluator.layout,
                run_dir=run_dir,
                layout_name=f"heuristic_{layout_name}",
                layer_idx=0
            )
            
        except Exception as e:
            print(f"❌ Error processing {layout_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print(f"✅ COMPLETE: Saved {len(LAYOUT_DATA)} heuristic layouts")
    print(f"{'='*80}")


def run_genetic_algorithm(
    keyboard_file='src/data/keyboards/ansi_60_percent.json',
    text_file='src/data/text/raw/simple_wikipedia_dataset.txt',
    fitts_a=0.5,
    fitts_b=0.3,
    finger_coefficients=None,
    population_size=50,
    max_iterations=100,
    stagnant_limit=15,
    max_concurrent_processes=4,
    save_heuristics=True  # NEW: Option to save initial layouts
):
    """
    Run the genetic algorithm with C# simulation
    """
    print("="*80)
    print("KEYBOARD LAYOUT GENETIC ALGORITHM (C# SIMULATION)")
    print("="*80)
    print(f"Keyboard: {keyboard_file}")
    print(f"Text file: {text_file}")
    print(f"Fitts's Law: a={fitts_a}, b={fitts_b}")
    print(f"Population size: {population_size}")
    print(f"Max iterations: {max_iterations}")
    print(f"Stagnation limit: {stagnant_limit}")
    print(f"Max processes: {max_concurrent_processes}")
    print(f"Save heuristics: {save_heuristics}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()

    # Initialize GA with simulation
    ga = GeneticAlgorithmSimulation(
        keyboard_file=keyboard_file,
        text_file=text_file,
        fitts_a=fitts_a,
        fitts_b=fitts_b,
        population_size=population_size,
        finger_coefficients=finger_coefficients,
        max_concurrent_processes=max_concurrent_processes
    )

    # Adjust population size if needed
    if len(ga.population) < population_size:
        ga.population_initialization(size=population_size)

    # Create output directory
    timestamp = datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
    output_dir = Path("output/ga_results")
    run_dir = output_dir / f"ga_run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Save heuristic layouts BEFORE running GA
    if save_heuristics:
        save_heuristic_layouts(ga, run_dir)

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
    print(f"Raw Distance: {best_individual.distance:.2f}")
    print(f"Raw Time: {best_individual.time_taken:.2f}")
    parent_names = [ga.get_individual_name(p) for p in best_individual.parents] if best_individual.parents else ['Initial Population']
    print(f"Parent Names: {', '.join(parent_names)}")
    print(f"\nOptimized Layout:")
    print(''.join(best_individual.chromosome))
    print()

    # Get the top 3 best individuals
    sorted_population = sorted(ga.population, key=lambda x: x.fitness if x.fitness is not None else float('inf'))
    top_3_individuals = sorted_population[:3]

    # Save GA run metadata
    ga_run_data = {
        "timestamp": timestamp,
        "keyboard_file": keyboard_file,
        "text_file": text_file,
        "fitts_a": fitts_a,
        "fitts_b": fitts_b,
        "finger_coefficients": finger_coefficients if finger_coefficients else [0.07, 0.06, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.06, 0.07],
        "population_size": population_size,
        "max_iterations": max_iterations,
        "stagnant_limit": stagnant_limit,
        "best_fitness": best_individual.fitness,
        "best_layout_name": best_individual.name,
        "best_layout": ''.join(best_individual.chromosome),
        "total_individuals_evaluated": len(ga.evaluated_individuals),
        "total_unique_individuals": len(ga.all_individuals)
    }

    ga_run_path = run_dir / "ga_run_metadata.json"
    with open(ga_run_path, 'w', encoding='utf-8') as f:
        json.dump(ga_run_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved GA run metadata: {ga_run_path}")

    # Save all unique individuals
    with open(run_dir / 'ga_all_individuals.json', 'w') as f:
        json.dump({
            'all_individuals': list(ga.all_individuals.values()),
            'best_individual': {
                'id': best_individual.id,
                'name': best_individual.name,
                'fitness': best_individual.fitness,
                'distance': best_individual.distance,
                'time_taken': best_individual.time_taken,
                'chromosome': ''.join(best_individual.chromosome),
                'generation': best_individual.generation,
                'parents': best_individual.parents
            }
        }, f, indent=2)
    print(f"✅ Saved all unique individuals to {run_dir / 'ga_all_individuals.json'}")

    # Save best 3 layouts with visualizations
    print("\n" + "="*80)
    print("GENERATING VISUALIZATIONS FOR TOP 3 OPTIMIZED LAYOUTS")
    print("="*80)

    # Attempt to initialize C# for stats generation
    # Note: If save_heuristics was True, the runtime might already be loaded by save_heuristic_layouts.
    # We try to load the types without explicitly setting the runtime again.
    try:
        # Attempt to load the reference and types without re-setting runtime
        # If the runtime was loaded previously, this should work.
        # If not, pythonnet might auto-load it on AddReference, though this is less reliable.
        import clr
        
        dll_dir = os.path.join(PROJECT_ROOT, "cs", "bin", "Release", "net9.0")
        dll_path = os.path.join(dll_dir, "KeyboardFitness.dll")
        
        if not os.path.exists(dll_path):
            print(f"❌ DLL not found at: {dll_path}")
            print("\n💡 To compile the C# library:")
            print("   cd cs")
            print("   dotnet build -c Release")
            print("\nSkipping visualization generation")
            return best_individual
        
        if dll_dir not in sys.path:
            sys.path.insert(0, dll_dir)
        
        clr.AddReference("KeyboardFitness")
        from FitnessNet import Fitness
        
        print(f"✅ C# fitness library components loaded/reused")
    except Exception as e:
        print(f"❌ Error loading C# library components for top 3 layouts: {e}")
        print("This often happens if the .NET runtime was already loaded in this Python session.")
        print("The core GA might still have run correctly.")
        # Depending on your needs, you might return early here, or continue if other parts are not critical.
        # For now, let's return to prevent further errors trying to use the Fitness class.
        return best_individual 

    for i, individual in enumerate(top_3_individuals, 1):
        layout_name = individual.name
        file_name = f"rank{i}_{layout_name}"
        
        print(f"\n{'='*80}")
        print(f"Processing Layout {i}: {layout_name}")
        print(f"{'='*80}")
        print(f"Fitness: {individual.fitness:.6f}")
        print(f"Distance: {individual.distance:.2f}")
        print(f"Time: {individual.time_taken:.2f}")
        print(f"Layout: {''.join(individual.chromosome)}")
        
        parent_names = [ga.get_individual_name(p) for p in individual.parents] if individual.parents else []

        json_data = {
            "timestamp": timestamp,
            "rank": i,
            "name": layout_name,
            "file_name": file_name,
            "fitness": individual.fitness,
            "distance": individual.distance,
            "time_taken": individual.time_taken,
            "chromosome": individual.chromosome,
            "parents": parent_names,
            "parent_ids": individual.parents,
            "generation": individual.generation,
            "layout_string": ''.join(individual.chromosome),
            "keyboard_file": keyboard_file,
            "text_file": text_file
        }

        json_path = run_dir / f"{file_name}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved JSON: {json_path.name}")

        try:
            ga.evaluator.layout.remap(LAYOUT_DATA["qwerty"], individual.chromosome)

            config_gen = CSharpFitnessConfig(
                keyboard=ga.evaluator.keyboard,
                layout=ga.evaluator.layout
            )

            json_string = config_gen.generate_json_string(
                text_file_path=os.path.join(PROJECT_ROOT, text_file) if not os.path.isabs(text_file) else text_file,
                finger_coefficients=ga.finger_coefficients,
                fitts_a=ga.fitts_a,
                fitts_b=ga.fitts_b
            )

            print(f"📊 Generating statistics...")
            fitness_calculator = Fitness(json_string) # This line should now work if the runtime is loaded
            stats_json = fitness_calculator.ComputeStats()
            
            stats_path = run_dir / f"{file_name}_stats.json"
            with open(stats_path, 'w', encoding='utf-8') as f:
                f.write(stats_json)
            print(f"✅ Saved Stats: {stats_path.name}")

            # Get all layers
            layers = []
            for key_id, layer_idx in ga.evaluator.layout.mapper.data.keys():
                if layer_idx not in layers:
                    layers.append(layer_idx)
            layers = sorted(layers) if layers else [0]

            # Generate visualizations for each layer
            for layer_idx in layers:
                save_layout_visualizations(
                    stats_json=stats_json,
                    keyboard=ga.evaluator.keyboard,
                    layout=ga.evaluator.layout,
                    run_dir=run_dir,
                    layout_name=file_name,
                    layer_idx=layer_idx
                )

        except Exception as e:
            import traceback
            print(f"❌ Error generating visualizations for {layout_name}: {e}")
            traceback.print_exc()

    print(f"\n{'='*80}")
    print(f"✅ COMPLETE: Saved {len(top_3_individuals)} optimized layouts with visualizations")
    print(f"📁 Output directory: {run_dir}")
    print(f"⏰ End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    return best_individual

# ... (rest of the code remains the same) ...


if __name__ == "__main__":
    # Configuration
    CONFIG = {
        'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
        'text_file': 'src/data/text/raw/simple_wikipedia_dataset.txt',
        'fitts_a': 0.5,
        'fitts_b': 0.3,
        'finger_coefficients': None,  # Use defaults
        'population_size': 30,
        'max_iterations': 50,
        'stagnant_limit': 10,
        'max_concurrent_processes': 4,
        'save_heuristics': True  # NEW: Save initial layouts
    }

    # Run GA
    best = run_genetic_algorithm(**CONFIG)

    print("\n" + "="*80)
    print("BEST INDIVIDUAL SUMMARY")
    print("="*80)
    print(f"Name: {best.name}")
    print(f"Fitness: {best.fitness:.6f}")
    print(f"Distance: {best.distance:.2f}")
    print(f"Time: {best.time_taken:.2f}")
    print(f"Layout: {''.join(best.chromosome)}")
    print("="*80)
    
    print("\n💡 To use different parameters, modify the CONFIG dictionary")
