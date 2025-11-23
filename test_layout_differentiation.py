#!/usr/bin/env python3

import sys
sys.path.append('.')

from src.config.config import Config
Config.fitness.use_simplified_fitness = True
Config.fitness.distance_weight = 0.5
Config.fitness.time_weight = 0.5

from src.core.simplified_typer import SimplifiedTyper
from src.core.layout import Layout
from src.core.keyboard import Serial
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA

def test_layouts_with_comprehensive_text():
    """Test different layouts with comprehensive text to ensure differences"""
    print("=== Testing Layouts with Comprehensive Text ===")
    
    # Load keyboard
    with open('src/data/keyboards/ansi_60_percent.json', 'r') as f:
        keyboard = Serial.parse(f.read())
    
    # Create comprehensive test text that uses all keys
    comprehensive_text = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890!@#$%^&*()_+-=[]{}|;':\",./<>?`~ "
    # Repeat to make it longer
    comprehensive_text = comprehensive_text * 100
    
    print(f"Test text length: {len(comprehensive_text)} characters")
    print(f"Unique characters: {len(set(comprehensive_text))}")
    
    # Test different layouts
    layouts_to_test = [
        ("qwerty", LAYOUT_DATA["qwerty"]),
        ("dvorak", LAYOUT_DATA["dvorak"]),
        ("colemak", LAYOUT_DATA["colemak"]),
    ]
    
    results = {}
    
    for layout_name, layout_chromosome in layouts_to_test:
        print(f"\n--- Testing {layout_name} ---")
        
        # Create layout and apply remapping
        layout = Layout(keyboard, debug=False)
        layout.remap(LAYOUT_DATA["qwerty"], layout_chromosome)
        
        # Create simplified typer with our comprehensive text
        # We'll simulate the text processing directly
        
        # Create typer
        typer = SimplifiedTyper(keyboard, None, layout, None, 'test', debug=False)
        
        # Reset finger positions
        typer.reset_finger_position()
        
        # Process text character by character
        total_distance = 0.0
        total_time = 0.0
        char_count = 0
        
        for char in comprehensive_text:
            if not typer.is_character_typed(char):
                continue  # Skip characters not on keyboard
                
            # Use parallel typing simulation for better accuracy
            distance, time = typer.process_parallel_typing(char)
            total_distance += distance
            total_time += time
            char_count += 1
            
            # Reset position occasionally to simulate breaks (every 256 chars)
            if char_count % Config.fitness.simulation_window_size == 0:
                typer.reset_finger_position()
        
        print(f"Characters processed: {char_count}")
        print(f"Total distance: {total_distance:.4f}")
        print(f"Total time: {total_time:.4f}")
        
        results[layout_name] = (total_distance, total_time)
    
    print(f"\n=== Results Summary ===")
    for layout_name, (distance, time) in results.items():
        print(f"{layout_name}: distance={distance:.4f}, time={time:.4f}")
    
    # Check if all results are the same
    result_values = list(results.values())
    if len(set(str(v) for v in result_values)) == 1:
        print("\n❌ All layouts returned the same result - issue detected")
        return False
    else:
        print("\n✅ Layouts returned different results - working correctly")
        return True

if __name__ == "__main__":
    success = test_layouts_with_comprehensive_text()
    if success:
        print("\n🎉 Layout differentiation is working!")
    else:
        print("\n💥 Layout differentiation issue detected!")