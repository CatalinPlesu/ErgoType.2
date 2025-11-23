from contextlib import redirect_stdout
from concurrent.futures import ProcessPoolExecutor, as_completed
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
from src.core.keyboard import Serial
from src.core.evaluator import Evaluator
from src.config.config import Config
import os
import pickle
import random
import sys
import multiprocessing as mp
import time


class Individual:
    _next_id = 0

    def __init__(self, chromosome, fitness=None, parents=None, generation=0, name=None):
        self.chromosome = chromosome
        self.fitness = fitness
        self.id = Individual._next_id
        Individual._next_id += 1
        self.parents = parents or []
        self.generation = generation
        # Generate name if not provided
        if name is None:
            self.name = f"gen_{generation}-{self.id}"
        else:
            self.name = name

    def __repr__(self):
        parent_names = [p if isinstance(p, str) else f"gen_{self.generation-1}-{p}" for p in self.parents] if self.parents else []
        return f"Individual(name={self.name}, fitness={self.fitness:.6f if self.fitness else None}, parents={parent_names})"


class GeneticAlgorithm:
    def __init__(self, keyboard_file='src/data/keyboards/ansi_60_percent.json',
                 dataset_file='src/data/text/processed/frequency_analysis.pkl',
                 dataset_name='simple_wikipedia'):
        """Initialize GA with evaluator"""
        print("Initializing Genetic Algorithm...")

        # Store file paths for parallel evaluators
        self.keyboard_file = keyboard_file
        self.dataset_file = dataset_file
        self.dataset_name = dataset_name

        # Initialize evaluator
        self.evaluator = Evaluator(debug=False)
        self.evaluator.load_keyoard(keyboard_file)
        self.evaluator.load_distance()
        self.evaluator.load_layout()
        self.evaluator.load_dataset(
            dataset_file=dataset_file, dataset_name=dataset_name)
        self.evaluator.load_typer()

        print("Evaluator initialized successfully")

        # Track current generation
        self.current_generation = 0
        # Map to track individual names by ID
        self.individual_names = {}
        
        # Track min/max values across all generations for normalization
        self.min_distance = float('inf')
        self.max_distance = float('-inf')
        self.min_time = float('inf')
        self.max_time = float('-inf')

        self.population_initialization()

        # Determine optimal number of processes
        self.num_processes = mp.cpu_count()
        print(f"Using {self.num_processes} processes for parallel evaluation")

    def population_initialization(self, size=50):
        """Initialize population with heuristic layouts and random permutations"""
        self.population = []

        # Add heuristic individuals with their actual layout names
        for layout_name, genotype in LAYOUT_DATA.items():
            individual = Individual(
                chromosome=list(genotype),
                generation=0,
                name=layout_name  # Use actual layout name
            )
            self.population.append(individual)
            self.individual_names[individual.id] = individual.name
            print(f"Added heuristic layout: {layout_name}")

        print(f"Population initialized with {len(self.population)} heuristic individuals")

        # Add random individuals if needed
        if size > len(self.population):
            if self.population:
                template_genotype = self.population[0].chromosome
                needed = size - len(self.population)
                print(f"Adding {needed} random individuals")

                for _ in range(needed):
                    shuffled_clone = template_genotype.copy()
                    random.shuffle(shuffled_clone)
                    individual = Individual(
                        chromosome=shuffled_clone,
                        generation=0
                    )
                    self.population.append(individual)
                    self.individual_names[individual.id] = individual.name

        self.previous_population_ids = self.get_current_population_ids()
        self.previous_population_iteration = 0
        self.evaluated_individuals = []  # Track all evaluated individuals
        print(f"Total population size: {len(self.population)}")

    def get_current_population_ids(self):
        """Get list of current population IDs"""
        return [ind.id for ind in self.population]

    def get_individual_name(self, individual_id):
        """Get the name of an individual by ID"""
        return self.individual_names.get(individual_id, f"unknown-{individual_id}")

    def evaluate_individual_fitness(self, individual):
        """Evaluate fitness for a single individual using process-based parallelism"""
        try:
            # Record start time for timing metadata
            start_time = time.time()
            
            # Create evaluator for this process
            evaluator = Evaluator(debug=False)
            evaluator.load_keyoard(self.keyboard_file)
            evaluator.load_distance()
            evaluator.load_layout()
            evaluator.load_dataset(
                dataset_file=self.dataset_file,
                dataset_name=self.dataset_name
            )
            evaluator.load_typer()

            # Remap layout to individual's chromosome
            from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
            evaluator.layout.remap(LAYOUT_DATA["qwerty"], individual.chromosome)
            
            # Recreate typer with the updated layout
            evaluator.load_typer()

            # Calculate fitness
            fitness_result = evaluator.get_fitness()
            
            # Handle different fitness result formats
            if isinstance(fitness_result, dict):
                # Legacy fitness format
                distance = fitness_result.get('distance_score', 0)
                time_component = fitness_result.get('ngram_score', 0) * 100  # Scale up
                fitness = distance + time_component
                
            elif isinstance(fitness_result, tuple) and len(fitness_result) == 2:
                # Simplified fitness format (distance, time)
                distance, time_component = fitness_result
                
                # For now, just use raw values - normalization will be done later
                fitness = distance + time_component
            else:
                # Fallback
                fitness = float(fitness_result) if fitness_result is not None else float('inf')
                distance = fitness
                time_component = 0

            # Check for cached result
            cache_hit = hasattr(evaluator, 'fitness_cache') and evaluator.fitness_cache is not None
            cached = False
            if hasattr(evaluator, '_get_cached_fitness'):
                # This would need to be implemented in evaluator to detect cache hits
                pass

            # Record timing metadata
            calculation_time = time.time() - start_time
            
            # Return fitness result with metadata
            return individual.id, {
                'fitness': fitness,
                'distance': distance,
                'time': time_component,
                'calculation_time': calculation_time,
                'from_cache': cached,
                'start_time': start_time
            }
            
        except Exception as e:
            print(f"Error evaluating {individual.name}: {e}")
            return individual.id, {
                'fitness': float('inf'),
                'distance': float('inf'),
                'time': float('inf'),
                'calculation_time': 0,
                'from_cache': False,
                'start_time': time.time()
            }

    def fitness_function_calculation(self):
        """Calculate fitness for all individuals without fitness values using process-based parallelism"""
        individuals_to_evaluate = [
            ind for ind in self.population if ind.fitness is None]

        if hasattr(self, 'children'):
            individuals_to_evaluate.extend(
                [child for child in self.children if child.fitness is None])

        if not individuals_to_evaluate:
            return

        print(f"Evaluating {len(individuals_to_evaluate)} individuals in parallel using {self.num_processes} processes...")
        
        # Start timing
        start_time = time.time()

        # Use ProcessPoolExecutor for process-based parallel execution
        with ProcessPoolExecutor(max_workers=self.num_processes) as executor:
            # Submit all evaluation tasks
            future_to_individual = {
                executor.submit(self.evaluate_individual_fitness, ind): ind
                for ind in individuals_to_evaluate
            }

            # Process completed evaluations as they finish
            completed_count = 0
            last_status_time = time.time()
            last_progress_print = time.time()
            
            for future in as_completed(future_to_individual):
                try:
                    individual_id, result = future.result()
                    
                    # Find the individual by ID and set its fitness
                    for ind in individuals_to_evaluate:
                        if ind.id == individual_id:
                            # Set fitness value
                            if isinstance(result, dict):
                                ind.fitness = result['fitness']
                                # Store timing metadata
                                if not hasattr(ind, 'timing_metadata'):
                                    ind.timing_metadata = {}
                                ind.timing_metadata.update({
                                    'calculation_time': result['calculation_time'],
                                    'from_cache': result.get('from_cache', False),
                                    'distance': result.get('distance', 0),
                                    'time_component': result.get('time', 0),
                                    'start_time': result.get('start_time', 0)
                                })
                            elif isinstance(result, tuple) and len(result) == 2:
                                # Simplified fitness format: (distance, time)
                                distance, time_component = result
                                # Apply simplified fitness formula - just use raw values for now
                                # Normalization will be done after all evaluations
                                fitness = (Config.fitness.distance_weight * distance + 
                                          Config.fitness.time_weight * time_component)
                                ind.fitness = fitness
                                
                                # Store timing metadata
                                if not hasattr(ind, 'timing_metadata'):
                                    ind.timing_metadata = {}
                                
                                # Set start_time if not already set (for simplified fitness)
                                current_time = time.time()
                                if 'start_time' not in ind.timing_metadata:
                                    ind.timing_metadata['start_time'] = current_time
                                
                                ind.timing_metadata.update({
                                    'calculation_time': current_time - ind.timing_metadata['start_time'],
                                    'from_cache': False,
                                    'distance': distance,
                                    'time_component': time_component
                                })
                            else:
                                # Fallback for legacy format
                                ind.fitness = result
                                if not hasattr(ind, 'timing_metadata'):
                                    ind.timing_metadata = {}
                                ind.timing_metadata['calculation_time'] = time.time() - (ind.timing_metadata.get('start_time', time.time()))
                            
                            # Add to evaluated individuals if not already there
                            if ind not in self.evaluated_individuals:
                                self.evaluated_individuals.append(ind)
                            break
                    completed_count += 1

                    # Print status updates only once per minute to avoid flicker
                    current_time = time.time()
                    time_since_last_print = current_time - last_progress_print
                    
                    # Only print when 20%, 40%, 60%, 80%, 100% complete, or every minute
                    progress_milestones = [0.2, 0.4, 0.6, 0.8, 1.0]
                    target_completed = [int(milestone * len(individuals_to_evaluate)) for milestone in progress_milestones]
                    
                    should_print = (time_since_last_print >= 60) or (completed_count in target_completed)
                    
                    if should_print:
                        # No screen clearing - just print progress update
                        
                        elapsed = current_time - start_time
                        avg_time_per_eval = elapsed / completed_count if completed_count > 0 else 0
                        progress_pct = (completed_count / len(individuals_to_evaluate)) * 100
                        
                        # Estimate remaining time (accounting for parallel processing)
                        if completed_count > 0:
                            # Calculate effective throughput (individuals per second across all processes)
                            effective_throughput = completed_count / elapsed
                            
                            # Remaining individuals to process
                            remaining_individuals = len(individuals_to_evaluate) - completed_count
                            
                            # Time to process remaining individuals (with parallel processing)
                            if effective_throughput > 0:
                                remaining = remaining_individuals / effective_throughput
                                total_estimated = len(individuals_to_evaluate) / effective_throughput
                            else:
                                remaining = float('inf')
                                total_estimated = float('inf')
                            
                            # Calculate estimated time for all iterations
                            total_generations = getattr(self, 'max_generations', 100)
                            current_generation = getattr(self, 'current_generation', 0) + 1
                            remaining_generations = total_generations - current_generation
                            
                            # For all iterations, assume similar timing per iteration
                            estimated_time_per_iteration = total_estimated
                            total_estimated_all_iterations = estimated_time_per_iteration * total_generations
                            elapsed_all_iterations = elapsed * current_generation
                            remaining_all_iterations = total_estimated_all_iterations - elapsed_all_iterations
                        else:
                            remaining = float('inf')
                            total_estimated = float('inf')
                            total_estimated_all_iterations = float('inf')
                            elapsed_all_iterations = 0
                            remaining_all_iterations = float('inf')
                        
                        # Format time nicely
                        def format_time(seconds):
                            if seconds >= 3600:
                                hours = int(seconds // 3600)
                                minutes = int((seconds % 3600) // 60)
                                return f"{hours}h {minutes}m"
                            elif seconds >= 60:
                                minutes = int(seconds // 60)
                                secs = int(seconds % 60)
                                return f"{minutes}m {secs}s"
                            else:
                                return f"{seconds:.1f}s"
                        
                        # Create progress bar
                        bar_length = 40
                        filled_length = int(bar_length * progress_pct // 100)
                        bar = '█' * filled_length + '-' * (bar_length - filled_length)
                        
                        print("=" * 60)
                        print("GENETIC ALGORITHM - FITNESS EVALUATION")
                        print("=" * 60)
                        print(f"Iteration: {getattr(self, 'current_generation', 0) + 1}/{getattr(self, 'max_generations', 100)}")
                        print(f"Population Size: {len(individuals_to_evaluate)}")
                        print(f"Processes: {self.num_processes}")
                        print()
                        print(f"Progress: [{bar}] {progress_pct:.1f}%")
                        print(f"Processed: {completed_count}/{len(individuals_to_evaluate)} individuals")
                        print(f"Status: {'COMPLETED' if completed_count == len(individuals_to_evaluate) else 'RUNNING'}")
                        print()
                        print(f"Timing:")
                        print(f"  This Iteration:")
                        print(f"    Elapsed: {format_time(elapsed)}")
                        print(f"    Remaining: {format_time(remaining)}")
                        print(f"    Total Estimated: {format_time(total_estimated)}")
                        print(f"    Per Individual: {avg_time_per_eval:.3f}s")
                        if total_generations > 1:
                            print(f"  All Iterations:")
                            print(f"    Elapsed: {format_time(elapsed_all_iterations)}")
                            print(f"    Remaining: {format_time(remaining_all_iterations)}")
                            print(f"    Total Estimated: {format_time(total_estimated_all_iterations)}")
                        print()
                        
                        # Show cache hit rate if available
                        cache_hits = sum(1 for ind in individuals_to_evaluate if hasattr(ind, 'timing_metadata') and ind.timing_metadata.get('from_cache', False))
                        if cache_hits > 0:
                            cache_rate = (cache_hits / completed_count) * 100
                            print(f"Cache Performance: {cache_rate:.1f}% ({cache_hits}/{completed_count})")
                        
                        print("=" * 60)
                        
                        last_progress_print = current_time
                        last_status_time = current_time
                        
                except Exception as e:
                    print(f"Error getting future result: {e}")
                    completed_count += 1
        
        # Calculate and display timing statistics
        total_time = time.time() - start_time
        avg_time_per_individual = total_time / len(individuals_to_evaluate)
        
        # For simplified fitness, recalculate with proper normalization
        if Config.fitness.use_simplified_fitness:
            # Collect all distance and time values to calculate bounds
            distances = []
            times = []
            
            for ind in individuals_to_evaluate:
                if hasattr(ind, 'timing_metadata') and 'distance' in ind.timing_metadata:
                    distances.append(ind.timing_metadata['distance'])
                    times.append(ind.timing_metadata['time_component'])
            
            if distances and times:
                # Calculate min/max bounds
                min_distance = min(distances)
                max_distance = max(distances)
                min_time = min(times)
                max_time = max(times)
                
                print(f"\n=== Normalization Bounds (Fitness Function) ===")
                print(f"Distance: {min_distance:.2f} (best) - {max_distance:.2f} (worst)")
                print(f"Time: {min_time:.2f} (best) - {max_time:.2f} (worst)")
                print(f"Normalization: value/max_value (0.0 = best, 1.0 = worst)")
                print(f"Fitness: 1.0 - sickness (1.0 = best, 0.0 = worst)")
                
                # Avoid division by zero
                distance_range = max_distance - min_distance
                time_range = max_time - min_time
                
                if distance_range > 0 and time_range > 0:
                    # Update global bounds for future iterations
                    self.min_distance = min(self.min_distance, min_distance)
                    self.max_distance = max(self.max_distance, max_distance)
                    self.min_time = min(self.min_time, min_time)
                    self.max_time = max(self.max_time, max_time)
                    
                    # Recalculate fitness with normalization
                    distance_weight = Config.fitness.distance_weight
                    time_weight = Config.fitness.time_weight
                    
                    for ind in individuals_to_evaluate:
                        if hasattr(ind, 'timing_metadata'):
                            distance = ind.timing_metadata['distance']
                            time_component = ind.timing_metadata['time_component']
                            
                            # Normalize to 0-1 range for fitness using max as max and 0 as min
                            # Then invert: fitness = 1 - normalized_value
                            # This gives: 1.0 = best (minimum distance/time), 0.0 = worst (maximum distance/time)
                            normalized_distance = distance / max_distance  # 0 = best, 1 = worst
                            normalized_time = time_component / max_time    # 0 = best, 1 = worst
                            
                            # Apply weighted sickness function, then invert to get fitness
                            sickness = (distance_weight * normalized_distance + 
                                       time_weight * normalized_time)
                            fitness = 1.0 - sickness  # Invert: 1.0 = best, 0.0 = worst
                            
                            ind.fitness = fitness
                            
                            if hasattr(Config, 'debug') and Config.debug:
                                print(f"  {ind.name}: distance={distance:.2f}→{normalized_distance:.4f}, time={time_component:.2f}→{normalized_time:.4f}, sickness={sickness:.6f}, fitness={fitness:.6f}")
                                print(f"    (normalized: 0.0 = best, 1.0 = worst | fitness: 1.0 = best, 0.0 = worst)")
                else:
                    print("⚠️  Warning: All individuals have identical distance/time values, using raw values")
        
        print(f"✅ Fitness evaluation completed:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average per individual: {avg_time_per_individual:.3f}s")
        print(f"  Throughput: {len(individuals_to_evaluate)/total_time:.2f} individuals/second")
        
        # Store timing metadata for each individual
        for ind in individuals_to_evaluate:
            if hasattr(ind, 'timing_metadata'):
                ind.timing_metadata['avg_calculation_time'] = avg_time_per_individual
                ind.timing_metadata['total_evaluation_time'] = total_time
                ind.timing_metadata['individual_count'] = len(individuals_to_evaluate)
        
        # Update typer with normalization bounds for simplified fitness
        if Config.fitness.use_simplified_fitness:
            self.evaluator.typer.set_normalization_bounds(
                self.min_distance, self.max_distance, self.min_time, self.max_time
            )
            print(f"Updated typer normalization bounds: Distance {self.min_distance:.1f}-{self.max_distance:.1f}, Time {self.min_time:.2f}-{self.max_time:.2f}")

    def order_fitness_values(self, limited=False):
        """Print ordered fitness values"""
        sorted_population = sorted(self.population, key=lambda x: x.fitness)
        print("\n" + "="*100)
        print("ORDERED FITNESS VALUES (Best to Worst)")
        print("="*100)
        print(f"{'Rank':<6} {'Name':<20} {'Fitness':<18} {'Parents':<40}")
        print("-"*100)

        display_population = sorted_population[:10] if limited else sorted_population

        for rank, individual in enumerate(display_population, 1):
            # Get parent names
            if individual.parents:
                parent_names = [self.get_individual_name(p) for p in individual.parents]
                parents_str = ", ".join(parent_names)
            else:
                parents_str = "Initial"
            
            print(f"{rank:<6} {individual.name:<20} {individual.fitness:<18.6f} {parents_str:<40}")

        print("="*100 + "\n")

    def tournament_selection(self, k=3):
        """Tournament selection - just reference existing individuals, don't create copies"""
        self.parents = []
        # Only select from individuals that have fitness values
        temp_population = [ind for ind in self.population if ind.fitness is not None]
        
        if len(temp_population) < k:
            print(f"Warning: Only {len(temp_population)} individuals have fitness values, need at least {k} for tournament selection")
            return

        print(f"Starting tournament selection with {len(temp_population)} individuals (out of {len(self.population)} total)")

        while len(temp_population) >= k:
            sample_size = min(k, len(temp_population))
            k_candidates = random.sample(
                range(len(temp_population)), sample_size)

            best_candidate = None
            best_fitness = float('inf')

            for idx in k_candidates:
                candidate = temp_population[idx]
                # Skip individuals without fitness values
                if candidate.fitness is None:
                    continue
                    
                if candidate.fitness < best_fitness:
                    best_fitness = candidate.fitness
                    best_candidate = candidate

            # Just append the reference, don't create a new Individual
            self.parents.append(best_candidate)

            for idx in sorted(k_candidates, reverse=True):
                temp_population.pop(idx)

        while temp_population and len(self.parents) < len(self.population):
            remaining_individual = temp_population.pop()
            self.parents.append(remaining_individual)

    def uniform_crossover(self, offsprings_per_pair=4):
        """Uniform crossover with uniqueness checking"""
        self.children = []

        def is_duplicate(chromosome, existing_individuals):
            chromosome_str = ''.join(chromosome)
            for individual in existing_individuals:
                if ''.join(individual.chromosome) == chromosome_str:
                    return True
            return False

        for i in range(0, len(self.parents) - 1, 2):
            parent0, parent1 = self.parents[i], self.parents[i+1]

            # Ensure both parents exist and have fitness values
            if parent0 is None or parent0.fitness is None:
                print(f"Warning: Parent {parent0.name if parent0 else 'None'} has no fitness, skipping")
                continue
            if parent1 is None or parent1.fitness is None:
                print(f"Warning: Parent {parent1.name if parent1 else 'None'} has no fitness, skipping")
                continue

            if parent1.fitness < parent0.fitness:
                parent0, parent1 = parent1, parent0

            for o in range(offsprings_per_pair):
                attempts = 0
                max_attempts = 10

                while attempts < max_attempts:
                    new_chromosome = [None] * len(parent0.chromosome)

                    # Bias towards better parent
                    for j in range(len(new_chromosome)):
                        if random.random() < 0.75 + o/30.0:
                            new_chromosome[j] = parent0.chromosome[j]

                    # Fill from parent1
                    for j in range(len(new_chromosome)):
                        if new_chromosome[j] is None and parent1.chromosome[j] not in new_chromosome:
                            new_chromosome[j] = parent1.chromosome[j]

                    # Fill from parent0
                    for j in range(len(new_chromosome)):
                        if new_chromosome[j] is None and parent0.chromosome[j] not in new_chromosome:
                            new_chromosome[j] = parent0.chromosome[j]

                    # Fill remaining
                    existing_genes = set(
                        gene for gene in new_chromosome if gene is not None)
                    all_possible_genes = set(parent0.chromosome)
                    missing_genes = list(all_possible_genes - existing_genes)
                    random.shuffle(missing_genes)

                    for j in range(len(new_chromosome)):
                        if new_chromosome[j] is None:
                            new_chromosome[j] = missing_genes.pop(0)

                    all_existing = self.population + \
                        self.children + [parent0, parent1]

                    if not is_duplicate(new_chromosome, all_existing):
                        child = Individual(
                            chromosome=new_chromosome,
                            fitness=None,
                            parents=[parent0.id, parent1.id],
                            generation=self.current_generation + 1
                        )
                        self.children.append(child)
                        self.individual_names[child.id] = child.name
                        break
                    else:
                        attempts += 1

                if attempts == max_attempts:
                    random_chromosome = parent0.chromosome.copy()
                    random.shuffle(random_chromosome)
                    all_existing = self.population + \
                        self.children + [parent0, parent1]
                    if not is_duplicate(random_chromosome, all_existing):
                        child = Individual(
                            chromosome=random_chromosome,
                            fitness=None,
                            parents=[parent0.id, parent1.id],
                            generation=self.current_generation + 1
                        )
                        self.children.append(child)
                        self.individual_names[child.id] = child.name

        print(f"Created {len(self.children)} unique children")

    def mutation(self):
        """Mutate children based on stagnation"""
        base_mutation_rate = 0.05
        if self.previous_population_iteration > 0:
            mutation_rate = base_mutation_rate * 0.5
        else:
            mutation_rate = base_mutation_rate

        num_mutations = 1 if self.previous_population_iteration == 0 else min(
            self.previous_population_iteration, 5)

        for individual in self.children:
            individual.chromosome = self.mutate_permutation(
                individual.chromosome, mutation_rate, num_mutations
            )

    def mutate_permutation(self, chromosome, mutation_rate=0.05, num_mutations=1):
        """Swap mutation for permutation"""
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
        """Elitist survivor selection"""
        self.fitness_function_calculation()
        combined = self.population + self.children
        sorted_combined = sorted(combined, key=lambda x: x.fitness)
        self.population = sorted_combined[:len(self.population)]

    def run(self, max_iterations=100, stagnant=15):
        """Run genetic algorithm"""
        iteration = 0
        print("Starting genetic algorithm...")
        
        # Start total runtime timing
        total_start_time = time.time()
        
        self.fitness_function_calculation()
        self.order_fitness_values(limited=True)

        while self.previous_population_iteration < stagnant and iteration < max_iterations:
            print(f"\n{'='*80}")
            print(f"ITERATION {iteration + 1} (Generation {self.current_generation + 1})")
            print(f"Stagnation count: {self.previous_population_iteration}/{stagnant}")
            print(f"{'='*80}")

            self.tournament_selection()
            self.uniform_crossover()
            self.mutation()
            
            # Increment generation before survivor selection
            self.current_generation += 1
            
            self.survivor_selection()

            self.order_fitness_values(limited=True)

            if self.previous_population_ids == self.get_current_population_ids():
                self.previous_population_iteration += 1
            else:
                self.previous_population_ids = self.get_current_population_ids()
                self.previous_population_iteration = 0

            iteration += 1

        # Calculate total runtime
        total_runtime = time.time() - total_start_time
        
        print(f"\nAlgorithm completed after {iteration} iterations")
        print(f"Final stagnation count: {self.previous_population_iteration}")
        print(f"Total runtime: {total_runtime:.2f}s")
        print(f"Average time per iteration: {total_runtime/iteration:.2f}s" if iteration > 0 else "")
        
        self.order_fitness_values(limited=False)

        # Return best individual
        best = min(self.population, key=lambda x: x.fitness)
        return best


if __name__ == "__main__":
    ga = GeneticAlgorithm(
        keyboard_file='src/data/keyboards/ansi_60_percent.json',
        dataset_file='src/data/text/processed/frequency_analysis.pkl',
        dataset_name='simple_wikipedia'
    )

    best_individual = ga.run(max_iterations=50, stagnant=10)

    print("\n" + "="*80)
    print("BEST INDIVIDUAL FOUND")
    print("="*80)
    print(f"Name: {best_individual.name}")
    print(f"Fitness: {best_individual.fitness:.6f}")
    parent_names = [ga.get_individual_name(p) for p in best_individual.parents] if best_individual.parents else ["Initial"]
    print(f"Parents: {', '.join(parent_names)}")
    print(f"Layout: {''.join(best_individual.chromosome)}")
    print("="*80)
