import os
import pickle
import time
import json
from src.domain.evaluation.layout_evaluator import KeyboardPhenotype
from src.domain.keyboard import Serial
from src.domain.hand_finger_enum import *
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
import src.data.languages.romanian_standard as ro_std

def test_layout_evaluation_basic():
    """Test basic layout evaluation functionality"""
    # Load keyboard data
    with open('src/data/keyboards/ansi_60_percent.json', 'r') as f:
        keyboard = Serial.parse(f.read())
    
    # Create layout evaluator with default pipeline
    layout_evaluator = KeyboardPhenotype(keyboard, {})
    
    # Test remap functionality
    layout_evaluator.select_remap_keys(LAYOUT_DATA['qwerty'])
    layout_evaluator.remap_to_keys(LAYOUT_DATA['asset'])
    
    print("✓ Basic layout evaluation setup successful")
    return True

def test_layout_evaluation_with_language():
    """Test layout evaluation with Romanian language layout"""
    # Load keyboard data
    with open('src/data/keyboards/ansi_60_percent.json', 'r') as f:
        keyboard = Serial.parse(f.read())
    
    # Get Romanian layout
    ro_remap = ro_std.get_layout()
    
    # Create layout evaluator with Romanian layout
    layout_evaluator = KeyboardPhenotype(keyboard, ro_remap)
    
    print("✓ Layout evaluation with Romanian language successful")
    return True

def test_layout_evaluation_fitness():
    """Test fitness calculation with frequency data"""
    # Load keyboard data
    with open('src/data/keyboards/ansi_60_percent.json', 'r') as f:
        keyboard = Serial.parse(f.read())
    
    # Create layout evaluator
    layout_evaluator = KeyboardPhenotype(keyboard, {})
    
    # Load frequency data
    with open('src/data/text/processed/frequency_analysis.pkl', 'rb') as f:
        frequency_data = pickle.load(f)
    
    # Time the fitness function
    print("Timing fitness function with frequency data...")
    start_time = time.time()
    fitness_score = layout_evaluator.fitness(frequency_data['simple_wikipedia'])
    end_time = time.time()
    fitness_freq_time = end_time - start_time
    
    print(f"✓ Fitness function completed in {fitness_freq_time:.4f} seconds")
    print(f"✓ Fitness score: {fitness_score}")
    
    # Test cost inspection
    costs = layout_evaluator.inspect_costs()
    assert 'total' in costs
    assert 'by_layer' in costs
    assert 'by_key' in costs
    
    print("✓ Cost inspection successful")
    return True

def test_layout_evaluation_different_keyboards():
    """Test layout evaluation with different keyboard types"""
    keyboards_to_test = [
        'src/data/keyboards/ansi_60_percent.json',
        'src/data/keyboards/dactyl_manuform_6x6_4.json',
        'src/data/keyboards/ferris_sweep.json'
    ]
    
    for keyboard_file in keyboards_to_test:
        if os.path.exists(keyboard_file):
            print(f"Testing {keyboard_file}...")
            with open(keyboard_file, 'r') as f:
                keyboard = Serial.parse(f.read())
            
            layout_evaluator = KeyboardPhenotype(keyboard, {})
            print(f"✓ {keyboard_file} setup successful")
        else:
            print(f"⚠ {keyboard_file} not found, skipping")
    
    return True

def test_layout_evaluation_keyboard_genotypes():
    """Test layout evaluation with different keyboard genotypes"""
    # Load keyboard data
    with open('src/data/keyboards/ansi_60_percent.json', 'r') as f:
        keyboard = Serial.parse(f.read())
    
    # Test different keyboard genotypes
    for layout_name, layout_keys in LAYOUT_DATA.items():
        print(f"Testing {layout_name} layout...")
        
        layout_evaluator = KeyboardPhenotype(keyboard, {})
        layout_evaluator.select_remap_keys(LAYOUT_DATA['qwerty'])  # Start with qwerty
        layout_evaluator.remap_to_keys(layout_keys)
        
        print(f"✓ {layout_name} layout remapping successful")

if __name__ == "__main__":
    print("Running layout evaluation tests...\n")
    
    try:
        test_layout_evaluation_basic()
        print()
        
        test_layout_evaluation_with_language()
        print()
        
        test_layout_evaluation_fitness()
        print()
        
        test_layout_evaluation_different_keyboards()
        print()
        
        test_layout_evaluation_keyboard_genotypes()
        print()
        
        print("✅ All layout evaluation tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        raise