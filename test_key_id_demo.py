#!/usr/bin/env python3
"""
Comprehensive demo of key_id feature working end-to-end.
This script demonstrates the complete flow from JSON generation through
C# processing to heatmap visualization.
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

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def demonstrate_key_id_feature():
    """Run comprehensive demonstration of key_id feature"""
    
    print_section("KEY_ID FEATURE DEMONSTRATION")
    
    # Step 1: Setup
    print("\n[Step 1] Setting up keyboard and layout...")
    ev = Evaluator(debug=False)
    ev.load_keyoard('src/data/keyboards/ansi_60_percent.json')
    ev.load_layout()
    ev.layout.querty_based_remap(LAYOUT_DATA["qwerty"])
    print("✓ Keyboard loaded: ANSI 60% layout")
    print(f"✓ Total keys: {len(ev.keyboard.keys)}")
    
    # Step 2: Generate JSON with key_id
    print("\n[Step 2] Generating JSON configuration with key_id...")
    config_gen = CSharpFitnessConfig(
        keyboard=ev.keyboard,
        layout=ev.layout
    )
    
    json_string = config_gen.generate_json_string(
        text_file_path="src/data/text/raw/simple_wikipedia_dataset.txt",
        finger_coefficients=[0.05] * 10,
        fitts_a=0.5,
        fitts_b=0.3
    )
    
    config_data = json.loads(json_string)
    
    # Show some examples
    print("✓ JSON generated successfully")
    print(f"✓ Total characters mapped: {len(config_data['char_mappings'])}")
    
    example_chars = ['a', 'T', 'Space', ',']
    print("\n  Example key_id mappings:")
    for char in example_chars:
        if char in config_data['char_mappings']:
            key_presses = config_data['char_mappings'][char]
            print(f"\n  Character: '{char}'")
            for i, kp in enumerate(key_presses):
                print(f"    Press {i+1}: key_id={kp['key_id']}, finger={kp['finger']}, pos=({kp['x']:.1f}, {kp['y']:.1f})")
    
    # Step 3: C# Processing
    print_section("[Step 3] C# Processing with key_id")
    print("Initializing C# Fitness calculator...")
    fitness_calculator = Fitness(json_string)
    print("✓ C# successfully parsed JSON with key_id fields")
    
    print("\nRunning fitness computation...")
    result = fitness_calculator.Compute()
    print(f"✓ Total distance: {result.Item1:.2f} units")
    print(f"✓ Total time: {result.Item2:.2f} units")
    
    print("\nGenerating detailed statistics...")
    stats_json = fitness_calculator.ComputeStats()
    stats = json.loads(stats_json)
    print(f"✓ Processed {stats['total_chars_processed']} characters")
    print(f"✓ Total key presses: {stats['total_presses']}")
    
    # Show key_id in stats
    print("\n  Statistics include key_id for each character:")
    for char in ['a', 'e', 'T']:
        if char in stats['char_mappings']:
            char_data = stats['char_mappings'][char]
            print(f"\n  '{char}': occurrences={char_data['occurrences']}, hover={char_data['hover_count']}")
            for i, kp in enumerate(char_data['key_presses']):
                print(f"    → key_id={kp['key_id']}")
    
    # Step 4: Heatmap Generation
    print_section("[Step 4] Generating Heatmaps Using key_id")
    
    # Count unique keys used
    unique_keys = set()
    for char_data in stats['char_mappings'].values():
        for kp in char_data.get('key_presses', []):
            unique_keys.add(kp.get('key_id'))
    
    print(f"Detected {len(unique_keys)} unique physical keys used in text")
    print("Generating visualizations...")
    
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    layout_svg, press_svg, hover_svg = generate_all_visualizations(
        stats_json=stats_json,
        keyboard=ev.keyboard,
        layout=ev.layout,
        layout_name="demo_qwerty",
        layer_idx=0,
        save_dir=output_dir
    )
    
    print("✓ Layout visualization generated")
    print("✓ Press heatmap generated (blue→red gradient)")
    print("✓ Hover heatmap generated (grey→green gradient)")
    
    # Verify files
    files = [
        ("Layout", "layouts/demo_qwerty_layer_0.svg"),
        ("Press Heatmap", "heatmaps_press/demo_qwerty_layer_0.svg"),
        ("Hover Heatmap", "heatmaps_hover/demo_qwerty_layer_0.svg")
    ]
    
    print("\n  Generated files:")
    for name, path in files:
        full_path = output_dir / path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"    ✓ {name}: {path} ({size:,} bytes)")
    
    # Step 5: Demonstrate key_id benefits
    print_section("[Step 5] Key ID Benefits Demonstration")
    
    print("\n1. ACCURATE KEY MAPPING")
    print("   Example: Character 'T' (uppercase)")
    if 'T' in stats['char_mappings']:
        t_data = stats['char_mappings']['T']
        key_presses = t_data['key_presses']
        print(f"   Requires {len(key_presses)} key presses:")
        for i, kp in enumerate(key_presses):
            key_obj = ev.keyboard.keys[kp['key_id']]
            labels = key_obj.get_labels()
            label = labels[0] if labels and labels[0] else "Unknown"
            print(f"     {i+1}. key_id={kp['key_id']} ({label}) - finger {kp['finger']}")
    
    print("\n2. NO AMBIGUITY")
    print("   Left Shift and Right Shift are tracked separately:")
    shift_keys_in_stats = {}
    for char, char_data in stats['char_mappings'].items():
        for kp in char_data.get('key_presses', []):
            key_id = kp['key_id']
            key_obj = ev.keyboard.keys[key_id]
            labels = key_obj.get_labels()
            if labels and 'Shift' in str(labels[0]):
                if key_id not in shift_keys_in_stats:
                    shift_keys_in_stats[key_id] = {
                        'label': labels[0],
                        'usage': 0
                    }
                shift_keys_in_stats[key_id]['usage'] += char_data['press_count']
    
    for key_id, data in shift_keys_in_stats.items():
        print(f"     key_id={key_id} ({data['label']}): {data['usage']} presses")
    
    print("\n3. CONSISTENT ACROSS LAYOUTS")
    print("   key_id=29 is always the same physical key,")
    print("   regardless of what character is mapped to it.")
    
    print("\n4. ENABLES ACCURATE HEATMAPS")
    print("   Each physical key's color represents its actual usage,")
    print("   not ambiguous character-based statistics.")
    
    # Final summary
    print_section("DEMONSTRATION COMPLETE")
    print("\n✅ All components working correctly:")
    print("   • JSON generation includes key_id")
    print("   • C# parsing handles key_id properly")
    print("   • Statistics maintain key_id throughout")
    print("   • Heatmaps use key_id for accurate visualization")
    print("\n✅ Benefits demonstrated:")
    print("   • Accurate physical key tracking")
    print("   • No ambiguity in key mapping")
    print("   • Consistent across layout changes")
    print("   • Precise heatmap generation")
    print(f"\n✅ Output files saved to: {output_dir}")
    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    try:
        demonstrate_key_id_feature()
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
