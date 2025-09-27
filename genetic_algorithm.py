from keyboard_genotypes import LAYOUT_DATA
import random
import os
import pickle
from keyboard_phenotype import KeyboardPhenotype
from kle.kle_model import Serial
import sys
from contextlib import redirect_stdout


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
        for _, genotype in LAYOUT_DATA.items():
            self.population.append(genotype)
        print(f"Population initialized with {len(self.population)} heuristic")
        print(f"""Population initialized with {
              size - len(self.population)} random""")
        if size > len(self.population):
            if self.population:
                template_genotype = self.population[0]
                needed = size - len(self.population)
                for _ in range(needed):
                    shuffled_clone = template_genotype.copy()
                    random.shuffle(shuffled_clone)
                    self.population.append(shuffled_clone)
                # for p in self.population:
                #     print(''.join(p))

    def fitness_function_calculation(self):
        self.fitness_values = [None] * len(self.population)

        with open('kle_keyboards/ansi_60_percent_hands.json', 'r') as f:
            keyboard = Serial.parse(f.read())

        keyboard = KeyboardPhenotype(keyboard, {})
        keyboard.select_remap_keys(LAYOUT_DATA['qwerty'])

        for index, genotype in enumerate(self.population):
            with open(os.devnull, 'w') as devnull:
                with redirect_stdout(devnull):
                    keyboard.remap_to_keys(genotype)
                    self.fitness_values[index] = keyboard.fitness(
                        self.data['simple_wikipedia'])
            # print(
            #     f"Genotype [{index}] has fitness -> {self.fitness_values[index]}")

    def order_fitness_values(self):
        # Create list of (index, fitness_value) tuples
        indexed_fitness = [(i, fitness)
                           for i, fitness in enumerate(self.fitness_values)]

        # Sort by fitness value (ascending order - best/lowest fitness first)
        sorted_fitness = sorted(indexed_fitness, key=lambda x: x[1])

        print("\n" + "="*80)
        print("ORDERED FITNESS VALUES (Best to Worst)")
        print("="*80)
        print(f"{'Rank':<4} {'Index':<6} {'Fitness':<12} {'Layout':<50}")
        print("-"*80)

        for rank, (index, fitness) in enumerate(sorted_fitness, 1):
            layout_str = ''.join(self.population[index])
            # Truncate layout if too long to save space
            display_layout = layout_str[:47] + \
                "..." if len(layout_str) > 50 else layout_str
            print(f"""{rank:<4} {index:<6} {
                  fitness:<18.6f} {display_layout:<70}""")

        print("="*80 + "\n")

    def tournament_selection(self, k=3):
        new_parents = []
        new_parents_fitness = []

        # Work with copies to avoid modifying during iteration issues
        temp_population = self.population.copy()
        temp_fitness_values = self.fitness_values.copy()

        while len(temp_population) >= k:
            # Generate k unique random indices from the current temporary population
            sample_size = min(k, len(temp_population))
            k_candidates = random.sample(
                range(len(temp_population)), sample_size)

            # Create zipped pairs
            zipped = [(idx, temp_fitness_values[idx]) for idx in k_candidates]
            min_tuple = min(zipped, key=lambda x: x[1])

            # Add the best individual to parents
            new_parents.append(temp_population[min_tuple[0]])
            new_parents_fitness.append(temp_fitness_values[min_tuple[0]])

            # Sort indices in DESCENDING order before popping to avoid index shifting
            for index in sorted(k_candidates, reverse=True):
                temp_population.pop(index)
                temp_fitness_values.pop(index)

        # Update the original population with remaining individuals
        self.population = []
        self.fitness_values = []
        self.new_parents = new_parents
        self.new_parents_fitness = new_parents_fitness

    def crossover(self):
        self.uniform_crossover()

    def uniform_crossover(self, offsprings=6):
        for chromosome in self.new_parents:
            print(''.join(chromosome))
        # we will have bias of 75 % for the genes of the parent with lower value
        for i in range(0, len(self.new_parents) - 1, 2):  # -1 to ensure we have pairs
            i0, i1 = i, i+1
            print(f"""P0 {
                  ''.join(self.new_parents[i0])}] with fitness - {self.new_parents_fitness[i0]}""")
            print(f"""P1 {
                  ''.join(self.new_parents[i1])}] with fitness - {self.new_parents_fitness[i1]}""")

            if (self.new_parents_fitness[i1] < self.new_parents_fitness[i0]):
                print("Swap predominant parent")
                i0, i1 = i1, i0

            for o in range(0, offsprings):
                print(f"Creating offspring {o}")
                new_chromosome = [None] * len(self.new_parents[i0])
                # take with probability 75% a gene from predominat parent
                for i in range(0, len(new_chromosome)):
                    if random.random() < 0.75+o/30.0:
                        new_chromosome[i] = self.new_parents[i0][i]
                # trie to put same genes from second parent if they are not found already
                for i in range(0, len(new_chromosome)):
                    if new_chromosome[i] is None and self.new_parents[i1][i] not in new_chromosome:
                        new_chromosome[i] = self.new_parents[i1][i]
                existing_genes = set(
                    gene for gene in new_chromosome if gene is not None)
                all_possible_genes = set(self.new_parents[i0])
                missing_genes = list(all_possible_genes - existing_genes)
                random.shuffle(missing_genes)
                for j in range(len(new_chromosome)):
                    if new_chromosome[j] is None:
                        new_chromosome[j] = missing_genes.pop(0)
                print(new_chromosome)
                self.population.append(new_chromosome)

    def mutation(self):
        for i, c in enumerate(self.population):
            new_chromosome = self.mutate_permutation(c)
            self.population[i] = new_chromosome
        pass

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
        pass

    def run(self):
        pass
