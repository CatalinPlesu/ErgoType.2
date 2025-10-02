from typing import Callable, List, Dict, Tuple, Optional
# ============================================================================
# INTEGRATION WITH EXISTING CODE
# ============================================================================

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


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

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
