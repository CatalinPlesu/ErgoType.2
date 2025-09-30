from enum import Enum

class FingerName(Enum):
    LEFT_PINKY = 0
    LEFT_RING = 1
    LEFT_MIDDLE = 2
    LEFT_INDEX = 3
    LEFT_THUMB = 4
    RIGHT_THUMB = 5
    RIGHT_INDEX = 6
    RIGHT_MIDDLE = 7
    RIGHT_RING = 8
    RIGHT_PINKY = 9


class Finger(Enum):
    UNKNOWN = 0
    THUMB = 1
    INDEX = 2
    MIDDLE = 3
    RING = 4
    PINKY = 5


class Hand(Enum):
    UNKNOWN = 0
    LEFT = 1
    RIGHT = 2
    BOTH = 3


FINGER_NAME_MAP = {
    FingerName.LEFT_PINKY: (Finger.PINKY, Hand.LEFT),
    FingerName.LEFT_RING: (Finger.RING, Hand.LEFT),
    FingerName.LEFT_MIDDLE: (Finger.MIDDLE, Hand.LEFT),
    FingerName.LEFT_INDEX: (Finger.INDEX, Hand.LEFT),
    FingerName.LEFT_THUMB: (Finger.THUMB, Hand.LEFT),
    FingerName.RIGHT_THUMB: (Finger.THUMB, Hand.RIGHT),
    FingerName.RIGHT_INDEX: (Finger.INDEX, Hand.RIGHT),
    FingerName.RIGHT_MIDDLE: (Finger.MIDDLE, Hand.RIGHT),
    FingerName.RIGHT_RING: (Finger.RING, Hand.RIGHT),
    FingerName.RIGHT_PINKY: (Finger.PINKY, Hand.RIGHT)
}


def fingername_to_enums(fingername):
    return FINGER_NAME_MAP[fingername]


def enums_to_fingername(finger, hand):
    if finger == Finger.THUMB and hand == Hand.BOTH:
        return [FingerName.LEFT_THUMB, FingerName.RIGHT_THUMB]

    for key, value in FINGER_NAME_MAP.items():
        if value[0] == finger and value[1] == hand:
            return key
