using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using System.Runtime.CompilerServices;

namespace FitnessNet;

public record Point(double X, double Y);
public record KeyPress(Point Position, int Finger);

public struct CharStats
{
    public int Occurrences;
    public int HoverCount;
}

public class Finger
{
    public double X;
    public double Y;
    public int PressCount;
    public int HoverCount;
    public int HoveredChar;

    double _homingX;
    double _homingY;
    int _index;

    public Finger(Point homing, int index)
    {
        X = homing.X;
        Y = homing.Y;
        _homingX = homing.X;
        _homingY = homing.Y;
        _index = index;
        PressCount = 0;
        HoverCount = 0;
        HoveredChar = -1;
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public double TapAndGetDistance(double keyX, double keyY)
    {
        double dx = X - keyX;
        double dy = Y - keyY;
        var result = Math.Sqrt(dx * dx + dy * dy);
        X = keyX;
        Y = keyY;
        return result;
    }

    public void ResetPosition()
    {
        X = _homingX;
        Y = _homingY;
        HoveredChar = -1;
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
    private CharStats[] _charStats;
    private (int CharCode, Point Pos)[] _reprKeys;

    public Fitness(string jsonData)
    {
        using JsonDocument doc = JsonDocument.Parse(jsonData);
        JsonElement root = doc.RootElement;

        _textFilePath = root.GetProperty("text_file_path").GetString();
        _fileContent = File.ReadAllText(_textFilePath);

        JsonElement fittsLaw = root.GetProperty("fitts_law");
        _fittsA = fittsLaw.GetProperty("a").GetDouble();
        _fittsB = fittsLaw.GetProperty("b").GetDouble();

        JsonElement fingerCoeffs = root.GetProperty("finger_coefficients");
        _fingerCoefficients = new double[fingerCoeffs.GetArrayLength()];
        int idx = 0;
        foreach (JsonElement coeff in fingerCoeffs.EnumerateArray())
        {
            _fingerCoefficients[idx++] = coeff.GetDouble();
        }

        JsonElement homingPositions = root.GetProperty("homing_positions");
        _homingPositions = new Point[homingPositions.GetArrayLength()];
        idx = 0;
        foreach (JsonElement pos in homingPositions.EnumerateArray())
        {
            double x = pos.GetProperty("x").GetDouble();
            double y = pos.GetProperty("y").GetDouble();
            _homingPositions[idx++] = new Point(x, y);
        }

        JsonElement charMappings = root.GetProperty("char_mappings");

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

        _charMappings = new KeyPress[_maxCharCode + 1][];

        foreach (JsonProperty charProp in charMappings.EnumerateObject())
        {
            string charStr = charProp.Name;
            if (charStr.Length == 0) continue;

            int charCode = char.ConvertToUtf32(charStr, 0);
            JsonElement keySequence = charProp.Value;

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

        _charStats = new CharStats[_maxCharCode + 1];

        var reprList = new List<(int, Point)>();
        for (int code = 0; code <= _maxCharCode; code++)
        {
            if (_charMappings[code] != null && _charMappings[code].Length > 0)
            {
                reprList.Add((code, _charMappings[code][0].Position));
            }
        }
        _reprKeys = reprList.ToArray();
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

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private double FittsLawInline(double distance)
    {
        return _fittsA + _fittsB * Math.Log2(distance + 1);
    }

    // Fast Compute for GA
    public (double TotalDistance, double TotalTime) Compute()
    {
        Finger[] fingers = InitializeFingers();
        double totalDistance = 0.0;
        double totalTime = 0.0;

        double[] groupDistances = new double[20];
        int[] groupFingers = new int[20];
        int groupSize = 0;
        bool[] usedFingers = new bool[_homingPositions.Length];

        ReadOnlySpan<char> textSpan = _fileContent.AsSpan();

        for (int idx = 0; idx < textSpan.Length; idx++)
        {
            char c = textSpan[idx];
            int charCode = c;

            if (charCode > _maxCharCode || _charMappings[charCode] == null)
                continue;

            KeyPress[] presses = _charMappings[charCode];

            for (int p = 0; p < presses.Length; p++)
            {
                var press = presses[p];
                int fingerIdx = press.Finger;

                if (usedFingers[fingerIdx])
                {
                    double maxTS = 0.0;
                    double sumTPS = 0.0;

                    for (int i = 0; i < groupSize; i++)
                    {
                        double distance = groupDistances[i];
                        totalDistance += distance;
                        double ts = FittsLawInline(distance);
                        if (ts > maxTS) maxTS = ts;
                        sumTPS += _fingerCoefficients[groupFingers[i]];
                    }

                    totalTime += maxTS + sumTPS;
                    groupSize = 0;
                    Array.Clear(usedFingers, 0, usedFingers.Length);
                }

                if (groupSize >= groupDistances.Length)
                {
                    var newDistances = new double[groupDistances.Length * 2];
                    var newFingers = new int[groupFingers.Length * 2];
                    Array.Copy(groupDistances, 0, newDistances, 0, groupSize);
                    Array.Copy(groupFingers, 0, newFingers, 0, groupSize);
                    groupDistances = newDistances;
                    groupFingers = newFingers;
                }

                var dist = fingers[fingerIdx].TapAndGetDistance(press.Position.X, press.Position.Y);
                groupDistances[groupSize] = dist;
                groupFingers[groupSize] = fingerIdx;
                groupSize++;
                usedFingers[fingerIdx] = true;
            }
        }

        if (groupSize > 0)
        {
            double maxTS = 0.0;
            double sumTPS = 0.0;
            for (int i = 0; i < groupSize; i++)
            {
                double distance = groupDistances[i];
                totalDistance += distance;
                double ts = FittsLawInline(distance);
                if (ts > maxTS) maxTS = ts;
                sumTPS += _fingerCoefficients[groupFingers[i]];
            }
            totalTime += maxTS + sumTPS;
        }

        return (totalDistance, totalTime);
    }

    public string ComputeStats()
    {
        Finger[] fingers = InitializeFingers();
        Array.Clear(_charStats, 0, _charStats.Length);

        ReadOnlySpan<char> textSpan = _fileContent.AsSpan();
        int totalPresses = textSpan.Length;

        // Track which character each finger is currently hovering over
        int[] fingerHoverChar = new int[fingers.Length];

        // Initialize - find nearest key for each finger's starting position
        for (int f = 0; f < fingers.Length; f++)
        {
            double bestD = double.MaxValue;
            int bestCode = -1;

            for (int r = 0; r < _reprKeys.Length; r++)
            {
                double dx = fingers[f].X - _reprKeys[r].Pos.X;
                double dy = fingers[f].Y - _reprKeys[r].Pos.Y;
                double d = dx * dx + dy * dy;
                if (d < bestD)
                {
                    bestD = d;
                    bestCode = _reprKeys[r].CharCode;
                }
            }
            fingerHoverChar[f] = bestCode;
        }

        // Process each character
        for (int idx = 0; idx < textSpan.Length; idx++)
        {
            char c = textSpan[idx];
            int charCode = c;

            if (charCode > _maxCharCode || _charMappings[charCode] == null)
                continue;

            // Count occurrence
            _charStats[charCode].Occurrences++;

            // BEFORE pressing: record current hover state for ALL fingers
            for (int f = 0; f < fingers.Length; f++)
            {
                int hoveredChar = fingerHoverChar[f];
                if (hoveredChar >= 0)
                {
                    _charStats[hoveredChar].HoverCount++;
                }
            }

            // NOW press the keys and update finger positions
            KeyPress[] presses = _charMappings[charCode];
            for (int p = 0; p < presses.Length; p++)
            {
                var press = presses[p];
                int fingerIdx = press.Finger;

                // Move finger
                fingers[fingerIdx].TapAndGetDistance(press.Position.X, press.Position.Y);

                // Update hover tracking - this finger now hovers over the key it just pressed
                fingerHoverChar[fingerIdx] = charCode;
            }
        }

        // Build JSON output (keep this part as is)
        var output = new Dictionary<string, object>();
        output["total_presses"] = totalPresses;
        output["total_chars_processed"] = textSpan.Length;

        var charMap = new Dictionary<string, object>();
        for (int code = 0; code <= _maxCharCode; code++)
        {
            if (_charMappings[code] != null && _charMappings[code].Length > 0)
            {
                string charKey = char.ConvertFromUtf32(code);
                var charData = new Dictionary<string, object>();

                var keyPressesArray = new List<Dictionary<string, object>>();
                foreach (var kp in _charMappings[code])
                {
                    keyPressesArray.Add(new Dictionary<string, object>
                    {
                        ["x"] = kp.Position.X,
                        ["y"] = kp.Position.Y,
                        ["finger"] = kp.Finger
                    });
                }
                charData["key_presses"] = keyPressesArray;
                charData["occurrences"] = _charStats[code].Occurrences;
                charData["hover_count"] = _charStats[code].HoverCount;
                charData["press_count"] = _charStats[code].Occurrences * _charMappings[code].Length;

                charMap[charKey] = charData;
            }
        }
        output["char_mappings"] = charMap;

        // NO finger stats - we don't care about them
        return JsonSerializer.Serialize(output, new JsonSerializerOptions { WriteIndented = true });
    }
}
