namespace ErgoType.Tests;

using ErgoType.Core;
using ErgoType.Core.Fitness;
using ErgoType.Data;
using Xunit;

/// <summary>
/// Tests for keyboard layout optimization functionality.
/// </summary>
public class KeyboardLayoutTests
{
    /// <summary>
    /// Tests that a keyboard can be created successfully.
    /// </summary>
    [Fact]
    public void CanCreateKeyboard()
    {
        var keyboard = KeyboardFactory.CreateAnsi60Percent();
        
        Assert.NotNull(keyboard);
        Assert.Equal("ANSI 60%", keyboard.Name);
        Assert.True(keyboard.Keys.Count > 0);
        Assert.True(keyboard.AllKeys.Count > 0);
    }
    
    /// <summary>
    /// Tests that keyboard distance calculation works.
    /// </summary>
    [Fact]
    public void CanCalculateKeyDistance()
    {
        var keyboard = KeyboardFactory.CreateAnsi60Percent();
        
        var distance = keyboard.GetDistance("q", "w");
        
        Assert.True(distance > 0);
        Assert.True(distance < 100); // Reasonable distance
    }
    
    /// <summary>
    /// Tests that keyboard layout can be created.
    /// </summary>
    [Fact]
    public void CanCreateKeyboardLayout()
    {
        var layout = KeyboardLayout.Create("test", "qwertyuiopasdfghjklzxcvbnm".ToCharArray());
        
        Assert.NotNull(layout);
        Assert.Equal("test", layout.Name);
        Assert.Equal(26, layout.Chromosome.Length);
        Assert.Equal("qwertyuiopasdfghjklzxcvbnm", layout.ToString());
    }
    
    /// <summary>
    /// Tests that individual can be created.
    /// </summary>
    [Fact]
    public void CanCreateIndividual()
    {
        var layout = KeyboardLayout.Create("test", "qwertyuiopasdfghjklzxcvbnm".ToCharArray());
        var individual = new Individual(1, "test", layout, 0);
        
        Assert.NotNull(individual);
        Assert.Equal(1, individual.Id);
        Assert.Equal("test", individual.Name);
        Assert.Equal(layout, individual.Layout);
        Assert.Equal(0, individual.Generation);
        Assert.Null(individual.Fitness);
    }
    
    /// <summary>
    /// Tests that fitness configuration validates correctly.
    /// </summary>
    [Fact]
    public void FitnessConfigValidatesCorrectly()
    {
        var config = new FitnessConfig
        {
            DistanceWeight = 0.7,
            TimeWeight = 0.3
        };
        
        var validatedConfig = config.Validate();
        
        Assert.Equal(0.7, validatedConfig.DistanceWeight);
        Assert.Equal(0.3, validatedConfig.TimeWeight);
    }
    
    /// <summary>
    /// Tests that fitness configuration validation fails with invalid weights.
    /// </summary>
    [Fact]
    public void FitnessConfigValidationFailsWithInvalidWeights()
    {
        var config = new FitnessConfig
        {
            DistanceWeight = 0.5,
            TimeWeight = 0.6 // Sum > 1.0
        };
        
        Assert.Throws<ArgumentException>(() => config.Validate());
    }
    
    /// <summary>
    /// Tests that GA configuration validates correctly.
    /// </summary>
    [Fact]
    public void GAConfigValidatesCorrectly()
    {
        var config = new GeneticAlgorithm.GAConfig
        {
            PopulationSize = 50,
            MaxGenerations = 100,
            TournamentSize = 3
        };
        
        var validatedConfig = config.Validate();
        
        Assert.Equal(50, validatedConfig.PopulationSize);
        Assert.Equal(100, validatedConfig.MaxGenerations);
        Assert.Equal(3, validatedConfig.TournamentSize);
    }
    
    /// <summary>
    /// Tests that simplified fitness evaluator can evaluate a layout.
    /// </summary>
    [Fact]
    public void SimplifiedFitnessEvaluatorCanEvaluateLayout()
    {
        var keyboard = KeyboardFactory.CreateAnsi60Percent();
        var layout = KeyboardLayout.Create("test", "qwertyuiopasdfghjklzxcvbnm".ToCharArray());
        var evaluator = new SimplifiedFitnessEvaluator(new FitnessConfig());
        
        var result = evaluator.Evaluate(layout, keyboard);
        
        Assert.NotNull(result);
        Assert.True(result.Fitness >= 0.0 && result.Fitness <= 1.0);
        Assert.True(result.DistanceScore >= 0);
        Assert.True(result.TimeScore >= 0);
        Assert.True(result.CalculationTimeMs >= 0);
    }
    
    /// <summary>
    /// Tests that keyboard layout optimizer can be created.
    /// </summary>
    [Fact]
    public void CanCreateKeyboardLayoutOptimizer()
    {
        var config = new OptimizationConfig();
        var optimizer = new KeyboardLayoutOptimizer(config);
        
        Assert.NotNull(optimizer);
        Assert.Equal(config, optimizer.Config);
        Assert.NotNull(optimizer.CurrentKeyboard);
        Assert.NotNull(optimizer.CurrentFitnessEvaluator);
    }
    
    /// <summary>
    /// Tests that layout comparison works.
    /// </summary>
    [Fact]
    public void CanCompareLayouts()
    {
        var config = new OptimizationConfig();
        var optimizer = new KeyboardLayoutOptimizer(config);
        
        var results = optimizer.CompareLayouts("QWERTY", "Dvorak");
        
        Assert.NotNull(results);
        Assert.True(results.ContainsKey("QWERTY"));
        Assert.True(results.ContainsKey("Dvorak"));
        Assert.True(results["QWERTY"].Fitness >= 0.0 && results["QWERTY"].Fitness <= 1.0);
        Assert.True(results["Dvorak"].Fitness >= 0.0 && results["Dvorak"].Fitness <= 1.0);
    }
}