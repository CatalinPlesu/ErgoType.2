#!/usr/bin/env python3

import sys
sys.path.append('.')

from src.core.layout import Layout
from src.core.keyboard import Serial
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA

def test_remap_detailed():
    """Test layout remapping with detailed output"""
    print("=== Detailed Layout Remapping Test ===")
    
    # Load keyboard
    with open('src/data/keyboards/ansi_60_percent.json', 'r') as f:
        keyboard = Serial.parse(f.read())
    
    # Test QWERTY to Dvorak remapping
    layout = Layout(keyboard, debug=False)
    
    print("Testing QWERTY -> Dvorak remapping...")
    
    # Get QWERTY and Dvorak layouts
    qwerty_layout = LAYOUT_DATA["qwerty"]
    dvorak_layout = LAYOUT_DATA["dvorak"]
    
    print(f"QWERTY layout (first 10): {qwerty_layout[:10]}")
    print(f"Dvorak layout (first 10): {dvorak_layout[:10]}")
    
    # Show the differences
    print("\nDifferences in first 20 positions:")
    for i in range(min(20, len(qwerty_layout), len(dvorak_layout))):
        if qwerty_layout[i] != dvorak_layout[i]:
            print(f"  Position {i}: QWERTY='{qwerty_layout[i]}' -> Dvorak='{dvorak_layout[i]}'")
    
    # Apply remapping
    print(f"\nApplying remapping...")
    layout.remap(qwerty_layout, dvorak_layout)
    
    # Check specific keys that should have changed
    test_keys = [15, 16, 17, 18]  # Keys that should change from q,w,e,r to different chars
    
    print(f"\nChecking specific key changes:")
    for key_id in test_keys:
        # Find the character for this key in the mapper
        found = False
        for (k_id, layer), key_obj in layout.mapper.data.items():
            if k_id == key_id and key_obj.key_type.name == 'CHAR':
                print(f"  Key {key_id}: '{key_obj.value[0]}' (layer {layer})")
                found = True
                break
        if not found:
            print(f"  Key {key_id}: Not found in mapper")
    
    # Check if any remapping actually occurred by comparing before/after
    print(f"\nChecking if remapping occurred...")
    
    # Create a fresh layout for comparison
    layout_fresh = Layout(keyboard, debug=False)
    
    changes_found = False
    for key_id in range(20):  # Check first 20 keys
        # Get character from remapped layout
        remapped_char = None
        for (k_id, layer), key_obj in layout.mapper.data.items():
            if k_id == key_id and key_obj.key_type.name == 'CHAR':
                remapped_char = key_obj.value[0]
                break
        
        # Get character from fresh layout
        fresh_char = None
        for (k_id, layer), key_obj in layout_fresh.mapper.data.items():
            if k_id == key_id and key_obj.key_type.name == 'CHAR':
                fresh_char = key_obj.value[0]
                break
        
        if remapped_char and fresh_char and remapped_char != fresh_char:
            print(f"  Key {key_id}: Changed from '{fresh_char}' to '{remapped_char}'")
            changes_found = True
    
    if not changes_found:
        print("  No changes detected - remapping may not be working")
        return False
    else:
        print("  Changes detected - remapping is working")
        return True

if __name__ == "__main__":
    success = test_remap_detailed()
    if success:
        print(f"\n✅ Layout remapping is working!")
    else:
        print(f"\n❌ Layout remapping issue detected!")