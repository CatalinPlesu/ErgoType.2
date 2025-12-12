from data.layouts.keyboard_genotypes import LAYOUT_DATA
from core.ga import GeneticAlgorithmSimulation
from core.map_json_exporter import CSharpFitnessConfig
from core.evaluator import Evaluator
from core.layout import Layout
from src.helpers.layouts.visualization import generate_all_visualizations
import sys
import os
from datetime import datetime
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def save_layout_visualizations(stats_json, keyboard, layout, run_dir, layout_name, layer_idx=0):
    """Generate and save all visualizations from C# ComputeStats output."""
    print(f"\n🎨 Generating visualizations for {layout_name}, Layer {layer_idx}...")
    
    try:
        layout_svg, press_svg, hover_svg = generate_all_visualizations(
            stats_json=stats_json,
            keyboard=keyboard,
            layout=layout,
            layout_name=layout_name,
            layer_idx=layer_idx,
            save_dir=run_dir
        )
        
        print(f"✅ All visualizations saved successfully!")
        
        stats = json.loads(stats_json)
        char_mappings = stats.get('char_mappings', {})
        
        if char_mappings:
            print(f"\n📊 Efficiency Analysis:")
            
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
    Ensure heuristic layouts (QWERTY, Dvorak, Colemak, etc.) are cached.
    Generates and caches any missing heuristics, but does not copy them to the GA run directory.
    Users can access cached heuristics in output/{dataset}/{keyboard}/ directories.
    """
    from helpers.layouts.heuristic_generator import (
        check_heuristic_cached, get_dataset_name, get_keyboard_name
    )
    
    print("\n" + "="*80)
    print("ENSURING HEURISTIC LAYOUTS ARE CACHED")
    print("="*80)
    
    dataset_name = get_dataset_name(ga.text_file)
    keyboard_name = get_keyboard_name(ga.keyboard_file)
    
    print(f"Dataset: {dataset_name}")
    print(f"Keyboard: {keyboard_name}")
    print(f"Checking cache...")
    
    # Count cached vs. need to generate
    cached_count = 0
    need_generate = []
    
    for layout_name in LAYOUT_DATA.keys():
        if check_heuristic_cached(dataset_name, keyboard_name, layout_name):
            cached_count += 1
        else:
            need_generate.append(layout_name)
    
    print(f"Cached: {cached_count}/{len(LAYOUT_DATA)}")
    print(f"Need to generate: {len(need_generate)}")
    
    # Generate missing heuristics and cache them
    if need_generate:
        print(f"\n🔧 Generating and caching {len(need_generate)} missing heuristics...")
        
        for layout_name in need_generate:
            genotype = LAYOUT_DATA[layout_name]
            print(f"\n{'='*80}")
            print(f"Caching heuristic layout: {layout_name}")
            print(f"{'='*80}")
           
            try:
                # Generate and cache the heuristic layout
                from helpers.layouts.heuristic_generator import generate_heuristic_layout
                success, message = generate_heuristic_layout(
                    layout_name=layout_name,
                    genotype=genotype,
                    keyboard_file=ga.keyboard_file,
                    text_file=ga.text_file,
                    fitts_a=ga.fitts_a,
                    fitts_b=ga.fitts_b,
                    finger_coefficients=ga.finger_coefficients,
                    force_regenerate=False
                )
                
                if success:
                    print(f"✅ {message}")
                else:
                    print(f"❌ {message}")
                
            except Exception as e:
                print(f"❌ Error processing {layout_name}: {e}")
                import traceback
                traceback.print_exc()
    
    print(f"\n{'='*80}")
    print(f"✅ COMPLETE: Heuristic layouts cached")
    print(f"  - Already cached: {cached_count}")
    print(f"  - Newly generated: {len(need_generate)}")
    print(f"  - Cache location: output/{dataset_name}/{keyboard_name}/")
    print(f"{'='*80}")


def save_fitness_evolution_plot(ga, run_dir):
    """Save matplotlib plot showing how fitness improves over generations"""
    print("\n📊 Generating fitness evolution plot...")
    
    try:
        if isinstance(ga.all_individuals, dict):
            individuals_list = list(ga.all_individuals.values())
        elif isinstance(ga.all_individuals, list):
            individuals_list = ga.all_individuals
        else:
            print(f"❌ Unexpected type for ga.all_individuals: {type(ga.all_individuals)}")
            return
        
        print(f"Total individuals to process: {len(individuals_list)}")
        
        if not individuals_list:
            print("❌ No individuals found to plot")
            return
        
        generation_fitness_data = {}
        
        for individual in individuals_list:
            if isinstance(individual, dict):
                gen = individual.get('generation')
                fitness = individual.get('fitness')
            else:
                if not hasattr(individual, 'generation') or not hasattr(individual, 'fitness'):
                    print(f"⚠️ Individual missing required attributes")
                    continue
                gen = individual.generation
                fitness = individual.fitness
            
            if gen is not None and fitness is not None:
                if gen not in generation_fitness_data:
                    generation_fitness_data[gen] = []
                generation_fitness_data[gen].append(fitness)
            else:
                print(f"⚠️ Individual has None generation or fitness: gen={gen}, fitness={fitness}")
        
        if not generation_fitness_data:
            print("❌ No valid generation data found")
            return
        
        print(f"Found generations: {sorted(generation_fitness_data.keys())}")
        for gen, fitnesses in generation_fitness_data.items():
            print(f"Generation {gen}: {len(fitnesses)} individuals")
        
        generations = sorted(generation_fitness_data.keys())
        avg_fitness_per_gen = []
        min_fitness_per_gen = []
        max_fitness_per_gen = []
        p25_fitness_per_gen = []
        p50_fitness_per_gen = []
        p75_fitness_per_gen = []
        
        for gen in generations:
            fitness_values = generation_fitness_data[gen]
            if fitness_values:
                avg_fitness_per_gen.append(np.mean(fitness_values))
                min_fitness_per_gen.append(min(fitness_values))
                max_fitness_per_gen.append(max(fitness_values))
                p25_fitness_per_gen.append(np.percentile(fitness_values, 25))
                p50_fitness_per_gen.append(np.percentile(fitness_values, 50))
                p75_fitness_per_gen.append(np.percentile(fitness_values, 75))
        
        if not generations:
            print("❌ No valid generations to plot")
            return
        
        plt.figure(figsize=(14, 10))
        
        plt.plot(generations, avg_fitness_per_gen, 'b-', label='Average Fitness', linewidth=2)
        plt.plot(generations, p25_fitness_per_gen, 'g--', label='25th Percentile', linewidth=1.5)
        plt.plot(generations, p50_fitness_per_gen, 'orange', label='Median (50th Percentile)', linewidth=1.5)
        plt.plot(generations, p75_fitness_per_gen, 'r--', label='75th Percentile', linewidth=1.5)
        plt.plot(generations, min_fitness_per_gen, 'k:', label='Best Fitness', linewidth=1.5)
        plt.plot(generations, max_fitness_per_gen, 'k:', label='Worst Fitness', linewidth=1.5, linestyle=':')
        
        plt.fill_between(generations, p25_fitness_per_gen, p75_fitness_per_gen, alpha=0.2, color='gray', label='25th-75th Percentile Range')
        
        plt.xlabel('Generation', fontsize=12)
        plt.ylabel('Fitness Score', fontsize=12)
        plt.title('Fitness Evolution Over Generations\n(Showing Percentiles and Range)', fontsize=14)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plot_path = run_dir / 'fitness_evolution.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Fitness evolution plot saved: {plot_path}")
        
    except Exception as e:
        print(f"❌ Error generating fitness evolution plot: {e}")
        import traceback
        traceback.print_exc()


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
    use_rabbitmq=True,
    save_heuristics=True
):
    """Run the genetic algorithm with C# simulation and distributed processing"""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich import box
        console = Console()
        use_rich = True
    except ImportError:
        use_rich = False
    
    if use_rich:
        console.rule("[bold cyan]KEYBOARD LAYOUT GENETIC ALGORITHM[/bold cyan]", style="cyan")
        console.print("[dim]Distributed C# Simulation[/dim]", justify="center")
        console.print()
        
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        table.add_column("Parameter", style="cyan")
        table.add_column("Value", style="yellow")
        table.add_row("Keyboard", keyboard_file)
        table.add_row("Text file", text_file)
        table.add_row("Fitts's Law", f"a={fitts_a}, b={fitts_b}")
        table.add_row("Population size", str(population_size))
        table.add_row("Max iterations", str(max_iterations))
        table.add_row("Stagnation limit", str(stagnant_limit))
        table.add_row("Max processes", str(max_concurrent_processes))
        table.add_row("Use RabbitMQ", str(use_rabbitmq))
        table.add_row("Save heuristics", str(save_heuristics))
        table.add_row("Start time", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        console.print(table)
        console.print()
    else:
        print("="*80)
        print("KEYBOARD LAYOUT GENETIC ALGORITHM (DISTRIBUTED C# SIMULATION)")
        print("="*80)
        print(f"Keyboard: {keyboard_file}")
        print(f"Text file: {text_file}")
        print(f"Fitts's Law: a={fitts_a}, b={fitts_b}")
        print(f"Population size: {population_size}")
        print(f"Max iterations: {max_iterations}")
        print(f"Stagnation limit: {stagnant_limit}")
        print(f"Max processes: {max_concurrent_processes}")
        print(f"Use RabbitMQ: {use_rabbitmq}")
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
        max_concurrent_processes=max_concurrent_processes,
        use_rabbitmq=use_rabbitmq,
        is_worker=False  # Master mode
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
    if use_rich:
        console.print()
        console.rule("[bold green]OPTIMIZATION COMPLETE[/bold green]", style="green")
        console.print()
        
        result_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        result_table.add_column("Metric", style="cyan")
        result_table.add_column("Value", style="yellow")
        result_table.add_row("Best Individual", best_individual.name)
        result_table.add_row("Fitness Score", f"{best_individual.fitness:.6f}")
        result_table.add_row("Raw Distance", f"{best_individual.distance:.2f}")
        result_table.add_row("Raw Time", f"{best_individual.time_taken:.2f}")
        parent_names = [ga.get_individual_name(p) for p in best_individual.parents] if best_individual.parents else ['Initial Population']
        result_table.add_row("Parents", ', '.join(parent_names))
        console.print(result_table)
        console.print()
        console.print("[bold]Optimized Layout:[/bold]")
        console.print(f"[green]{''.join(best_individual.chromosome)}[/green]")
        console.print()
    else:
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
        "use_rabbitmq": use_rabbitmq,
        "best_fitness": best_individual.fitness,
        "best_layout_name": best_individual.name,
        "best_layout": ''.join(best_individual.chromosome),
        "total_individuals_evaluated": len(ga.evaluated_individuals),
        "total_unique_individuals": len(ga.all_individuals)
    }
    
    # Add timing statistics from progress tracker if available
    progress_tracker = getattr(ga, 'progress_tracker', None)
    if progress_tracker:
        total_time = progress_tracker.get_total_elapsed_time()
        avg_job_time = progress_tracker.get_average_job_time()
        
        ga_run_data["total_run_time_seconds"] = round(total_time, 2)
        if avg_job_time is not None:
            ga_run_data["average_job_time_seconds"] = round(avg_job_time, 4)

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

    # Save fitness evolution plot
    save_fitness_evolution_plot(ga, run_dir)

    # Save best 3 layouts with visualizations
    print("\n" + "="*80)
    print("GENERATING VISUALIZATIONS FOR TOP 3 OPTIMIZED LAYOUTS")
    print("="*80)

    try:
        dll_dir = os.path.join(PROJECT_ROOT, "cs", "bin", "Release", "net9.0")
        dll_path = os.path.join(dll_dir, "KeyboardFitness.dll")
        
        if not os.path.exists(dll_path):
            print(f"❌ DLL not found at: {dll_path}")
            print("\n💡 To compile the C# library:")
            print("   cd cs")
            print("   dotnet build -c Release")
            print("\nSkipping visualization generation")
            return best_individual
        
        from core.clr_loader_helper import load_csharp_fitness_library
        Fitness, _ = load_csharp_fitness_library(PROJECT_ROOT)
        
        print(f"✅ C# fitness library components loaded/reused")
    except Exception as e:
        print(f"❌ Error loading C# library components for top 3 layouts: {e}")
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
            # Create separate evaluator for this individual
            evaluator = Evaluator(debug=False)
            evaluator.load_keyoard(ga.keyboard_file)
            evaluator.load_layout()
            evaluator.layout.remap(LAYOUT_DATA["qwerty"], individual.chromosome)

            config_gen = CSharpFitnessConfig(
                keyboard=evaluator.keyboard,
                layout=evaluator.layout
            )

            json_string = config_gen.generate_json_string(
                text_file_path=os.path.join(PROJECT_ROOT, text_file) if not os.path.isabs(text_file) else text_file,
                finger_coefficients=ga.finger_coefficients,
                fitts_a=ga.fitts_a,
                fitts_b=ga.fitts_b
            )

            print(f"📊 Generating statistics...")
            fitness_calculator = Fitness(json_string)
            stats_json = fitness_calculator.ComputeStats()
            
            stats_path = run_dir / f"{file_name}_stats.json"
            with open(stats_path, 'w', encoding='utf-8') as f:
                f.write(stats_json)
            print(f"✅ Saved Stats: {stats_path.name}")

            layers = []
            for key_id, layer_idx in evaluator.layout.mapper.data.keys():
                if layer_idx not in layers:
                    layers.append(layer_idx)
            layers = sorted(layers) if layers else [0]

            for layer_idx in layers:
                save_layout_visualizations(
                    stats_json=stats_json,
                    keyboard=evaluator.keyboard,
                    layout=evaluator.layout,
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


if __name__ == "__main__":
    CONFIG = {
        'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
        'text_file': 'src/data/text/raw/simple_wikipedia_dataset.txt',
        'fitts_a': 0.5,
        'fitts_b': 0.3,
        'finger_coefficients': None,
        'population_size': 30,
        'max_iterations': 50,
        'stagnant_limit': 10,
        'max_concurrent_processes': 4,
        'use_rabbitmq': True,
        'save_heuristics': True
    }

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
