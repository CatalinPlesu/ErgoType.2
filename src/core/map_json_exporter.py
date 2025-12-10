"""
C# Fitness Library JSON Interface

This module generates JSON configuration for a C# fitness calculation library.
It converts keyboard layout and character mappings into an efficient format 
for stateful typing simulation with Fitts's Law time grouping.

The C# library returns raw total_distance and total_time values.
Python handles normalization after calling the library multiple times.
"""

import json
from src.core.keyboard import FingerName
from src.core.mapper import KeyType

class CSharpFitnessConfig:
    """
    Generates JSON configuration string for C# fitness calculation.
    
    The C# library will:
    1. Load text file and process characters
    2. Simulate typing with stateful finger positions
    3. Calculate distances and Fitts's Law times
    4. Group simultaneous key presses (parallel typing)
    5. Return: {total_distance: float, total_time: float}
    
    Python then normalizes these values across multiple layouts.
    """
    
    # Finger name to integer mapping for C# (0-based indexing)
    FINGER_TO_INT = {
        FingerName.LEFT_PINKY: 0,
        FingerName.LEFT_RING: 1,
        FingerName.LEFT_MIDDLE: 2,
        FingerName.LEFT_INDEX: 3,
        FingerName.LEFT_THUMB: 4,
        FingerName.RIGHT_THUMB: 5,
        FingerName.RIGHT_INDEX: 6,
        FingerName.RIGHT_MIDDLE: 7,
        FingerName.RIGHT_RING: 8,
        FingerName.RIGHT_PINKY: 9
    }
    
    def __init__(self, keyboard, layout):
        """
        Initialize configuration generator.
        
        Args:
            keyboard: Keyboard object with key positions and dimensions
            layout: Layout object with character mappings (contains mapper)
        """
        self.keyboard = keyboard
        self.layout = layout
        
    def _get_finger_int(self, key_id, prefer_finger=None):
        """
        Convert key's finger to integer index.
        
        Args:
            key_id: The key ID
            prefer_finger: If provided, prefer this FingerName when key has multiple fingers
        """
        key = self.keyboard.keys[key_id]
        finger_name = key.get_finger_name()
        
        # Handle case where finger_name might be a list (e.g., for BOTH hand - spacebar)
        if isinstance(finger_name, list):
            if prefer_finger and prefer_finger in finger_name:
                finger_name = prefer_finger
            else:
                finger_name = finger_name[0]
            
        return self.FINGER_TO_INT.get(finger_name, -1)
    
    def _get_key_position(self, key_id, prefer_finger=None):
        """
        Get key center position as (x, y) with key_id.
        
        Args:
            key_id: The key ID
            prefer_finger: If provided, use this finger ID when key has multiple fingers
        """
        key = self.keyboard.keys[key_id]
        center = key.get_key_center_position()
        return {
            "x": float(center[0]),
            "y": float(center[1]),
            "finger": self._get_finger_int(key_id, prefer_finger),
            "key_id": int(key_id)
        }
    
    def _get_char_key_sequence(self, char):
        """
        Get the sequence of keys needed to type a character.
        Returns list of key positions that must be pressed simultaneously.
        """
        # Find the base key for this character
        key_id, layer, qmk_key = self.layout.find_key_for_char(char)
        
        if key_id is None:
            return None
            
        key_sequence = []
        
        # Handle shift if needed
        shift_keys = self.layout.mapper.filter_data(
            lambda kid, lid, value: value.key_type == KeyType.CONTROL and value.value == 'Shift'
        )
        
        shifted_symbols = self.layout.get_shifted_symbols()
        if char in shifted_symbols:
            # Find appropriate shift key (opposite hand)
            for shift in shift_keys:
                shift_id = shift[0][0]  # Extract key_id from ((key_id, layer), value)
                key = self.keyboard.keys[key_id]
                shift_key = self.keyboard.keys[shift_id]
                
                if key.hand != shift_key.hand:
                    key_sequence.append(self._get_key_position(shift_id))
                    break
        
        # Handle AltGr if needed (layer 1)
        if layer == 1:
            altgr_keys = self.layout.mapper.filter_data(
                lambda kid, lid, value: value.key_type == KeyType.LAYER and value.value == 'AltGr'
            )
            
            if altgr_keys:
                # Find appropriate AltGr key (prefer opposite hand)
                base_key = self.keyboard.keys[key_id]
                altgr_id = None
                
                for altgr in altgr_keys:
                    ag_id = altgr[0][0]
                    ag_key = self.keyboard.keys[ag_id]
                    
                    if base_key.hand != ag_key.hand:
                        altgr_id = ag_id
                        break
                
                # Fallback to any AltGr key
                if altgr_id is None and altgr_keys:
                    altgr_id = altgr_keys[0][0][0]
                
                if altgr_id is not None:
                    key_sequence.append(self._get_key_position(altgr_id))
        
        # Add the main character key
        key_sequence.append(self._get_key_position(key_id))
        
        return key_sequence
    
    def generate_json_string(self, 
                            text_file_path,
                            finger_coefficients=None,
                            fitts_a=0.1,
                            fitts_b=0.1):
        """
        Generate JSON string for C# library.
        
        Args:
            text_file_path: Path to text file to process
            finger_coefficients: List of 10 coefficients for press time/sync by finger
                                (default: 50ms for all fingers)
            fitts_a: Fitts's Law constant 'a' in milliseconds (default: 0)
            fitts_b: Fitts's Law constant 'b' in milliseconds (default: 150)
            
        Returns:
            JSON string ready to pass to C# library
        """
        if finger_coefficients is None:
            # Default: 50ms press time for all fingers
            finger_coefficients = [0.25] * 10
        
        # Build character mapping
        char_map = {}
        
        # Get all unique characters from layout
        all_chars = set()
        all_chars.update(self.layout.get_unshifted_symbols())
        all_chars.update(self.layout.get_shifted_symbols())
        all_chars.update(self.layout.get_altgr_symbols())
        
        # Add special characters
        for (key_id, layer), key_obj in self.layout.mapper.data.items():
            if key_obj.key_type == KeyType.SPECIAL_CHAR:
                if isinstance(key_obj.value, tuple):
                    all_chars.add(key_obj.value[0])
        
        # Generate key sequences for each character
        for char in all_chars:
            if char is None:
                continue
                
            key_sequence = self._get_char_key_sequence(char)
            if key_sequence:
                char_map[char] = key_sequence
        
        # Get homing positions for each finger (use array, not dict)
        # Ensure all 10 positions are filled, even if some fingers share keys
        homing_positions = []
        
        for finger_name in FingerName:
            homing_key = self.keyboard.get_homing_key_for_finger_name(finger_name)
            finger_int = self.FINGER_TO_INT[finger_name]
            
            if homing_key:
                pos = self._get_key_position(homing_key.id, prefer_finger=finger_name)
                # Override the finger field to ensure it matches the correct finger
                pos["finger"] = finger_int
                homing_positions.append(pos)
            else:
                # Fallback: use center of keyboard if no homing key found
                # This should rarely happen in well-defined keyboards
                homing_positions.append({
                    "x": 6.5,
                    "y": 2.5,
                    "finger": finger_int
                })
        
        # Verify we have exactly 10 positions
        assert len(homing_positions) == 10, f"Expected 10 homing positions, got {len(homing_positions)}"
        
        # Build complete configuration
        config = {
            "text_file_path": text_file_path,
            "fitts_law": {
                "a": float(fitts_a),
                "b": float(fitts_b)
            },
            "finger_coefficients": [float(c) for c in finger_coefficients],
            "homing_positions": homing_positions,
            "char_mappings": char_map
        }
        
        return json.dumps(config, ensure_ascii=False)


# Example usage
if __name__ == "__main__":
    from src.core.evaluator import Evaluator
    from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
    
    # Initialize evaluator (only need keyboard and layout)
    ev = Evaluator(debug=False)
    ev.load_keyoard('src/data/keyboards/ansi_60_percent.json')
    ev.load_layout()
    
    # Apply a layout
    ev.layout.querty_based_remap(LAYOUT_DATA["qwerty"])
    
    # Create configuration generator (no distance calculator needed!)
    config_gen = CSharpFitnessConfig(
        keyboard=ev.keyboard,
        layout=ev.layout
    )
    
    # Generate JSON string to pass to C# library
    json_string = config_gen.generate_json_string(
        text_file_path="src/data/text/raw/simple_wikipedia_dataset.txt",
        fitts_a=0.1,
        fitts_b=0.1
    )
    
    # print("JSON string ready to pass to C#:")
    
    print(json_string)

    # Example: Custom finger coefficients for different finger speeds
    custom_coefficients = [
        0.7,  # Left pinky (slower)
        0.6,  # Left ring
        0.5,  # Left middle
        0.5,  # Left index
        0.5,  # Left thumb
        0.5,  # Right thumb
        0.5,  # Right index
        0.5,  # Right middle
        0.6,  # Right ring
        0.7,  # Right pinky (slower)
    ]
    
    json_string = config_gen.generate_json_string(
        text_file_path="src/data/text/processed/sample.txt",
        finger_coefficients=custom_coefficients,
        fitts_a=0.0,
        fitts_b=150.0
    )
    
    # Now pass json_string to your C# library
    # result = csharp_lib.calculate_fitness(json_string)
    # result will be: {"total_distance": 12345.67, "total_time": 8901.23}
    
    # print("\nReady to pass to C# library!")
    # print(f"Config size: {len(json_string)} bytes")
