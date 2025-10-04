import pytest
from src.core.enums import FingerName, Finger, Hand, fingername_to_enums, enums_to_fingername, FINGER_NAME_MAP


def test_fingername_enum():
    """Test FingerName enum values"""
    assert FingerName.LEFT_PINKY.value == 0
    assert FingerName.LEFT_RING.value == 1
    assert FingerName.LEFT_MIDDLE.value == 2
    assert FingerName.LEFT_INDEX.value == 3
    assert FingerName.LEFT_THUMB.value == 4
    assert FingerName.RIGHT_THUMB.value == 5
    assert FingerName.RIGHT_INDEX.value == 6
    assert FingerName.RIGHT_MIDDLE.value == 7
    assert FingerName.RIGHT_RING.value == 8
    assert FingerName.RIGHT_PINKY.value == 9


def test_finger_enum():
    """Test Finger enum values"""
    assert Finger.UNKNOWN.value == 0
    assert Finger.THUMB.value == 1
    assert Finger.INDEX.value == 2
    assert Finger.MIDDLE.value == 3
    assert Finger.RING.value == 4
    assert Finger.PINKY.value == 5


def test_hand_enum():
    """Test Hand enum values"""
    assert Hand.UNKNOWN.value == 0
    assert Hand.LEFT.value == 1
    assert Hand.RIGHT.value == 2
    assert Hand.BOTH.value == 3


def test_finger_name_map():
    """Test FINGER_NAME_MAP contains all expected mappings"""
    expected_mappings = {
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
    
    for finger_name, expected in expected_mappings.items():
        assert FINGER_NAME_MAP[finger_name] == expected


def test_fingername_to_enums():
    """Test fingername_to_enums function"""
    result = fingername_to_enums(FingerName.LEFT_INDEX)
    expected = (Finger.INDEX, Hand.LEFT)
    assert result == expected


def test_enums_to_fingername():
    """Test enums_to_fingername function"""
    # Test normal case
    result = enums_to_fingername(Finger.INDEX, Hand.LEFT)
    assert result == FingerName.LEFT_INDEX
    
    # Test thumb both hands case
    result = enums_to_fingername(Finger.THUMB, Hand.BOTH)
    assert result == [FingerName.LEFT_THUMB, FingerName.RIGHT_THUMB]
    
    # Test non-existent combination
    result = enums_to_fingername(Finger.UNKNOWN, Hand.UNKNOWN)
    assert result is None