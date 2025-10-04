import sys
from src.core.keyboard import Key, Keyboard, KeyboardMetadata, Serial
from src.core.distance_calculator import DistanctCalculator


class Evaluator:
    def __init__(self, debug=False):
        self.debug = debug
        pass

    def load_keyoard(self, keyboard_file='src/data/keyboards/ansi_60_percent.json'):
        with open(keyboard_file, 'r') as f:
            self._print(f"Read file: '{keyboard_file}'")
            self.keyboard_file = keyboard_file
            self.keyboard = Serial.parse(f.read())
        return self

    def load_distance(self):
        self._print("Calculating distance")
        self.distance = DistanctCalculator(
            self.keyboard_file, self.keyboard, debug=self.debug)
        return self

    def load_layout(self):
        return self

    def load_mapper(self):
        return self

    def get_fitness(self):
        pass

    def render_layout(self):
        pass

    def _print(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)


# keyboard = Keyboard(keyboard_file)
# phisical_key_cost = RawDistanceCalculator(keyboard_file)
# layout = Layout(keyboard, langauage, maping)
# test
if __name__ == "__main__":
    ev = Evaluator(debug=True).load_keyoard().load_distance()
