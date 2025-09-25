from kle.kle_model import FingerName

# Finger dimensions: (width_mm, length_mm) - width measured at base
FINGER_DIMENSIONS = {
    FingerName.LEFT_PINKY: (18.8, 61.4),
    FingerName.LEFT_RING: (19.7, 75.4),
    FingerName.LEFT_MIDDLE: (22.4, 81.7),
    FingerName.LEFT_INDEX: (26.5, 79.1),
    FingerName.LEFT_THUMB: (38.9, 70),
    FingerName.RIGHT_THUMB: (38.9, 70),
    FingerName.RIGHT_INDEX: (26.5, 79.1),
    FingerName.RIGHT_MIDDLE: (22.4, 81.7),
    FingerName.RIGHT_RING: (19.7, 75.4),
    FingerName.RIGHT_PINKY: (18.8, 61.4)
}


def calculate_finger_strength(width_mm, length_mm):
    """Calculate finger strength using formula: (width²) / length"""
    return (width_mm ** 2) / length_mm


# Calculate raw strengths
_raw_strengths = {finger: calculate_finger_strength(*dims)
                  for finger, dims in FINGER_DIMENSIONS.items()}

# Normalize to max value = 1.0
_max_strength = max(_raw_strengths.values())
FINGER_STRENGTHS = {finger: strength / _max_strength
                    for finger, strength in _raw_strengths.items()}

# List ordered by enum for easy indexing
FINGER_STRENGTH_LIST = [FINGER_STRENGTHS[finger] for finger in FingerName]
print(FINGER_STRENGTHS)
