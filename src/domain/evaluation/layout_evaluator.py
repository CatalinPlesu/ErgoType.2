from src.domain.keyboard import Keyboard
from src.domain.hand_finger_enum import FingerName, Hand
from src.domain.layout_phenotype import LayoutPhenotype
from src.data_helpers.keyboards.layout_visualization import LayoutVisualization
from src.domain.key_mapper import KeyMapper
from collections import defaultdict
import string
import random
import math
from src.config.finger_strength import FINGER_BIAS

class KeyboardPhenotype:
    def __init__(self, physical_keyboard, remap=None, cost_pipeline=None):
        print("Init keyboard phenotype")
        self.remap_keys = {}
        self.physical_keyboard = physical_keyboard
        
        # Create cost calculator with pipeline
        if cost_pipeline is None:
            cost_pipeline = create_default_pipeline()
        self.cost_calculator = CostCalculatorPlugin(cost_pipeline)
        
        # Pass calculator to finger manager
        self.finger_manager = FingerManager(
            self.physical_keyboard, 
            self.cost_calculator
        )
        
        # Create layout phenotype instance
        self.layout = LayoutPhenotype()
        
        # If remap is provided, apply the language configuration
        if remap is not None:
            self.layout.apply_language_layout(remap)
        
        # Create key mapper
        self.key_mapper = KeyMapper(self.physical_keyboard, self.layout)
        
        # Track which keys are used during fitness calculation
        self.used_physical_keys = set()
        self.unreachable_chars = set()

        self.visualizer = LayoutVisualization(self.physical_keyboard, self.layout)
        self.visualizer.set_layout(self.layout, self.key_mapper)

    def select_remap_keys(self, keys_list):
        self.remap_keys = dict()
        self.remap_key_length = len(keys_list)
        self.original_key_list = keys_list

    def remap_to_keys(self, keys_list):
        if self.remap_key_length != len(keys_list):
            print("remap key list doesn't match in length")
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
            dataset_frequency_ Single dataset from the frequency analysis (not the full results dict)
            total_simulated_presses: Total number of presses to simulate
        """
        self.finger_manager.reset()
        self.used_physical_keys.clear()
        self.unreachable_chars.clear()

        # Extract word frequencies (top words)
        word_frequencies = dataset_frequency_data['word_frequencies']
        char_frequencies = dataset_frequency_data['character_frequencies']

        # Calculate total word frequency for normalization
        total_word_freq = sum(word_data['absolute']
                              for word_data in word_frequencies)
        total_char_freq = sum(data['absolute']
                              for data in char_frequencies.values())

        dataset_chars = set()
        
        # Process top words
        word_presses_budget = total_simulated_presses * 0.7
        top_words = word_frequencies[:5000]

        for word_data in top_words:
            word = word_data['word']
            word_frequency = word_data['absolute']
            word_presses = (word_frequency / total_word_freq) * word_presses_budget

            for i, char in enumerate(word):
                char_lower = char.lower()
                dataset_chars.add(char_lower)

                key_sequence = self.layout.get_key_sequence(char_lower)
                if key_sequence:
                    for key_name in key_sequence:
                        physical_key = self.key_mapper.get_physical_key(key_name)
                        if physical_key:
                            self.finger_manager.press(physical_key, word_presses)
                            self.used_physical_keys.add(physical_key)
                        else:
                            print(f"Warning: No physical key found for virtual key '{key_name}'")
                            if key_name not in ['Shift', 'AltGr', 'Space', 'Tab', 'Enter', 'Backspace', 'Caps Lock', 'Ctrl', 'Win', 'Alt', 'Menu']:
                                self.unreachable_chars.add(char_lower)
                else:
                    self.unreachable_chars.add(char_lower)

            self.finger_manager.reset_position()

        # Process individual characters (remaining 30% of presses)
        char_presses_budget = total_simulated_presses * 0.3

        for char, char_data in char_frequencies.items():
            char_frequency = char_data['absolute']
            char_presses = (char_frequency / total_char_freq) * char_presses_budget
            
            dataset_chars.add(char)

            key_sequence = self.layout.get_key_sequence(char)
            if key_sequence:
                for key_name in key_sequence:
                    physical_key = self.key_mapper.get_physical_key(key_name)
                    if physical_key:
                        self.finger_manager.press(physical_key, char_presses)
                        self.used_physical_keys.add(physical_key)
                    else:
                        print(f"Warning: No physical key found for virtual key '{key_name}'")
                        if key_name not in ['Shift', 'AltGr', 'Space', 'Tab', 'Enter', 'Backspace', 'Caps Lock', 'Ctrl', 'Win', 'Alt', 'Menu']:
                            self.unreachable_chars.add(char)
            else:
                self.unreachable_chars.add(char)

        total_cost = self.finger_manager.get_total_cost()

        # NEW: Print cost breakdown by layer
        self._print_cost_breakdown()

        # Print summary of key usage
        print(f"Total cost from frequency-based simulation: {total_cost:,.2f}")
        print(f"Processed {min(len(top_words), 5000)} words from top 5000")
        print(f"Processed {len(char_frequencies)} individual characters")
        print(f"Total word frequency: {total_word_freq:,}")
        print(f"Total character frequency: {total_char_freq:,}")
        
        # Report key usage statistics
        total_physical_keys = len(self.physical_keyboard.keys)
        used_key_count = len(self.used_physical_keys)
        unused_key_count = total_physical_keys - used_key_count
        unreachable_char_count = len(self.unreachable_chars)
        
        print(f"Physical keys used: {used_key_count}/{total_physical_keys} ({used_key_count/total_physical_keys*100:.1f}%)")
        print(f"Physical keys unused: {unused_key_count}/{total_physical_keys} ({unused_key_count/total_physical_keys*100:.1f}%)")
        print(f"Characters unreachable in dataset: {unreachable_char_count}")
        
        if self.unreachable_chars:
            print(f"Unreachable characters: {sorted(list(self.unreachable_chars))}")
        
        # Find unused physical keys
        all_physical_keys = set(self.physical_keyboard.keys)
        unused_physical_keys = all_physical_keys - self.used_physical_keys
        if unused_physical_keys:
            unused_labels = []
            for key in unused_physical_keys:
                labels = key.get_labels()
                unused_labels.extend(list(labels))
            print(f"Unused physical key labels: {sorted(unused_labels)}")

        return total_cost

    def _print_cost_breakdown(self):
        """Print detailed cost breakdown by layer"""
        accumulator = self.finger_manager.get_accumulator()
        
        print("\n--- Cost Breakdown by Layer ---")
        layer_totals = accumulator.sum_by_layer()
        total = sum(layer_totals.values())
        
        for layer_name in sorted(layer_totals.keys()):
            cost = layer_totals[layer_name]
            percentage = (cost / total * 100) if total > 0 else 0
            print(f"  {layer_name:25} {cost:>15,.2f} ({percentage:>5.1f}%)")
        print(f"  {'TOTAL':25} {total:>15,.2f}")
        print()

    def inspect_costs(self, layer_names=None):
        """
        Inspect costs after fitness calculation.
        
        Args:
            layer_names: Optional list of layer names to filter by
        
        Returns:
            Dict with detailed cost information
        """
        accumulator = self.finger_manager.get_accumulator()
        
        return {
            'total': accumulator.total(layer_names),
            'by_layer': accumulator.sum_by_layer(),
            'by_key': accumulator.sum_by_key(layer_names),
            'matrix': accumulator.get_matrix(),
            'press_counts': accumulator.get_press_counts()
        }

    def get_key(self, symbol):
        """Get physical key for a virtual key symbol."""
        if symbol in self.remap_keys.keys():
            symbol = self.remap_keys[symbol]
        physical_key = self.key_mapper.get_physical_key(symbol)
        return [physical_key] if physical_key else []

    def inspect_layout(self, **kwargs):
        """
        Inspect the current layout with visualization options and display it.
        
        Args:
            layers: List of layers to display [0, 1] where 0=unshifted, 1=shifted
            show_costs: Whether to show cost information on keys
            cost_per_press: Cost multiplier for cost visualization
            custom_labels: Optional custom labels to override default behavior
        """
        return self.visualizer.inspect(**kwargs)
