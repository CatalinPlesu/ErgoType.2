import json
from enum import Enum
from typing import List, Dict, Any, Optional, Union

# ----------------------------
# Enums
# ----------------------------


class FingerName(Enum):
    LEFT_PINKY = 0
    LEFT_RING = 1
    LEFT_MIDDLE = 2
    LEFT_INDEX = 3
    LEFT_THUMB = 4
    RIGHT_THUMB = 5
    RIGHT_INDEX = 6
    RIGHT_MIDDLE = 7
    RIGHT_RING = 8
    RIGHT_PINKY = 9


class Finger(Enum):
    UNKNOWN = 0
    THUMB = 1
    INDEX = 2
    MIDDLE = 3
    RING = 4
    PINKY = 5


class Hand(Enum):
    UNKNOWN = 0
    LEFT = 1
    RIGHT = 2
    BOTH = 3


FINGER_NAME_MAP = {
    FingerName.LEFT_PINKY: (Finger.PINKY, Hand.LEFT),
    FingerName.LEFT_RING: (Finger.RING, Hand.LEFT),
    FingerName.LEFT_MIDDLE: (Finger.MIDDLE, Hand.LEFT),
    FingerName.LEFT_INDEX: (Finger.INDEX, Hand.LEFT),
    FingerName.LEFT_THUMB: (Finger.THUMB, Hand.LEFT),
    FingerName.RIGHT_THUMB: (Finger.THUMB, Hand.RIGHT),
    FingerName.RIGHT_INDEX: (Finger.INDEX, Hand.RIGHT),
    FingerName.RIGHT_MIDDLE: (Finger.MIDDLE, Hand.RIGHT),
    FingerName.RIGHT_RING: (Finger.RING, Hand.RIGHT),
    FingerName.RIGHT_PINKY: (Finger.PINKY, Hand.RIGHT)
}


def fingername_to_enums(fingername):
    return FINGER_NAME_MAP[fingername]


def enums_to_fingername(finger, hand):
    if finger == Finger.THUMB and hand == Hand.BOTH:
        return [FingerName.LEFT_THUMB, FingerName.RIGHT_THUMB]

    for key, value in FINGER_NAME_MAP.items():
        if value[0] == finger and value[1] == hand:
            return key

# ----------------------------
# Key Class
# ----------------------------


class Key:
    def __init__(self):
        self.color: str = "#cccccc"
        self.labels: List[Optional[str]] = [None] * 12
        self.textColor: List[Optional[str]] = [None] * 12
        self.textSize: List[Optional[float]] = [None] * 12
        self.default = {
            "textColor": "#000000",
            "textSize": 3
        }
        self.finger: Finger = Finger.UNKNOWN
        self.hand: Hand = Hand.UNKNOWN
        self.homing: bool = False
        self.x: float = 0
        self.y: float = 0
        self.z: float = 0
        self.width: float = 1
        self.height: float = 1
        self.x2: float = 0
        self.y2: float = 0
        self.width2: float = 1
        self.height2: float = 1
        self.rotation_x: float = 0
        self.rotation_y: float = 0
        self.rotation_angle: float = 0
        self.decal: bool = False
        self.ghost: bool = False
        self.stepped: bool = False
        self.nub: bool = False
        self.profile: str = ""
        self.sm: str = ""  # switch mount
        self.sb: str = ""  # switch brand
        self.st: str = ""  # switch type

    def get_height(self):
        return self.height

    def get_width(self):
        return self.width

    def get_key_center_position(self):
        """Get the geometric center of the key."""
        return (self.x + self.width/2, self.y + self.height/2, self.z)

    def get_finger_name(self):
        return enums_to_fingername(self.finger, self.hand)

    def get_labels(self) -> tuple:
        """Return a tuple of non-None labels in order."""
        result = tuple(label for label in self.labels if label is not None)
        return result if result else (None,)

    def set_labels(self, labels: Union[tuple, list]):
        """Set primary and optionally shifted label."""
        if not isinstance(labels, (tuple, list)):
            raise ValueError("Labels must be a tuple or list.")
        if len(labels) > 0:
            self.labels[0] = labels[0]
        if len(labels) > 1:
            self.labels[6] = labels[1]
        if len(labels) < 2:
            self.labels[6] = None

    def __repr__(self):
        base_repr = f"""Key(label={self.labels[0]}, shifted={
            self.labels[6]}, x={self.x}, y={self.y}, z={self.z}"""
        extra_repr = f""", finger={self.finger.name}, hand={
            self.hand.name}, homing={self.homing})"""
        return base_repr + extra_repr


# ----------------------------
# Keyboard Metadata Class
# ----------------------------
class KeyboardMetadata:
    def __init__(self):
        self.author: str = ""
        self.backcolor: str = "#eeeeee"
        self.background: Optional[Dict[str, str]] = None
        self.name: str = ""
        self.notes: str = ""
        self.radii: str = ""
        self.switchBrand: str = ""
        self.switchMount: str = ""
        self.switchType: str = ""


# ----------------------------
# Keyboard Class
# ----------------------------
class Keyboard:
    def __init__(self):
        self.meta: KeyboardMetadata = KeyboardMetadata()
        self.keys: List[Key] = []
        self._cached_homing_keys: Optional[Dict[FingerName, Key]] = None

    def _build_homing_key_cache(self):
        """Build cache mapping finger names to their homing keys."""
        if self._cached_homing_keys is not None:
            return  # Already built

        self._cached_homing_keys = {}

        for key in self.keys:
            if key.homing:
                finger_name = key.get_finger_name()
                if finger_name and isinstance(finger_name, FingerName):
                    # For each finger name, store the homing key
                    self._cached_homing_keys[finger_name] = key
                elif finger_name and isinstance(finger_name, list):
                    # Handle case where key.get_finger_name() returns a list (e.g., for BOTH hand)
                    for fn in finger_name:
                        self._cached_homing_keys[fn] = key

    def get_homing_key_for_finger_name(self, finger_name: FingerName) -> Optional[Key]:
        """
        Get the homing key for a specific finger name.
        Uses caching for efficiency.
        """
        self._build_homing_key_cache()
        return self._cached_homing_keys.get(finger_name)

    def get_finger_keys(self, finger_name: FingerName):
        return [key for key in self.keys if finger_name == enums_to_fingername(key.finger, key.hand)]
# ----------------------------
# Serial Module
# ----------------------------


class Serial:
    labelMap = [
        # 0  1  2  3  4  5  6  7  8  9 10 11   // align flags
        [0, 6, 2, 8, 9, 11, 3, 5, 1, 4, 7, 10],  # 0 = no centering
        [1, 7, -1, -1, 9, 11, 4, -1, -1, -1, -1, 10],  # 1 = center x
        [3, -1, 5, -1, 9, 11, -1, -1, 4, -1, -1, 10],  # 2 = center y
        [4, -1, -1, -1, 9, 11, -1, -1, -1, -1, -1, 10],  # 3 = center x & y
        [0, 6, 2, 8, 10, -1, 3, 5, 1, 4, 7, -1],  # 4 = center front (default)
        [1, 7, -1, -1, 10, -1, 4, -1, -1, -1, -1, -1],  # 5 = center front & x
        [3, -1, 5, -1, 10, -1, -1, -1, 4, -1, -1, -1],  # 6 = center front & y
        # 7 = center front & x & y
        [4, -1, -1, -1, 10, -1, -1, -1, -1, -1, -1, -1],
    ]

    @staticmethod
    def copy(obj):
        if not isinstance(obj, dict) and not isinstance(obj, list):
            return obj
        elif isinstance(obj, list):
            return [Serial.copy(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: Serial.copy(v) for k, v in obj.items()}
        return obj

    @staticmethod
    def reorder_labels(labels, align):
        ret = [None] * 12
        for i in range(len(labels)):
            pos = Serial.labelMap[align][i]
            if pos != -1 and labels[i]:
                ret[pos] = labels[i]
        return ret

    @staticmethod
    def deserialize_error(msg, data=None):
        error_msg = f"Error: {msg}"
        if data:
            error_msg += f":\n  {json.dumps(data)}"
        raise ValueError(error_msg)

    @staticmethod
    def deserialize(rows: List[Any]) -> Keyboard:
        if not isinstance(rows, list):
            Serial.deserialize_error("expected an array of objects")

        # Start with a default key template
        current = Key()
        kbd = Keyboard()
        align = 4

        for r in range(len(rows)):
            row = rows[r]
            if isinstance(row, list):
                for k in range(len(row)):
                    item = row[k]
                    if isinstance(item, str):
                        # --- FIXED PART 1: Copy current state BEFORE modifying current for the next key ---
                        # Create a copy of the current template's state for this specific key
                        new_key_state = Serial.copy(vars(current))

                        # Convert the copied state dictionary back into a Key object
                        key_obj = Key()
                        for attr, value in new_key_state.items():
                            setattr(key_obj, attr, value)

                        # Apply key-specific calculations and properties
                        key_obj.width2 = key_obj.width2 or current.width
                        key_obj.height2 = key_obj.height2 or current.height
                        key_obj.labels = Serial.reorder_labels(
                            item.split("\n"), align)
                        key_obj.textSize = Serial.reorder_labels(
                            key_obj.textSize, align)

                        for i in range(12):
                            if not key_obj.labels[i]:
                                key_obj.textSize[i] = None
                                key_obj.textColor[i] = None
                            if key_obj.textSize[i] == key_obj.default["textSize"]:
                                key_obj.textSize[i] = None
                            if key_obj.textColor[i] == key_obj.default["textColor"]:
                                key_obj.textColor[i] = None

                        # Add the newly created key to the keyboard
                        kbd.keys.append(key_obj)

                        # --- FIXED PART 2: Reset transient properties on the template AFTER creating the key ---
                        # Reset properties that should not carry over to the next key implicitly.
                        # These are typically set explicitly via property dictionaries.
                        # width/height/x/y are positional and handled by the loop logic.
                        # Properties like color, profile etc. *can* carry over, which is often desired.
                        # Boolean flags like homing, nub, stepped, decal, ghost usually should NOT carry over.
                        current.homing = False  # <-- KEY FIX: Reset homing
                        current.finger = Finger.UNKNOWN  # <-- KEY FIX: Reset finger
                        current.hand = Hand.UNKNOWN     # <-- KEY FIX: Reset hand
                        # Reset other transient flags if needed
                        # current.nub = False # Example, if nub should not carry over
                        # current.stepped = False
                        # current.decal = False
                        # current.ghost = False

                        # Advance the x position for the next key
                        current.x += current.width
                        # Reset width/height back to default for the next key unless overridden
                        current.width = current.height = 1
                        # Reset secondary dimensions
                        current.x2 = current.y2 = current.width2 = current.height2 = 0
                        # Note: nub, stepped, decal are NOT reset here because their state often carries
                        # over in KLE (e.g., a cluster of stepped keys). The reset above is for explicit flags.
                        # If issues persist with other flags, add them to the reset list above.

                    else:  # item is a dict (property modifier)
                        # Error check for rotation placement
                        if k != 0 and ("r" in item or "rx" in item or "ry" in item):
                            Serial.deserialize_error(
                                "rotation can only be specified on the first key in a row", item)

                        # Apply property changes to the current template
                        if "r" in item:
                            current.rotation_angle = item["r"]
                        if "rx" in item:
                            current.rotation_x = item["rx"]
                        if "ry" in item:
                            current.rotation_y = item["ry"]
                        if "a" in item:
                            align = item["a"]
                        if "f" in item:
                            current.default["textSize"] = item["f"]
                            current.textSize = [None] * 12
                        if "f2" in item:
                            for i in range(1, 12):
                                current.textSize[i] = item["f2"]
                        if "fa" in item:
                            current.textSize = item["fa"]
                        if "p" in item:
                            current.profile = item["p"]
                        if "c" in item:
                            current.color = item["c"]
                        if "t" in item:
                            split = item["t"].split("\n")
                            if split[0]:
                                current.default["textColor"] = split[0]
                            current.textColor = Serial.reorder_labels(
                                split, align)
                        if "x" in item:
                            current.x += item["x"]
                        if "y" in item:
                            current.y += item["y"]
                        if "z" in item:  # To enable sculpting more intricate 3D keyboards
                            current.z += item["z"]
                        if "w" in item:
                            current.width = current.width2 = item["w"]
                        if "h" in item:
                            current.height = current.height2 = item["h"]
                        if "x2" in item:
                            current.x2 = item["x2"]
                        if "y2" in item:
                            current.y2 = item["y2"]
                        if "w2" in item:
                            current.width2 = item["w2"]
                        if "h2" in item:
                            current.height2 = item["h2"]
                        if "n" in item:
                            current.nub = item["n"]
                        if "l" in item:
                            current.stepped = item["l"]
                        if "d" in item:
                            current.decal = item["d"]
                        if "g" in item:
                            current.ghost = item["g"]
                        if "sm" in item:
                            current.sm = item["sm"]
                        if "sb" in item:
                            current.sb = item["sb"]
                        if "st" in item:
                            current.st = item["st"]
                        if "finger" in item:
                            finger_val = item["finger"]
                            if isinstance(finger_val, str):
                                try:
                                    current.finger = Finger[finger_val.upper()]
                                except KeyError:
                                    print(f"""Warning: Invalid finger string value '{
                                          finger_val}'. Defaulting to UNKNOWN.""")
                                    current.finger = Finger.UNKNOWN
                        if "hand" in item:
                            hand_val = item["hand"]
                            if isinstance(hand_val, str):
                                try:
                                    current.hand = Hand[hand_val.upper()]
                                except KeyError:
                                    print(f"""Warning: Invalid hand string value '{
                                          hand_val}'. Defaulting to UNKNOWN.""")
                                    current.hand = Hand.UNKNOWN
                        if "homing" in item:
                            current.homing = bool(item["homing"])
                # End of row: Move to the next row
                current.y += 1
                # Reset x to the row's starting x (potentially rotated)
                current.x = current.rotation_x
            elif isinstance(row, dict):
                # Handle metadata (must be the first element)
                if r != 0:
                    Serial.deserialize_error(
                        "keyboard metadata must be the first element", row)
                for prop in vars(kbd.meta):
                    if prop in row:
                        setattr(kbd.meta, prop, row[prop])
            else:
                Serial.deserialize_error("unexpected", row)
        return kbd

    @staticmethod
    def parse(json_str: str) -> Keyboard:
        import json5
        data = json5.loads(json_str)
        return Serial.deserialize(data)
