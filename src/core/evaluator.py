from src.core.distance_calculator import DistanceCalculator
from src.core.keyboard import Serial
from src.core.layout import Layout
from src.core.typer import Typer
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
from src.helpers.layouts.visualization import LayoutVisualization
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

    def render_layout(self, show_heatmap=False, dataset_file=None, dataset_name='simple_wikipedia'):
        """Render the keyboard layout.
        
        Args:
            show_heatmap: If True, show heatmap overlay with frequency data
            dataset_file: Path to frequency dataset file
            dataset_name: Name of dataset to use for heatmap
            
        Returns:
            Self for method chaining
        """
        if show_heatmap:
            # Load frequency data if not already loaded
            if not hasattr(self, 'dataset') or self.dataset_name != dataset_name:
                if dataset_file is None:
                    dataset_file = 'src/data/text/processed/frequency_analysis.pkl'
                
                try:
                    with open(dataset_file, 'rb') as f:
                        self.full_dataset = pickle.load(f)
                        self.dataset_name = dataset_name
                        self.dataset = self.full_dataset[dataset_name]
                        self._print(f"Loaded dataset: {dataset_name}")
                except FileNotFoundError:
                    print(f"Dataset file not found: {dataset_file}")
                    return self
                except KeyError:
                    print(f"Dataset '{dataset_name}' not found in frequency data")
                    return self
            
            LayoutVisualization(self.keyboard, self.layout).inspect(
                show_heatmap=True, 
                dataset_file=dataset_file, 
                dataset_name=dataset_name,
                dataset=self.dataset
            )
        else:
            LayoutVisualization(self.keyboard, self.layout).inspect()
        return self
    
    def render_heatmap(self, dataset_file=None, dataset_name='simple_wikipedia'):
        """Render the keyboard layout with automatic heatmap overlay.
        
        This method automatically loads frequency data and displays the keyboard with heatmap overlay.
        
        Args:
            dataset_file: Path to frequency dataset file (optional)
            dataset_name: Name of dataset to use for heatmap (default: 'simple_wikipedia')
            
        Returns:
            Self for method chaining
        """
        return self.render_layout(show_heatmap=True, dataset_file=dataset_file, dataset_name=dataset_name)

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
    # ev.layout.querty_based_remap(LAYOUT_DATA["dvorak"])
    # ev.layout.querty_based_remap(LAYOUT_DATA["asset"])
    # ev.layout._print_layout()
    ev.load_dataset(dataset_name='newsgroup')
    ev.load_typer()
