from src.core.keyboard import Key, Keyboard, KeyboardMetadata, Serial
from src.helpers.keyboards.renderer import show_keyboard, render_keyboard, render_keyboard_with_heatmap
from src.core.mapper import KeyType
import pickle
import os
from typing import Dict, List, Tuple, Optional
import math

# Mock dependencies if not available
try:
    import svgwrite
    SVGWRITE_AVAILABLE = True
except ImportError:
    SVGWRITE_AVAILABLE = False
    # Create minimal mock for svgwrite
    class MockSvgwrite:
        class Drawing:
            def __init__(self, filename, size):
                self.filename = filename
                self.size = size
            def add(self, element):
                pass
            def save(self):
                print(f"SVG would be saved to {self.filename}")
    svgwrite = MockSvgwrite()

# Mock IPython if not available
try:
    from IPython.display import SVG, display
except ImportError:
    class MockSVG:
        def __init__(self, content):
            self.content = content
    def display(obj):
        print(f"Display: {obj}")
    SVG = MockSVG


class LayoutVisualization:
    def __init__(self, keyboard, layout=None):
        self.keyboard = keyboard
        self.layout = layout

    def inspect(self, layers=None, show_heatmap=False, dataset_file=None, dataset_name='simple_wikipedia', dataset=None):
        if layers is None:
            layers = []
            if self.layout and hasattr(self.layout, 'mapper') and hasattr(self.layout.mapper, 'data'):
                for key_id, layer_idx in self.layout.mapper.data.keys():
                    if layer_idx not in layers:
                        layers.append(layer_idx)
            # Default to layer 0 if no data
            layers = sorted(layers) if layers else [0]

        if show_heatmap:
            # Load frequency data for heatmap
            if dataset is None:
                if dataset_file is None:
                    dataset_file = 'src/data/text/processed/frequency_analysis.pkl'
                
                if not os.path.exists(dataset_file):
                    print(f"Dataset file not found: {dataset_file}")
                    return
                
                try:
                    with open(dataset_file, 'rb') as f:
                        full_dataset = pickle.load(f)
                    
                    if dataset_name not in full_dataset:
                        print(f"Dataset '{dataset_name}' not found in frequency data")
                        return
                    
                    dataset = full_dataset[dataset_name]
                except Exception as e:
                    print(f"Error loading dataset: {e}")
                    return
            
            char_frequencies = dataset.get('character_frequencies', {})
            
            # Generate keyboard with heatmap for each layer
            keyboard_svgs = []
            for layer_idx in layers:
                # Set labels for this layer (same logic as non-heatmap path)
                for key_obj in self.keyboard.keys:
                    key_obj.clear_labels()
                for key_obj in self.keyboard.keys:
                    key_id = key_obj.id
                    
                    if (key_id, layer_idx) in self.layout.mapper.data:
                        key_data = self.layout.mapper.data[(key_id, layer_idx)]
                        if key_data.key_type == KeyType.CHAR:
                            key_obj.set_labels(key_data.value)
                        elif key_data.key_type in [KeyType.SPECIAL_CHAR, KeyType.CONTROL, KeyType.LAYER]:
                            if isinstance(key_data.value, tuple):
                                key_obj.set_labels((key_data.value[1],) if len(
                                    key_data.value) > 1 else (key_data.value[0],))
                            else:
                                key_obj.set_labels((key_data.value,))
                
                # Generate keyboard with heatmap for this layer
                keyboard_svg = self.render_keyboard_with_heatmap(char_frequencies, layer_idx=layer_idx)
                keyboard_svgs.append(keyboard_svg)
            
            # Display all keyboard SVGs
            for svg in keyboard_svgs:
                display(svg)
            
            return keyboard_svgs
        else:
            # Original behavior without heatmap
            def render_layer(layer_idx):
                print(f"--- Layer {layer_idx} ---")
                for key_obj in self.keyboard.keys:
                    key_obj.clear_labels()
                for key_obj in self.keyboard.keys:
                    key_id = key_obj.id

                    if (key_id, layer_idx) in self.layout.mapper.data:
                        key_data = self.layout.mapper.data[(key_id, layer_idx)]
                        if key_data.key_type == KeyType.CHAR:
                            key_obj.set_labels(key_data.value)
                        elif key_data.key_type in [KeyType.SPECIAL_CHAR, KeyType.CONTROL, KeyType.LAYER]:
                            if isinstance(key_data.value, tuple):
                                key_obj.set_labels((key_data.value[1],) if len(
                                    key_data.value) > 1 else (key_data.value[0],))
                            else:
                                key_obj.set_labels((key_data.value,))
                show_keyboard(self.keyboard)

            for layer_idx in layers:
                render_layer(layer_idx)

    def render_keyboard_with_heatmap(self, char_frequencies: Dict, layer_idx: int = 0) -> SVG:
        """Render keyboard with heatmap overlay showing character usage frequency"""
        # Normalize frequency values
        if char_frequencies:
            max_freq = max(freq['relative'] for freq in char_frequencies.values())
            min_freq = min(freq['relative'] for freq in char_frequencies.values())
            freq_range = max_freq - min_freq if max_freq > min_freq else 1.0
        else:
            max_freq = 1.0
            min_freq = 0.0
            freq_range = 1.0
        
        # Create a modified keyboard renderer that includes heatmap
        return render_keyboard_with_heatmap(self.keyboard, char_frequencies, layer_idx, freq_range, min_freq, self.layout)
    
    def get_key_color_for_frequency(self, normalized_freq: float) -> str:
        """Get color based on normalized frequency (0-1)"""
        # Color gradient from blue (low) to red (high)
        red = int(255 * normalized_freq)
        blue = int(255 * (1 - normalized_freq))
        green = int(128 * (1 - abs(normalized_freq - 0.5) * 2))  # Peak at middle
        return f"#{red:02x}{green:02x}{blue:02x}"
