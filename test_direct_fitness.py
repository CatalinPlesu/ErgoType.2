#!/usr/bin/env python3

import sys
sys.path.append('.')

from src.config.config import Config
Config.fitness.use_simplified_fitness = True
Config.fitness.distance_weight = 0.5
Config.fitness.time_weight = 0.5

from src.core.evaluator import Evaluator
from src.core.simplified_typer import SimplifiedTyper
from src.core.layout import Layout
from src.core.keyboard import Serial

def test_direct_fitness():
    """Test fitness calculation directly"""
    print("=== Testing Direct Fitness Calculation ===")
    
    # Load keyboard
    with open('src/data/keyboards/ansi_60_percent.json', 'r') as f:
        keyboard = Serial.parse(f.read())
    
    layout = Layout(keyboard)
    
    # Create minimal dataset
    test_dataset = {
        'character_frequencies': [
            {'char': 'a', 'relative': 0.1},
            {'char': 's', 'relative': 0.1},
            {'char': 'd', 'relative': 0.1},
            {'char': 'f', 'relative': 0.1}
        ]
    }
    
    # Create simplified typer
    typer = SimplifiedTyper(keyboard, None, layout, test_dataset, 'test', debug=True)
    
    print("\nTesting fitness calculation...")
    try:
        fitness = typer.fitness()
        print(f"Fitness result: {fitness}")
        print(f"Type: {type(fitness)}")
        
        if isinstance(fitness, tuple):
            distance, time = fitness
            print(f"Distance: {distance:.4f}, Time: {time:.4f}")
            print("✅ Success: Got tuple result")
            return True
        else:
            print(f"❌ Unexpected result type: {type(fitness)}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_direct_fitness()
    if success:
        print("\n🎉 Direct fitness calculation working!")
    else:
        print("\n💥 Direct fitness calculation failed!")