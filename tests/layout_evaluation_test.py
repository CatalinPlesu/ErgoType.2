import pytest
from unittest.mock import Mock, patch
from src.core.layout_evaluation import KeyboardPhenotype


class MockKeyboard:
    def __init__(self):
        self.keys = [
            MockPhysicalKey("key1", ["a", "A"], (0, 0), "index"),
            MockPhysicalKey("key2", ["b", "B"], (1, 0), "middle"),
            MockPhysicalKey("key3", ["c", "C"], (2, 0), "ring")
        ]
    
    def get_homing_key_for_finger_name(self, finger_name):
        # Return a mock key for each finger
        return MockPhysicalKey(f"home_{finger_name}", ["home"], (0, -1), finger_name)


class MockPhysicalKey:
    def __init__(self, key_id, labels, position, finger_name):
        self.key_id = key_id
        self._labels = labels
        self._position = position
        self._finger_name = finger_name
    
    def get_labels(self):
        return self._labels
    
    def get_key_center_position(self):
        return self._position
    
    def get_finger_name(self):
        return self._finger_name


class MockLayoutPhenotype:
    def __init__(self):
        self.virtual_keys = {
            "a": None,
            "b": None,
            "c": None
        }
    
    def get_key_sequence(self, char):
        return [char]
    
    def apply_language_layout(self, remap):
        pass
    
    def generate_random_layout(self):
        pass


class MockKeyMapper:
    def __init__(self, physical_keyboard, layout):
        self.physical_keyboard = physical_keyboard
        self.layout = layout
        self.virtual_to_physical = {
            "a": physical_keyboard.keys[0],
            "b": physical_keyboard.keys[1],
            "c": physical_keyboard.keys[2]
        }
    
    def get_physical_key(self, virtual_key_id):
        return self.virtual_to_physical.get(virtual_key_id)
    
    def get_all_mappings(self):
        return self.virtual_to_physical.copy()
    
    def get_unmapped_virtual_keys(self):
        return set()
    
    def get_physical_key_for_char(self, char):
        key_sequence = self.layout.get_key_sequence(char)
        if key_sequence and len(key_sequence) > 0:
            return self.get_physical_key(key_sequence[0])
        return None


class MockCostCalculator:
    def __init__(self):
        self.accumulator = Mock()
        self.accumulator.total.return_value = 0.0
        self.accumulator.sum_by_layer.return_value = {}
        self.accumulator.sum_by_key.return_value = {}
        self.accumulator.get_matrix.return_value = {}
        self.accumulator.get_press_counts.return_value = {}
    
    def calculate_press_cost(self, ctx):
        return 1.0
    
    def reset(self):
        pass


class MockFingerManager:
    def __init__(self, physical_keyboard, cost_calculator):
        self.cost_calculator = cost_calculator
        self.reset_called = False
        self.used_physical_keys = set()
        self.unreachable_chars = set()
    
    def press(self, physical_key, presses):
        pass
    
    def get_total_cost(self):
        return 100.0
    
    def get_accumulator(self):
        return self.cost_calculator.accumulator
    
    def reset(self):
        self.reset_called = True
    
    def reset_position(self):
        pass


class MockLayoutVisualization:
    def __init__(self, physical_keyboard, layout):
        self.physical_keyboard = physical_keyboard
        self.layout = layout
    
    def set_layout(self, layout, key_mapper):
        pass
    
    def inspect(self, **kwargs):
        return "mock_inspection"


def test_keyboard_phenotype_initialization():
    """Test KeyboardPhenotype initialization"""
    mock_keyboard = MockKeyboard()
    
    phenotype = KeyboardPhenotype(mock_keyboard)
    
    assert phenotype.physical_keyboard == mock_keyboard
    assert phenotype.remap_keys == {}
    assert phenotype.layout is not None
    assert phenotype.key_mapper is not None
    assert phenotype.used_physical_keys == set()
    assert phenotype.unreachable_chars == set()


def test_keyboard_phenotype_initialization_with_remap():
    """Test KeyboardPhenotype initialization with remap"""
    mock_keyboard = MockKeyboard()
    remap = {"a": "b", "b": "a"}
    
    phenotype = KeyboardPhenotype(mock_keyboard, remap)
    
    assert phenotype.layout is not None


@patch('src.core.layout_evaluation.KeyboardPhenotype.layout', MockLayoutPhenotype())
@patch('src.core.layout_evaluation.KeyboardPhenotype.key_mapper', MockKeyMapper(MockKeyboard(), MockLayoutPhenotype()))
@patch('src.core.layout_evaluation.KeyboardPhenotype.cost_calculator', MockCostCalculator())
@patch('src.core.layout_evaluation.KeyboardPhenotype.finger_manager', MockFingerManager(MockKeyboard(), MockCostCalculator()))
def test_keyboard_phenotype_select_remap_keys():
    """Test select_remap_keys method"""
    mock_keyboard = MockKeyboard()
    phenotype = KeyboardPhenotype(mock_keyboard)
    
    keys_list = ["key1", "key2", "key3"]
    phenotype.select_remap_keys(keys_list)
    
    assert phenotype.remap_key_length == 3
    assert phenotype.original_key_list == keys_list


@patch('src.core.layout_evaluation.KeyboardPhenotype.layout', MockLayoutPhenotype())
@patch('src.core.layout_evaluation.KeyboardPhenotype.key_mapper', MockKeyMapper(MockKeyboard(), MockLayoutPhenotype()))
@patch('src.core.layout_evaluation.KeyboardPhenotype.cost_calculator', MockCostCalculator())
@patch('src.core.layout_evaluation.KeyboardPhenotype.finger_manager', MockFingerManager(MockKeyboard(), MockCostCalculator()))
def test_keyboard_phenotype_remap_to_keys():
    """Test remap_to_keys method"""
    mock_keyboard = MockKeyboard()
    phenotype = KeyboardPhenotype(mock_keyboard)
    
    phenotype.select_remap_keys(["a", "b"])
    phenotype.remap_to_keys(["x", "y"])
    
    assert phenotype.remap_keys == {"a": "x", "b": "y"}


@patch('src.core.layout_evaluation.KeyboardPhenotype.layout', MockLayoutPhenotype())
@patch('src.core.layout_evaluation.KeyboardPhenotype.key_mapper', MockKeyMapper(MockKeyboard(), MockLayoutPhenotype()))
@patch('src.core.layout_evaluation.KeyboardPhenotype.cost_calculator', MockCostCalculator())
@patch('src.core.layout_evaluation.KeyboardPhenotype.finger_manager', MockFingerManager(MockKeyboard(), MockCostCalculator()))
@patch('src.core.layout_evaluation.KeyboardPhenotype.visualizer', MockLayoutVisualization(MockKeyboard(), MockLayoutPhenotype()))
def test_keyboard_phenotype_get_key():
    """Test get_key method"""
    mock_keyboard = MockKeyboard()
    phenotype = KeyboardPhenotype(mock_keyboard)
    
    # Test normal key
    result = phenotype.get_key("a")
    assert result is not None
    
    # Test remapped key
    phenotype.select_remap_keys(["a"])
    phenotype.remap_to_keys(["b"])
    result = phenotype.get_key("a")
    # Should return the key for "b" now
    assert result is not None


@patch('src.core.layout_evaluation.KeyboardPhenotype.layout', MockLayoutPhenotype())
@patch('src.core.layout_evaluation.KeyboardPhenotype.key_mapper', MockKeyMapper(MockKeyboard(), MockLayoutPhenotype()))
@patch('src.core.layout_evaluation.KeyboardPhenotype.cost_calculator', MockCostCalculator())
@patch('src.core.layout_evaluation.KeyboardPhenotype.finger_manager', MockFingerManager(MockKeyboard(), MockCostCalculator()))
@patch('src.core.layout_evaluation.KeyboardPhenotype.visualizer', MockLayoutVisualization(MockKeyboard(), MockLayoutPhenotype()))
def test_keyboard_phenotype_inspect_layout():
    """Test inspect_layout method"""
    mock_keyboard = MockKeyboard()
    phenotype = KeyboardPhenotype(mock_keyboard)
    
    result = phenotype.inspect_layout()
    assert result == "mock_inspection"


@patch('src.core.layout_evaluation.KeyboardPhenotype.layout', MockLayoutPhenotype())
@patch('src.core.layout_evaluation.KeyboardPhenotype.key_mapper', MockKeyMapper(MockKeyboard(), MockLayoutPhenotype()))
@patch('src.core.layout_evaluation.KeyboardPhenotype.cost_calculator', MockCostCalculator())
@patch('src.core.layout_evaluation.KeyboardPhenotype.finger_manager', MockFingerManager(MockKeyboard(), MockCostCalculator()))
@patch('src.core.layout_evaluation.KeyboardPhenotype.visualizer', MockLayoutVisualization(MockKeyboard(), MockLayoutPhenotype()))
def test_keyboard_phenotype_inspect_costs():
    """Test inspect_costs method"""
    mock_keyboard = MockKeyboard()
    phenotype = KeyboardPhenotype(mock_keyboard)
    
    result = phenotype.inspect_costs()
    
    assert "total" in result
    assert "by_layer" in result
    assert "by_key" in result
    assert "matrix" in result
    assert "press_counts" in result