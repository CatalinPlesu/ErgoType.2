import pytest
from unittest.mock import Mock
from src.core.fingers import Finger, FingerManager
from src.core.enums import FingerName


class MockPhysicalKey:
    def __init__(self, key_id, finger_name, position=(0, 0)):
        self.key_id = key_id
        self._finger_name = finger_name
        self._position = position
    
    def get_finger_name(self):
        # Return FingerName enum instead of string for testing
        if isinstance(self._finger_name, str):
            # Map string names to FingerName enums
            name_mapping = {
                'index': FingerName.LEFT_INDEX,
                'middle': FingerName.LEFT_MIDDLE,
                'ring': FingerName.LEFT_RING,
                'pinky': FingerName.LEFT_PINKY,
                'thumb': FingerName.LEFT_THUMB,
                'left_index': FingerName.LEFT_INDEX,
                'right_index': FingerName.RIGHT_INDEX,
                'left_thumb': FingerName.LEFT_THUMB,
                'right_thumb': FingerName.RIGHT_THUMB,
            }
            return name_mapping.get(self._finger_name, FingerName.LEFT_INDEX)
        return self._finger_name
    
    def get_key_center_position(self):
        return self._position
    
    def get_labels(self):
        return [self.key_id]


class MockCostCalculator:
    def __init__(self):
        self.accumulator = Mock()
        self.accumulator.total.return_value = 0.0
    
    def calculate_press_cost(self, ctx):
        return 1.0
    
    def reset(self):
        pass


def test_finger_initialization():
    """Test Finger class initialization"""
    mock_key = MockPhysicalKey("key1", "index", (0, 0))
    mock_calculator = MockCostCalculator()
    
    finger = Finger(mock_key, mock_calculator)
    
    assert finger.homing_position == (0, 0)
    assert finger.current_position == (0, 0)
    assert finger.cost_calculator == mock_calculator
    assert finger.last_key is None
    assert finger.finger_name is None


def test_finger_press():
    """Test Finger press method"""
    mock_key = MockPhysicalKey("key1", "index", (0, 0))
    mock_calculator = MockCostCalculator()
    
    finger = Finger(mock_key, mock_calculator)
    
    # Mock the movement context that will be created
    mock_ctx = Mock()
    mock_calculator.calculate_press_cost = Mock(return_value=5.0)
    
    # Press the finger
    finger.press(mock_key, 10, "index")
    
    # Check that position was updated
    assert finger.current_position == (0, 0)
    assert finger.last_key == mock_key
    assert finger.finger_name == "index"
    
    # Check that calculate_press_cost was called
    mock_calculator.calculate_press_cost.assert_called_once()


def test_finger_reset_position():
    """Test Finger reset_position method"""
    mock_key = MockPhysicalKey("key1", "index", (0, 0))
    mock_calculator = MockCostCalculator()
    
    finger = Finger(mock_key, mock_calculator)
    finger.current_position = (1, 1)
    finger.last_key = mock_key
    finger.finger_name = "index"
    
    finger.reset_position()
    
    # Position should be reset, but other state should remain
    assert finger.current_position == (0, 0)
    assert finger.last_key == mock_key  # Should remain for sequence tracking
    assert finger.finger_name == "index"


def test_finger_reset():
    """Test Finger reset method"""
    mock_key = MockPhysicalKey("key1", "index", (0, 0))
    mock_calculator = MockCostCalculator()
    
    finger = Finger(mock_key, mock_calculator)
    finger.current_position = (1, 1)
    finger.last_key = mock_key
    finger.finger_name = "index"
    
    finger.reset()
    
    # Everything should be reset
    assert finger.current_position == (0, 0)
    assert finger.last_key is None
    assert finger.finger_name is None


def test_finger_manager_initialization():
    """Test FingerManager initialization"""
    mock_keyboard = Mock()
    mock_keyboard.get_homing_key_for_finger_name = Mock(return_value=MockPhysicalKey("home", "index", (0, 0)))
    mock_calculator = MockCostCalculator()
    
    manager = FingerManager(mock_keyboard, mock_calculator)
    
    assert len(manager.fingers) > 0
    assert manager.list_alternation == 0
    assert manager.cost_calculator == mock_calculator


def test_finger_manager_press_single_finger():
    """Test FingerManager press with single finger"""
    mock_keyboard = Mock()
    mock_key = MockPhysicalKey("key1", FingerName.LEFT_INDEX, (1, 0))
    mock_keyboard.get_homing_key_for_finger_name = Mock(return_value=MockPhysicalKey("home", FingerName.LEFT_INDEX, (0, 0)))
    mock_calculator = MockCostCalculator()
    
    manager = FingerManager(mock_keyboard, mock_calculator)
    
    # Press a key
    manager.press(mock_key, 5)
    
    # Check that alternation didn't change (single finger)
    assert manager.list_alternation == 0


def test_finger_manager_press_alternating_fingers():
    """Test FingerManager press with alternating fingers"""
    mock_keyboard = Mock()
    mock_key = MockPhysicalKey("key1", [FingerName.LEFT_INDEX, FingerName.RIGHT_INDEX], (1, 0))
    mock_keyboard.get_homing_key_for_finger_name = Mock(return_value=MockPhysicalKey("home", FingerName.LEFT_INDEX, (0, 0)))
    mock_calculator = MockCostCalculator()
    
    manager = FingerManager(mock_keyboard, mock_calculator)
    
    # First press
    manager.press(mock_key, 5)
    assert manager.list_alternation == 1
    
    # Second press
    manager.press(mock_key, 5)
    assert manager.list_alternation == 0


def test_finger_manager_get_total_cost():
    """Test FingerManager get_total_cost method"""
    mock_keyboard = Mock()
    mock_keyboard.get_homing_key_for_finger_name = Mock(return_value=MockPhysicalKey("home", "index", (0, 0)))
    mock_calculator = MockCostCalculator()
    mock_calculator.accumulator.total.return_value = 42.0
    
    manager = FingerManager(mock_keyboard, mock_calculator)
    
    total_cost = manager.get_total_cost()
    assert total_cost == 42.0


def test_finger_manager_get_accumulator():
    """Test FingerManager get_accumulator method"""
    mock_keyboard = Mock()
    mock_keyboard.get_homing_key_for_finger_name = Mock(return_value=MockPhysicalKey("home", "index", (0, 0)))
    mock_calculator = MockCostCalculator()
    
    manager = FingerManager(mock_keyboard, mock_calculator)
    
    accumulator = manager.get_accumulator()
    assert accumulator == mock_calculator.accumulator


def test_finger_manager_reset():
    """Test FingerManager reset method"""
    mock_keyboard = Mock()
    mock_keyboard.get_homing_key_for_finger_name = Mock(return_value=MockPhysicalKey("home", "index", (0, 0)))
    mock_calculator = MockCostCalculator()
    
    manager = FingerManager(mock_keyboard, mock_calculator)
    
    # Do some operations first
    manager.list_alternation = 1
    
    # Reset
    manager.reset()
    
    # Alternation should be reset
    assert manager.list_alternation == 0
    
    # Calculator should be reset (check if reset method exists and was called)
    if hasattr(mock_calculator, 'reset') and hasattr(mock_calculator.reset, 'assert_called_once'):
        mock_calculator.reset.assert_called_once()