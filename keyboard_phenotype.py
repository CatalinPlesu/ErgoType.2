from kle.kle_model import Keyboard, FingerName, Hand
from collections import defaultdict
import string
from enum import Enum
import math
from finger_strength import FINGER_STRENGTHS


def cartesian_distance(point1, point2):
    """
    Calculate the Cartesian distance between two points.
    """
    if len(point1) != len(point2) or len(point1) not in [2, 3]:
        raise ValueError("Points must have the same dimensionality (2D or 3D)")

    squared_diffs = [(a - b) ** 2 for a, b in zip(point1, point2)]
    return math.sqrt(sum(squared_diffs))


def fitts_law_time(distance, target_width, a=0.1, b=0.2):
    """
    Calculate movement time using Fitts's law.

    MT = a + b * log2(D/W + 1)

    Where:
    - MT = Movement Time
    - D = Distance to target
    - W = Width of target
    - a, b = empirically determined constants

    Default constants are typical for pointing tasks.
    You may need to adjust these based on typing studies.
    """
    if target_width <= 0:
        raise ValueError("Target width must be positive")

    if distance <= 0:
        return a  # No movement needed

    index_of_difficulty = math.log2(distance / target_width + 1)
    movement_time = a + b * index_of_difficulty

    return movement_time


def fitts_law_cost(distance, target_width, a=0.1, b=0.2):
    """
    Calculate movement cost using Fitts's law.
    This is essentially the movement time, which represents difficulty/cost.
    """
    return fitts_law_time(distance, target_width, a, b)


class Finger:
    def __init__(self, homing_key):
        self.homming_position = homing_key.get_key_center_position()
        self.current_position = homing_key.get_key_center_position()
        self.total_cost = 0

    def press(self, key, presses, use_fitts_law=True, fitts_a=0.1, fitts_b=0.2):
        """
        Press a key and calculate the cost.

        Args:
            key: The key being pressed
            presses: Number of times the key is pressed
            use_fitts_law: Whether to use Fitts's law (True) or simple distance (False)
            fitts_a, fitts_b: Fitts's law constants
        """
        new_position = key.get_key_center_position()
        distance = cartesian_distance(self.current_position, new_position)

        if use_fitts_law and distance > 0:
            # Get target dimensions - you may need to add these methods to your key class
            try:
                # Try to get key width - smaller dimension is typically the constraint
                key_width = min(key.get_width(), key.get_height())
            except AttributeError:
                # Fallback to assumed standard key size if methods don't exist
                key_width = 1.0  # Adjust this based on your key units
                print(f"""Warning: Could not get key dimensions, using default width: {
                      key_width}""")

            cost = fitts_law_cost(distance, key_width, fitts_a, fitts_b)

            # DEBUG: Print detailed calculations
            if hasattr(key, 'get_labels'):
                labels = key.get_labels()
                id_val = math.log2(distance / key_width +
                                   1) if distance > 0 else 0
                print(f"""Key {labels}: dist={distance:.2f}, width={
                      key_width:.2f}, ID={id_val:.2f}, cost={cost:.2f}""")
        else:
            # Fallback to original distance-based cost
            cost = distance

        self.total_cost += cost * presses
        self.current_position = new_position

    def reset(self):
        self.total_cost = 0
        self.current_position = self.homming_position


class FingerManager:
    def __init__(self, physical_keyboard):
        self.fingers = {}
        self.list_alternation = 0
        self.use_fitts_law = True
        self.fitts_a = 0.1  # Empirical constant - adjust based on typing studies
        self.fitts_b = 0.2  # Empirical constant - adjust based on typing studies

        for item in FingerName:
            self.fingers[item] = Finger(
                physical_keyboard.get_homing_key_for_finger_name(item))

    def set_fitts_parameters(self, use_fitts_law=True, fitts_a=0.1, fitts_b=0.2):
        """
        Configure Fitts's law parameters.

        Args:
            use_fitts_law: Whether to use Fitts's law
            fitts_a: Fitts's law intercept constant (baseline time)
            fitts_b: Fitts's law slope constant (sensitivity to difficulty)
        """
        self.use_fitts_law = use_fitts_law
        self.fitts_a = fitts_a
        self.fitts_b = fitts_b

    def press(self, key, presses):
        fingername = key.get_finger_name()
        if isinstance(fingername, list):
            self.fingers[fingername[self.list_alternation]].press(
                key, presses, self.use_fitts_law, self.fitts_a, self.fitts_b)
            self.list_alternation = 1 if self.list_alternation == 0 else 0
        else:
            self.fingers[fingername].press(
                key, presses, self.use_fitts_law, self.fitts_a, self.fitts_b)

    def get_total_cost(self):
        total_cost = 0
        for key, value in self.fingers.items():
            total_cost += value.total_cost
        return total_cost

    def reset(self):
        for key in self.fingers.keys():
            self.fingers[key].reset()


class KeyboardPhenotype:
    def __init__(self, physical_keyboard, remap):
        print("Init keyboard phenotype")
        self.remap_keys = {}
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

    def configure_fitts_law(self, use_fitts_law=True, fitts_a=0.1, fitts_b=0.2):
        """
        Configure whether to use Fitts's law and set its parameters.

        Args:
            use_fitts_law: Whether to use Fitts's law for cost calculation
            fitts_a: Intercept constant (typical values: 0.05-0.2)
            fitts_b: Slope constant (typical values: 0.1-0.3)

        Recommended parameter ranges based on HCI research:
        - For mouse pointing: a=0.1-0.2, b=0.2-0.3
        - For touch interfaces: a=0.05-0.15, b=0.15-0.25
        - For typing: may need custom calibration
        """
        self.finger_manager.set_fitts_parameters(
            use_fitts_law, fitts_a, fitts_b)

    def select_remap_keys(self, keys_list):
        self.remap_keys = dict()
        self.remap_key_length = len(keys_list)
        self.original_key_list = keys_list

    def remap_to_keys(self, keys_list):
        if self.remap_key_length != len(keys_list):
            print("remap key liset doesn't match in length")
            return

        remap_keys = dict()
        for index, key in enumerate(self.original_key_list):
            remap_keys[key] = keys_list[index]
        self.remap_keys = remap_keys
        print(self.remap_keys)

    def fitness(self, markov_chain, simulated_presses=1_000_000, depth=1):
        self.finger_manager.reset()
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

        total_cost = self.finger_manager.get_total_cost()
        print(f"Total cost: {total_cost:,.2f}")
        print(f"Total presses: {total_presses:,}")

        if self.finger_manager.use_fitts_law:
            print(f"""Cost calculation: Fitts's Law (a={
                  self.finger_manager.fitts_a}, b={self.finger_manager.fitts_b})""")
        else:
            print("Cost calculation: Cartesian distance")

        return total_cost

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

    def get_phisical_keyboard(self):
        for key, value in self.remap_keys.items():
            self.keymap[key][0].set_labels((value,))
        return self.physical_keyboard

    def get_physical_keyboard_with_costs(self):
        """
        Calculate the cost of pressing each key once with the appropriate finger
        and store this cost information on the physical keyboard model.
        """
        # Reset finger manager to start from home positions
        self.finger_manager.reset()

        print("=== DEBUGGING FITTS LAW COSTS ===")
        print(f"Using Fitts's Law: {self.finger_manager.use_fitts_law}")
        print(f"""Parameters: a={self.finger_manager.fitts_a}, b={
              self.finger_manager.fitts_b}""")

        # For each key on the physical keyboard, calculate the cost of one press
        for key in self.physical_keyboard.keys:
            # Get finger and calculate distance from home position
            finger_name = key.get_finger_name()
            if isinstance(finger_name, list):
                finger_name = finger_name[0]

            finger = self.finger_manager.fingers[finger_name]
            distance = cartesian_distance(
                finger.homming_position, key.get_key_center_position())

            # Calculate cost manually for debugging
            if self.finger_manager.use_fitts_law and distance > 0:
                try:
                    key_width = min(key.get_width(), key.get_height())
                except AttributeError:
                    key_width = 1.0

                id_val = math.log2(distance / key_width + 1)
                cost = self.finger_manager.fitts_a + self.finger_manager.fitts_b * id_val

                labels = key.get_labels() if hasattr(
                    key, 'get_labels') else ['unknown']
                print(f"""Key {labels[0] if labels else 'N/A'}: dist={distance:.2f}, width={
                      key_width:.2f}, ID={id_val:.2f}, cost={cost:.2f}""")
            else:
                cost = distance
                labels = key.get_labels() if hasattr(
                    key, 'get_labels') else ['unknown']
                print(f"""Key {labels[0] if labels else 'N/A'}: dist={
                      distance:.2f}, cost={cost:.2f} (simple distance)""")

            # Store the cost on the key
            key.set_labels((str(f"{cost:.2f}"),))

        return self.physical_keyboard

    def analyze_fitts_difficulty(self):
        """
        Analyze the Index of Difficulty (ID) for each key according to Fitts's law.
        Returns a dictionary mapping keys to their difficulty values.
        """
        if not self.finger_manager.use_fitts_law:
            print("Fitts's law is not enabled. Enable it with configure_fitts_law(True)")
            return {}

        key_difficulties = {}

        for key in self.physical_keyboard.keys:
            finger_name = key.get_finger_name()
            if isinstance(finger_name, list):
                finger_name = finger_name[0]  # Use first finger option

            finger = self.finger_manager.fingers[finger_name]
            distance = cartesian_distance(
                finger.homming_position, key.get_key_center_position())

            try:
                key_width = min(key.get_width(), key.get_height())
            except AttributeError:
                key_width = 1.0

            if distance > 0:
                index_of_difficulty = math.log2(distance / key_width + 1)
                key_difficulties[key] = {
                    'distance': distance,
                    'width': key_width,
                    'index_of_difficulty': index_of_difficulty,
                    'predicted_time': fitts_law_time(distance, key_width,
                                                     self.finger_manager.fitts_a,
                                                     self.finger_manager.fitts_b)
                }

        return key_difficulties
