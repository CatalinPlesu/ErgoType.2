using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using System.Runtime.CompilerServices;

namespace FitnessNet;

public record Point(double X, double Y);

public record KeyPress(Point Position, int Finger);

public class Finger
{
    public double X;
    public double Y;
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
