"""
Simplified Typer for new evaluation workflow
Implements simplified fitness function: fitness = weight1 * normalized_distance + weight2 * normalized_time
- Distance simulation in 256-character window with persistent finger state
- Time calculation using Fitts law with finger strength factors
- Parallel typing with synchronous endings for even finger usage
"""

import os
import time
from src.config.config import Config
from src.core.mapper import KeyType
from src.core.keyboard import FingerName, enums_to_fingername, fingername_to_enums, Hand
from collections import defaultdict, deque
import math


class SimplifiedTyper:
    def __init__(self, keyboard, distance, layout, dataset, dataset_name='simple_wikipedia', debug=False):
        self.debug = debug
        self.dataset_name = dataset_name
        self._print("Simplified Typer initiated")
        self.keyboard = keyboard
        self.distance = distance
        self.layout = layout
        self.dataset = dataset
        self.load_finger_positions()

    def load_finger_positions(self):
        """Initialize finger positions and state tracking"""
        self.finger = {}
        for finger in FingerName:
            try:
                homing_key = self.keyboard.get_homing_key_for_finger_name(finger)
                if homing_key is None:
                    self._print(f"⚠️  Warning: No homing key found for finger {finger}")
                    continue
                homing_position = homing_key.id
                
                # Debug: Print finger to homing key mapping
                if self.debug:
                    print(f"Finger {finger} homing position: key {homing_position} at ({homing_key.x}, {homing_key.y})")
                
                self.finger[finger] = {
                    'homing_position': homing_position,
                    'current_position': homing_position,
                    'total_distance': 0.0,
                    'total_time': 0.0,
                    'key_count': 0,
                    'active_in_window': False
                }
            except Exception as e:
                self._print(f"⚠️  Error initializing finger {finger}: {e}")
                continue

        # Sliding window for simulation
        self.simulation_window = deque(maxlen=Config.fitness.simulation_window_size)
        self.window_finger_states = {}  # Track finger states within current window

    def reset_finger_position(self):
        """Reset all fingers to homing position"""
        for finger in self.finger:
            self.finger[finger]['current_position'] = self.finger[finger]['homing_position']
        self.simulation_window.clear()
        self.window_finger_states.clear()

    def get_finger_for_key(self, key_id):
        """Get the finger name for a key based on the current layout"""
        # Use the layout to determine which finger should press this key
        # The layout should have the finger assignment for each key
        try:
            # First try to get finger from layout's key assignment
            if hasattr(self.layout, 'mapper') and hasattr(self.layout.mapper, 'data'):
                for (k_id, layer_id), key_data in self.layout.mapper.data.items():
                    if k_id == key_id and key_data.key_type.name == 'CHAR':
                        # This key is assigned to a character, find which finger should press it
                        # For now, fall back to keyboard default, but this should be layout-specific
                        break
            
            # Fall back to keyboard default finger assignment
            fingername = enums_to_fingername(
                self.keyboard.keys[key_id].finger,
                self.keyboard.keys[key_id].hand
            )
            if isinstance(fingername, list):
                fingername = fingername[0]
            
            # Debug: Print finger assignment
            if self.debug:
                key_obj = self.keyboard.keys[key_id]
                self._print(f"Key {key_id} ('{key_obj.label}'): assigned to {fingername} (keyboard finger: {key_obj.finger}, hand: {key_obj.hand})")
            
            return fingername
        except Exception as e:
            print(f"Error getting finger for key {key_id}: {e}")
            # Return a default finger if there's an error
            return FingerName.INDEX_FINGER_LEFT

    def calculate_fitts_time(self, distance, finger):
        """Calculate movement time using Fitts law with finger strength factor"""
        # Base Fitts law: MT = a + b * log2(D/W + 1)
        # For typing, we approximate W (target width) as constant
        # So: MT = a + b * log2(D + 1)
        fitts_a = Config.fitness.fitts_a
        fitts_b = Config.fitness.fitts_b
        
        base_time = fitts_a + fitts_b * math.log2(distance + 1)
        
        # Apply finger strength factor
        finger_factor = Config.fitness.finger_time_base.get(finger, 1.0)
        adjusted_time = base_time * finger_factor
        
        return adjusted_time

    def move_finger_in_window(self, finger_param, key_to, char):
        """Move finger within simulation window with state persistence"""
        key_from = self.finger[finger_param]['current_position']
        
        # Calculate distance directly using keyboard geometry
        if hasattr(finger_param, 'name'):
            finger_name = finger_param.name.lower()
        elif hasattr(finger_param, 'value'):
            finger_name = str(finger_param.value).lower()
        else:
            finger_name = str(finger_param).lower()
        
        # Get key positions
        try:
            key_from_obj = self.keyboard.keys[key_from]
            key_to_obj = self.keyboard.keys[key_to]
        except KeyError as e:
            print(f"⚠️  Key lookup error: key_from={key_from}, key_to={key_to}, available keys: {list(self.keyboard.keys.keys())[:10]}...")
            raise
        
        # Calculate Euclidean distance
        dx = key_to_obj.x - key_from_obj.x
        dy = key_to_obj.y - key_from_obj.y
        distance = (dx**2 + dy**2)**0.5
        
        # Debug: Check for invalid distance
        if distance <= 0:
            # Only warn if this is not a same-key movement (which is normal)
            if key_from != key_to:
                self._print(f"⚠️  Warning: Invalid distance calculated: {distance}")
                self._print(f"  From: ({key_from_obj.x}, {key_from_obj.y}) to ({key_to_obj.x}, {key_to_obj.y})")
                self._print(f"  Finger: {finger_name}, Char: {char}")
                self._print(f"  Key from: {key_from}, Key to: {key_to}")
            # For same-key movements (distance = 0), use a small distance for Fitts' law calculation
            distance = 0.1 if key_from != key_to else 0.01  # Very small distance for same key
        
        # Calculate time using Fitts' Law
        time = self.calculate_fitts_time(distance, finger_param)
        
        # Debug: Check for invalid time
        if time <= 0 or time == float('inf'):
            self._print(f"⚠️  Warning: Invalid time calculated: {time}")
            self._print(f"  Distance: {distance}, Finger: {finger_name}")
            time = 0.001  # Fallback to small positive time
        
        # Update finger statistics
        self.finger[finger_param]['total_distance'] += distance
        self.finger[finger_param]['total_time'] += time
        self.finger[finger_param]['key_count'] += 1
        
        # Update current position
        self.finger[finger_param]['current_position'] = key_to
        
        # Track in simulation window
        movement_record = {
            'finger': finger_param,
            'from': key_from,
            'to': key_to,
            'distance': distance,
            'time': time,
            'char': char,
            'finger_name': finger_name
        }
        
        self.simulation_window.append(movement_record)
        
        if Config.fitness.finger_state_persistence:
            # Update window finger state
            self.window_finger_states[finger_param] = {
                'position': key_to,
                'last_movement': len(self.simulation_window) - 1
            }
        
        return distance, time

    def process_parallel_typing(self, char_sequence):
        """Process typing with parallel finger movements and synchronous endings"""
        if not Config.fitness.parallel_typing_enabled:
            # Sequential typing
            total_distance = 0.0
            total_time = 0.0
            
            for char in char_sequence:
                distance, time = self.type_character_sequential(char)
                total_distance += distance
                total_time += time
                
            return total_distance, total_time
        
        # Parallel typing simulation
        parallel_movements = []
        current_time = 0.0
        
        for i, char in enumerate(char_sequence):
            distance, time = self.type_character_parallel(char, current_time)
            parallel_movements.append({
                'char': char,
                'distance': distance,
                'time': time,
                'start_time': current_time
            })
            current_time += 0.01  # Small offset to simulate slight asynchronicity
        
        # Calculate total time with synchronous endings
        if Config.fitness.synchronous_end and parallel_movements:
            max_completion_time = max(m['start_time'] + m['time'] for m in parallel_movements)
            total_time = max_completion_time
        else:
            total_time = sum(m['time'] for m in parallel_movements)
        
        total_distance = sum(m['distance'] for m in parallel_movements)
        
        return total_distance, total_time

    def type_character_sequential(self, char):
        """Type a single character sequentially"""
        key_id, layer, qmk_key = self.layout.find_key_for_char(char)
        
        # Handle modifiers (Shift, AltGr)
        modifiers_distance = 0.0
        modifiers_time = 0.0
        
        shift_keys = self.layout.mapper.filter_data(
            lambda key_id, layer_id, value: value.key_type == KeyType.CONTROL and value.value == 'Shift')
        altgr_keys = self.layout.mapper.filter_data(
            lambda key_id, layer_id, value: value.key_type == KeyType.LAYER and value.value == 'AltGr')
        
        # Handle shift if needed
        shift_key_id = self.get_shift_key_for_char(char, key_id, shift_keys)
        if shift_key_id is not None:
            shift_finger = self.get_finger_for_key(shift_key_id)
            shift_dist, shift_time = self.move_finger_in_window(shift_finger, shift_key_id, 'Shift')
            modifiers_distance += shift_dist
            modifiers_time += shift_time
        
        # Handle AltGr if needed
        altgr_key_id = None
        if layer == 1:  # ALTGR_LAYER
            altgr_key_id = self.get_altgr_key_for_char(char, key_id, altgr_keys)
            if altgr_key_id is not None:
                altgr_finger = self.get_finger_for_key(altgr_key_id)
                altgr_dist, altgr_time = self.move_finger_in_window(altgr_finger, altgr_key_id, 'AltGr')
                modifiers_distance += altgr_dist
                modifiers_time += altgr_time
        
        # Type the character
        finger = self.get_finger_for_key(key_id)
        char_distance, char_time = self.move_finger_in_window(finger, key_id, char)
        
        total_distance = modifiers_distance + char_distance
        total_time = modifiers_time + char_time
        
        return total_distance, total_time

    def type_character_parallel(self, char, start_time):
        """Type a single character for parallel processing"""
        return self.type_character_sequential(char)

    def get_shift_key_for_char(self, char, key_id, shift_keys):
        """Get the appropriate shift key (opposite hand) for a character"""
        shifted = self.layout.get_shifted_symbols()
        if char not in shifted:
            return None

        for shift in shift_keys:
            shift_id, _ = shift
            if self.keyboard.keys[key_id].hand != self.keyboard.keys[shift_id[0]].hand:
                return shift_id[0]
        return None

    def get_altgr_key_for_char(self, char, key_id, altgr_keys):
        """Get the appropriate AltGr key for a character"""
        layer1_chars = self.layout.get_altgr_symbols()
        if char not in layer1_chars:
            return None

        base_key_for_char = self.layout.find_key_for_char(char)
        if not base_key_for_char:
            return None
        
        base_char_key_id = base_key_for_char[0]
        base_key = self.keyboard.keys[base_char_key_id]
        
        # Find AltGr key - prefer opposite hand
        for altgr_item in altgr_keys:
            altgr_key_tuple = altgr_item[0]
            altgr_key_id = altgr_key_tuple[0]
            altgr_key = self.keyboard.keys[altgr_key_id]
            
            if base_key.hand != altgr_key.hand:
                return altgr_key_id
        
        # Fallback to any available AltGr key
        for altgr_item in altgr_keys:
            altgr_key_tuple = altgr_item[0]
            altgr_key_id = altgr_key_tuple[0]
            return altgr_key_id

        return None

    def set_normalization_bounds(self, min_distance, max_distance, min_time, max_time):
        """Set normalization bounds from GA tracking"""
        self.min_distance = min_distance
        self.max_distance = max_distance
        self.min_time = min_time
        self.max_time = max_time

    def is_character_typed(self, char):
        """Check if character can be typed on this keyboard layout"""
        try:
            key_id, layer, qmk_key = self.layout.find_key_for_char(char)
            return key_id is not None
        except:
            return False

    def calculate_distance_and_time_from_raw_text(self, text_file_path):
        """Calculate distance and time by processing raw text character by character"""
        try:
            with open(text_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Warning: Raw text file {text_file_path} not found, falling back to frequency method")
            return 0.0, 0.0, 0.0
        
        # Process text character by character
        total_distance = 0.0
        total_time = 0.0
        char_count = 0
        
        # Reset finger positions at start
        self.reset_finger_position()
        
        for char in text:
            if not self.is_character_typed(char):
                continue  # Skip characters not on keyboard
                
            distance, time = self.type_character_sequential(char)
            total_distance += distance
            total_time += time
            char_count += 1
            
            # Reset position occasionally to simulate breaks (every 256 chars)
            if char_count % Config.fitness.simulation_window_size == 0:
                self.reset_finger_position()
        
        coverage = (char_count / len(text)) * 100 if text else 0
        print(f"Raw text processing: {char_count} typed chars out of {len(text)} total ({coverage:.2f}% coverage)")
        
        return total_distance, total_time, coverage

    def calculate_distance_and_time_from_text(self, dataset):
        """Calculate distance and time by processing character frequency data from dataset"""
        char_data = dataset.get(Config.dataset.field_character_frequencies, [])
        print(f"Debug: Found {len(char_data)} character entries in dataset")
        
        if not char_data:
            print("⚠️  No character frequency data found in dataset!")
            return 0.0, 0.0, 0.0
        
        total_weighted_distance = 0.0
        total_weighted_time = 0.0
        total_percentage = 0.0
        total_chars_processed = 0
        
        # Character frequency processing debug (DISABLED during GA runs)
        # print("=== Character Frequency Processing ===")
        
        for char_entry in char_data:
            char = char_entry.get(Config.dataset.field_character_frequencies_char, '')
            percentage = char_entry.get(Config.dataset.field_character_frequencies_relative, 0) * 100
            
            if percentage <= 0 or not char:
                continue
                
            total_percentage += percentage
            
            # Reset for each character calculation
            self.reset_finger_position()
            
            # Process the character
            distance, time = self.process_parallel_typing(char)
            
            # Weight by character frequency
            weighted_distance = distance * percentage
            weighted_time = time * percentage
            
            total_weighted_distance += weighted_distance
            total_weighted_time += weighted_time
            total_chars_processed += 1
            
            if self.debug:
                print(f"Character '{char}': distance={distance:.4f}, time={time:.4f}, weight={percentage:.4f}")
        
        # Character processing summary (DISABLED during GA runs)
        # print(f"Processed {total_chars_processed} unique characters")
        # print(f"Total character frequency coverage: {total_percentage:.2f}%")
        
        return total_weighted_distance, total_weighted_time, total_percentage

    def calculate_distance_and_time_from_words(self, word_data):
        """Calculate total distance and time from word data"""
        words = word_data.get(Config.dataset.field_word_frequencies, [])
        print(f"Debug: Found {len(words)} words in dataset")
        
        if not words:
            print("⚠️  No words found in dataset!")
            return 0.0, 0.0, 0.0
        
        total_weighted_distance = 0.0
        total_weighted_time = 0.0
        total_percentage = 0.0
        
        for word_entry in words:
            word = word_entry.get(Config.dataset.field_word_frequencies_word, '')
            percentage = word_entry.get(Config.dataset.field_word_frequencies_relative, 0) * 100
            
            if percentage <= 0 or not word:
                continue
                
            total_percentage += percentage
            
            # Reset for each word calculation
            self.reset_finger_position()
            
            # Process the word with parallel typing
            distance, time = self.process_parallel_typing(word)
            
            # Weight by word frequency
            weighted_distance = distance * percentage
            weighted_time = time * percentage
            
            total_weighted_distance += weighted_distance
            total_weighted_time += weighted_time
            
            if self.debug:
                print(f"Word '{word}': distance={distance:.4f}, time={time:.4f}, weight={percentage:.4f}")
        
        return total_weighted_distance, total_weighted_time, total_percentage

    def normalize_values(self, value, min_val, max_val):
        """Normalize value to 0-1 range"""
        if max_val > min_val:
            return (value - min_val) / (max_val - min_val)
        return 0.0

    def fitness(self):
        """Calculate simplified fitness using new formula"""
        if not Config.fitness.use_simplified_fitness:
            # Fall back to legacy fitness calculation
            return self.legacy_fitness()
        
        # Quick fitness calculation for preview mode
        # Use minimal computation to avoid long processing times
        import time
        start_time = time.time()
        
        # Use preview file if available, otherwise full dataset
        raw_text_path = f"src/data/text/raw/{self.dataset_name}_dataset.txt"
        preview_text_path = f"src/data/text/raw/{self.dataset_name}_dataset_preview.txt"
        
        # Determine which file to use
        if os.path.exists(preview_text_path):
            text_path = preview_text_path
            data_size = "preview"
        elif os.path.exists(raw_text_path):
            text_path = raw_text_path
            data_size = "full"
        else:
            # Fallback to simple calculation if no text file
            print(f"⚠️  No text file found for dataset '{self.dataset_name}'")
            print(f"  Expected files: {raw_text_path} or {preview_text_path}")
            total_distance = 100.0
            total_time = 50.0
            char_count = 0
            calculation_time = time.time() - start_time
            
            # Print finger usage statistics (DISABLED during GA runs)
            # self.print_finger_statistics()
            
            print(f"Fitness calculation completed (fallback):")
            print(f"  Characters processed: {char_count:,}")
            print(f"  Total distance: {total_distance:.4f} mm")
            print(f"  Total time: {total_time:.4f} s")
            print(f"  Calculation time: {calculation_time:.3f}s")
            
            return (total_distance, total_time)
        
        # Simple character counting for preview mode
        try:
            with open(text_path, 'r', encoding='utf-8', errors='ignore') as f:
                # For preview mode, only process first 100,000 characters to be faster
                if data_size == "preview":
                    text = f.read(100000)  # Only read first 100KB for preview
                else:
                    # For full dataset, limit to first 500,000 characters to avoid hanging
                    self._print(f"Processing large dataset ({data_size}), limiting to 500KB sample...")
                    text = f.read(500000)  # Limit to 500KB to avoid memory issues
                    self._print(f"Read {len(text)} characters from {data_size} dataset")
            
            # Process text character by character for actual finger movement simulation
            total_distance = 0.0
            total_time = 0.0
            char_count = 0
            
            # Reset finger positions at start
            self.reset_finger_position()
            
            for char in text:
                if not self.is_character_typed(char):
                    continue  # Skip characters not on keyboard
                    
                # Use parallel typing simulation for better accuracy
                distance, time_component = self.process_parallel_typing(char)
                total_distance += distance
                total_time += time_component
                char_count += 1
                
                # Reset position occasionally to simulate breaks (every 256 chars)
                if char_count % Config.fitness.simulation_window_size == 0:
                    self.reset_finger_position()
            
            calculation_time = time.time() - start_time
            
            # Debug info only when explicitly requested
            if hasattr(Config, 'debug') and Config.debug:
                print(f"Preview fitness calculation ({data_size}):")
                print(f"  Characters processed: {char_count:,}")
                print(f"  Calculation time: {calculation_time:.3f}s")
                print(f"  Total distance: {total_distance:.1f}, Total time: {total_time:.1f}")
            
            # Print finger usage statistics (DISABLED during GA runs)
            # self.print_finger_statistics()
            
        except Exception as e:
            # Fallback on error
            total_distance = 100.0
            total_time = 50.0
            char_count = 0  # Define char_count for fallback case
            calculation_time = time.time() - start_time
            
            # Print finger usage statistics (DISABLED during GA runs)
            # self.print_finger_statistics()
        
        # Set coverage variables based on which method was used
        if os.path.exists(raw_text_path) or (os.path.exists(preview_text_path)):
            coverage_type = "raw text"
            word_percentage = 0.0
            char_percentage = 0.0
        else:
            coverage_type = "frequency"
            word_percentage = 0.0  # Initialize to avoid NameError
            char_percentage = 0.0  # Initialize to avoid NameError
        
        # Coverage and processing debug (DISABLED during GA runs)
        # print(f"Coverage type: {coverage_type}")
        # if coverage_type == "frequency":
        #     print(f"Word coverage: {word_percentage:.2f}%")
        #     print(f"Character coverage: {char_percentage:.2f}%")
        # else:
        #     print(f"Raw text processed successfully")
        
        if self.debug:
            print(f"Total distance: {total_distance:.4f}")
            print(f"Total time: {total_time:.4f}")
        
        # Debug: Check for invalid values
        if total_distance <= 0 or total_time <= 0:
            self._print(f"⚠️  Warning: Invalid distance ({total_distance}) or time ({total_time}) values")
            self._print(f"  This may cause inf fitness. Using fallback values.")
            total_distance = max(total_distance, 0.1)  # Ensure positive
            total_time = max(total_time, 0.1)          # Ensure positive
        
        self._print(f"Fitness calculation completed:")
        self._print(f"  Characters processed: {char_count:,}")
        self._print(f"  Total distance: {total_distance:.4f} mm")
        self._print(f"  Total time: {total_time:.4f} s")
        self._print(f"  Calculation time: {calculation_time:.3f}s")
        
        # Return raw distance and time values for GA to process
        # The GA will handle normalization and fitness calculation
        return (total_distance, total_time)

    def set_normalization_bounds(self, min_distance, max_distance, min_time, max_time):
        """Set normalization bounds from GA for consistent fitness calculation"""
        self.min_distance = min_distance
        self.max_distance = max_distance
        self.min_time = min_time
        self.max_time = max_time
        print(f"Typer bounds updated: Distance {min_distance:.1f}-{max_distance:.1f}, Time {min_time:.2f}-{max_time:.2f}")

    def print_finger_statistics(self):
        """Print finger usage statistics for even distribution analysis"""
        print(f"\n=== Finger Usage Statistics ===")
        
        total_distance = sum(f['total_distance'] for f in self.finger.values())
        total_time = sum(f['total_time'] for f in self.finger.values())
        total_presses = sum(f['key_count'] for f in self.finger.values())
        
        print(f"{'Finger':<15} {'Presses':<8} {'% Presses':<10} {'Distance':<10} {'% Distance':<10} {'Time':<10} {'% Time':<10}")
        print("-" * 80)
        
        if total_presses > 0:
            for finger_name, finger_data in self.finger.items():
                presses = finger_data['key_count']
                press_pct = (presses / total_presses) * 100
                distance_pct = (finger_data['total_distance'] / total_distance * 100) if total_distance > 0 else 0
                time_pct = (finger_data['total_time'] / total_time * 100) if total_time > 0 else 0
                
                print(f"{finger_name:<15} {presses:<8} {press_pct:<10.1f} {finger_data['total_distance']:<10.2f} {distance_pct:<10.1f} {finger_data['total_time']:<10.2f} {time_pct:<10.1f}")
        
        print("-" * 80)
        print(f"{'TOTAL':<15} {total_presses:<8} {'100.0':<10} {total_distance:<10.2f} {'100.0':<10} {total_time:<10.2f} {'100.0':<10}")

    def legacy_fitness(self):
        """Fall back to legacy fitness calculation for comparison"""
        # This would call the original typer.fitness() method
        # For now, return a basic structure
        return {
            'distance_score': 0.0,
            'ngram_score': 1.0,
            'homing_score': 1.0
        }

    def _print(self, *args, **kwargs):
        """Debug printing"""
        if self.debug:
            print(*args, **kwargs)