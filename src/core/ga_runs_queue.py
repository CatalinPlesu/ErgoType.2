"""
GA Runs Queue - Programmatically define and execute multiple GA runs sequentially.
Queue is stored as a list of dictionaries for easy manipulation.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


# Default parameter values
DEFAULT_PARAMS = {
    'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
    'text_file': 'src/data/text/raw/simple_wikipedia_dataset.txt',
    'population_size': 30,
    'max_iterations': 50,
    'stagnant_limit': 10,
    'max_concurrent_processes': 4,
    'fitts_a': 0.5,
    'fitts_b': 0.3,
    'finger_coefficients': [0.07, 0.06, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.06, 0.07],
    'use_rabbitmq': True,
    'save_heuristics': True
}


def create_run_config(name: str, **kwargs) -> Dict[str, Any]:
    """
    Create a run configuration dictionary.
    
    Args:
        name: Name of the run
        **kwargs: Any GA parameters to override defaults
        
    Returns:
        Dictionary with run configuration
    """
    config = {'name': name}
    config.update(DEFAULT_PARAMS)
    config.update(kwargs)
    return config


class GARunsQueue:
    """
    Queue of GA runs to execute sequentially.
    Stores runs as a list of dictionaries for easy adding/removing.
    """
    
    def __init__(self):
        self.runs: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
    
    def add_run(self, run_config: Dict[str, Any]):
        """
        Add a run configuration to the queue.
        
        Args:
            run_config: Dictionary with run parameters (use create_run_config helper)
        """
        # Ensure name is present
        if 'name' not in run_config:
            run_config['name'] = f"Run {len(self.runs) + 1}"
        
        # Merge with defaults for any missing parameters
        full_config = DEFAULT_PARAMS.copy()
        full_config.update(run_config)
        
        self.runs.append(full_config)
    
    def remove_run(self, index: int):
        """Remove a run by index"""
        if 0 <= index < len(self.runs):
            self.runs.pop(index)
    
    def clear(self):
        """Clear all runs from the queue"""
        self.runs.clear()
        self.results.clear()
    
    def save_to_file(self, filepath: str):
        """Save queue configuration to a JSON file"""
        data = {
            'runs': self.runs
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, filepath: str):
        """Load queue configuration from a JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.runs.clear()
        for run_data in data.get('runs', []):
            self.add_run(run_data)
    
    def execute(self, verbose: bool = True):
        """
        Execute all runs in the queue sequentially.
        Resets Individual._next_id before each run.
        """
        from core.run_ga import run_genetic_algorithm
        from core.ga import Individual
        
        if verbose:
            print("\n" + "="*80)
            print(f"EXECUTING GA RUNS QUEUE - {len(self.runs)} runs")
            print("="*80)
        
        self.results.clear()
        
        # Track overall execution metrics
        queue_start_time = datetime.now()
        total_individuals_processed = 0
        
        for i, run_config in enumerate(self.runs, 1):
            if verbose:
                print(f"\n{'='*80}")
                print(f"RUN {i}/{len(self.runs)}: {run_config['name']}")
                print(f"{'='*80}")
            
            # CRITICAL: Reset Individual ID counter before each run
            Individual._next_id = 0
            if verbose:
                print(f"✅ Reset Individual ID counter to 0")
            
            # Capture start time before try block
            start_time = datetime.now()
            
            try:
                # Extract parameters for run_genetic_algorithm (exclude 'name')
                run_params = {k: v for k, v in run_config.items() if k != 'name'}
                
                # Execute the GA run
                best_individual = run_genetic_algorithm(**run_params)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Calculate individuals processed in this run
                individuals_this_run = run_config['population_size'] * run_config['max_iterations']
                total_individuals_processed += individuals_this_run
                
                # Store results
                result = {
                    'run_number': i,
                    'name': run_config['name'],
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': duration,
                    'individuals_processed': individuals_this_run,
                    'success': True,
                    'best_fitness': best_individual.fitness if best_individual and hasattr(best_individual, 'fitness') else None,
                    'best_layout': ''.join(best_individual.chromosome) if best_individual and hasattr(best_individual, 'chromosome') else None,
                    'config': run_config
                }
                
                self.results.append(result)
                
                if verbose:
                    print(f"\n✅ Run {i} completed successfully")
                    print(f"   Duration: {duration:.2f} seconds")
                    if best_individual:
                        print(f"   Best fitness: {best_individual.fitness:.6f}")
                    
                    # Print progress banner
                    self._print_progress_banner(
                        i, 
                        len(self.runs), 
                        queue_start_time, 
                        total_individuals_processed
                    )
                
            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Estimate individuals processed (may be less if failed early)
                individuals_this_run = run_config['population_size'] * run_config['max_iterations']
                total_individuals_processed += individuals_this_run
                
                if verbose:
                    print(f"\n❌ Run {i} failed: {e}")
                    import traceback
                    traceback.print_exc()
                
                result = {
                    'run_number': i,
                    'name': run_config['name'],
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': duration,
                    'individuals_processed': individuals_this_run,
                    'success': False,
                    'error': str(e),
                    'config': run_config
                }
                
                self.results.append(result)
                
                if verbose:
                    # Print progress banner even for failed runs
                    self._print_progress_banner(
                        i, 
                        len(self.runs), 
                        queue_start_time, 
                        total_individuals_processed
                    )
        
        if verbose:
            self._print_summary()
        
        return self.results
    
    def _print_progress_banner(self, completed: int, total: int, start_time: datetime, total_individuals: int):
        """
        Print a detailed progress banner after each run completion.
        
        Args:
            completed: Number of runs completed
            total: Total number of runs
            start_time: When the queue execution started
            total_individuals: Total individuals processed so far
        """
        elapsed = (datetime.now() - start_time).total_seconds()
        elapsed_str = self._format_duration(elapsed)
        
        # Calculate time per individual
        time_per_individual = elapsed / total_individuals if total_individuals > 0 else 0
        
        # Estimate remaining individuals to process
        remaining_individuals = 0
        for i in range(completed, total):
            run = self.runs[i]
            remaining_individuals += run['population_size'] * run['max_iterations']
        
        # Estimate remaining time
        estimated_remaining = remaining_individuals * time_per_individual if time_per_individual > 0 else 0
        remaining_str = self._format_duration(estimated_remaining)
        
        # Calculate percentage
        percentage = (completed / total) * 100
        
        # Create progress bar
        bar_width = 50
        filled = int(bar_width * completed / total)
        bar = '█' * filled + '░' * (bar_width - filled)
        
        # Print banner
        print("\n" + "╔" + "═"*78 + "╗")
        print("║" + " "*78 + "║")
        print("║" + f"{'QUEUE EXECUTION PROGRESS':^78}" + "║")
        print("║" + " "*78 + "║")
        print("╠" + "═"*78 + "╣")
        print("║" + " "*78 + "║")
        print("║" + f"  Progress: [{bar}] {percentage:>5.1f}%".ljust(78) + "║")
        print("║" + f"  Completed: {completed}/{total} runs".ljust(78) + "║")
        print("║" + " "*78 + "║")
        print("║" + f"  ⏱️  Elapsed Time:    {elapsed_str}".ljust(78) + "║")
        print("║" + f"  ⏳ Estimated Remaining: {remaining_str}".ljust(78) + "║")
        print("║" + " "*78 + "║")
        print("║" + f"  📊 Individuals Processed: {total_individuals:,}".ljust(78) + "║")
        print("║" + f"  ⚡ Time per Individual:   {time_per_individual*1000:.2f} ms".ljust(78) + "║")
        print("║" + " "*78 + "║")
        print("╚" + "═"*78 + "╝")
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to a human-readable string."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"{hours}h {mins}m"
    
    def _print_summary(self):
        """Print summary of all runs"""
        print("\n" + "="*80)
        print("GA RUNS QUEUE - SUMMARY")
        print("="*80)
        
        successful_runs = [r for r in self.results if r.get('success', False)]
        failed_runs = [r for r in self.results if not r.get('success', False)]
        
        print(f"Total runs: {len(self.results)}")
        print(f"Successful: {len(successful_runs)}")
        print(f"Failed: {len(failed_runs)}")
        
        if successful_runs:
            print(f"\n✅ Successful runs:")
            for result in successful_runs:
                duration = result.get('duration_seconds', 0)
                fitness = result.get('best_fitness', 'N/A')
                print(f"  {result['run_number']}. {result['name']}: fitness={fitness}, duration={duration:.2f}s")
        
        if failed_runs:
            print(f"\n❌ Failed runs:")
            for result in failed_runs:
                error = result.get('error', 'Unknown error')
                print(f"  {result['run_number']}. {result['name']}: {error}")
        
        print("="*80)
    
    def save_results(self, filepath: str):
        """Save execution results to a JSON file"""
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_runs': len(self.results),
                'successful_runs': sum(1 for r in self.results if r.get('success', False)),
                'failed_runs': sum(1 for r in self.results if not r.get('success', False)),
                'results': self.results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Results saved to: {filepath}")


def create_parameter_exploration_queue() -> GARunsQueue:
    """
    Create a 25-configuration matrix for parameter space exploration.
    
    Optimized for ~3 hours runtime with maximum parameter coverage.
    All runs use stagnation_threshold=3 and processes=1.
    
    Explores:
    - Iterations: 5 to 300 (10 levels)
    - Population: 5 to 300 (7 levels)
    
    Returns:
        GARunsQueue with 25 predefined configurations
    """
    queue = GARunsQueue()
    
    # Configuration matrix: (iterations, population, purpose)
    configs = [
        (5, 5, "Sanity check"),
        (5, 150, "Wide shallow search"),
        (5, 300, "Max width minimal depth"),
        (50, 5, "Narrow deep search"),
        (50, 30, "Small balanced"),
        (50, 70, "Reference baseline"),
        (50, 150, "Wide quick search"),
        (50, 300, "Max population test"),
        (75, 50, "Balanced small-medium"),
        (75, 110, "Sweet spot candidate"),
        (100, 30, "Reference point"),
        (100, 70, "Medium balanced"),
        (100, 150, "Large pop moderate iter"),
        (150, 30, "Deep narrow"),
        (150, 70, "Balanced medium-large"),
        (150, 110, "Sweet spot"),
        (175, 50, "Deep moderate width"),
        (200, 30, "Very deep narrow"),
        (200, 70, "Deep balanced"),
        (200, 110, "Large thorough"),
        (250, 50, "Very deep moderate"),
        (250, 70, "Max depth moderate pop"),
        (275, 30, "Extreme depth narrow"),
        (300, 50, "Max depth moderate"),
        (300, 70, "Max depth good pop"),
    ]
    
    for i, (iterations, population, purpose) in enumerate(configs, 1):
        queue.add_run(create_run_config(
            name=f"Config{i:02d}_I{iterations}_P{population}_{purpose.replace(' ', '_')}",
            population_size=population,
            max_iterations=iterations,
            stagnant_limit=3,
            max_concurrent_processes=1
        ))
    
    return queue


if __name__ == "__main__":
    # Example usage - create parameter exploration queue
    queue = create_parameter_exploration_queue()
    
    print(f"Created parameter exploration queue with {len(queue.runs)} runs:")
    for i, run in enumerate(queue.runs, 1):
        print(f"{i}. {run['name']}")
    
    # Save queue configuration
    queue.save_to_file("output/param_exploration_queue.json")
    print("\nQueue configuration saved to output/param_exploration_queue.json")
    
    # Execute the queue
    # queue.execute()
