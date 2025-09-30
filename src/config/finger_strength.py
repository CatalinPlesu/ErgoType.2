from src.domain.hand_finger_enum import *
from dataclasses import dataclass
from typing import Dict

@dataclass
class Bias:
    effort: float      # Overall effort multiplier
    x_penalty: float   # Horizontal movement penalty
    y_penalty: float   # Vertical movement penalty  
    z_penalty: float   # Depth movement penalty

# Define bias for left hand fingers only
LEFT_HAND_BIAS = {
    FingerName.LEFT_PINKY: Bias(  effort=2.0, x_penalty=1.3, y_penalty=0.0, z_penalty=0.0),
    FingerName.LEFT_RING: Bias(   effort=1.8, x_penalty=1.0, y_penalty=0.0, z_penalty=0.0),
    FingerName.LEFT_MIDDLE: Bias( effort=1.4, x_penalty=1.0, y_penalty=0.0, z_penalty=0.0),
    FingerName.LEFT_INDEX: Bias(  effort=1.2, x_penalty=1.0, y_penalty=0.0, z_penalty=0.0),
    FingerName.LEFT_THUMB: Bias(  effort=1.0, x_penalty=0.0, y_penalty=1.0, z_penalty=0.0),
}

# Mirror left hand bias to create right hand bias
FINGER_BIAS: Dict[FingerName, Bias] = {}

# Add left hand bias as is
FINGER_BIAS.update(LEFT_HAND_BIAS)

# Mirror to right hand
for left_finger, bias in LEFT_HAND_BIAS.items():
    finger_enum, hand_enum = fingername_to_enums(left_finger)
    right_finger = enums_to_fingername(finger_enum, Hand.RIGHT)
    FINGER_BIAS[right_finger] = bias

print(FINGER_BIAS)
