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


class Typer:
    def __init__(self, keyboard, distance, layout, dataset, debug=False):
        self.debug = debug
        self._print("Typer initiated")
        self.keyboard = keyboard
        self.distance = distance
        self.layout = layout
        self.dataset = dataset
        self.fitness(words=False)

    def fitness(self, words=True, symbols=True, fluid_typing=False):
        match (words, symbols, fluid_typing):
            case (False, True, False):
                self._print("Only Symbols")
                self.fitness_symbol_simple()
            case (True, True, False):
                self._print("Words and Symbols")
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
        print(f"unshifted {unshifted}")
        print(f"shifted {shifted}")

        shift_keys = self.layout.mapper.filter_data(
            lambda key_id, layer_id, value: value.key_type == KeyType.CONTROL and value.value == 'Shift')

        shift_key = None
        print(f"shift keys {shift_keys}")

        for key, value in self.dataset[Config.dataset.field_character_frequencies].items():
            # print(key, value)
            relative = value[Config.dataset.field_category_frequencies_relative] * 100
            total_percentage += relative
            # data = self.layout.mapper.filter_data(
            #     lambda key_id, layer_id, value:  key in value)
            key_id, layer, qmk_key = self.layout.find_key_for_char(key)
            print(key_id, layer)
            if key in shifted:
                for shift in shift_keys:
                    shift_id, _ = shift
                    if self.keyboard.keys[key_id].hand != self.keyboard.keys[shift_id[0]].hand:
                        shift_key = shift
                        break
            print(f""" key {key} - key_id {key_id} """)
            if shift_key is not None:
                print(f""" shift - key_id {shift_key[0][0]} """)

        print(f"""Total percentage of key pressed is '{
              total_percentage}', it should be almost 100""")

    def _print(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)


if __name__ == "__main__":
    pass
