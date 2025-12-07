using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using System.Runtime.CompilerServices;

namespace FitnessNet;

public record Point(double X, double Y);
public record KeyPress(Point Position, int Finger);

// Lightweight stats struct - only what's needed
public struct CharStats
{
    public int Occurrences;   // how many times char appears in text
    public int HoverCount;    // how many times any finger hovered over this char
}

// Enhanced Finger class with counters
public class Finger
{
    public double X;
    public double Y;
    public int PressCount;    // how many times this finger pressed
    public int HoverCount;    // how many times this finger hovered (samples)
    public int HoveredChar;   // last sampled nearest character code (or -1)

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

    // New fields for stats tracking
    private CharStats[] _charStats;
    private (int CharCode, Point Pos)[] _reprKeys;  // representative key positions for hover mapping

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

        // Initialize stats structures
        _charStats = new CharStats[_maxCharCode + 1];
        
        // Build representative key positions (first mapping position per char)
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

    public KeyPress[] GetKeyPressesForChar(char c)
    {
        int charCode = c;
        if (charCode <= _maxCharCode && _charMappings[charCode] != null)
        {
            return _charMappings[charCode];
        }
        return Array.Empty<KeyPress>();
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private double FittsLawInline(double distance)
    {
        return _fittsA + _fittsB * Math.Log2(distance + 1);
    }

    // ORIGINAL COMPUTE - UNCHANGED (fast path for GA evolution)
    public (double TotalDistance, double TotalTime) Compute()
    {
        Finger[] fingers = InitializeFingers();

        double totalDistance = 0.0;
        double totalTime = 0.0;

        // Current group tracking
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
                    // Process current group
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

                    // Reset group
                    groupSize = 0;
                    Array.Clear(usedFingers, 0, usedFingers.Length);
                }

                // Expand group buffer if needed
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

        // Process final group
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

    // NEW METHOD - ComputeStats (detailed reporting for final generation)
    // hoverSampleInterval: sample hover every N characters (default 100)
public string ComputeStats(int hoverSampleInterval = 100)
{
    Finger[] fingers = InitializeFingers();
    
    // Reset stats
    Array.Clear(_charStats, 0, _charStats.Length);

    ReadOnlySpan<char> textSpan = _fileContent.AsSpan();
    int totalPresses = textSpan.Length;

    int sampleCount = 0;
    
    for (int idx = 0; idx < textSpan.Length; idx++)
    {
        char c = textSpan[idx];
        int charCode = c;

        if (charCode > _maxCharCode || _charMappings[charCode] == null)
            continue;

        // Increment occurrence
        _charStats[charCode].Occurrences++;

        KeyPress[] presses = _charMappings[charCode];

        // Sample hover state BEFORE processing the presses
        if (sampleCount % hoverSampleInterval == 0)
        {
            // For each finger, find which character key it's hovering over
            for (int f = 0; f < fingers.Length; f++)
            {
                double bestD = double.MaxValue;
                int bestCode = -1;
                double fx = fingers[f].X;
                double fy = fingers[f].Y;

                // Find nearest representative key where this finger is hovering
                for (int r = 0; r < _reprKeys.Length; r++)
                {
                    double dx = fx - _reprKeys[r].Pos.X;
                    double dy = fy - _reprKeys[r].Pos.Y;
                    double d = dx * dx + dy * dy;
                    if (d < bestD)
                    {
                        bestD = d;
                        bestCode = _reprKeys[r].CharCode;
                    }
                }

                // FIXED: Only track char hover counts, not finger hover counts
                // Finger hover count is just: total_samples / fingers.Length
                if (bestCode >= 0)
                {
                    fingers[f].HoveredChar = bestCode;
                    _charStats[bestCode].HoverCount++;    // This char was hovered over
                }
            }
        }
        
        sampleCount++;

        // Process presses - move fingers and count
        for (int p = 0; p < presses.Length; p++)
        {
            var press = presses[p];
            int fingerIdx = press.Finger;

            fingers[fingerIdx].PressCount++;
            fingers[fingerIdx].TapAndGetDistance(press.Position.X, press.Position.Y);
        }
    }

    // Calculate total samples taken
    int totalSamples = (textSpan.Length + hoverSampleInterval - 1) / hoverSampleInterval;

    // Build JSON output
    var output = new Dictionary<string, object>();
    
    // Total presses (string length)
    output["total_presses"] = totalPresses;
    output["total_hover_samples"] = totalSamples;

    // Char mappings with stats
    var charMap = new Dictionary<string, object>();
    for (int code = 0; code <= _maxCharCode; code++)
    {
        if (_charMappings[code] != null && _charMappings[code].Length > 0)
        {
            string charKey = char.ConvertFromUtf32(code);
            var charData = new Dictionary<string, object>();
            
            // Original key presses array
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
            
            // Stats
            charData["occurrences"] = _charStats[code].Occurrences;
            charData["hover_count"] = _charStats[code].HoverCount;
            
            // Reconstructed press count (occurrences * number of key presses per char)
            charData["press_count"] = _charStats[code].Occurrences * _charMappings[code].Length;
            
            charMap[charKey] = charData;
        }
    }
    output["char_mappings"] = charMap;

    // Finger stats - simplified without misleading hover counts
    var fingerStats = new List<Dictionary<string, object>>();
    for (int i = 0; i < fingers.Length; i++)
    {
        fingerStats.Add(new Dictionary<string, object>
        {
            ["finger_index"] = i,
            ["press_count"] = fingers[i].PressCount,
            // Remove hover_count from finger stats - it's meaningless
            // Each finger is sampled equally: totalSamples times
        });
    }
    output["finger_stats"] = fingerStats;

    return JsonSerializer.Serialize(output, new JsonSerializerOptions { WriteIndented = true });
}

    public double GetTotalTime(List<List<(double Distance, int Finger)>> distances)
    {
        double total = 0.0;
        foreach (var group in distances)
        {
            total += GetGroupPressTime(group);
        }
        return total;
    }

    public double GetGroupPressTime(List<(double Distance, int Finger)> distances)
    {
        double maxTS = 0.0;
        double sumTPS = 0.0;

        foreach (var (Distance, Finger) in distances)
        {
            double ts = FittsLaw(Distance);
            if (ts > maxTS) maxTS = ts;
            sumTPS += _fingerCoefficients[Finger];
        }

        return maxTS + sumTPS;
    }

    public double FittsLaw(double Distance)
    {
        return _fittsA + _fittsB * Math.Log2(Distance / 1 + 1);
    }

    public (double Distance, int Finger)[][] GetDistancesByFinger()
    {
        Finger[] fingers = InitializeFingers();

        int estimatedGroups = _fileContent.Length / 2;
        var tempResults = new (double Distance, int Finger)[estimatedGroups][];
        var tempGroup = new (double Distance, int Finger)[20];
        int tempGroupSize = 0;
        int resultCount = 0;

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
                var distance = fingers[press.Finger].TapAndGetDistance(press.Position.X, press.Position.Y);

                if (usedFingers[press.Finger])
                {
                    var newGroup = new (double Distance, int Finger)[tempGroupSize];
                    Array.Copy(tempGroup, 0, newGroup, 0, tempGroupSize);

                    if (resultCount >= tempResults.Length)
                    {
                        var newTempResults = new (double Distance, int Finger)[tempResults.Length * 2][];
                        Array.Copy(tempResults, 0, newTempResults, 0, resultCount);
                        tempResults = newTempResults;
                    }

                    tempResults[resultCount++] = newGroup;
                    tempGroupSize = 0;
                    Array.Clear(usedFingers, 0, usedFingers.Length);
                }

                if (tempGroupSize >= tempGroup.Length)
                {
                    var newTempGroup = new (double Distance, int Finger)[tempGroup.Length * 2];
                    Array.Copy(tempGroup, 0, newTempGroup, 0, tempGroupSize);
                    tempGroup = newTempGroup;
                }

                tempGroup[tempGroupSize++] = (distance, press.Finger);
                usedFingers[press.Finger] = true;
            }
        }

        if (tempGroupSize > 0)
        {
            var finalGroup = new (double Distance, int Finger)[tempGroupSize];
            Array.Copy(tempGroup, 0, finalGroup, 0, tempGroupSize);

            if (resultCount >= tempResults.Length)
            {
                var newTempResults = new (double Distance, int Finger)[resultCount + 1][];
                Array.Copy(tempResults, 0, newTempResults, 0, resultCount);
                tempResults = newTempResults;
            }

            tempResults[resultCount++] = finalGroup;
        }

        var result = new (double Distance, int Finger)[resultCount][];
        Array.Copy(tempResults, 0, result, 0, resultCount);

        return result;
    }

    public string SayHay()
    {
        return "Hi";
    }
}
