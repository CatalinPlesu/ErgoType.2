namespace ErgoType.Core.Fitness;

using System;
using System.Collections.Generic;
using System.Linq;

/// <summary>
/// Interface for fitness evaluation strategies.
/// </summary>
public interface IFitnessEvaluator
{
    /// <summary>
    /// Evaluates the fitness of a keyboard layout.
    /// </summary>
    /// <param name="layout">The layout to evaluate.</param>
    /// <param name="keyboard">The keyboard to use for evaluation.</param>
    /// <returns>Fitness result.</returns>
    FitnessResult Evaluate(KeyboardLayout layout, Keyboard keyboard);
    
    /// <summary>
    /// Gets the configuration used by this evaluator.
    /// </summary>
    FitnessConfig Config { get; }
}

/// <summary>
/// Simplified fitness evaluator using distance and time calculations.
/// </summary>
public class SimplifiedFitnessEvaluator : IFitnessEvaluator
{
    /// <summary>
    /// Configuration for fitness evaluation.
    /// </summary>
    public FitnessConfig Config { get; }
    
    /// <summary>
    /// Character frequency data.
    /// </summary>
    private readonly Dictionary<char, double> _charFrequencies;
    
    /// <summary>
    /// Bigram frequency data.
    /// </summary>
    private readonly Dictionary<string, double> _bigramFrequencies;
    
    /// <summary>
    /// Normalization bounds for fitness calculation.
    /// </summary>
    private (double minDistance, double maxDistance, double minTime, double maxTime) _bounds;
    
    /// <summary>
    /// Creates a new simplified fitness evaluator.
    /// </summary>
    public SimplifiedFitnessEvaluator(FitnessConfig config)
    {
        Config = config.Validate();
        _charFrequencies = LoadCharacterFrequencies();
        _bigramFrequencies = LoadBigramFrequencies();
        _bounds = (double.MaxValue, double.MinValue, double.MaxValue, double.MinValue);
    }
    
    /// <summary>
    /// Sets the normalization bounds for fitness calculation.
    /// </summary>
    public void SetBounds(double minDistance, double maxDistance, double minTime, double maxTime)
    {
        _bounds = (minDistance, maxDistance, minTime, maxTime);
    }
    
    /// <summary>
    /// Evaluates the fitness of a keyboard layout.
    /// </summary>
    public FitnessResult Evaluate(KeyboardLayout layout, Keyboard keyboard)
    {
        var startTime = DateTime.Now;
        
        // Calculate distance and time scores
        var distanceScore = CalculateDistanceScore(layout, keyboard);
        var timeScore = CalculateTimeScore(layout, keyboard);
        
        // Update bounds for normalization
        UpdateBounds(distanceScore, timeScore);
        
        // Normalize scores if bounds are available
        var normalizedDistance = NormalizeDistance(distanceScore);
        var normalizedTime = NormalizeTime(timeScore);
        
        // Calculate weighted fitness (inverted since lower scores are better)
        var sickness = Config.DistanceWeight * normalizedDistance + Config.TimeWeight * normalizedTime;
        var fitness = 1.0 - sickness;
        
        var calculationTime = (DateTime.Now - startTime).TotalMilliseconds;
        
        return new FitnessResult(fitness, distanceScore, timeScore, calculationTime);
    }
    
    /// <summary>
    /// Calculates the total distance score for typing common text.
    /// </summary>
    private double CalculateDistanceScore(KeyboardLayout layout, Keyboard keyboard)
    {
        double totalDistance = 0;
        int totalTransitions = 0;
        
        // Use a representative text sample for distance calculation
        var sampleText = GetSampleText();
        var keyMap = CreateKeyMap(layout, keyboard);
        
        for (int i = 0; i < sampleText.Length - 1; i++)
        {
            var fromChar = char.ToLower(sampleText[i]);
            var toChar = char.ToLower(sampleText[i + 1]);
            
            if (keyMap.TryGetValue(fromChar, out var fromKey) && 
                keyMap.TryGetValue(toChar, out var toKey))
            {
                totalDistance += keyboard.GetDistance(fromKey, toKey);
                totalTransitions++;
            }
        }
        
        return totalTransitions > 0 ? totalDistance / totalTransitions : 0;
    }
    
    /// <summary>
    /// Calculates the total time score for typing common text.
    /// </summary>
    private double CalculateTimeScore(KeyboardLayout layout, Keyboard keyboard)
    {
        double totalTime = 0;
        int totalTransitions = 0;
        
        var sampleText = GetSampleText();
        var keyMap = CreateKeyMap(layout, keyboard);
        
        for (int i = 0; i < sampleText.Length - 1; i++)
        {
            var fromChar = char.ToLower(sampleText[i]);
            var toChar = char.ToLower(sampleText[i + 1]);
            
            if (keyMap.TryGetValue(fromChar, out var fromKey) && 
                keyMap.TryGetValue(toChar, out var toKey))
            {
                var distance = keyboard.GetDistance(fromKey, toKey);
                var fromKeyObj = keyboard.GetKey(fromKey);
                var toKeyObj = keyboard.GetKey(toKey);
                
                if (fromKeyObj is not null && toKeyObj is not null)
                {
                    // Fitts law calculation
                    var width = 0.019; // Key width (assumed)
                    var movementTime = Config.FittsA + Config.FittsB * Math.Log2(distance / width + 1);
                    
                    // Add finger strength modifier
                    var fingerStrength = toKeyObj.Finger.GetStrengthMultiplier();
                    totalTime += movementTime * fingerStrength;
                    totalTransitions++;
                }
            }
        }
        
        return totalTransitions > 0 ? totalTime / totalTransitions : 0;
    }
    
    /// <summary>
    /// Creates a mapping from characters to key IDs.
    /// </summary>
    private Dictionary<char, string> CreateKeyMap(KeyboardLayout layout, Keyboard keyboard)
    {
        var keyMap = new Dictionary<char, string>();
        var keys = keyboard.AllKeys.ToList();
        
        for (int i = 0; i < Math.Min(layout.Chromosome.Length, keys.Count); i++)
        {
            keyMap[layout.Chromosome[i]] = keys[i].Id;
        }
        
        return keyMap;
    }
    
    /// <summary>
    /// Updates the normalization bounds.
    /// </summary>
    private void UpdateBounds(double distance, double time)
    {
        _bounds = (
            Math.Min(_bounds.minDistance, distance),
            Math.Max(_bounds.maxDistance, distance),
            Math.Min(_bounds.minTime, time),
            Math.Max(_bounds.maxTime, time)
        );
    }
    
    /// <summary>
    /// Normalizes distance score to 0-1 range.
    /// </summary>
    private double NormalizeDistance(double distance)
    {
        if (_bounds.maxDistance <= _bounds.minDistance) return 0.5;
        return Math.Min(1.0, Math.Max(0.0, distance / _bounds.maxDistance));
    }
    
    /// <summary>
    /// Normalizes time score to 0-1 range.
    /// </summary>
    private double NormalizeTime(double time)
    {
        if (_bounds.maxTime <= _bounds.minTime) return 0.5;
        return Math.Min(1.0, Math.Max(0.0, time / _bounds.maxTime));
    }
    
    /// <summary>
    /// Gets a sample text for fitness evaluation.
    /// </summary>
    private string GetSampleText() => 
        "the quick brown fox jumps over the lazy dog " +
        "and now for something completely different " +
        "hello world programming examples " +
        "sample text for keyboard layout evaluation";
    
    /// <summary>
    /// Loads character frequency data.
    /// </summary>
    private Dictionary<char, double> LoadCharacterFrequencies() => new()
    {
        ['e'] = 0.127, ['t'] = 0.091, ['a'] = 0.082, ['o'] = 0.075, ['i'] = 0.070,
        ['n'] = 0.067, ['s'] = 0.063, ['h'] = 0.061, ['r'] = 0.060, ['d'] = 0.043,
        ['l'] = 0.040, ['c'] = 0.028, ['u'] = 0.028, ['m'] = 0.024, ['w'] = 0.024,
        ['f'] = 0.022, ['g'] = 0.020, ['y'] = 0.020, ['p'] = 0.019, ['b'] = 0.015,
        ['v'] = 0.009, ['k'] = 0.008, ['j'] = 0.002, ['x'] = 0.002, ['q'] = 0.001,
        ['z'] = 0.001
    };
    
    /// <summary>
    /// Loads bigram frequency data.
    /// </summary>
    private Dictionary<string, double> LoadBigramFrequencies() => new()
    {
        ["th"] = 0.0315, ["he"] = 0.0251, ["in"] = 0.0211, ["er"] = 0.0175,
        ["an"] = 0.0122, ["re"] = 0.0085, ["es"] = 0.0083, ["on"] = 0.0078,
        ["st"] = 0.0072, ["nt"] = 0.0067
    };
}