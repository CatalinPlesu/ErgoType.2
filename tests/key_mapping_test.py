import pytest
from unittest.mock import Mock, MagicMock
from src.core.key_mapping import KeyMapper


class MockPhysicalKey:
    def __init__(self, key_id, labels, position=(0, 0)):
        self.key_id = key_id
        self._labels = labels
        self._position = position
    
    def get_labels(self):
        return self._labels
    
    def get_key_center_position(self):
        return self._position


class MockLayoutPhenotype:
    def __init__(self, virtual_keys=None):
        self.virtual_keys = virtual_keys or {}
    
    def get_key_sequence(self, char):
        # Simple mock - return the char itself as the key sequence
        return [char]


def test_key_mapper_initialization():
    """Test KeyMapper initialization"""
    physical_keyboard = Mock()
    physical_keyboard.keys = [
        MockPhysicalKey("key1", ["a", "A"], (0, 0)),
        MockPhysicalKey("key2", ["b", "B"], (1, 0)),
        MockPhysicalKey("key3", ["c", "C"], (2, 0))
    ]
    
    layout = MockLayoutPhenotype({"a": None, "b": None})
    
    mapper = KeyMapper(physical_keyboard, layout)
    
    assert mapper.physical_keyboard == physical_keyboard
    assert mapper.layout_phenotype == layout
    assert isinstance(mapper.virtual_to_physical, dict)


def test_key_mapping_basic():
    """Test basic key mapping functionality"""
    physical_keyboard = Mock()
    physical_keyboard.keys = [
        MockPhysicalKey("key1", ["a", "A"], (0, 0)),
        MockPhysicalKey("key2", ["b", "B"], (1, 0))
    ]
    
    layout = MockLayoutPhenotype({"a": None, "b": None})
    
    mapper = KeyMapper(physical_keyboard, layout)
    
    # Test direct mapping
    assert mapper.get_physical_key("a") == physical_keyboard.keys[0]
    assert mapper.get_physical_key("b") == physical_keyboard.keys[1]


def test_key_mapping_case_insensitive():
    """Test case insensitive key mapping"""
    physical_keyboard = Mock()
    physical_keyboard.keys = [
        MockPhysicalKey("key1", ["a", "A"], (0, 0)),
        MockPhysicalKey("key2", ["b", "B"], (1, 0))
    ]
    
    layout = MockLayoutPhenotype({"a": None, "A": None})
    
    mapper = KeyMapper(physical_keyboard, layout)
    
    # Test lowercase mapping
    assert mapper.get_physical_key("a") == physical_keyboard.keys[0]
    assert mapper.get_physical_key("A") == physical_keyboard.keys[0]


def test_key_mapping_special_keys():
    """Test special key mapping"""
    physical_keyboard = Mock()
    physical_keyboard.keys = [
        MockPhysicalKey("key1", ["a", "A"], (0, 0)),
        MockPhysicalKey("key2", ["Shift", "shift"], (1, 0)),
        MockPhysicalKey("key3", ["Space", " "], (2, 0))
    ]
    
    layout = MockLayoutPhenotype({"a": None})
    
    mapper = KeyMapper(physical_keyboard, layout)
    
    # Test special keys are added automatically
    assert mapper.get_physical_key("Shift") is not None
    assert mapper.get_physical_key("Space") is not None


def test_get_physical_key_for_char():
    """Test getting physical key for character"""
    physical_keyboard = Mock()
    physical_keyboard.keys = [
        MockPhysicalKey("key1", ["a", "A"], (0, 0)),
        MockPhysicalKey("key2", ["b", "B"], (1, 0))
    ]
    
    layout = MockLayoutPhenotype()
    layout.get_key_sequence = Mock(return_value=["a"])
    layout.virtual_keys = {"a": None}  # Add the virtual key
    
    mapper = KeyMapper(physical_keyboard, layout)
    
    result = mapper.get_physical_key_for_char("a")
    assert result == physical_keyboard.keys[0]


def test_unmapped_virtual_keys():
    """Test getting unmapped virtual keys"""
    physical_keyboard = Mock()
    physical_keyboard.keys = [
        MockPhysicalKey("key1", ["a", "A"], (0, 0))
    ]
    
    layout = MockLayoutPhenotype({"a": None, "b": None})
    
    mapper = KeyMapper(physical_keyboard, layout)
    
    unmapped = mapper.get_unmapped_virtual_keys()
    assert unmapped == {"b"}


def test_get_all_mappings():
    """Test getting all mappings"""
    physical_keyboard = Mock()
    physical_keyboard.keys = [
        MockPhysicalKey("key1", ["a", "A"], (0, 0))
    ]
    
    layout = MockLayoutPhenotype({"a": None})
    
    mapper = KeyMapper(physical_keyboard, layout)
    
    all_mappings = mapper.get_all_mappings()
    assert "a" in all_mappings
    assert all_mappings["a"] == physical_keyboard.keys[0]