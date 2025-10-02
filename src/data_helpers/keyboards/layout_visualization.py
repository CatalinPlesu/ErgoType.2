from src.domain.keyboard import Key, Keyboard, KeyboardMetadata, Serial
from src.data_helpers.keyboards.renderer import show_keyboard, render_keyboard
from src.domain.layout_phenotype import LayoutPhenotype
from src.domain.key_mapper import KeyMapper
import json

class LayoutVisualization:
    def __init__(self, physical_keyboard, layout_phenotype=None):
        self.physical_keyboard = physical_keyboard
        self.layout_phenotype = layout_phenotype or LayoutPhenotype()
        self.key_mapper = None
    
    def set_layout(self, layout_phenotype, key_mapper=None):
        """Set the layout and key mapper for visualization."""
        self.layout_phenotype = layout_phenotype
        if key_mapper:
            self.key_mapper = key_mapper
        else:
            # Create a default key mapper if not provided
            self.key_mapper = KeyMapper(self.physical_keyboard, self.layout_phenotype)
    
    def inspect(self, layers=[0], show_costs=False, cost_per_press=1.0, custom_labels=None):
        """
        Visualize the keyboard layout with various options and display it.
        
        Args:
            layers: List of layers to display [0, 1] where 0=unshifted, 1=shifted
            show_costs: Whether to show cost information on keys
            cost_per_press: Cost multiplier for cost visualization
            custom_labels: Optional custom labels to override default behavior
        """
        # Create a copy of the keyboard for visualization
        temp_keyboard = self._clone_keyboard(self.physical_keyboard)
        
        # Apply layout visualization
        if self.key_mapper and self.layout_phenotype:
            self._apply_layout_to_keyboard(temp_keyboard, layers, show_costs, cost_per_press, custom_labels)
        
        # Display the keyboard
        show_keyboard(temp_keyboard)
        
        return temp_keyboard  # Return in case user wants to do additional operations
    
    def _clone_keyboard(self, keyboard):
        """Create a deep copy of the keyboard to avoid modifying the original."""
        # Create a new keyboard object
        new_kbd = Keyboard()
        
        # Copy metadata
        new_kbd.meta = KeyboardMetadata()
        for attr in vars(keyboard.meta):
            setattr(new_kbd.meta, attr, getattr(keyboard.meta, attr))
        
        # Copy all keys with their properties
        for key in keyboard.keys:
            new_key = Key()
            # Copy all attributes from the original key
            for attr in vars(key):
                value = getattr(key, attr)
                # Deep copy mutable attributes
                if isinstance(value, (list, dict)):
                    setattr(new_key, attr, self._deep_copy(value))
                else:
                    setattr(new_key, attr, value)
            new_kbd.keys.append(new_key)
        
        return new_kbd
    
    def _deep_copy(self, obj):
        """Simple deep copy implementation."""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj
    
    def _apply_layout_to_keyboard(self, keyboard, layers, show_costs, cost_per_press, custom_labels):
        """Apply the current layout to the keyboard for visualization."""
        if custom_labels:
            # Apply custom labels if provided
            for i, key in enumerate(keyboard.keys):
                if i < len(custom_labels):
                    key.set_labels((custom_labels[i],))
        else:
            # Apply layout from key mapper
            for virtual_key_id, physical_key in self.key_mapper.get_all_mappings().items():
                if virtual_key_id in self.layout_phenotype.virtual_keys:
                    vkey = self.layout_phenotype.virtual_keys[virtual_key_id]
                    
                    # Build label based on requested layers
                    labels = []
                    for layer_idx in layers:
                        if layer_idx in vkey.layers:
                            unshifted, shifted = vkey.layers[layer_idx]
                            if layer_idx == 0:
                                labels.append(unshifted)
                            elif layer_idx == 1:
                                labels.append(shifted)
                    
                    if labels:
                        physical_key.set_labels(tuple(labels))
        
        # If showing costs, we would need finger manager integration
        if show_costs and self.key_mapper and self.layout_phenotype:
            self._apply_costs_to_keyboard(keyboard, cost_per_press)
    
    def _apply_costs_to_keyboard(self, keyboard, cost_per_press):
        """Apply cost information to the keyboard."""
        from src.domain.keyboard_phenotype import FingerManager  # Import here to avoid circular dependency
        
        finger_manager = FingerManager(keyboard)
        
        for physical_key in keyboard.keys:
            # Get finger for this key
            fingername = physical_key.get_finger_name()
            if isinstance(fingername, list):
                fingername = fingername[0]  # Use first finger if it's a list
            
            # Simulate one press to get the cost
            original_total_cost = finger_manager.get_total_cost()
            
            # Create a temporary key to press (this is tricky without the actual key object)
            # For now, we'll use the physical key directly
            if hasattr(physical_key, 'get_finger_name'):
                # Calculate cost for this specific key press
                # This is a simplified approach - in reality, you'd need the full finger movement calculation
                cost_label = f"{cost_per_press:.2f}"
                current_labels = physical_key.get_labels()
                # Add cost to the label
                new_labels = current_labels + (cost_label,)
                physical_key.set_labels(new_labels)
            
            # Reset for next key
            finger_manager.reset()
    
    def visualize_multiple_layouts(self, layouts_config, layers=[0]):
        """
        Visualize multiple layouts side by side or in sequence.
        
        Args:
            layouts_config: List of tuples (layout_name, layout_phenotype, key_mapper)
        """
        for name, layout_phenotype, key_mapper in layouts_config:
            print(f"\n--- Visualizing {name} ---")
            self.set_layout(layout_phenotype, key_mapper)
            self.inspect(layers=layers)
