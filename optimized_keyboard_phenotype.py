from kle.kle_model import Keyboard, FingerName, Hand
from collections import defaultdict, Counter
import string
import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Set
from finger_strength import SCALED_COST_PER_FINGER, FINGER_MOBILITY_PENALITY


def cartesian_distance(point1, point2, penalty):
    """Calculate the Cartesian distance between two points with penalty weights."""
    if len(point1) != len(point2) or len(point1) not in [2, 3]:
        raise ValueError("Points must have the same dimensionality (2D or 3D)")

    squared_diffs = [c * (a - b) ** 2 for a, b,
                     c in zip(point1, point2, penalty)]
    return math.sqrt(sum(squared_diffs))


@dataclass
class KeyPress:
    """Immutable representation of a key press."""
    key: object  # The physical key object
    finger_name: object  # FingerName enum
    presses: float  # Number of times pressed


@dataclass
class FingerState:
    """Immutable finger state."""
    current_position: Tuple[float, float, float]
    total_cost: float = 0.0


class PureFitnessCalculator:
    """Pure fitness calculator - no mutable state."""

    def __init__(self, physical_keyboard):
        self.physical_keyboard = physical_keyboard
        # Pre-compute home positions (immutable)
        self.home_positions = self._compute_home_positions()

    def _compute_home_positions(self) -> Dict[object, Tuple[float, float, float]]:
        """Pre-compute home positions for all fingers."""
        positions = {}
        for finger_name in FingerName:
            homing_key = self.physical_keyboard.get_homing_key_for_finger_name(
                finger_name)
            positions[finger_name] = homing_key.get_key_center_position()
        return positions

    def calculate_sequence_cost(self, key_presses: List[KeyPress]) -> float:
        """
        Pure function: calculate total cost for a sequence of key presses.
        Returns same result for same input, no side effects.
        """
        # Initialize finger states
        finger_states = {
            finger_name: FingerState(position)
            for finger_name, position in self.home_positions.items()
        }

        alternation_state = 0  # For keys with multiple finger options

        total_cost = 0.0

        for key_press in key_presses:
            finger_name = key_press.finger_name

            # Handle keys that can be pressed by multiple fingers
            if isinstance(finger_name, list):
                actual_finger = finger_name[alternation_state]
                alternation_state = 1 - alternation_state  # Toggle 0/1
            else:
                actual_finger = finger_name

            # Get current finger state
            current_state = finger_states[actual_finger]

            # Calculate movement cost
            new_position = key_press.key.get_key_center_position()
            movement_cost = cartesian_distance(
                current_state.current_position,
                new_position,
                FINGER_MOBILITY_PENALITY[actual_finger]
            )

            # Calculate total cost for this key press
            press_cost = movement_cost * key_press.presses * \
                SCALED_COST_PER_FINGER[actual_finger]
            total_cost += press_cost

            # Update finger state (create new immutable state)
            finger_states[actual_finger] = FingerState(
                current_position=new_position,
                total_cost=current_state.total_cost + press_cost
            )

        return total_cost


class KeyboardLayoutMapper:
    """Handles mapping between characters and physical keys."""

    def __init__(self, physical_keyboard):
        self.physical_keyboard = physical_keyboard
        self.char_key_map = self._build_char_key_map()
        self.keymap = self._build_keymap()
        self.remap_keys = {}

    def _build_char_key_map(self) -> Dict[str, List[str]]:
        """Build mapping from characters to key sequences needed to type them."""
        char_key_map = {}

        # Basic letters (lowercase and uppercase)
        for i, letter in enumerate(string.ascii_lowercase):
            char_key_map[letter] = [letter]  # lowercase direct
            # uppercase with shift
            char_key_map[letter.upper()] = ['Shift', letter]

        # Numbers and their shifted symbols
        number_shift_map = {
            '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
            '6': '^', '7': '&', '8': '*', '9': '(', '0': ')'
        }
        for num, symbol in number_shift_map.items():
            char_key_map[num] = [num]
            char_key_map[symbol] = ['Shift', num]

        # Special characters and their shifted versions
        special_shift_map = {
            '`': '~', '-': '_', '=': '+',
            '[': '{', ']': '}', '\\': '|',
            ';': ':', "'": '"',
            ',': '<', '.': '>', '/': '?'
        }
        for base, shifted in special_shift_map.items():
            char_key_map[base] = [base]
            char_key_map[shifted] = ['Shift', base]

        # Space, tab, newline
        char_key_map[' '] = ['Space']
        char_key_map['\t'] = ['Tab']
        char_key_map['\n'] = ['Enter']

        return char_key_map

    def _build_keymap(self) -> Dict[str, List[object]]:
        """Build mapping from key names to physical key objects with improved matching."""
        keymap = defaultdict(list)

        # Create a comprehensive mapping of logical key names to possible physical key labels
        key_name_mappings = {
            # Letters
            **{letter: [letter, letter.upper(), letter.lower()]
               for letter in string.ascii_lowercase},

            # Numbers
            **{str(i): [str(i)] for i in range(10)},

            # Special characters - map both ways
            '`': ['`', '~', 'Grave'],
            '-': ['-', '_', 'Minus'],
            '=': ['=', '+', 'Equal'],
            '[': ['[', '{', 'BracketLeft'],
            ']': [']', '}', 'BracketRight'],
            '\\': ['\\', '|', 'Backslash'],
            ';': [';', ':', 'Semicolon'],
            "'": ["'", '"', 'Quote'],
            ',': [',', '<', 'Comma'],
            '.': ['.', '>', 'Period'],
            '/': ['/', '?', 'Slash'],

            # Special keys
            'Space': [' ', 'Space', 'space'],
            'Tab': ['Tab', '\t'],
            'Enter': ['Enter', '\n', 'Return'],
            'Shift': ['Shift', 'LShift', 'RShift', 'Left Shift', 'Right Shift'],
        }

        # Build reverse mapping from physical keys
        for key in self.physical_keyboard.keys:
            labels = key.get_labels()

            # For each logical key name we need to map
            for logical_name, possible_labels in key_name_mappings.items():
                # Check if any of the key's labels match this logical key
                for label in labels:
                    if label in possible_labels:
                        keymap[logical_name].append(key)
                        break

                # Also check if the logical name itself appears in labels
                if logical_name in labels:
                    keymap[logical_name].append(key)

        # Debug: Print what keys we found vs what we need
        needed_keys = set()
        for key_sequence in self.char_key_map.values():
            needed_keys.update(key_sequence)

        missing_keys = []
        for needed_key in needed_keys:
            if needed_key not in keymap or not keymap[needed_key]:
                missing_keys.append(needed_key)

        if missing_keys:
            print(f"""Warning: Missing physical keys for logical keys: {
                  missing_keys}""")

            # Try to find these keys by examining all physical key labels
            print("Available physical key labels:")
            all_labels = set()
            for key in self.physical_keyboard.keys:
                all_labels.update(key.get_labels())
            print(sorted(all_labels))

        return keymap

    def set_remap(self, remap_dict: Dict[str, str]):
        """Set key remapping."""
        self.remap_keys = remap_dict.copy()

    def char_to_key_presses(self, char: str) -> List[KeyPress]:
        """Convert a character to the key presses needed to type it."""
        if char not in self.char_key_map:
            # Try to handle unknown characters gracefully
            print(f"""Warning: Character '{
                  repr(char)}' not in character mapping""")
            return []

        key_sequence = self.char_key_map[char]
        key_presses = []

        for key_name in key_sequence:
            # Apply remapping if exists
            physical_key_name = self.remap_keys.get(key_name, key_name)

            if physical_key_name not in self.keymap or not self.keymap[physical_key_name]:
                print(f"""Warning: Key '{
                      physical_key_name}' not found in physical keyboard""")
                continue

            physical_keys = self.keymap[physical_key_name]

            # Handle multiple physical keys for same logical key
            for physical_key in physical_keys:
                finger_name = physical_key.get_finger_name()
                key_presses.append(KeyPress(
                    key=physical_key,
                    finger_name=finger_name,
                    presses=1.0
                ))

        return key_presses


class OptimizedKeyboardPhenotype:
    """Refactored keyboard phenotype with proper separation of concerns."""

    def __init__(self, physical_keyboard, remap=None):
        self.physical_keyboard = physical_keyboard
        self.layout_mapper = KeyboardLayoutMapper(physical_keyboard)
        self.fitness_calculator = PureFitnessCalculator(physical_keyboard)

        if remap:
            self.layout_mapper.set_remap(remap)

    def set_remap(self, remap_dict: Dict[str, str]):
        """Apply key remapping."""
        self.layout_mapper.set_remap(remap_dict)

    def fitness(self, dataset_frequency_data, total_simulated_presses=50_000_000,
                word_weight=0.7, char_weight=0.3, max_words=5000):
        """
        Improved fitness function with proper character accounting to avoid double-counting.
        """
        word_frequencies = dataset_frequency_data['word_frequencies']
        char_frequencies = dataset_frequency_data['character_frequencies']

        # Calculate expected character presses from global frequencies
        char_expected_presses = {}
        total_expected_char_presses = 0

        for char, char_data in char_frequencies.items():
            expected_presses = char_data['relative'] * total_simulated_presses
            char_expected_presses[char] = expected_presses
            total_expected_char_presses += expected_presses

        print(f"""Debug: Expected total char presses: {
              total_expected_char_presses:,.0f}""")
        print(f"Debug: Target total presses: {total_simulated_presses:,.0f}")

        # Collect all key presses
        all_key_presses = []
        chars_used_in_words = Counter()  # Track what we use in words

        # Step 1: Process words (70% of total presses)
        word_presses_budget = total_simulated_presses * word_weight
        top_words = word_frequencies[:max_words]

        if top_words:
            total_word_freq = sum(word_data['absolute']
                                  for word_data in top_words)

            for word_data in top_words:
                word = word_data['word'].lower()
                word_frequency = word_data['absolute']

                # Calculate total presses for this word
                word_weight_in_budget = word_frequency / total_word_freq
                word_total_presses = word_weight_in_budget * word_presses_budget

                # Add characters in word
                if len(word) > 0:
                    presses_per_char = word_total_presses / len(word)

                    for char in word:
                        chars_used_in_words[char] += presses_per_char
                        key_presses = self.layout_mapper.char_to_key_presses(
                            char)

                        for key_press in key_presses:
                            all_key_presses.append(KeyPress(
                                key=key_press.key,
                                finger_name=key_press.finger_name,
                                presses=key_press.presses * presses_per_char
                            ))

                # Add space after word
                chars_used_in_words[' '] += word_total_presses
                space_key_presses = self.layout_mapper.char_to_key_presses(' ')
                for key_press in space_key_presses:
                    all_key_presses.append(KeyPress(
                        key=key_press.key,
                        finger_name=key_press.finger_name,
                        presses=key_press.presses * word_total_presses
                    ))

        # Step 2: Calculate what percentage of each character's global frequency we used in words
        char_word_percentages = {}
        for char, expected_global_presses in char_expected_presses.items():
            used_in_words = chars_used_in_words.get(char, 0)
            if expected_global_presses > 0:
                percentage_used = used_in_words / expected_global_presses
                char_word_percentages[char] = min(
                    1.0, percentage_used)  # Cap at 100%
            else:
                char_word_percentages[char] = 0.0

        print(f"""Debug: Sample word percentages - " +
              ", """.join([f"'{k}': {v:.1%}" for k, v in
                           list(char_word_percentages.items())[:10]]))

        # Step 3: Process remaining characters (30% budget for non-word usage)
        char_presses_budget = total_simulated_presses * char_weight

        for char, expected_global_presses in char_expected_presses.items():
            # Calculate remaining percentage not covered by words
            word_percentage = char_word_percentages.get(char, 0.0)
            remaining_percentage = max(0.0, 1.0 - word_percentage)

            # Calculate remaining presses needed
            remaining_presses_needed = expected_global_presses * remaining_percentage

            # Allocate from our character budget proportionally
            if total_expected_char_presses > 0 and remaining_presses_needed > 0:
                char_press_count = (
                    remaining_presses_needed / total_expected_char_presses) * char_presses_budget

                if char_press_count > 1:  # Only simulate if meaningful
                    key_presses = self.layout_mapper.char_to_key_presses(char)

                    for key_press in key_presses:
                        all_key_presses.append(KeyPress(
                            key=key_press.key,
                            finger_name=key_press.finger_name,
                            presses=key_press.presses * char_press_count
                        ))

        # Calculate fitness
        total_cost = self.fitness_calculator.calculate_sequence_cost(
            all_key_presses)

        # Debug information
        total_actual_presses = sum(kp.presses for kp in all_key_presses)
        word_presses_count = sum(kp.presses for kp in all_key_presses[:len(
            [kp for kp in all_key_presses if any(chars_used_in_words)])])

        print(f"Total cost: {total_cost:,.2f}")
        print(f"Processed {len(top_words)} words from top {max_words}")
        print(f"Word presses: {sum(chars_used_in_words.values()):,.0f}")
        print(f"""Character presses: {
              total_actual_presses - sum(chars_used_in_words.values()):,.0f}""")
        print(f"Total press events: {len(all_key_presses):,}")
        print(f"Total actual presses: {total_actual_presses:,.0f}")
        print(f"Target presses: {total_simulated_presses:,.0f}")
        print(f"""Coverage: {(total_actual_presses /
              total_simulated_presses)*100:.1f}%""")

        return total_cost

    def get_physical_keyboard_with_remap(self):
        """Return physical keyboard with remapped labels."""
        keyboard_copy = self.physical_keyboard

        for original_key, new_key in self.layout_mapper.remap_keys.items():
            if original_key in self.layout_mapper.keymap:
                for physical_key in self.layout_mapper.keymap[original_key]:
                    physical_key.set_labels((new_key,))

        return keyboard_copy
