using System;
using System.Linq;
using System.Collections.Generic;

namespace FitnessNet;

public record Point(double X, double Y);

public enum FingerName
{
    PinkyLeft = 0,
    RingLeft,
    MiddleLeft,
    IndexLeft,
    ThumbLeft,
    ThumbRight,
    IndexRight,
    MiddleRight,
    RingRight,
    PinkyRight
}

public class Finger
{
    Point _currentPosition;
    Point _homingPosition;
    FingerName _finger;

    public Finger(Point homing, FingerName finger)
    {
        _currentPosition = homing;
        _homingPosition = homing;
        _finger = finger;
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
    public (double TotalDistance, double TotalTime) FitnessComponents(string fullText, Dictionary<char, Point> charPositionMapper)
    {
        var distanceByFinger = GetDistancesByFinger(fullText, charPositionMapper);
        var totalDistance = distanceByFinger.SelectMany(d => d).Select(d => d.Distance).Sum();
        return (totalDistance, 0);
    }

    public double GetTotalTime(List<List<(double Distance, FingerName Finger)>> distances, double[] TPS)
    {
        return distances.Select(d => GetGroupPressTime(d, TPS)).Sum();
    }

    public double GetGroupPressTime(List<(double Distance, FingerName Finger)> distances, double[] tps)
    {
        var TS = distances.Select(d => FittsLaw(d.Distance));
        var sumTPS = distances.Select(d => tps[(int)d.Finger]).Sum();
        return TS.Max() + sumTPS;
    }

    public double FittsLaw(double Distance)
    {
        const double a = 0.1;
        const double b = 0.1;
        var fittsTime = a + b * Math.Log2(Distance / 1 + 1);
        return fittsTime;
    }

    public List<List<(double Distance, FingerName Finger)>> GetDistancesByFinger(string fullText, Dictionary<char, Point> charPositionMapper)
    {
        int numberOfFingers = Enum.GetValues(typeof(FingerName)).Length;
        Finger[] fingers = new Finger[numberOfFingers];

        foreach (FingerName fingerName in Enum.GetValues(typeof(FingerName)))
        {
            Point initialHomingPosition = new Point(0, 0);
            int index = (int)fingerName;
            fingers[index] = new Finger(initialHomingPosition, fingerName);
        }

        List<List<(double Distance, FingerName Finger)>> result = new();
        List<(double Distance, FingerName Finger)> currentGroup = new();

        foreach (char c in fullText)
        {
            if (charPositionMapper.TryGetValue(c, out Point keyPosition))
            {
                FingerName finger = DetermineFingerForCharacter(c);
                var distance = fingers[(int)finger].TapAndGetDistance(keyPosition);
                currentGroup.Add((distance, finger));
            }
        }

        result.Add(currentGroup);
        return result;
    }

    private FingerName DetermineFingerForCharacter(char c)
    {
        // Implement your logic to determine which finger should press which character
        // This is a simplified version - you'll need to implement proper finger assignment
        return FingerName.IndexLeft; // Placeholder
    }

    public string SayHay()
    {
        return "Hi";
    }
}
