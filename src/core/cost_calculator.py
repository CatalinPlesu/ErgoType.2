from typing import Callable, List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class MovementContext:
    """All information about a single key press movement"""
    physical_key: 'PhysicalKey'  # The key being pressed
    finger: str
    from_position: tuple  # Current finger position
    to_position: tuple    # Target key position
    press_count: float    # Number of times this press happens
    previous_key: Optional['PhysicalKey'] = None
    previous_finger: Optional[str] = None


@dataclass 
class CostComponent:
    """A single cost calculation result"""
    layer_name: str
    value: float
    metadata: dict = None  # Optional debugging info
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CostPipeline:
    """Pipeline of cost calculators"""
    
    def __init__(self, calculators):
        self.calculators = calculators
    
    def calculate(self, ctx: MovementContext) -> List[CostComponent]:
        """Calculate cost through all calculators in the pipeline"""
        return [calc(ctx) for calc in self.calculators]
    
    def add(self, calculator):
        """Add a calculator to the pipeline"""
        return CostPipeline(self.calculators + [calculator])


class CostAccumulator:
    """Accumulates and analyzes cost data"""
    
    def __init__(self):
        self.records = []
    
    def record(self, physical_key_id, components, press_count):
        """Record a cost calculation"""
        self.records.append({
            'physical_key_id': physical_key_id,
            'components': components,
            'press_count': press_count
        })
    
    def total(self, layer_names=None):
        """Calculate total accumulated cost"""
        total = 0.0
        for record in self.records:
            for component in record['components']:
                if layer_names is None or component.layer_name in layer_names:
                    total += component.value * record['press_count']
        return total
    
    def sum_by_layer(self):
        """Sum costs by layer name"""
        layer_totals = {}
        for record in self.records:
            for component in record['components']:
                layer_name = component.layer_name
                if layer_name not in layer_totals:
                    layer_totals[layer_name] = 0.0
                layer_totals[layer_name] += component.value * record['press_count']
        return layer_totals
    
    def sum_by_key(self, layer_names=None):
        """Sum costs by physical key"""
        key_totals = {}
        for record in self.records:
            key_id = record['physical_key_id']
            if key_id not in key_totals:
                key_totals[key_id] = 0.0
            
            for component in record['components']:
                if layer_names is None or component.layer_name in layer_names:
                    key_totals[key_id] += component.value * record['press_count']
        return key_totals
    
    def get_matrix(self):
        """Get cost matrix (for advanced analysis)"""
        return {
            'records': self.records,
            'layer_totals': self.sum_by_layer(),
            'key_totals': self.sum_by_key()
        }
    
    def get_press_counts(self):
        """Get press counts by key"""
        press_counts = {}
        for record in self.records:
            key_id = record['physical_key_id']
            if key_id not in press_counts:
                press_counts[key_id] = 0
            press_counts[key_id] += record['press_count']
        return press_counts


def physical_distance(ctx: MovementContext) -> CostComponent:
    """Calculate cost based on physical distance"""
    from math import sqrt
    
    dx = ctx.to_position[0] - ctx.from_position[0]
    dy = ctx.to_position[1] - ctx.from_position[1]
    distance = sqrt(dx*dx + dy*dy)
    
    return CostComponent("physical_distance", distance)


def finger_effort_multiplier(ctx: MovementContext) -> CostComponent:
    """Calculate cost based on finger effort"""
    # Simple finger effort mapping
    finger_effort_map = {
        'pinky': 2.0,
        'ring': 1.5,
        'middle': 1.2,
        'index': 1.0,
        'thumb': 1.3
    }
    
    finger_str = str(ctx.finger).lower()
    effort = 1.0
    for finger_name, multiplier in finger_effort_map.items():
        if finger_name in finger_str:
            effort = multiplier
            break
    
    return CostComponent("finger_effort", effort)


def directional_penalty_x(ctx: MovementContext) -> CostComponent:
    """Calculate penalty for horizontal movement"""
    dx = abs(ctx.to_position[0] - ctx.from_position[0])
    penalty = dx * 0.1
    return CostComponent("directional_x", penalty)


def directional_penalty_y(ctx: MovementContext) -> CostComponent:
    """Calculate penalty for vertical movement"""
    dy = abs(ctx.to_position[1] - ctx.from_position[1])
    penalty = dy * 0.15
    return CostComponent("directional_y", penalty)


def directional_penalty_z(ctx: MovementContext) -> CostComponent:
    """Calculate penalty for finger height changes"""
    # Simplified - assume z-difference based on finger movement
    penalty = 0.05  # Small penalty for any finger movement
    return CostComponent("directional_z", penalty)


class CostCalculatorPlugin:
    """
    Drop-in replacement for the cost calculation in Finger class.
    Plugs cleanly into your existing code.
    """
    
    def __init__(self, pipeline: CostPipeline):
        self.pipeline = pipeline
        self.accumulator = CostAccumulator()
    
    def calculate_press_cost(self, ctx: MovementContext) -> float:
        """
        Calculate total cost for a press (backward compatible).
        Returns single float for existing code.
        """
        components = self.pipeline.calculate(ctx)
        
        # Use Python's built-in id() to get unique identifier
        key_identifier = str(id(ctx.physical_key))
        
        # Record in accumulator
        self.accumulator.record(
            physical_key_id=key_identifier,
            components=components,
            press_count=ctx.press_count
        )
        
        # Return sum for backward compatibility
        return sum(comp.value for comp in components) * ctx.press_count
    
    def get_accumulator(self) -> CostAccumulator:
        """Get the accumulator for detailed analysis"""
        return self.accumulator
    
    def reset(self):
        """Reset accumulator"""
        self.accumulator = CostAccumulator()


def create_default_pipeline() -> CostPipeline:
    """Factory function for standard cost pipeline"""
    return CostPipeline([
        physical_distance,
        finger_effort_multiplier,
        directional_penalty_x,
        directional_penalty_y,
        directional_penalty_z,
    ])


def create_experimental_pipeline() -> CostPipeline:
    """Pipeline with experimental features"""
    return create_default_pipeline()\
        .add(same_finger_consecutive_penalty)\
        .add(hand_alternation_bonus)


def same_finger_consecutive_penalty(ctx: MovementContext) -> CostComponent:
    """Penalty for consecutive presses with same finger"""
    penalty = 0.0
    if ctx.previous_key and ctx.previous_finger == ctx.finger:
        penalty = 0.2
    return CostComponent("same_finger_penalty", penalty)


def hand_alternation_bonus(ctx: MovementContext) -> CostComponent:
    """Bonus for hand alternation"""
    bonus = 0.0
    # Simple hand alternation detection (would need more complex logic in real implementation)
    if ctx.previous_finger and str(ctx.previous_finger) != str(ctx.finger):
        bonus = -0.1  # Negative cost = bonus
    return CostComponent("hand_alternation_bonus", bonus)