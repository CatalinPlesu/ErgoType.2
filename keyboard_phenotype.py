from kle.kle_model import Keyboard
from collections import defaultdict
import string


class KeyboardPhenotype:
    def __init__(self, physical_keyboard, remap):
        print("Init keyboard phenotype")
        self.physical_keyboard = physical_keyboard

        # create teh logical layers of keyboard, assuming that shift layer is tightly coulpled to a key, and we don't break it down
        layers = {
            "base": list(zip(list(string.ascii_lowercase), list(string.ascii_uppercase)))
            + list(zip(list('1234567890'), list('!@#$%^&*()')))
            + list(zip(list('[]=,./\\;-\'`'), list('{}+<>?|:_"~')))
        }

        # Map special keys to their characters if they have them
        special_key_map = {'Space': ' ', 'Tab': '\t',
                           'Enter': '\n', 'Shift': '', 'AltGr': ''}

        char_key_map = dict()
        for key, value in special_key_map.items():
            if value != '':
                char_key_map[value] = [key]
            else:
                char_key_map[key] = [key]  # for keys that don't have symbols

        # add the letters, numbers and symbols to the keymap
        for key in layers["base"]:
            char_key_map[key[0]] = [key[0]]
            char_key_map[key[1]] = ['Shift', key[0]]

        # identify unique needed keys for typing
        needed_keys = []
        for _, values in char_key_map.items():
            needed_keys += values
        needed_keys = set(needed_keys)

        # keymap maping keys to their phisical attributes
        keymap = defaultdict(list)
        for key in physical_keyboard.keys:
            found = False
            for k in needed_keys:
                if k in key.get_labels() or k.upper() in key.get_labels():
                    keymap[k].append(key)
                    # print(f"Key is needed {key.get_labels()}")
                    found = True
                    break
            if not found:
                print(f"Key is unneeded {key.get_labels()}")

        self.keymap = keymap
        self.char_key_map = char_key_map

    def select_remap_keys(self, keys_list):
        remap_keys = dict()
        self.remap_key_length = len(keys_list)
        self.original_key_list = keys_list

    def remap_to_keys(self, keys_list):
        if self.remap_key_length != len(keys_list):
            print("remap key liset doesn't match in length")
            return

        remap_keys = dict()
        for index, key in enumerate(keys_list):
            remap_keys[key] = self.original_key_list[index]
        self.remap_keys = remap_keys
        print(self.remap_keys)

    # interfaces:
    # apply genotype
    # format:
    # remap List[Key] -> List[Key]

    # on init
    # construct keyboard layouts
    # 3 layouts a keybard has and we care about from start shift and altgr
    # detect if it is a specific layout so we in std ro, [] keyes press ăî and you need alt gr press to reach those keys
    # consider making the map a dict of key - base/shift/altgr to  list of keys

    # running fitness function for a given genotype

    # determine travel cost for finger press

    # determinte travel cost for sequence
    # think here of typing faster by paralell finger movement when not stopped.
