from typing import Callable, List, Dict, Tuple, Optional

# ============================================================================
# COST PIPELINE - The Composable Core
# ============================================================================

class CostPipeline:
    """Functional pipeline for cost calculations"""
    
    def __init__(self, calculators: List[CostCalculator] = None):
        self.calculators = calculators or []
        self._enabled = {calc.__name__: True for calc in self.calculators}
    
    def add(self, calculator: CostCalculator) -> 'CostPipeline':
        """Immutable add - returns new pipeline"""
        new_pipeline = CostPipeline(self.calculators + [calculator])
        new_pipeline._enabled = self._enabled.copy()
        new_pipeline._enabled[calculator.__name__] = True
        return new_pipeline
    
    def disable(self, *layer_names: str) -> 'CostPipeline':
        """Disable specific layers by name"""
        new_pipeline = CostPipeline(self.calculators)
        new_pipeline._enabled = self._enabled.copy()
        for name in layer_names:
            new_pipeline._enabled[name] = False
        return new_pipeline
    
    def enable_only(self, *layer_names: str) -> 'CostPipeline':
        """Enable only specified layers"""
        new_pipeline = CostPipeline(self.calculators)
        new_pipeline._enabled = {name: False for name in self._enabled}
        for name in layer_names:
            new_pipeline._enabled[name] = True
        return new_pipeline
    
    def calculate(self, ctx: MovementContext) -> List[CostComponent]:
        """Execute pipeline and return all components"""
        results = []
        for calc in self.calculators:
            if self._enabled.get(calc.__name__, True):
                component = calc(ctx)
                results.append(component)
        return results
    
    def calculate_dict(self, ctx: MovementContext) -> Dict[str, float]:
        """Execute and return as dictionary"""
        return {comp.layer_name: comp.value for comp in self.calculate(ctx)}
    
    def get_layer_names(self) -> List[str]:
        """Get names of all layers in pipeline"""
        return [calc.__name__ for calc in self.calculators]

