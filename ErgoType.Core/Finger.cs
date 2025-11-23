namespace ErgoType.Core;

using System;

/// <summary>
/// Represents a finger used for typing.
/// </summary>
public enum Finger
{
    /// <summary>
    /// Left pinky finger.
    /// </summary>
    LeftPinky,
    
    /// <summary>
    /// Left ring finger.
    /// </summary>
    LeftRing,
    
    /// <summary>
    /// Left middle finger.
    /// </summary>
    LeftMiddle,
    
    /// <summary>
    /// Left index finger.
    /// </summary>
    LeftIndex,
    
    /// <summary>
    /// Left thumb.
    /// </summary>
    LeftThumb,
    
    /// <summary>
    /// Right index finger.
    /// </summary>
    RightIndex,
    
    /// <summary>
    /// Right middle finger.
    /// </summary>
    RightMiddle,
    
    /// <summary>
    /// Right ring finger.
    /// </summary>
    RightRing,
    
    /// <summary>
    /// Right pinky finger.
    /// </summary>
    RightPinky,
    
    /// <summary>
    /// Right thumb.
    /// </summary>
    RightThumb
}

/// <summary>
/// Extensions for Finger enum.
/// </summary>
public static class FingerExtensions
{
    /// <summary>
    /// Gets the hand that this finger belongs to.
    /// </summary>
    public static Hand GetHand(this Finger finger) => finger switch
    {
        Finger.LeftPinky or Finger.LeftRing or Finger.LeftMiddle or 
        Finger.LeftIndex or Finger.LeftThumb => Hand.Left,
        Finger.RightIndex or Finger.RightMiddle or Finger.RightRing or 
        Finger.RightPinky or Finger.RightThumb => Hand.Right,
        _ => throw new ArgumentException($"Unknown finger: {finger}")
    };
    
    /// <summary>
    /// Gets the finger strength multiplier (lower = faster).
    /// </summary>
    public static double GetStrengthMultiplier(this Finger finger) => finger switch
    {
        Finger.LeftIndex or Finger.RightIndex => 1.0,
        Finger.LeftMiddle or Finger.RightMiddle => 1.2,
        Finger.LeftRing or Finger.RightRing => 1.5,
        Finger.LeftPinky or Finger.RightPinky => 1.8,
        Finger.LeftThumb or Finger.RightThumb => 1.3,
        _ => 1.0
    };
    
    /// <summary>
    /// Gets a display name for the finger.
    /// </summary>
    public static string GetDisplayName(this Finger finger) => finger switch
    {
        Finger.LeftPinky => "Left Pinky",
        Finger.LeftRing => "Left Ring",
        Finger.LeftMiddle => "Left Middle",
        Finger.LeftIndex => "Left Index",
        Finger.LeftThumb => "Left Thumb",
        Finger.RightIndex => "Right Index",
        Finger.RightMiddle => "Right Middle",
        Finger.RightRing => "Right Ring",
        Finger.RightPinky => "Right Pinky",
        Finger.RightThumb => "Right Thumb",
        _ => "Unknown"
    };
}

/// <summary>
/// Represents a hand.
/// </summary>
public enum Hand
{
    Left,
    Right
}