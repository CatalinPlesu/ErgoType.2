from typing import Callable, List, Dict, Tuple, Optional
import math
from .context import MovementContext, CostComponent

# ============================================================================
# BASE COST CALCULATORS (Pure Functions)
# ============================================================================

def physical_distance(ctx: MovementContext) -> CostComponent:
    """Pure geometric distance - no penalties"""
    if len(ctx.from_position) != len(ctx.to_position):
        raise ValueError("Position dimensionality mismatch")
    
    squared_sum = sum((a - b) ** 2 for a, b in zip(ctx.from_position, ctx.to_position))
    distance = math.sqrt(squared_sum)
    
    return CostComponent(
        layer_name="physical_distance",
        value=distance,
        metadata={
            'from': ctx.from_position,
            'to': ctx.to_position,
            'euclidean_dist': distance
        }
    )

def finger_effort_multiplier(ctx: MovementContext) -> CostComponent:
    """Finger strength penalty based on FINGER_BIAS"""
    from src.config.finger_strength import FINGER_BIAS
    
    bias = FINGER_BIAS[ctx.finger]
    effort = bias.effort
    
    return CostComponent(
        layer_name="finger_effort",
        value=effort,
        metadata={
            'finger': ctx.finger.name,
            'effort_multiplier': effort
        }
    )

def directional_penalty_x(ctx: MovementContext) -> CostComponent:
    """X-axis movement penalty"""
    from src.config.finger_strength import FINGER_BIAS
    
    bias = FINGER_BIAS[ctx.finger]
    dx = abs(ctx.to_position[0] - ctx.from_position[0])
    penalty = dx * dx * bias.x_penalty
    
    return CostComponent(
        layer_name="direction_x",
        value=penalty,
        metadata={
            'dx': dx,
            'x_penalty_factor': bias.x_penalty
        }
    )

def directional_penalty_y(ctx: MovementContext) -> CostComponent:
    """Y-axis movement penalty"""
    from src.config.finger_strength import FINGER_BIAS
    
    bias = FINGER_BIAS[ctx.finger]
    dy = abs(ctx.to_position[1] - ctx.from_position[1])
    penalty = dy * dy * bias.y_penalty
    
    return CostComponent(
        layer_name="direction_y",
        value=penalty,
        metadata={
            'dy': dy,
            'y_penalty_factor': bias.y_penalty
        }
    )

def directional_penalty_z(ctx: MovementContext) -> CostComponent:
    """Z-axis movement penalty (for 3D keyboards)"""
    from src.config.finger_strength import FINGER_BIAS
    
    if len(ctx.from_position) < 3 or len(ctx.to_position) < 3:
        return CostComponent(layer_name="direction_z", value=0.0)
    
    bias = FINGER_BIAS[ctx.finger]
    dz = abs(ctx.to_position[2] - ctx.from_position[2])
    penalty = dz * dz * bias.z_penalty
    
    return CostComponent(
        layer_name="direction_z",
        value=penalty,
        metadata={
            'dz': dz,
            'z_penalty_factor': bias.z_penalty
        }
    )

def same_finger_consecutive_penalty(ctx: MovementContext) -> CostComponent:
    """Penalty for using same finger twice in a row"""
    if ctx.previous_finger is None or ctx.previous_finger != ctx.finger:
        return CostComponent(layer_name="same_finger_penalty", value=0.0)
    
    # Heavy penalty for consecutive same-finger usage
    penalty = 2.0
    
    return CostComponent(
        layer_name="same_finger_penalty",
        value=penalty,
        metadata={'consecutive_finger': ctx.finger.name}
    )

def hand_alternation_bonus(ctx: MovementContext) -> CostComponent:
    """Bonus (negative cost) for alternating hands"""
    if ctx.previous_finger is None:
        return CostComponent(layer_name="hand_alternation", value=0.0)
    
    current_hand = ctx.finger.value[0]  # Assumes enum like LEFT_INDEX, RIGHT_INDEX
    previous_hand = ctx.previous_finger.value[0]
    
    if current_hand != previous_hand:
        bonus = -0.5  # Negative = reward
        return CostComponent(
            layer_name="hand_alternation",
            value=bonus,
            metadata={'alternated': True}
        )
    
    return CostComponent(layer_name="hand_alternation", value=0.0)
