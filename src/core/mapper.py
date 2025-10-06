from collections import defaultdict
from enum import Enum


class KeyType(Enum):
    CHAR = "char"
    # chars that their label is not what is printed (tab, space, enter)
    SPECIAL_CHAR = "special_char"
    CONTROL = "control"  # alt, shift, altgr, win, ctrl, esc
    LAYER = "layer"  # layer keys


class Key:
    def __init__(self, key_type, value):
        self.key_type = key_type
        self.value = value

    def __repr__(self):
        return f"QMKKey({self.key_type.value}, {self.value})"


class Mapper:
    def __init__(self):
        self.data = {}
        self.by_layer = defaultdict(dict)
        self.by_key = defaultdict(dict)

    def __setitem__(self, key, value):
        key_id, layer_id = key
        self.data[(key_id, layer_id)] = value
        self.by_layer[layer_id][key_id] = value
        self.by_key[key_id][layer_id] = value

    def __getitem__(self, key):
        if isinstance(key, tuple):
            key_id, layer_id = key
            return self.data[key]
        return self.by_layer[key]

    def get_by_key(self, key_id):
        return self.by_key[key_id]

    def get_by_layer(self, layer_id):
        return self.by_layer[layer_id]

    def filter_data(self, filter_func):
        """Filter all data using a custom function that takes (key_id, layer_id, value)"""
        results = []
        for (key_id, layer_id), value in self.data.items():
            if filter_func(key_id, layer_id, value):
                results.append(((key_id, layer_id), value))
        return results

    def filter_by_layer(self, layer_id, filter_func):
        """Filter data for a specific layer using a function that takes (key_id, value)"""
        results = []
        for key_id, value in self.by_layer[layer_id].items():
            if filter_func(key_id, value):
                results.append((key_id, value))
        return results

    def filter_by_key(self, key_id, filter_func):
        """Filter data for a specific key using a function that takes (layer_id, value)"""
        results = []
        for layer_id, value in self.by_key[key_id].items():
            if filter_func(layer_id, value):
                results.append((layer_id, value))
        return results

    def get_all_pairs(self):
        return list(self.data.keys())


if __name__ == "__main__":
    d = Mapper()

    special_chars = ['tab', 'space', 'enter', 'escape']
    controls = ['shift', 'alt', 'ctrl', 'win', 'altgr']
    momentary_keys = ['MO1', 'MO2', 'MO3', 'MO4']

    for key_id in range(1, 11):
        for layer_id in range(1, 4):
            if key_id <= 5:
                d[key_id, layer_id] = Key(
                    KeyType.CHAR,
                    chr(ord('a') + key_id - 1 + (layer_id-1) * 5)
                )
            elif key_id <= 8:
                if key_id <= 6:
                    d[key_id, layer_id] = Key(
                        KeyType.SPECIAL_CHAR,
                        special_chars[key_id - 6]
                    )
                else:
                    d[key_id, layer_id] = Key(
                        KeyType.CONTROL,
                        controls[key_id - 7]
                    )
            else:
                d[key_id, layer_id] = Key(
                    KeyType.LAYER,
                    momentary_keys[key_id - 9]
                )

    print("All data for layer 1:")
    print(d[1])
    print()

    char_keys = d.filter_data(
        lambda key_id, layer_id, value: value.key_type == KeyType.CHAR and value.value in [
            'a', 'b', 'c']
    )
    print("Character keys with 'a', 'b', or 'c':")
    for (key_id, layer_id), item in char_keys:
        print(f"  ({key_id}, {layer_id}): {item}")
    print()

    special_in_layer2 = d.filter_by_layer(2,
                                          lambda key_id, value: value.key_type == KeyType.SPECIAL_CHAR
                                          )
    print("Special character keys in layer 2:")
    for key_id, item in special_in_layer2:
        print(f"  Key {key_id}: {item}")
    print()

    control_keys = d.filter_data(
        lambda key_id, layer_id, value: value.key_type == KeyType.CONTROL
    )
    print("All control keys:")
    for (key_id, layer_id), item in control_keys:
        print(f"  ({key_id}, {layer_id}): {item}")
    print()

    layer_keys = d.filter_data(
        lambda key_id, layer_id, value: value.key_type == KeyType.LAYER
    )
    print("All layer keys:")
    for (key_id, layer_id), item in layer_keys:
        print(f"  ({key_id}, {layer_id}): {item}")
    print()
