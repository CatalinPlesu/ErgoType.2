namespace ErgoType.Core;

using System;

/// <summary>
/// Represents a key on a keyboard with its position and properties.
/// </summary>
public record Key
{
    /// <summary>
    /// Unique identifier for the key.
    /// </summary>
    public string Id { get; }
    
    /// <summary>
    /// Row position (0-based from top).
    /// </summary>
    public int Row { get; }
    
    /// <summary>
    /// Column position (0-based from left).
    /// </summary>
    public int Column { get; }
    
    /// <summary>
    /// X coordinate in physical space.
    /// </summary>
    public double X { get; }
    
    /// <summary>
    /// Y coordinate in physical space.
    /// </summary>
    public double Y { get; }
    
    /// <summary>
    /// Finger assigned to this key.
    /// </summary>
    public Finger Finger { get; }
    
    /// <summary>
    /// Creates a new key.
    /// </summary>
    public Key(string id, int row, int column, double x, double y, Finger finger)
    {
        Id = id;
        Row = row;
        Column = column;
        X = x;
        Y = y;
        Finger = finger;
    }
    
    /// <summary>
    /// Calculates the Euclidean distance to another key.
    /// </summary>
    public double DistanceTo(Key other) => 
        Math.Sqrt(Math.Pow(X - other.X, 2) + Math.Pow(Y - other.Y, 2));
    
    /// <summary>
    /// Returns a string representation of the key.
    /// </summary>
    public override string ToString() => 
        $"Key({Id}, Row={Row}, Col={Column}, Finger={Finger})";
}