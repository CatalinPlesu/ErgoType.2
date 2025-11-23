#!/usr/bin/env python3

import sys
sys.path.append('.')

from src.core.layout import Layout
from src.core.keyboard import Serial
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA

def test_remap_directly():
    """Test layout remapping directly without fitness calculation"""
    print("=== Testing Layout Remapping Directly ===")
    
    # Load keyboard
    with open('src/data/keyboards/ansi_60_percent.json', 'r') as f:
        keyboard = Serial.parse(f.read())
    
    # Test QWERTY to Dvorak remapping
    layout = Layout(keyboard, debug=False)  # Don't print initial layout
    
    print("Original QWERTY layout (first 10 chars):")
    # Get first 10 character keys from mapper
    char_keys = []
    for (key_id, layer), key_obj in layout.mapper.data.items():
        if key_obj.key_type.name == 'CHAR' and len(char_keys) < 10:
            char_keys.append((key_id, key_obj.value[0]))
    
    for key_id, char in char_keys[:10]:
        print(f"  Key {key_id}: '{char}'")
    
    print(f"\nRemapping to Dvorak...")
    layout.remap(LAYOUT_DATA["qwerty"], LAYOUT_DATA["dvorak"])
    
    print("After Dvorak remapping (first 10 chars):")
    char_keys_after = []
    for (key_id, layer), key_obj in layout.mapper.data.items():
        if key_obj.key_type.name == 'CHAR' and len(char_keys_after) < 10:
            char_keys_after.append((key_id, key_obj.value[0]))
    
    for key_id, char in char_keys_after[:10]:
        print(f"  Key {key_id}: '{char}'")
    
    # Check if remapping worked by comparing specific keys
    print(f"\nSpecific key changes:")
    test_keys = [15, 16, 17, 18]  # q, w, e, r in QWERTY
    for key_id in test_keys:
        original_char = None
        remapped_char = None
        
        # Find original character for this key
        for (k_id, layer), key_obj in layout.mapper.data.items():
            if k_id == key_id and key_obj.key_type.name == 'CHAR':
                if original_char is None:
                    # This should be the remapped character now
                    remapped_char = key_obj.value[0]
                    break
        
        print(f"  Key {key_id}: Should be remapped")
        if remapped_char:
            print(f"    Now shows: '{remapped_char}'")
    
    # Check if any changes occurred
    original_chars = [char for key_id, char in char_keys]
    remapped_chars = [char for key_id, char in char_keys_after]
    
    if original_chars == remapped_chars:
        print(f"\n❌ No changes detected - remapping may not be working")
        return False
    else:
        print(f"\n✅ Changes detected - remapping appears to be working")
        return True

if __name__ == "__main__":
    success = test_remap_directly()
    if success:
        print(f"\n🎉 Layout remapping is working!")
    else:
        print(f"\n💥 Layout remapping issue detected!")