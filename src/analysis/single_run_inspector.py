"""
Single Run Inspector

Interactive tool for browsing and analyzing a single GA run.
Allows viewing individual chromosomes and generating visualizations.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add src to import path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Analysis output directory
ANALYSIS_OUTPUT_DIR = Path("output/analysis")

from src.analysis.ga_run_loader import GARunLoader
from src.ui.rich_menu import console, print_header, print_success, print_error, print_info, print_warning
from src.ui.rich_menu import select_from_list, confirm_action, display_config
from rich.table import Table
from rich import box


class SingleRunInspector:
    """Inspects a single GA run interactively"""
    
    def __init__(self, run_dir: Path):
        """
        Initialize inspector for a GA run.
        
        Args:
            run_dir: Path to the ga_run_{timestamp} directory
        """
        self.loader = GARunLoader(run_dir)
        self.run_dir = Path(run_dir)
        
    def display_run_summary(self):
        """Display a summary of the GA run"""
        summary = self.loader.get_run_summary()
        
        print_header("GA Run Summary", str(self.run_dir.name))
        
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="yellow")
        
        table.add_row("Timestamp", summary['timestamp'])
        table.add_row("Keyboard", summary['keyboard_file'])
        table.add_row("Text File", summary['text_file'])
        table.add_row("Population Size", str(summary['population_size']))
        table.add_row("Max Iterations", str(summary['max_iterations']))
        table.add_row("Total Generations", str(summary['total_generations']))
        table.add_row("Total Individuals", str(summary['total_individuals']))
        table.add_row("Best Fitness", f"{summary['best_fitness']:.6f}")
        table.add_row("Best Layout", summary['best_layout_name'])
        
        console.print(table)
        console.print()
    
    def browse_generations(self):
        """Browse all generations and select one to view"""
        by_gen = self.loader.get_individuals_by_generation()
        
        if not by_gen:
            print_error("No generations found in this run")
            return
        
        # Create list of generations
        gen_list = []
        for gen_num in sorted(by_gen.keys()):
            individuals = by_gen[gen_num]
            count = len(individuals)
            best_fitness = min(ind.get('fitness', float('inf')) for ind in individuals)
            gen_list.append((f"Generation {gen_num} ({count} individuals, best: {best_fitness:.6f})", gen_num))
        
        console.print("[bold]Select a generation to view:[/bold]\n")
        result = select_from_list("Available Generations", gen_list)
        
        if result is None:
            print_warning("Cancelled")
            return
        
        _, gen_num = result
        self.browse_individuals(gen_num, by_gen[gen_num])
    
    def browse_individuals(self, gen_num: int, individuals: List[Dict[str, Any]]):
        """
        Browse individuals in a generation.
        
        Args:
            gen_num: Generation number
            individuals: List of individuals in this generation
        """
        # Sort by fitness
        sorted_individuals = sorted(individuals, key=lambda x: x.get('fitness', float('inf')))
        
        # Create list for selection
        ind_list = []
        for idx, ind in enumerate(sorted_individuals, 1):
            name = ind.get('name', f"Unknown-{idx}")
            fitness = ind.get('fitness', float('inf'))
            ind_list.append((f"#{idx}: {name} (fitness: {fitness:.6f})", ind))
        
        console.print(f"\n[bold]Generation {gen_num} - Select an individual:[/bold]\n")
        result = select_from_list(f"Individuals in Generation {gen_num}", ind_list)
        
        if result is None:
            print_warning("Cancelled")
            return
        
        _, individual = result
        self.display_individual_details(individual)
    
    def display_individual_details(self, individual: Dict[str, Any]):
        """
        Display full details of an individual.
        
        Args:
            individual: Individual data dictionary
        """
        print_header("Individual Details", individual.get('name', 'Unknown'))
        
        # Basic info table
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="yellow")
        
        table.add_row("Name", individual.get('name', 'N/A'))
        table.add_row("Generation", str(individual.get('generation', 'N/A')))
        table.add_row("Fitness", f"{individual.get('fitness', float('inf')):.6f}")
        table.add_row("Distance", f"{individual.get('distance', 0):.2f}")
        table.add_row("Time", f"{individual.get('time', 0):.2f}")
        
        parents = individual.get('parents', [])
        if parents:
            table.add_row("Parents", ', '.join(str(p) for p in parents))
        
        console.print(table)
        console.print()
        
        # Layout visualization
        chromosome = individual.get('chromosome', [])
        if chromosome:
            console.print("[bold]Layout (chromosome):[/bold]")
            if isinstance(chromosome, list):
                layout_str = ''.join(chromosome)
            else:
                layout_str = str(chromosome)
            console.print(f"[green]{layout_str}[/green]")
            console.print()
        
        # Ask if user wants to generate visualizations
        if confirm_action("Generate and save SVG heatmaps for this layout?", default=False):
            self.generate_individual_visualizations(individual)
    
    def generate_individual_visualizations(self, individual: Dict[str, Any]):
        """
        Generate and save SVG heatmaps for an individual.
        
        Args:
            individual: Individual data dictionary
        """
        print_info("Generating visualizations...")
        
        try:
            # Get metadata for configuration
            metadata = self.loader.load_metadata()
            
            # Import required modules
            from src.core.evaluator import Evaluator
            from src.core.map_json_exporter import CSharpFitnessConfig
            from src.core.clr_loader_helper import load_csharp_fitness_library
            from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
            from src.helpers.layouts.visualization import generate_all_visualizations
            
            # Get project root
            PROJECT_ROOT = Path(__file__).parent.parent.parent
            
            # Load C# library
            Fitness, _ = load_csharp_fitness_library(PROJECT_ROOT)
            
            # Create evaluator
            evaluator = Evaluator(debug=False)
            evaluator.load_keyoard(metadata['keyboard_file'])
            evaluator.load_layout()
            
            # Get chromosome
            chromosome = individual.get('chromosome', [])
            if isinstance(chromosome, str):
                chromosome = list(chromosome)
            
            # Remap layout
            evaluator.layout.remap(list(LAYOUT_DATA["qwerty"]), chromosome)
            
            # Generate config
            config_gen = CSharpFitnessConfig(
                keyboard=evaluator.keyboard,
                layout=evaluator.layout
            )
            
            json_string = config_gen.generate_json_string(
                text_file_path=str(PROJECT_ROOT / metadata['text_file']) if not os.path.isabs(metadata['text_file']) else metadata['text_file'],
                finger_coefficients=metadata.get('finger_coefficients'),
                fitts_a=metadata.get('fitts_a', 0.5),
                fitts_b=metadata.get('fitts_b', 0.3)
            )
            
            # Compute stats
            fitness_calculator = Fitness(json_string)
            stats_json = fitness_calculator.ComputeStats()
            
            # Create output directory
            ind_name = individual.get('name', 'unknown')
            gen = individual.get('generation', 0)
            ind_id = individual.get('id', 0)
            
            output_dir = ANALYSIS_OUTPUT_DIR / self.run_dir.name / "cherry_picked" / f"gen_{gen}_chr_{ind_id}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save stats
            stats_path = output_dir / f"{ind_name}_stats.json"
            with open(stats_path, 'w', encoding='utf-8') as f:
                f.write(stats_json)
            print_success(f"Saved stats: {stats_path}")
            
            # Generate visualizations for each layer
            layers = []
            for key_id, layer_idx in evaluator.layout.mapper.data.keys():
                if layer_idx not in layers:
                    layers.append(layer_idx)
            layers = sorted(layers) if layers else [0]
            
            for layer_idx in layers:
                layout_svg, press_svg, hover_svg = generate_all_visualizations(
                    stats_json=stats_json,
                    keyboard=evaluator.keyboard,
                    layout=evaluator.layout,
                    layout_name=ind_name,
                    layer_idx=layer_idx,
                    save_dir=output_dir
                )
            
            print_success(f"✅ All visualizations saved to: {output_dir}")
            console.print()
            
        except Exception as e:
            print_error(f"Error generating visualizations: {e}")
            import traceback
            traceback.print_exc()


def run_single_run_inspector():
    """Main entry point for single run inspector"""
    print_header("Single GA Run Inspector", "Browse generations and chromosomes")
    
    # Find available GA runs
    runs = GARunLoader.find_ga_runs()
    
    if not runs:
        print_error("No GA runs found in output/ga_results/")
        print_info("Run the genetic algorithm first to generate data")
        return
    
    # Create selection list with detailed information
    run_list = []
    for run_dir in runs:
        try:
            loader = GARunLoader(run_dir)
            summary = loader.get_run_summary()
            name = (f"{run_dir.name} | "
                   f"Pop:{summary['population_size']} "
                   f"Iter:{summary['max_iterations']} "
                   f"Inds:{summary['total_individuals']} | "
                   f"Best:{summary['best_fitness']:.6f}")
            run_list.append((name, run_dir))
        except Exception as e:
            # Skip runs that can't be loaded
            console.print(f"[dim]Warning: Could not load {run_dir.name}: {e}[/dim]")
    
    if not run_list:
        print_error("No valid GA runs found")
        return
    
    console.print("[bold]Select a GA run to inspect:[/bold]\n")
    result = select_from_list("Available GA Runs", run_list)
    
    if result is None:
        print_warning("Cancelled")
        return
    
    _, run_dir = result
    
    # Create inspector
    inspector = SingleRunInspector(run_dir)
    
    # Display summary
    inspector.display_run_summary()
    console.print()
    
    # Browse generations
    inspector.browse_generations()
