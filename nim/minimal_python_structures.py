# Minimal key structure for Nim port
import json
import math
from typing import Dict, List, Tuple, Optional

class KeyData:
    """Minimal key representation for Nim port"""
    def __init__(self, id: int, char: str, finger: int, x: float, y: float):
        self.id = id
        self.char = char
        self.finger = finger  # 0-9 representing FingerName enum
        self.x = x
        self.y = y
        
    def distance_to(self, other: 'KeyData') -> float:
        """Calculate Euclidean distance to another key"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
        
    def get_position(self) -> Tuple[float, float]:
        return (self.x, self.y)

class FingerState:
    """Track finger position and statistics"""
    def __init__(self, finger_id: int, homing_key_id: int):
        self.finger_id = finger_id
        self.homing_key_id = homing_key_id
        self.current_key_id = homing_key_id
        self.total_distance = 0.0
        self.total_time = 0.0
        self.key_count = 0

class MinimalLayout:
    """Minimal layout mapping for Nim port"""
    def __init__(self, key_map: Dict[str, KeyData]):
        self.key_map = key_map  # char -> KeyData
        self.reverse_map = {key.id: key for key in key_map.values()}  # id -> KeyData
        
    def find_key_for_char(self, char: str) -> Optional[KeyData]:
        """Find key data for a character"""
        return self.key_map.get(char.lower(), None)
        
    def get_key_by_id(self, key_id: int) -> Optional[KeyData]:
        """Get key data by ID"""
        return self.reverse_map.get(key_id, None)

class MinimalFittsCalculator:
    """Minimal Fitts law calculator"""
    def __init__(self, fitts_a: float = 0.0, fitts_b: float = 150.0, target_width: float = 19.05):
        self.fitts_a = fitts_a
        self.fitts_b = fitts_b
        self.target_width = target_width
        
    def calculate_time(self, distance: float) -> float:
        """Calculate movement time using Fitts law"""
        if distance == 0:
            return 0.0
        # Fitts's Law: MT = a + b * log2(D/W + 1)
        id_value = math.log2(distance / self.target_width + 1)
        return self.fitts_a + self.fitts_b * id_value

def load_minimal_layout_from_keyboard(keyboard_file: str) -> MinimalLayout:
    """Load minimal layout from keyboard JSON file"""
    with open(keyboard_file, 'r') as f:
        data = json.load(f)
    
    key_map = {}
    key_id = 0
    
    # ANSI 60% layout is a 2D array of rows
    for row_idx, row in enumerate(data):
        col_idx = 0
        i = 0
        while i < len(row):
            item = row[i]
            
            # Check if this is a metadata object (finger, hand, etc.)
            if isinstance(item, dict):
                finger_info = item
                # Skip to next item which should be the key label
                i += 1
                if i < len(row):
                    label = row[i]
                    
                    # Extract character from label (handle multi-line labels like "!\n1")
                    if isinstance(label, str):
                        # Get the printable character (first non-empty line)
                        lines = [line.strip() for line in label.split('\n') if line.strip()]
                        if lines:
                            char = lines[0]
                            
                            # Only map single printable characters
                            if len(char) == 1 and char.isprintable() and char.isalnum():
                                # Convert finger info to numeric
                                finger_name = finger_info.get('finger', 'UNKNOWN')
                                finger_map = {
                                    'PINKY': 0, 'RING': 1, 'MIDDLE': 2, 'INDEX': 3, 
                                    'THUMB': 4, 'UNKNOWN': 0
                                }
                                finger = finger_map.get(finger_name, 0)
                                
                                # Simple grid-based positioning
                                x = col_idx * 19.05  # Standard key spacing
                                y = row_idx * 19.05
                                
                                key_map[char.lower()] = KeyData(key_id, char.lower(), finger, x, y)
                                key_id += 1
                    
                    # Handle key width for spacing
                    width = finger_info.get('w', 1)
                    col_idx += width
            i += 1
    
    return MinimalLayout(key_map)

def load_sample_text(file_path: str, max_chars: int = 100000) -> str:
    """Load text with optional character limit"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read(max_chars)
        return text
    except FileNotFoundError:
        return ""

if __name__ == "__main__":
    # Example usage
    layout = load_minimal_layout_from_keyboard("src/data/keyboards/ansi_60_percent.json")
    print(f"Loaded {len(layout.key_map)} character mappings")
    
    # Test character lookup
    key = layout.find_key_for_char('a')
    if key:
        print(f"Character 'a' maps to key {key.id} at position ({key.x}, {key.y})")