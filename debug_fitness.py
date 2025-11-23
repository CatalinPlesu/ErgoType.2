#!/usr/bin/env python3

import sys
sys.path.append('.')

from src.config.config import Config
from src.core.evaluator import Evaluator

def debug_fitness_calculation():
    """Debug fitness calculation to identify the issue"""
    print("=== Debugging Fitness Calculation ===")
    
    # Set up configuration
    Config.fitness.use_simplified_fitness = True
    Config.fitness.distance_weight = 0.5
    Config.fitness.time_weight = 0.5
    
    # Create evaluator
    evaluator = Evaluator(debug=True)
    evaluator.load_keyoard().load_distance().load_layout()
    
    # Test different layouts
    layouts_to_test = [
        ("qwerty", None),
        ("dvorak", {"dvorak": "qwerty"}),  # This will need proper mapping
    ]
    
    for layout_name, mapping in layouts_to_test:
        print(f"\n--- Testing {layout_name} ---")
        
        # Reset layout
        evaluator.layout = Layout(evaluator.keyboard, debug=True)
        
        if mapping:
            # Apply layout mapping
            for key, value in mapping.items():
                # This is a simplified test - real implementation needs proper layout remapping
                pass
        
        # Load dataset and typer
        try:
            evaluator.load_dataset(dataset_name='simple_wikipedia')
            evaluator.load_typer()
            
            # Calculate fitness
            fitness = evaluator.get_fitness()
            print(f"Fitness result: {fitness}")
            print(f"Type: {type(fitness)}")
            
            if isinstance(fitness, tuple):
                print(f"Tuple contents: distance={fitness[0]}, time={fitness[1]}")
            
        except Exception as e:
            print(f"Error calculating fitness: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_fitness_calculation()