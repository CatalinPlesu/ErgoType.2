from src.domain.keyboard import Keyboard
from src.domain.hand_finger_enum import FingerName, Hand
from src.domain.layout_phenotype import LayoutPhenotype
from collections import defaultdict
import string
import random
import math
from src.config.finger_strength import FINGER_BIAS


def cartesian_distance(point1, point2, penalty):
    """
    Calculate the Cartesian distance between two points with weighted penalties.
    """
    if len(point1) != len(point2) or len(point1) not in [2, 3]:
        raise ValueError("Points must have the same dimensionality (2D or 3D)")

    squared_diffs = [c * (a - b) ** 2 for a, b,
                     c in zip(point1, point2, penalty)]
    return math.sqrt(sum(squared_diffs))


class Finger:
    def __init__(self, homing_key):
        self.homing_position = homing_key.get_key_center_position()
        self.current_position = homing_key.get_key_center_position()
        self.total_cost = 0

    def press(self, key, presses, fingername):
        new_position = key.get_key_center_position()
        
        # Get the bias for this finger
        bias = FINGER_BIAS[fingername]
        
        # Calculate penalties based on bias
        if len(self.current_position) == 2:  # 2D
            penalties = [bias.x_penalty, bias.y_penalty]
        else:  # 3D
            penalties = [bias.x_penalty, bias.y_penalty, bias.z_penalty]
        
        # Calculate distance with penalties
        distance = cartesian_distance(self.current_position, new_position, penalties)
        
        # Update position
        self.current_position = new_position
        
        # Calculate cost using effort multiplier
        cost = distance * bias.effort
        
        # Add to total cost
        self.total_cost += cost * presses


    def reset_position(self):
        self.current_position = self.homing_position

    def reset(self):
        self.total_cost = 0
        self.current_position = self.homing_position


class FingerManager:
    def __init__(self, physical_keyboard):
        self.fingers = {}
        self.list_alternation = 0
        for item in FingerName:
            self.fingers[item] = Finger(
                physical_keyboard.get_homing_key_for_finger_name(item))

    def press(self, key, presses):
        fingername = key.get_finger_name()
        if isinstance(fingername, list):
            self.fingers[fingername[self.list_alternation]].press(
                key, presses, fingername[0])
            self.list_alternation = 1 if self.list_alternation == 0 else 0
        else:
            self.fingers[fingername].press(key, presses, fingername)

    def get_total_cost(self):
        total_cost = 0
        for key, value in self.fingers.items():
            total_cost += value.total_cost
        return total_cost

    def reset_position(self):
        for key in self.fingers.keys():
            self.fingers[key].reset_position()

    def reset(self):
        for key in self.fingers.keys():
            self.fingers[key].reset()


class KeyboardPhenotype:
    def __init__(self, physical_keyboard, remap=None):
        print("Init keyboard phenotype")
        self.remap_keys = {}
        self.physical_keyboard = physical_keyboard
        self.finger_manager = FingerManager(self.physical_keyboard)
        
        # Create layout phenotype instance
        self.layout = LayoutPhenotype()
        
        # If remap is provided, apply the language configuration
        if remap is not None:
            self.layout.apply_language_layout(remap)
        
        # Build key mapping between virtual keys and physical keys
        self._build_key_mapping()
        
        # Track which keys are used during fitness calculation
        self.used_physical_keys = set()
        self.unreachable_chars = set()

    def _build_key_mapping(self):
        """Build mapping between virtual keys and physical keys."""
        # Create mapping from virtual key IDs to physical keys
        self.virtual_to_physical = {}
        
        # First, create a mapping from physical key labels to physical keys
        physical_key_map = {}
        for physical_key in self.physical_keyboard.keys:
            labels = physical_key.get_labels()
            for label in labels:
                # Add both the label and its lowercase version
                physical_key_map[label] = physical_key
                if label.lower() != label:
                    physical_key_map[label.lower()] = physical_key
        
        # Now map virtual keys to physical keys
        for virtual_key_id in self.layout.virtual_keys.keys():
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

    def select_remap_keys(self, keys_list):
        self.remap_keys = dict()
        self.remap_key_length = len(keys_list)
        self.original_key_list = keys_list

    def remap_to_keys(self, keys_list):
        if self.remap_key_length != len(keys_list):
            print("remap key list doesn't match in length")
            return

        remap_keys = dict()
        for index, key in enumerate(self.original_key_list):
            remap_keys[key] = keys_list[index]
        self.remap_keys = remap_keys
        print(self.remap_keys)

    def fitness(self, dataset_frequency_data, total_simulated_presses=50_000_000):
        """
        Fitness function based on frequency analysis data containing both word and character frequencies.

        Args:
            dataset_frequency_ Single dataset from the frequency analysis (not the full results dict)
            total_simulated_presses: Total number of presses to simulate
        """
        self.finger_manager.reset()
        self.used_physical_keys.clear()  # Reset tracking
        self.unreachable_chars.clear()  # Reset tracking

        # Extract word frequencies (top words)
        # List of dicts with 'word', 'absolute', 'relative', 'percentage'
        word_frequencies = dataset_frequency_data['word_frequencies']

        # Extract character frequencies
        # Dict with char as key and {'absolute', 'relative'} as value
        char_frequencies = dataset_frequency_data['character_frequencies']

        # Calculate total word frequency for normalization
        total_word_freq = sum(word_data['absolute']
                              for word_data in word_frequencies)

        # Calculate total character frequency for normalization
        total_char_freq = sum(data['absolute']
                              for data in char_frequencies.values())

        # Collect all characters that appear in the dataset
        dataset_chars = set()
        
        # Process top words
        word_presses_budget = total_simulated_presses * 0.7
        top_words = word_frequencies[:5000]

        for word_data in top_words:
            word = word_data['word']
            word_frequency = word_data['absolute']

            # Calculate how many times this word should be simulated based on its frequency
            word_presses = (word_frequency / total_word_freq) * \
                word_presses_budget

            # Process each character in the word
            for i, char in enumerate(word):
                # Convert to lowercase to match the frequency data
                char_lower = char.lower()
                dataset_chars.add(char_lower)

                # Get the key sequence needed to type this character
                key_sequence = self.layout.get_key_sequence(char_lower)
                if key_sequence:
                    for key_name in key_sequence:
                        # Look up the physical key for this virtual key
                        physical_key = self.virtual_to_physical.get(key_name)
                        if physical_key:
                            self.finger_manager.press(physical_key, word_presses)
                            self.used_physical_keys.add(physical_key)
                        else:
                            print(f"Warning: No physical key found for virtual key '{key_name}'")
                            if key_name not in ['Shift', 'AltGr', 'Space', 'Tab', 'Enter', 'Backspace', 'Caps Lock', 'Ctrl', 'Win', 'Alt', 'Menu']:
                                self.unreachable_chars.add(char_lower)
                else:
                    self.unreachable_chars.add(char_lower)

            # Reset position after each word to simulate moving to next word
            self.finger_manager.reset_position()

        # Process individual characters (remaining 30% of presses)
        char_presses_budget = total_simulated_presses * 0.3

        for char, char_data in char_frequencies.items():
            char_frequency = char_data['absolute']
            char_presses = (char_frequency / total_char_freq) * \
                char_presses_budget
            
            dataset_chars.add(char)

            # Get the key sequence needed to type this character
            key_sequence = self.layout.get_key_sequence(char)
            if key_sequence:
                for key_name in key_sequence:
                    # Look up the physical key for this virtual key
                    physical_key = self.virtual_to_physical.get(key_name)
                    if physical_key:
                        self.finger_manager.press(physical_key, char_presses)
                        self.used_physical_keys.add(physical_key)
                    else:
                        print(f"Warning: No physical key found for virtual key '{key_name}'")
                        if key_name not in ['Shift', 'AltGr', 'Space', 'Tab', 'Enter', 'Backspace', 'Caps Lock', 'Ctrl', 'Win', 'Alt', 'Menu']:
                            self.unreachable_chars.add(char)
            else:
                self.unreachable_chars.add(char)

        total_cost = self.finger_manager.get_total_cost()

        # Print summary of key usage
        print(f"Total cost from frequency-based simulation: {total_cost:,.2f}")
        print(f"Processed {min(len(top_words), 5000)} words from top 5000")
        print(f"Processed {len(char_frequencies)} individual characters")
        print(f"Total word frequency: {total_word_freq:,}")
        print(f"Total character frequency: {total_char_freq:,}")
        
        # Report key usage statistics
        total_physical_keys = len(self.physical_keyboard.keys)
        used_key_count = len(self.used_physical_keys)
        unused_key_count = total_physical_keys - used_key_count
        unreachable_char_count = len(self.unreachable_chars)
        
        print(f"Physical keys used: {used_key_count}/{total_physical_keys} ({used_key_count/total_physical_keys*100:.1f}%)")
        print(f"Physical keys unused: {unused_key_count}/{total_physical_keys} ({unused_key_count/total_physical_keys*100:.1f}%)")
        print(f"Characters unreachable in dataset: {unreachable_char_count}")
        
        if self.unreachable_chars:
            print(f"Unreachable characters: {sorted(list(self.unreachable_chars))}")
        
        # Find unused physical keys
        all_physical_keys = set(self.physical_keyboard.keys)
        unused_physical_keys = all_physical_keys - self.used_physical_keys
        if unused_physical_keys:
            unused_labels = []
            for key in unused_physical_keys:
                labels = key.get_labels()
                unused_labels.extend(list(labels))
            print(f"Unused physical key labels: {sorted(unused_labels)}")

        return total_cost

    def get_key(self, symbol):
        """Get physical key for a virtual key symbol."""
        if symbol in self.remap_keys.keys():
            symbol = self.remap_keys[symbol]
        physical_key = self.virtual_to_physical.get(symbol)
        return [physical_key] if physical_key else []

    def get_physical_keyboard(self):
        """Return the physical keyboard with updated labels."""
        # Update the labels on physical keys to reflect the current layout
        for virtual_key_id, physical_key in self.virtual_to_physical.items():
            if virtual_key_id in self.layout.virtual_keys:
                vkey = self.layout.virtual_keys[virtual_key_id]
                # Get the base layer character
                if 0 in vkey.layers:
                    unshifted, shifted = vkey.layers[0]
                    physical_key.set_labels((unshifted,))
        
        return self.physical_keyboard

    def get_physical_keyboard_with_costs(self):
        """
        Calculate the cost of pressing each key once with the appropriate finger
        and store this cost information on the physical keyboard model.
        """
        # Reset finger manager to start from home positions
        self.finger_manager.reset()

        # For each physical key, calculate the cost of one press
        for physical_key in self.physical_keyboard.keys:
            # Find which virtual key this physical key represents
            virtual_key_id = None
            for virt_id, phys_key in self.virtual_to_physical.items():
                if phys_key == physical_key:
                    virtual_key_id = virt_id
                    break
            
            if virtual_key_id and virtual_key_id in self.layout.virtual_keys:
                # Get finger name for this physical key
                fingername = physical_key.get_finger_name()
                if isinstance(fingername, list):
                    fingername = fingername[0]  # Use the first finger if it's a list
                
                # Press the key once using the finger manager
                self.finger_manager.fingers[fingername].press(physical_key, 1, fingername)

                # Get the total cost after this press
                cost = self.finger_manager.get_total_cost()

                # Store the cost on the key (assuming similar interface to set_labels)
                physical_key.set_labels((str(f"{cost:.2f}"),))

                # Reset finger manager for next key calculation
                self.finger_manager.reset()

        return self.physical_keyboard
