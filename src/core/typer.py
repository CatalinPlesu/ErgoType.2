"""
This class will be responsible for handling the simulation logic, of typing words and symbols
Stateful Simulation: Tracks finger positions across key presses, resetting Shift key positions after each n-gram.
Parallel Typing: Handles simultaneous key presses (e.g., Shift + 'a' for 'A') by including Shift in the key sequence for uppercase characters.
N-gram Support: Uses unigrams, bigrams, or higher-order n-grams to optimize cost calculations, weighted by frequency.
Efficiency: Supports random sampling of words to reduce computation time for large datasets.
Extensibility: Can incorporate additional cost factors (e.g., finger effort, alternation penalties) by modifying _simulate_word.
"""

from src.config.config import Config
from src.core.mapper import KeyType
from src.core.keyboard import FingerName, enums_to_fingername, fingername_to_enums, Hand
from collections import Counter

HOMING_POSITION = 'homing'
CURRENT_POSITION = 'current'
USE_HOMING = 'use_homing'
USE_NON_HOMING = 'use_non_homing'


class Typer:
    def __init__(self, keyboard, distance, layout, dataset, debug=False):
        self.debug = debug
        self._print("Typer initiated")
        self.keyboard = keyboard
        self.distance = distance
        self.layout = layout
        self.dataset = dataset
        self.load_finger_positions()

    def load_finger_positions(self):
        """Initialize finger positions and counters"""
        self.finger = {finger:
                       {HOMING_POSITION: self.keyboard.get_homing_key_for_finger_name(
                           finger).id} for finger in FingerName}

        for finger in self.finger:
            self.finger[finger][USE_HOMING] = 0
            self.finger[finger][USE_NON_HOMING] = 0

        self.reset_finger_position()

    def reset_finger_position(self):
        """Reset all fingers to homing position"""
        for finger in self.finger:
            self.finger[finger][CURRENT_POSITION] = self.finger[finger][HOMING_POSITION]
        self.moved_fingers = []
        self.last_key_x = None
        self.last_hand = None

    def move_finger(self, finger, key_to):
        """Move a single finger and update counters"""
        if self.finger[finger][HOMING_POSITION] == key_to:
            self.finger[finger][USE_HOMING] += 1
        else:
            self.finger[finger][USE_NON_HOMING] += 1

        key_from = self.finger[finger][CURRENT_POSITION]
        self.finger[finger][CURRENT_POSITION] = key_to
        d, m = self.distance.get_distance_and_movement(key_from, key_to)
        return d

    def move_fingers_home(self):
        """Move all fingers back to homing position"""
        self.moved_fingers = []
        total = 0
        for finger in self.finger:
            homing_key = self.finger[finger][HOMING_POSITION]
            total += self.move_finger(finger, homing_key)
        return total

    def move_finger_stateful(self, finger, key_to):
        """Move finger with n-gram detection (same finger reuse)"""
        extra_distance = 0
        ngram = None

        if finger in self.moved_fingers:
            ngram = len(self.moved_fingers)
            extra_distance += self.move_fingers_home()

        if self.finger[finger][HOMING_POSITION] == key_to:
            self.finger[finger][USE_HOMING] += 1
        else:
            self.finger[finger][USE_NON_HOMING] += 1

        self.moved_fingers.append(finger)
        key_from = self.finger[finger][CURRENT_POSITION]
        self.finger[finger][CURRENT_POSITION] = key_to
        distance, _ = self.distance.get_distance_and_movement(key_from, key_to)
        return (distance + extra_distance, ngram)

    def move_finger_fluid(self, finger, key_to):
        """
        Move finger with fluid typing detection (alternating hands moving inward).
        Detects when typing alternates between hands and both hands move inward.
        """
        extra_distance = 0
        fluid_ngram = None

        # Get current key position and hand
        current_key = self.keyboard.keys[key_to]
        current_x = current_key.x
        _, current_hand = fingername_to_enums(finger)

        # Check for fluid typing pattern
        if self.last_key_x is not None and self.last_hand is not None:
            # Check if hands alternate
            if current_hand != self.last_hand:
                # Check if both hands are moving inward
                left_moving_right = (
                    self.last_hand == Hand.LEFT and current_x > self.last_key_x)
                right_moving_left = (
                    self.last_hand == Hand.RIGHT and current_x < self.last_key_x)

                if left_moving_right or right_moving_left:
                    fluid_ngram = len(self.moved_fingers)
                    extra_distance += self.move_fingers_home()

        # Check for same-finger reuse (traditional n-gram)
        if finger in self.moved_fingers and fluid_ngram is None:
            fluid_ngram = len(self.moved_fingers)
            extra_distance += self.move_fingers_home()

        # Update counters
        if self.finger[finger][HOMING_POSITION] == key_to:
            self.finger[finger][USE_HOMING] += 1
        else:
            self.finger[finger][USE_NON_HOMING] += 1

        self.moved_fingers.append(finger)
        key_from = self.finger[finger][CURRENT_POSITION]
        self.finger[finger][CURRENT_POSITION] = key_to
        distance, _ = self.distance.get_distance_and_movement(key_from, key_to)

        # Update tracking for next iteration
        self.last_key_x = current_x
        self.last_hand = current_hand

        return (distance + extra_distance, fluid_ngram)

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
        # Find layer 1 characters
        layer1_chars = self.layout.get_altgr_symbols()

        if char not in layer1_chars:
            return None

        # Find the base key for this character
        base_key_for_char = self.layout.find_key_for_char(char)
        if not base_key_for_char:
            return None
        
        base_char_key_id = base_key_for_char[0]
        base_key = self.keyboard.keys[base_char_key_id]
        
        # Find AltGr key - prefer opposite hand, but if not available, use same hand
        for altgr_item in altgr_keys:
            # altgr_item is ((key_id, layer_id), value)
            altgr_key_tuple = altgr_item[0]  # Get (key_id, layer_id)
            altgr_key_id = altgr_key_tuple[0]  # Get key_id
            altgr_key = self.keyboard.keys[altgr_key_id]
            
            # Prefer opposite hand (like shift)
            if base_key.hand != altgr_key.hand:
                return altgr_key_id
        
        # If no opposite hand AltGr key found, use any available AltGr key
        for altgr_item in altgr_keys:
            altgr_key_tuple = altgr_item[0]  # Get (key_id, layer_id)
            altgr_key_id = altgr_key_tuple[0]  # Get key_id
            return altgr_key_id

        return None

    def get_finger_for_key(self, key_id):
        """Get the finger name for a key"""
        fingername = enums_to_fingername(
            self.keyboard.keys[key_id].finger,
            self.keyboard.keys[key_id].hand
        )
        if isinstance(fingername, list):
            fingername = fingername[0]
        return fingername

    def type_char_simple(self, char, shift_keys, altgr_keys):
        """Type a single character without state tracking"""
        key_id, layer, qmk_key = self.layout.find_key_for_char(char)
        
        # If character not found in layout, return large distance penalty
        if key_id is None:
            return 1000.0
        
        distance = 0

        # Handle shift if needed
        shift_key_id = self.get_shift_key_for_char(char, key_id, shift_keys)
        if shift_key_id is not None:
            shift_finger = self.get_finger_for_key(shift_key_id)
            distance += self.move_finger(shift_finger, shift_key_id)

        # Handle AltGr if needed (layer 1)
        altgr_key_id = None
        if layer == 1:  # ALTGR_LAYER
            altgr_key_id = self.get_altgr_key_for_char(char, key_id, altgr_keys)
            if altgr_key_id is not None:
                altgr_finger = self.get_finger_for_key(altgr_key_id)
                distance += self.move_finger(altgr_finger, altgr_key_id)

        # Type the character
        finger = self.get_finger_for_key(key_id)
        distance += self.move_finger(finger, key_id)

        return distance

    def type_char_fluid(self, char, shift_keys, altgr_keys):
        """Type a single character with fluid typing detection"""
        key_id, layer, qmk_key = self.layout.find_key_for_char(char)
        
        # If character not found in layout, return large distance penalty
        if key_id is None:
            return 1000.0, 0.0
            
        distance = 0
        ngram = None

        # Handle shift if needed
        shift_key_id = self.get_shift_key_for_char(char, key_id, shift_keys)
        if shift_key_id is not None:
            shift_finger = self.get_finger_for_key(shift_key_id)
            distance += self.move_finger(shift_finger, shift_key_id)

        # Handle AltGr if needed (layer 1)
        altgr_key_id = None
        if layer == 1:  # ALTGR_LAYER
            altgr_key_id = self.get_altgr_key_for_char(char, key_id, altgr_keys)
            if altgr_key_id is not None:
                altgr_finger = self.get_finger_for_key(altgr_key_id)
                distance += self.move_finger(altgr_finger, altgr_key_id)

        # Type the character with fluid tracking
        finger = self.get_finger_for_key(key_id)
        char_distance, ngram = self.move_finger_fluid(finger, key_id)
        distance += char_distance

        return distance, ngram

    def calculate_scaled_character_fitness(self):
        """Scale character score to represent remaining typing after words"""
        shift_keys = self.layout.mapper.filter_data(
            lambda key_id, layer_id, value: value.key_type == KeyType.CONTROL and value.value == 'Shift')
        
        altgr_keys = self.layout.mapper.filter_data(
            lambda key_id, layer_id, value: value.key_type == KeyType.LAYER and value.value == 'AltGr')

        char_freq = self.dataset[Config.dataset.field_character_frequencies]
        words = self.dataset[Config.dataset.field_word_frequencies]

        # Calculate how much of typing is done by words
        total_word_percentage = sum(word_data[Config.dataset.field_word_frequencies_relative] * 100
                                    for word_data in words)

        # Calculate remaining percentage for characters (100% - word percentage)
        remaining_percentage = 100.0 - total_word_percentage

        # Calculate character score weighted by their relative frequencies
        total_char_score = 0
        total_char_percentage = 0

        for char, value in char_freq.items():
            percentage = value[Config.dataset.field_category_frequencies_relative] * 100
            total_char_percentage += percentage

            distance = self.type_char_simple(char, shift_keys, altgr_keys)
            # Weight the character distance by its frequency
            weighted_distance = distance * percentage
            total_char_score += weighted_distance

            self.reset_finger_position()

        # Now scale the character score to represent what it would be
        # if characters filled the remaining typing percentage (remaining_percentage)
        if total_char_percentage > 0:
            # Scale character score to match the remaining typing percentage
            scale_factor = remaining_percentage / total_char_percentage
            scaled_score = total_char_score * scale_factor
        else:
            scaled_score = 0

        return scaled_score, remaining_percentage

    def calculate_word_fitness(self):
        """Calculate fitness for word frequencies with fluid typing detection"""
        shift_keys = self.layout.mapper.filter_data(
            lambda key_id, layer_id, value: value.key_type == KeyType.CONTROL and value.value == 'Shift')
        
        altgr_keys = self.layout.mapper.filter_data(
            lambda key_id, layer_id, value: value.key_type == KeyType.LAYER and value.value == 'AltGr')

        words = self.dataset[Config.dataset.field_word_frequencies]
        total_percentage = 0
        total_score = 0
        ngrams = []

        for word_data in words:
            word = word_data[Config.dataset.field_word_frequencies_word]
            percentage = word_data[Config.dataset.field_word_frequencies_relative] * 100
            total_percentage += percentage

            self._print(f"Processing: {word} ({percentage:.4f}%)")
            self.reset_finger_position()

            for char in word:
                distance, ngram = self.type_char_fluid(char, shift_keys, altgr_keys)

                # Weight by the word's frequency
                weighted_distance = distance * percentage
                total_score += weighted_distance  # Weighted by word frequency

                if ngram:
                    ngrams.append(ngram)
                    self._print(f"  N-gram detected: {ngram}")

        return total_score, total_percentage, Counter(ngrams)

    def calculate_ngram_score(self, ngram_counter):
        """Calculate normalized n-gram score"""
        if not ngram_counter:
            return 1.0

        score = 0
        ngram_sum = sum(ngram_counter.values()) * 8

        for k, v in ngram_counter.items():
            score -= v * k * Config.fitness.n_gram_multiplier

        score = 1 - max(0, score * -1) / ngram_sum
        return score

    def calculate_homing_score(self):
        """Calculate unified homing key usage score as weighted average percentage"""
        total_presses = 0
        total_homing = 0

        for finger in self.finger:
            homing = self.finger[finger][USE_HOMING]
            non_homing = self.finger[finger][USE_NON_HOMING]
            total = homing + non_homing

            total_presses += total
            total_homing += homing

        if total_presses == 0:
            return 0.0

        return (total_homing / total_presses)

    def fitness(self):
        """Main fitness calculation with fluid typing"""
        word_score, word_percentage, ngram_counter = self.calculate_word_fitness()
        scaled_char_score, char_percentage = self.calculate_scaled_character_fitness()
        ngram_score = self.calculate_ngram_score(ngram_counter)
        homing_score = self.calculate_homing_score()

        distance_score = word_score + scaled_char_score

        self._print(f"\n=== Fluid Typing Fitness ===")
        self._print(f"Word coverage: {word_percentage:.2f}%")
        self._print(f"Character coverage (scaled): {char_percentage:.2f}%")
        self._print(f"\nWord distance: {word_score:.2f}")
        self._print(f"Scaled character distance: {scaled_char_score:.2f}")
        self._print(f"Total distance: {distance_score:.2f}")
        self._print(f"\nN-grams detected: {ngram_counter}")
        self._print(f"N-gram score: {ngram_score:.4f}")
        self._print(f"Homing usage: {homing_score:.2f}%")

        return {
            'distance_score': distance_score,
            'ngram_score': ngram_score,
            'homing_score': homing_score
        }

    def _print(self, *args, **kwargs):
        """Debug printing"""
        if self.debug:
            print(*args, **kwargs)


if __name__ == "__main__":
    pass
