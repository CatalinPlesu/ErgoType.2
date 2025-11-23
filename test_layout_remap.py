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
from src.core.layout import Layout

def test_layout_remap():
    """Test that layout remapping works correctly"""
    print("=== Testing Layout Remapping ===")
    
    # Create evaluator
    evaluator = Evaluator(debug=True)
    evaluator.load_keyoard().load_distance().load_layout()
    evaluator.load_dataset(dataset_name='simple_wikipedia')
    evaluator.load_typer()
    
    # Test different layouts
    layouts_to_test = [
        ("qwerty", LAYOUT_DATA["qwerty"]),
        ("dvorak", LAYOUT_DATA["dvorak"]),
        ("colemak", LAYOUT_DATA["colemak"]),
    ]
    
    results = {}
    
    for layout_name, layout_chromosome in layouts_to_test:
        print(f"\n--- Testing {layout_name} ---")
        
        # Reset layout
        evaluator.layout = Layout(evaluator.keyboard, debug=True)
        
        # Apply layout remapping
        evaluator.layout.remap(LAYOUT_DATA["qwerty"], layout_chromosome)
        
        # Load typer with updated layout
        evaluator.load_typer()
        
        # Calculate fitness
        try:
            fitness = evaluator.get_fitness()
            print(f"Fitness result: {fitness}")
            
            if isinstance(fitness, tuple):
                distance, time = fitness
                print(f"Distance: {distance:.4f}, Time: {time:.4f}")
                results[layout_name] = (distance, time)
            else:
                print(f"Unexpected result type: {type(fitness)}")
                results[layout_name] = fitness
                
        except Exception as e:
            print(f"Error calculating fitness for {layout_name}: {e}")
            results[layout_name] = None
    
    print(f"\n=== Results Summary ===")
    for layout_name, result in results.items():
        if result and isinstance(result, tuple):
            print(f"{layout_name}: distance={result[0]:.4f}, time={result[1]:.4f}")
        else:
            print(f"{layout_name}: {result}")
    
    # Check if all results are the same (indicating remapping issue)
    if len(set(str(v) for v in results.values() if v)) == 1:
        print("\n❌ All layouts returned the same result - remapping may not be working")
        return False
    else:
        print("\n✅ Layouts returned different results - remapping is working")
        return True

if __name__ == "__main__":
    success = test_layout_remap()
    if success:
        print("\n🎉 Layout remapping is working correctly!")
    else:
        print("\n💥 Layout remapping issue detected!")