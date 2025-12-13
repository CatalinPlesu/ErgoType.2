"""
GA Runs Queue - Programmatically define and execute multiple GA runs sequentially.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class GARunConfig:
    """Configuration for a single GA run"""
    
    def __init__(
        self,
        name: str,
        keyboard_file: str = 'src/data/keyboards/ansi_60_percent.json',
        text_file: str = 'src/data/text/raw/simple_wikipedia_dataset.txt',
        population_size: int = 30,
        max_iterations: int = 50,
        stagnant_limit: int = 10,
        max_concurrent_processes: int = 4,
        fitts_a: float = 0.5,
        fitts_b: float = 0.3,
        finger_coefficients: Optional[List[float]] = None,
        use_rabbitmq: bool = True,
        save_heuristics: bool = True
    ):
        self.name = name
        self.keyboard_file = keyboard_file
        self.text_file = text_file
        self.population_size = population_size
        self.max_iterations = max_iterations
        self.stagnant_limit = stagnant_limit
        self.max_concurrent_processes = max_concurrent_processes
        self.fitts_a = fitts_a
        self.fitts_b = fitts_b
        self.finger_coefficients = finger_coefficients or [0.07, 0.06, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.06, 0.07]
        self.use_rabbitmq = use_rabbitmq
        self.save_heuristics = save_heuristics
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for run_genetic_algorithm"""
        return {
            'keyboard_file': self.keyboard_file,
            'text_file': self.text_file,
            'population_size': self.population_size,
            'max_iterations': self.max_iterations,
            'stagnant_limit': self.stagnant_limit,
            'max_concurrent_processes': self.max_concurrent_processes,
            'fitts_a': self.fitts_a,
            'fitts_b': self.fitts_b,
            'finger_coefficients': self.finger_coefficients,
            'use_rabbitmq': self.use_rabbitmq,
            'save_heuristics': self.save_heuristics
        }
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        return {
            'name': self.name,
            **self.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GARunConfig':
        """Create from dictionary"""
        return cls(**data)


class GARunsQueue:
    """Queue of GA runs to execute sequentially"""
    
    def __init__(self):
        self.runs: List[GARunConfig] = []
        self.results: List[Dict[str, Any]] = []
    
    def add_run(self, config: GARunConfig):
        """Add a run configuration to the queue"""
        self.runs.append(config)
    
    def clear(self):
        """Clear all runs from the queue"""
        self.runs.clear()
        self.results.clear()
    
    def save_to_file(self, filepath: str):
        """Save queue configuration to a JSON file"""
        data = {
            'runs': [run.to_json() for run in self.runs]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, filepath: str):
        """Load queue configuration from a JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.runs.clear()
        for run_data in data.get('runs', []):
            self.runs.append(GARunConfig.from_dict(run_data))
    
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
        
        for i, run_config in enumerate(self.runs, 1):
            if verbose:
                print(f"\n{'='*80}")
                print(f"RUN {i}/{len(self.runs)}: {run_config.name}")
                print(f"{'='*80}")
            
            # CRITICAL: Reset Individual ID counter before each run
            Individual._next_id = 0
            if verbose:
                print(f"✅ Reset Individual ID counter to 0")
            
            # Capture start time before try block
            start_time = datetime.now()
            
            try:
                # Execute the GA run
                best_individual = run_genetic_algorithm(**run_config.to_dict())
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Store results
                result = {
                    'run_number': i,
                    'name': run_config.name,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': duration,
                    'success': True,
                    'best_fitness': best_individual.fitness if best_individual and hasattr(best_individual, 'fitness') else None,
                    'best_layout': ''.join(best_individual.chromosome) if best_individual and hasattr(best_individual, 'chromosome') else None,
                    'config': run_config.to_json()
                }
                
                self.results.append(result)
                
                if verbose:
                    print(f"\n✅ Run {i} completed successfully")
                    print(f"   Duration: {duration:.2f} seconds")
                    if best_individual:
                        print(f"   Best fitness: {best_individual.fitness:.6f}")
                
            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                if verbose:
                    print(f"\n❌ Run {i} failed: {e}")
                    import traceback
                    traceback.print_exc()
                
                result = {
                    'run_number': i,
                    'name': run_config.name,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': duration,
                    'success': False,
                    'error': str(e),
                    'config': run_config.to_json()
                }
                
                self.results.append(result)
        
        if verbose:
            self._print_summary()
        
        return self.results
    
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


def create_example_queue() -> GARunsQueue:
    """
    Create an example queue with multiple GA runs for demonstration.
    Users can modify this function or create their own queues programmatically.
    """
    queue = GARunsQueue()
    
    # Example 1: Small population, quick test
    queue.add_run(GARunConfig(
        name="Quick Test - Small Population",
        population_size=10,
        max_iterations=20,
        stagnant_limit=5,
        max_concurrent_processes=4
    ))
    
    # Example 2: Medium population
    queue.add_run(GARunConfig(
        name="Medium Run - Standard Parameters",
        population_size=30,
        max_iterations=50,
        stagnant_limit=10,
        max_concurrent_processes=4
    ))
    
    # Example 3: Different Fitts's Law parameters
    queue.add_run(GARunConfig(
        name="Custom Fitts Parameters",
        population_size=20,
        max_iterations=30,
        stagnant_limit=8,
        fitts_a=0.6,
        fitts_b=0.4,
        max_concurrent_processes=4
    ))
    
    return queue


if __name__ == "__main__":
    # Example usage
    queue = create_example_queue()
    
    print(f"Created queue with {len(queue.runs)} runs:")
    for i, run in enumerate(queue.runs, 1):
        print(f"{i}. {run.name}")
    
    # Save queue configuration
    queue.save_to_file("output/example_ga_queue.json")
    print("\nQueue configuration saved to output/example_ga_queue.json")
    
    # Execute the queue
    # queue.execute()
