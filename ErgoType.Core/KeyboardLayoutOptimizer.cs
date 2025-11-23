namespace ErgoType.Core;

using System;
using System.Collections.Generic;
using ErgoType.Core.Fitness;
using ErgoType.Core.GeneticAlgorithm;

/// <summary>
/// Configuration for keyboard layout optimization.
/// </summary>
public record OptimizationConfig
{
    /// <summary>
    /// Genetic algorithm configuration.
    /// </summary>
    public GAConfig GAConfig { get; init; } = new();
    
    /// <summary>
    /// Fitness evaluation configuration.
    /// </summary>
    public FitnessConfig FitnessConfig { get; init; } = new();
    
    /// <summary>
    /// Keyboard layout to use.
    /// </summary>
    public string KeyboardLayout { get; init; } = "ANSI_60%";
    
    /// <summary>
    /// Whether to enable detailed logging.
    /// </summary>
    public bool Verbose { get; init; } = false;
    
    /// <summary>
    /// Validates the configuration.
    /// </summary>
    public OptimizationConfig Validate()
    {
        GAConfig.Validate();
        FitnessConfig.Validate();
        
        if (string.IsNullOrWhiteSpace(KeyboardLayout))
            throw new ArgumentException("Keyboard layout cannot be empty");
            
        return this;
    }
}

/// <summary>
/// Main keyboard layout optimizer orchestrating genetic algorithms and fitness evaluation.
/// </summary>
public class KeyboardLayoutOptimizer
{
    /// <summary>
    /// Configuration for optimization.
    /// </summary>
    public OptimizationConfig Config { get; }
    
    /// <summary>
    /// Current keyboard being optimized.
    /// </summary>
    public Keyboard CurrentKeyboard { get; private set; }
    
    /// <summary>
    /// Current fitness evaluator.
    /// </summary>
    public IFitnessEvaluator CurrentFitnessEvaluator { get; private set; }
    
    /// <summary>
    /// Creates a new keyboard layout optimizer.
    /// </summary>
    public KeyboardLayoutOptimizer(OptimizationConfig? config = null)
    {
        Config = config?.Validate() ?? new OptimizationConfig().Validate();
        CurrentKeyboard = CreateKeyboard(Config.KeyboardLayout);
        CurrentFitnessEvaluator = new Fitness.SimplifiedFitnessEvaluator(Config.FitnessConfig);
    }
    
    /// <summary>
    /// Sets a custom fitness evaluator.
    /// </summary>
    public void SetFitnessEvaluator(IFitnessEvaluator evaluator)
    {
        CurrentFitnessEvaluator = evaluator ?? 
            throw new ArgumentNullException(nameof(evaluator));
    }
    
    /// <summary>
    /// Sets a different keyboard layout.
    /// </summary>
    public void SetKeyboard(string keyboardLayout)
    {
        CurrentKeyboard = CreateKeyboard(keyboardLayout);
    }
    
    /// <summary>
    /// Optimizes a keyboard layout using genetic algorithm.
    /// </summary>
    /// <returns>Optimization result with best layout found.</returns>
    public GAResult Optimize()
    {
        Console.WriteLine("=".PadRight(80, '='));
        Console.WriteLine("KEYBOARD LAYOUT OPTIMIZATION");
        Console.WriteLine("=".PadRight(80, '='));
        Console.WriteLine($"Keyboard: {CurrentKeyboard.Name}");
        Console.WriteLine($"Fitness: {CurrentFitnessEvaluator.GetType().Name}");
        Console.WriteLine($"Population: {Config.GAConfig.PopulationSize}");
        Console.WriteLine($"Max Generations: {Config.GAConfig.MaxGenerations}");
        Console.WriteLine("Starting optimization...\n");
        
        var ga = new GeneticAlgorithm.GeneticAlgorithm(
            Config.GAConfig, 
            CurrentFitnessEvaluator, 
            CurrentKeyboard
        );
        
        var result = ga.Run();
        
        Console.WriteLine("\n" + "=".PadRight(80, '='));
        Console.WriteLine("OPTIMIZATION COMPLETE");
        Console.WriteLine("=".PadRight(80, '='));
        Console.WriteLine($"Best Layout: {result.BestIndividual.Name}");
        Console.WriteLine($"Fitness: {result.BestIndividual.Fitness?.ToString("F6") ?? "N/A"}");
        Console.WriteLine($"Generations: {result.Generations}");
        Console.WriteLine($"Execution Time: {result.ExecutionTimeMs:F0}ms");
        Console.WriteLine($"Layout: {result.BestIndividual.Layout}");
        Console.WriteLine("=".PadRight(80, '='));
        
        return result;
    }
    
    /// <summary>
    /// Compares multiple keyboard layouts.
    /// </summary>
    /// <param name="layoutNames">Names of layouts to compare.</param>
    /// <returns>Comparison results.</returns>
    public Dictionary<string, Fitness.FitnessResult> CompareLayouts(params string[] layoutNames)
    {
        var results = new Dictionary<string, Fitness.FitnessResult>();
        
        foreach (var layoutName in layoutNames)
        {
            var layout = GetStandardLayout(layoutName);
            if (layout is not null)
            {
                var fitnessResult = CurrentFitnessEvaluator.Evaluate(layout, CurrentKeyboard);
                results[layoutName] = fitnessResult;
                
                if (Config.Verbose)
                {
                    Console.WriteLine($"{layoutName}: Fitness={fitnessResult.Fitness:F6}, " +
                                    $"Distance={fitnessResult.DistanceScore:F1}, Time={fitnessResult.TimeScore:F1}");
                }
            }
        }
        
        return results;
    }
    
    /// <summary>
    /// Evaluates a specific layout.
    /// </summary>
    /// <param name="layout">Layout to evaluate.</param>
    /// <returns>Fitness result.</returns>
    public Fitness.FitnessResult EvaluateLayout(KeyboardLayout layout)
    {
        return CurrentFitnessEvaluator.Evaluate(layout, CurrentKeyboard);
    }
    
    /// <summary>
    /// Creates a keyboard based on the specified layout name.
    /// </summary>
    private Keyboard CreateKeyboard(string layoutName)
    {
        return layoutName.ToLower() switch
        {
            "ansi_60%" or "ansi60" or "60%" => KeyboardFactory.CreateAnsi60Percent(),
            "dactyl" or "dactyl_manuform" or "manuform" => KeyboardFactory.CreateDactylManuForm(),
            "ferris" or "ferris_sweep" or "sweep" => KeyboardFactory.CreateFerrisSweep(),
            _ => KeyboardFactory.CreateAnsi60Percent() // Default
        };
    }
    
    /// <summary>
    /// Gets a standard keyboard layout by name.
    /// </summary>
    private KeyboardLayout? GetStandardLayout(string layoutName)
    {
        return layoutName.ToLower() switch
        {
            "qwerty" => KeyboardLayout.Create("qwerty", "qwertyuiopasdfghjklzxcvbnm".ToCharArray()),
            "dvorak" => KeyboardLayout.Create("dvorak", "pyfgcrlaoeuidhtnsqjkxbmwvz".ToCharArray()),
            "colemak" => KeyboardLayout.Create("colemak", "qwfpgjluyarstdhneiozxcvmbk".ToCharArray()),
            "workman" => KeyboardLayout.Create("workman", "qdrwypfujelsiozhaxngctmbvk".ToCharArray()),
            "asset" => KeyboardLayout.Create("asset", "amswfdtugnelkhirozcypbqvjx".ToCharArray()),
            "norman" => KeyboardLayout.Create("norman", "qwfpgjluyarasdhtneoizxcdvbm".ToCharArray()),
            "minimak" => KeyboardLayout.Create("minimak", "qwfpgjluyarstdhneiozxcvbm".ToCharArray()),
            _ => null
        };
    }
}