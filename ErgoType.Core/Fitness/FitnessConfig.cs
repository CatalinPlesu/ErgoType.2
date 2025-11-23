namespace ErgoType.Core.Fitness;

using System;

/// <summary>
/// Configuration for fitness evaluation.
/// </summary>
public record FitnessConfig
{
    /// <summary>
    /// Weight for distance component (0.0 to 1.0).
    /// </summary>
    public double DistanceWeight { get; init; } = 0.7;
    
    /// <summary>
    /// Weight for time component (0.0 to 1.0).
    /// </summary>
    public double TimeWeight { get; init; } = 0.3;
    
    /// <summary>
    /// Whether to use simplified fitness calculation.
    /// </summary>
    public bool UseSimplifiedFitness { get; init; } = true;
    
    /// <summary>
    /// Fitts law intercept constant.
    /// </summary>
    public double FittsA { get; init; } = 0.05;
    
    /// <summary>
    /// Fitts law slope constant.
    /// </summary>
    public double FittsB { get; init; } = 0.025;
    
    /// <summary>
    /// Size of the character window for simulation.
    /// </summary>
    public int SimulationWindowSize { get; init; } = 256;
    
    /// <summary>
    /// Validates the configuration.
    /// </summary>
    public FitnessConfig Validate()
    {
        if (DistanceWeight < 0 || DistanceWeight > 1)
            throw new ArgumentException("Distance weight must be between 0 and 1");
            
        if (TimeWeight < 0 || TimeWeight > 1)
            throw new ArgumentException("Time weight must be between 0 and 1");
            
        if (Math.Abs(DistanceWeight + TimeWeight - 1.0) > 0.001)
            throw new ArgumentException("Distance and time weights must sum to 1.0");
            
        return this;
    }
}

/// <summary>
/// Result of fitness evaluation.
/// </summary>
public record FitnessResult
{
    /// <summary>
    /// Overall fitness score (higher is better).
    /// </summary>
    public double Fitness { get; }
    
    /// <summary>
    /// Distance component score.
    /// </summary>
    public double DistanceScore { get; }
    
    /// <summary>
    /// Time component score.
    /// </summary>
    public double TimeScore { get; }
    
    /// <summary>
    /// Calculation time in milliseconds.
    /// </summary>
    public double CalculationTimeMs { get; }
    
    /// <summary>
    /// Whether the result was cached.
    /// </summary>
    public bool FromCache { get; }
    
    /// <summary>
    /// Creates a new fitness result.
    /// </summary>
    public FitnessResult(double fitness, double distanceScore, double timeScore, 
                        double calculationTimeMs, bool fromCache = false)
    {
        Fitness = fitness;
        DistanceScore = distanceScore;
        TimeScore = timeScore;
        CalculationTimeMs = calculationTimeMs;
        FromCache = fromCache;
    }
}