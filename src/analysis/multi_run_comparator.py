"""
Multi-Run Comparator

Compares multiple GA runs to analyze parameter impact and generate
comparison visualizations.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np

# Add src to import path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Analysis output directory
ANALYSIS_OUTPUT_DIR = Path("output/analysis")

from src.analysis.ga_run_loader import GARunLoader
from src.ui.rich_menu import console, print_header, print_success, print_error, print_info, print_warning
from src.ui.rich_menu import confirm_action
from rich.table import Table
from rich import box
from rich.prompt import Prompt


class MultiRunComparator:
    """Compares multiple GA runs"""
    
    def __init__(self, run_dirs: List[Path]):
        """
        Initialize comparator with multiple GA runs.
        
        Args:
            run_dirs: List of paths to ga_run_{timestamp} directories
        """
        self.run_dirs = [Path(d) for d in run_dirs]
        self.loaders = [GARunLoader(d) for d in self.run_dirs]
        self.summaries = []
        
        # Load all summaries
        for loader in self.loaders:
            try:
                self.summaries.append(loader.get_run_summary())
            except Exception as e:
                print_warning(f"Could not load run {loader.run_dir.name}: {e}")
    
    def display_comparison_summary(self):
        """Display a comparison table of all runs"""
        print_header("Multi-Run Comparison", f"{len(self.summaries)} runs selected")
        
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("#", style="cyan", justify="right", width=3)
        table.add_column("Run", style="white")
        table.add_column("Pop Size", justify="right", style="yellow")
        table.add_column("Max Iter", justify="right", style="yellow")
        table.add_column("Gens", justify="right", style="yellow")
        table.add_column("Best Fitness", justify="right", style="green")
        table.add_column("Total Inds", justify="right", style="cyan")
        
        for idx, summary in enumerate(self.summaries, 1):
            run_name = Path(summary['run_dir']).name
            table.add_row(
                str(idx),
                run_name,
                str(summary['population_size']),
                str(summary['max_iterations']),
                str(summary['total_generations']),
                f"{summary['best_fitness']:.6f}",
                str(summary['total_individuals'])
            )
        
        console.print(table)
        console.print()
    
    def re_normalize_fitness_across_runs(self) -> List[Dict[str, Any]]:
        """
        Re-normalize all fitness values across all runs for fair comparison.
        
        Returns:
            List of all individuals with re-normalized fitness
        """
        print_info("Re-normalizing fitness across all runs...")
        
        all_individuals = []
        
        # Collect all individuals from all runs
        for loader in self.loaders:
            try:
                individuals_data = loader.load_all_individuals()
                for ind in individuals_data.get('all_individuals', []):
                    ind['run_dir'] = str(loader.run_dir)
                    all_individuals.append(ind)
            except Exception as e:
                print_warning(f"Could not load individuals from {loader.run_dir.name}: {e}")
        
        if not all_individuals:
            print_error("No individuals found across all runs")
            return []
        
        # Find global min/max for distance and time
        distances = [ind.get('distance', float('inf')) for ind in all_individuals 
                    if ind.get('distance') is not None and ind.get('distance') != float('inf')]
        times = [ind.get('time', float('inf')) for ind in all_individuals 
                if ind.get('time') is not None and ind.get('time') != float('inf')]
        
        if not distances or not times:
            print_error("No valid fitness values found")
            return all_individuals
        
        min_distance = min(distances)
        max_distance = max(distances)
        min_time = min(times)
        max_time = max(times)
        
        # Re-normalize each individual
        for ind in all_individuals:
            distance = ind.get('distance')
            time = ind.get('time')
            
            if distance is not None and distance != float('inf') and max_distance > min_distance:
                norm_distance = (distance - min_distance) / (max_distance - min_distance)
            else:
                norm_distance = 1.0
            
            if time is not None and time != float('inf') and max_time > min_time:
                norm_time = (time - min_time) / (max_time - min_time)
            else:
                norm_time = 1.0
            
            # Calculate normalized fitness (average of normalized distance and time)
            ind['normalized_fitness'] = (norm_distance + norm_time) / 2
        
        print_success(f"Re-normalized {len(all_individuals)} individuals across {len(self.loaders)} runs")
        return all_individuals
    
    def analyze_parameter_impact(self) -> Dict[str, Any]:
        """
        Analyze the impact of different parameters on results.
        
        Returns:
            Dictionary with analysis results
        """
        print_info("Analyzing parameter impact...")
        
        analysis = {
            'population_size_vs_fitness': [],
            'iterations_vs_fitness': [],
            'generations_vs_fitness': [],
            'runtime_data': []
        }
        
        for summary in self.summaries:
            analysis['population_size_vs_fitness'].append({
                'population_size': summary['population_size'],
                'best_fitness': summary['best_fitness']
            })
            
            analysis['iterations_vs_fitness'].append({
                'max_iterations': summary['max_iterations'],
                'actual_generations': summary['total_generations'],
                'best_fitness': summary['best_fitness']
            })
            
            analysis['generations_vs_fitness'].append({
                'generations': summary['total_generations'],
                'best_fitness': summary['best_fitness']
            })
            
            # Runtime data (if available)
            analysis['runtime_data'].append({
                'total_individuals': summary['total_individuals'],
                'best_fitness': summary['best_fitness']
            })
        
        return analysis
    
    def generate_comparison_visualizations(self, output_dir: Path, normalized_individuals: List[Dict[str, Any]]):
        """
        Generate comparison visualizations.
        
        Args:
            output_dir: Directory to save visualizations
            normalized_individuals: List of individuals with normalized fitness
        """
        print_info("Generating comparison visualizations...")
        
        try:
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            import matplotlib.pyplot as plt
            
            # 1. Fitness progression overlay chart
            self._generate_fitness_progression_chart(output_dir, normalized_individuals)
            
            # 2. Parameter correlation plots
            self._generate_parameter_correlation_plots(output_dir)
            
            # 3. Statistical summary
            self._generate_statistical_summary(output_dir, normalized_individuals)
            
            print_success(f"All visualizations saved to: {output_dir}")
            
        except Exception as e:
            print_error(f"Error generating visualizations: {e}")
            import traceback
            traceback.print_exc()
    
    def _generate_fitness_progression_chart(self, output_dir: Path, normalized_individuals: List[Dict[str, Any]]):
        """Generate fitness progression overlay chart"""
        import matplotlib.pyplot as plt
        
        # Group by run and generation
        run_data = {}
        for ind in normalized_individuals:
            run_dir = ind.get('run_dir', 'unknown')
            gen = ind.get('generation', 0)
            fitness = ind.get('normalized_fitness', 1.0)
            
            if run_dir not in run_data:
                run_data[run_dir] = {}
            if gen not in run_data[run_dir]:
                run_data[run_dir][gen] = []
            run_data[run_dir][gen].append(fitness)
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for run_dir, gen_data in run_data.items():
            generations = sorted(gen_data.keys())
            best_fitness = [min(gen_data[g]) for g in generations]
            avg_fitness = [np.mean(gen_data[g]) for g in generations]
            
            run_name = Path(run_dir).name
            ax.plot(generations, best_fitness, marker='o', label=f"{run_name} (best)", alpha=0.7)
            ax.plot(generations, avg_fitness, marker='s', linestyle='--', label=f"{run_name} (avg)", alpha=0.5)
        
        ax.set_xlabel('Generation')
        ax.set_ylabel('Normalized Fitness (lower is better)')
        ax.set_title('Fitness Progression Across Multiple Runs')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'fitness_progression.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        print_success("✓ Generated fitness_progression.png")
    
    def _generate_parameter_correlation_plots(self, output_dir: Path):
        """Generate parameter correlation scatter plots"""
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. Population size vs best fitness
        pop_sizes = [s['population_size'] for s in self.summaries]
        best_fitness = [s['best_fitness'] for s in self.summaries]
        axes[0, 0].scatter(pop_sizes, best_fitness, alpha=0.7, s=100)
        axes[0, 0].set_xlabel('Population Size')
        axes[0, 0].set_ylabel('Best Fitness')
        axes[0, 0].set_title('Population Size vs Best Fitness')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Max iterations vs generations achieved
        max_iters = [s['max_iterations'] for s in self.summaries]
        actual_gens = [s['total_generations'] for s in self.summaries]
        axes[0, 1].scatter(max_iters, actual_gens, alpha=0.7, s=100, c=best_fitness, cmap='viridis')
        axes[0, 1].set_xlabel('Max Iterations')
        axes[0, 1].set_ylabel('Actual Generations')
        axes[0, 1].set_title('Convergence Analysis')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Generations vs best fitness
        axes[1, 0].scatter(actual_gens, best_fitness, alpha=0.7, s=100)
        axes[1, 0].set_xlabel('Total Generations')
        axes[1, 0].set_ylabel('Best Fitness')
        axes[1, 0].set_title('Generations vs Best Fitness')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Total individuals vs best fitness
        total_inds = [s['total_individuals'] for s in self.summaries]
        axes[1, 1].scatter(total_inds, best_fitness, alpha=0.7, s=100)
        axes[1, 1].set_xlabel('Total Individuals Evaluated')
        axes[1, 1].set_ylabel('Best Fitness')
        axes[1, 1].set_title('Search Space Coverage vs Quality')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'parameter_correlations.png', dpi=150)
        plt.close()
        
        print_success("✓ Generated parameter_correlations.png")
    
    def _generate_statistical_summary(self, output_dir: Path, normalized_individuals: List[Dict[str, Any]]):
        """Generate statistical summary table and export as CSV/JSON"""
        
        # Calculate statistics per run
        stats = []
        for loader, summary in zip(self.loaders, self.summaries):
            run_individuals = [ind for ind in normalized_individuals 
                             if ind.get('run_dir') == str(loader.run_dir)]
            
            if run_individuals:
                fitness_values = [ind.get('normalized_fitness', 1.0) for ind in run_individuals]
                
                stats.append({
                    'run_name': Path(summary['run_dir']).name,
                    'population_size': summary['population_size'],
                    'max_iterations': summary['max_iterations'],
                    'actual_generations': summary['total_generations'],
                    'total_individuals': summary['total_individuals'],
                    'best_fitness': summary['best_fitness'],
                    'best_normalized_fitness': min(fitness_values),
                    'avg_normalized_fitness': np.mean(fitness_values),
                    'std_normalized_fitness': np.std(fitness_values),
                    'convergence_rate': summary['total_generations'] / summary['max_iterations']
                })
        
        # Save as JSON
        with open(output_dir / 'comparison_summary.json', 'w') as f:
            json.dump(stats, f, indent=2)
        print_success("✓ Generated comparison_summary.json")
        
        # Save as CSV
        try:
            import pandas as pd
            df = pd.DataFrame(stats)
            df.to_csv(output_dir / 'comparison_summary.csv', index=False)
            print_success("✓ Generated comparison_summary.csv")
        except ImportError:
            print_warning("pandas not available, skipping CSV export")
        
        # Generate markdown report
        self._generate_markdown_report(output_dir, stats)
    
    def _generate_markdown_report(self, output_dir: Path, stats: List[Dict[str, Any]]):
        """Generate a markdown analysis report"""
        
        report_lines = [
            "# Multi-Run GA Analysis Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Runs Analyzed:** {len(stats)}",
            "",
            "## Summary Statistics",
            "",
            "| Run | Pop Size | Max Iter | Gens | Total Inds | Best Fitness | Avg Norm Fitness | Convergence Rate |",
            "|-----|----------|----------|------|------------|--------------|------------------|------------------|"
        ]
        
        for s in stats:
            report_lines.append(
                f"| {s['run_name']} | {s['population_size']} | {s['max_iterations']} | "
                f"{s['actual_generations']} | {s['total_individuals']} | {s['best_fitness']:.6f} | "
                f"{s['avg_normalized_fitness']:.6f} | {s['convergence_rate']:.2%} |"
            )
        
        report_lines.extend([
            "",
            "## Key Findings",
            "",
            "### Best Performing Run",
            ""
        ])
        
        best_run = min(stats, key=lambda x: x['best_fitness'])
        report_lines.extend([
            f"- **Run:** {best_run['run_name']}",
            f"- **Best Fitness:** {best_run['best_fitness']:.6f}",
            f"- **Population Size:** {best_run['population_size']}",
            f"- **Generations:** {best_run['actual_generations']}",
            "",
            "### Parameter Impact Analysis",
            "",
            "#### Population Size",
            f"- Range: {min(s['population_size'] for s in stats)} to {max(s['population_size'] for s in stats)}",
            "",
            "#### Convergence",
            f"- Average convergence rate: {np.mean([s['convergence_rate'] for s in stats]):.2%}",
            f"- Runs reaching max iterations: {sum(1 for s in stats if s['convergence_rate'] >= 0.99)}",
            "",
            "## Visualizations",
            "",
            "- `fitness_progression.png` - Fitness evolution over generations",
            "- `parameter_correlations.png` - Parameter impact analysis",
            "- `comparison_summary.csv` - Detailed statistics in CSV format",
            "- `comparison_summary.json` - Detailed statistics in JSON format",
        ])
        
        report_path = output_dir / 'analysis_report.md'
        with open(report_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print_success("✓ Generated analysis_report.md")
    
    def export_results(self, output_dir: Path):
        """
        Export all comparison results.
        
        Args:
            output_dir: Directory to save results
        """
        print_info(f"Exporting results to {output_dir}...")
        
        # Re-normalize fitness
        normalized_individuals = self.re_normalize_fitness_across_runs()
        
        # Generate visualizations
        self.generate_comparison_visualizations(output_dir, normalized_individuals)
        
        print_success(f"✅ Export complete! Results saved to: {output_dir}")


def run_multi_run_comparator():
    """Main entry point for multi-run comparator"""
    print_header("Multi-Run GA Comparator", "Compare multiple GA runs")
    
    # Find available GA runs
    runs = GARunLoader.find_ga_runs()
    
    if not runs:
        print_error("No GA runs found in output/ga_results/")
        print_info("Run the genetic algorithm first to generate data")
        return
    
    if len(runs) < 2:
        print_error("At least 2 GA runs are required for comparison")
        print_info(f"Found only {len(runs)} run(s)")
        return
    
    # Display available runs
    console.print("[bold]Available GA Runs:[/bold]\n")
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", justify="right", width=3)
    table.add_column("Run", style="white")
    table.add_column("Pop Size", justify="right", style="yellow")
    table.add_column("Max Iter", justify="right", style="yellow")
    table.add_column("Total Inds", justify="right", style="cyan")
    table.add_column("Best Fitness", justify="right", style="green")
    
    for idx, run_dir in enumerate(runs, 1):
        try:
            loader = GARunLoader(run_dir)
            summary = loader.get_run_summary()
            table.add_row(
                str(idx), 
                run_dir.name, 
                str(summary['population_size']),
                str(summary['max_iterations']),
                str(summary['total_individuals']),
                f"{summary['best_fitness']:.6f}"
            )
        except Exception as e:
            table.add_row(str(idx), run_dir.name, "[red]Error[/red]", "[red]Error[/red]", "[red]Error[/red]", "[red]Error loading[/red]")
    
    console.print(table)
    console.print()
    
    # Get user selection
    console.print("[bold]Select runs to compare (comma-separated numbers, e.g., '1,2,3' or 'all'):[/bold]")
    selection = Prompt.ask("Selection", default="all")
    
    if selection.lower() == 'all':
        selected_runs = runs
    else:
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected_runs = [runs[i] for i in indices if 0 <= i < len(runs)]
        except (ValueError, IndexError):
            print_error("Invalid selection")
            return
    
    if len(selected_runs) < 2:
        print_error("At least 2 runs must be selected")
        return
    
    console.print()
    print_info(f"Selected {len(selected_runs)} runs for comparison")
    console.print()
    
    # Create comparator
    comparator = MultiRunComparator(selected_runs)
    
    # Display comparison summary
    comparator.display_comparison_summary()
    
    # Ask if user wants to export results
    if confirm_action("Generate and export comparison analysis?", default=True):
        timestamp = datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
        output_dir = ANALYSIS_OUTPUT_DIR / f"multi_run_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        comparator.export_results(output_dir)
