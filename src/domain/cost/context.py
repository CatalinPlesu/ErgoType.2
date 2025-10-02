from dataclasses import dataclass
from typing import Callable, List, Dict, Tuple, Optional
# ============================================================================
# COST LAYER DEFINITIONS
# ============================================================================

@dataclass
class MovementContext:
    """All information about a single key press movement"""
    physical_key: 'PhysicalKey'  # The key being pressed
    finger: FingerName
    from_position: tuple  # Current finger position
    to_position: tuple    # Target key position
    press_count: float    # Number of times this press happens
    previous_key: Optional['PhysicalKey'] = None
    previous_finger: Optional[FingerName] = None


@dataclass
class CostComponent:
    """A single cost calculation result"""
    layer_name: str
    value: float
    metadata: dict = None  # Optional debugging info
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

# Type alias for cost calculator functions
CostCalculator = Callable[[MovementContext], CostComponent]
