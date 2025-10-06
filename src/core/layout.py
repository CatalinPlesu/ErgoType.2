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
        if len(symbols_before) != len(symbols_after):
            print("Can't remap layou's with differnet length")
            return
        print("############33 here")
        remap = zip(symbols_before, symbols_after)
        # Stage 1: Collect all keys that need to be remapped
        keys_to_update = []
        for before, after in remap:
            if before == after:
                continue
            char_keys = self.mapper.filter_data(
                lambda key_id, layer_id, value: value.key_type == KeyType.CHAR and value.value[0] == before)
            for char_key in char_keys:
                keys_to_update.append((char_key[0], before, after))

        # Stage 2: Apply all remappings
        for key_id, before, after in keys_to_update:
            self.mapper[key_id] = Key(
                KeyType.CHAR, (after, after.upper()))

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


if __name__ == "__main__":
    from src.core.keyboard import Keyboard, Serial
    from .mapper import Mapper, KeyType, Key
    import string

    # Load keyboard
    keyboard_file = 'src/data/keyboards/ansi_60_percent.json'
    with open(keyboard_file, 'r') as f:
        keyboard = Serial.parse(f.read())

    # Create layout
    layout = Layout(keyboard, debug=True)

    print("\n" + "="*80)
    print("TESTING MAPPER FUNCTIONALITY")
    print("="*80)

    # Get the mapper from the layout
    mapper = layout.mapper

    print(f"Total key-layer pairs in mapper: {len(mapper.data)}")

    # Test 1: Find key and layer for specific characters
    print("\n1. FINDING KEYS FOR SPECIFIC CHARACTERS:")
    print("-" * 40)

    test_chars = ['a', 'A', '1', '!', 'q', 'z']
    for char in test_chars:
        found = False
        for (key_id, layer_id), key_obj in mapper.data.items():
            if key_obj.key_type == KeyType.CHAR:
                # key_obj.value is a tuple (lowercase, uppercase) for chars
                if isinstance(key_obj.value, tuple):
                    lower_val, upper_val = key_obj.value
                    if lower_val == char or upper_val == char:
                        print(f"""Character '{char}' -> Key ID: {key_id:<3} | Layer: {
                              layer_id} | Value: {key_obj.value}""")
                        found = True
                        break
        if not found:
            print(f"Character '{char}' not found in layout")

    # Test 2: Find all mappings for a specific character (case insensitive)
    print(f"\n2. FINDING ALL MAPPINGS FOR CHARACTER 'a':")
    print("-" * 40)
    char_to_find = 'a'
    for (key_id, layer_id), key_obj in mapper.data.items():
        if key_obj.key_type == KeyType.CHAR:
            if isinstance(key_obj.value, tuple):
                lower_val, upper_val = key_obj.value
                if lower_val == char_to_find or upper_val == char_to_find:
                    print(f"""Key ID: {key_id:<3} | Layer: {layer_id} | Type: {
                          key_obj.key_type.name:<13} | Value: {key_obj.value}""")

    # Test 3: Find all printable characters and their mappings
    print(f"\n3. ALL PRINTABLE CHARACTER MAPPINGS:")
    print("-" * 40)
    printable_chars = []
    for (key_id, layer_id), key_obj in mapper.data.items():
        if key_obj.key_type == KeyType.CHAR:
            if isinstance(key_obj.value, tuple):
                lower_val, upper_val = key_obj.value
                printable_chars.append(
                    (key_id, layer_id, lower_val, upper_val))

    # Show first 20
    for key_id, layer_id, lower, upper in printable_chars[:20]:
        print(f"""Key ID: {key_id:<3} | Layer: {layer_id}
              | Lower: '{lower}' | Upper: '{upper}'""")

    # Test 4: Find special characters (punctuation)
    print(f"\n4. SPECIAL CHARACTER MAPPINGS (punctuation):")
    print("-" * 40)
    for (key_id, layer_id), key_obj in mapper.data.items():
        if key_obj.key_type == KeyType.CHAR:
            if isinstance(key_obj.value, tuple):
                lower_val, upper_val = key_obj.value
                if lower_val in string.punctuation or upper_val in string.punctuation:
                    print(f"""Key ID: {key_id:<3} | Layer: {
                          layer_id} | Punct: '{lower_val}'/'{upper_val}'""")

    # Test 5: Find special character keys (Tab, Enter, Space, etc.)
    print(f"\n5. SPECIAL CHARACTER KEYS (Tab, Enter, Space, etc.):")
    print("-" * 40)
    for (key_id, layer_id), key_obj in mapper.data.items():
        if key_obj.key_type == KeyType.SPECIAL_CHAR:
            print(f"""Key ID: {key_id:<3} | Layer: {
                  layer_id} | Special: {key_obj.value}""")

    # Test 6: Find control keys
    print(f"\n6. CONTROL KEYS:")
    print("-" * 40)
    for (key_id, layer_id), key_obj in mapper.data.items():
        if key_obj.key_type == KeyType.CONTROL:
            print(f"""Key ID: {key_id:<3} | Layer: {
                  layer_id} | Control: {key_obj.value}""")

    # Test 7: Find layer keys
    print(f"\n7. LAYER KEYS:")
    print("-" * 40)
    for (key_id, layer_id), key_obj in mapper.data.items():
        if key_obj.key_type == KeyType.LAYER:
            print(f"""Key ID: {key_id:<3} | Layer: {
                  layer_id} | Layer Key: {key_obj.value}""")

    # Test 8: Count how many shift keys exist
    print(f"\n8. COUNTING SHIFT KEYS:")
    print("-" * 40)
    shift_keys = []
    for (key_id, layer_id), key_obj in mapper.data.items():
        if key_obj.key_type == KeyType.CONTROL and key_obj.value == 'Shift':
            shift_keys.append((key_id, layer_id))

    print(f"Total SHIFT keys found: {len(shift_keys)}")
    for key_id, layer_id in shift_keys:
        print(f"""Shift key -> Key ID: {key_id} | Layer: {layer_id}""")

    # Test 9: Function to find key for any character
    def find_key_for_char(target_char):
        """Find the key_id and layer_id for a given character"""
        for (key_id, layer_id), key_obj in mapper.data.items():
            if key_obj.key_type == KeyType.CHAR:
                if isinstance(key_obj.value, tuple):
                    lower_val, upper_val = key_obj.value
                    if lower_val == target_char or upper_val == target_char:
                        return key_id, layer_id, key_obj
            elif key_obj.key_type == KeyType.SPECIAL_CHAR:
                if isinstance(key_obj.value, tuple):
                    special_set, display_val = key_obj.value
                    if target_char in special_set:
                        return key_id, layer_id, key_obj
        return None, None, None

    # Test the function
    print(f"\n9. TESTING find_key_for_char FUNCTION:")
    print("-" * 40)
    test_chars_func = ['a', 'Z', '5', '\t', '\n', ' ']
    for char in test_chars_func:
        key_id, layer_id, key_obj = find_key_for_char(char)
        if key_id is not None:
            print(f"""Character '{char}' -> Key ID: {key_id}
                  | Layer: {layer_id} | Value: {key_obj.value}""")
        else:
            print(f"""Character '{char}' -> NOT FOUND""")

    print(f"\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
    layout.querty_based_remap(LAYOUT_DATA["asset"])
    layout._print_layout()
