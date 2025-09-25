from kle.kle_model import Keyboard, FingerName, Hand
from collections import defaultdict
import string
from enum import Enum
import math


def cartesian_distance(point1, point2):
    """
    Calculate the Cartesian distance between two points.
    """
    if len(point1) != len(point2) or len(point1) not in [2, 3]:
        raise ValueError("Points must have the same dimensionality (2D or 3D)")

    squared_diffs = [(a - b) ** 2 for a, b in zip(point1, point2)]
    return math.sqrt(sum(squared_diffs))


class Finger:
    def __init__(self, homing_key):
        # self.homming_position = homing_key.get_key_center_position()
        self.current_position = homing_key.get_key_center_position()
        self.total_cost = 0

    def press(self, key, presses):
        new_possition = key.get_key_center_position()
        cost = cartesian_distance(self.current_position, new_possition)
        self.total_cost += cost * presses


class FingerManager:
    def __init__(self, physical_keyboard):
        self.fingers = {}
        self.list_alternation = 0
        for item in FingerName:
            self.fingers[item] = Finger(
                physical_keyboard.get_homing_key_for_finger_name(item))

    def press(self, key, presses):
        fingername = key.get_finger_name()
        if isinstance(fingername, list):
            self.fingers[fingername[self.list_alternation]].press(key, presses)
            self.list_alternation = 1 if self.list_alternation == 0 else 0
        else:
            self.fingers[fingername].press(key, presses)
        pass

    def get_total_cost(self):
        total_cost = 0
        for key, value in self.fingers.items():
            total_cost += value.total_cost
        return total_cost


class KeyboardPhenotype:
    def __init__(self, physical_keyboard, remap):
        print("Init keyboard phenotype")
        self.physical_keyboard = physical_keyboard
        self.finger_manager = FingerManager(self.physical_keyboard)

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

    def fitness(self, markov_chain, simulated_presses=1_000_000, depth=1):
        simulated_presses /= 100
        simulated_presses /= depth
        total_presses = 0
        for key in markov_chain['markov_chain'].keys():
            if key not in self.char_key_map.keys():
                print(f"Key {key} won't be reachable")

        for key in markov_chain['markov_chain'].keys():
            percentage = markov_chain['markov_chain'][key]['global_percentage']
            presses = percentage * simulated_presses
            total_presses += presses
            keys = self.translate_char_to_keys(key)
            for x in keys:
                self.finger_manager.press(x, presses)

        print(f"Total cost: {self.finger_manager.get_total_cost():,.2f}")
        print(f"Total presses: {total_presses:,}")

    def translate_char_to_keys(self, character):
        keys = self.char_key_map[character]
        # print(keys)
        keys = [self.get_key(key) for key in keys]
        # print(keys)
        if len(keys) == 2 and len(keys[0]) == 2:
            if keys[1][0].hand == Hand.LEFT:
                keys[0] = next(x for x in keys[0] if x.hand == Hand.RIGHT)
                keys[1] = keys[1][0]
            else:
                keys[0] = next(x for x in keys[0] if x.hand == Hand.LEFT)
                keys[1] = keys[1][0]
        else:
            keys = keys[0]
        return keys

    def get_key(self, symbol):
        if symbol in self.remap_keys.keys():
            symbol = self.remap_keys[symbol]
        keys = self.keymap[symbol]
        return keys

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
