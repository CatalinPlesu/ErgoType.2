from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
from .mapper import Mapper, KeyType, Key
import string

BASE_LAYER = 0
ALTGR_LAYER = 1

SPECIAL_CHARS = {'Tab': '\t',  'Enter': '\n', 'Space': ' '}
CONTROLS = ['Caps Lock', 'Backspace', 'Shift', 'Ctrl', 'Win', 'Alt',  'Menu']
LAYER_KEYS = ['AltGr']


class Layout:
    def __init__(self, keyboard, debug=False):
        self.debug = debug
        self.load_keyboard(keyboard)
        self.load_mapper()
        self._print_layout()

    def load_mapper(self):
        self.mapper = Mapper()
        symbols = string.ascii_letters+string.punctuation + string.digits
        for key in self.keyboard.keys:
            kl = key.get_labels()
            if kl[0] in symbols:
                if kl[0].isupper():
                    k = kl[0]
                    v = (k.lower(), k)
                    self.mapper[key.id, BASE_LAYER] = Key(KeyType.CHAR, v)
                else:
                    s, u = kl
                    v = (u, s)
                    self.mapper[key.id, BASE_LAYER] = Key(KeyType.CHAR, v)
            else:
                k = kl[0]
                if k in SPECIAL_CHARS:
                    v = ({SPECIAL_CHARS[k]}, k)
                    self.mapper[key.id, BASE_LAYER] = Key(
                        KeyType.SPECIAL_CHAR, v)
                elif k in CONTROLS:
                    self.mapper[key.id, BASE_LAYER] = Key(KeyType.CONTROL, k)
                elif k in LAYER_KEYS:
                    self.mapper[key.id, BASE_LAYER] = Key(KeyType.LAYER, k)

    def load_keyboard(self, keyboard):
        self._print("Layout Loaded Keyboard")
        self.keyboard = keyboard

    def querty_based_remap(self, symbols):
        self.remap(LAYOUT_DATA["qwerty"], symbols)

    def remap(self, symbols_before, symbols_after):
        pass

    def apply_language_layout(self, remap):
        pass

    def _print(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)

    def _print_layout(self):
        if not self.debug:
            return

        """Print the complete layout with all layers"""
        print("\n" + "="*80)
        print("LAYOUT DEBUG - ALL LAYERS")
        print("="*80)

        # Group mapper items by layer
        layer_mapping = {}
        for (key_id, layer), key_obj in self.mapper.data.items():
            if layer not in layer_mapping:
                layer_mapping[layer] = []
            layer_mapping[layer].append((key_id, key_obj))

        # Print each layer in compact format
        for layer in sorted(layer_mapping.keys()):
            print(f"\nLAYER {layer}: ", end="")
            for i, (key_id, key_obj) in enumerate(layer_mapping[layer]):
                if i > 0:
                    print(" | ", end="")
                print(f"""{key_id:<3}:{key_obj.key_type.name:<13}={
                      str(key_obj.value):17}""", end="")
                if i % 3 == 0:
                    print()
            print()  # New line after each layer

        print(f"\nTotal layers: {len(layer_mapping)}")
        print("="*80)
