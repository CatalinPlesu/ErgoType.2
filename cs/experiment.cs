using System;
using System.Collections.Generic;
using System.Linq;

// ==========================================
// 1. TWEAK YOUR VALUES HERE
// ==========================================
double fitts_a = 0.1;          // Reaction time (seconds)
double fitts_b = 0.3;        // Movement difficulty (seconds/bit) - Adjusted slightly for target
double finger_press_cost = 0.07; // Cost to press a key (seconds)
int target_wpm = 40;           // Goal WPM
int words_count = 40;          // Number of words to simulate
int chars_per_word = 6;        // Chars per word (e.g., 5 letters + 1 space)
// ==========================================

// 2. GENERATE CONTENT (40 words of 6 chars)
string pattern = "abcde "; // 6 chars
string text = string.Join("", Enumerable.Repeat(pattern, words_count));

// 3. SETUP SIMULATION DATA (Hardcoded Layout)
// Simple linear layout for testing: keys 0.0 to 9.0
var fingers = new Finger[10];
for (int i = 0; i < 10; i++) fingers[i] = new Finger(new Point(i, 0), i); // Homing positions (0,0) to (9,0)

// Map characters 'a', 'b', 'c', 'd', 'e' to specific fingers/locations
var charMap = new Dictionary<char, KeyPress[]>
{
    { 'a', new[] { new KeyPress(new Point(0.5, 1), 0) } }, // Finger 0
    { 'b', new[] { new KeyPress(new Point(1.5, 1), 1) } }, // Finger 1
    { 'c', new[] { new KeyPress(new Point(2.5, 1), 2) } }, // Finger 2
    { 'd', new[] { new KeyPress(new Point(3.5, 1), 3) } }, // Finger 3
    { 'e', new[] { new KeyPress(new Point(4.5, 1), 4) } }, // Finger 4
    { ' ', new[] { new KeyPress(new Point(5.0, 2), 5) } }  // Space on Finger 5
};

// 4. RUN SIMULATION LOGIC
var groups = new List<List<(double Dist, int Finger)>>();
var currentGroup = new List<(double Dist, int Finger)>();

foreach (char c in text)
{
    if (!charMap.ContainsKey(c)) continue;

    foreach (var press in charMap[c])
    {
        double dist = fingers[press.Finger].Tap(press.Position);

        // If finger used in current chord, push group and start new
        if (currentGroup.Any(x => x.Finger == press.Finger))
        {
            groups.Add(currentGroup);
            currentGroup = new List<(double, int)>();
        }
        currentGroup.Add((dist, press.Finger));
    }
}
if (currentGroup.Any()) groups.Add(currentGroup);

// 5. CALCULATE TIME
double totalTime = 0;
foreach (var group in groups)
{
    // Fitts Law for travel time
    var travelTimes = group.Select(x => fitts_a + fitts_b * Math.Log2(x.Dist / 1.0 + 1)).ToList();

    // Sum of execution times (finger press costs)
    var pressCosts = group.Select(x => finger_press_cost).Sum();

    // Group time = Max Travel + Total Press Costs
    totalTime += (travelTimes.Any() ? travelTimes.Max() : 0) + pressCosts;
}

// 6. PRINT RESULTS
double total_chars = text.Length;
double wpm = (total_chars / chars_per_word) / (totalTime / 60.0);

Console.WriteLine($"--- SIMULATION REPORT ---");
Console.WriteLine($"Text Length:   {total_chars} chars");
Console.WriteLine($"Total Time:    {totalTime:F4} seconds");
Console.WriteLine($"Calculated WPM:{wpm:F2}");
Console.WriteLine($"Target:        60.00 seconds ({target_wpm} WPM)");

if (Math.Abs(totalTime - 60.0) < 1.0)
    Console.WriteLine(">> RESULT: PERFECTLY CALIBRATED <<");
else if (totalTime < 60.0)
    Console.WriteLine($">> TOO FAST. Increase 'fitts_b' (try {fitts_b * (60 / totalTime):F3}) or 'finger_press_cost'.");
else
    Console.WriteLine($">> TOO SLOW. Decrease 'fitts_b' (try {fitts_b * (60 / totalTime):F3}) or 'finger_press_cost'.");

// ==========================================
// DEFINITIONS
// ==========================================
public record Point(double X, double Y);
public record KeyPress(Point Position, int Finger);

public class Finger
{
    Point _pos;
    Point _home;
    public int Index;
    public Finger(Point home, int idx) { _pos = home; _home = home; Index = idx; }
    public double Tap(Point target)
    {
        double d = Math.Sqrt(Math.Pow(_pos.X - target.X, 2) + Math.Pow(_pos.Y - target.Y, 2));
        _pos = target;
        return d;
    }
}
