namespace ErgoType.Core;

using System;
using System.Linq;

/// <summary>
/// Represents a keyboard layout chromosome as a permutation of characters.
/// </summary>
public record KeyboardLayout(string Name, char[] Chromosome)
{
    /// <summary>
    /// Creates a new layout with the specified name and chromosome.
    /// </summary>
    public static KeyboardLayout Create(string name, char[] chromosome) => 
        new(name, chromosome.ToArray());
    
    /// <summary>
    /// Creates a copy of this layout.
    /// </summary>
    public KeyboardLayout Copy(string? name = null) => 
        new(name ?? Name, Chromosome.ToArray());
    
    /// <summary>
    /// Gets the chromosome as a string.
    /// </summary>
    public override string ToString() => new string(Chromosome);
    
    /// <summary>
    /// Checks if this layout is identical to another layout.
    /// </summary>
    public bool IsIdenticalTo(KeyboardLayout other) => 
        Chromosome.SequenceEqual(other.Chromosome);
}