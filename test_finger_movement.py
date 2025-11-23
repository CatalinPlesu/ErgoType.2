#!/usr/bin/env python3

import sys
sys.path.append('.')

from src.config.config import Config
from src.core.simplified_typer import SimplifiedTyper
from src.core.layout import Layout
from src.core.serial_io import Serial

def test_finger_movement():
    """Test basic finger movement simulation"""
    print("=== Testing Finger Movement ===")
    
    # Load keyboard
    with open('src/data/keyboards/ansi_60_percent.json', 'r') as f:
        keyboard = Serial.parse(f.read())
    
    # Create layout and typer
    layout = Layout(keyboard, debug=True)
    distance = None  # Will be None for simplified typer
    
    # Create simplified typer
    typer = SimplifiedTyper(keyboard, distance, layout, None, 'test', debug=True)
    
    # Test typing some characters
    test_chars = ['a', 's', 'd', 'f', 'j', 'k', 'l', ';']
    
    print("Testing finger movement for characters:")
    for char in test_chars:
        print(f"\nTyping character: '{char}'")
        
        # Reset to home position
        typer.reset_finger_position()
        
        # Type the character
        distance, time = typer.type_character_sequential(char)
        print(f"  Distance: {distance:.4f}, Time: {time:.4f}")
        
        # Print finger positions
        for finger_name, finger_data in typer.finger.items():
            if finger_data['current_key'] is not None:
                key_obj = keyboard.keys[finger_data['current_key']]
                print(f"  {finger_name}: key {finger_data['current_key']} at ({key_obj.x:.1f}, {key_obj.y:.1f})")

if __name__ == "__main__":
    test_finger_movement()