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

        # Handle multi-layer chromosomes
        # Chromosome can be:
        # 1. Single list (legacy): ['a', 'b', 'c', ...]
        # 2. List of lists (multi-layer): [['a', 'b', 'c', ...], ['ă', 'â', 'î', ...], ...]
        if isinstance(chromosome, str):
            chromosome = [list(chromosome)]  # Wrap in layer
        elif isinstance(chromosome, list):
            if chromosome and isinstance(chromosome[0], list):
                # Already multi-layer format
                pass
            else:
                # Single layer - wrap it
                chromosome = [chromosome]
        
        # For now, only use the first layer (base layer) for remapping
        # TODO: Implement proper multi-layer remapping in Layout class
        qwerty_base = list(LAYOUT_DATA["qwerty"])
        base_layer = chromosome[0]
        evaluator.layout.remap(qwerty_base, base_layer)
        
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

    def __init__(self, chromosome, fitness=None, distance=None, time_taken=None, parents=None, generation=0, name=None, layer_modifiers=None):
        """
        Initialize an Individual with a chromosome that can be single or multi-layer.
        
        Args:
            chromosome: Can be:
                - Single list (legacy/single-layer): ['a', 'b', 'c', ...]
                - List of lists (multi-layer): [['a', 'b', 'c', ...], ['ă', 'â', 'î', ...], ...]
            layer_modifiers: Dict mapping layer index to modifier key(s) required to access it
                - Example: {1: 'AltGr', 2: 'Shift+AltGr'}
                - If None, defaults are assigned based on layer count
        """
        # Validate chromosome is not empty
        if not chromosome:
            raise ValueError("Chromosome cannot be empty")
        
        # Normalize chromosome to always be list of lists internally
        if len(chromosome) > 0 and isinstance(chromosome[0], list):
            # Already multi-layer
            self.chromosome = chromosome
        else:
            # Single layer - wrap in list
            self.chromosome = [chromosome]
        
        # Assign default modifier keys if not provided
        if layer_modifiers is None:
            self.layer_modifiers = self._assign_default_modifiers()
        else:
            self.layer_modifiers = layer_modifiers
        
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
    
    def _assign_default_modifiers(self):
        """
        Assign default modifier keys for accessing each layer.
        Layer 0 (base) has no modifier.
        Upper layers get standard modifier combinations.
        """
        modifiers = {}
        num_layers = len(self.chromosome)
        
        if num_layers > 1:
            modifiers[1] = 'AltGr'  # Standard for diacritics/special chars
        if num_layers > 2:
            modifiers[2] = 'Shift+AltGr'  # Second special layer
        if num_layers > 3:
            modifiers[3] = 'Ctrl+Alt'  # Third special layer
        
        return modifiers

    def get_layer_count(self):
        """Get number of layers in this individual's chromosome."""
        return len(self.chromosome)
    
    def get_layer(self, layer_idx):
        """Get a specific layer from the chromosome."""
        if layer_idx < len(self.chromosome):
            return self.chromosome[layer_idx]
        return None
    
    def get_modifier_for_layer(self, layer_idx):
        """Get the modifier key(s) required to access a specific layer."""
        if layer_idx == 0:
            return None  # Base layer has no modifier
        return self.layer_modifiers.get(layer_idx, None)
    
    def get_flattened_chromosome(self):
        """Get chromosome as flat structure (for backwards compatibility)."""
        if len(self.chromosome) == 1:
            return self.chromosome[0]
        return self.chromosome

    def __repr__(self):
        parent_names = [p if isinstance(p, str) else f"gen_{self.generation-1}-{p}" for p in self.parents] if self.parents else []
        layer_info = f", layers={len(self.chromosome)}"
        return f"Individual(name={self.name}, fitness={self.fitness:.6f if self.fitness else None}, distance={self.distance}, time={self.time_taken}{layer_info}, parents={parent_names})"


class GeneticAlgorithmSimulation:
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
                 num_layers=1,
                 max_layers=3,
                 language_layout=None,
                 mutation_rate=0.20,
                 layer_mutation_rate=0.15):
        """
        Initialize GA with C# fitness calculator.
        
        Args:
            is_worker: If True, runs in worker mode (processes jobs from queue)
                      If False, runs as master (coordinates GA and also processes jobs)
            num_layers: Initial number of layers for chromosomes (default: 1)
            max_layers: Maximum number of layers allowed (default: 3)
            language_layout: Module path for language layout remapping (e.g., 'data.languages.romanian_programmers')
            mutation_rate: Probability that an individual gets mutated (default: 0.20 = 20%)
            layer_mutation_rate: Probability of layer add/remove mutations (default: 0.15 = 15%)
        """
        self.is_worker = is_worker
        self.num_layers = num_layers
        self.max_layers = max_layers
        self.language_layout = language_layout
        self.mutation_rate = mutation_rate
        self.layer_mutation_rate = layer_mutation_rate
        
        if is_worker:
            print("="*80)
            print("🔧 WORKER MODE - Waiting for jobs from master...")
            print("="*80)
        else:
            print("="*80)
            print("👑 MASTER MODE - Coordinating GA and processing jobs...")
            print(f"  Initial layers: {num_layers}, Max layers: {max_layers}")
            print(f"  Mutation rate: {mutation_rate*100:.1f}%, Layer mutation: {layer_mutation_rate*100:.1f}%")
            if language_layout:
                print(f"  Language layout: {language_layout}")
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
    
    def get_language_layer_chars(self):
        """
        Extract character mappings from language layout for layer initialization.
        Returns dict mapping base character to AltGr character for layer 1.
        """
        if not self.language_layout:
            return {}
        
        try:
            import importlib
            module = importlib.import_module(self.language_layout)
            layout = module.get_layout()
            
            # Extract AltGr mappings for layer 1
            layer1_chars = {}
            if 'altgr_remaps' in layout:
                for base_char, altgr_tuple in layout['altgr_remaps'].items():
                    # altgr_tuple is (lowercase, uppercase)
                    # Use lowercase version for layer 1
                    if isinstance(altgr_tuple, tuple) and len(altgr_tuple) > 0:
                        layer1_chars[base_char] = altgr_tuple[0]
            
            return layer1_chars
        except Exception as e:
            print(f"Warning: Could not load language layout characters: {e}")
            return {}

    def population_initialization(self, size=50):
        """Initialize population (master only) with sparse multi-layer support"""
        if self.is_worker:
            return
            
        self.population = []
        
        # Get language layer character mappings (e.g., a->ă for Romanian)
        layer1_char_map = self.get_language_layer_chars()

        # Add heuristic layouts with sparse upper layers
        for layout_name, genotype in LAYOUT_DATA.items():
            # Create multi-layer chromosome
            # Layer 0: Fully populated with base layout
            chromosome = [list(genotype)]
            
            # Add additional layers if num_layers > 1
            if self.num_layers > 1:
                for layer_idx in range(1, self.num_layers):
                    # Create sparse layer (mostly None)
                    sparse_layer = [None] * len(genotype)
                    
                    # For layer 1, use language layout mappings if available
                    if layer_idx == 1 and layer1_char_map:
                        # Place AltGr characters at the same positions as their base chars
                        for pos, base_char in enumerate(genotype):
                            if base_char in layer1_char_map:
                                sparse_layer[pos] = layer1_char_map[base_char]
                        
                        diacritic_count = sum(1 for c in sparse_layer if c is not None)
                        print(f"  Layer 1 for {layout_name}: {diacritic_count} diacritics from language layout")
                    else:
                        # Other layers: seed with 1-5 random characters
                        num_seeds = random.randint(1, min(5, len(genotype) // 10))
                        seed_positions = random.sample(range(len(genotype)), num_seeds)
                        available_chars = list(genotype)
                        random.shuffle(available_chars)
                        
                        for i, pos in enumerate(seed_positions):
                            if i < len(available_chars):
                                sparse_layer[pos] = available_chars[i]
                    
                    chromosome.append(sparse_layer)
            
            individual = Individual(chromosome=chromosome, generation=0, name=layout_name)
            self.population.append(individual)
            self.individual_names[individual.id] = individual.name
            print(f"Added heuristic layout: {layout_name} with {len(chromosome)} layer(s)")

        print(f"Population initialized with {len(self.population)} heuristic individuals")

        if size > len(self.population):
            if self.population:
                # Use the base layer from first individual as template
                template_base_layer = self.population[0].chromosome[0]
                needed = size - len(self.population)
                print(f"Adding {needed} random individuals with {self.num_layers} layer(s)")

                for _ in range(needed):
                    # Create multi-layer chromosome
                    chromosome = []
                    
                    # Layer 0: Fully populated (shuffled base)
                    layer0 = template_base_layer.copy()
                    random.shuffle(layer0)
                    chromosome.append(layer0)
                    
                    # Upper layers: Sparse initialization
                    for layer_idx in range(1, self.num_layers):
                        sparse_layer = [None] * len(template_base_layer)
                        
                        # For layer 1, use language layout mappings if available
                        if layer_idx == 1 and layer1_char_map:
                            # Place AltGr characters at same positions as base chars
                            for pos, base_char in enumerate(layer0):
                                if base_char in layer1_char_map:
                                    sparse_layer[pos] = layer1_char_map[base_char]
                        else:
                            # Other layers: seed with few random characters
                            num_seeds = random.randint(1, min(5, len(template_base_layer) // 10))
                            seed_positions = random.sample(range(len(template_base_layer)), num_seeds)
                            available_chars = template_base_layer.copy()
                            random.shuffle(available_chars)
                            
                            for i, pos in enumerate(seed_positions):
                                if i < len(available_chars):
                                    sparse_layer[pos] = available_chars[i]
                        
                        chromosome.append(sparse_layer)
                    
                    individual = Individual(chromosome=chromosome, generation=0)
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
        """Uniform crossover - create children from parent pairs with multi-layer support"""
        self.children = []

        def is_duplicate(chromosome, existing_individuals):
            """Check if chromosome is duplicate - works with multi-layer"""
            # Validate chromosome is not empty
            if not chromosome or len(chromosome) == 0:
                return False
            
            # Convert to string representation for comparison
            # Handle None values in sparse layers by converting to placeholder
            if isinstance(chromosome[0], list):
                # Multi-layer - convert None to ∅ for comparison
                chromosome_str = '|'.join([''.join(str(g) if g is not None else '∅' for g in layer) for layer in chromosome])
            else:
                # Single layer (shouldn't happen but handle it)
                chromosome_str = ''.join(str(g) if g is not None else '∅' for g in chromosome)
            
            for individual in existing_individuals:
                ind_chrom = individual.chromosome
                if not ind_chrom or len(ind_chrom) == 0:
                    continue
                    
                if isinstance(ind_chrom[0], list):
                    # Multi-layer - convert None to ∅ for comparison
                    ind_str = '|'.join([''.join(str(g) if g is not None else '∅' for g in layer) for layer in ind_chrom])
                else:
                    ind_str = ''.join(str(g) if g is not None else '∅' for g in ind_chrom)
                
                if ind_str == chromosome_str:
                    return True
            return False
        
        def crossover_single_layer(parent0_layer, parent1_layer, bias):
            """Perform crossover on a single layer"""
            new_layer = [None] * len(parent0_layer)

            # First pass: take from parent0 with bias
            for j in range(len(new_layer)):
                if random.random() < bias:
                    new_layer[j] = parent0_layer[j]

            # Second pass: fill from parent1 where not duplicate
            for j in range(len(new_layer)):
                if new_layer[j] is None and parent1_layer[j] not in new_layer:
                    new_layer[j] = parent1_layer[j]

            # Third pass: fill remaining from parent0 where not duplicate
            for j in range(len(new_layer)):
                if new_layer[j] is None and parent0_layer[j] not in new_layer:
                    new_layer[j] = parent0_layer[j]

            # Fourth pass: fill any remaining gaps with missing genes
            # For sparse layers, we allow None to remain in the child
            existing_genes = set(gene for gene in new_layer if gene is not None)
            # Filter out None from parent genes (for sparse layers)
            # Combine genes from both parents to avoid losing genes unique to parent1
            all_possible_genes = set(gene for gene in parent0_layer + parent1_layer if gene is not None)
            missing_genes = list(all_possible_genes - existing_genes)
            random.shuffle(missing_genes)

            # Fill remaining None positions only if we have missing genes
            for j in range(len(new_layer)):
                if new_layer[j] is None and len(missing_genes) > 0:
                    new_layer[j] = missing_genes.pop(0)
            # Note: Some positions may remain None for sparse layers
            
            return new_layer

        if len(self.parents) < 2:
            print(f"Warning: Not enough parents. Have {len(self.parents)} parents.")
            return

        sorted_parents = sorted(self.parents, key=lambda x: x.fitness if x.fitness is not None else float('inf'))
        num_pairs = len(sorted_parents) // 2
        target_children = len(self.population)
        
        crossover_failures = 0
        mutated_clones_created = 0
        
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
                child_created = False

                while attempts < max_attempts:
                    # Perform layer-to-layer crossover
                    new_chromosome = []
                    bias = 0.75 + o/30.0
                    
                    # Crossover each layer independently, handling different layer counts
                    max_layers = max(len(parent0.chromosome), len(parent1.chromosome))
                    for layer_idx in range(max_layers):
                        # If parent has this layer, use it; otherwise use None placeholder
                        parent0_layer = parent0.chromosome[layer_idx] if layer_idx < len(parent0.chromosome) else None
                        parent1_layer = parent1.chromosome[layer_idx] if layer_idx < len(parent1.chromosome) else None
                        
                        # If both parents have this layer, crossover
                        if parent0_layer is not None and parent1_layer is not None:
                            new_layer = crossover_single_layer(parent0_layer, parent1_layer, bias)
                            new_chromosome.append(new_layer)
                        # If only one parent has this layer, inherit with 50% probability
                        elif parent0_layer is not None:
                            if random.random() < 0.5:
                                new_chromosome.append(parent0_layer[:])  # Copy layer
                        elif parent1_layer is not None:
                            if random.random() < 0.5:
                                new_chromosome.append(parent1_layer[:])  # Copy layer
                    
                    # Ensure child has at least one layer (base layer from better parent)
                    if len(new_chromosome) == 0:
                        better_parent = parent0 if parent0.fitness < parent1.fitness else parent1
                        if len(better_parent.chromosome) > 0:
                            new_chromosome.append(better_parent.chromosome[0][:])

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
                        child_created = True
                        break
                    else:
                        attempts += 1
                
                # If crossover failed, create a mutated clone as fallback
                if not child_created and len(self.children) < target_children:
                    crossover_failures += 1
                    # Pick the better parent and create a mutated clone
                    better_parent = parent0 if parent0.fitness < parent1.fitness else parent1
                    clone_chromosome = [layer.copy() for layer in better_parent.chromosome]
                    
                    # Apply multiple mutations to ensure it's different
                    for _ in range(3):
                        layer_idx = random.randint(0, len(clone_chromosome) - 1)
                        layer = clone_chromosome[layer_idx]
                        non_none_positions = [i for i, k in enumerate(layer) if k is not None]
                        if len(non_none_positions) >= 2:
                            pos1, pos2 = random.sample(non_none_positions, 2)
                            layer[pos1], layer[pos2] = layer[pos2], layer[pos1]
                    
                    child = Individual(
                        chromosome=clone_chromosome,
                        fitness=None,
                        distance=None,
                        time_taken=None,
                        parents=[better_parent.id],
                        generation=self.current_generation + 1
                    )
                    self.children.append(child)
                    self.individual_names[child.id] = child.name
                    mutated_clones_created += 1
            
            if len(self.children) >= target_children:
                break

        if crossover_failures > 0:
            print(f"Created {len(self.children)} unique children (target: {target_children}) - {crossover_failures} crossover failures, {mutated_clones_created} mutated clones")

    def mutation(self):
        """Mutate children with 7 mutation strategies"""
        for individual in self.children:
            # Apply standard mutations with configurable probability
            if random.random() < self.mutation_rate:
                mutation_type = random.choices(
                    ['intra_layer_swap', 'cross_layer_swap', 'populate_none', 
                     'safe_replace', 'relocate_replace', 'layer_promotion'],
                    weights=[0.30, 0.20, 0.25, 0.10, 0.05, 0.10]
                )[0]
                
                if mutation_type == 'intra_layer_swap':
                    self.mutate_intra_layer_swap(individual)
                elif mutation_type == 'cross_layer_swap':
                    self.mutate_cross_layer_swap(individual)
                elif mutation_type == 'populate_none':
                    self.mutate_populate_none(individual)
                elif mutation_type == 'safe_replace':
                    self.mutate_safe_replace(individual)
                elif mutation_type == 'relocate_replace':
                    self.mutate_relocate_replace(individual)
                elif mutation_type == 'layer_promotion':
                    self.mutate_layer_promotion(individual)
            
            # Layer addition as separate pass with higher effective probability
            # Direct probability: mutation_rate * exponential_decay
            # Layer 2: 20% * 5% = 1%, Layer 3: 20% * 2.5% = 0.5%, Layer 4: 20% * 1.25% = 0.25%
            if random.random() < self.mutation_rate:
                self.add_layer_mutation_exponential(individual)
            
            # Layer removal with configurable probability
            if len(individual.chromosome) > 1 and random.random() < (self.layer_mutation_rate * 0.1):
                self.remove_layer_mutation(individual)
            
            # Validate after mutations
            self.validate_chromosome(individual)
    
    def mutate_intra_layer_swap(self, individual):
        """Type 1: Swap two keys within the same layer (30%)"""
        if not individual.chromosome:
            return
        
        layer_idx = random.randint(0, len(individual.chromosome) - 1)
        layer = individual.chromosome[layer_idx]
        
        # Find non-None positions
        non_none_positions = [i for i, k in enumerate(layer) if k is not None]
        if len(non_none_positions) < 2:
            return
        
        pos1, pos2 = random.sample(non_none_positions, 2)
        layer[pos1], layer[pos2] = layer[pos2], layer[pos1]
    
    def mutate_cross_layer_swap(self, individual):
        """Type 2: Swap keys at SAME position across different layers (20%)"""
        if len(individual.chromosome) < 2:
            return
        
        pos = random.randint(0, len(individual.chromosome[0]) - 1)
        layer1_idx, layer2_idx = random.sample(range(len(individual.chromosome)), 2)
        
        layer1 = individual.chromosome[layer1_idx]
        layer2 = individual.chromosome[layer2_idx]
        
        layer1[pos], layer2[pos] = layer2[pos], layer1[pos]
    
    def mutate_populate_none(self, individual):
        """Type 3: Add key to None position (25%, higher if many None values)"""
        if len(individual.chromosome) < 2:
            return
        
        # Focus on upper layers (not base layer)
        layer_idx = random.randint(1, len(individual.chromosome) - 1)
        layer = individual.chromosome[layer_idx]
        
        none_positions = [i for i, k in enumerate(layer) if k is None]
        if not none_positions:
            return
        
        pos = random.choice(none_positions)
        
        # Get available characters from base layer
        base_layer = individual.chromosome[0]
        available_chars = [c for c in base_layer if c is not None and c not in layer]
        
        if available_chars:
            layer[pos] = random.choice(available_chars)
    
    def mutate_safe_replace(self, individual):
        """Type 4: Replace key ONLY if at least 1 copy remains elsewhere (10%)"""
        if not individual.chromosome:
            return
        
        layer_idx = random.randint(0, len(individual.chromosome) - 1)
        layer = individual.chromosome[layer_idx]
        
        non_none_positions = [i for i, k in enumerate(layer) if k is not None]
        if not non_none_positions:
            return
        
        pos = random.choice(non_none_positions)
        old_key = layer[pos]
        
        # Count occurrences across all layers
        total_count = sum(l.count(old_key) for l in individual.chromosome if l is not None)
        
        if total_count > 1:  # Safe to replace
            base_layer = individual.chromosome[0]
            available_chars = [c for c in base_layer if c is not None]
            if available_chars:
                layer[pos] = random.choice(available_chars)
    
    def mutate_relocate_replace(self, individual):
        """Type 5: Replace key but move it to random None position first (5%)"""
        if not individual.chromosome:
            return
        
        layer_idx = random.randint(0, len(individual.chromosome) - 1)
        layer = individual.chromosome[layer_idx]
        
        non_none_positions = [i for i, k in enumerate(layer) if k is not None]
        if not non_none_positions:
            return
        
        pos = random.choice(non_none_positions)
        old_key = layer[pos]
        
        # Find empty slots in any layer
        empty_slots = []
        for l_idx, l in enumerate(individual.chromosome):
            for p_idx, k in enumerate(l):
                if k is None:
                    empty_slots.append((l_idx, p_idx))
        
        if empty_slots:
            new_layer_idx, new_pos = random.choice(empty_slots)
            individual.chromosome[new_layer_idx][new_pos] = old_key
            
            # Replace with new character
            base_layer = individual.chromosome[0]
            available_chars = [c for c in base_layer if c is not None]
            if available_chars:
                layer[pos] = random.choice(available_chars)
    
    def mutate_layer_promotion(self, individual):
        """Type 6: Swap high-frequency key from upper layer with low-frequency from base (5%)"""
        if len(individual.chromosome) < 2:
            return
        
        # Simple heuristic: swap random keys between base and upper layer
        base_layer = individual.chromosome[0]
        upper_layer_idx = random.randint(1, len(individual.chromosome) - 1)
        upper_layer = individual.chromosome[upper_layer_idx]
        
        # Find non-None positions in both layers
        base_positions = [i for i, k in enumerate(base_layer) if k is not None]
        upper_positions = [i for i, k in enumerate(upper_layer) if k is not None]
        
        if base_positions and upper_positions:
            base_pos = random.choice(base_positions)
            upper_pos = random.choice(upper_positions)
            base_layer[base_pos], upper_layer[upper_pos] = upper_layer[upper_pos], base_layer[base_pos]
    
    def add_layer_mutation_exponential(self, individual):
        """Type 7: Add new sparse layer with exponentially decreasing probability
        
        Also attempts to place a modifier key on the base layer to access the new layer.
        If the modifier key would replace an indispensable key, that key is moved to the new layer.
        """
        if not individual.chromosome or len(individual.chromosome) == 0:
            return
        
        current_layers = len(individual.chromosome)
        
        # Only if under max_layers
        if current_layers >= self.max_layers:
            return
        
        # Exponential decay probability: 5% / (2^(n-1))
        # Layer 2: 5%, Layer 3: 2.5%, Layer 4: 1.25%
        probability = 0.05 / (2 ** (current_layers - 1))
        
        if random.random() < probability:
            base_layer = individual.chromosome[0]
            
            # Create sparse new layer (mostly None)
            new_layer = [None] * len(base_layer)
            
            # Try to find a position for the layer modifier key on base layer
            # Prefer positions with less important keys (not letters)
            letter_positions = []
            non_letter_positions = []
            
            for i, char in enumerate(base_layer):
                if char is not None:
                    if char.isalpha():
                        letter_positions.append(i)
                    else:
                        non_letter_positions.append(i)
            
            # Attempt to place modifier on a non-letter key position
            modifier_position = None
            replaced_key = None
            
            if non_letter_positions:
                # Prefer replacing non-letter keys
                modifier_position = random.choice(non_letter_positions)
                replaced_key = base_layer[modifier_position]
            elif letter_positions:
                # If no non-letter positions, use a letter position
                modifier_position = random.choice(letter_positions)
                replaced_key = base_layer[modifier_position]
            
            # If we found a position and replaced a key, move that key to the new layer
            if modifier_position is not None and replaced_key is not None:
                # Move the replaced key to the new layer at the same position
                new_layer[modifier_position] = replaced_key
                # Mark base layer position as having a modifier (using a special marker)
                # Note: In actual implementation, the modifier is metadata, not in the chromosome
                # The chromosome position could remain the same or be marked differently
            
            # Seed new layer with 1-3 additional random characters
            num_seeds = random.randint(1, 3)
            available_positions = [i for i in range(len(base_layer)) if new_layer[i] is None]
            if available_positions:
                seed_positions = random.sample(available_positions, min(num_seeds, len(available_positions)))
                available_chars = [c for c in base_layer if c is not None]
                random.shuffle(available_chars)
                
                for i, pos in enumerate(seed_positions):
                    if i < len(available_chars):
                        new_layer[pos] = available_chars[i]
            
            individual.chromosome.append(new_layer)
            
            # Assign modifier key for the new layer
            new_layer_idx = len(individual.chromosome) - 1
            if new_layer_idx == 1:
                individual.layer_modifiers[new_layer_idx] = 'AltGr'
            elif new_layer_idx == 2:
                individual.layer_modifiers[new_layer_idx] = 'Shift+AltGr'
            elif new_layer_idx == 3:
                individual.layer_modifiers[new_layer_idx] = 'Ctrl+Alt'
            
            modifier = individual.layer_modifiers.get(new_layer_idx, '?')
            if modifier_position is not None and replaced_key is not None:
                print(f"  ➕ Added sparse layer {new_layer_idx} to {individual.name}: now has {len(individual.chromosome)} layers (accessed via {modifier}, moved '{replaced_key}' to new layer)")
            else:
                print(f"  ➕ Added sparse layer {new_layer_idx} to {individual.name}: now has {len(individual.chromosome)} layers (accessed via {modifier})")
    
    def remove_layer_mutation(self, individual):
        """Remove a layer from an individual's chromosome (never remove base layer)"""
        # Guard: never remove if only 1 or 0 layers
        if not individual.chromosome or len(individual.chromosome) <= 1:
            return
        
        # Remove a random layer (but not the base layer 0)
        layer_to_remove = random.randint(1, len(individual.chromosome) - 1)
        del individual.chromosome[layer_to_remove]
        
        # Remove modifier assignment for removed layer
        if layer_to_remove in individual.layer_modifiers:
            del individual.layer_modifiers[layer_to_remove]
        
        # Renumber modifiers for layers above the removed one
        new_modifiers = {}
        for layer_idx, modifier in individual.layer_modifiers.items():
            if layer_idx < layer_to_remove:
                new_modifiers[layer_idx] = modifier
            elif layer_idx > layer_to_remove:
                new_modifiers[layer_idx - 1] = modifier
        individual.layer_modifiers = new_modifiers
        
        print(f"  ➖ Removed layer {layer_to_remove} from {individual.name}: now has {len(individual.chromosome)} layers")
    
    def validate_chromosome(self, individual):
        """Ensure chromosome is always valid"""
        if not individual.chromosome or len(individual.chromosome) == 0:
            return
        
        base_layer = individual.chromosome[0]
        
        # Rule 1: Base layer must not be entirely None
        non_none_in_base = [k for k in base_layer if k is not None]
        if len(non_none_in_base) < len(base_layer) // 2:
            # Too many None values in base layer - this shouldn't happen
            # Fill with available characters
            all_chars = set()
            for layer in individual.chromosome:
                for char in layer:
                    if char is not None:
                        all_chars.add(char)
            
            if all_chars:
                for i in range(len(base_layer)):
                    if base_layer[i] is None:
                        base_layer[i] = random.choice(list(all_chars))
        
        # Rule 2: Ensure no duplicate non-None values within same layer
        for layer_idx, layer in enumerate(individual.chromosome):
            non_none_chars = [c for c in layer if c is not None]
            if len(non_none_chars) != len(set(non_none_chars)):
                # Has duplicates - remove them
                seen = set()
                for i in range(len(layer)):
                    if layer[i] is not None:
                        if layer[i] in seen:
                            layer[i] = None  # Clear duplicate
                        else:
                            seen.add(layer[i])

    def survivor_selection(self):
        """Elitist survivor selection with individual tracking"""
        self.fitness_function_calculation()
        combined = self.population + self.children
        sorted_combined = sorted(combined, key=lambda x: x.fitness if x.fitness is not None else float('inf'))
        
        for ind in sorted_combined:
            if ind.id not in self.all_individuals:
                # Serialize multi-layer chromosome properly (handle None values)
                if isinstance(ind.chromosome[0], list):
                    # Multi-layer: serialize as list of joined strings, replace None with placeholder
                    chromosome_serialized = []
                    for layer in ind.chromosome:
                        layer_str = ''.join(c if c is not None else '∅' for c in layer)
                        chromosome_serialized.append(layer_str)
                else:
                    # Single layer (shouldn't happen but handle it)
                    chromosome_serialized = [''.join(c if c is not None else '∅' for c in ind.chromosome)]
                
                self.all_individuals[ind.id] = {
                    'id': ind.id,
                    'name': ind.name,
                    'generation': ind.generation,
                    'chromosome': chromosome_serialized,
                    'num_layers': len(ind.chromosome),
                    'layer_modifiers': ind.layer_modifiers,
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

    def run(self, max_iterations=100, stagnant=15):
        """Run genetic algorithm (master only)"""
        if self.is_worker:
            return None
            
        # Purge queues on startup
        print("\n🧹 Purging all queues...")
        self.job_queue.purge_all()
        
        # Initialize progress tracker
        from ui.progress_tracker import GAProgressTracker
        progress_tracker = GAProgressTracker(
            max_iterations=max_iterations,
            stagnation_limit=stagnant
        )
        progress_tracker.start()
        self.progress_tracker = progress_tracker  # Store for use in fitness calculation
        
        iteration = 0
        print("Starting genetic algorithm...")
        self.fitness_function_calculation()
        self.order_fitness_values(limited=True)

        try:
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
        
        # Store actual iterations executed
        self.actual_iterations = iteration
        
        # Close queue connection
        self.job_queue.close()
        
        return best


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
        print(f"Layers: {len(best_individual.chromosome)}")
        parent_names = [ga.get_individual_name(p) for p in best_individual.parents] if best_individual.parents else ["Initial"]
        print(f"Parents: {', '.join(parent_names)}")
        
        # Print each layer (handle None values)
        for layer_idx, layer in enumerate(best_individual.chromosome):
            layer_str = ''.join(c if c is not None else '∅' for c in layer)
            none_count = sum(1 for c in layer if c is None)
            utilization = ((len(layer) - none_count) / len(layer)) * 100 if layer else 0
            modifier = best_individual.get_modifier_for_layer(layer_idx)
            if modifier:
                print(f"Layer {layer_idx} ({modifier}): {layer_str} ({utilization:.1f}% utilized)")
            else:
                print(f"Layer {layer_idx}: {layer_str} ({utilization:.1f}% utilized)")
        print("="*80)
        
        print("\n" + "="*80)
        print("RUN STATISTICS")
        print("="*80)
        print(f"Total individuals evaluated: {len(ga.evaluated_individuals)}")
        print(f"Total unique individuals tracked: {len(ga.all_individuals)}")
        print(f"Final population size: {len(ga.population)}")
        print("="*80)
        
        import json
        
        # Serialize chromosome properly (handle None values)
        if isinstance(best_individual.chromosome[0], list):
            chromosome_serialized = []
            for layer in best_individual.chromosome:
                layer_str = ''.join(c if c is not None else '∅' for c in layer)
                chromosome_serialized.append(layer_str)
        else:
            chromosome_serialized = [''.join(c if c is not None else '∅' for c in best_individual.chromosome)]
        
        with open('ga_all_individuals.json', 'w') as f:
            json.dump({
                'all_individuals': list(ga.all_individuals.values()),
                'best_individual': {
                    'id': best_individual.id,
                    'name': best_individual.name,
                    'fitness': best_individual.fitness,
                    'distance': best_individual.distance,
                    'time_taken': best_individual.time_taken,
                    'chromosome': chromosome_serialized,
                    'num_layers': len(best_individual.chromosome),
                    'layer_modifiers': best_individual.layer_modifiers,
                    'generation': best_individual.generation,
                    'parents': best_individual.parents
                }
            }, f, indent=2)
        print("\nSaved all unique individuals to ga_all_individuals.json")
