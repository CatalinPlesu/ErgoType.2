from keyboard_genotypes import LAYOUT_DATA
import random
import os
import pickle
from keyboard_phenotype import KeyboardPhenotype
from kle.kle_model import Serial
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

    def population_initialization(self, size=100):
        self.population = []

        # Add heuristic individuals
        for _, genotype in LAYOUT_DATA.items():
            individual = Individual(chromosome=genotype)
            self.population.append(individual)

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
                        individual.fitness = keyboard.fitness(
                            self.data['simple_wikipedia'])

        # Process children individuals if they exist
        if hasattr(self, 'children'):
            for child in self.children:
                if child.fitness is None:  # Only calculate if not already present
                    with open(os.devnull, 'w') as devnull:
                        with redirect_stdout(devnull):
                            keyboard.remap_to_keys(child.chromosome)
                            child.fitness = keyboard.fitness(
                                self.data['simple_wikipedia'])

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

                # print(new_chromosome)

                # Create child individual without fitness (will be calculated later)
                child = Individual(chromosome=new_chromosome, fitness=None, parents=[
                                   parent0.id, parent1.id])
                self.children.append(child)

    def mutation(self):
        for individual in self.children:
            individual.chromosome = self.mutate_permutation(
                individual.chromosome)

    def mutate_permutation(self, chromosome, mutation_rate=0.05):
        """Mutation for permutation problems - mutate exactly one position"""
        mutated = chromosome.copy()
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

    def run(self):
        self.fitness_function_calculation()
        self.tournament_selection()
        self.crossover()
        self.mutation()
        self.survivor_selection()
        self.order_fitness_values(limited=True)
