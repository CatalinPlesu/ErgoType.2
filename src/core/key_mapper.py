from typing import Dict, Set, Optional
from src.core.keyboard import Keyboard


class KeyMapper:
    """Handles mapping between virtual keys and physical keys."""
    
    def __init__(self, physical_keyboard: Keyboard, layout_phenotype):
        """
        Initialize the key mapper.
        
        Args:
            physical_keyboard: The physical keyboard model
            layout_phenotype: The layout phenotype containing virtual keys
        """
        self.physical_keyboard = physical_keyboard
        self.layout_phenotype = layout_phenotype
        self.virtual_to_physical = {}
        self._build_key_mapping()
    
    def _build_key_mapping(self):
        """Build mapping between virtual keys and physical keys."""
        # Create mapping from virtual key IDs to physical keys
        self.virtual_to_physical = {}
        
        # First, create a mapping from physical key labels to physical keys
        physical_key_map = {}
        for physical_key in self.physical_keyboard.keys:
            labels = physical_key.get_labels()
            for label in labels:
                if label is None:
                    continue
                # Add both the label and its lowercase version
                physical_key_map[label] = physical_key
                if label.lower() != label:
                    physical_key_map[label.lower()] = physical_key
        
        # Now map virtual keys to physical keys
        for virtual_key_id in self.layout_phenotype.virtual_keys.keys():
            # Try to find a physical key that matches this virtual key ID
            if virtual_key_id in physical_key_map:
                self.virtual_to_physical[virtual_key_id] = physical_key_map[virtual_key_id]
            elif virtual_key_id.lower() in physical_key_map:
                self.virtual_to_physical[virtual_key_id] = physical_key_map[virtual_key_id.lower()]
            elif virtual_key_id.upper() in physical_key_map:
                self.virtual_to_physical[virtual_key_id] = physical_key_map[virtual_key_id.upper()]
            else:
                print(f"Virtual key '{virtual_key_id}' not found in physical keyboard")
        
        # Also add special keys that might not be in the virtual layout but exist physically
        special_keys = ['Shift', 'AltGr', 'Space', 'Tab', 'Enter', 'Backspace', 'Caps Lock', 'Ctrl', 'Win', 'Alt', 'Menu']
        for special_key in special_keys:
            if special_key in physical_key_map and special_key not in self.virtual_to_physical:
                self.virtual_to_physical[special_key] = physical_key_map[special_key]
    
    def get_physical_key(self, virtual_key_id: str) -> Optional:
        """
        Get the physical key for a given virtual key ID.
        
        Args:
            virtual_key_id: The virtual key identifier
            
        Returns:
            The corresponding physical key or None if not found
        """
        return self.virtual_to_physical.get(virtual_key_id)
    
    def get_all_mappings(self) -> Dict[str, object]:
        """
        Get all virtual to physical key mappings.
        
        Returns:
            Dictionary mapping virtual key IDs to physical keys
        """
        return self.virtual_to_physical.copy()
    
    def get_unmapped_virtual_keys(self) -> Set[str]:
        """
        Get virtual keys that don't have corresponding physical keys.
        
        Returns:
            Set of unmapped virtual key IDs
        """
        mapped_keys = set(self.virtual_to_physical.keys())
        all_virtual_keys = set(self.layout_phenotype.virtual_keys.keys())
        return all_virtual_keys - mapped_keys
    
    def get_physical_key_for_char(self, char: str) -> Optional:
        """
        Get physical key for a character by first getting the virtual key sequence
        and then mapping to physical key.
        
        Args:
            char: The character to find the key for
            
        Returns:
            The corresponding physical key or None if not found
        """
        key_sequence = self.layout_phenotype.get_key_sequence(char)
        if key_sequence and len(key_sequence) > 0:
            virtual_key_id = key_sequence[0]  # Get the first key in the sequence
            return self.get_physical_key(virtual_key_id)
        return None
