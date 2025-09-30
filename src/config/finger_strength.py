from src.domain.keyboard import FingerName

# Finger dimensions: (width_mm, length_mm) - width measured at base
FINGER_DIMENSIONS = {
    FingerName.LEFT_PINKY: (18.8, 61.4),
    FingerName.LEFT_RING: (21, 75.4),
    FingerName.LEFT_MIDDLE: (22.4, 81.7),
    FingerName.LEFT_INDEX: (26.5, 79.1),
    FingerName.LEFT_THUMB: (38.9, 70),
    FingerName.RIGHT_THUMB: (38.9, 70),
    FingerName.RIGHT_INDEX: (26.5, 79.1),
    FingerName.RIGHT_MIDDLE: (22.4, 81.7),
    FingerName.RIGHT_RING: (21, 75.4),
    FingerName.RIGHT_PINKY: (18.8, 61.4)
}

# x, y, z between 1 - leaves as it is , and 2 doubles it.
FINGER_MOBILITY_PENALITY = {
    FingerName.LEFT_PINKY: (1.1, 1, 1),
    FingerName.LEFT_RING: (1.1, 1, 1),
    FingerName.LEFT_MIDDLE: (1.1, 1, 1),
    FingerName.LEFT_INDEX: (1.1, 1, 1),
    FingerName.LEFT_THUMB: (1, 1.1, 1),
    FingerName.RIGHT_THUMB: (1, 1.1, 1),
    FingerName.RIGHT_INDEX: (1.1, 1, 1),
    FingerName.RIGHT_MIDDLE: (1.1, 1, 1),
    FingerName.RIGHT_RING: (1.1, 1, 1),
    FingerName.RIGHT_PINKY: (1.1, 1, 1)
}


def calculate_finger_strength(width_mm, length_mm):
    """Calculate finger strength using formula: (width²) / length"""
    return (width_mm ** 2) / length_mm


# Calculate raw strengths
_raw_strengths = {finger: calculate_finger_strength(*dims)
                  for finger, dims in FINGER_DIMENSIONS.items()}

# Normalize to max value = 1.0
_max_strength = max(_raw_strengths.values())
FINGER_STRENGTHS = {finger: strength /
                    _max_strength for finger, strength in _raw_strengths.items()}


COST_PER_FINGER = {finger: 1/strength for finger,
                   strength in FINGER_STRENGTHS.items()}


def scale_to_range(values_dict, new_min=1, new_max=1.5):
    """
    Scale dictionary values from current range to new range [new_min, new_max]
    """
    current_values = list(values_dict.values())
    current_min = min(current_values)
    current_max = max(current_values)

    # Avoid division by zero
    if current_min == current_max:
        return {finger: new_min for finger in values_dict.keys()}

    # Scale each value to new range
    scaled_dict = {}
    for finger, value in values_dict.items():
        # Normalize to [0,1] then scale to [new_min, new_max]
        normalized = (value - current_min) / (current_max - current_min)
        scaled_value = new_min + normalized * (new_max - new_min)
        scaled_dict[finger] = scaled_value

    return scaled_dict


# Scale COST_PER_FINGER to range [1, 1.5]
SCALED_COST_PER_FINGER = scale_to_range(COST_PER_FINGER, 1, 1.5)

print("Original COST_PER_FINGER:")
print(COST_PER_FINGER)
print("\nScaled COST_PER_FINGER (1 to 1.5):")
print(SCALED_COST_PER_FINGER)

# Verify the scaling worked correctly
print(f"\nMin value: {min(SCALED_COST_PER_FINGER.values())}")
print(f"Max value: {max(SCALED_COST_PER_FINGER.values())}")
