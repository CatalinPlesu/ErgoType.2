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


class DistanctCalculator:
    def __init__(self, keyboard_file, keyboard, debug=False):
        self.debug = debug
        self._print("Distance Calculator Invoked")
        self.keyboard_file = keyboard_file
        self.keyboard = keyboard
        self.file_hash()
        self.load_cache()
        self.load_cost()
        print("here")
        self.save_cache()

    def calculate_cost(self):
        if self.cost is None:
            self.cost = {}

        if self.keyboard_file not in self.cost:
            self.cost[self.keyboard_file] = {}

        self.cost[self.keyboard_file]['md5'] = self.keyboard_md5
        fingers = [member for member in FingerName]
        finger_keys = {}
        for finger in fingers:
            finger_keys[finger] = [key.get_key_center_position()
                                   for key in self.keyboard.get_finger_keys(finger)]
        self._print("Identified keys of each finger")

        all_movements = {}
        for finger in fingers:
            x = finger_keys[finger]
            all_movements[finger] = [(x1, x2) for x1 in x for x2 in x]

        self._print("Identified all possible movements of a finger")

        movement_distance = {}
        for finger in fingers:
            for movement in all_movements[finger]:
                movement_distance[movement] = {}
                p1, p2 = movement
                movement_distance[movement]['distance'] = cartesian_distance(
                    p1, p2)
                movement_distance[movement]['movement'] = axis_movement(p1, p2)
        self.cost[self.keyboard_file]['costs'] = movement_distance
        self._print("cost's for this keyboard have been cached")

    def load_cost(self):
        if self.cost is None:
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
            self._print(f"ERROR loading data: {e}")
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

    def _print(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)
