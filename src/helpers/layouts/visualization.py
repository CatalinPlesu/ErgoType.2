from src.core.keyboard import Key, Keyboard, KeyboardMetadata, Serial
from src.helpers.keyboards.renderer import show_keyboard, render_keyboard
from src.core.mapper import KeyType


class LayoutVisualization:
    def __init__(self, keyboard, layout=None):
        self.keyboard = keyboard
        self.layout = layout

    def inspect(self, layers=None):
        if layers is None:
            layers = []
            if self.layout and hasattr(self.layout, 'mapper') and hasattr(self.layout.mapper, 'data'):
                for key_id, layer_idx in self.layout.mapper.data.keys():
                    if layer_idx not in layers:
                        layers.append(layer_idx)
            # Default to layer 0 if no data
            layers = sorted(layers) if layers else [0]

        def render_layer(layer):
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
