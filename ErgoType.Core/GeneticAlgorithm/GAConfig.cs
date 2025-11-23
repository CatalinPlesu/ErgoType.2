namespace ErgoType.Core.GeneticAlgorithm;

using System.Collections.Generic;

/// <summary>
/// Configuration for genetic algorithm parameters.
/// </summary>
public record GAConfig
{
    /// <summary>
    /// Population size.
    /// </summary>
    public int PopulationSize { get; init; } = 50;
    
    /// <summary>
    /// Maximum number of generations.
    /// </summary>
    public int MaxGenerations { get; init; } = 100;
    
    /// <summary>
    /// Tournament size for selection.
    /// </summary>
    public int TournamentSize { get; init; } = 3;
    
    /// <summary>
    /// Number of offspring per parent pair.
    /// </summary>
    public int OffspringPerPair { get; init; } = 4;
    
    /// <summary>
    /// Base mutation rate.
    /// </summary>
    public double MutationRate { get; init; } = 0.05;
    
    /// <summary>
    /// Stagnation limit before increasing mutation.
    /// </summary>
    public int StagnationLimit { get; init; } = 15;
    
    /// <summary>
    /// Number of elite individuals to preserve.
    /// </summary>
    public int EliteCount { get; init; } = 5;
    
    /// <summary>
    /// Validates the configuration.
    /// </summary>
    public GAConfig Validate()
    {
        if (PopulationSize < 10)
            throw new ArgumentException("Population size must be at least 10");
            
        if (MaxGenerations < 1)
            throw new ArgumentException("Max generations must be at least 1");
            
        if (TournamentSize < 2)
            throw new ArgumentException("Tournament size must be at least 2");
            
        if (OffspringPerPair < 1)
            throw new ArgumentException("Offspring per pair must be at least 1");
            
        if (MutationRate < 0 || MutationRate > 1)
            throw new ArgumentException("Mutation rate must be between 0 and 1");
            
        if (StagnationLimit < 1)
            throw new ArgumentException("Stagnation limit must be at least 1");
            
        if (EliteCount < 0 || EliteCount > PopulationSize / 2)
            throw new ArgumentException("Elite count must be between 0 and half population size");
            
        return this;
    }
}

/// <summary>
/// Result of genetic algorithm optimization.
/// </summary>
public record GAResult
{
    /// <summary>
    /// Best individual found.
    /// </summary>
    public Individual BestIndividual { get; }
    
    /// <summary>
    /// Number of generations executed.
    /// </summary>
    public int Generations { get; }
    
    /// <summary>
    /// Total execution time in milliseconds.
    /// </summary>
    public double ExecutionTimeMs { get; }
    
    /// <summary>
    /// Whether the algorithm stopped due to stagnation.
    /// </summary>
    public bool Stagnated { get; }
    
    /// <summary>
    /// Fitness history across generations.
    /// </summary>
    public IReadOnlyList<double> FitnessHistory { get; }
    
    /// <summary>
    /// Creates a new GA result.
    /// </summary>
    public GAResult(Individual bestIndividual, int generations, double executionTimeMs, 
                   bool stagnated, IReadOnlyList<double> fitnessHistory)
    {
        BestIndividual = bestIndividual;
        Generations = generations;
        ExecutionTimeMs = executionTimeMs;
        Stagnated = stagnated;
        FitnessHistory = fitnessHistory;
    }
}