namespace ErgoType.Core;

using System;

/// <summary>
/// Represents an individual in the genetic algorithm population.
/// </summary>
public class Individual
{
    /// <summary>
    /// Unique identifier for the individual.
    /// </summary>
    public int Id { get; set; }
    
    /// <summary>
    /// Name or identifier for the individual.
    /// </summary>
    public string Name { get; set; }
    
    /// <summary>
    /// The keyboard layout chromosome.
    /// </summary>
    public KeyboardLayout Layout { get; set; }
    
    /// <summary>
    /// Fitness value (higher is better).
    /// </summary>
    public double? Fitness { get; set; }
    
    /// <summary>
    /// Generation this individual belongs to.
    /// </summary>
    public int Generation { get; set; }
    
    /// <summary>
    /// Parent identifiers.
    /// </summary>
    public int[] Parents { get; set; }
    
    /// <summary>
    /// Creates a new individual.
    /// </summary>
    public Individual(int id, string name, KeyboardLayout layout, int generation = 0, int[]? parents = null)
    {
        Id = id;
        Name = name;
        Layout = layout;
        Generation = generation;
        Parents = parents ?? Array.Empty<int>();
    }
    
    /// <summary>
    /// Creates a copy of this individual with optional modifications.
    /// </summary>
    public Individual Copy(
        string? name = null, 
        double? fitness = null, 
        int? generation = null,
        int[]? parents = null) => 
        new Individual(Id, name ?? Name, Layout, generation ?? Generation, parents ?? Parents)
        {
            Fitness = fitness ?? Fitness
        };
    
    /// <summary>
    /// Returns a string representation of the individual.
    /// </summary>
    public override string ToString() => 
        $"Individual(Id={Id}, Name={Name}, Fitness={Fitness?.ToString("F6") ?? "null"})";
}