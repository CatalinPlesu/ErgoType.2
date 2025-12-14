from concurrent.futures import ProcessPoolExecutor, as_completed
from data.layouts.keyboard_genotypes import LAYOUT_DATA
from core.map_json_exporter import CSharpFitnessConfig
from core.keyboard import Serial
from core.evaluator import Evaluator
from core.job_queue import JobQueue
from config.config import Config
import os
import pickle
import random
import sys
import multiprocessing as mp
import time
import gc

# Get the project root directory (go up two levels from src/core)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _evaluate_individual_worker(individual_data, keyboard_file, text_file, finger_coefficients, fitts_a, fitts_b):
    """Worker function - each process evaluates ONE individual then exits"""
    try:
        individual_id, chromosome, name = individual_data
        
        # DEBUG: Print what we received
        # print(f"Worker {os.getpid()}: Processing {name}, chromosome type: {type(chromosome)}, length: {len(chromosome)}")
        
        # Initialize C# in this process using the safe helper
        from core.clr_loader_helper import load_csharp_fitness_library
        Fitness, _ = load_csharp_fitness_library(PROJECT_ROOT)
        
        # Create evaluator - CRITICAL: Use absolute path
        evaluator = Evaluator(debug=False)
        evaluator.load_keyoard(keyboard_file)
        evaluator.load_layout()

        # CRITICAL: Ensure chromosome is a list
        if isinstance(chromosome, str):
            chromosome = list(chromosome)
        elif not isinstance(chromosome, list):
            chromosome = list(chromosome)
        
        # Remap layout
        qwerty_base = list(LAYOUT_DATA["qwerty"])
        evaluator.layout.remap(qwerty_base, chromosome)
        
        # DEBUG: Check if char_mappings would be generated
        # print(f"Worker {os.getpid()}: Layout mapper has {len(evaluator.layout.mapper.data)} keys")

        # Generate C# configuration JSON
        config_gen = CSharpFitnessConfig(
            keyboard=evaluator.keyboard,
            layout=evaluator.layout
        )

        json_string = config_gen.generate_json_string(
            text_file_path=text_file,
            finger_coefficients=finger_coefficients,
            fitts_a=fitts_a,
            fitts_b=fitts_b
        )
        
        # DEBUG: Verify JSON has char_mappings
        import json as json_module
        try:
            config_check = json_module.loads(json_string)
            if 'char_mappings' not in config_check:
                raise ValueError(f"Missing char_mappings in JSON for {name}")
            if len(config_check['char_mappings']) == 0:
                raise ValueError(f"Empty char_mappings in JSON for {name}")
            # print(f"Worker {os.getpid()}: JSON has {len(config_check['char_mappings'])} characters")
        except Exception as json_err:
            print(f"JSON validation error for {name}: {json_err}")
            raise

        # Calculate fitness
        fitness_calculator = Fitness(json_string)
        result = fitness_calculator.Compute()

        distance = result.Item1
        time_taken = result.Item2

        print(f"Process {os.getpid()}: Evaluated {name}, distance = {distance:.2f}, time = {time_taken:.2f}")
        
        return individual_id, distance, time_taken

    except Exception as e:
        print(f"Error evaluating {name} in process {os.getpid()}: {e}")
        import traceback
        traceback.print_exc()
        return individual_id, float('inf'), float('inf')


class Individual:
    _next_id = 0

    def __init__(self, chromosome, fitness=None, distance=None, time_taken=None, parents=None, generation=0, name=None):
        self.chromosome = chromosome
        self.fitness = fitness
        self.distance = distance
        self.time_taken = time_taken
        self.id = Individual._next_id
        Individual._next_id += 1
        self.parents = parents or []
        self.generation = generation
        if name is None:
            self.name = f"gen_{generation}-{self.id}"
        else:
            self.name = name

    def __repr__(self):
        parent_names = [p if isinstance(p, str) else f"gen_{self.generation-1}-{p}" for p in self.parents] if self.parents else []
        return f"Individual(name={self.name}, fitness={self.fitness:.6f if self.fitness else None}, distance={self.distance}, time={self.time_taken}, parents={parent_names})"


class GeneticAlgorithmSimulation:
    # Constants for population adjustment during phase transitions
    EXPANSION_MUTATION_RATE = 0.1  # Mutation rate when expanding population
    EXPANSION_NUM_MUTATIONS = 2     # Number of mutations when expanding population
    EXPANSION_TEMPLATE_POOL_SIZE = 10  # Use top N individuals as templates for expansion
    
    def __init__(self, 
                 keyboard_file='data/keyboards/ansi_60_percent.json',
                 text_file='data/text/raw/simple_wikipedia_dataset.txt',
                 population_size=50,
                 fitts_a=0.5,
                 fitts_b=0.3,
                 finger_coefficients=None,
                 max_concurrent_processes=None,
                 use_rabbitmq=True,
                 is_worker=False,
                 population_phases=None):
        """
        Initialize GA with C# fitness calculator.
        
        Args:
            is_worker: If True, runs in worker mode (processes jobs from queue)
                      If False, runs as master (coordinates GA and also processes jobs)
            population_phases: Optional list of tuples (iterations, max_population) for dynamic phases.
                             If provided, replaces population_size and max_iterations parameters.
                             Example: [(30, 50), (1, 1000), (10, 50)]
        """
        self.is_worker = is_worker
        self.population_phases = population_phases
        
        if is_worker:
            print("="*80)
            print("🔧 WORKER MODE - Waiting for jobs from master...")
            print("="*80)
        else:
            print("="*80)
            print("👑 MASTER MODE - Coordinating GA and processing jobs...")
            print("="*80)
        
        # Store configuration - always store as absolute paths internally
        self.keyboard_file = os.path.join(PROJECT_ROOT, keyboard_file) if not os.path.isabs(keyboard_file) else keyboard_file
        self.text_file = os.path.join(PROJECT_ROOT, text_file) if not os.path.isabs(text_file) else text_file
        self.fitts_a = fitts_a
        self.fitts_b = fitts_b
        
        if finger_coefficients is None:
            self.finger_coefficients = [0.07, 0.06, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.06, 0.07]
        else:
            self.finger_coefficients = finger_coefficients

        # Initialize evaluator for layout management
        self.evaluator = Evaluator(debug=False)
        self.evaluator.load_keyoard(self.keyboard_file)
        self.evaluator.load_layout()

        print("Evaluator initialized successfully")

        # Process pool configuration
        if max_concurrent_processes is None:
            self.max_processes = mp.cpu_count()
        else:
            self.max_processes = max_concurrent_processes
        
        print(f"Using up to {self.max_processes} local concurrent processes")

        # Initialize distributed queue
        self.job_queue = JobQueue(use_rabbitmq=use_rabbitmq)
        
        if is_worker:
            # Worker mode: just run the worker loop
            self._run_worker()
        else:
            # Master mode: initialize GA state
            self.current_generation = 0
            self.individual_names = {}
            self.all_individuals = {}
            self.population_size = population_size
            self.population_initialization(self.population_size)
            self.previous_population_ids = self.get_current_population_ids()
            self.previous_population_iteration = 0
            self.evaluated_individuals = []

    def _run_worker(self):
        """Worker mode: continuously process jobs from queue"""
        print(f"\n🔧 Worker starting with {self.max_processes} local processes")
        print("⏳ Waiting for jobs...")
        
        # Initialize C# once at worker startup using the safe helper
        try:
            from core.clr_loader_helper import initialize_clr_runtime
            was_initialized = initialize_clr_runtime()
            if was_initialized:
                print("✅ C# runtime initialized")
            else:
                print("✅ C# runtime already initialized")
        except Exception as e:
            print(f"⚠️  Warning: C# runtime init: {e}")
        
        current_config = None
        last_job_time = time.time()
        
        # Use ProcessPoolExecutor for parallel processing
        with ProcessPoolExecutor(max_workers=self.max_processes, max_tasks_per_child=1) as executor:
            futures = {}
            
            while True:
                try:
                    # Check if jobs queue has items
                    jobs_count = self.job_queue.get_jobs_queue_size()
                    
                    # If queue just got populated, fetch fresh config
                    if jobs_count > 0 and current_config is None:
                        print(f"\n📋 Jobs detected ({jobs_count} pending), fetching configuration...")
                        current_config = self.job_queue.get_config(timeout=5)
                        if current_config:
                            # Update local config - convert relative paths to absolute
                            self.keyboard_file = self._to_absolute_path(current_config.get('keyboard_file', self.keyboard_file))
                            self.text_file = self._to_absolute_path(current_config.get('text_file', self.text_file))
                            self.fitts_a = current_config.get('fitts_a', self.fitts_a)
                            self.fitts_b = current_config.get('fitts_b', self.fitts_b)
                            self.finger_coefficients = current_config.get('finger_coefficients', self.finger_coefficients)
                            print(f"✅ Configuration loaded (converted to absolute paths):")
                            print(f"   Keyboard: {self.keyboard_file}")
                            print(f"   Text: {self.text_file}")
                            print(f"   Fitts: a={self.fitts_a}, b={self.fitts_b}")
                    
                    # Pull jobs while we have available workers
                    active_jobs = len(futures)
                    
                    while active_jobs < self.max_processes:
                        job_data, delivery_tag = self.job_queue.pull_job(timeout=0.1)
                        
                        if not job_data:
                            # No jobs available right now
                            break
                        
                        last_job_time = time.time()
                        individual_id = job_data['individual_id']
                        chromosome = job_data['chromosome']
                        name = job_data['name']
                        
                        print(f"🔨 Processing job: {name} (ID: {individual_id}) [active: {active_jobs+1}/{self.max_processes}]")
                        
                        # Submit to process pool
                        individual_data = (individual_id, chromosome, name)
                        future = executor.submit(
                            _evaluate_individual_worker,
                            individual_data,
                            self.keyboard_file,
                            self.text_file,
                            self.finger_coefficients,
                            self.fitts_a,
                            self.fitts_b
                        )
                        futures[future] = (job_data, delivery_tag)
                        active_jobs = len(futures)
                    
                    # Check for completed jobs
                    if futures:
                        for future in list(futures.keys()):
                            if future.done():
                                job_data, delivery_tag = futures.pop(future)
                                
                                try:
                                    result_id, distance, time_taken = future.result()
                                    
                                    # Push result
                                    result = {
                                        'individual_id': result_id,
                                        'distance': distance,
                                        'time_taken': time_taken
                                    }
                                    self.job_queue.push_result(result)
                                    self.job_queue.ack_job(delivery_tag)
                                    
                                    print(f"✅ Completed: {job_data['name']}")
                                    
                                except Exception as e:
                                    print(f"❌ Error processing {job_data['name']}: {e}")
                                    import traceback
                                    traceback.print_exc()
                                    self.job_queue.nack_job(delivery_tag, requeue=True)
                    
                    # Check if we should reset config (idle for a while)
                    active_jobs = len(futures)
                    
                    if active_jobs == 0:
                        time_since_last = time.time() - last_job_time
                        
                        # If queue was active but now empty for a while, reset config
                        if current_config is not None and time_since_last > 10:
                            jobs_remaining = self.job_queue.get_jobs_queue_size()
                            if jobs_remaining == 0:
                                print(f"\n💤 No jobs for 10s, waiting for next batch...")
                                current_config = None
                        
                        time.sleep(0.5)  # Short sleep when idle
                    else:
                        time.sleep(0.1)  # Very short sleep when processing
                            
                except KeyboardInterrupt:
                    print("\n\n🛑 Worker stopped by user")
                    self.job_queue.close()
                    sys.exit(0)
                except Exception as e:
                    print(f"⚠️  Worker error: {e}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(1)

    def population_initialization(self, size=50):
        """Initialize population (master only)"""
        if self.is_worker:
            return
            
        self.population = []

        for layout_name, genotype in LAYOUT_DATA.items():
            individual = Individual(chromosome=list(genotype), generation=0, name=layout_name)
            self.population.append(individual)
            self.individual_names[individual.id] = individual.name
            print(f"Added heuristic layout: {layout_name}")

        print(f"Population initialized with {len(self.population)} heuristic individuals")

        if size > len(self.population):
            if self.population:
                template_genotype = self.population[0].chromosome
                needed = size - len(self.population)
                print(f"Adding {needed} random individuals")

                for _ in range(needed):
                    shuffled_clone = template_genotype.copy()
                    random.shuffle(shuffled_clone)
                    individual = Individual(chromosome=shuffled_clone, generation=0)
                    self.population.append(individual)
                    self.individual_names[individual.id] = individual.name

        print(f"Total population size: {len(self.population)}")

    def get_current_population_ids(self):
        return [ind.id for ind in self.population]

    def get_individual_name(self, individual_id):
        return self.individual_names.get(individual_id, f"unknown-{individual_id}")

    def prepare_individual_data(self, individual):
        return (individual.id, individual.chromosome, individual.name)

    def _to_relative_path(self, absolute_path):
        """
        Convert absolute path to relative path from PROJECT_ROOT.
        This allows distributed workers to find files in their local repository.
        
        Args:
            absolute_path: Absolute file path
            
        Returns:
            Relative path from PROJECT_ROOT, or original path if conversion fails
        """
        try:
            # Normalize to absolute path then compute relative path
            abs_path = os.path.abspath(absolute_path)
            rel_path = os.path.relpath(abs_path, PROJECT_ROOT)
            return rel_path
        except (ValueError, TypeError):
            # If conversion fails (e.g., different drives on Windows), return original
            return absolute_path
    
    def _to_absolute_path(self, relative_path):
        """
        Convert relative path to absolute path based on PROJECT_ROOT.
        This allows workers to resolve relative paths from distributed jobs.
        
        Args:
            relative_path: Relative file path from PROJECT_ROOT
            
        Returns:
            Absolute path, or original if already absolute
        """
        if os.path.isabs(relative_path):
            return relative_path
        return os.path.join(PROJECT_ROOT, relative_path)

    def normalize_and_calculate_fitness(self):
        """Normalize toward 0 (better = closer to 0) with 1.2x max scaling"""
        all_evaluated = [ind for ind in self.evaluated_individuals
                        if ind.distance is not None and ind.time_taken is not None 
                        and ind.distance != float('inf') and ind.time_taken != float('inf')]
        
        if not all_evaluated:
            print("Warning: No individuals with valid raw metrics to normalize")
            return

        distances = [ind.distance for ind in all_evaluated]
        times = [ind.time_taken for ind in all_evaluated]

        max_distance = max(distances) * 1.2
        max_time = max(times) * 1.2

        print(f"\nNormalization ranges (global across all generations):")
        print(f"  Distance: [0, {max_distance:.2f}]")
        print(f"  Time: [0, {max_time:.2f}]")

        for ind in all_evaluated:
            normalized_distance = ind.distance / max_distance
            normalized_time = ind.time_taken / max_time
            ind.fitness = 0.5 * normalized_distance + 0.5 * normalized_time
        
        for ind in self.population + getattr(self, 'children', []):
            if ind.distance == float('inf') or ind.time_taken == float('inf'):
                ind.fitness = float('inf')

    def fitness_function_calculation(self):
        """
        Calculate fitness using distributed queue system.
        Master acts as both coordinator and worker.
        """
        if self.is_worker:
            return  # Workers don't call this
            
        individuals_to_evaluate = [ind for ind in self.population if ind.distance is None]

        if hasattr(self, 'children'):
            individuals_to_evaluate.extend([child for child in self.children if child.distance is None])

        if not individuals_to_evaluate:
            self.normalize_and_calculate_fitness()
            return

        print(f"\n{'='*80}")
        print(f"📤 DISTRIBUTING {len(individuals_to_evaluate)} JOBS")
        print(f"{'='*80}")
        
        # Update progress tracker with job batch
        if hasattr(self, 'progress_tracker'):
            self.progress_tracker.start_job_batch(len(individuals_to_evaluate))

        # Push configuration with relative paths for distributed workers
        config = {
            'keyboard_file': self._to_relative_path(self.keyboard_file),
            'text_file': self._to_relative_path(self.text_file),
            'fitts_a': self.fitts_a,
            'fitts_b': self.fitts_b,
            'finger_coefficients': self.finger_coefficients
        }
        self.job_queue.push_config(config)
        print("✅ Configuration pushed to queue (using relative paths)")

        # Push all jobs
        for ind in individuals_to_evaluate:
            job = {
                'individual_id': ind.id,
                'chromosome': ind.chromosome,
                'name': ind.name
            }
            self.job_queue.push_job(job)
        
        print(f"✅ Pushed {len(individuals_to_evaluate)} jobs to queue")

        # ========================================================================
        # FIXED: Master competes fairly with workers
        # ========================================================================
        print(f"\n🔨 Master processing jobs with {self.max_processes} local workers...")
        print(f"💡 Master will compete with remote workers for jobs (fair distribution)")
        
        # Process using ProcessPoolExecutor - pull jobs one at a time
        with ProcessPoolExecutor(max_workers=self.max_processes, max_tasks_per_child=1) as executor:
            futures = {}
            no_job_cycles = 0
            
            # Keep pulling and submitting jobs as workers become available
            while True:
                active_jobs = len(futures)
                
                # Try to keep all workers busy - pull jobs up to max_processes
                while active_jobs < self.max_processes:
                    job_data, delivery_tag = self.job_queue.pull_job(timeout=0.1)
                    
                    if not job_data:
                        # No more jobs available right now
                        break
                    
                    no_job_cycles = 0  # Reset counter when we get a job
                    
                    # Submit job to local worker
                    individual_data = (
                        job_data['individual_id'],
                        job_data['chromosome'],
                        job_data['name']
                    )
                    
                    future = executor.submit(
                        _evaluate_individual_worker,
                        individual_data,
                        self.keyboard_file,
                        self.text_file,
                        self.finger_coefficients,
                        self.fitts_a,
                        self.fitts_b
                    )
                    futures[future] = (job_data, delivery_tag)
                    active_jobs = len(futures)
                    print(f"  🔨 Master pulled job: {job_data['name']} (active: {active_jobs}/{self.max_processes})")
                
                # Check if any jobs completed
                if futures:
                    for future in list(futures.keys()):
                        if future.done():
                            job_data, delivery_tag = futures.pop(future)
                            
                            try:
                                result_id, distance, time_taken = future.result()
                                
                                # Push result
                                result = {
                                    'individual_id': result_id,
                                    'distance': distance,
                                    'time_taken': time_taken
                                }
                                self.job_queue.push_result(result)
                                self.job_queue.ack_job(delivery_tag)
                                print(f"  ✅ Master completed: {job_data['name']}")
                                
                            except Exception as e:
                                print(f"  ❌ Master processing error: {e}")
                                self.job_queue.nack_job(delivery_tag, requeue=True)
                
                # Check termination conditions
                active_jobs = len(futures)
                jobs_remaining = self.job_queue.get_jobs_queue_size()
                
                if active_jobs == 0 and jobs_remaining == 0:
                    # No active jobs and no jobs in queue
                    no_job_cycles += 1
                    if no_job_cycles > 5:
                        # Give it a few cycles to make sure no jobs coming
                        print(f"  ℹ️  Master: No jobs available, exiting processing loop")
                        break
                else:
                    no_job_cycles = 0
                
                # Small sleep to avoid busy waiting
                time.sleep(0.2)

        print(f"✅ Master completed local processing")

        # Collect results
        print(f"\n📥 COLLECTING RESULTS")
        print(f"{'='*80}")
        
        results_collected = 0
        expected_results = len(individuals_to_evaluate)
        timeout_start = None
        
        while results_collected < expected_results:
            result = self.job_queue.pull_result(timeout=0.5)
            
            if result:
                timeout_start = None  # Reset timeout
                individual_id = result['individual_id']
                distance = result['distance']
                time_taken = result['time_taken']
                
                # Find and update individual
                for ind in individuals_to_evaluate:
                    if ind.id == individual_id:
                        ind.distance = distance
                        ind.time_taken = time_taken
                        if ind not in self.evaluated_individuals:
                            self.evaluated_individuals.append(ind)
                        results_collected += 1
                        
                        # Update progress tracker
                        if hasattr(self, 'progress_tracker'):
                            self.progress_tracker.update_job_progress(results_collected)
                        break
                
                if results_collected % 10 == 0 or results_collected == expected_results:
                    print(f"  📊 Progress: {results_collected}/{expected_results} results collected")
            
            else:
                # No result available
                jobs_remaining = self.job_queue.get_jobs_queue_size()
                
                if jobs_remaining == 0:
                    # Queue is empty, start timeout
                    if timeout_start is None:
                        timeout_start = time.time()
                        print(f"  ⏳ Job queue empty, waiting up to 30s for remaining {expected_results - results_collected} results...")
                    
                    elif time.time() - timeout_start > 30:
                        # Timeout - mark missing as failed
                        missing = expected_results - results_collected
                        print(f"  ⚠️  TIMEOUT: Marking {missing} missing individuals as failed (fitness=inf)")
                        
                        for ind in individuals_to_evaluate:
                            if ind.distance is None:
                                ind.distance = float('inf')
                                ind.time_taken = float('inf')
                                results_collected += 1
                        break
                
                time.sleep(0.5)

        print(f"✅ Collection complete: {results_collected}/{expected_results} results")
        print(f"{'='*80}\n")
        
        # Complete job batch tracking
        if hasattr(self, 'progress_tracker'):
            self.progress_tracker.complete_job_batch()
        
        gc.collect()
        self.normalize_and_calculate_fitness()

    def order_fitness_values(self, limited=False):
        """Print ordered fitness values"""
        sorted_population = sorted(self.population, key=lambda x: x.fitness if x.fitness is not None else float('inf'))
        print("\n" + "="*120)
        print("ORDERED FITNESS VALUES (Best to Worst)")
        print("="*120)
        print(f"{'Rank':<6} {'Name':<20} {'Fitness':<12} {'Distance':<15} {'Time':<15} {'Parents':<40}")
        print("-"*120)

        display_population = sorted_population[:10] if limited else sorted_population

        for rank, individual in enumerate(display_population, 1):
            if individual.parents:
                parent_names = [self.get_individual_name(p) for p in individual.parents]
                parents_str = ", ".join(parent_names)
            else:
                parents_str = "Initial"
            
            fitness_str = f"{individual.fitness:.6f}" if individual.fitness is not None else "N/A"
            distance_str = f"{individual.distance:.2f}" if individual.distance is not None else "N/A"
            time_str = f"{individual.time_taken:.2f}" if individual.time_taken is not None else "N/A"
            
            print(f"{rank:<6} {individual.name:<20} {fitness_str:<12} {distance_str:<15} {time_str:<15} {parents_str:<40}")

        print("="*120 + "\n")

    def tournament_selection(self, k=3):
        """Tournament selection - select exactly population_size parents"""
        self.parents = []
        target_size = len(self.population)
        
        while len(self.parents) < target_size:
            sample_size = min(k, len(self.population))
            candidates = random.sample(self.population, sample_size)
            
            best_candidate = None
            best_fitness = float('inf')
            
            for candidate in candidates:
                if candidate.fitness is not None and candidate.fitness < best_fitness:
                    best_fitness = candidate.fitness
                    best_candidate = candidate
            
            if best_candidate is not None:
                self.parents.append(best_candidate)
        
        print(f"Selected {len(self.parents)} parents via tournament selection")

    def uniform_crossover(self, offsprings_per_pair=4):
        """Uniform crossover - create children from parent pairs"""
        self.children = []

        def is_duplicate(chromosome, existing_individuals):
            chromosome_str = ''.join(chromosome)
            for individual in existing_individuals:
                if ''.join(individual.chromosome) == chromosome_str:
                    return True
            return False
        
        def is_duplicate_in_lists(chromosome, population_list, children_list):
            """Check if chromosome is duplicate without list concatenation for performance"""
            chromosome_str = ''.join(chromosome)
            for individual in population_list:
                if ''.join(individual.chromosome) == chromosome_str:
                    return True
            for individual in children_list:
                if ''.join(individual.chromosome) == chromosome_str:
                    return True
            return False

        if len(self.parents) < 2:
            print(f"Warning: Not enough parents. Have {len(self.parents)} parents.")
            return

        sorted_parents = sorted(self.parents, key=lambda x: x.fitness if x.fitness is not None else float('inf'))
        num_pairs = len(sorted_parents) // 2
        target_children = len(self.population)
        
        for pair_idx in range(num_pairs):
            parent0 = sorted_parents[pair_idx * 2]
            parent1 = sorted_parents[pair_idx * 2 + 1]

            if parent0.fitness is None or parent1.fitness is None:
                continue

            if parent0.fitness > parent1.fitness:
                parent0, parent1 = parent1, parent0

            for o in range(offsprings_per_pair):
                if len(self.children) >= target_children:
                    break
                    
                attempts = 0
                max_attempts = 10

                while attempts < max_attempts:
                    new_chromosome = [None] * len(parent0.chromosome)

                    for j in range(len(new_chromosome)):
                        if random.random() < 0.75 + o/30.0:
                            new_chromosome[j] = parent0.chromosome[j]

                    for j in range(len(new_chromosome)):
                        if new_chromosome[j] is None and parent1.chromosome[j] not in new_chromosome:
                            new_chromosome[j] = parent1.chromosome[j]

                    for j in range(len(new_chromosome)):
                        if new_chromosome[j] is None and parent0.chromosome[j] not in new_chromosome:
                            new_chromosome[j] = parent0.chromosome[j]

                    existing_genes = set(gene for gene in new_chromosome if gene is not None)
                    all_possible_genes = set(parent0.chromosome)
                    missing_genes = list(all_possible_genes - existing_genes)
                    random.shuffle(missing_genes)

                    for j in range(len(new_chromosome)):
                        if new_chromosome[j] is None:
                            new_chromosome[j] = missing_genes.pop(0)

                    all_existing = self.population + self.children + [parent0, parent1]

                    if not is_duplicate(new_chromosome, all_existing):
                        child = Individual(
                            chromosome=new_chromosome,
                            fitness=None,
                            distance=None,
                            time_taken=None,
                            parents=[parent0.id, parent1.id],
                            generation=self.current_generation + 1
                        )
                        self.children.append(child)
                        self.individual_names[child.id] = child.name
                        break
                    else:
                        attempts += 1
            
            if len(self.children) >= target_children:
                break

        # If we didn't create enough children through crossover, clone and mutate existing children
        if len(self.children) < target_children and len(self.children) > 0:
            print(f"Created {len(self.children)} unique children (target: {target_children})")
            shortage = target_children - len(self.children)
            print(f"Filling shortage of {shortage} children by cloning and mutating existing children...")
            
            # Configuration constants for population filling
            CLONE_ATTEMPTS_MULTIPLIER = 10
            BEST_PARENTS_COUNT = 10
            PARENT_MUTATION_ATTEMPTS_MULTIPLIER = 15
            CLONE_MUTATION_RATE = 0.15
            PARENT_MUTATION_RATE = 0.2
            MAX_MUTATIONS = 5
            
            # Clone and mutate existing children to fill the gap
            original_children = self.children.copy()
            clones_created = 0
            max_clone_attempts = shortage * CLONE_ATTEMPTS_MULTIPLIER
            mutation_strength = 2  # Start with moderate mutation
            
            while len(self.children) < target_children and clones_created < max_clone_attempts:
                # Select a random child to clone (prefer different sources for diversity)
                source_child = random.choice(original_children)
                
                # Clone and mutate the chromosome with increasing mutation strength
                cloned_chromosome = source_child.chromosome.copy()
                # Increase mutation strength as we make more attempts to avoid duplicates
                num_mutations = mutation_strength + (clones_created // shortage if shortage > 0 else 0)
                mutated_chromosome = self.mutate_permutation(cloned_chromosome, mutation_rate=CLONE_MUTATION_RATE, num_mutations=min(num_mutations, MAX_MUTATIONS))
                
                # Check if this clone is unique (avoid list concatenation for performance)
                if not is_duplicate_in_lists(mutated_chromosome, self.population, self.children):
                    clone = Individual(
                        chromosome=mutated_chromosome,
                        fitness=None,
                        distance=None,
                        time_taken=None,
                        parents=source_child.parents,  # Keep same parents as source
                        generation=self.current_generation + 1
                    )
                    self.children.append(clone)
                    self.individual_names[clone.id] = clone.name
                
                clones_created += 1
            
            print(f"Added {len(self.children) - len(original_children)} cloned and mutated children")
            
            # If we still don't have enough, fill remaining with random mutations of best parents
            if len(self.children) < target_children:
                remaining_shortage = target_children - len(self.children)
                print(f"Still short by {remaining_shortage}. Adding random mutations of best parents...")
                
                children_before_parent_mutations = len(self.children)
                
                # Use best parents for additional diversity
                best_parents = sorted(self.parents, key=lambda x: x.fitness if x.fitness is not None else float('inf'))[:BEST_PARENTS_COUNT]
                attempts = 0
                max_random_attempts = remaining_shortage * PARENT_MUTATION_ATTEMPTS_MULTIPLIER
                
                while len(self.children) < target_children and attempts < max_random_attempts:
                    parent = random.choice(best_parents)
                    mutated_chromosome = self.mutate_permutation(parent.chromosome.copy(), mutation_rate=PARENT_MUTATION_RATE, num_mutations=MAX_MUTATIONS)
                    
                    # Check if this mutation is unique (avoid list concatenation for performance)
                    if not is_duplicate_in_lists(mutated_chromosome, self.population, self.children):
                        child = Individual(
                            chromosome=mutated_chromosome,
                            fitness=None,
                            distance=None,
                            time_taken=None,
                            parents=[parent.id],
                            generation=self.current_generation + 1
                        )
                        self.children.append(child)
                        self.individual_names[child.id] = child.name
                    
                    attempts += 1
                
                print(f"Added {len(self.children) - children_before_parent_mutations} more children from parent mutations")
        
        print(f"Final children count: {len(self.children)} (target: {target_children})")

    def mutation(self):
        """Mutate children"""
        base_mutation_rate = 0.05
        mutation_rate = base_mutation_rate * 0.5 if self.previous_population_iteration > 0 else base_mutation_rate
        num_mutations = 1 if self.previous_population_iteration == 0 else min(self.previous_population_iteration, 5)

        for individual in self.children:
            individual.chromosome = self.mutate_permutation(individual.chromosome, mutation_rate, num_mutations)

    def mutate_permutation(self, chromosome, mutation_rate=0.05, num_mutations=1):
        """Swap mutation"""
        mutated = chromosome.copy()
        for _ in range(num_mutations):
            if random.random() < mutation_rate:
                i = random.randint(0, len(chromosome) - 1)
                j = random.randint(0, len(chromosome) - 1)
                while i == j:
                    j = random.randint(0, len(chromosome) - 1)
                mutated[i], mutated[j] = mutated[j], mutated[i]
        return mutated

    def survivor_selection(self):
        """Elitist survivor selection with individual tracking"""
        self.fitness_function_calculation()
        combined = self.population + self.children
        sorted_combined = sorted(combined, key=lambda x: x.fitness if x.fitness is not None else float('inf'))
        
        for ind in sorted_combined:
            if ind.id not in self.all_individuals:
                self.all_individuals[ind.id] = {
                    'id': ind.id,
                    'name': ind.name,
                    'generation': ind.generation,
                    'chromosome': ''.join(ind.chromosome),
                    'distance': ind.distance,
                    'time_taken': ind.time_taken,
                    'fitness': ind.fitness,
                    'parents': ind.parents
                }
        
        self.population = sorted_combined[:len(self.population)]
        
        discarded_count = len(sorted_combined) - len(self.population)
        print(f"Survivors: {len(self.population)}, Discarded: {discarded_count}, Total unique individuals: {len(self.all_individuals)}")

    def renormalize_all_individuals(self):
        """Re-normalize ALL individuals using global max values"""
        if not self.evaluated_individuals:
            print("No evaluated individuals to use for renormalization")
            return
        
        all_evaluated = [ind for ind in self.evaluated_individuals
                        if ind.distance is not None and ind.time_taken is not None 
                        and ind.distance != float('inf') and ind.time_taken != float('inf')]
        
        if not all_evaluated:
            return
        
        distances = [ind.distance for ind in all_evaluated]
        times = [ind.time_taken for ind in all_evaluated]
        
        max_distance = max(distances) * 1.2
        max_time = max(times) * 1.2
        
        print(f"\n{'='*80}")
        print("RE-NORMALIZING ALL INDIVIDUALS WITH FINAL GLOBAL SCALE")
        print(f"{'='*80}")
        print(f"Final normalization scale:")
        print(f"  Distance: [0, {max_distance:.2f}]")
        print(f"  Time: [0, {max_time:.2f}]")
        
        total_renormalized = 0
        for ind_id, ind_dict in self.all_individuals.items():
            if ind_dict['distance'] != float('inf') and ind_dict['time_taken'] != float('inf'):
                normalized_distance = ind_dict['distance'] / max_distance
                normalized_time = ind_dict['time_taken'] / max_time
                ind_dict['fitness'] = 0.5 * normalized_distance + 0.5 * normalized_time
                total_renormalized += 1
            else:
                ind_dict['fitness'] = float('inf')
        
        print(f"Re-normalized {total_renormalized} unique individuals")
        print(f"{'='*80}\n")

    def run(self, max_iterations=100, stagnant=15, population_phases=None):
        """
        Run genetic algorithm (master only)
        
        Args:
            max_iterations: Maximum iterations (ignored if population_phases is provided)
            stagnant: Stagnation limit for termination
            population_phases: Optional list of tuples (iterations, max_population) for dynamic phases.
                             If provided, replaces max_iterations parameter.
        """
        if self.is_worker:
            return None
        
        # Use instance population_phases if not provided as argument
        if population_phases is None:
            population_phases = self.population_phases
            
        # Purge queues on startup
        print("\n🧹 Purging all queues...")
        self.job_queue.purge_all()
        
        # Calculate total max iterations for progress tracker
        if population_phases:
            total_max_iterations = sum(phase[0] for phase in population_phases)
            print(f"\n📋 POPULATION PHASES MODE:")
            print(f"   Total phases: {len(population_phases)}")
            for i, (iters, pop) in enumerate(population_phases, 1):
                print(f"   Phase {i}: {iters} iterations with max population {pop}")
            print(f"   Total max iterations: {total_max_iterations}")
        else:
            total_max_iterations = max_iterations
        
        # Initialize progress tracker
        from ui.progress_tracker import GAProgressTracker
        progress_tracker = GAProgressTracker(
            max_iterations=total_max_iterations,
            stagnation_limit=stagnant,
            population_phases=population_phases  # Pass phases for accurate ETA
        )
        progress_tracker.start()
        self.progress_tracker = progress_tracker  # Store for use in fitness calculation
        
        iteration = 0
        print("Starting genetic algorithm...")
        self.fitness_function_calculation()
        self.order_fitness_values(limited=True)

        try:
            if population_phases:
                # Multi-phase execution
                for phase_idx, (phase_iterations, phase_max_pop) in enumerate(population_phases, 1):
                    print(f"\n{'='*80}")
                    print(f"🔀 STARTING PHASE {phase_idx}/{len(population_phases)}")
                    print(f"   Iterations: {phase_iterations}, Max Population: {phase_max_pop}")
                    print(f"{'='*80}")
                    
                    # Adjust population size for this phase
                    self._adjust_population_size(phase_max_pop)
                    
                    phase_start_iteration = iteration
                    phase_end_iteration = iteration + phase_iterations
                    
                    while self.previous_population_iteration < stagnant and iteration < phase_end_iteration:
                        # Update progress tracker
                        progress_tracker.start_iteration(iteration + 1, self.previous_population_iteration)
                        
                        print(f"\n{'='*80}")
                        print(f"ITERATION {iteration + 1} (Phase {phase_idx}, Local iter {iteration - phase_start_iteration + 1}/{phase_iterations})")
                        print(f"Generation {self.current_generation + 1}, Stagnation: {self.previous_population_iteration}/{stagnant}")
                        print(f"Current population: {len(self.population)}")
                        print(f"{'='*80}")

                        self.tournament_selection()
                        self.uniform_crossover()
                        self.mutation()
                        self.current_generation += 1
                        self.survivor_selection()
                        self.order_fitness_values(limited=True)

                        if self.previous_population_ids == self.get_current_population_ids():
                            self.previous_population_iteration += 1
                        else:
                            self.previous_population_ids = self.get_current_population_ids()
                            self.previous_population_iteration = 0

                        iteration += 1
                        
                        # Mark iteration complete
                        progress_tracker.complete_iteration()
                    
                    # Check if we should stop early due to stagnation
                    if self.previous_population_iteration >= stagnant:
                        print(f"\n⚠️  Stagnation limit reached in phase {phase_idx}, stopping early")
                        break
                    
                    print(f"\n✅ Phase {phase_idx} completed")
            else:
                # Single-phase execution (original behavior)
                while self.previous_population_iteration < stagnant and iteration < max_iterations:
                    # Update progress tracker
                    progress_tracker.start_iteration(iteration + 1, self.previous_population_iteration)
                    
                    print(f"\n{'='*80}")
                    print(f"ITERATION {iteration + 1} (Generation {self.current_generation + 1})")
                    print(f"Stagnation count: {self.previous_population_iteration}/{stagnant}")
                    print(f"{'='*80}")

                    self.tournament_selection()
                    self.uniform_crossover()
                    self.mutation()
                    self.current_generation += 1
                    self.survivor_selection()
                    self.order_fitness_values(limited=True)

                    if self.previous_population_ids == self.get_current_population_ids():
                        self.previous_population_iteration += 1
                    else:
                        self.previous_population_ids = self.get_current_population_ids()
                        self.previous_population_iteration = 0

                    iteration += 1
                    
                    # Mark iteration complete
                    progress_tracker.complete_iteration()

        except KeyboardInterrupt:
            print("\n\n🛑 Interrupted by user!")
        finally:
            # Stop progress tracker
            progress_tracker.stop()

        print(f"\nAlgorithm completed after {iteration} iterations")
        print(f"Final stagnation count: {self.previous_population_iteration}")
        print(f"Total individuals evaluated: {len(self.evaluated_individuals)}")
        print(f"Total unique individuals: {len(self.all_individuals)}")
        
        self.renormalize_all_individuals()
        self.order_fitness_values(limited=False)

        best = min(self.population, key=lambda x: x.fitness if x.fitness is not None else float('inf'))
        
        # Close queue connection
        self.job_queue.close()
        
        return best
    
    def _adjust_population_size(self, target_size):
        """
        Adjust population size to target_size by adding or removing individuals.
        When shrinking, keeps the best individuals.
        When expanding, adds random variations of the best individuals.
        """
        current_size = len(self.population)
        
        if current_size == target_size:
            return
        
        if current_size > target_size:
            # Shrink population - keep best individuals
            print(f"   Shrinking population from {current_size} to {target_size}")
            sorted_pop = sorted(self.population, key=lambda x: x.fitness if x.fitness is not None else float('inf'))
            self.population = sorted_pop[:target_size]
            self.population_size = target_size
        else:
            # Expand population - add variations of best individuals
            print(f"   Expanding population from {current_size} to {target_size}")
            needed = target_size - current_size
            sorted_pop = sorted(self.population, key=lambda x: x.fitness if x.fitness is not None else float('inf'))
            
            # Use best individuals as templates
            for i in range(needed):
                template_idx = i % min(self.EXPANSION_TEMPLATE_POOL_SIZE, len(sorted_pop))  # Use top N or less
                template = sorted_pop[template_idx]
                
                # Create variation by mutation
                new_chromosome = self.mutate_permutation(
                    template.chromosome.copy(), 
                    mutation_rate=self.EXPANSION_MUTATION_RATE, 
                    num_mutations=self.EXPANSION_NUM_MUTATIONS
                )
                new_individual = Individual(
                    chromosome=new_chromosome,
                    generation=self.current_generation,
                    parents=[template.id]
                )
                self.population.append(new_individual)
                self.individual_names[new_individual.id] = new_individual.name
            
            self.population_size = target_size
            
            # Evaluate newly expanded individuals immediately to avoid counting them twice
            # in the next iteration's fitness calculation
            print(f"   Evaluating {needed} newly expanded individuals...")
            self.fitness_function_calculation()


if __name__ == "__main__":
    ga = GeneticAlgorithmSimulation(
        keyboard_file='data/keyboards/ansi_60_percent.json',
        text_file='data/text/raw/simple_wikipedia_dataset.txt',
        fitts_a=0.5,
        fitts_b=0.3,
        max_concurrent_processes=4,
        use_rabbitmq=True,
        is_worker=False
    )

    if not ga.is_worker:
        best_individual = ga.run(max_iterations=50, stagnant=10)

        print("\n" + "="*80)
        print("BEST INDIVIDUAL FOUND")
        print("="*80)
        print(f"Name: {best_individual.name}")
        print(f"Fitness: {best_individual.fitness:.6f}")
        print(f"Raw Distance: {best_individual.distance:.2f}")
        print(f"Raw Time: {best_individual.time_taken:.2f}")
        parent_names = [ga.get_individual_name(p) for p in best_individual.parents] if best_individual.parents else ["Initial"]
        print(f"Parents: {', '.join(parent_names)}")
        print(f"Layout: {''.join(best_individual.chromosome)}")
        print("="*80)
        
        print("\n" + "="*80)
        print("RUN STATISTICS")
        print("="*80)
        print(f"Total individuals evaluated: {len(ga.evaluated_individuals)}")
        print(f"Total unique individuals tracked: {len(ga.all_individuals)}")
        print(f"Final population size: {len(ga.population)}")
        print("="*80)
        
        import json
        with open('ga_all_individuals.json', 'w') as f:
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
        print("\nSaved all unique individuals to ga_all_individuals.json")
