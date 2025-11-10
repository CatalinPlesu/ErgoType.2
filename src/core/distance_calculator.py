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
    def __init__(self, keyboard_file, keyboard, debug=False, fitts_a=0, fitts_b=150):
        """
        Initialize DistanceCalculator with Fitts's Law support.
        
        Args:
            keyboard_file: Path to keyboard layout file
            keyboard: Keyboard object
            debug: Enable debug printing
            fitts_a: Fitts's Law constant 'a' in milliseconds (default: 0)
            fitts_b: Fitts's Law constant 'b' in milliseconds (default: 150)
        """
        self.debug = debug
        self.fitts_a = fitts_a
        self.fitts_b = fitts_b
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

    def _calculate_fitts_time(self, key1_id: int, key2_id: int, distance: float) -> float:
        """
        Calculate movement time using Fitts's Law: MT = a + b * log2(D/W + 1)
        
        Args:
            key1_id: Starting key ID
            key2_id: Target key ID
            distance: Pre-calculated distance between keys
            
        Returns:
            Estimated movement time in milliseconds
        """
        key2 = self.keyboard.keys[key2_id]
        
        # Get target key width (effective width for Fitts's Law)
        # Assuming keys have a 'width' attribute, fallback to default if not
        target_width = getattr(key2, 'width', 19.05)  # Default: 19.05mm (standard key)
        
        # Handle same-key case (distance = 0)
        if distance == 0:
            return 0.0
        
        # Fitts's Law: MT = a + b * log2(D/W + 1)
        # Index of Difficulty (ID)
        id_value = math.log2(distance / target_width + 1)
        movement_time = self.fitts_a + self.fitts_b * id_value
        
        return movement_time

    def calculate_cost(self):
        if self.cost is None:
            self.cost = {}

        if self.keyboard_file not in self.cost:
            self.cost[self.keyboard_file] = {}

        self.cost[self.keyboard_file]['md5'] = self.keyboard_md5
        self.cost[self.keyboard_file]['fitts_params'] = {
            'a': self.fitts_a,
            'b': self.fitts_b
        }

        # Get the exact matrix size from the keyboard keys list
        matrix_size = len(self.keyboard.keys)

        # Initialize 2D matrices with None values
        movement_matrix = [[None for _ in range(
            matrix_size)] for _ in range(matrix_size)]
        time_matrix = [[None for _ in range(
            matrix_size)] for _ in range(matrix_size)]

        fingers = [member for member in FingerName]
        finger_keys = {}
        for finger in fingers:
            finger_keys[finger] = self.keyboard.get_finger_keys(finger)

        self._print("Identified keys of each finger")
        self._print(
            "Calculating all possible movements, times, and caching in 2D matrices")

        # Calculate distances, movements, and Fitts times for all key pairs within each finger
        for finger in fingers:
            keys = finger_keys[finger]
            for key1 in keys:
                for key2 in keys:
                    key_id1, key_id2 = key1.id, key2.id

                    # Calculate distance and movement
                    distance, movement = self._calculate_distance_and_movement(
                        key_id1, key_id2)
                    
                    # Calculate Fitts's Law time
                    fitts_time = self._calculate_fitts_time(
                        key_id1, key_id2, distance)

                    # Store in matrices
                    movement_matrix[key_id1][key_id2] = (distance, movement)
                    time_matrix[key_id1][key_id2] = fitts_time

        self.cost[self.keyboard_file]['movement_matrix'] = movement_matrix
        self.cost[self.keyboard_file]['time_matrix'] = time_matrix
        self.cost[self.keyboard_file]['matrix_size'] = matrix_size
        self._print("Costs and times for this keyboard have been cached in 2D matrices")

    def load_cost(self):
        if self.cost is None or self.debug:
            self._print("Calculating costs")
            self.calculate_cost()
            return

        if self.keyboard_file in self.cost:
            # Check if MD5 matches and Fitts parameters match
            cached_fitts = self.cost[self.keyboard_file].get('fitts_params', {})
            fitts_match = (cached_fitts.get('a') == self.fitts_a and 
                          cached_fitts.get('b') == self.fitts_b)
            
            if self.keyboard_md5 == self.cost[self.keyboard_file]['md5'] and fitts_match:
                self._print(
                    "Cost already exists in cache, nothing to calculate")
            else:
                if not fitts_match:
                    self._print("Fitts parameters differ, recalculating")
                else:
                    self._print("MD5 hashes differ, recalculating")
                self.calculate_cost()
        else:
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
                    self._print(f"✅ Successfully loaded data from {DISTANCE_CACHE}")
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
        """
        Get cached distance and movement between two keys.
        
        Args:
            key1_id: Starting key ID
            key2_id: Target key ID
            
        Returns:
            tuple: (distance, movement) where movement is a tuple of axis movements
        """
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

    def get_movement_time(self, key1_id: int, key2_id: int) -> float:
        """
        Get cached Fitts's Law movement time between two keys.
        
        Args:
            key1_id: Starting key ID
            key2_id: Target key ID
            
        Returns:
            float: Estimated movement time in milliseconds
        """
        if (self.cost and
            self.keyboard_file in self.cost and
                'time_matrix' in self.cost[self.keyboard_file]):

            time_matrix = self.cost[self.keyboard_file]['time_matrix']
            matrix_size = self.cost[self.keyboard_file]['matrix_size']

            # Check if key IDs are within bounds
            if key1_id < matrix_size and key2_id < matrix_size:
                cached_time = time_matrix[key1_id][key2_id]

                if cached_time is not None:
                    return cached_time

        # Calculate on-the-fly if not cached
        distance, _ = self._calculate_distance_and_movement(key1_id, key2_id)
        return self._calculate_fitts_time(key1_id, key2_id, distance)

    def get_distance_movement_and_time(self, key1_id: int, key2_id: int) -> tuple:
        """
        Get all cached data: distance, movement, and time between two keys.
        
        Args:
            key1_id: Starting key ID
            key2_id: Target key ID
            
        Returns:
            tuple: (distance, movement, time) where:
                - distance: float (Cartesian distance)
                - movement: tuple (axis movements)
                - time: float (Fitts's Law time in ms)
        """
        distance, movement = self.get_distance_and_movement(key1_id, key2_id)
        time = self.get_movement_time(key1_id, key2_id)
        return distance, movement, time

    def _print(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)


if __name__ == "__main__":
    import os
    from src.core.keyboard import Serial
    from src.config.file_paths import DISTANCE_CACHE

    def load_keyboard(keyboard_file):
        print(f"load_keyboard called with: keyboard_file={keyboard_file}")
        with open(keyboard_file, 'r') as f:
            print(f"Read file: '{keyboard_file}'")
            keyboard = Serial.parse(f.read())
        print(f"load_keyboard returning: keyboard_file={keyboard_file}, keyboard type={type(keyboard)}")
        return keyboard_file, keyboard

    def load_distance(keyboard_file, keyboard, debug=True):
        print(f"load_distance called with: keyboard_file={keyboard_file}, keyboard={keyboard}, debug={debug}")
        distance = DistanceCalculator(keyboard_file, keyboard, debug=debug)
        print(f"load_distance returning: distance={distance}")
        return distance

    # Test all keyboard files
    keyboard_files = [
        'src/data/keyboards/ansi_60_percent.json',
        'src/data/keyboards/ansi_60_percent_thinkpad.json',
        'src/data/keyboards/dactyl_manuform_6x6_4.json',
        'src/data/keyboards/ferris_sweep.json'
    ]

    print(f"Testing keyboard files: {keyboard_files}")

    for keyboard_file in keyboard_files:
        print(f"Processing keyboard_file: {keyboard_file}")
        if os.path.exists(keyboard_file):
            print(f"\n--- Testing {keyboard_file} ---")
            keyboard_file_loaded, keyboard = load_keyboard(keyboard_file)
            distance = load_distance(keyboard_file_loaded, keyboard)

            # Test with first key only to avoid cross-finger issues
            print(f"Keyboard has {len(keyboard.keys)} keys")
            if len(keyboard.keys) >= 1:
                # Test distance from key to itself (should be 0)
                print(f"Testing distance for key 0 to itself")
                dist, movement = distance.get_distance_and_movement(0, 0)
                time = distance.get_movement_time(0, 0)
                print(f"Distance for key 0 to itself: {dist}, Time: {time}ms")

                # Test with actual finger keys if available
                from src.core.keyboard import FingerName
                fingers = [member for member in FingerName]
                print(f"Testing finger keys for fingers: {fingers}")
                for finger in fingers:
                    finger_keys = keyboard.get_finger_keys(finger)
                    print(f"Finger {finger} has {len(finger_keys)} keys")
                    if len(finger_keys) >= 2:
                        key1_id = finger_keys[0].id
                        key2_id = finger_keys[1].id
                        print(f"Testing distance between {finger} keys {key1_id} and {key2_id}")
                        
                        # Test individual methods
                        dist, movement = distance.get_distance_and_movement(key1_id, key2_id)
                        time = distance.get_movement_time(key1_id, key2_id)
                        print(f"Distance: {dist:.2f}mm, Time: {time:.2f}ms")
                        
                        # Test combined method
                        d, m, t = distance.get_distance_movement_and_time(key1_id, key2_id)
                        print(f"Combined - Distance: {d:.2f}mm, Movement: {m}, Time: {t:.2f}ms")
                        break  # Just test first finger with multiple keys
        else:
            print(f"File not found: {keyboard_file}")
