#!/usr/bin/env python3
"""
Simple debug script to test basic typer functionality
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.config.config import Config
from src.core.simplified_typer import SimplifiedTyper
from src.core.keyboard import Serial
from src.core.distance_calculator import DistanceCalculator
from src.core.layout import Layout

def test_typer_basic():
    """Test basic typer functionality"""
    
    print("=== Testing Basic Typer Functionality ===")
    
    # Load minimal data
    with open('src/data/keyboards/ansi_60_percent.json', 'r') as f:
        keyboard = Serial.parse(f.read())
    
    distance = DistanceCalculator('src/data/keyboards/ansi_60_percent.json', keyboard)
    layout = Layout(keyboard)
    
    # Create simplified typer
    typer = SimplifiedTyper(keyboard, distance, layout, None, 'simple_wikipedia', debug=True)
    
    print("Typer created successfully")
    print(f"Number of fingers: {len(typer.finger)}")
    
    # Test character typing
    test_chars = ['a', 'b', 'c', '1', ' ']
    
    for char in test_chars:
        print(f"\nTesting character: '{char}'")
        try:
            can_type = typer.is_character_typed(char)
            print(f"Can type '{char}': {can_type}")
            
            if can_type:
                # Reset position
                typer.reset_finger_position()
                
                # Type the character
                distance, time = typer.process_parallel_typing(char)
                print(f"Distance: {distance}, Time: {time}")
                
        except Exception as e:
            print(f"Error with '{char}': {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_typer_basic()