from src.domain.keyboard import Keyboard
from src.domain.hand_finger_enum import FingerName, Hand
from collections import defaultdict
import string
import random
import math
from finger_strength import SCALED_COST_PER_FINGER, FINGER_MOBILITY_PENALITY


def cartesian_distance(point1, point2, penality):
    """
    Calculate the Cartesian distance between two points.
    """
    if len(point1) != len(point2) or len(point1) not in [2, 3]:
        raise ValueError("Points must have the same dimensionality (2D or 3D)")

    # squared_diffs = [(a - b) ** 2 for a, b in zip(point1, point2, pen)]
    squared_diffs = [c * (a - b) ** 2 for a, b,
                     c in zip(point1, point2, penality)]
    return math.sqrt(sum(squared_diffs))


class Finger:
    def __init__(self, homing_key):
        self.homming_position = homing_key.get_key_center_position()
        self.current_position = homing_key.get_key_center_position()
        self.total_cost = 0

    def press(self, key, presses, fingername):
        new_possition = key.get_key_center_position()
        cost = cartesian_distance(
            self.current_position, new_possition, FINGER_MOBILITY_PENALITY[fingername])
        self.current_position = new_possition
        # cost = cartesian_distance(self.homming_position, new_possition)
        self.total_cost += cost * presses * SCALED_COST_PER_FINGER[fingername]

    def reset_position(self):
        self.current_position = self.homming_position

    def reset(self):
        self.total_cost = 0
        self.current_position = self.homming_position


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
        pass

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
    def __init__(self, physical_keyboard, remap):
        print("Init keyboard phenotype")
        self.remap_keys = {}
        self.physical_keyboard = physical_keyboard
        self.finger_manager = FingerManager(self.physical_keyboard)

        # create teh logical layers of keyboard, assuming that shift layer is tightly coulpled to a key, and we don't break it down
        layers = {
            "base": list(zip(list(string.ascii_lowercase), list(string.ascii_uppercase)))
            + list(zip(list('1234567890'), list('!@#$%^&*()')))
            + list(zip(list('[]=,./\\;-\'`'), list('{}+<>?|:_"~')))
        }

        # Map special keys to their characters if they have them
        special_key_map = {'Space': ' ', 'Tab': '\t',
                           'Enter': '\n', 'Shift': '', 'AltGr': ''}

        char_key_map = dict()
        for key, value in special_key_map.items():
            if value != '':
                char_key_map[value] = [key]
            else:
                char_key_map[key] = [key]  # for keys that don't have symbols

        # add the letters, numbers and symbols to the keymap
        for key in layers["base"]:
            char_key_map[key[0]] = [key[0]]
            char_key_map[key[1]] = ['Shift', key[0]]

        # identify unique needed keys for typing
        needed_keys = []
        for _, values in char_key_map.items():
            needed_keys += values
        needed_keys = set(needed_keys)

        # keymap maping keys to their phisical attributes
        keymap = defaultdict(list)
        for key in physical_keyboard.keys:
            found = False
            for k in needed_keys:
                if k in key.get_labels() or k.upper() in key.get_labels():
                    keymap[k].append(key)
                    found = True
                    break
            if not found:
                print(f"Key is unneeded {key.get_labels()}")

        self.keymap = keymap
        self.char_key_map = char_key_map

    def select_remap_keys(self, keys_list):
        self.remap_keys = dict()
        self.remap_key_length = len(keys_list)
        self.original_key_list = keys_list

    def remap_to_keys(self, keys_list):
        if self.remap_key_length != len(keys_list):
            print("remap key liset doesn't match in length")
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
            dataset_frequency_data: Single dataset from the frequency analysis (not the full results dict)
            total_simulated_presses: Total number of presses to simulate
        """
        self.finger_manager.reset()

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

        # Process top words (allocate 70% of presses to words)
        word_presses_budget = total_simulated_presses * 0.7

        # Take top words up to 5000 if available
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

                if char_lower in self.char_key_map.keys():
                    keys = self.translate_char_to_keys(char_lower)
                    for key in keys:
                        self.finger_manager.press(key, word_presses)

            # Reset position after each word to simulate moving to next word
            self.finger_manager.reset_position()

        # Process individual characters (remaining 30% of presses)
        char_presses_budget = total_simulated_presses * 0.3

        for char, char_data in char_frequencies.items():
            char_frequency = char_data['absolute']
            char_presses = (char_frequency / total_char_freq) * \
                char_presses_budget

            if char in self.char_key_map.keys():
                keys = self.translate_char_to_keys(char)
                for key in keys:
                    self.finger_manager.press(key, char_presses)

        total_cost = self.finger_manager.get_total_cost()

        print(f"Total cost from frequency-based simulation: {total_cost:,.2f}")
        print(f"Processed {min(len(top_words), 5000)} words from top 5000")
        print(f"Processed {len(char_frequencies)} individual characters")
        print(f"Total word frequency: {total_word_freq:,}")
        print(f"Total character frequency: {total_char_freq:,}")

        return total_cost

    def translate_char_to_keys(self, character):
        keys = self.char_key_map[character]
        # print(keys)
        keys = [self.get_key(key) for key in keys]
        # print(keys)
        if len(keys) == 2 and len(keys[0]) == 2:
            if keys[1][0].hand == Hand.LEFT:
                keys[0] = next(x for x in keys[0] if x.hand == Hand.RIGHT)
                keys[1] = keys[1][0]
            else:
                keys[0] = next(x for x in keys[0] if x.hand == Hand.LEFT)
                keys[1] = keys[1][0]
        else:
            keys = keys[0]
        return keys

    def get_key(self, symbol):
        if symbol in self.remap_keys.keys():
            symbol = self.remap_keys[symbol]
        keys = self.keymap[symbol]
        return keys

    def get_phisical_keyboard(self):
        for key, value in self.remap_keys.items():
            if len(self.keymap[key]) > 0:
                self.keymap[key][0].set_labels((value,))

        return self.physical_keyboard

    def get_physical_keyboard_with_costs(self):
        """
        Calculate the cost of pressing each key once with the appropriate finger
        and store this cost information on the physical keyboard model.
        """
        # Reset finger manager to start from home positions
        self.finger_manager.reset()

        # For each key on the physical keyboard, calculate the cost of one press
        for key in self.physical_keyboard.keys:
            # Press the key once using the finger manager
            self.finger_manager.press(key, 1)

            # Get the total cost after this press
            cost = self.finger_manager.get_total_cost()

            # Store the cost on the key (assuming similar interface to set_labels)
            key.set_labels((str(f"{cost:.2f}"),))

            # Reset finger manager for next key calculation
            self.finger_manager.reset()

        return self.physical_keyboard
