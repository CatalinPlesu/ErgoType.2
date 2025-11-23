using System;
using System.Collections.Generic;
using System.Linq;

namespace KeyboardLayoutOptimizer
{
    /// <summary>
    /// Enumeration of finger types
    /// </summary>
    public enum Finger
    {
        Unknown = 0,
        Thumb = 1,
        Index = 2,
        Middle = 3,
        Ring = 4,
        Pinky = 5
    }

    /// <summary>
    /// Enumeration of hand types
    /// </summary>
    public enum Hand
    {
        Unknown = 0,
        Left = 1,
        Right = 2,
        Both = 3
    }

    /// <summary>
    /// Individual key on a keyboard
    /// </summary>
    public class Key
    {
        public string Color { get; set; } = "#cccccc";
        public string[] Labels { get; set; } = new string[12];
        public string[] TextColors { get; set; } = new string[12];
        public double[] TextSizes { get; set; } = new double[12];
        
        public Dictionary<string, object> Default { get; set; } = new Dictionary<string, object>
        {
            ["textColor"] = "#000000",
            ["textSize"] = 3.0
        };

        public Finger Finger { get; set; } = Finger.Unknown;
        public Hand Hand { get; set; } = Hand.Unknown;
        public bool Homing { get; set; } = false;
        
        // Position and dimensions
        public double X { get; set; } = 0;
        public double Y { get; set; } = 0;
        public double Z { get; set; } = 0;
        public double Width { get; set; } = 1;
        public double Height { get; set; } = 1;
        public double X2 { get; set; } = 0;
        public double Y2 { get; set; } = 0;
        public double Width2 { get; set; } = 1;
        public double Height2 { get; set; } = 1;
        
        // Rotation
        public double RotationX { get; set; } = 0;
        public double RotationY { get; set; } = 0;
        public double RotationAngle { get; set; } = 0;
        
        // Additional properties
        public bool Decal { get; set; } = false;
        public bool Ghost { get; set; } = false;
        public bool Stepped { get; set; } = false;
        public bool Nub { get; set; } = false;
        public string Profile { get; set; } = "";
        public string SwitchMount { get; set; } = "";
        public string SwitchBrand { get; set; } = "";
        public string SwitchType { get; set; } = "";

        public (Finger, Hand) GetFingerHand()
        {
            return (Finger, Hand);
        }

        public (double, double, double) GetCenterPosition()
        {
            return (X + Width / 2, Y + Height / 2, Z);
        }

        public override string ToString()
        {
            return $"Key(label={Labels[0]}, x={X}, y={Y}, z={Z}, finger={Finger}, hand={Hand}, homing={Homing})";
        }
    }

    /// <summary>
    /// Metadata for a keyboard layout
    /// </summary>
    public class KeyboardMetadata
    {
        public string Author { get; set; } = "";
        public string Backcolor { get; set; } = "#eeeeee";
        public Dictionary<string, string> Background { get; set; }
        public string Name { get; set; } = "";
        public string Notes { get; set; } = "";
        public string Radii { get; set; } = "";
        public string SwitchBrand { get; set; } = "";
        public string SwitchMount { get; set; } = "";
        public string SwitchType { get; set; } = "";
    }

    /// <summary>
    /// Complete keyboard layout representation
    /// </summary>
    public class Keyboard
    {
        public KeyboardMetadata Meta { get; set; } = new KeyboardMetadata();
        public List<Key> Keys { get; set; } = new List<Key>();

        /// <summary>
        /// Load keyboard layout from JSON file
        /// </summary>
        public static Keyboard LoadFromFile(string filePath)
        {
            // For demo purposes, create a simple keyboard layout
            return CreateDemoKeyboard();
        }

        /// <summary>
        /// Create a demo keyboard layout
        /// </summary>
        private static Keyboard CreateDemoKeyboard()
        {
            var keyboard = new Keyboard();
            keyboard.Meta.Name = "Demo Keyboard";
            
            // Create a simple QWERTY-like layout
            var layout = new[]
            {
                new { Row = 0, Keys = "qwertyuiop" },
                new { Row = 1, Keys = "asdfghjkl" },
                new { Row = 2, Keys = "zxcvbnm" }
            };

            var fingerMap = new Dictionary<char, (Finger finger, Hand hand)>
            {
                // Top row
                ['q'] = (Finger.Pinky, Hand.Left), ['w'] = (Finger.Ring, Hand.Left),
                ['e'] = (Finger.Middle, Hand.Left), ['r'] = (Finger.Index, Hand.Left),
                ['t'] = (Finger.Index, Hand.Left), ['y'] = (Finger.Index, Hand.Right),
                ['u'] = (Finger.Middle, Hand.Right), ['i'] = (Finger.Ring, Hand.Right),
                ['o'] = (Finger.Pinky, Hand.Right), ['p'] = (Finger.Pinky, Hand.Right),
                
                // Home row
                ['a'] = (Finger.Pinky, Hand.Left), ['s'] = (Finger.Ring, Hand.Left),
                ['d'] = (Finger.Middle, Hand.Left), ['f'] = (Finger.Index, Hand.Left),
                ['g'] = (Finger.Index, Hand.Left), ['h'] = (Finger.Index, Hand.Right),
                ['j'] = (Finger.Index, Hand.Right), ['k'] = (Finger.Middle, Hand.Right),
                ['l'] = (Finger.Ring, Hand.Right),
                
                // Bottom row
                ['z'] = (Finger.Ring, Hand.Left), ['x'] = (Finger.Middle, Hand.Left),
                ['c'] = (Finger.Index, Hand.Left), ['v'] = (Finger.Index, Hand.Left),
                ['b'] = (Finger.Index, Hand.Right), ['n'] = (Finger.Middle, Hand.Right),
                ['m'] = (Finger.Ring, Hand.Right)
            };

            for (int row = 0; row < layout.Length; row++)
            {
                var rowLayout = layout[row];
                for (int col = 0; col < rowLayout.Keys.Length; col++)
                {
                    var keyChar = rowLayout.Keys[col];
                    var key = new Key
                    {
                        X = col,
                        Y = row,
                        Z = 0,
                        Labels = new string[12],
                        Finger = fingerMap.ContainsKey(keyChar) ? fingerMap[keyChar].finger : Finger.Unknown,
                        Hand = fingerMap.ContainsKey(keyChar) ? fingerMap[keyChar].hand : Hand.Unknown
                    };
                    key.Labels[0] = keyChar.ToString();
                    keyboard.Keys.Add(key);
                }
            }

            return keyboard;
        }
    }
}