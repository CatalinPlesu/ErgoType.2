from typing import Callable, List, Dict, Tuple, Optional
from collections import defaultdict
from .context import CostComponent

# ============================================================================
# COST ACCUMULATOR - Collects results per physical key
# ============================================================================

class CostAccumulator:
    """Accumulates costs per physical key across all presses"""
    
    def __init__(self):
        # Structure: {physical_key_id: [CostComponent, CostComponent, ...]}
        self._costs_by_key: Dict[str, List[CostComponent]] = defaultdict(list)
        self._press_counts: Dict[str, float] = defaultdict(float)
    
    def record(self, physical_key_id: str, components: List[CostComponent], 
               press_count: float = 1.0):
        """Record cost components for a physical key press"""
        for component in components:
            # Scale by press count
            scaled = CostComponent(
                layer_name=component.layer_name,
                value=component.value * press_count,
                metadata=component.metadata
            )
            self._costs_by_key[physical_key_id].append(scaled)
        
        self._press_counts[physical_key_id] += press_count
    
    def get_matrix(self) -> Dict[str, Dict[str, List[float]]]:
        """
        Returns cost matrix structure:
        {
            physical_key_id: {
                layer_name: [cost1, cost2, ...],
                ...
            }
        }
        """
        matrix = {}
        for key_id, components in self._costs_by_key.items():
            matrix[key_id] = defaultdict(list)
            for comp in components:
                matrix[key_id][comp.layer_name].append(comp.value)
        return dict(matrix)
    
    def sum_by_key(self, layer_names: List[str] = None) -> Dict[str, float]:
        """Sum costs per physical key, optionally filtering layers"""
        result = {}
        matrix = self.get_matrix()
        
        for key_id, layers in matrix.items():
            if layer_names is None:
                # Sum all layers
                result[key_id] = sum(sum(costs) for costs in layers.values())
            else:
                # Sum only specified layers
                result[key_id] = sum(
                    sum(layers.get(layer, [])) 
                    for layer in layer_names
                )
        return result
    
    def sum_by_layer(self) -> Dict[str, float]:
        """Get total cost per layer across all keys"""
        layer_totals = defaultdict(float)
        for key_id, components in self._costs_by_key.items():
            for comp in components:
                layer_totals[comp.layer_name] += comp.value
        return dict(layer_totals)
    
    def total(self, layer_names: List[str] = None) -> float:
        """Total cost across all keys and layers"""
        return sum(self.sum_by_key(layer_names).values())
    
    def get_press_counts(self) -> Dict[str, float]:
        """Get total press count per physical key"""
        return dict(self._press_counts)
    
    def get_average_cost_per_press(self, key_id: str, 
                                    layer_names: List[str] = None) -> float:
        """Average cost per press for a specific key"""
        total_cost = self.sum_by_key(layer_names).get(key_id, 0.0)
        press_count = self._press_counts.get(key_id, 0)
        return total_cost / press_count if press_count > 0 else 0.0

