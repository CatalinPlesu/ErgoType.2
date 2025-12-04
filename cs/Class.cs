using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using System.Runtime.CompilerServices;

namespace FitnessNet;

public record Point(double X, double Y);

public record KeyPress(Point Position, int Finger);

// Fixed-point version for fast computation
public struct KeyPressFixed
{
    public long X;
    public long Y;
    public int Finger;

    public KeyPressFixed(long x, long y, int finger)
    {
        X = x;
        Y = y;
        Finger = finger;
    }
}

public class Finger
{
    public long X;
    public long Y;
    long _homingX;
    long _homingY;
    int _index;

    public Finger(long homingX, long homingY, int index)
    {
        X = homingX;
        Y = homingY;
        _homingX = homingX;
        _homingY = homingY;
        _index = index;
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public long TapAndGetDistance(long keyX, long keyY)
    {
        long dx = X - keyX;
        long dy = Y - keyY;
        long distSquared = dx * dx + dy * dy;
        long result = (long)(Math.Sqrt(distSquared));
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
    private long _fittsA;
    private long _fittsB;
    private long[] _fingerCoefficients;
    private long[] _homingPositions; // Flattened: [x0, y0, x1, y1, ...]
    private KeyPress[][] _charMappings;
    private KeyPressFixed[][] _charMappingsFixed; // Fixed-point version
    private int _maxCharCode;
    private int _numFingers;

    public Fitness(string jsonData)
    {
        using JsonDocument doc = JsonDocument.Parse(jsonData);
        JsonElement root = doc.RootElement;

        _textFilePath = root.GetProperty("text_file_path").GetString();
        _fileContent = File.ReadAllText(_textFilePath);

        JsonElement fittsLaw = root.GetProperty("fitts_law");
        _fittsA = (long)(fittsLaw.GetProperty("a").GetDouble() * 10000);
        _fittsB = (long)(fittsLaw.GetProperty("b").GetDouble() * 10000);

        JsonElement fingerCoeffs = root.GetProperty("finger_coefficients");
        _fingerCoefficients = new long[fingerCoeffs.GetArrayLength()];
        int idx = 0;
        foreach (JsonElement coeff in fingerCoeffs.EnumerateArray())
        {
            _fingerCoefficients[idx++] = (long)(coeff.GetDouble() * 10000);
        }

        JsonElement homingPositions = root.GetProperty("homing_positions");
        _numFingers = homingPositions.GetArrayLength();
        _homingPositions = new long[_numFingers * 2];
        idx = 0;
        foreach (JsonElement pos in homingPositions.EnumerateArray())
        {
            double x = pos.GetProperty("x").GetDouble();
            double y = pos.GetProperty("y").GetDouble();
            _homingPositions[idx++] = (long)(x * 10000);
            _homingPositions[idx++] = (long)(y * 10000);
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
        _charMappingsFixed = new KeyPressFixed[_maxCharCode + 1][];

        foreach (JsonProperty charProp in charMappings.EnumerateObject())
        {
            string charStr = charProp.Name;
            if (charStr.Length == 0) continue;

            int charCode = char.ConvertToUtf32(charStr, 0);
            JsonElement keySequence = charProp.Value;

            int sequenceLength = keySequence.GetArrayLength();
            KeyPress[] keyPresses = new KeyPress[sequenceLength];
            KeyPressFixed[] keyPressesFixed = new KeyPressFixed[sequenceLength];

            int i = 0;
            foreach (JsonElement keyPress in keySequence.EnumerateArray())
            {
                double x = keyPress.GetProperty("x").GetDouble();
                double y = keyPress.GetProperty("y").GetDouble();
                int finger = keyPress.GetProperty("finger").GetInt32();

                keyPresses[i] = new KeyPress(new Point(x, y), finger);
                keyPressesFixed[i] = new KeyPressFixed(
                    (long)(x * 10000),
                    (long)(y * 10000),
                    finger);
                i++;
            }

            _charMappings[charCode] = keyPresses;
            _charMappingsFixed[charCode] = keyPressesFixed;
        }
    }

    public Finger[] InitializeFingers()
    {
        Finger[] fingers = new Finger[_numFingers];
        for (int i = 0; i < _numFingers; i++)
        {
            fingers[i] = new Finger(_homingPositions[i * 2], _homingPositions[i * 2 + 1], i);
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
    private long FittsLawInline(long distance)
    {
        // distance is already in fixed-point (scaled by 10000)
        // We need to convert to double only for Log2
        double distDouble = distance / 10000.0;
        double logResult = Math.Log2(distDouble + 1);
        return _fittsA + (long)(_fittsB * logResult);
    }

    public (double TotalDistance, double TotalTime) Compute()
    {
        Finger[] fingers = InitializeFingers();

        long totalDistance = 0;
        long totalTime = 0;

        long[] groupDistances = new long[20];
        int[] groupFingers = new int[20];
        int groupSize = 0;

        bool[] usedFingers = new bool[_numFingers];

        ReadOnlySpan<char> textSpan = _fileContent.AsSpan();

        for (int idx = 0; idx < textSpan.Length; idx++)
        {
            int charCode = textSpan[idx];

            if (charCode > _maxCharCode || _charMappingsFixed[charCode] == null)
                continue;

            KeyPressFixed[] presses = _charMappingsFixed[charCode];

            for (int p = 0; p < presses.Length; p++)
            {
                ref KeyPressFixed press = ref presses[p];
                int fingerIdx = press.Finger;

                if (usedFingers[fingerIdx])
                {
                    long maxTS = 0;
                    long sumTPS = 0;

                    for (int i = 0; i < groupSize; i++)
                    {
                        long distance = groupDistances[i];
                        totalDistance += distance;

                        long ts = FittsLawInline(distance);
                        if (ts > maxTS) maxTS = ts;

                        sumTPS += _fingerCoefficients[groupFingers[i]];
                    }

                    totalTime += maxTS + sumTPS;

                    groupSize = 0;
                    Array.Clear(usedFingers, 0, usedFingers.Length);
                }

                if (groupSize >= groupDistances.Length)
                {
                    var newDistances = new long[groupDistances.Length * 2];
                    var newFingers = new int[groupFingers.Length * 2];
                    Array.Copy(groupDistances, 0, newDistances, 0, groupSize);
                    Array.Copy(groupFingers, 0, newFingers, 0, groupSize);
                    groupDistances = newDistances;
                    groupFingers = newFingers;
                }

                long dist = fingers[fingerIdx].TapAndGetDistance(press.X, press.Y);
                groupDistances[groupSize] = dist;
                groupFingers[groupSize] = fingerIdx;
                groupSize++;
                usedFingers[fingerIdx] = true;
            }
        }

        if (groupSize > 0)
        {
            long maxTS = 0;
            long sumTPS = 0;

            for (int i = 0; i < groupSize; i++)
            {
                long distance = groupDistances[i];
                totalDistance += distance;

                long ts = FittsLawInline(distance);
                if (ts > maxTS) maxTS = ts;

                sumTPS += _fingerCoefficients[groupFingers[i]];
            }

            totalTime += maxTS + sumTPS;
        }

        return (totalDistance / 10000.0, totalTime / 10000.0);
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
            sumTPS += _fingerCoefficients[Finger] / 10000.0;
        }

        return maxTS + sumTPS;
    }

    public double FittsLaw(double Distance)
    {
        return _fittsA / 10000.0 + _fittsB / 10000.0 * Math.Log2(Distance / 1 + 1);
    }

    public (double Distance, int Finger)[][] GetDistancesByFinger()
    {
        Finger[] fingers = InitializeFingers();

        int estimatedGroups = _fileContent.Length / 2;
        var tempResults = new (double Distance, int Finger)[estimatedGroups][];
        var tempGroup = new (double Distance, int Finger)[20];
        int tempGroupSize = 0;
        int resultCount = 0;

        bool[] usedFingers = new bool[_numFingers];

        ReadOnlySpan<char> textSpan = _fileContent.AsSpan();

        for (int idx = 0; idx < textSpan.Length; idx++)
        {
            int charCode = textSpan[idx];

            if (charCode > _maxCharCode || _charMappingsFixed[charCode] == null)
                continue;

            KeyPressFixed[] presses = _charMappingsFixed[charCode];

            for (int p = 0; p < presses.Length; p++)
            {
                ref KeyPressFixed press = ref presses[p];
                long dist = fingers[press.Finger].TapAndGetDistance(press.X, press.Y);
                double distance = dist / 10000.0;

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
