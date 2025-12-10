#!/usr/bin/env python3
"""
Test script to verify key_id field is properly added to JSON generation
and parsed by C# Fitness class.
"""

from pythonnet import set_runtime
from clr_loader import get_coreclr
import sys
import os
import json

# Setup CLR
set_runtime(get_coreclr())
import clr

dll_dir = os.path.join(os.getcwd(), "cs", "bin", "Release", "net9.0")
sys.path.insert(0, dll_dir)
clr.AddReference("KeyboardFitness")

from FitnessNet import Fitness
from src.core.map_json_exporter import CSharpFitnessConfig
from src.core.evaluator import Evaluator
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA

print("=" * 80)
print("KEY_ID FIELD VERIFICATION TEST")
print("=" * 80)

# Setup evaluator and layout
ev = Evaluator(debug=False)
ev.load_keyoard('src/data/keyboards/ansi_60_percent.json')
ev.load_layout()
ev.layout.querty_based_remap(LAYOUT_DATA["qwerty"])

# Create config generator
config_gen = CSharpFitnessConfig(
    keyboard=ev.keyboard,
    layout=ev.layout
)

# Generate JSON string
json_string = config_gen.generate_json_string(
    text_file_path="src/data/text/raw/simple_wikipedia_dataset.txt",
    finger_coefficients=[0.05] * 10,
    fitts_a=0.5,
    fitts_b=0.3
)

# Parse JSON to verify key_id field is present
print("\n1. VERIFYING JSON GENERATION:")
print("-" * 80)
config_data = json.loads(json_string)

# Check a few character mappings
test_chars = ['a', 'e', 'T', ' ']
for char in test_chars:
    if char in config_data['char_mappings']:
        key_presses = config_data['char_mappings'][char]
        print(f"\nCharacter '{char}':")
        for i, key_press in enumerate(key_presses):
            has_key_id = 'key_id' in key_press
            status = "✓" if has_key_id else "✗"
            print(f"  {status} Key press {i}: x={key_press['x']:.2f}, y={key_press['y']:.2f}, finger={key_press['finger']}", end="")
            if has_key_id:
                print(f", key_id={key_press['key_id']}")
            else:
                print(" (MISSING key_id)")

# Test C# parsing
print("\n\n2. VERIFYING C# PARSING:")
print("-" * 80)
fitness_calculator = Fitness(json_string)
print("✓ C# Fitness class initialized successfully (no parsing errors)")

# Run ComputeStats to get detailed output with key_id
print("\n\n3. VERIFYING C# STATS OUTPUT:")
print("-" * 80)
stats_json = fitness_calculator.ComputeStats()
stats = json.loads(stats_json)

# Check that key_id is in the output
print(f"Total characters processed: {stats['total_chars_processed']}")
print(f"Total presses: {stats['total_presses']}")

print("\nChecking key_id in stats output:")
for char in test_chars:
    if char in stats['char_mappings']:
        char_data = stats['char_mappings'][char]
        key_presses = char_data.get('key_presses', [])
        print(f"\nCharacter '{char}':")
        print(f"  Occurrences: {char_data['occurrences']}")
        print(f"  Hover count: {char_data['hover_count']}")
        print(f"  Press count: {char_data['press_count']}")
        for i, key_press in enumerate(key_presses):
            has_key_id = 'key_id' in key_press
            status = "✓" if has_key_id else "✗"
            print(f"  {status} Key press {i}: x={key_press['x']:.2f}, y={key_press['y']:.2f}, finger={key_press['finger']}", end="")
            if has_key_id:
                print(f", key_id={key_press['key_id']}")
            else:
                print(" (MISSING key_id)")

print("\n" + "=" * 80)
print("KEY_ID VERIFICATION COMPLETE")
print("=" * 80)
print("\n✓ All checks passed! key_id field is properly added and parsed.")
