from keyboard_genotypes import LAYOUT_DATA
import random
import os
import pickle
from keyboard_phenotype import KeyboardPhenotype
from src.domain.keyboard import Serial
import sys
from contextlib import redirect_stdout


class Individual:
    _next_id = 0  # Static counter

    def __init__(self, chromosome, fitness=None, parents=None):
        self.chromosome = chromosome
        self.fitness = fitness
        self.id = Individual._next_id  # Assign current ID
        Individual._next_id += 1       # Increment for next individual
        self.parents = parents or []   # List of parent IDs

    def __repr__(self):
        return f"Individual(id={self.id}, chromosome={''.join(self.chromosome)}, fitness={self.fitness}, parents={self.parents})"


class GeneticAlgorithm:
    def __init__(self):
        self.population_initialization()
        try:
            data_file = './processed/markov_chains.pkl'
            if not os.path.exists(data_file):
                print(f"ERROR: Data file not found: {data_file}")
                data = {}
            else:
                with open(data_file, 'rb') as f:
                    data = pickle.load(f)
                print(f"✅ Successfully loaded data from {data_file}")
        except Exception as e:
            print(f"ERROR loading data: {e}")
            data = {}
        self.data = data
        with open('./processed/frequency_analysis.pkl', 'rb') as f:
            self.data2 = pickle.load(f)

    def population_initialization(self, size=100):
        self.population = []

        # Add heuristic individuals
        for _, genotype in LAYOUT_DATA.items():
            individual = Individual(chromosome=genotype)
            self.population.append(individual)
            # break

        print(f"Population initialized with {len(self.population)} heuristic")
        print(f"""Population initialized with {
              size - len(self.population)} random""")

        if size > len(self.population):
            if self.population:
                template_genotype = self.population[0].chromosome
                needed = size - len(self.population)
                for _ in range(needed):
                    shuffled_clone = template_genotype.copy()
                    random.shuffle(shuffled_clone)
                    individual = Individual(chromosome=shuffled_clone)
                    self.population.append(individual)

        self.previous_population_ids = self.get_current_population_ids()
        self.previous_population_iteration = 0

    def get_current_population_ids(self):
        return [c.id for c in self.population]

    def fitness_function_calculation(self):
        with open('kle_keyboards/ansi_60_percent_hands.json', 'r') as f:
            keyboard = Serial.parse(f.read())

        keyboard = KeyboardPhenotype(keyboard, {})
        keyboard.select_remap_keys(LAYOUT_DATA['qwerty'])

        # Process population individuals
        for individual in self.population:
            if individual.fitness is None:  # Only calculate if not already present
                with open(os.devnull, 'w') as devnull:
                    with redirect_stdout(devnull):
                        keyboard.remap_to_keys(individual.chromosome)
                        # individual.fitness = keyboard.fitness(
                        #     self.data['simple_wikipedia'], depth=1)
                        individual.fitness = keyboard.fitness_with_frequency_data(
                            self.data2['simple_wikipedia'])

        # Process children individuals if they exist
        if hasattr(self, 'children'):
            for child in self.children:
                if child.fitness is None:  # Only calculate if not already present
                    with open(os.devnull, 'w') as devnull:
                        with redirect_stdout(devnull):
                            keyboard.remap_to_keys(child.chromosome)
                            child.fitness = keyboard.fitness_with_frequency_data(
                                self.data2['simple_wikipedia'])

    def order_fitness_values(self, limited=False):
        sorted_population = sorted(self.population, key=lambda x: x.fitness)
        print("\n" + "="*100)
        print("ORDERED FITNESS VALUES (Best to Worst)")
        print("="*100)
        print(f"""{'Rank':<4} {'ID':<6} {'Fitness':<12} {
              'Parents':<15} {'Layout':<50}""")
        print("-"*100)

        # Determine which individuals to display
        display_population = sorted_population[:
                                               5] if limited else sorted_population

        for rank, individual in enumerate(display_population, 1):
            layout_str = ''.join(individual.chromosome)
            display_layout = layout_str[:47] + \
                "..." if len(layout_str) > 50 else layout_str

            parents_str = str(
                individual.parents) if individual.parents else "[]"
            print(f"""{rank:<4} {individual.id:<6} {individual.fitness:<12.6f} {
                  parents_str:<15} {display_layout:<70}""")
        print("="*100 + "\n")

    def tournament_selection(self, k=3):
        self.parents = []

        # Create a copy of population to work with (to avoid modifying original during selection)
        temp_population = self.population.copy()

        while len(temp_population) >= k:
            # Generate k unique random indices from the current temporary population
            sample_size = min(k, len(temp_population))
            k_candidates = random.sample(
                range(len(temp_population)), sample_size)

            # Find the candidate with the best (lowest) fitness
            best_candidate = None
            best_fitness = float('inf')

            for idx in k_candidates:
                if temp_population[idx].fitness < best_fitness:
                    best_fitness = temp_population[idx].fitness
                    best_candidate = temp_population[idx]

            # Add the best individual to parents
            self.parents.append(Individual(
                chromosome=best_candidate.chromosome.copy(),
                fitness=best_candidate.fitness
            ))

            # Remove the selected candidates from temp_population in reverse order to avoid index shifting
            for idx in sorted(k_candidates, reverse=True):
                temp_population.pop(idx)

        # If there are remaining individuals and we need more parents, add them
        while temp_population and len(self.parents) < len(self.population):
            remaining_individual = temp_population.pop()
            self.parents.append(Individual(
                chromosome=remaining_individual.chromosome.copy(),
                fitness=remaining_individual.fitness
            ))

    def crossover(self):
        self.uniform_crossover()

    def uniform_crossover(self, offsprings_per_pair=6):
        self.children = []

        def is_duplicate(chromosome, existing_individuals):
            """Check if chromosome exists in existing individuals"""
            chromosome_str = ''.join(chromosome)
            for individual in existing_individuals:
                if ''.join(individual.chromosome) == chromosome_str:
                    return True
            return False

        for i in range(0, len(self.parents) - 1, 2):  # -1 to ensure we have pairs
            parent0, parent1 = self.parents[i], self.parents[i+1]

            # print(f"""P0 [{''.join(parent0.chromosome)
            #                }] with fitness - {parent0.fitness}""")
            # print(f"""P1 [{''.join(parent1.chromosome)
            #                }] with fitness - {parent1.fitness}""")

            # Ensure parent0 has better (lower) fitness
            if parent1.fitness < parent0.fitness:
                # print("Swap predominant parent")
                parent0, parent1 = parent1, parent0

            for o in range(offsprings_per_pair):
                # print(f"Creating offspring {o}")

                # Keep trying until we get a unique chromosome
                attempts = 0
                max_attempts = 10  # Prevent infinite loops

                while attempts < max_attempts:
                    new_chromosome = [None] * len(parent0.chromosome)

                    # Take with probability 75% + bias a gene from predominant parent
                    for i in range(len(new_chromosome)):
                        if random.random() < 0.75 + o/30.0:  # next children will resemble the first parent more
                            new_chromosome[i] = parent0.chromosome[i]

                    # Try to put same genes from second parent if they are not found already
                    for i in range(len(new_chromosome)):
                        if new_chromosome[i] is None and parent1.chromosome[i] not in new_chromosome:
                            new_chromosome[i] = parent1.chromosome[i]

                    # Try to put same genes from first parent if they are not found already
                    for i in range(len(new_chromosome)):
                        if new_chromosome[i] is None and parent0.chromosome[i] not in new_chromosome:
                            new_chromosome[i] = parent0.chromosome[i]

                    # Fill remaining positions with missing genes
                    existing_genes = set(
                        gene for gene in new_chromosome if gene is not None)
                    all_possible_genes = set(parent0.chromosome)
                    missing_genes = list(all_possible_genes - existing_genes)
                    random.shuffle(missing_genes)

                    for j in range(len(new_chromosome)):
                        if new_chromosome[j] is None:
                            new_chromosome[j] = missing_genes.pop(0)

                    # Check if this chromosome is a duplicate of parents or existing children
                    all_existing = self.population + \
                        self.children + [parent0, parent1]

                    if not is_duplicate(new_chromosome, all_existing):
                        # Create child individual without fitness (will be calculated later)
                        child = Individual(chromosome=new_chromosome, fitness=None, parents=[
                                           parent0.id, parent1.id])
                        self.children.append(child)
                        break  # Successfully created a unique child
                    else:
                        attempts += 1

                # If we couldn't create a unique child after max attempts,
                # create a completely random permutation
                if attempts == max_attempts:
                    # Create a random permutation of the parent's chromosome
                    random_chromosome = parent0.chromosome.copy()
                    random.shuffle(random_chromosome)

                    # Double check it's not a duplicate
                    all_existing = self.population + \
                        self.children + [parent0, parent1]
                    if not is_duplicate(random_chromosome, all_existing):
                        child = Individual(chromosome=random_chromosome, fitness=None, parents=[
                                           parent0.id, parent1.id])
                        self.children.append(child)
                    else:
                        # If even random chromosome is a duplicate, skip this child
                        continue

        print(f"Created {len(self.children)} unique children")

    def mutation(self):
        # Calculate mutation rate based on stagnation
        base_mutation_rate = 0.05
        if self.previous_population_iteration > 0:
            mutation_rate = base_mutation_rate * 0.05  # Multiply by 0.05 when not 0
        else:
            mutation_rate = base_mutation_rate

        # Determine number of mutations: either 1 or n (where n = previous_population_iteration)
        num_mutations = 1 if self.previous_population_iteration == 0 else self.previous_population_iteration

        for individual in self.children:
            individual.chromosome = self.mutate_permutation(
                individual.chromosome, mutation_rate, num_mutations)

    def mutate_permutation(self, chromosome, mutation_rate=0.05, num_mutations=1):
        """Mutation for permutation problems - mutate either 1 or n positions based on stagnation"""
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
        self.fitness_function_calculation()
        # Combine population and children, then select best individuals for next generation
        combined = self.population + self.children

        # Sort by fitness and keep the best individuals for next generation
        sorted_combined = sorted(combined, key=lambda x: x.fitness)
        self.population = sorted_combined[:len(self.population)]

    def run(self, stagnant=10):
        iteration = 0
        self.fitness_function_calculation()
        self.order_fitness_values()
        while self.previous_population_iteration < stagnant:
            self.fitness_function_calculation()
            self.tournament_selection()
            self.crossover()
            self.mutation()
            self.survivor_selection()

            # Print current iteration
            print(f"""CURRENT ITERATION: {iteration} PREVIOUS POPULATION ITERATION: {
                  self.previous_population_iteration}""")

            self.order_fitness_values(limited=True)

            if self.previous_population_ids == self.get_current_population_ids():
                self.previous_population_iteration += 1
            else:
                self.previous_population_ids = self.get_current_population_ids()
                self.previous_population_iteration = 0

            iteration += 1
