from contextlib import redirect_stdout
from concurrent.futures import ProcessPoolExecutor, as_completed
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
from src.core.map_json_exporter import CSharpFitnessConfig
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

            config_gen = CSharpFitnessConfig(
                keyboard=ev.keyboard,
                layout=ev.layout
            )

            json_string = config_gen.generate_json_string(
                text_file_path="path/to/your/text/file.txt",
                fitts_a=0.0,
                fitts_b=150.0
            )

            # Calculate fitness
            with open(os.devnull, 'w') as devnull:
                with redirect_stdout(devnull):
                    fitness_dict = evaluator.typer.fitness()

            # Combined fitness score (lower is better)
            distance = fitness_dict['distance_score']
            ngram = fitness_dict['ngram_score']
            homing = fitness_dict['homing_score']

            # Fitness formula: lower is better
            fitness = Config.fitness.distance_weight * distance + \
                Config.fitness.n_gram_weight * distance * (1.0 - ngram) + \
                Config.fitness.homerow_weight * distance * (1.0 - homing)
            print(f"Process {os.getpid()}: Evaluated {individual.name}, fitness = {fitness:.6f}")
            
            # Add to evaluated individuals if not already there
            if individual not in self.evaluated_individuals:
                self.evaluated_individuals.append(individual)
            
            return individual.id, fitness

        except Exception as e:
            print(f"Error evaluating {individual.name} in process {os.getpid()}: {e}")
            return individual.id, float('inf')

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

        # Use ProcessPoolExecutor for process-based parallel execution
        with ProcessPoolExecutor(max_workers=self.num_processes) as executor:
            # Submit all evaluation tasks
            future_to_individual = {
                executor.submit(self.evaluate_individual_fitness, ind): ind
                for ind in individuals_to_evaluate
            }

            # Process completed evaluations as they finish
            completed_count = 0
            for future in as_completed(future_to_individual):
                try:
                    individual_id, fitness = future.result()
                    # Find the individual by ID and set its fitness
                    for ind in individuals_to_evaluate:
                        if ind.id == individual_id:
                            ind.fitness = fitness
                            # Add to evaluated individuals if not already there
                            if ind not in self.evaluated_individuals:
                                self.evaluated_individuals.append(ind)
                            break
                    completed_count += 1

                    if completed_count % 10 == 0:
                        print(f"  Completed {completed_count}/{len(individuals_to_evaluate)} evaluations")
                except Exception as e:
                    print(f"Error getting future result: {e}")
                    completed_count += 1

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
        temp_population = self.population.copy()

        while len(temp_population) >= k:
            sample_size = min(k, len(temp_population))
            k_candidates = random.sample(
                range(len(temp_population)), sample_size)

            best_candidate = None
            best_fitness = float('inf')

            for idx in k_candidates:
                # Skip individuals with None fitness
                if temp_population[idx].fitness is None:
                    continue
                if temp_population[idx].fitness < best_fitness:
                    best_fitness = temp_population[idx].fitness
                    best_candidate = temp_population[idx]

            # Only append if we found a valid candidate
            if best_candidate is not None:
                self.parents.append(best_candidate)

            for idx in sorted(k_candidates, reverse=True):
                temp_population.pop(idx)

        while temp_population and len(self.parents) < len(self.population):
            remaining_individual = temp_population.pop()
            # Only add if fitness is not None
            if remaining_individual.fitness is not None:
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

        # Check if we have enough parents with valid fitness
        if len(self.parents) < 2:
            print(f"Warning: Not enough parents with valid fitness for crossover. Have {len(self.parents)} parents.")
            return

        for i in range(0, len(self.parents) - 1, 2):
            parent0, parent1 = self.parents[i], self.parents[i+1]

            # Safety check: ensure both parents have valid fitness
            if parent0.fitness is None or parent1.fitness is None:
                print(f"Warning: Skipping crossover due to None fitness values: parent0={parent0.name}, parent1={parent1.name}")
                continue
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

        print(f"\nAlgorithm completed after {iteration} iterations")
        print(f"Final stagnation count: {self.previous_population_iteration}")
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
