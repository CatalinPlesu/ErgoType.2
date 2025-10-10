import hashlib
import pickle
from src.config.file_paths import DISTANCE_CACHE
import os
from src.core.keyboard import *
import math


def cartesian_distance(point1: tuple, point2: tuple) -> float:
    if len(point1) != len(point2):
        raise ValueError(
            "Points must have the same dimension (e.g., both 2D or both 3D).")
    squared_differences_sum = sum((p1_coord - p2_coord) ** 2
                                  for p1_coord, p2_coord in zip(point1, point2))
    distance = math.sqrt(squared_differences_sum)
    return distance


def axis_movement(point1: tuple, point2: tuple) -> tuple:
    if len(point1) != len(point2):
        raise ValueError(
            "Points must have the same dimension (e.g., both 2D or both 3D).")
    movement = tuple(p2_coord - p1_coord
                     for p1_coord, p2_coord in zip(point1, point2))
    return movement


class DistanceCalculator:
    def __init__(self, keyboard_file, keyboard, debug=False):
        self.debug = debug
        self._print("Distance Calculator Invoked")
        self.keyboard_file = keyboard_file
        self.keyboard = keyboard
        self.file_hash()
        self.load_cache()
        self.load_cost()
        self.save_cache()

    def _calculate_distance_and_movement(self, key1_id: int, key2_id: int) -> tuple:
        key1 = self.keyboard.keys[key1_id]
        key2 = self.keyboard.keys[key2_id]

        if not key1 or not key2:
            raise ValueError(f"Key with ID {key1_id} or {key2_id} not found")

        p1 = key1.get_key_center_position()
        p2 = key2.get_key_center_position()
        distance = cartesian_distance(p1, p2)
        movement = axis_movement(p1, p2)
        return distance, movement

    def calculate_cost(self):
        if self.cost is None:
            self.cost = {}

        if self.keyboard_file not in self.cost:
            self.cost[self.keyboard_file] = {}

        self.cost[self.keyboard_file]['md5'] = self.keyboard_md5

        # Get the exact matrix size from the keyboard keys list
        # No -1, no buffer - exact size needed
        matrix_size = len(self.keyboard.keys)

        # Initialize 2D matrix with None values - list of lists
        movement_matrix = [[None for _ in range(
            matrix_size)] for _ in range(matrix_size)]

        fingers = [member for member in FingerName]
        finger_keys = {}
        for finger in fingers:
            finger_keys[finger] = self.keyboard.get_finger_keys(finger)

        self._print("Identified keys of each finger")

        self._print(
            "Calculating all possible movements and caching in 2D matrix")

        # Calculate distances and movements for all key pairs within each finger
        for finger in fingers:
            keys = finger_keys[finger]
            for key1 in keys:
                for key2 in keys:
                    key_id1, key_id2 = key1.id, key2.id

                    # Store in matrix as tuple (distance, movement)
                    # Assuming key IDs are within the range [0, matrix_size)
                    movement_matrix[key_id1][key_id2] = self._calculate_distance_and_movement(
                        key_id1, key_id2)

        self.cost[self.keyboard_file]['movement_matrix'] = movement_matrix
        self.cost[self.keyboard_file]['matrix_size'] = matrix_size
        self._print("cost's for this keyboard have been cached in 2D matrix")

    def load_cost(self):
        if self.cost is None or self.debug:
            self._print("Calculating costs")
            self.calculate_cost()
            return

        if self.keyboard_file in self.cost:
            if self.keyboard_md5 == self.cost[self.keyboard_file]['md5']:
                self._print(
                    "Cost already exist in cache, nothing to calculate")
            else:
                self._print("MD5 hashes differ, recalculating")
                self.calculate_cost()

    def load_cache(self):
        self._print("Loading Cache")
        try:
            if not os.path.exists(DISTANCE_CACHE):
                self._print(f"ERROR: Data file not found: {DISTANCE_CACHE}")
                self.cost = None
            else:
                with open(DISTANCE_CACHE, 'rb') as f:
                    self.cost = pickle.load(f)
                    self._print(f"""✅ Successfully loaded data from {
                                DISTANCE_CACHE}""")
        except Exception as e:
            self._print(f"ERROR loading {e}")
            self.cost = None

    def save_cache(self):
        os.makedirs(os.path.dirname(DISTANCE_CACHE), exist_ok=True)
        self._print("Saved cache")
        with open(DISTANCE_CACHE, 'wb') as f:
            pickle.dump(self.cost, f)

    def file_hash(self):
        with open(self.keyboard_file, 'rb') as f:
            data = f.read()
            self.keyboard_md5 = hashlib.md5(data).hexdigest()
            self._print(
                f"Obtained '{self.keyboard_md5}' hash for current keyboard")

    def get_distance_and_movement(self, key1_id: int, key2_id: int) -> tuple:
        if (self.cost and
            self.keyboard_file in self.cost and
                'movement_matrix' in self.cost[self.keyboard_file]):

            movement_matrix = self.cost[self.keyboard_file]['movement_matrix']
            matrix_size = self.cost[self.keyboard_file]['matrix_size']

            # Check if key IDs are within bounds
            if key1_id < matrix_size and key2_id < matrix_size:
                cached_data = movement_matrix[key1_id][key2_id]

                if cached_data is not None:
                    return cached_data

        return self._calculate_distance_and_movement(key1_id, key2_id)

    def _print(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)


if __name__ == "__main__":
    import os
    from src.core.keyboard import Serial
    from src.config.file_paths import DISTANCE_CACHE

    def load_keyboard(keyboard_file):
        print(f"""load_keyboard called with: keyboard_file={keyboard_file}""")
        with open(keyboard_file, 'r') as f:
            print(f"""Read file: '{keyboard_file}'""")
            keyboard = Serial.parse(f.read())
        print(f"""load_keyboard returning: keyboard_file={
              keyboard_file}, keyboard type={type(keyboard)}""")
        return keyboard_file, keyboard

    def load_distance(keyboard_file, keyboard, debug=True):
        print(f"""load_distance called with: keyboard_file={
              keyboard_file}, keyboard={keyboard}, debug={debug}""")
        distance = DistanceCalculator(keyboard_file, keyboard, debug=debug)
        print(f"""load_distance returning: distance={distance}""")
        return distance

    # Test all keyboard files
    keyboard_files = [
        'src/data/keyboards/ansi_60_percent.json',
        'src/data/keyboards/ansi_60_percent_thinkpad.json',
        'src/data/keyboards/dactyl_manuform_6x6_4.json',
        'src/data/keyboards/ferris_sweep.json'
    ]

    print(f"""Testing keyboard files: {keyboard_files}""")

    for keyboard_file in keyboard_files:
        print(f"""Processing keyboard_file: {keyboard_file}""")
        if os.path.exists(keyboard_file):
            print(f"""\n--- Testing {keyboard_file} ---""")
            keyboard_file_loaded, keyboard = load_keyboard(keyboard_file)
            distance = load_distance(keyboard_file_loaded, keyboard)

            # Test with first key only to avoid cross-finger issues
            print(f"""Keyboard has {len(keyboard.keys)} keys""")
            if len(keyboard.keys) >= 1:
                # Test distance from key to itself (should be 0)
                print(f"""Testing distance for key 0 to itself""")
                dist, movement = distance.get_distance_and_movement(0, 0)
                print(f"""Distance for key 0 to itself: {dist}""")

                # Test with actual finger keys if available
                from src.core.keyboard import FingerName
                fingers = [member for member in FingerName]
                print(f"""Testing finger keys for fingers: {fingers}""")
                for finger in fingers:
                    finger_keys = keyboard.get_finger_keys(finger)
                    print(f"""Finger {finger} has {len(finger_keys)} keys""")
                    if len(finger_keys) >= 2:
                        key1_id = finger_keys[0].id
                        key2_id = finger_keys[1].id
                        print(f"""Testing distance between {
                              finger} keys {key1_id} and {key2_id}""")
                        dist, movement = distance.get_distance_and_movement(
                            key1_id, key2_id)
                        print(f"""Distance between {finger} keys {
                              key1_id} and {key2_id}: {dist}""")
                        break  # Just test first finger with multiple keys
        else:
            print(f"""File not found: {keyboard_file}""")
