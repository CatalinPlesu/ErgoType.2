using System;
using System.IO;
using System.Diagnostics;
using System.Linq;
using System.Collections.Generic;

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



class Fitness
{
    public (double TotalDistance, double TotalTime) FitnessComponents(string fullText, object charPositionMapper)
    {

        var distanceByFinger = GetDistancesByFinger(fullText, charPositionMapper);
        var totalDistance = distanceByFinger.SelectMany(d => d).Select(d => d.Distance).Sum();
        return (totalDistance, 0);
    }

    public double GetTotalTime(List<List<(double Distance, FingerName Finger)>> distances, object TPS)
    {
        return distances.Select(d => GetGroupPressTime(d, TPS)).Sum();
    }

    public double GetGroupPressTime(List<(double Distance, FingerName Finger)> distances, object tps)
    {
        var TS = distances.Select(d => FittsLaw(d.Distance));
        List<double> TPS = ((IEnumerable<object>)tps)
            .Cast<double>()
            .ToList();
        var sumTPS = distances.Select(d => TPS[(int)d.Finger]).Sum();
        return TS.Max() + sumTPS;
    }

    public double FittsLaw(double Distance)
    {
        const double a = 0.1;
        const double b = 0.1;
        // fitts = a + b * Log2 ( Distance / Width + 1)
        var fittsTime = a + b * Math.Log2(Distance / 1 + 1);
        return fittsTime;
    }

    public List<List<(double Distance, FingerName Finger)>> GetDistancesByFinger(string fullText, object charPositionMapper)
    {
        List<(double, FingerName)> distances = new();

        int numberOfFingers = Enum.GetValues(typeof(FingerName)).Length;
        Finger[] fingers = new Finger[numberOfFingers];
        foreach (FingerName fingerName in Enum.GetValues(typeof(FingerName)))
        {
            Point initialHomingPosition = new Point(0, 0);
            int index = (int)fingerName;
            fingers[index] = new Finger(initialHomingPosition, fingerName);
        }
        Finger indexLeftFinger = fingers[(int)FingerName.IndexLeft];

        return new();
    }

    static void Main(string[] args)
    {

        Console.WriteLine("====================");
    }
}
