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
from src.core.keyboard import FingerName, enums_to_fingername
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
        self.fitness()

    def load_finger_positions(self):
        self.finger = {finger:
                       {HOMING_POSITION: self.keyboard.get_homing_key_for_finger_name(
                           finger).id} for finger in FingerName}

        for finger in self.finger:
            self.finger[finger][USE_HOMING] = 0

        for finger in self.finger:
            self.finger[finger][USE_NON_HOMING] = 0

        self.reset_finger_position()

    def reset_finger_position(self):
        for finger in self.finger:
            self.finger[finger][CURRENT_POSITION] = self.finger[finger][HOMING_POSITION]
        self.moved_fingers = []

    def move_finger(self, finger, key_to):
        # self.moved_fingers.append(finger)

        if self.finger[finger][HOMING_POSITION] == key_to:
            self.finger[finger][USE_HOMING] += 1
        else:
            self.finger[finger][USE_NON_HOMING] += 1

        key_from = self.finger[finger][CURRENT_POSITION]
        self.finger[finger][CURRENT_POSITION] = key_to
        d, m = self.distance.get_distance_and_movement(key_from, key_to)
        return d

    def move_fingers_home(self):
        self.moved_fingers = []
        sum = 0
        for finger in self.finger:
            homing_key = self.finger[finger][HOMING_POSITION]
            sum += self.move_finger(finger, homing_key)
        return sum

    # moved_fingers represnt the bigram
    def move_finger_stateful(self, finger, key_to):
        sum = 0
        ngram = None
        if finger in self.moved_fingers:
            ngram = len(self.moved_fingers)
            sum += self.move_fingers_home()

        if self.finger[finger][HOMING_POSITION] == key_to:
            self.finger[finger][USE_HOMING] += 1
        else:
            self.finger[finger][USE_NON_HOMING] += 1

        self.moved_fingers.append(finger)
        key_from = self.finger[finger][CURRENT_POSITION]
        self.finger[finger][CURRENT_POSITION] = key_to
        distance, _ = self.distance.get_distance_and_movement(key_from, key_to)
        return (distance+sum, ngram)

    def fitness(self, words=True, symbols=True, fluid_typing=False):
        match (words, symbols, fluid_typing):
            case (False, True, False):
                self._print("Only Symbols")
                self.fitness_symbol_simple()
            case (True, True, False):
                self._print("Words and Symbols")
                self.fitness_with_words()
            case (True, True, True):
                self._print("Fluid Words and Symbols")
            case _:
                self._print("Other case")

        pass

    def fitness_symbol_simple(self):
        total_percentage = 0
        score = 0
        unshifted = self.layout.get_unshifted_symbols()
        shifted = self.layout.get_shifted_symbols()
        # print(f"unshifted {unshifted}")
        # print(f"shifted {shifted}")

        shift_keys = self.layout.mapper.filter_data(
            lambda key_id, layer_id, value: value.key_type == KeyType.CONTROL and value.value == 'Shift')

        shift_key = None
        shift_key_id = None
        # print(f"shift keys {shift_keys}")

        for key, value in self.dataset[Config.dataset.field_character_frequencies].items():
            # print(key, value)
            relative = value[Config.dataset.field_category_frequencies_relative] * 100
            total_percentage += relative
            # data = self.layout.mapper.filter_data(
            #     lambda key_id, layer_id, value:  key in value)
            # print(f"seraching for charater '{key}'")
            key_id, layer, qmk_key = self.layout.find_key_for_char(key)
            # print(key_id, layer)
            if key in shifted:
                for shift in shift_keys:
                    shift_id, _ = shift
                    if self.keyboard.keys[key_id].hand != self.keyboard.keys[shift_id[0]].hand:
                        shift_key = shift
                        break
            # print(f""" key {key} - key_id {key_id} """)
            if shift_key is not None:
                shift_key_id = shift_key[0][0]
                # print(f""" shift - key_id {shift_key_id} """)

                fingername = enums_to_fingername(
                    self.keyboard.keys[shift_key_id].finger, self.keyboard.keys[shift_key_id].hand)
                if isinstance(fingername, list):
                    fingername = fingername[0]
                score += self.move_finger(fingername, shift_key_id)

            fingername = enums_to_fingername(
                self.keyboard.keys[key_id].finger, self.keyboard.keys[key_id].hand)
            if isinstance(fingername, list):
                fingername = fingername[0]
            score += self.move_finger(fingername, key_id)
            self.reset_finger_position()

        print(f"""Total percentage of key pressed is '{
              total_percentage}', it should be almost 100""")
        print(f"""Total score {score}""")

    def fitness_with_words(self):
        total_percentage = 0
        score = 0
        unshifted = self.layout.get_unshifted_symbols()
        shifted = self.layout.get_shifted_symbols()
        ngrams = []
        # print(f"unshifted {unshifted}")
        # print(f"shifted {shifted}")

        shift_keys = self.layout.mapper.filter_data(
            lambda key_id, layer_id, value: value.key_type == KeyType.CONTROL and value.value == 'Shift')

        shift_key = None
        shift_key_id = None
        # print(f"shift keys {shift_keys}")
        words = self.dataset[Config.dataset.field_word_frequencies]
        i = 0
        for word in words:
            i += 1
            print(word)
            word, percentage = (word[Config.dataset.field_word_frequencies_word],
                                word[Config.dataset.field_word_frequencies_relative] * 100)
            total_percentage += percentage
            print(word, percentage)

            shift_key = None
            shift_key_id = None
            for key in word:
                key_id, layer, qmk_key = self.layout.find_key_for_char(key)
                if key in shifted:
                    for shift in shift_keys:
                        shift_id, _ = shift
                        if self.keyboard.keys[key_id].hand != self.keyboard.keys[shift_id[0]].hand:
                            shift_key = shift
                            break
                if shift_key is not None:
                    shift_key_id = shift_key[0][0]

                    fingername = enums_to_fingername(
                        self.keyboard.keys[shift_key_id].finger, self.keyboard.keys[shift_key_id].hand)
                    if isinstance(fingername, list):
                        fingername = fingername[0]
                    score += self.move_finger(fingername, shift_key_id)

                fingername = enums_to_fingername(
                    self.keyboard.keys[key_id].finger, self.keyboard.keys[key_id].hand)
                if isinstance(fingername, list):
                    fingername = fingername[0]
                distance, ngram = self.move_finger_stateful(fingername, key_id)
                print(distance, ngram)
                score += distance
                if ngram:
                    ngrams.append(ngram)

        char_freq = self.dataset[Config.dataset.field_character_frequencies]
        chart_total_percentage = 0
        char_score = 0
        for key, value in char_freq.items():
            percentage = char_freq[key][Config.dataset.field_word_frequencies_relative] * 100
            chart_total_percentage += percentage

            key_id, layer, qmk_key = self.layout.find_key_for_char(key)
            if key in shifted:
                for shift in shift_keys:
                    shift_id, _ = shift
                    if self.keyboard.keys[key_id].hand != self.keyboard.keys[shift_id[0]].hand:
                        shift_key = shift
                        break
            if shift_key is not None:
                shift_key_id = shift_key[0][0]

                fingername = enums_to_fingername(
                    self.keyboard.keys[shift_key_id].finger, self.keyboard.keys[shift_key_id].hand)
                if isinstance(fingername, list):
                    fingername = fingername[0]
                char_score += self.move_finger(fingername, shift_key_id)

            fingername = enums_to_fingername(
                self.keyboard.keys[key_id].finger, self.keyboard.keys[key_id].hand)
            if isinstance(fingername, list):
                fingername = fingername[0]
            char_score += self.move_finger(fingername, key_id)
            self.reset_finger_position()

        print(f"""Total percentage of key pressed is '{
              total_percentage}' + '{chart_total_percentage}', it should be almost 100""")
        print(f"""Total words score {score}""")
        print(f"""Total chars score {char_score}""")
        print(f"""Ngrams {Counter(ngrams)}""")
        ngram_score = self.score_ngrams(Counter(ngrams))
        print(f"""Ngrams_score {ngram_score}""")

        for finger in self.finger:
            print(finger)
            print(f"homing use: {self.finger[finger][USE_HOMING]}")
            print(f"not homing use: {self.finger[finger][USE_NON_HOMING]}")

    def score_ngrams(self, ngarms_counter):
        score = 0
        ngram_sum = sum(ngarms_counter.values()) * 8
        for k, v in ngarms_counter.items():
            score -= v * k * Config.fitness.n_gram_multiplier
        score = 1 - max(0, score * -1) / ngram_sum
        return score

    def _print(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)


if __name__ == "__main__":
    pass
