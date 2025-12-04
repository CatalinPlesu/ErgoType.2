using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;

namespace FitnessNet;

public record Point(double X, double Y);

public record KeyPress(Point Position, int Finger);

public class Finger
{
    Point _currentPosition;
    Point _homingPosition;
    int _index;

    public Finger(Point homing, int index)
    {
        _currentPosition = homing;
        _homingPosition = homing;
        _index = index;
    }

    public double TapAndGetDistance(Point key)
    {
        var result = Math.Sqrt(Math.Pow(_currentPosition.X - key.X, 2) + Math.Pow(_currentPosition.Y - key.Y, 2));
        _currentPosition = key;
        return result;
    }

    public void ResetPosition()
    {
        _currentPosition = _homingPosition;
    }
}

public class Fitness
{
    private string _textFilePath;
    private string _fileContent;
    private double _fittsA;
    private double _fittsB;
    private double[] _fingerCoefficients;
    private Point[] _homingPositions;
    private KeyPress[][] _charMappings;
    private int _maxCharCode;

    public Fitness(string jsonData)
    {
        using JsonDocument doc = JsonDocument.Parse(jsonData);
        JsonElement root = doc.RootElement;

        // Parse text file path
        _textFilePath = root.GetProperty("text_file_path").GetString();

        _fileContent = File.ReadAllText(_textFilePath);

        // Parse Fitts's Law parameters
        JsonElement fittsLaw = root.GetProperty("fitts_law");
        _fittsA = fittsLaw.GetProperty("a").GetDouble();
        _fittsB = fittsLaw.GetProperty("b").GetDouble();

        // Parse finger coefficients
        JsonElement fingerCoeffs = root.GetProperty("finger_coefficients");
        _fingerCoefficients = new double[fingerCoeffs.GetArrayLength()];
        int idx = 0;
        foreach (JsonElement coeff in fingerCoeffs.EnumerateArray())
        {
            _fingerCoefficients[idx++] = coeff.GetDouble();
        }

        // Parse homing positions
        JsonElement homingPositions = root.GetProperty("homing_positions");
        _homingPositions = new Point[homingPositions.GetArrayLength()];
        idx = 0;
        foreach (JsonElement pos in homingPositions.EnumerateArray())
        {
            double x = pos.GetProperty("x").GetDouble();
            double y = pos.GetProperty("y").GetDouble();
            _homingPositions[idx++] = new Point(x, y);
        }

        // Parse character mappings
        JsonElement charMappings = root.GetProperty("char_mappings");

        // First pass: find max char code
        _maxCharCode = 0;
        foreach (JsonProperty charProp in charMappings.EnumerateObject())
        {
            string charStr = charProp.Name;
            if (charStr.Length > 0)
            {
                int charCode = char.ConvertToUtf32(charStr, 0);
                if (charCode > _maxCharCode)
                {
                    _maxCharCode = charCode;
                }
            }
        }

        // Initialize array with max char code + 1
        _charMappings = new KeyPress[_maxCharCode + 1][];

        // Second pass: populate the array
        foreach (JsonProperty charProp in charMappings.EnumerateObject())
        {
            string charStr = charProp.Name;
            if (charStr.Length == 0) continue;

            int charCode = char.ConvertToUtf32(charStr, 0);
            JsonElement keySequence = charProp.Value;

            // Parse the list of key presses for this character
            int sequenceLength = keySequence.GetArrayLength();
            KeyPress[] keyPresses = new KeyPress[sequenceLength];

            int i = 0;
            foreach (JsonElement keyPress in keySequence.EnumerateArray())
            {
                double x = keyPress.GetProperty("x").GetDouble();
                double y = keyPress.GetProperty("y").GetDouble();
                int finger = keyPress.GetProperty("finger").GetInt32();

                keyPresses[i++] = new KeyPress(new Point(x, y), finger);
            }

            _charMappings[charCode] = keyPresses;
        }
    }

    public Finger[] InitializeFingers()
    {
        Finger[] fingers = new Finger[_homingPositions.Length];
        for (int i = 0; i < _homingPositions.Length; i++)
        {
            fingers[i] = new Finger(_homingPositions[i], i);
        }
        return fingers;
    }

    public KeyPress[] GetKeyPressesForChar(char c)
    {
        int charCode = c;
        if (charCode <= _maxCharCode && _charMappings[charCode] != null)
        {
            return _charMappings[charCode];
        }
        return Array.Empty<KeyPress>();
    }

    public (double TotalDistance, double TotalTime) FitnessComponents()
    {
        var distanceByFinger = GetDistancesByFinger(_fileContent, _charMappings);
        var totalDistance = distanceByFinger.SelectMany(d => d).Select(d => d.Distance).Sum();
        var totalTime = GetTotalTime(distanceByFinger, _fingerCoefficients);
        return (totalDistance, totalTime);
    }

    public double GetTotalTime(List<List<(double Distance, int Finger)>> distances, double[] TPS)
    {
        return distances.Select(d => GetGroupPressTime(d, TPS)).Sum();
    }

    public double GetGroupPressTime(List<(double Distance, int Finger)> distances, double[] tps)
    {
        var TS = distances.Select(d => FittsLaw(d.Distance));
        var sumTPS = distances.Select(d => tps[(int)d.Finger]).Sum();
        return TS.Max() + sumTPS;
    }

    public double FittsLaw(double Distance)
    {
        var fittsTime = _fittsA + _fittsB * Math.Log2(Distance / 1 + 1);
        return fittsTime;
    }

    public List<List<(double Distance, int Finger)>> GetDistancesByFinger(string fullText, KeyPress[][] charPositionMapper)
    {
        Finger[] fingers = InitializeFingers();

        List<List<(double Distance, int Finger)>> result = new();
        List<(double Distance, int Finger)> currentGroup = new();

        foreach (char c in fullText)
        {
            KeyPress[] presses = GetKeyPressesForChar(c);
            foreach (var press in presses)
            {
                var distance = fingers[press.Finger].TapAndGetDistance(press.Position);
                if (currentGroup.Any(g => g.Finger == press.Finger))
                {
                    // If finger was already used commit current group and create new one.
                    result.Add(currentGroup);
                    currentGroup = new();
                }
                currentGroup.Add((distance, press.Finger));
            }
        }
        if (currentGroup.Any())
        {
            result.Add(currentGroup);
        }

        return result;
    }

    public string SayHay()
    {
        return "Hi";
    }
}
