import pytest
from unittest.mock import Mock
from src.core.cost_calculator import CostCalculatorPlugin, create_default_pipeline, create_experimental_pipeline


class MockMovementContext:
    def __init__(self, physical_key, finger, from_position, to_position, press_count, previous_key=None, previous_finger=None):
        self.physical_key = physical_key
        self.finger = finger
        self.from_position = from_position
        self.to_position = to_position
        self.press_count = press_count
        self.previous_key = previous_key
        self.previous_finger = previous_finger


class MockCostComponent:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class MockPipeline:
    def __init__(self, calculators):
        self.calculators = calculators
    
    def calculate(self, ctx):
        # Mock calculation - return some dummy components
        return [
            MockCostComponent("distance", 1.0),
            MockCostComponent("effort", 2.0),
            MockCostComponent("direction", 0.5)
        ]


def test_cost_calculator_plugin_initialization():
    """Test CostCalculatorPlugin initialization"""
    pipeline = MockPipeline([])
    plugin = CostCalculatorPlugin(pipeline)
    
    assert plugin.pipeline == pipeline
    assert plugin.accumulator is not None


def test_cost_calculator_calculate_press_cost():
    """Test calculate_press_cost method"""
    pipeline = MockPipeline([])
    plugin = CostCalculatorPlugin(pipeline)
    
    # Mock context
    ctx = MockMovementContext(
        physical_key="key1",
        finger="index",
        from_position=(0, 0),
        to_position=(1, 0),
        press_count=10
    )
    
    cost = plugin.calculate_press_cost(ctx)
    
    # Should return sum of component values * press_count
    # 1.0 + 2.0 + 0.5 = 3.5 * 10 = 35.0
    assert cost == 35.0


def test_cost_calculator_get_accumulator():
    """Test get_accumulator method"""
    pipeline = MockPipeline([])
    plugin = CostCalculatorPlugin(pipeline)
    
    accumulator = plugin.get_accumulator()
    assert accumulator is not None


def test_cost_calculator_reset():
    """Test reset method"""
    pipeline = MockPipeline([])
    plugin = CostCalculatorPlugin(pipeline)
    
    # Do some calculation first
    ctx = MockMovementContext(
        physical_key="key1",
        finger="index",
        from_position=(0, 0),
        to_position=(1, 0),
        press_count=10
    )
    plugin.calculate_press_cost(ctx)
    
    # Reset
    plugin.reset()
    
    # Accumulator should be reset (new instance)
    assert plugin.accumulator is not None


def test_create_default_pipeline():
    """Test create_default_pipeline function"""
    pipeline = create_default_pipeline()
    
    assert pipeline is not None
    # Should have the expected calculators
    assert len(pipeline.calculators) > 0


def test_create_experimental_pipeline():
    """Test create_experimental_pipeline function"""
    pipeline = create_experimental_pipeline()
    
    assert pipeline is not None
    # Should have more calculators than default (if experimental features are added)
    assert len(pipeline.calculators) >= len(create_default_pipeline().calculators)