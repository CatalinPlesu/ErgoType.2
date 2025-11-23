#!/usr/bin/env python3
"""
Simple test to debug finger handling
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.core.evaluator import Evaluator
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
from src.config.config import Config

def debug_finger_handling():
    """Debug finger handling in simplified typer"""
    
    # Configure for simplified evaluation
    Config.fitness.use_simplified_fitness = True
    
    # Initialize evaluator
    evaluator = Evaluator(debug=False)
    evaluator.load_keyoard('src/data/keyboards/ansi_60_percent.json')
    evaluator.load_distance()
    evaluator.load_layout()
    evaluator.load_dataset(dataset_name='simple_wikipedia')
    evaluator.load_typer()
    
    # Apply a simple layout
    layout_genotype = LAYOUT_DATA['qwerty']
    evaluator.layout.remap(LAYOUT_DATA["qwerty"], layout_genotype)
    
    # Test getting finger for a key
    simple_typer = evaluator.typer
    
    # Test with a simple character
    try:
        key_id, layer, qmk_key = simple_typer.layout.find_key_for_char('a')
        print(f"Key ID for 'a': {key_id}")
        print(f"Layer: {layer}")
        print(f"QMK key: {qmk_key}")
        
        finger = simple_typer.get_finger_for_key(key_id)
        print(f"Finger type: {type(finger)}")
        print(f"Finger value: {finger}")
        
        if hasattr(finger, 'value'):
            print(f"Finger enum value: {finger.value}")
            print(f"Finger enum name: {finger.name}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_finger_handling()