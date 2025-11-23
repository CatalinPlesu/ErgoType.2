namespace ErgoType.Core;

using System.Collections.Generic;
using System.Linq;

/// <summary>
/// Represents a keyboard layout with key positions and finger assignments.
/// </summary>
public record Keyboard
{
    /// <summary>
    /// Name of the keyboard layout.
    /// </summary>
    public string Name { get; }
    
    /// <summary>
    /// Dictionary mapping key IDs to Key objects.
    /// </summary>
    public IReadOnlyDictionary<string, Key> Keys { get; }
    
    /// <summary>
    /// All keys in the keyboard.
    /// </summary>
    public IReadOnlyList<Key> AllKeys { get; }
    
    /// <summary>
    /// Creates a new keyboard.
    /// </summary>
    public Keyboard(string name, IReadOnlyDictionary<string, Key> keys)
    {
        Name = name;
        Keys = keys;
        AllKeys = keys.Values.OrderBy(k => k.Row).ThenBy(k => k.Column).ToList();
    }
    
    /// <summary>
    /// Gets a key by its ID.
    /// </summary>
    public Key? GetKey(string keyId) => Keys.TryGetValue(keyId, out var key) ? key : null;
    
    /// <summary>
    /// Calculates the distance between two keys.
    /// </summary>
    public double GetDistance(string fromKeyId, string toKeyId)
    {
        var fromKey = GetKey(fromKeyId);
        var toKey = GetKey(toKeyId);
        
        if (fromKey is null || toKey is null)
            throw new ArgumentException($"Key not found: {fromKeyId} or {toKeyId}");
            
        return fromKey.DistanceTo(toKey);
    }
    
    /// <summary>
    /// Gets all keys assigned to a specific finger.
    /// </summary>
    public IEnumerable<Key> GetKeysForFinger(Finger finger) => 
        AllKeys.Where(k => k.Finger == finger);
    
    /// <summary>
    /// Gets all keys on a specific hand.
    /// </summary>
    public IEnumerable<Key> GetKeysForHand(Hand hand) => 
        AllKeys.Where(k => k.Finger.GetHand() == hand);
    
    /// <summary>
    /// Returns a string representation of the keyboard.
    /// </summary>
    public override string ToString() => 
        $"Keyboard(Name={Name}, Keys={Keys.Count})";
}