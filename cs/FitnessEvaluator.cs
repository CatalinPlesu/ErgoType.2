using System;
using System.Collections.Generic;
using System.Linq;

namespace KeyboardLayoutOptimizer
{
    /// <summary>
    /// Configuration for fitness evaluation
    /// </summary>
    public class FitnessConfig
    {
        public double DistanceWeight { get; set; } = 0.7;
        public double TimeWeight { get; set; } = 0.3;
        public bool UseSimplifiedFitness { get; set; } = false;
        public bool EnableCaching { get; set; } = true;
    }

    /// <summary>
    /// Base class for fitness evaluation strategies
    /// </summary>
    public abstract class FitnessEvaluatorBase
    {
        protected FitnessConfig Config;

        protected FitnessEvaluatorBase(FitnessConfig config)
        {
            Config = config;
        }

        public abstract double Evaluate(char[] layout);
        public abstract (double distance, double time) CalculateComponents(char[] layout);
    }

    /// <summary>
    /// Fitness evaluator using frequency data and keyboard geometry
    /// </summary>
    public class FrequencyBasedEvaluator : FitnessEvaluatorBase
    {
        private Dictionary<char, double> _letterFrequencies;
        private Dictionary<string, double> _bigramFrequencies;
        private Dictionary<char, (double x, double y, Finger finger, Hand hand)> _keyPositions;

        public FrequencyBasedEvaluator(FitnessConfig config) : base(config)
        {
            LoadDefaultFrequencies();
            InitializeKeyPositions();
        }

        private void LoadDefaultFrequencies()
        {
            // English letter frequencies (simplified)
            _letterFrequencies = new Dictionary<char, double>
            {
                ['e'] = 0.127, ['t'] = 0.091, ['a'] = 0.082, ['o'] = 0.075, ['i'] = 0.070,
                ['n'] = 0.067, ['s'] = 0.063, ['h'] = 0.061, ['r'] = 0.060, ['d'] = 0.043,
                ['l'] = 0.040, ['c'] = 0.028, ['u'] = 0.028, ['m'] = 0.024, ['w'] = 0.024,
                ['f'] = 0.022, ['g'] = 0.020, ['y'] = 0.020, ['p'] = 0.019, ['b'] = 0.015,
                ['v'] = 0.0098, ['k'] = 0.0077, ['j'] = 0.0015, ['x'] = 0.0015, ['q'] = 0.00095, ['z'] = 0.00074
            };

            // Common English bigrams (simplified)
            _bigramFrequencies = new Dictionary<string, double>
            {
                ["th"] = 0.035, ["er"] = 0.025, ["on"] = 0.020, ["an"] = 0.018, ["re"] = 0.017,
                ["he"] = 0.016, ["in"] = 0.015, ["ed"] = 0.014, ["es"] = 0.013, ["ng"] = 0.012,
                ["at"] = 0.011, ["ti"] = 0.010, ["st"] = 0.010, ["en"] = 0.009, ["nd"] = 0.009
            };
        }

        private void InitializeKeyPositions()
        {
            // QWERTY keyboard positions (simplified grid layout)
            var qwertyLayout = new Dictionary<char, (double x, double y, Finger finger, Hand hand)>
            {
                // Top row
                ['q'] = (-3, 0, Finger.Index, Hand.Left), ['w'] = (-2, 0, Finger.Middle, Hand.Left),
                ['e'] = (-1, 0, Finger.Ring, Hand.Left), ['r'] = (0, 0, Finger.Pinky, Hand.Left),
                ['t'] = (1, 0, Finger.Pinky, Hand.Left), ['y'] = (2, 0, Finger.Pinky, Hand.Right),
                ['u'] = (3, 0, Finger.Ring, Hand.Right), ['i'] = (4, 0, Finger.Middle, Hand.Right),
                ['o'] = (5, 0, Finger.Index, Hand.Right), ['p'] = (6, 0, Finger.Thumb, Hand.Right),
                
                // Home row
                ['a'] = (-2.5, 1, Finger.Pinky, Hand.Left), ['s'] = (-1.5, 1, Finger.Ring, Hand.Left),
                ['d'] = (-0.5, 1, Finger.Middle, Hand.Left), ['f'] = (0.5, 1, Finger.Index, Hand.Left),
                ['g'] = (1.5, 1, Finger.Index, Hand.Right), ['h'] = (2.5, 1, Finger.Middle, Hand.Right),
                ['j'] = (3.5, 1, Finger.Ring, Hand.Right), ['k'] = (4.5, Finger.Pinky, Hand.Right),
                ['l'] = (5.5, 1, Finger.Pinky, Hand.Right),
                
                // Bottom row
                ['z'] = (-2, 2, Finger.Ring, Hand.Left), ['x'] = (-1, 2, Finger.Middle, Hand.Left),
                ['c'] = (0, 2, Finger.Index, Hand.Left), ['v'] = (1, 2, Finger.Index, Hand.Right),
                ['b'] = (2, 2, Finger.Ring, Hand.Right), ['n'] = (3, 2, Finger.Pinky, Hand.Right),
                ['m'] = (4, 2, Finger.Pinky, Hand.Right)
            };

            _keyPositions = qwertyLayout;
        }

        public override double Evaluate(char[] layout)
        {
            var (distance, time) = CalculateComponents(layout);
            return Config.DistanceWeight * distance + Config.TimeWeight * time;
        }

        public override (double distance, double time) CalculateComponents(char[] layout)
        {
            double totalDistance = 0;
            double totalTime = 0;
            int totalChars = 0;

            // Calculate unigram frequency scores
            foreach (var kvp in _letterFrequencies)
            {
                var character = kvp.Key;
                var frequency = kvp.Value;
                
                if (_keyPositions.TryGetValue(character, out var position))
                {
                    var distance = CalculateKeyDistance(character, position.finger, position.hand);
                    totalDistance += distance * frequency;
                    totalTime += CalculateTypingTime(distance, position.finger) * frequency;
                    totalChars += (int)(frequency * 1000); // Scale up for calculation
                }
            }

            // Calculate bigram transition scores
            foreach (var kvp in _bigramFrequencies)
            {
                var bigram = kvp.Key;
                var frequency = kvp.Value;
                
                if (bigram.Length == 2 && 
                    _keyPositions.TryGetValue(bigram[0], out var pos1) &&
                    _keyPositions.TryGetValue(bigram[1], out var pos2))
                {
                    var distance = CalculateTransitionDistance(pos1, pos2);
                    totalDistance += distance * frequency;
                    totalTime += CalculateTransitionTime(distance, pos1.finger, pos2.finger) * frequency;
                }
            }

            return (totalDistance / Math.Max(totalChars, 1), totalTime / Math.Max(totalChars, 1));
        }

        private double CalculateKeyDistance(char character, Finger finger, Hand hand)
        {
            // Calculate distance from home position to key
            if (_keyPositions.TryGetValue(character, out var position))
            {
                var homePosition = GetHomePosition(finger, hand);
                var (x, y) = position;
                
                return Math.Sqrt(Math.Pow(x - homePosition.x, 2) + Math.Pow(y - homePosition.y, 2));
            }
            return 1.0; // Default distance if key not found
        }

        private double CalculateTransitionDistance((double x, double y, Finger finger, Hand hand) fromPos, 
                                                  (double x, double y, Finger finger, Hand hand) toPos)
        {
            return Math.Sqrt(Math.Pow(toPos.x - fromPos.x, 2) + Math.Pow(toPos.y - fromPos.y, 2));
        }

        private (double x, double y) GetHomePosition(Finger finger, Hand hand)
        {
            // Return home position for each finger
            return (hand, finger) switch
            {
                (Hand.Left, Finger.Pinky) => (-3, 1),
                (Hand.Left, Finger.Ring) => (-2, 1),
                (Hand.Left, Finger.Middle) => (-1, 1),
                (Hand.Left, Finger.Index) => (0, 1),
                (Hand.Left, Finger.Thumb) => (0, 2),
                (Hand.Right, Finger.Thumb) => (1, 2),
                (Hand.Right, Finger.Index) => (1, 1),
                (Hand.Right, Finger.Middle) => (2, 1),
                (Hand.Right, Finger.Ring) => (3, 1),
                (Hand.Right, Finger.Pinky) => (4, 1),
                _ => (0, 0)
            };
        }

        private double CalculateTypingTime(double distance, Finger finger)
        {
            // Simple time calculation based on distance and finger speed
            var baseTime = 0.1; // Base typing time
            var distancePenalty = distance * 0.05;
            var fingerPenalty = finger switch
            {
                Finger.Pinky => 0.03,
                Finger.Ring => 0.02,
                Finger.Middle => 0.01,
                Finger.Index => 0.0,
                Finger.Thumb => 0.02,
                _ => 0.01
            };
            
            return baseTime + distancePenalty + fingerPenalty;
        }

        private double CalculateTransitionTime(double distance, Finger fromFinger, Finger toFinger)
        {
            var baseTime = 0.05;
            var distancePenalty = distance * 0.03;
            var sameHandPenalty = (fromFinger <= Finger.Thumb) == (toFinger <= Finger.Thumb) ? 0.02 : 0.0;
            
            return baseTime + distancePenalty + sameHandPenalty;
        }
    }

    /// <summary>
    /// Simple text-based fitness evaluator
    /// </summary>
    public class TextBasedEvaluator : FitnessEvaluatorBase
    {
        private readonly string _sampleText;
        private Dictionary<char, (double x, double y, Finger finger, Hand hand)> _keyPositions;

        public TextBasedEvaluator(string sampleText, FitnessConfig config) : base(config)
        {
            _sampleText = sampleText.ToLower();
            InitializeKeyPositions();
        }

        private void InitializeKeyPositions()
        {
            // QWERTY keyboard positions
            var qwertyLayout = new Dictionary<char, (double x, double y, Finger finger, Hand hand)>
            {
                ['q'] = (-3, 0, Finger.Index, Hand.Left), ['w'] = (-2, 0, Finger.Middle, Hand.Left),
                ['e'] = (-1, 0, Finger.Ring, Hand.Left), ['r'] = (0, 0, Finger.Pinky, Hand.Left),
                ['t'] = (1, 0, Finger.Pinky, Hand.Left), ['y'] = (2, 0, Finger.Pinky, Hand.Right),
                ['u'] = (3, 0, Finger.Ring, Hand.Right), ['i'] = (4, 0, Finger.Middle, Hand.Right),
                ['o'] = (5, 0, Finger.Index, Hand.Right), ['p'] = (6, 0, Finger.Thumb, Hand.Right),
                ['a'] = (-2.5, 1, Finger.Pinky, Hand.Left), ['s'] = (-1.5, 1, Finger.Ring, Hand.Left),
                ['d'] = (-0.5, 1, Finger.Middle, Hand.Left), ['f'] = (0.5, 1, Finger.Index, Hand.Left),
                ['g'] = (1.5, 1, Finger.Index, Hand.Right), ['h'] = (2.5, 1, Finger.Middle, Hand.Right),
                ['j'] = (3.5, 1, Finger.Ring, Hand.Right), ['k'] = (4.5, Finger.Pinky, Hand.Right),
                ['l'] = (5.5, 1, Finger.Pinky, Hand.Right), ['z'] = (-2, 2, Finger.Ring, Hand.Left),
                ['x'] = (-1, 2, Finger.Middle, Hand.Left), ['c'] = (0, 2, Finger.Index, Hand.Left),
                ['v'] = (1, 2, Finger.Index, Hand.Right), ['b'] = (2, 2, Finger.Ring, Hand.Right),
                ['n'] = (3, 2, Finger.Pinky, Hand.Right), ['m'] = (4, 2, Finger.Pinky, Hand.Right)
            };

            _keyPositions = qwertyLayout;
        }

        public override double Evaluate(char[] layout)
        {
            var (distance, time) = CalculateComponents(layout);
            return Config.DistanceWeight * distance + Config.TimeWeight * time;
        }

        public override (double distance, double time) CalculateComponents(char[] layout)
        {
            double totalDistance = 0;
            double totalTime = 0;
            int totalChars = 0;
            char? prevChar = null;

            foreach (var ch in _sampleText)
            {
                if (char.IsLetter(ch) && _keyPositions.TryGetValue(ch, out var position))
                {
                    var distance = CalculateKeyDistance(ch, position.finger, position.hand);
                    totalDistance += distance;
                    totalTime += CalculateTypingTime(distance, position.finger);
                    totalChars++;

                    if (prevChar.HasValue && _keyPositions.TryGetValue(prevChar.Value, out var prevPos))
                    {
                        var transitionDistance = CalculateTransitionDistance(prevPos, position);
                        totalDistance += transitionDistance;
                        totalTime += CalculateTransitionTime(transitionDistance, prevPos.finger, position.finger);
                    }

                    prevChar = ch;
                }
            }

            return (totalDistance / Math.Max(totalChars, 1), totalTime / Math.Max(totalChars, 1));
        }

        private double CalculateKeyDistance(char character, Finger finger, Hand hand)
        {
            if (_keyPositions.TryGetValue(character, out var position))
            {
                var homePosition = GetHomePosition(finger, hand);
                var (x, y) = position;
                
                return Math.Sqrt(Math.Pow(x - homePosition.x, 2) + Math.Pow(y - homePosition.y, 2));
            }
            return 1.0;
        }

        private double CalculateTransitionDistance((double x, double y, Finger finger, Hand hand) fromPos, 
                                                  (double x, double y, Finger finger, Hand hand) toPos)
        {
            return Math.Sqrt(Math.Pow(toPos.x - fromPos.x, 2) + Math.Pow(toPos.y - fromPos.y, 2));
        }

        private (double x, double y) GetHomePosition(Finger finger, Hand hand)
        {
            return (hand, finger) switch
            {
                (Hand.Left, Finger.Pinky) => (-3, 1),
                (Hand.Left, Finger.Ring) => (-2, 1),
                (Hand.Left, Finger.Middle) => (-1, 1),
                (Hand.Left, Finger.Index) => (0, 1),
                (Hand.Left, Finger.Thumb) => (0, 2),
                (Hand.Right, Finger.Thumb) => (1, 2),
                (Hand.Right, Finger.Index) => (1, 1),
                (Hand.Right, Finger.Middle) => (2, 1),
                (Hand.Right, Finger.Ring) => (3, 1),
                (Hand.Right, Finger.Pinky) => (4, 1),
                _ => (0, 0)
            };
        }

        private double CalculateTypingTime(double distance, Finger finger)
        {
            var baseTime = 0.1;
            var distancePenalty = distance * 0.05;
            var fingerPenalty = finger switch
            {
                Finger.Pinky => 0.03,
                Finger.Ring => 0.02,
                Finger.Middle => 0.01,
                Finger.Index => 0.0,
                Finger.Thumb => 0.02,
                _ => 0.01
            };
            
            return baseTime + distancePenalty + fingerPenalty;
        }

        private double CalculateTransitionTime(double distance, Finger fromFinger, Finger toFinger)
        {
            var baseTime = 0.05;
            var distancePenalty = distance * 0.03;
            var sameHandPenalty = (fromFinger <= Finger.Thumb) == (toFinger <= Finger.Thumb) ? 0.02 : 0.0;
            
            return baseTime + distancePenalty + sameHandPenalty;
        }
    }

    /// <summary>
    /// Main fitness evaluator that can switch between different strategies
    /// </summary>
    public class FitnessEvaluator
    {
        private readonly Dictionary<string, double> _cache = new Dictionary<string, double>();
        private readonly FitnessEvaluatorBase _evaluator;

        public FitnessEvaluator(FitnessEvaluatorBase evaluator)
        {
            _evaluator = evaluator;
        }

        public double Evaluate(char[] layout)
        {
            var layoutKey = GetLayoutKey(layout);
            
            if (_evaluator.Config.EnableCaching && _cache.TryGetValue(layoutKey, out var cached))
            {
                return cached;
            }

            var fitness = _evaluator.Evaluate(layout);
            
            if (_evaluator.Config.EnableCaching)
            {
                _cache[layoutKey] = fitness;
            }

            return fitness;
        }

        public (double distance, double time) CalculateComponents(char[] layout)
        {
            return _evaluator.CalculateComponents(layout);
        }

        private string GetLayoutKey(char[] layout)
        {
            return new string(layout);
        }
    }
}