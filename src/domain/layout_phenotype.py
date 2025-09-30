"""
Multi-layer keyboard layout system inspired by QMK firmware.
Supports arbitrary number of layers with momentary switching (MO keys).
"""

from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import string


class VirtualKey:
    """
    Represents a virtual key position that can have different characters across layers.
    This abstracts away from physical keyboard positions.
    """
    
    def __init__(self, key_id: str):
        self.key_id = key_id
        # layers[layer_index] = (unshifted_char, shifted_char)
        self.layers: Dict[int, Tuple[str, str]] = {}
    
    def set_layer_mapping(self, layer: int, unshifted: str, shifted: Optional[str] = None):
        """Set character mapping for a specific layer."""
        if shifted is None:
            shifted = unshifted  # No shift variant
        self.layers[layer] = (unshifted, shifted)
    
    def get_char(self, layer: int, shifted: bool = False) -> Optional[str]:
        """Get character for a specific layer and shift state."""
        if layer not in self.layers:
            return None
        return self.layers[layer][1 if shifted else 0]
    
    def remove_layer(self, layer: int):
        """Remove a layer mapping."""
        if layer in self.layers and layer > 1:  # Protect base (0) and altgr (1)
            del self.layers[layer]


class LayoutPhenotype:
    """
    Multi-layer keyboard layout with QMK-style layer switching.
    
    Layer 0: Base layer (standard typing)
    Layer 1: AltGr layer (accessed via AltGr key, typically shift equivalent)
    Layer 2+: Custom layers (accessed via MO2, MO3, etc.)
    """
    
    # Standard base layer mappings (QWERTY-like defaults)
    DEFAULT_BASE_LAYER = {
        'letters': list(zip(string.ascii_lowercase, string.ascii_uppercase)),
        'numbers': list(zip('1234567890', '!@#$%^&*()')),
        'symbols': list(zip('[]=,./\\;-\'`', '{}+<>?|:_"~'))
    }
    
    # Special keys that don't produce characters but are needed for layer switching
    SPECIAL_KEYS = {
        'Space': ' ',
        'Tab': '\t',
        'Enter': '\n',
        'Shift': '',  # Modifier
        'AltGr': '',  # Layer 1 momentary switch
    }
    
    def __init__(self):
        """Initialize with base and altgr layers."""
        self.virtual_keys: Dict[str, VirtualKey] = {}
        self.layers: Dict[int, str] = {
            0: 'base',
            1: 'altgr'
        }
        self.layer_count = 2
        
        # Reverse lookup: character -> (layer, key_id, shifted)
        self.char_to_key_map: Dict[str, List[Tuple[int, str, bool]]] = defaultdict(list)
        
        # Initialize with default QWERTY layout
        self._initialize_default_layout()
    
    def _initialize_default_layout(self):
        """Set up default base and altgr layers."""
        # Create virtual keys for letters
        for lower, upper in self.DEFAULT_BASE_LAYER['letters']:
            key_id = lower
            vkey = VirtualKey(key_id)
            vkey.set_layer_mapping(0, lower, upper)
            self.virtual_keys[key_id] = vkey
            self._update_char_map(lower, 0, key_id, False)
            self._update_char_map(upper, 0, key_id, True)
        
        # Create virtual keys for numbers
        for num, shifted in self.DEFAULT_BASE_LAYER['numbers']:
            key_id = num
            vkey = VirtualKey(key_id)
            vkey.set_layer_mapping(0, num, shifted)
            self.virtual_keys[key_id] = vkey
            self._update_char_map(num, 0, key_id, False)
            self._update_char_map(shifted, 0, key_id, True)
        
        # Create virtual keys for symbols
        for base, shifted in self.DEFAULT_BASE_LAYER['symbols']:
            key_id = base
            vkey = VirtualKey(key_id)
            vkey.set_layer_mapping(0, base, shifted)
            self.virtual_keys[key_id] = vkey
            self._update_char_map(base, 0, key_id, False)
            self._update_char_map(shifted, 0, key_id, True)
        
        # Add special keys
        for key_name, char in self.SPECIAL_KEYS.items():
            if char:  # Only create virtual keys for keys that produce characters
                vkey = VirtualKey(key_name)
                vkey.set_layer_mapping(0, char, char)
                self.virtual_keys[key_name] = vkey
                self._update_char_map(char, 0, key_name, False)
    
    def _update_char_map(self, char: str, layer: int, key_id: str, shifted: bool):
        """Update the character to key mapping."""
        # Remove old mappings for this key_id on this layer
        self.char_to_key_map[char] = [
            (l, k, s) for l, k, s in self.char_to_key_map[char]
            if not (l == layer and k == key_id)
        ]
        # Add new mapping
        self.char_to_key_map[char].append((layer, key_id, shifted))
    
    def add_layer(self, layer_name: str) -> int:
        """
        Add a new layer and return its index.
        New layers get MO{index} momentary switches.
        """
        layer_index = self.layer_count
        self.layers[layer_index] = layer_name
        self.layer_count += 1
        return layer_index
    
    def remove_layer(self, layer_index: int) -> bool:
        """
        Remove a layer. Cannot remove base (0) or altgr (1).
        Returns True if successful.
        """
        if layer_index <= 1:
            return False
        
        if layer_index not in self.layers:
            return False
        
        # Remove layer from all virtual keys
        for vkey in self.virtual_keys.values():
            vkey.remove_layer(layer_index)
        
        # Remove from layers dict
        del self.layers[layer_index]
        
        # Clean up char_to_key_map
        for char in list(self.char_to_key_map.keys()):
            self.char_to_key_map[char] = [
                (l, k, s) for l, k, s in self.char_to_key_map[char]
                if l != layer_index
            ]
            if not self.char_to_key_map[char]:
                del self.char_to_key_map[char]
        
        return True
    
    def set_key_on_layer(self, key_id: str, layer: int, 
                         unshifted: str, shifted: Optional[str] = None):
        """
        Map a character to a virtual key on a specific layer.
        Creates the virtual key if it doesn't exist.
        """
        if key_id not in self.virtual_keys:
            self.virtual_keys[key_id] = VirtualKey(key_id)
        
        vkey = self.virtual_keys[key_id]
        vkey.set_layer_mapping(layer, unshifted, shifted)
        
        # Update reverse lookup
        self._update_char_map(unshifted, layer, key_id, False)
        if shifted and shifted != unshifted:
            self._update_char_map(shifted, layer, key_id, True)
    
    def get_key_sequence(self, char: str) -> Optional[List[str]]:
        """
        Translate a character to the key sequence needed to type it.
        
        Returns:
            List of keys to press in order:
            - base layer: ['key']
            - shifted: ['Shift', 'key']
            - layer N: ['MO{N}', 'key']
            - layer N shifted: ['MO{N}', 'Shift', 'key']
            
        Returns None if character is not mapped.
        """
        if char not in self.char_to_key_map:
            return None
        
        # Get the first mapping (prioritize lower layers)
        mappings = sorted(self.char_to_key_map[char], key=lambda x: x[0])
        if not mappings:
            return None
        
        layer, key_id, shifted = mappings[0]
        
        sequence = []
        
        # Add layer switch if not base layer
        if layer == 1:
            sequence.append('AltGr')
        elif layer > 1:
            sequence.append(f'MO{layer}')
        
        # Add shift if needed
        if shifted:
            sequence.append('Shift')
        
        # Add the actual key
        sequence.append(key_id)
        
        return sequence
    
    def get_all_chars_on_layer(self, layer: int) -> Dict[str, Tuple[str, Optional[str]]]:
        """
        Get all characters available on a specific layer.
        Returns dict: key_id -> (unshifted_char, shifted_char)
        """
        result = {}
        for key_id, vkey in self.virtual_keys.items():
            if layer in vkey.layers:
                result[key_id] = vkey.layers[layer]
        return result
    
    def remap_key(self, from_key_id: str, to_key_id: str, layer: int = 0):
        """
        Swap the mappings of two virtual keys on a specific layer.
        Useful for genetic algorithm optimization.
        """
        if from_key_id not in self.virtual_keys or to_key_id not in self.virtual_keys:
            return False
        
        from_vkey = self.virtual_keys[from_key_id]
        to_vkey = self.virtual_keys[to_key_id]
        
        if layer not in from_vkey.layers or layer not in to_vkey.layers:
            return False
        
        # Swap the layer mappings
        from_mapping = from_vkey.layers[layer]
        to_mapping = to_vkey.layers[layer]
        
        from_vkey.layers[layer] = to_mapping
        to_vkey.layers[layer] = from_mapping
        
        # Rebuild char_to_key_map for this layer
        self._rebuild_char_map_for_layer(layer)
        
        return True
    
    def _rebuild_char_map_for_layer(self, layer: int):
        """Rebuild the character map for a specific layer."""
        # Remove all mappings for this layer
        for char in list(self.char_to_key_map.keys()):
            self.char_to_key_map[char] = [
                (l, k, s) for l, k, s in self.char_to_key_map[char]
                if l != layer
            ]
        
        # Rebuild mappings for this layer
        for key_id, vkey in self.virtual_keys.items():
            if layer in vkey.layers:
                unshifted, shifted = vkey.layers[layer]
                self._update_char_map(unshifted, layer, key_id, False)
                if shifted != unshifted:
                    self._update_char_map(shifted, layer, key_id, True)
    
    def get_layer_info(self) -> Dict[int, str]:
        """Get information about all layers."""
        return self.layers.copy()
    
    def get_virtual_key_count(self) -> int:
        """Get the number of virtual keys."""
        return len(self.virtual_keys)
    
    def clone(self) -> 'LayoutPhenotype':
        """Create a deep copy of this layout for genetic algorithm operations."""
        new_layout = LayoutPhenotype()
        new_layout.layers = self.layers.copy()
        new_layout.layer_count = self.layer_count
        
        # Deep copy virtual keys
        for key_id, vkey in self.virtual_keys.items():
            new_vkey = VirtualKey(key_id)
            new_vkey.layers = vkey.layers.copy()
            new_layout.virtual_keys[key_id] = new_vkey
        
        # Rebuild char map
        for layer in self.layers.keys():
            new_layout._rebuild_char_map_for_layer(layer)
        
        return new_layout
    
    def apply_language_layout(self, language_config: dict):
        """
        Apply a language-specific layout configuration.
        This remaps base layer keys and sets up AltGr layer with displaced characters.
        
        Args:
            language_config: Dictionary with layout configuration containing:
                - 'base_remaps': {key_id: (unshifted, shifted)}
                - 'altgr_remaps': {key_id: (unshifted, shifted)}
                - 'altgr_recovery': {key_id: (unshifted, shifted)}
        """
        # Apply base layer remappings
        for base_key, new_chars in language_config.get('base_remaps', {}).items():
            unshifted, shifted = new_chars
            if base_key in self.virtual_keys:
                # Store old mappings for AltGr recovery if needed
                old_mapping = self.virtual_keys[base_key].layers.get(0)
                
                # Set new base layer mapping
                self.set_key_on_layer(base_key, 0, unshifted, shifted)
                
                # If there's an AltGr recovery mapping, apply it
                if base_key in language_config.get('altgr_recovery', {}):
                    altgr_chars = language_config['altgr_recovery'][base_key]
                    self.set_key_on_layer(base_key, 1, altgr_chars[0], altgr_chars[1])
                elif old_mapping and base_key not in language_config.get('altgr_remaps', {}):
                    # Auto-recover: put old chars on AltGr if not explicitly set
                    self.set_key_on_layer(base_key, 1, old_mapping[0], old_mapping[1])
        
        # Apply direct AltGr layer remappings (independent of base changes)
        for base_key, altgr_chars in language_config.get('altgr_remaps', {}).items():
            unshifted, shifted = altgr_chars
            self.set_key_on_layer(base_key, 1, unshifted, shifted)
    
    def __repr__(self):
        return f"LayoutPhenotype(layers={len(self.layers)}, keys={len(self.virtual_keys)})"

    def debug_print_layout(self, show_all_layers: bool = True, show_mappings: bool = True, show_char_lookup: bool = False):
        """
        Debug function to print the complete state of the layout in a readable format.
        
        Args:
            show_all_layers: Whether to show character mappings for all layers
            show_mappings: Whether to show the key->char mappings
            show_char_lookup: Whether to show the reverse lookup (char->key) mappings
        """
        print("=" * 60)
        print("LAYOUT DEBUG STATE")
        print("=" * 60)
        
        # Basic info
        print(f"Total layers: {len(self.layers)}")
        print(f"Total virtual keys: {len(self.virtual_keys)}")
        print(f"Layer names: {dict(self.layers)}")
        print()
        
        # Layer details
        print("LAYER DETAILS:")
        for layer_idx in sorted(self.layers.keys()):
            print(f"  Layer {layer_idx} ('{self.layers[layer_idx]}'): {len([k for k in self.virtual_keys.values() if layer_idx in k.layers])} keys mapped")
        print()
        
        if show_mappings:
            print("KEY MAPPINGS BY LAYER:")
            for layer_idx in sorted(self.layers.keys()):
                print(f"\n  --- Layer {layer_idx} ('{self.layers[layer_idx]}') ---")
                layer_keys = {k: v for k, v in self.virtual_keys.items() if layer_idx in v.layers}
                if not layer_keys:
                    print("    No keys mapped")
                    continue
                
                for key_id in sorted(layer_keys.keys()):
                    vkey = layer_keys[key_id]
                    unshifted, shifted = vkey.layers[layer_idx]
                    if shifted == unshifted:
                        print(f"    {key_id:10} -> '{unshifted}'")
                    else:
                        print(f"    {key_id:10} -> '{unshifted}' / '{shifted}' (unshifted/shifted)")
            print()
        
        if show_char_lookup:
            print("CHARACTER LOOKUP MAPPINGS:")
            for char in sorted(self.char_to_key_map.keys()):
                mappings = self.char_to_key_map[char]
                mapping_strs = []
                for layer, key_id, shifted in mappings:
                    layer_name = self.layers[layer]
                    shift_str = " (shifted)" if shifted else ""
                    mapping_strs.append(f"L{layer}({layer_name}):{key_id}{shift_str}")
                print(f"  '{char}': {', '.join(mapping_strs)}")
            print()
        
        # Special statistics
        print("LAYER STATISTICS:")
        for layer_idx in sorted(self.layers.keys()):
            layer_keys = [k for k, v in self.virtual_keys.items() if layer_idx in v.layers]
            unique_chars = set()
            for key_id in layer_keys:
                vkey = self.virtual_keys[key_id]
                unshifted, shifted = vkey.layers[layer_idx]
                unique_chars.add(unshifted)
                if shifted != unshifted:
                    unique_chars.add(shifted)
            
            print(f"  Layer {layer_idx}: {len(layer_keys)} keys, {len(unique_chars)} unique characters")
        print()
        
        print("VIRTUAL KEY SUMMARY:")
        for key_id, vkey in list(self.virtual_keys.items()):  # Show first 10
            layers_str = ", ".join([f"L{l}" for l in sorted(vkey.layers.keys())])
            print(f"  {key_id:10} -> layers: [{layers_str}]")
        print("=" * 60)
