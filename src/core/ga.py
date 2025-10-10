from contextlib import redirect_stdout
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
from src.core.keyboard import Serial
from src.core.evaluator import Evaluator
import os
import pickle
import random
import sys


class Individual:
    _next_id = 0

    def __init__(self, chromosome, fitness=None, parents=None):
        self.chromosome = chromosome
        self.fitness = fitness
        self.id = Individual._next_id
        Individual._next_id += 1
        self.parents = parents or []

    def __repr__(self):
        return f"Individual(id={self.id}, chromosome={''.join(self.chromosome)[:20]}..., fitness={self.fitness:.6f if self.fitness else None}, parents={self.parents})"


class GeneticAlgorithm:
    def __init__(self, keyboard_file='src/data/keyboards/ansi_60_percent.json',
                 dataset_file='src/data/text/processed/frequency_analysis.pkl',
                 dataset_name='simple_wikipedia'):
        """Initialize GA with evaluator"""
        print("Initializing Genetic Algorithm...")

        # Initialize evaluator
        self.evaluator = Evaluator(debug=False)
        self.evaluator.load_keyoard(keyboard_file)
        self.evaluator.load_distance()
        self.evaluator.load_layout()
        self.evaluator.load_dataset(
            dataset_file=dataset_file, dataset_name=dataset_name)
        self.evaluator.load_typer()

        print("Evaluator initialized successfully")

        self.population_initialization()

    def population_initialization(self, size=50):
        """Initialize population with heuristic layouts and random permutations"""
        self.population = []

        # Add heuristic individuals
        for layout_name, genotype in LAYOUT_DATA.items():
            individual = Individual(chromosome=list(genotype))
            self.population.append(individual)
            print(f"Added heuristic layout: {layout_name}")

        print(f"""Population initialized with {
              len(self.population)} heuristic individuals""")

        # Add random individuals if needed
        if size > len(self.population):
            if self.population:
                template_genotype = self.population[0].chromosome
                needed = size - len(self.population)
                print(f"Adding {needed} random individuals")

                for _ in range(needed):
                    shuffled_clone = template_genotype.copy()
                    random.shuffle(shuffled_clone)
                    individual = Individual(chromosome=shuffled_clone)
                    self.population.append(individual)

        self.previous_population_ids = self.get_current_population_ids()
        self.previous_population_iteration = 0
        print(f"Total population size: {len(self.population)}")

    def get_current_population_ids(self):
        """Get list of current population IDs"""
        return [ind.id for ind in self.population]

    def fitness_function_calculation(self):
        """Calculate fitness for all individuals without fitness values"""
        individuals_to_evaluate = [
            ind for ind in self.population if ind.fitness is None]

        if hasattr(self, 'children'):
            individuals_to_evaluate.extend(
                [child for child in self.children if child.fitness is None])

        if not individuals_to_evaluate:
            return

        print(f"Evaluating {len(individuals_to_evaluate)} individuals...")

        for i, individual in enumerate(individuals_to_evaluate):
            # Remap layout to individual's chromosome
            self.evaluator.layout.querty_based_remap(individual.chromosome)

            # Calculate fitness
            with open(os.devnull, 'w') as devnull:
                with redirect_stdout(devnull):
                    fitness_dict = self.evaluator.typer.fitness()

            # Combined fitness score (lower is better)
            # Distance score is primary, modified by ngram and homing scores
            distance = fitness_dict['distance_score']
            ngram = fitness_dict['ngram_score']
            homing = fitness_dict['homing_score']

            # Fitness formula: lower is better
            # Penalize distance, reward high ngram and homing scores
            individual.fitness = distance * (2.0 - ngram) * (2.0 - homing)

            if (i + 1) % 10 == 0:
                print(f"""  Evaluated {
                      i + 1}/{len(individuals_to_evaluate)} individuals""")

    def order_fitness_values(self, limited=False):
        """Print ordered fitness values"""
        sorted_population = sorted(self.population, key=lambda x: x.fitness)
        print("\n" + "="*100)
        print("ORDERED FITNESS VALUES (Best to Worst)")
        print("="*100)
        print(f"""{'Rank':<6} {'ID':<6} {'Fitness':<18} {
              'Parents':<20} {'Layout Preview':<30}""")
        print("-"*100)

        display_population = sorted_population[:
                                               10] if limited else sorted_population

        for rank, individual in enumerate(display_population, 1):
            layout_str = ''.join(individual.chromosome[:15]) + "..." if len(
                individual.chromosome) > 15 else ''.join(individual.chromosome)
            parents_str = str(
                individual.parents) if individual.parents else "None"
            print(f"""{rank:<6} {individual.id:<6} {individual.fitness:<18.6f} {
                  parents_str:<20} {layout_str:<30}""")

        print("="*100 + "\n")

    def tournament_selection(self, k=3):
        """Tournament selection with replacement"""
        self.parents = []
        temp_population = self.population.copy()

        while len(temp_population) >= k:
            sample_size = min(k, len(temp_population))
            k_candidates = random.sample(
                range(len(temp_population)), sample_size)

            best_candidate = None
            best_fitness = float('inf')

            for idx in k_candidates:
                if temp_population[idx].fitness < best_fitness:
                    best_fitness = temp_population[idx].fitness
                    best_candidate = temp_population[idx]

            self.parents.append(Individual(
                chromosome=best_candidate.chromosome.copy(),
                fitness=best_candidate.fitness,
                parents=best_candidate.parents.copy()
            ))

            for idx in sorted(k_candidates, reverse=True):
                temp_population.pop(idx)

        while temp_population and len(self.parents) < len(self.population):
            remaining_individual = temp_population.pop()
            self.parents.append(Individual(
                chromosome=remaining_individual.chromosome.copy(),
                fitness=remaining_individual.fitness,
                parents=remaining_individual.parents.copy()
            ))

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
                            parents=[parent0.id, parent1.id]
                        )
                        self.children.append(child)
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
                            parents=[parent0.id, parent1.id]
                        )
                        self.children.append(child)

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
            print(f"ITERATION {iteration + 1}")
            print(f"""Stagnation count: {
                  self.previous_population_iteration}/{stagnant}""")
            print(f"{'='*80}")

            self.tournament_selection()
            self.uniform_crossover()
            self.mutation()
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
    print(f"ID: {best_individual.id}")
    print(f"Fitness: {best_individual.fitness:.6f}")
    print(f"Parents: {best_individual.parents}")
    print(f"Layout: {''.join(best_individual.chromosome)}")
    print("="*80)
