using System;
using System.Collections.Generic;
using System.Linq;

namespace KeyboardLayoutOptimizer
{
    /// <summary>
    /// Individual in the genetic algorithm population
    /// </summary>
    public class Individual
    {
        public static int NextId { get; private set; } = 0;
        
        public int Id { get; }
        public string Name { get; set; }
        public char[] Chromosome { get; set; }
        public double? Fitness { get; set; }
        public int Generation { get; set; }
        public List<int> Parents { get; set; } = new List<int>();
        public Dictionary<string, object> Metadata { get; set; } = new Dictionary<string, object>();

        public Individual(char[] chromosome, int generation = 0, string name = null)
        {
            Id = NextId++;
            Chromosome = chromosome;
            Generation = generation;
            Name = name ?? $"gen_{generation}-{Id}";
        }

        public override string ToString()
        {
            var parentStr = Parents.Any() ? string.Join(", ", Parents) : "Initial";
            return $"Individual(Id={Id}, Name={Name}, Fitness={Fitness?.ToString("F6") ?? "N/A"}, Parents=[{parentStr}])";
        }
    }

    /// <summary>
    /// Delegate for fitness function - allows different evaluation strategies
    /// </summary>
    /// <param name="layout">Layout chromosome to evaluate</param>
    /// <returns>Fitness score (lower is better)</returns>
    public delegate double FitnessFunction(char[] layout);

    /// <summary>
    /// Genetic Algorithm implementation for keyboard layout optimization
    /// </summary>
    public class GeneticAlgorithm
    {
        private readonly Random _random = new Random();
        private readonly FitnessFunction _fitnessFunction;

        public int PopulationSize { get; set; } = 50;
        public double MutationRate { get; set; } = 0.05;
        public int TournamentSize { get; set; } = 3;
        public int OffspringPerPair { get; set; } = 4;
        public int MaxGenerations { get; set; } = 100;
        public int StagnationLimit { get; set; } = 15;

        public List<Individual> Population { get; private set; } = new List<Individual>();
        public List<LayoutPreset> Presets { get; set; } = new List<LayoutPreset>();

        public GeneticAlgorithm(FitnessFunction fitnessFunction)
        {
            _fitnessFunction = fitnessFunction;
        }

        /// <summary>
        /// Run the genetic algorithm optimization
        /// </summary>
        public OptimizationResult Run(int populationSize = 50, int maxGenerations = 100, int stagnationLimit = 15)
        {
            PopulationSize = populationSize;
            MaxGenerations = maxGenerations;
            StagnationLimit = stagnationLimit;

            var result = new OptimizationResult
            {
                GenerationHistory = new List<GenerationStats>(),
                TotalTime = TimeSpan.Zero
            };

            var startTime = DateTime.Now;

            InitializePopulation();
            EvaluatePopulation();

            var bestFitness = Population.Min(i => i.Fitness);
            var bestIndividual = Population.First(i => i.Fitness == bestFitness);
            
            var stagnantCount = 0;
            var previousPopulationIds = GetPopulationIds();

            Console.WriteLine($"Initial best fitness: {bestFitness:F6}");

            for (int generation = 1; generation <= MaxGenerations; generation++)
            {
                var generationStart = DateTime.Now;

                // Selection, crossover, and mutation
                var parents = TournamentSelection();
                var children = UniformCrossover(parents);
                MutateChildren(children);

                // Survivor selection
                Population.AddRange(children);
                EvaluatePopulation();
                Population = Population.OrderBy(i => i.Fitness).Take(PopulationSize).ToList();

                var currentBestFitness = Population.Min(i => i.Fitness);
                var currentBestIndividual = Population.First(i => i.Fitness == currentBestFitness);

                // Track generation statistics
                var generationStats = new GenerationStats
                {
                    Generation = generation,
                    BestFitness = currentBestFitness.Value,
                    AverageFitness = Population.Average(i => i.Fitness),
                    WorstFitness = Population.Max(i => i.Fitness),
                    GenerationTime = DateTime.Now - generationStart
                };

                result.GenerationHistory.Add(generationStats);

                // Check for improvement
                if (currentBestFitness < bestFitness)
                {
                    bestFitness = currentBestFitness;
                    bestIndividual = currentBestIndividual;
                    stagnantCount = 0;
                    Console.WriteLine($"Generation {generation}: New best fitness: {bestFitness:F6}");
                }
                else
                {
                    stagnantCount++;
                }

                // Check for population stagnation
                var currentPopulationIds = GetPopulationIds();
                if (currentPopulationIds.SequenceEqual(previousPopulationIds))
                {
                    stagnantCount++;
                }
                else
                {
                    previousPopulationIds = currentPopulationIds;
                    stagnantCount = 0;
                }

                if (stagnantCount >= StagnationLimit)
                {
                    Console.WriteLine($"Stopping due to stagnation after {generation} generations");
                    result.ElapsedGenerations = generation;
                    break;
                }

                if (generation == MaxGenerations)
                {
                    result.ElapsedGenerations = generation;
                }
            }

            result.BestIndividual = bestIndividual;
            result.TotalTime = DateTime.Now - startTime;

            return result;
        }

        private void InitializePopulation()
        {
            Population.Clear();

            // Add preset layouts
            foreach (var preset in Presets)
            {
                Population.Add(new Individual(preset.Chromosome, 0, preset.Name));
            }

            // Add random individuals to fill population
            var template = Presets.FirstOrDefault()?.Chromosome ?? GenerateRandomLayout();
            while (Population.Count < PopulationSize)
            {
                var randomLayout = MutateLayout(template, 0.5, 5); // High mutation for diversity
                var individual = new Individual(randomLayout, 0);
                Population.Add(individual);
            }

            Console.WriteLine($"Initialized population with {Population.Count} individuals");
        }

        private void EvaluatePopulation()
        {
            var tasks = Population
                .Where(i => i.Fitness == null)
                .Select(i => 
                {
                    var fitness = _fitnessFunction(i.Chromosome);
                    return new { Individual = i, Fitness = fitness };
                })
                .ToList();

            foreach (var task in tasks)
            {
                task.Individual.Fitness = task.Fitness;
            }
        }

        private List<int> GetPopulationIds()
        {
            return Population.Select(i => i.Id).OrderBy(id => id).ToList();
        }

        private List<Individual> TournamentSelection()
        {
            var parents = new List<Individual>();
            var candidates = Population.Where(i => i.Fitness.HasValue).ToList();

            while (candidates.Count >= TournamentSize && parents.Count < PopulationSize)
            {
                var tournament = _random.Next(candidates.Count);
                var best = candidates[tournament];

                for (int i = 1; i < TournamentSize; i++)
                {
                    var candidate = candidates[_random.Next(candidates.Count)];
                    if (candidate.Fitness < best.Fitness)
                    {
                        best = candidate;
                    }
                }

                parents.Add(best);
                candidates.Remove(best);
            }

            return parents;
        }

        private List<Individual> UniformCrossover(List<Individual> parents)
        {
            var children = new List<Individual>();
            var generation = Population.Max(i => i.Generation) + 1;

            for (int i = 0; i < parents.Count - 1; i += 2)
            {
                var parent1 = parents[i];
                var parent2 = parents[i + 1];

                for (int j = 0; j < OffspringPerPair; j++)
                {
                    var childChromosome = CreateChildChromosome(parent1.Chromosome, parent2.Chromosome);
                    var child = new Individual(childChromosome, generation)
                    {
                        Parents = new List<int> { parent1.Id, parent2.Id }
                    };
                    children.Add(child);
                }
            }

            return children;
        }

        private char[] CreateChildChromosome(char[] parent1, char[] parent2)
        {
            var chromosome = new char[parent1.Length];
            var usedChars = new HashSet<char>();

            // Copy genes from parent1 with bias
            for (int i = 0; i < chromosome.Length; i++)
            {
                if (_random.NextDouble() < 0.75)
                {
                    var gene = parent1[i];
                    if (!usedChars.Contains(gene))
                    {
                        chromosome[i] = gene;
                        usedChars.Add(gene);
                    }
                }
            }

            // Fill remaining positions from parent2
            for (int i = 0; i < chromosome.Length; i++)
            {
                if (chromosome[i] == default)
                {
                    foreach (var gene in parent2)
                    {
                        if (!usedChars.Contains(gene))
                        {
                            chromosome[i] = gene;
                            usedChars.Add(gene);
                            break;
                        }
                    }
                }
            }

            // Fill any remaining positions with unused genes
            var unusedGenes = parent1.Except(usedChars).ToList();
            _random.Shuffle(unusedGenes);

            for (int i = 0; i < chromosome.Length; i++)
            {
                if (chromosome[i] == default)
                {
                    chromosome[i] = unusedGenes.First();
                    unusedGenes.RemoveAt(0);
                }
            }

            return chromosome;
        }

        private void MutateChildren(List<Individual> children)
        {
            foreach (var child in children)
            {
                child.Chromosome = MutateLayout(child.Chromosome, MutationRate, 1);
            }
        }

        private char[] MutateLayout(char[] layout, double mutationRate, int maxMutations)
        {
            var mutated = (char[])layout.Clone();
            var mutationCount = _random.Next(1, maxMutations + 1);

            for (int i = 0; i < mutationCount; i++)
            {
                if (_random.NextDouble() < mutationRate)
                {
                    var pos1 = _random.Next(mutated.Length);
                    var pos2 = _random.Next(mutated.Length);
                    while (pos2 == pos1) pos2 = _random.Next(mutated.Length);

                    var temp = mutated[pos1];
                    mutated[pos1] = mutated[pos2];
                    mutated[pos2] = temp;
                }
            }

            return mutated;
        }

        private char[] GenerateRandomLayout()
        {
            var layout = "abcdefghijklmnopqrstuvwxyz".ToCharArray();
            _random.Shuffle(layout);
            return layout;
        }
    }

    /// <summary>
    /// Predefined keyboard layout
    /// </summary>
    public class LayoutPreset
    {
        public string Name { get; set; }
        public char[] Chromosome { get; set; }

        public LayoutPreset(string name, char[] chromosome)
        {
            Name = name;
            Chromosome = chromosome;
        }
    }

    /// <summary>
    /// Extension methods for randomization
    /// </summary>
    public static class RandomExtensions
    {
        public static void Shuffle<T>(this Random rng, IList<T> array)
        {
            int n = array.Count;
            while (n > 1)
            {
                int k = rng.Next(n--);
                T temp = array[n];
                array[n] = array[k];
                array[k] = temp;
            }
        }
    }
}