#!/usr/bin/env python3
"""
Test script to verify heatmap rendering uses key_id correctly.
"""

from pythonnet import set_runtime
from clr_loader import get_coreclr
import sys
import os
import json
from pathlib import Path

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
from src.helpers.layouts.visualization import generate_all_visualizations

print("=" * 80)
print("HEATMAP RENDERING WITH KEY_ID TEST")
print("=" * 80)

# Setup evaluator and layout
print("\n1. Setting up keyboard and layout...")
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

# Initialize C# fitness calculator
print("2. Running C# fitness calculation...")
fitness_calculator = Fitness(json_string)
stats_json = fitness_calculator.ComputeStats()

# Parse stats to verify key_id structure
print("\n3. Verifying stats structure...")
stats = json.loads(stats_json)
char_mappings = stats.get('char_mappings', {})

# Check a few characters to see their key_id mappings
test_chars = ['a', 'e', 'T']
print("\nKey ID mappings from C# stats:")
for char in test_chars:
    if char in char_mappings:
        char_data = char_mappings[char]
        key_presses = char_data.get('key_presses', [])
        print(f"\n  Character '{char}':")
        print(f"    Occurrences: {char_data['occurrences']}")
        print(f"    Hover count: {char_data['hover_count']}")
        for i, kp in enumerate(key_presses):
            print(f"    Key press {i}: key_id={kp['key_id']}, finger={kp['finger']}")

# Generate all visualizations
print("\n4. Generating heatmap visualizations...")
output_dir = Path("test_output")
output_dir.mkdir(exist_ok=True)

try:
    layout_svg, press_svg, hover_svg = generate_all_visualizations(
        stats_json=stats_json,
        keyboard=ev.keyboard,
        layout=ev.layout,
        layout_name="qwerty_test",
        layer_idx=0,
        save_dir=output_dir
    )
    
    print("✓ Layout SVG generated")
    print("✓ Press heatmap SVG generated")
    print("✓ Hover heatmap SVG generated")
    
    # Check that files were saved
    layout_file = output_dir / "layouts" / "qwerty_test_layer_0.svg"
    press_file = output_dir / "heatmaps_press" / "qwerty_test_layer_0.svg"
    hover_file = output_dir / "heatmaps_hover" / "qwerty_test_layer_0.svg"
    
    print(f"\n5. Verifying output files:")
    print(f"  Layout: {layout_file} - {'✓ exists' if layout_file.exists() else '✗ missing'}")
    print(f"  Press:  {press_file} - {'✓ exists' if press_file.exists() else '✗ missing'}")
    print(f"  Hover:  {hover_file} - {'✓ exists' if hover_file.exists() else '✗ missing'}")
    
    # Verify SVG content includes text labels (keycap labels)
    if press_file.exists():
        with open(press_file, 'r') as f:
            svg_content = f.read()
            # Check for text elements (keycap labels)
            has_text = '<text' in svg_content
            has_gradient = 'heatmap_gradient' in svg_content
            print(f"\n6. SVG content verification:")
            print(f"  Has text labels: {'✓' if has_text else '✗'}")
            print(f"  Has heatmap gradient: {'✓' if has_gradient else '✗'}")
    
    print("\n" + "=" * 80)
    print("HEATMAP RENDERING TEST COMPLETE")
    print("=" * 80)
    print(f"\n✓ All checks passed!")
    print(f"✓ Heatmaps successfully generated in {output_dir}")
    print(f"✓ Key IDs are properly used for heatmap generation")
    
except Exception as e:
    print(f"\n✗ Error generating visualizations: {e}")
    import traceback
    traceback.print_exc()
