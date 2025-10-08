from src.core.distance_calculator import DistanceCalculator
from src.core.keyboard import Serial
from src.core.layout import Layout
from src.helpers.layouts.visualization import LayoutVisualization
from src.core.typer import Typer
import pickle


class Evaluator:
    def __init__(self, debug=False):
        self.debug = debug

    def load_keyoard(self,
                     keyboard_file='src/data/keyboards/ansi_60_percent.json'):
        with open(keyboard_file, 'r') as f:
            self._print(f"Read file: '{keyboard_file}'")
            self.keyboard_file = keyboard_file
            self.keyboard = Serial.parse(f.read())
        return self

    def load_distance(self):
        self._print("Calculating distance")
        self.distance = DistanceCalculator(
            self.keyboard_file, self.keyboard, debug=self.debug)
        return self

    def load_layout(self):
        self.layout = Layout(self.keyboard, debug=self.debug)
        return self

    def get_fitness(self):
        return self

    def render_layout(self):
        LayoutVisualization(self.keyboard, self.layout).inspect()
        return self

    def load_dataset(self,
                     dataset_file='src/data/text/processed/frequency_analysis.pkl',
                     dataset_name='simple_wikipedia'):
        with open(dataset_file, 'rb') as f:
            self._print("Dataset loaded successfully")
            self.full_dataset = pickle.load(f)
            self.dataset_name = dataset_name
            self.dataset = self.full_dataset[self.dataset_name]
        return self

    def load_typer(self):
        self.typer = Typer(self.keyboard, self.distance, self.layout,
                           self.dataset, debug=self.debug)
        return self

    def _print(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)


if __name__ == "__main__":
    ev = Evaluator(debug=True).load_keyoard().load_distance().load_layout()
    ev.load_dataset()
    ev.load_typer()
