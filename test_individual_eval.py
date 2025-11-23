#!/usr/bin/env python3

import sys
sys.path.append('.')

from src.config.config import Config
Config.fitness.use_simplified_fitness = True
Config.fitness.distance_weight = 0.5
Config.fitness.time_weight = 0.5

from src.core.evaluator import Evaluator
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
from src.core.ga import Individual

def test_individual_evaluation():
    """Test individual evaluation with debug output"""
    print("=== Testing Individual Evaluation ===")
    
    # Create evaluator
    evaluator = Evaluator(debug=True)
    evaluator.load_keyoard().load_distance().load_layout()
    evaluator.load_dataset(dataset_name='simple_wikipedia')
    evaluator.load_typer()
    
    # Create a test individual (use QWERTY layout)
    from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
    individual = Individual(chromosome=LAYOUT_DATA["qwerty"], generation=0)
    individual.name = "test_qwerty"
    
    # Test the evaluation function directly
    print(f"\nTesting evaluation of {individual.name}...")
    
    # This simulates what happens in the GA evaluation
    try:
        # Remap layout
        from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
        evaluator.layout.remap(LAYOUT_DATA["qwerty"], individual.chromosome)
        
        # Recreate typer with updated layout
        evaluator.load_typer()
        
        # Calculate fitness
        fitness_result = evaluator.get_fitness()
        
        # Debug: Show what we received
        print(f"DEBUG: Received fitness result: {fitness_result} (type: {type(fitness_result)})")
        
        # Handle different fitness result formats
        if isinstance(fitness_result, dict):
            # Legacy fitness format
            distance = fitness_result.get('distance_score', 0)
            time_component = fitness_result.get('ngram_score', 0) * 100  # Scale up
            fitness = distance + time_component
            
        elif isinstance(fitness_result, tuple) and len(fitness_result) == 2:
            # Simplified fitness format (distance, time)
            distance, time_component = fitness_result
            
            # For now, just use raw values - normalization will be done later
            fitness = distance + time_component
        else:
            # Fallback
            fitness = float(fitness_result) if fitness_result is not None else float('inf')
            distance = fitness
            time_component = 0
        
        print(f"Final fitness: {fitness}")
        print(f"Distance: {distance}, Time: {time_component}")
        
        return True
        
    except Exception as e:
        print(f"Error in individual evaluation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_individual_evaluation()
    if success:
        print("\n✅ Individual evaluation working correctly!")
    else:
        print("\n❌ Individual evaluation failed!")