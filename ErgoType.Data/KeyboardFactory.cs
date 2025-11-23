namespace ErgoType.Data;

/// <summary>
/// Factory for creating standard keyboard layouts.
/// </summary>
public static class KeyboardFactory
{
    /// <summary>
    /// Creates an ANSI 60% keyboard layout.
    /// </summary>
    public static Keyboard CreateAnsi60Percent()
    {
        var keys = new Dictionary<string, Key>();
        var keySize = 19.0; // 19mm key size
        var spacing = 2.0;  // 2mm spacing
        
        // Row 0 (top row)
        AddRow(keys, 0, 0, "q w e r t y u i o p".Split(), keySize, spacing);
        
        // Row 1 
        AddRow(keys, 1, 0.5, "a s d f g h j k l".Split(), keySize, spacing);
        
        // Row 2
        AddRow(keys, 2, 1.5, "z x c v b n m , . /".Split(), keySize, spacing);
        
        return new Keyboard("ANSI 60%", keys);
    }
    
    /// <summary>
    /// Creates a Dactyl ManuForm keyboard layout.
    /// </summary>
    public static Keyboard CreateDactylManuForm()
    {
        var keys = new Dictionary<string, Key>();
        var keySize = 19.0;
        var spacing = 2.0;
        
        // Left half
        AddStaggeredRow(keys, 0, 0, "q w e r t".Split(), keySize, spacing, -2, Finger.LeftPinky);
        AddStaggeredRow(keys, 1, 0.2, "a s d f g".Split(), keySize, spacing, -1, Finger.LeftRing);
        AddStaggeredRow(keys, 2, 0.3, "z x c v b".Split(), keySize, spacing, 0, Finger.LeftMiddle);
        
        // Right half (mirrored)
        AddStaggeredRow(keys, 0, 6, "y u i o p".Split(), keySize, spacing, 2, Finger.RightRing);
        AddStaggeredRow(keys, 1, 6.2, "h j k l ;".Split(), keySize, spacing, 1, Finger.RightMiddle);
        AddStaggeredRow(keys, 2, 6.3, "n m , . /".Split(), keySize, spacing, 0, Finger.RightIndex);
        
        return new Keyboard("Dactyl ManuForm", keys);
    }
    
    /// <summary>
    /// Creates a Ferris Sweep keyboard layout.
    /// </summary>
    public static Keyboard CreateFerrisSweep()
    {
        var keys = new Dictionary<string, Key>();
        var keySize = 19.0;
        var spacing = 2.0;
        
        // Row 0
        AddStaggeredRow(keys, 0, 0, "q w e r t y u i o p".Split(), keySize, spacing, 0, Finger.LeftPinky);
        
        // Row 1
        AddStaggeredRow(keys, 1, 0.5, "a s d f g h j k l ;".Split(), keySize, spacing, 0, Finger.LeftRing);
        
        // Row 2
        AddStaggeredRow(keys, 2, 1.0, "z x c v b n m , . /".Split(), keySize, spacing, 0, Finger.LeftMiddle);
        
        return new Keyboard("Ferris Sweep", keys);
    }
    
    /// <summary>
    /// Adds a standard row of keys.
    /// </summary>
    private static void AddRow(Dictionary<string, Key> keys, int row, double xOffset, 
                              string[] chars, double keySize, double spacing)
    {
        for (int i = 0; i < chars.Length; i++)
        {
            var charKey = chars[i];
            var x = xOffset + i * (keySize + spacing);
            var y = row * (keySize + spacing);
            
            var finger = GetFingerForPosition(i, row, chars.Length);
            
            keys[charKey] = new Key(charKey, row, i, x, y, finger);
        }
    }
    
    /// <summary>
    /// Adds a staggered row of keys.
    /// </summary>
    private static void AddStaggeredRow(Dictionary<string, Key> keys, int row, double xOffset, 
                                       string[] chars, double keySize, double spacing, 
                                       double staggerOffset, Finger baseFinger)
    {
        for (int i = 0; i < chars.Length; i++)
        {
            var charKey = chars[i];
            var x = xOffset + i * (keySize + spacing) + staggerOffset * (keySize + spacing) * 0.5;
            var y = row * (keySize + spacing);
            
            var finger = GetFingerForStaggeredPosition(i, baseFinger);
            
            keys[charKey] = new Key(charKey, row, i, x, y, finger);
        }
    }
    
    /// <summary>
    /// Gets the finger assignment for a standard position.
    /// </summary>
    private static Finger GetFingerForPosition(int column, int row, int totalColumns)
    {
        // ANSI layout finger assignment
        if (row == 0) // Top row
        {
            return column switch
            {
                0 or 1 => Finger.LeftPinky,
                2 or 3 => Finger.LeftRing,
                4 => Finger.LeftMiddle,
                5 => Finger.LeftIndex,
                6 => Finger.RightIndex,
                7 or 8 => Finger.RightMiddle,
                9 => Finger.RightRing,
                _ => Finger.RightPinky
            };
        }
        else if (row == 1) // Home row
        {
            return column switch
            {
                0 => Finger.LeftPinky,
                1 => Finger.LeftRing,
                2 => Finger.LeftMiddle,
                3 => Finger.LeftIndex,
                4 => Finger.LeftIndex,
                5 => Finger.RightIndex,
                6 => Finger.RightIndex,
                7 => Finger.RightMiddle,
                8 => Finger.RightRing,
                _ => Finger.RightPinky
            };
        }
        else // Bottom row
        {
            return column switch
            {
                0 => Finger.LeftPinky,
                1 => Finger.LeftRing,
                2 => Finger.LeftMiddle,
                3 => Finger.LeftIndex,
                4 => Finger.LeftThumb,
                5 => Finger.RightThumb,
                6 => Finger.RightIndex,
                7 => Finger.RightMiddle,
                8 => Finger.RightRing,
                _ => Finger.RightPinky
            };
        }
    }
    
    /// <summary>
    /// Gets the finger assignment for a staggered layout position.
    /// </summary>
    private static Finger GetFingerForStaggeredPosition(int position, Finger baseFinger)
    {
        var fingers = baseFinger switch
        {
            Finger.LeftPinky => new[] { Finger.LeftPinky, Finger.LeftPinky, Finger.LeftRing, Finger.LeftMiddle, Finger.LeftIndex },
            Finger.LeftRing => new[] { Finger.LeftRing, Finger.LeftRing, Finger.LeftMiddle, Finger.LeftIndex, Finger.LeftIndex },
            Finger.LeftMiddle => new[] { Finger.LeftMiddle, Finger.LeftMiddle, Finger.LeftIndex, Finger.LeftIndex, Finger.LeftThumb },
            Finger.LeftIndex => new[] { Finger.LeftIndex, Finger.LeftIndex, Finger.LeftThumb, Finger.RightThumb, Finger.RightIndex },
            Finger.RightIndex => new[] { Finger.RightIndex, Finger.RightIndex, Finger.RightThumb, Finger.RightThumb, Finger.RightMiddle },
            Finger.RightMiddle => new[] { Finger.RightMiddle, Finger.RightMiddle, Finger.RightIndex, Finger.RightIndex, Finger.RightRing },
            Finger.RightRing => new[] { Finger.RightRing, Finger.RightRing, Finger.RightMiddle, Finger.RightMiddle, Finger.RightPinky },
            Finger.RightPinky => new[] { Finger.RightPinky, Finger.RightPinky, Finger.RightRing, Finger.RightMiddle, Finger.RightIndex },
            _ => Finger.LeftIndex
        };
        
        return position < fingers.Length ? fingers[position] : Finger.LeftIndex;
    }
}