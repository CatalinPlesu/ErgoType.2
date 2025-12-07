from concurrent.futures import ProcessPoolExecutor, as_completed
from data.layouts.keyboard_genotypes import LAYOUT_DATA
from core.map_json_exporter import CSharpFitnessConfig
from core.keyboard import Serial
from core.evaluator import Evaluator
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
        
        # Initialize C# in this process
        from pythonnet import set_runtime
        from clr_loader import get_coreclr
        set_runtime(get_coreclr())
        import clr
        
        dll_dir = os.path.join(PROJECT_ROOT, "cs", "bin", "Release", "net9.0")
        if dll_dir not in sys.path:
            sys.path.insert(0, dll_dir)
        clr.AddReference("KeyboardFitness")
        from FitnessNet import Fitness
        
        # Create evaluator
        evaluator = Evaluator(debug=False)
        evaluator.load_keyoard(keyboard_file)
        evaluator.load_layout()

        # Remap layout
        evaluator.layout.remap(LAYOUT_DATA["qwerty"], chromosome)

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
    def __init__(self, keyboard_file='data/keyboards/ansi_60_percent.json',
                 text_file='data/text/raw/simple_wikipedia_dataset.txt',
                 population_size=50,
                 fitts_a=0.5,
                 fitts_b=0.3,
                 finger_coefficients=None,
                 max_concurrent_processes=mp.cpu_count()):
        """Initialize GA with C# fitness calculator"""
        print("Initializing Genetic Algorithm...")

        # Store configuration
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

        self.current_generation = 0
        self.individual_names = {}
        
        # Track all unique individuals as a dict (using ID as key for uniqueness)
        self.all_individuals = {}
        
        self.population_size = population_size
        self.population_initialization(self.population_size)

        self.max_processes = max_concurrent_processes
        print(f"Using up to {self.max_processes} concurrent processes")

    def population_initialization(self, size=50):
        """Initialize population"""
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

        self.previous_population_ids = self.get_current_population_ids()
        self.previous_population_iteration = 0
        self.evaluated_individuals = []
        print(f"Total population size: {len(self.population)}")

    def get_current_population_ids(self):
        return [ind.id for ind in self.population]

    def get_individual_name(self, individual_id):
        return self.individual_names.get(individual_id, f"unknown-{individual_id}")

    def prepare_individual_data(self, individual):
        return (individual.id, individual.chromosome, individual.name)

    def normalize_and_calculate_fitness(self):
        """Normalize toward 0 (better = closer to 0) with 1.2x max scaling
        
        IMPORTANT: Normalizes using global max across ALL evaluated individuals
        to ensure fitness values are comparable across generations.
        """
        # Get ALL evaluated individuals (including from previous generations)
        all_evaluated = [ind for ind in self.evaluated_individuals
                        if ind.distance is not None and ind.time_taken is not None 
                        and ind.distance != float('inf') and ind.time_taken != float('inf')]
        
        if not all_evaluated:
            print("Warning: No individuals with valid raw metrics to normalize")
            return

        # Use GLOBAL max across all generations for consistent normalization
        distances = [ind.distance for ind in all_evaluated]
        times = [ind.time_taken for ind in all_evaluated]

        max_distance = max(distances) * 1.2
        max_time = max(times) * 1.2

        print(f"\nNormalization ranges (global across all generations):")
        print(f"  Distance: [0, {max_distance:.2f}]")
        print(f"  Time: [0, {max_time:.2f}]")

        # Re-normalize ALL evaluated individuals with global scale
        for ind in all_evaluated:
            normalized_distance = ind.distance / max_distance
            normalized_time = ind.time_taken / max_time
            ind.fitness = 0.5 * normalized_distance + 0.5 * normalized_time
        
        # Handle invalid individuals
        for ind in self.population + getattr(self, 'children', []):
            if ind.distance == float('inf') or ind.time_taken == float('inf'):
                ind.fitness = float('inf')

    def fitness_function_calculation(self):
        """Calculate fitness using fresh processes (max_tasks_per_child=1)"""
        individuals_to_evaluate = [ind for ind in self.population if ind.distance is None]

        if hasattr(self, 'children'):
            individuals_to_evaluate.extend([child for child in self.children if child.distance is None])

        if individuals_to_evaluate:
            print(f"Evaluating {len(individuals_to_evaluate)} individuals in parallel...")

            individual_data_list = [self.prepare_individual_data(ind) for ind in individuals_to_evaluate]
            
            # KEY FIX: max_tasks_per_child=1 means each process handles ONE task then exits
            # This prevents memory buildup
            with ProcessPoolExecutor(max_workers=self.max_processes, max_tasks_per_child=1) as executor:
                future_to_individual = {
                    executor.submit(
                        _evaluate_individual_worker,
                        ind_data,
                        self.keyboard_file,
                        self.text_file,
                        self.finger_coefficients,
                        self.fitts_a,
                        self.fitts_b
                    ): ind
                    for ind, ind_data in zip(individuals_to_evaluate, individual_data_list)
                }

                completed_count = 0
                for future in as_completed(future_to_individual):
                    try:
                        individual_id, distance, time_taken = future.result()
                        for ind in individuals_to_evaluate:
                            if ind.id == individual_id:
                                ind.distance = distance
                                ind.time_taken = time_taken
                                if ind not in self.evaluated_individuals:
                                    self.evaluated_individuals.append(ind)
                                break
                        completed_count += 1

                        if completed_count % 10 == 0:
                            print(f"  Completed {completed_count}/{len(individuals_to_evaluate)} evaluations")
                    except Exception as e:
                        print(f"Error getting future result: {e}")
                        completed_count += 1

            print(f"All {len(individuals_to_evaluate)} evaluations completed")
            gc.collect()  # Force garbage collection

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
        
        # Keep selecting until we have enough parents
        while len(self.parents) < target_size:
            # Select k random individuals from population
            sample_size = min(k, len(self.population))
            candidates = random.sample(self.population, sample_size)
            
            # Find best candidate (lowest fitness)
            best_candidate = None
            best_fitness = float('inf')
            
            for candidate in candidates:
                if candidate.fitness is not None and candidate.fitness < best_fitness:
                    best_fitness = candidate.fitness
                    best_candidate = candidate
            
            # Add best candidate to parents (can be selected multiple times)
            if best_candidate is not None:
                self.parents.append(best_candidate)
        
        print(f"Selected {len(self.parents)} parents via tournament selection")

    def uniform_crossover(self, offsprings_per_pair=4):
        """Uniform crossover - create children from parent pairs, prioritizing fitter parents"""
        self.children = []

        def is_duplicate(chromosome, existing_individuals):
            chromosome_str = ''.join(chromosome)
            for individual in existing_individuals:
                if ''.join(individual.chromosome) == chromosome_str:
                    return True
            return False

        if len(self.parents) < 2:
            print(f"Warning: Not enough parents. Have {len(self.parents)} parents.")
            return

        # Sort parents by fitness (best first) to prioritize fitter individuals
        sorted_parents = sorted(self.parents, key=lambda x: x.fitness if x.fitness is not None else float('inf'))
        
        # Create pairs from sorted parents - fittest individuals paired first
        num_pairs = len(sorted_parents) // 2
        target_children = len(self.population)  # Want to create as many children as population size
        
        for pair_idx in range(num_pairs):
            parent0 = sorted_parents[pair_idx * 2]
            parent1 = sorted_parents[pair_idx * 2 + 1]

            if parent0.fitness is None or parent1.fitness is None:
                continue

            # parent0 should already be fitter due to sorting, but double-check
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

        print(f"Created {len(self.children)} unique children (target: {target_children})")

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
        
        # Save all individuals to the unique set (dict keyed by ID)
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
        
        # Keep only survivors
        self.population = sorted_combined[:len(self.population)]
        
        discarded_count = len(sorted_combined) - len(self.population)
        print(f"Survivors: {len(self.population)}, Discarded: {discarded_count}, Total unique individuals: {len(self.all_individuals)}")

    def renormalize_all_individuals(self):
        """Re-normalize ALL individuals using global max values"""
        if not self.evaluated_individuals:
            print("No evaluated individuals to use for renormalization")
            return
        
        # Get global max from ALL evaluated individuals
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
        
        # Re-normalize all individuals in the unique set
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
        """Run genetic algorithm"""
        iteration = 0
        print("Starting genetic algorithm...")
        self.fitness_function_calculation()
        self.order_fitness_values(limited=True)

        try:
            while self.previous_population_iteration < stagnant and iteration < max_iterations:
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

        except KeyboardInterrupt:
            print("\n\nInterrupted by user!")

        print(f"\nAlgorithm completed after {iteration} iterations")
        print(f"Final stagnation count: {self.previous_population_iteration}")
        print(f"Total individuals evaluated: {len(self.evaluated_individuals)}")
        print(f"Total unique individuals: {len(self.all_individuals)}")
        
        # Re-normalize all saved individuals with final global scale
        self.renormalize_all_individuals()
        
        self.order_fitness_values(limited=False)

        best = min(self.population, key=lambda x: x.fitness if x.fitness is not None else float('inf'))
        return best


if __name__ == "__main__":
    ga = GeneticAlgorithmSimulation(
        keyboard_file='data/keyboards/ansi_60_percent.json',
        text_file='data/text/raw/simple_wikipedia_dataset.txt',
        fitts_a=0.5,
        fitts_b=0.3,
        max_concurrent_processes=4
    )

    # Run without auto-saving
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
    
    # Additional statistics
    print("\n" + "="*80)
    print("RUN STATISTICS")
    print("="*80)
    print(f"Total individuals evaluated: {len(ga.evaluated_individuals)}")
    print(f"Total unique individuals tracked: {len(ga.all_individuals)}")
    print(f"Final population size: {len(ga.population)}")
    print("="*80)
    
    # Save all individuals to JSON
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
