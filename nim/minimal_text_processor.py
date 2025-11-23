import os
import time
import math
from typing import Dict, List, Tuple, Optional
from minimal_python_structures import (
    KeyData, FingerState, MinimalLayout, MinimalFittsCalculator,
    load_minimal_layout_from_keyboard
)

class SimplifiedTextProcessor:
    """Minimal text processor for Nim port"""
    
    def __init__(self, layout: MinimalLayout, fitts_a: float = 0.0, fitts_b: float = 150.0):
        self.layout = layout
        self.fitts_calc = MinimalFittsCalculator(fitts_a, fitts_b)
        self.finger_states = {}  # finger_id -> FingerState
        self.setup_finger_states()
        
    def setup_finger_states(self):
        """Initialize finger states with homing keys"""
        # Find homing keys for each finger (simplified)
        homing_keys = {}
        for key_data in self.layout.key_map.values():
            if key_data.char in ['a', 's', 'd', 'f']:  # Left hand homing
                homing_keys[key_data.finger] = key_data.id
            elif key_data.char in ['j', 'k', 'l', ';']:  # Right hand homing  
                homing_keys[key_data.finger] = key_data.id
        
        # Initialize finger states
        for finger_id in range(5):  # 0-4 for one hand, will extend for both
            homing_key_id = homing_keys.get(finger_id, 0)
            self.finger_states[finger_id] = FingerState(finger_id, homing_key_id)
    
    def reset_finger_positions(self):
        """Reset all fingers to homing positions"""
        for finger_state in self.finger_states.values():
            finger_state.current_key_id = finger_state.homing_key_id
            finger_state.total_distance = 0.0
            finger_state.total_time = 0.0
            finger_state.key_count = 0
    
    def type_character(self, char: str) -> Tuple[float, float]:
        """Type a single character and return (distance, time)"""
        # Find target key
        key_data = self.layout.find_key_for_char(char)
        if not key_data:
            return 0.0, 0.0  # Character not available
        
        # Get finger for this key
        finger_state = self.finger_states.get(key_data.finger)
        if not finger_state:
            return 0.0, 0.0
        
        # Get current and target positions
        current_key = self.layout.get_key_by_id(finger_state.current_key_id)
        if not current_key:
            return 0.0, 0.0
            
        target_key = key_data
        
        # Calculate distance and time
        distance = current_key.distance_to(target_key)
        time_ms = self.fitts_calc.calculate_time(distance)
        
        # Update finger state
        finger_state.current_key_id = target_key.id
        finger_state.total_distance += distance
        finger_state.total_time += time_ms
        finger_state.key_count += 1
        
        return distance, time_ms
    
    def process_text(self, text: str, preview_mode: bool = False, max_chars: int = 100000) -> Dict:
        """Process text and return statistics"""
        start_time = time.time()
        
        if preview_mode and len(text) > max_chars:
            text = text[:max_chars]
        
        self.reset_finger_positions()
        
        total_distance = 0.0
        total_time = 0.0
        char_count = 0
        typed_chars = 0
        
        for char in text:
            char_count += 1
            
            if not char.isprintable() or char.isspace():
                continue
                
            distance, time_ms = self.type_character(char)
            
            if distance > 0:  # Character was typed
                total_distance += distance
                total_time += time_ms
                typed_chars += 1
                
                # Reset positions occasionally (simulate breaks)
                if typed_chars % 256 == 0:
                    self.reset_finger_positions()
        
        processing_time = time.time() - start_time
        coverage = (typed_chars / char_count * 100) if char_count > 0 else 0
        
        return {
            'total_distance': total_distance,
            'total_time': total_time,
            'char_count': char_count,
            'typed_chars': typed_chars,
            'coverage': coverage,
            'processing_time': processing_time,
            'chars_per_second': typed_chars / processing_time if processing_time > 0 else 0
        }
    
    def print_finger_stats(self):
        """Print finger usage statistics"""
        print("\n=== Finger Usage Statistics ===")
        
        total_distance = sum(fs.total_distance for fs in self.finger_states.values())
        total_time = sum(fs.total_time for fs in self.finger_states.values())
        total_presses = sum(fs.key_count for fs in self.finger_states.values())
        
        finger_names = ['Pinky', 'Ring', 'Middle', 'Index', 'Thumb']
        
        print(f"{'Finger':<10} {'Presses':<8} {'Distance':<12} {'Time':<10}")
        print("-" * 45)
        
        for i, finger_state in self.finger_states.items():
            finger_name = finger_names[i] if i < len(finger_names) else f"Finger{i}"
            presses = finger_state.key_count
            distance = finger_state.total_distance
            time_ms = finger_state.total_time
            
            press_pct = (presses / total_presses * 100) if total_presses > 0 else 0
            dist_pct = (distance / total_distance * 100) if total_distance > 0 else 0
            time_pct = (time_ms / total_time * 100) if total_time > 0 else 0
            
            print(f"{finger_name:<10} {presses:<8} {distance:<12.1f} {time_ms:<10.1f}")
        
        print("-" * 45)
        print(f"{'TOTAL':<10} {total_presses:<8} {total_distance:<12.1f} {total_time:<10.1f}")

def process_file(file_path: str, layout_file: str = "src/data/keyboards/ansi_60_percent.json", 
                preview_mode: bool = False, max_chars: int = 100000) -> Dict:
    """Process a text file and return statistics"""
    print(f"Loading layout from {layout_file}")
    layout = load_minimal_layout_from_keyboard(layout_file)
    print(f"Loaded layout with {len(layout.key_map)} character mappings")
    
    processor = SimplifiedTextProcessor(layout)
    
    if not os.path.exists(file_path):
        print(f"Warning: File {file_path} not found")
        return {}
    
    print(f"Loading text from {file_path}")
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read(max_chars if preview_mode else None)
    
    print(f"Processing {len(text)} characters (preview: {preview_mode})")
    
    stats = processor.process_text(text, preview_mode, max_chars)
    
    print(f"\n=== Processing Results ===")
    print(f"Characters processed: {stats['char_count']:,}")
    print(f"Characters typed: {stats['typed_chars']:,}")
    print(f"Coverage: {stats['coverage']:.2f}%")
    print(f"Total distance: {stats['total_distance']:.1f} mm")
    print(f"Total time: {stats['total_time']:.1f} ms")
    print(f"Processing time: {stats['processing_time']:.3f} s")
    print(f"Speed: {stats['chars_per_second']:.1f} chars/sec")
    
    processor.print_finger_stats()
    
    return stats

if __name__ == "__main__":
    # Test with preview file
    preview_file = "src/data/text/raw/simple_wikipedia_dataset_preview.txt"
    stats = process_file(preview_file, preview_mode=True, max_chars=50000)
    
    print(f"\n=== Comparison with Python ===")
    print("This minimal implementation processes text character-by-character")
    print("and calculates finger movement distances and times using Fitts law.")
    print("The Nim port should be significantly faster for large text files.")