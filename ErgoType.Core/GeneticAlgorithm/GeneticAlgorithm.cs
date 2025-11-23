namespace ErgoType.Core.GeneticAlgorithm;

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using ErgoType.Core.Fitness;

/// <summary>
/// Main genetic algorithm implementation for keyboard layout optimization.
/// </summary>
public class GeneticAlgorithm
{
    /// <summary>
    /// Configuration for the genetic algorithm.
    /// </summary>
    public GAConfig Config { get; }
    
    /// <summary>
    /// Fitness evaluator used for layout evaluation.
    /// </summary>
    public IFitnessEvaluator FitnessEvaluator { get; }
    
    /// <summary>
    /// Keyboard layout used for evaluation.
    /// </summary>
    public Keyboard Keyboard { get; }
    
    /// <summary>
    /// Current population.
    /// </summary>
    public IReadOnlyList<Individual> Population => _population;
    
    /// <summary>
    /// Best individual found so far.
    /// </summary>
    public Individual? BestIndividual => _population.FirstOrDefault();
    
    /// <summary>
    /// Current generation number.
    /// </summary>
    public int CurrentGeneration { get; private set; }
    
    /// <summary>
    /// Number of generations without improvement.
    /// </summary>
    public int StagnationCount { get; private set; }
    
    /// <summary>
    /// Fitness history across generations.
    /// </summary>
    public IReadOnlyList<double> FitnessHistory => _fitnessHistory;
    
    private List<Individual> _population;
    private readonly List<double> _fitnessHistory;
    private readonly Random _random;
    private readonly Dictionary<string, Individual> _individualCache;
    
    /// <summary>
    /// Creates a new genetic algorithm instance.
    /// </summary>
    public GeneticAlgorithm(GAConfig config, IFitnessEvaluator fitnessEvaluator, Keyboard keyboard)
    {
        Config = config.Validate();
        FitnessEvaluator = fitnessEvaluator;
        Keyboard = keyboard;
        
        _population = new List<Individual>();
        _fitnessHistory = new List<double>();
        _random = new Random();
        _individualCache = new Dictionary<string, Individual>();
        
        InitializePopulation();
    }
    
    /// <summary>
    /// Runs the genetic algorithm optimization.
    /// </summary>
    /// <returns>Optimization result.</returns>
    public GAResult Run()
    {
        var startTime = DateTime.Now;
        
        Console.WriteLine("Starting Genetic Algorithm Optimization...");
        Console.WriteLine($"Population: {Config.PopulationSize}, Max Generations: {Config.MaxGenerations}");
        
        EvaluatePopulation();
        UpdateBestIndividual();
        
        while (CurrentGeneration < Config.MaxGenerations && StagnationCount < Config.StagnationLimit)
        {
            var generationStart = DateTime.Now;
            
            Console.WriteLine($"\nGeneration {CurrentGeneration + 1}/{Config.MaxGenerations}");
            Console.WriteLine($"Best Fitness: {BestIndividual?.Fitness?.ToString("F6") ?? "N/A"}");
            Console.WriteLine($"Stagnation: {StagnationCount}/{Config.StagnationLimit}");
            
            var parents = SelectParents();
            var children = CreateChildren(parents);
            MutateChildren(children);
            
            ReplacePopulation(children);
            EvaluatePopulation();
            UpdateBestIndividual();
            
            var generationTime = (DateTime.Now - generationStart).TotalMilliseconds;
            Console.WriteLine($"Generation completed in {generationTime:F0}ms");
            
            CurrentGeneration++;
        }
        
        var totalTime = (DateTime.Now - startTime).TotalMilliseconds;
        
        return new GAResult(
            BestIndividual ?? throw new InvalidOperationException("No best individual found"),
            CurrentGeneration,
            totalTime,
            StagnationCount >= Config.StagnationLimit,
            _fitnessHistory.ToList()
        );
    }
    
    /// <summary>
    /// Initializes the population with heuristic and random layouts.
    /// </summary>
    private void InitializePopulation()
    {
        _population.Clear();
        CurrentGeneration = 0;
        StagnationCount = 0;
        
        // Add heuristic layouts (QWERTY, Dvorak, etc.)
        var heuristicLayouts = GetHeuristicLayouts();
        foreach (var layout in heuristicLayouts.Take(Config.PopulationSize / 2))
        {
            _population.Add(new Individual(
                _population.Count,
                layout.Name,
                layout,
                0
            ));
        }
        
        // Add random layouts to fill the population
        var baseLayout = heuristicLayouts.First();
        while (_population.Count < Config.PopulationSize)
        {
            var randomLayout = CreateRandomLayout(baseLayout);
            _population.Add(new Individual(
                _population.Count,
                $"random_{_population.Count}",
                randomLayout,
                0
            ));
        }
        
        Console.WriteLine($"Initialized population with {_population.Count} individuals");
    }
    
    /// <summary>
    /// Evaluates fitness for all individuals in the population.
    /// </summary>
    private void EvaluatePopulation()
    {
        var toEvaluate = _population.Where(i => i.Fitness is null).ToList();
        
        if (!toEvaluate.Any()) return;
        
        Console.WriteLine($"Evaluating {toEvaluate.Count} individuals...");
        
        // Use parallel processing for fitness evaluation
        var parallelOptions = new ParallelOptions 
        { 
            MaxDegreeOfParallelism = Environment.ProcessorCount 
        };
        
        Parallel.ForEach(toEvaluate, parallelOptions, individual =>
        {
            var fitnessResult = FitnessEvaluator.Evaluate(individual.Layout, Keyboard);
            lock (_population)
            {
                var index = _population.IndexOf(individual);
                if (index >= 0)
                {
                    _population[index] = individual.Copy(fitness: fitnessResult.Fitness);
                }
            }
        });
        
        // Sort population by fitness (best first)
        _population = _population
            .OrderByDescending(i => i.Fitness)
            .ToList();
    }
    
    /// <summary>
    /// Updates the best individual and fitness history.
    /// </summary>
    private void UpdateBestIndividual()
    {
        var bestFitness = BestIndividual?.Fitness ?? 0;
        _fitnessHistory.Add(bestFitness);
        
        if (_fitnessHistory.Count > 1 && 
            Math.Abs(_fitnessHistory.Last() - _fitnessHistory[^2]) < 0.0001)
        {
            StagnationCount++;
        }
        else
        {
            StagnationCount = 0;
        }
    }
    
    /// <summary>
    /// Selects parents using tournament selection.
    /// </summary>
    private List<Individual> SelectParents()
    {
        var parents = new List<Individual>();
        var candidates = _population.Take(_population.Count - Config.EliteCount).ToList();
        
        while (parents.Count < _population.Count - Config.EliteCount)
        {
            var tournament = candidates
                .OrderBy(x => _random.Next())
                .Take(Config.TournamentSize)
                .MaxBy(x => x.Fitness);
                
            if (tournament is not null)
                parents.Add(tournament);
        }
        
        return parents;
    }
    
    /// <summary>
    /// Creates children through uniform crossover.
    /// </summary>
    private List<Individual> CreateChildren(List<Individual> parents)
    {
        var children = new List<Individual>();
        var usedLayouts = new HashSet<string>();
        
        for (int i = 0; i < parents.Count; i += 2)
        {
            if (i + 1 >= parents.Count) break;
            
            var parent1 = parents[i];
            var parent2 = parents[i + 1];
            
            for (int j = 0; j < Config.OffspringPerPair; j++)
            {
                var childLayout = UniformCrossover(parent1.Layout, parent2.Layout);
                var layoutKey = new string(childLayout.Chromosome);
                
                if (!usedLayouts.Contains(layoutKey))
                {
                    usedLayouts.Add(layoutKey);
                    children.Add(new Individual(
                        _population.Count + children.Count,
                        $"child_{i}_{j}",
                        childLayout,
                        CurrentGeneration + 1,
                        new[] { parent1.Id, parent2.Id }
                    ));
                }
            }
        }
        
        return children;
    }
    
    /// <summary>
    /// Performs uniform crossover between two parent layouts.
    /// </summary>
    private KeyboardLayout UniformCrossover(KeyboardLayout parent1, KeyboardLayout parent2)
    {
        var chromosome = new char[parent1.Chromosome.Length];
        var usedChars = new HashSet<char>();
        var remainingChars = new List<char>(parent2.Chromosome);
        
        // Copy genes from parent1 with bias
        for (int i = 0; i < chromosome.Length; i++)
        {
            if (_random.NextDouble() < 0.75) // 75% bias towards better parent
            {
                var gene = parent1.Chromosome[i];
                if (!usedChars.Contains(gene))
                {
                    chromosome[i] = gene;
                    usedChars.Add(gene);
                    remainingChars.Remove(gene);
                }
            }
        }
        
        // Fill remaining positions with genes from parent2
        var remainingPositions = Enumerable.Range(0, chromosome.Length)
            .Where(i => chromosome[i] == '\0')
            .ToList();
            
        _random.Shuffle(remainingChars);
        
        for (int i = 0; i < remainingPositions.Count; i++)
        {
            chromosome[remainingPositions[i]] = remainingChars[i];
        }
        
        return KeyboardLayout.Create($"crossover_{_random.Next()}", chromosome);
    }
    
    /// <summary>
    /// Applies mutation to children.
    /// </summary>
    private void MutateChildren(List<Individual> children)
    {
        var mutationRate = Config.MutationRate;
        
        // Increase mutation rate if stagnant
        if (StagnationCount > 0)
        {
            mutationRate *= 1.0 + (StagnationCount * 0.1);
            mutationRate = Math.Min(mutationRate, 0.2);
        }
        
        foreach (var child in children)
        {
            if (_random.NextDouble() < mutationRate)
            {
                var mutatedChromosome = MutateChromosome(child.Layout.Chromosome);
                var mutatedLayout = KeyboardLayout.Create(child.Layout.Name, mutatedChromosome);
                var mutatedChild = child.Copy(name: $"mutated_{child.Name}");
                mutatedChild.Layout = mutatedLayout;
                
                // Replace in children list
                var index = children.IndexOf(child);
                children[index] = mutatedChild;
            }
        }
    }
    
    /// <summary>
    /// Mutates a chromosome using swap mutation.
    /// </summary>
    private char[] MutateChromosome(char[] chromosome)
    {
        var mutated = chromosome.ToArray();
        var numMutations = _random.Next(1, 4); // 1-3 swaps
        
        for (int i = 0; i < numMutations; i++)
        {
            var pos1 = _random.Next(mutated.Length);
            var pos2 = _random.Next(mutated.Length);
            
            if (pos1 != pos2)
            {
                var temp = mutated[pos1];
                mutated[pos1] = mutated[pos2];
                mutated[pos2] = temp;
            }
        }
        
        return mutated;
    }
    
    /// <summary>
    /// Replaces the population with new individuals.
    /// </summary>
    private void ReplacePopulation(List<Individual> children)
    {
        // Keep elite individuals
        var elite = _population.Take(Config.EliteCount).ToList();
        
        // Add children and fill remaining spots
        var newPopulation = elite.Concat(children)
            .Take(Config.PopulationSize)
            .ToList();
            
        // Fill any remaining spots with random individuals
        var baseLayout = GetHeuristicLayouts().First();
        while (newPopulation.Count < Config.PopulationSize)
        {
            var randomLayout = CreateRandomLayout(baseLayout);
            newPopulation.Add(new Individual(
                _population.Count + newPopulation.Count,
                $"random_{newPopulation.Count}",
                randomLayout,
                CurrentGeneration + 1
            ));
        }
        
        _population = newPopulation;
    }
    
    /// <summary>
    /// Creates a random layout by shuffling a base layout.
    /// </summary>
    private KeyboardLayout CreateRandomLayout(KeyboardLayout baseLayout)
    {
        var chromosome = baseLayout.Chromosome.ToArray();
        _random.Shuffle(chromosome);
        return KeyboardLayout.Create($"random_{_random.Next()}", chromosome);
    }
    
    /// <summary>
    /// Gets heuristic keyboard layouts for initialization.
    /// </summary>
    private List<KeyboardLayout> GetHeuristicLayouts()
    {
        return new List<KeyboardLayout>
        {
            // QWERTY layout
            KeyboardLayout.Create("qwerty", "qwertyuiopasdfghjklzxcvbnm".ToCharArray()),
            
            // Dvorak layout  
            KeyboardLayout.Create("dvorak", "pyfgcrlaoeuidhtnsqjkxbmwvz".ToCharArray()),
            
            // Colemak layout
            KeyboardLayout.Create("colemak", "qwfpgjluyarstdhneiozxcvmbk".ToCharArray()),
            
            // Workman layout
            KeyboardLayout.Create("workman", "qdrwypfujelsiozhaxngctmbvk".ToCharArray()),
            
            // Asset layout
            KeyboardLayout.Create("asset", "amswfdtugnelkhirozcypbqvjx".ToCharArray()),
            
            // Norman layout
            KeyboardLayout.Create("norman", "qwfpgjluyarasdhtneoizxcdvbm".ToCharArray()),
            
            // Minimal layout
            KeyboardLayout.Create("minimak", "qwfpgjluyarstdhneiozxcvbm".ToCharArray())
        };
    }
}

/// <summary>
/// Extensions for Random class.
/// </summary>
public static class RandomExtensions
{
    /// <summary>
    /// Shuffles a list in place using Fisher-Yates algorithm.
    /// </summary>
    public static void Shuffle<T>(this Random random, IList<T> list)
    {
        for (int i = list.Count - 1; i > 0; i--)
        {
            int j = random.Next(i + 1);
            var temp = list[i];
            list[i] = list[j];
            list[j] = temp;
        }
    }
}