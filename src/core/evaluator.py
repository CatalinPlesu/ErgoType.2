from src.core.distance_calculator import DistanceCalculator
from src.core.keyboard import Serial
from src.core.layout import Layout
from src.core.typer import Typer
from src.core.simplified_typer import SimplifiedTyper
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
from src.helpers.layouts.visualization import LayoutVisualization
import pickle
import os
import hashlib
from src.config.file_paths import FITNESS_CACHE


class Evaluator:
    def __init__(self, debug=False):
        self.debug = debug
        self.use_simplified = False  # Will be set based on config
        self.fitness_cache = None
        self._load_fitness_cache()

    def _layout_to_chromosome(self, layout):
        """Convert layout to chromosome representation for caching"""
        # Get all character mappings from the layout mapper
        chromosome = []
        for (key_id, layer_id), key_obj in layout.mapper.data.items():
            if key_obj.key_type.name == 'CHAR' and hasattr(key_obj, 'value'):
                if isinstance(key_obj.value, tuple) and len(key_obj.value) >= 2:
                    # For CHAR type, use the character value
                    chromosome.append(key_obj.value[0])
                else:
                    chromosome.append(str(key_obj.value))
            else:
                chromosome.append(None)
        return tuple(chromosome)

    def _calculate_layout_hash(self, layout, dataset_name):
        """Calculate unique hash for layout + dataset combination"""
        chromosome = self._layout_to_chromosome(layout)
        hash_input = f"{chromosome}_{dataset_name}_{self.use_simplified}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    def _load_fitness_cache(self):
        """Load fitness cache from file"""
        from src.config.config import Config
        if not Config.cache.fitness_cache_enabled:
            return
            
        self._print("Loading fitness cache")
        try:
            if os.path.exists(FITNESS_CACHE):
                with open(FITNESS_CACHE, 'rb') as f:
                    self.fitness_cache = pickle.load(f)
                    self._print(f"✅ Successfully loaded fitness cache from {FITNESS_CACHE}")
            else:
                self.fitness_cache = {}
                self._print("Fitness cache file not found, starting fresh")
        except Exception as e:
            self._print(f"Error loading fitness cache: {e}")
            self.fitness_cache = {}

    def _save_fitness_cache(self):
        """Save fitness cache to file"""
        from src.config.config import Config
        if not Config.cache.fitness_cache_enabled:
            return
            
        self._print("Saving fitness cache")
        try:
            os.makedirs(os.path.dirname(FITNESS_CACHE), exist_ok=True)
            with open(FITNESS_CACHE, 'wb') as f:
                pickle.dump(self.fitness_cache, f)
                self._print(f"✅ Successfully saved fitness cache to {FITNESS_CACHE}")
        except Exception as e:
            self._print(f"Error saving fitness cache: {e}")

    def _get_cached_fitness(self, layout, dataset_name):
        """Get cached fitness value if available"""
        from src.config.config import Config
        if not Config.cache.fitness_cache_enabled or self.fitness_cache is None:
            return None
            
        layout_hash = self._calculate_layout_hash(layout, dataset_name)
        cached_data = self.fitness_cache.get(layout_hash)
        
        if cached_data is not None:
            self._print(f"🎯 Cache HIT for layout {layout_hash[:8]}...")
            return cached_data['fitness']
        else:
            self._print(f"❌ Cache MISS for layout {layout_hash[:8]}...")
            return None

    def _cache_fitness(self, layout, dataset_name, fitness):
        """Cache fitness value"""
        from src.config.config import Config
        if not Config.cache.fitness_cache_enabled:
            return
            
        layout_hash = self._calculate_layout_hash(layout, dataset_name)
        self.fitness_cache[layout_hash] = {
            'fitness': fitness,
            'timestamp': os.time() if hasattr(os, 'time') else 0
        }
        self._save_fitness_cache()
        if isinstance(fitness, dict):
            fitness_str = str(fitness)
        else:
            # Handle tuple format from simplified typer
            if isinstance(fitness, tuple) and len(fitness) == 2:
                distance, time_component = fitness
                fitness_str = f"({distance:.3f}, {time_component:.3f})"
            else:
                # Handle numeric fitness values
                try:
                    fitness_str = f"{fitness:.6f}"
                except (TypeError, ValueError):
                    fitness_str = str(fitness)
        self._print(f"💾 Cached fitness {fitness_str} for layout {layout_hash[:8]}...")

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
        """Calculate fitness with caching support"""
        from src.config.config import Config
        
        # Check cache first
        cached_fitness = self._get_cached_fitness(self.layout, self.dataset_name)
        if cached_fitness is not None:
            return cached_fitness
            
        # Calculate fitness if not cached
        if self.use_simplified:
            fitness = self.typer.fitness()
        else:
            # Legacy fitness calculation
            if hasattr(self.typer, 'fitness'):
                fitness = self.typer.fitness()
            else:
                # Fallback for older typer implementations
                fitness = self.typer.calculate_word_fitness()[0]
                
        # Cache the result
        self._cache_fitness(self.layout, self.dataset_name, fitness)
        
        return fitness

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
        # Import config here to avoid circular imports
        from src.config.config import Config
        self.use_simplified = Config.fitness.use_simplified_fitness
        
        if self.use_simplified:
            self.typer = SimplifiedTyper(self.keyboard, self.distance, self.layout,
                                       self.dataset, self.dataset_name, debug=self.debug)
            self._print("Using SimplifiedTyper for fitness calculation")
        else:
            self.typer = Typer(self.keyboard, self.distance, self.layout,
                             self.dataset, debug=self.debug)
            self._print("Using legacy Typer for fitness calculation")
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
