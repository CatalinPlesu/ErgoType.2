#!/usr/bin/env python3

import sys
sys.path.append('.')

from src.config.config import Config
Config.fitness.use_simplified_fitness = True
Config.fitness.distance_weight = 0.5
Config.fitness.time_weight = 0.5
Config.fitness.simulation_window_size = 256

from src.core.simplified_typer import SimplifiedTyper
from src.core.layout import Layout
from src.core.keyboard import Serial

def test_simplified_fitness():
    """Test simplified fitness calculation with minimal data"""
    print("=== Testing Simplified Fitness Calculation ===")
    
    # Load keyboard
    with open('src/data/keyboards/ansi_60_percent.json', 'r') as f:
        keyboard = Serial.parse(f.read())
    
    layout = Layout(keyboard)
    
    # Create a minimal dataset for testing
    test_dataset = {
        'character_frequencies': [
            {'char': 'a', 'relative': 0.1},
            {'char': 's', 'relative': 0.1},
            {'char': 'd', 'relative': 0.1},
            {'char': 'f', 'relative': 0.1},
            {'char': 'j', 'relative': 0.1},
            {'char': 'k', 'relative': 0.1},
            {'char': 'l', 'relative': 0.1},
            {'char': ';', 'relative': 0.1}
        ]
    }
    
    # Create simplified typer
    typer = SimplifiedTyper(keyboard, None, layout, test_dataset, 'test', debug=True)
    
    # Test fitness calculation
    print("\nTesting fitness calculation...")
    try:
        fitness = typer.fitness()
        print(f"Fitness result: {fitness}")
        print(f"Type: {type(fitness)}")
        
        if isinstance(fitness, tuple):
            distance, time = fitness
            print(f"Distance: {distance:.4f}, Time: {time:.4f}")
            if distance > 0 and time > 0:
                print("✅ Success: Got positive distance and time values")
                return True
            else:
                print("❌ Failed: Got zero or negative values")
                return False
        else:
            print(f"Unexpected fitness format: {fitness}")
            return False
            
    except Exception as e:
        print(f"❌ Error in fitness calculation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simplified_fitness()
    if success:
        print("\n🎉 Simplified fitness calculation is working!")
    else:
        print("\n💥 Simplified fitness calculation failed!")