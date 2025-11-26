# keyboard_renderer.py
"""
Keyboard renderer module for displaying keyboard layouts in Jupyter notebooks.
"""

import math
import svgwrite
from typing import List, Dict, Any
from IPython.display import SVG, display
from src.core.mapper import KeyType
from src.core.typer import Typer

# Unit sizes configuration (similar to the JavaScript version)
UNIT_SIZES = {
    "px": {
        "unit": 54,
        "strokeWidth": 1,
        "profiles": {
            "": {
                "profile": "", 
                "keySpacing": 0, 
                "bevelMargin": 6, 
                "bevelOffsetTop": 3, 
                "bevelOffsetBottom": 3, 
                "padding": 3, 
                "roundOuter": 5, 
                "roundInner": 3
            },
            "DCS": {
                "profile": "DCS", 
                "keySpacing": 0, 
                "bevelMargin": 6, 
                "bevelOffsetTop": 3, 
                "bevelOffsetBottom": 3, 
                "padding": 3, 
                "roundOuter": 5, 
                "roundInner": 3
            },
            "DSA": {
                "profile": "DSA", 
                "keySpacing": 0, 
                "bevelMargin": 6, 
                "bevelOffsetTop": 0, 
                "bevelOffsetBottom": 0, 
                "padding": 3, 
                "roundOuter": 5, 
                "roundInner": 8
            },
            "SA": {
                "profile": "SA", 
                "keySpacing": 0, 
                "bevelMargin": 6, 
                "bevelOffsetTop": 2, 
                "bevelOffsetBottom": 2, 
                "padding": 3, 
                "roundOuter": 5, 
                "roundInner": 5
            },
            "CHICKLET": {
                "profile": "CHICKLET", 
                "keySpacing": 3, 
                "bevelMargin": 1, 
                "bevelOffsetTop": 0, 
                "bevelOffsetBottom": 2, 
                "padding": 4, 
                "roundOuter": 4, 
                "roundInner": 4
            },
            "FLAT": {
                "profile": "FLAT", 
                "keySpacing": 1, 
                "bevelMargin": 1, 
                "bevelOffsetTop": 0, 
                "bevelOffsetBottom": 0, 
                "padding": 4, 
                "roundOuter": 5, 
                "roundInner": 3
            },
        }
    }
}

# Add OEM as alias for DCS
UNIT_SIZES["px"]["profiles"]["OEM"] = UNIT_SIZES["px"]["profiles"]["DCS"]

# Gruvbox color palette for keyboard renderer
DEFAULT_COLOR_PALETTE = {
    # Finger colors (for key top) - Gruvbox accent colors
    "thumb": "#CC241D",      # Gruvbox Red (dracula)
    "index": "#98971A",      # Gruvbox Green (jedi)
    "middle": "#D79921",     # Gruvbox Yellow (leia)
    "ring": "#458588",       # Gruvbox Blue (skywalker)
    "pinky": "#B16286",      # Gruvbox Purple (vader)
    
    # Hand colors (for key bottom) - Gruvbox background tones
    "left": "#8EC07C",       # Gruvbox Aqua (green-cyan)
    "right": "#BD6D2F",      # Desaturated orange (muted orange-brown)
    "both": "#A89984",       # Gruvbox Light4 (neutral gray)
    
    # Homing key modifier
    "homing_factor": 0.85    # Light homing adjustment (since gruvbox is already earthy)
}

def get_color_palette():
    """Return the current color palette"""
    return DEFAULT_COLOR_PALETTE.copy()

def set_color_palette(palette: Dict[str, Any]):
    """Update the color palette"""
    global DEFAULT_COLOR_PALETTE
    DEFAULT_COLOR_PALETTE.update(palette)

def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb: tuple) -> str:
    """Convert RGB tuple to hex color"""
    return "#{:02x}{:02x}{:02x}".format(*rgb)

def darken_color(hex_color: str, factor: float) -> str:
    """Darken a hex color by a factor"""
    r, g, b = hex_to_rgb(hex_color)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return rgb_to_hex((r, g, b))

def get_finger_color(finger) -> str:
    """Get color for a finger (accepts Finger enum or int)"""
    # Handle both enum and integer values
    if hasattr(finger, 'value'):
        finger_val = finger.value
    else:
        finger_val = finger
    
    finger_map = {
        1: DEFAULT_COLOR_PALETTE["thumb"],    # THUMB
        2: DEFAULT_COLOR_PALETTE["index"],    # INDEX
        3: DEFAULT_COLOR_PALETTE["middle"],   # MIDDLE
        4: DEFAULT_COLOR_PALETTE["ring"],     # RING
        5: DEFAULT_COLOR_PALETTE["pinky"]     # PINKY
    }
    # Return a distinct color for unknown fingers to make debugging easier
    return finger_map.get(finger_val, "#cdcdcd")  # Light red for unknown

def get_hand_color(hand) -> str:
    """Get color for a hand (accepts Hand enum or int)"""
    # Handle both enum and integer values
    if hasattr(hand, 'value'):
        hand_val = hand.value
    else:
        hand_val = hand
    
    hand_map = {
        1: DEFAULT_COLOR_PALETTE["left"],     # LEFT
        2: DEFAULT_COLOR_PALETTE["right"],    # RIGHT
        3: DEFAULT_COLOR_PALETTE["both"]      # BOTH
    }
    # Return a distinct color for unknown hands to make debugging easier
    return hand_map.get(hand_val, "#ccc")  # Light green for unknown

def get_profile(key) -> str:
    """Extract profile name from key profile string"""
    import re
    match = re.search(r'\b(SA|DSA|DCS|OEM|CHICKLET|FLAT)\b', key.profile)
    return match.group(0) if match else ""

def lighten_color(hex_color: str, factor: float) -> str:
    """Lighten a hex color by a factor using Lab color space"""
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Convert to 0-1 range
    r, g, b = [c/255.0 for c in rgb]
    
    # Convert to linear RGB
    def to_linear(c):
        if c <= 0.04045:
            return c / 12.92
        else:
            return ((c + 0.055) / 1.055) ** 2.4
    
    r_lin = to_linear(r)
    g_lin = to_linear(g)
    b_lin = to_linear(b)
    
    # Convert to XYZ
    x = 0.4124 * r_lin + 0.3576 * g_lin + 0.1805 * b_lin
    y = 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin
    z = 0.0193 * r_lin + 0.1192 * g_lin + 0.9505 * b_lin
    
    # Convert to Lab
    xn, yn, zn = 95.047, 100.000, 108.883
    x /= xn
    y /= yn
    z /= zn
    
    def xyz_to_lab(t):
        if t > 0.008856:
            return t ** (1/3)
        else:
            return (7.787 * t) + (16/116)
    
    fx = xyz_to_lab(x)
    fy = xyz_to_lab(y)
    fz = xyz_to_lab(z)
    
    l = (116 * fy) - 16
    a = 500 * (fx - fy)
    b_lab = 200 * (fy - fz)
    
    # Lighten L component
    l = min(100, l * factor)
    
    # Convert back to XYZ
    y = (l + 16) / 116
    x = a / 500 + y
    z = y - b_lab / 200
    
    def lab_to_xyz(t):
        tt = t**3
        if tt > 0.008856:
            return tt
        else:
            return (t - 16/116) / 7.787
    
    x = xn * lab_to_xyz(x)
    y = yn * lab_to_xyz(y)
    z = zn * lab_to_xyz(z)
    
    # Convert to linear RGB
    r_lin = 3.2406 * x - 1.5372 * y - 0.4986 * z
    g_lin = -0.9689 * x + 1.8758 * y + 0.0415 * z
    b_lin = 0.0557 * x - 0.2040 * y + 1.0570 * z
    
    # Convert to sRGB
    def to_srgb(c):
        if c <= 0.0031308:
            return 12.92 * c
        else:
            return 1.055 * (c ** (1/2.4)) - 0.055
    
    r = max(0, min(1, to_srgb(r_lin)))
    g = max(0, min(1, to_srgb(g_lin)))
    b = max(0, min(1, to_srgb(b_lin)))
    
    # Convert to hex
    return "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))

def get_render_params(key, sizes: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate rendering parameters for a key"""
    parms = {}
    
    # Check if key is J-shaped
    parms["jShaped"] = (
        key.width != key.width2 or 
        key.height != key.height2 or 
        key.x2 != 0 or 
        key.y2 != 0
    )
    
    # Overall dimensions of the unit square(s)
    parms["capwidth"] = sizes["unit"] * key.width
    parms["capheight"] = sizes["unit"] * key.height
    parms["capx"] = sizes["unit"] * key.x
    parms["capy"] = sizes["unit"] * key.y
    
    if parms["jShaped"]:
        parms["capwidth2"] = sizes["unit"] * key.width2
        parms["capheight2"] = sizes["unit"] * key.height2
        parms["capx2"] = sizes["unit"] * (key.x + key.x2)
        parms["capy2"] = sizes["unit"] * (key.y + key.y2)
    
    # Dimensions of the outer part of the cap
    parms["outercapwidth"] = parms["capwidth"] - sizes["keySpacing"] * 2
    parms["outercapheight"] = parms["capheight"] - sizes["keySpacing"] * 2
    parms["outercapx"] = parms["capx"] + sizes["keySpacing"]
    parms["outercapy"] = parms["capy"] + sizes["keySpacing"]
    
    if parms["jShaped"]:
        parms["outercapx2"] = parms["capx2"] + sizes["keySpacing"]
        parms["outercapy2"] = parms["capy2"] + sizes["keySpacing"]
        parms["outercapwidth2"] = parms["capwidth2"] - sizes["keySpacing"] * 2
        parms["outercapheight2"] = parms["capheight2"] - sizes["keySpacing"] * 2
    
    # Dimensions of the top of the cap - ensure there's enough margin to see hand color
    bevel_margin = max(sizes["bevelMargin"], 4)  # Ensure at least 4px margin
    parms["innercapwidth"] = parms["outercapwidth"] - bevel_margin * 2
    parms["innercapheight"] = parms["outercapheight"] - bevel_margin * 2 - (sizes["bevelOffsetBottom"] - sizes["bevelOffsetTop"])
    parms["innercapx"] = parms["outercapx"] + bevel_margin
    parms["innercapy"] = parms["outercapy"] + bevel_margin - sizes["bevelOffsetTop"]
    
    if parms["jShaped"]:
        parms["innercapwidth2"] = parms["outercapwidth2"] - bevel_margin * 2
        parms["innercapheight2"] = parms["outercapheight2"] - bevel_margin * 2
        parms["innercapx2"] = parms["outercapx2"] + bevel_margin
        parms["innercapy2"] = parms["outercapy2"] + bevel_margin - sizes["bevelOffsetTop"]
    
    # Dimensions of the text part of the cap
    parms["textcapwidth"] = parms["innercapwidth"] - sizes["padding"] * 2
    parms["textcapheight"] = parms["innercapheight"] - sizes["padding"] * 2
    parms["textcapx"] = parms["innercapx"] + sizes["padding"]
    parms["textcapy"] = parms["innercapy"] + sizes["padding"]
    
    # Determine base colors
    finger_color = get_finger_color(key.finger)
    hand_color = get_hand_color(key.hand)
    
    # Apply homing key modifier to the finger color (top part)
    if key.homing:
        finger_color = darken_color(finger_color, DEFAULT_COLOR_PALETTE["homing_factor"])
    
    # Colors - finger color is for inner (top) part, hand color for outer (bottom)
    parms["lightColor"] = finger_color  # Top part of keycap (inner rectangle)
    parms["darkColor"] = hand_color     # Bottom part of keycap (outer rectangle)
    
    # Rotation calculations
    parms["origin_x"] = sizes["unit"] * key.rotation_x
    parms["origin_y"] = sizes["unit"] * key.rotation_y
    
    # Create transformation matrix functions
    angle_rad = math.radians(key.rotation_angle)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    # Translation to origin
    tx1, ty1 = -parms["origin_x"], -parms["origin_y"]
    # Translation back
    tx2, ty2 = parms["origin_x"], parms["origin_y"]
    
    # Combined transformation function
    def transform_point(x, y):
        # Apply first translation
        x, y = x + tx1, y + ty1
        # Apply rotation
        new_x = x * cos_a - y * sin_a
        new_y = x * sin_a + y * cos_a
        # Apply second translation
        new_x, new_y = new_x + tx2, new_y + ty2
        return new_x, new_y
    
    # Calculate bounding box
    parms["rect"] = {
        "x": parms["capx"],
        "y": parms["capy"],
        "w": parms["capwidth"],
        "h": parms["capheight"],
        "x2": parms["capx"] + parms["capwidth"],
        "y2": parms["capy"] + parms["capheight"]
    }
    
    if parms["jShaped"]:
        parms["rect2"] = {
            "x": parms["capx2"],
            "y": parms["capy2"],
            "w": parms["capwidth2"],
            "h": parms["capheight2"],
            "x2": parms["capx2"] + parms["capwidth2"],
            "y2": parms["capy2"] + parms["capheight2"]
        }
    else:
        parms["rect2"] = parms["rect"]
    
    # Transform corners and find bounding box
    corners = [
        (parms["rect"]["x"], parms["rect"]["y"]),
        (parms["rect"]["x"], parms["rect"]["y2"]),
        (parms["rect"]["x2"], parms["rect"]["y"]),
        (parms["rect"]["x2"], parms["rect"]["y2"])
    ]
    
    if parms["jShaped"]:
        corners.extend([
            (parms["rect2"]["x"], parms["rect2"]["y"]),
            (parms["rect2"]["x"], parms["rect2"]["y2"]),
            (parms["rect2"]["x2"], parms["rect2"]["y"]),
            (parms["rect2"]["x2"], parms["rect2"]["y2"])
        ])
    
    transformed_corners = [transform_point(x, y) for x, y in corners]
    
    parms["bbox"] = {
        "x": min(pt[0] for pt in transformed_corners),
        "y": min(pt[1] for pt in transformed_corners),
        "x2": max(pt[0] for pt in transformed_corners),
        "y2": max(pt[1] for pt in transformed_corners)
    }
    parms["bbox"]["w"] = parms["bbox"]["x2"] - parms["bbox"]["x"]
    parms["bbox"]["h"] = parms["bbox"]["y2"] - parms["bbox"]["y"]
    
    return parms

def draw_keycap(dwg, key, index: int, sizes: Dict[str, Any]) -> svgwrite.container.Group:
    """Draw a single keycap as SVG elements"""
    parms = get_render_params(key, sizes)
    
    # Create group for this key
    group = dwg.g(id=f"key-{index}")
    
    # Apply rotation if needed
    if key.rotation_angle != 0:
        transform = f"rotate({key.rotation_angle}, {parms['origin_x']}, {parms['origin_y']})"
        group.attribs['transform'] = transform
    
    # Draw outer cap (bottom part - hand color)
    if parms["jShaped"]:
        # For J-shaped keys, we need to create a path
        path_data = [
            f"M {parms['outercapx']},{parms['outercapy']}",
            f"L {parms['outercapx']},{parms['outercapy']+parms['outercapheight']}",
            f"L {parms['outercapx']+parms['outercapwidth']},{parms['outercapy']+parms['outercapheight']}",
            f"L {parms['outercapx2']+parms['outercapwidth2']},{parms['outercapy2']+parms['outercapheight2']}",
            f"L {parms['outercapx2']+parms['outercapwidth2']},{parms['outercapy2']}",
            f"L {parms['outercapx2']},{parms['outercapy2']}",
            f"L {parms['outercapx']},{parms['outercapy']}",
            "Z"
        ]
        outer_path = dwg.path(
            d=" ".join(path_data),
            fill=parms["darkColor"],
            stroke="black",
            stroke_width=sizes["strokeWidth"]
        )
    else:
        # Simple rectangle for regular keys
        outer_path = dwg.rect(
            insert=(parms["outercapx"], parms["outercapy"]),
            size=(parms["outercapwidth"], parms["outercapheight"]),
            rx=sizes["roundOuter"],
            ry=sizes["roundOuter"],
            fill=parms["darkColor"],
            stroke="black",
            stroke_width=sizes["strokeWidth"]
        )
    
    group.add(outer_path)
    
    # Draw inner cap (top part - finger color)
    if parms["jShaped"]:
        # For J-shaped keys, create inner path
        path_data = [
            f"M {parms['innercapx']},{parms['innercapy']}",
            f"L {parms['innercapx']},{parms['innercapy']+parms['innercapheight']}",
            f"L {parms['innercapx']+parms['innercapwidth']},{parms['innercapy']+parms['innercapheight']}",
            f"L {parms['innercapx2']+parms['innercapwidth2']},{parms['innercapy2']+parms['innercapheight2']}",
            f"L {parms['innercapx2']+parms['innercapwidth2']},{parms['innercapy2']}",
            f"L {parms['innercapx2']},{parms['innercapy2']}",
            f"L {parms['innercapx']},{parms['innercapy']}",
            "Z"
        ]
        inner_path = dwg.path(
            d=" ".join(path_data),
            fill=parms["lightColor"],
            stroke="black",
            stroke_width=sizes["strokeWidth"]
        )
    else:
        # Simple rectangle for regular keys
        inner_path = dwg.rect(
            insert=(parms["innercapx"], parms["innercapy"]),
            size=(parms["innercapwidth"], parms["innercapheight"]),
            rx=sizes["roundInner"],
            ry=sizes["roundInner"],
            fill=parms["lightColor"],
            stroke="black",
            stroke_width=sizes["strokeWidth"]
        )
    
    group.add(inner_path)
    
    # Draw text labels
    labels = key.get_labels()
    for i, label in enumerate(labels):
        if label:
            # Position text in the center of the text area
            text_x = parms["textcapx"] + parms["textcapwidth"] / 2
            # For multiple labels, position them vertically
            if len(labels) > 1:
                text_y = parms["textcapy"] + (i + 1) * parms["textcapheight"] / (len(labels) + 1)
            else:
                text_y = parms["textcapy"] + parms["textcapheight"] / 2
            
            # Get text color (default to black if not specified)
            text_color = key.textColor[i] if i < len(key.textColor) and key.textColor[i] else "#000000"
            
            # Get text size (default to 3 if not specified)
            text_size = key.textSize[i] if i < len(key.textSize) and key.textSize[i] else key.default["textSize"]
            font_size = text_size * 4  # Scale factor for visibility
            
            text_elem = dwg.text(
                label,
                insert=(text_x, text_y),
                text_anchor="middle",
                dominant_baseline="middle",
                fill=text_color,
                font_size=font_size,
                font_family="Arial, sans-serif"
            )
            group.add(text_elem)
    
    return group

def render_keyboard(keyboard, units: str = "px") -> SVG:
    """
    Render a keyboard to SVG and return as IPython SVG for Jupyter display.
    
    Args:
        keyboard: Keyboard object with meta and keys attributes
        units: Unit system to use ("px" only supported currently)
    
    Returns:
        IPython.display.SVG object ready for display in Jupyter
    """
    # Get sizes for the unit system
    unit_config = UNIT_SIZES[units]
    sizes_base = unit_config["profiles"]
    
    # Calculate overall bounding box
    bbox = {"x": float('inf'), "y": float('inf'), "x2": float('-inf'), "y2": float('-inf')}
    
    # First pass: calculate bounding box
    for key in keyboard.keys:
        profile = get_profile(key)
        # Create a complete size dictionary with unit and strokeWidth
        key_sizes = sizes_base[profile] if profile in sizes_base else sizes_base[""]
        key_sizes["unit"] = unit_config["unit"]
        key_sizes["strokeWidth"] = unit_config["strokeWidth"]
        
        parms = get_render_params(key, key_sizes)
        bbox["x"] = min(bbox["x"], parms["bbox"]["x"])
        bbox["y"] = min(bbox["y"], parms["bbox"]["y"])
        bbox["x2"] = max(bbox["x2"], parms["bbox"]["x2"])
        bbox["y2"] = max(bbox["y2"], parms["bbox"]["y2"])
    
    # Add margins
    margin = 10
    bbox["x"] -= margin
    bbox["y"] -= margin
    bbox["x2"] += margin
    bbox["y2"] += margin
    width = bbox["x2"] - bbox["x"]
    height = bbox["y2"] - bbox["y"]
    
    # Create SVG drawing
    dwg = svgwrite.Drawing(
        size=(f"{width}px", f"{height}px"),
        viewBox=(f"{bbox['x']} {bbox['y']} {width} {height}")
    )
    
    # Add background
    background = dwg.rect(
        insert=(bbox["x"], bbox["y"]),
        size=(width, height),
        fill=keyboard.meta.backcolor
    )
    dwg.add(background)
    
    # Draw each key
    for i, key in enumerate(keyboard.keys):
        profile = get_profile(key)
        # Create a complete size dictionary with unit and strokeWidth
        key_sizes = sizes_base[profile] if profile in sizes_base else sizes_base[""]
        key_sizes["unit"] = unit_config["unit"]
        key_sizes["strokeWidth"] = unit_config["strokeWidth"]
        
        key_group = draw_keycap(dwg, key, i, key_sizes)
        dwg.add(key_group)
    
    # Return as IPython SVG for Jupyter display
    return SVG(dwg.tostring())

# Convenience function for Jupyter
def show_keyboard(keyboard):
    """
    Display a keyboard in a Jupyter notebook.
    
    Args:
        keyboard: Keyboard object to display
    """
    svg = render_keyboard(keyboard)
    display(svg)

def render_keyboard_with_heatmap(keyboard, char_frequencies: Dict, layer_idx: int = 0, 
                               freq_range: float = 1.0, min_freq: float = 0.0, layout=None) -> SVG:
    """
    Render a keyboard to SVG with heatmap overlay and return as IPython SVG for Jupyter display.
    
    Args:
        keyboard: Keyboard object with meta and keys attributes
        char_frequencies: Dictionary of character frequency data
        layer_idx: Layer to display (default 0)
        freq_range: Range of frequencies for normalization
        min_freq: Minimum frequency value
        layout: Layout object to get character mappings
    
    Returns:
        IPython.display.SVG object ready for display in Jupyter
    """
    # Get sizes for the unit system
    unit_config = UNIT_SIZES["px"]
    sizes_base = unit_config["profiles"]
    
    # Calculate overall bounding box
    bbox = {"x": float('inf'), "y": float('inf'), "x2": float('-inf'), "y2": float('-inf')}
    
    # First pass: calculate bounding box
    for key in keyboard.keys:
        profile = get_profile(key)
        # Create a complete size dictionary with unit and strokeWidth
        key_sizes = sizes_base[profile] if profile in sizes_base else sizes_base[""]
        key_sizes["unit"] = unit_config["unit"]
        key_sizes["strokeWidth"] = unit_config["strokeWidth"]
        
        parms = get_render_params(key, key_sizes)
        bbox["x"] = min(bbox["x"], parms["bbox"]["x"])
        bbox["y"] = min(bbox["y"], parms["bbox"]["y"])
        bbox["x2"] = max(bbox["x2"], parms["bbox"]["x2"])
        bbox["y2"] = max(bbox["y2"], parms["bbox"]["y2"])
    
    # Add margins
    margin = 10
    bbox["x"] -= margin
    bbox["y"] -= margin
    bbox["x2"] += margin
    bbox["y2"] += margin
    width = bbox["x2"] - bbox["x"]
    height = bbox["y2"] - bbox["y"]
    
    # Create SVG drawing
    dwg = svgwrite.Drawing(
        size=(f"{width}px", f"{height}px"),
        viewBox=(f"{bbox['x']} {bbox['y']} {width} {height}")
    )
    
    # Add background
    background = dwg.rect(
        insert=(bbox["x"], bbox["y"]),
        size=(width, height),
        fill=keyboard.meta.backcolor
    )
    dwg.add(background)
    
    # Draw each key
    for i, key in enumerate(keyboard.keys):
        profile = get_profile(key)
        # Create a complete size dictionary with unit and strokeWidth
        key_sizes = sizes_base[profile] if profile in sizes_base else sizes_base[""]
        key_sizes["unit"] = unit_config["unit"]
        key_sizes["strokeWidth"] = unit_config["strokeWidth"]
        
        key_group = draw_keycap(dwg, key, i, key_sizes)
        dwg.add(key_group)
    
    # Add heatmap overlay
    for key in keyboard.keys:
        key_id = key.id
        
        # Get character from layout mapping if available
        char = None
        if layout and hasattr(layout, 'mapper') and layout.mapper:
            # Check if key has mapping for the specified layer
            if (key_id, layer_idx) in layout.mapper.data:
                key_data = layout.mapper.data[(key_id, layer_idx)]
                if key_data.key_type == KeyType.CHAR:
                    # For CHAR type, value is a tuple (unshifted, shifted)
                    char = key_data.value[0]  # Use unshifted character
                elif key_data.key_type == KeyType.SPECIAL_CHAR:
                    # For SPECIAL_CHAR type, value is a tuple (character, display_name)
                    char = key_data.value[0]  # Use actual character
                elif key_data.key_type == KeyType.CONTROL and key_data.value == 'Shift':
                    # Handle shift keys specially
                    char = 'SHIFT'  # Special marker for shift keys
                elif key_data.key_type == KeyType.LAYER:
                    # Handle layer keys - use the layer name as the character for heatmap
                    char = key_data.value  # Use the layer name like "AltGr"
        
        # Fallback to key labels if no layout mapping
        if char is None:
            labels = key.get_labels()
            if labels and len(labels) > 0 and labels[0]:
                label = labels[0]
                # Try to map common labels to actual characters
                if label == 'Space':
                    char = ' '
                elif label == 'Tab':
                    char = '\t'
                elif label == 'Enter':
                    char = '\n'
                elif label == 'AltGr':
                    # Layer key (modifier) - use layer name for heatmap
                    char = 'AltGr'
                else:
                    char = label  # Use label as-is for other cases
        
        # Calculate total frequency for this character or shift key
        total_freq = 0.0
        if char == 'SHIFT' and layout:
            # For shift keys, calculate frequency based on uppercase characters
            shift_key_freq = 0.0
            uppercase_chars = [c for c in char_frequencies.keys() if c.isupper()]
            
            for upper_char in uppercase_chars:
                # Find the base key for this uppercase character
                base_key_id, _, _ = layout.find_key_for_char(upper_char.lower())
                if base_key_id:
                    # Get the appropriate shift key for this character (opposite hand)
                    shift_keys = layout.mapper.filter_data(
                        lambda k_id, l_id, value: value.key_type == KeyType.CONTROL and value.value == 'Shift'
                    )
                    typer = Typer(keyboard, None, layout, None, debug=False)  # We don't need distance for this
                    shift_key_for_char = typer.get_shift_key_for_char(upper_char, base_key_id, shift_keys)
                    
                    # If this shift key is used for this character, add its frequency
                    if shift_key_for_char == key_id:
                        shift_key_freq += char_frequencies[upper_char]['relative']
            
            total_freq = shift_key_freq
        elif char == 'AltGr' and layout:
            # For AltGr keys, calculate frequency based on layer 1 characters
            altgr_key_freq = 0.0
            
            # Get all AltGr layer 1 characters (target characters)
            layer1_chars = []
            for (char_key_id, layer_idx), key_data in layout.mapper.data.items():
                if layer_idx == 1 and key_data.key_type == KeyType.CHAR:
                    # For layer 1, we want the target characters (second element of tuple)
                    if isinstance(key_data.value, tuple) and len(key_data.value) >= 2:
                        layer1_chars.append(key_data.value[1])
                    else:
                        layer1_chars.append(key_data.value)
            
            # Get all AltGr modifier keys
            altgr_modifier_keys = layout.mapper.filter_data(
                lambda k_id, l_id, value: value.key_type == KeyType.LAYER and value.value == 'AltGr'
            )
            
            # For each layer 1 character, find if it maps to this AltGr key
            for layer1_char in layer1_chars:
                if layer1_char in char_frequencies:
                    # Find the base key for this layer 1 character
                    base_key_id, _, _ = layout.find_key_for_char(layer1_char)
                    if base_key_id:
                        # Get the appropriate AltGr key for this character
                        typer = Typer(keyboard, None, layout, None, debug=False)
                        altgr_key_for_char = typer.get_altgr_key_for_char(layer1_char, base_key_id, altgr_modifier_keys)
                        
                        # If this AltGr key is used for this character, add its frequency
                        if altgr_key_for_char == key_id:
                            altgr_key_freq += char_frequencies[layer1_char]['relative']
            
            total_freq = altgr_key_freq
        elif char and char in char_frequencies:
            # For regular characters, use their direct frequency
            total_freq = char_frequencies[char]['relative']
        
        if total_freq > 0:
                # Normalize frequency (0-1 range)
                normalized_freq = (total_freq - min_freq) / freq_range
                
                # Calculate opacity (0.3 to 1.0) - increased minimum opacity
                opacity = 0.3 + (normalized_freq * 0.7)
                
                # Calculate circle size based on key size - increased size
                key_width = key.width * 54  # 54px unit size
                key_height = key.height * 54
                circle_radius = min(key_width, key_height) * 0.35  # Increased from 0.2 to 0.35
                
                # Calculate key center position
                center_x = key.x * 54 + key_width / 2
                center_y = key.y * 54 + key_height / 2
                
                # Enhanced color gradient from blue (low) to red (high)
                # Make colors more vibrant
                red = int(255 * normalized_freq)
                blue = int(255 * (1 - normalized_freq))
                green = int(50 * (1 - abs(normalized_freq - 0.5) * 2))  # Less green, more vibrant
                color = f"#{red:02x}{green:02x}{blue:02x}"
                
                # Add heatmap circle with stroke for better visibility
                circle = dwg.circle(
                    center=(center_x, center_y),
                    r=circle_radius,
                    fill=color,
                    fill_opacity=opacity,
                    stroke="black",
                    stroke_width=0.5
                )
                dwg.add(circle)
    
    # Return as IPython SVG for Jupyter display
    return SVG(dwg.tostring())


def render_keyboard_heatmap_only(keyboard, char_frequencies: dict, layer_idx: int = 0, 
                                 freq_range: float = 1.0, min_freq: float = 0.0, layout=None) -> SVG:
    """
    Render a keyboard to SVG with heatmap overlay only (no bubbles, grey-to-red gradient).
    Keys are grey by default, with red heatmap overlay showing usage intensity.
    
    Args:
        keyboard: Keyboard object with meta and keys attributes
        char_frequencies: Dictionary of character frequency data
        layer_idx: Layer to display (default 0)
        freq_range: Range of frequencies for normalization
        min_freq: Minimum frequency value
        layout: Layout object to get character mappings
    
    Returns:
        IPython.display.SVG object ready for display in Jupyter
    """
    # Get sizes for the unit system
    unit_config = UNIT_SIZES["px"]
    sizes_base = unit_config["profiles"]
    
    # Calculate overall bounding box
    bbox = {"x": float('inf'), "y": float('inf'), "x2": float('-inf'), "y2": float('-inf')}
    
    # First pass: calculate bounding box
    for key in keyboard.keys:
        profile = get_profile(key)
        # Create a complete size dictionary with unit and strokeWidth
        key_sizes = sizes_base[profile] if profile in sizes_base else sizes_base[""]
        key_sizes["unit"] = unit_config["unit"]
        key_sizes["strokeWidth"] = unit_config["strokeWidth"]
        
        parms = get_render_params(key, key_sizes)
        bbox["x"] = min(bbox["x"], parms["bbox"]["x"])
        bbox["y"] = min(bbox["y"], parms["bbox"]["y"])
        bbox["x2"] = max(bbox["x2"], parms["bbox"]["x2"])
        bbox["y2"] = max(bbox["y2"], parms["bbox"]["y2"])
    
    # Add margins
    margin = 10
    bbox["x"] -= margin
    bbox["y"] -= margin
    bbox["x2"] += margin
    bbox["y2"] += margin
    width = bbox["x2"] - bbox["x"]
    height = bbox["y2"] - bbox["y"]
    
    # Create SVG drawing
    dwg = svgwrite.Drawing(
        size=(f"{width}px", f"{height}px"),
        viewBox=(f"{bbox['x']} {bbox['y']} {width} {height}")
    )

    # Add background
    background = dwg.rect(
        insert=(bbox["x"], bbox["y"]),
        size=(width, height),
        fill=keyboard.meta.backcolor
    )
    dwg.add(background)
    
    # Draw each key with grey base color using proper key styling
    for i, key in enumerate(keyboard.keys):
        profile = get_profile(key)
        # Create a complete size dictionary with unit and strokeWidth
        key_sizes = sizes_base[profile] if profile in sizes_base else sizes_base[""]
        key_sizes["unit"] = unit_config["unit"]
        key_sizes["strokeWidth"] = unit_config["strokeWidth"]
        
        # Get key render parameters
        parms = get_render_params(key, key_sizes)
        
        # Create key group
        key_group = dwg.g(id=f"key-{i}")
        
        # Apply rotation if needed
        if key.rotation_angle != 0:
            transform = f"rotate({key.rotation_angle}, {parms['origin_x']}, {parms['origin_y']})"
            key_group.attribs['transform'] = transform
        
        # Draw outer cap (bottom part - grey base)
        if parms.get("jShaped", False):
            # For J-shaped keys, we need to create a path
            path_data = [
                f"M {parms['outercapx']},{parms['outercapy']}",
                f"L {parms['outercapx']},{parms['outercapy']+parms['outercapheight']}",
                f"L {parms['outercapx']+parms['outercapwidth']},{parms['outercapy']+parms['outercapheight']}",
                f"L {parms['outercapx2']+parms['outercapwidth2']},{parms['outercapy2']+parms['outercapheight2']}",
                f"L {parms['outercapx2']+parms['outercapwidth2']},{parms['outercapy2']}",
                f"L {parms['outercapx2']},{parms['outercapy2']}",
                f"L {parms['outercapx']},{parms['outercapy']}",
                "Z"
            ]
            outer_path = dwg.path(
                d=" ".join(path_data),
                fill="#e0e0e0",  # Light grey base color
                stroke="black",
                stroke_width=key_sizes["strokeWidth"]
            )
        else:
            # Simple rectangle for regular keys
            outer_path = dwg.rect(
                insert=(parms["outercapx"], parms["outercapy"]),
                size=(parms["outercapwidth"], parms["outercapheight"]),
                rx=key_sizes["roundOuter"],
                ry=key_sizes["roundOuter"],
                fill="#e0e0e0",  # Light grey base color
                stroke="black",
                stroke_width=key_sizes["strokeWidth"]
            )
        
        key_group.add(outer_path)
        
        # Draw inner cap (top part - grey base)
        if parms.get("jShaped", False):
            # For J-shaped keys, create inner path
            path_data = [
                f"M {parms['innercapx']},{parms['innercapy']}",
                f"L {parms['innercapx']},{parms['innercapy']+parms['innercapheight']}",
                f"L {parms['innercapx']+parms['innercapwidth']},{parms['innercapy']+parms['innercapheight']}",
                f"L {parms['innercapx2']+parms['innercapwidth2']},{parms['innercapy2']+parms['innercapheight2']}",
                f"L {parms['innercapx2']+parms['innercapwidth2']},{parms['innercapy2']}",
                f"L {parms['innercapx2']},{parms['innercapy2']}",
                f"L {parms['innercapx']},{parms['innercapy']}",
                "Z"
            ]
            inner_path = dwg.path(
                d=" ".join(path_data),
                fill="#e0e0e0",  # Light grey base color
                stroke="black",
                stroke_width=key_sizes["strokeWidth"]
            )
        else:
            # Simple rectangle for regular keys
            inner_path = dwg.rect(
                insert=(parms["innercapx"], parms["innercapy"]),
                size=(parms["innercapwidth"], parms["innercapheight"]),
                rx=key_sizes["roundInner"],
                ry=key_sizes["roundInner"],
                fill="#e0e0e0",  # Light grey base color
                stroke="black",
                stroke_width=key_sizes["strokeWidth"]
            )
        
        key_group.add(inner_path)
        
        # Add key labels (proper positioning like layout drawing)
        labels = key.get_labels()
        for i, label in enumerate(labels):
            if label:
                # Position text in the center of the text area
                text_x = parms["textcapx"] + parms["textcapwidth"] / 2
                # For multiple labels, position them vertically
                if len(labels) > 1:
                    text_y = parms["textcapy"] + (i + 1) * parms["textcapheight"] / (len(labels) + 1)
                else:
                    text_y = parms["textcapy"] + parms["textcapheight"] / 2
                
                # Get text color (default to black if not specified)
                text_color = key.textColor[i] if i < len(key.textColor) and key.textColor[i] else "#000000"
                
                # Get text size (default to 3 if not specified)
                text_size = key.textSize[i] if i < len(key.textSize) and key.textSize[i] else key.default["textSize"]
                font_size = text_size * 4  # Scale factor for visibility
                
                text_elem = dwg.text(
                    label,
                    insert=(text_x, text_y),
                    text_anchor="middle",
                    dominant_baseline="middle",
                    fill=text_color,
                    font_size=font_size,
                    font_family="Arial, sans-serif"
                )
                key_group.add(text_elem)
        
        dwg.add(key_group)

    # Add heatmap overlay - now as solid red fill instead of bubbles
    for key in keyboard.keys:
        key_id = key.id
        
        # Get character from layout mapping if available
        char = None
        if layout and hasattr(layout, 'mapper') and layout.mapper:
            # Check if key has mapping for the specified layer
            if (key_id, layer_idx) in layout.mapper.data:
                key_data = layout.mapper.data[(key_id, layer_idx)]
                if key_data.key_type == KeyType.CHAR:
                    # For CHAR type, value is a tuple (unshifted, shifted)
                    char = key_data.value[0]  # Use unshifted character
                elif key_data.key_type == KeyType.SPECIAL_CHAR:
                    # For SPECIAL_CHAR type, value is a tuple (character, display_name)
                    char = key_data.value[0]  # Use actual character
                elif key_data.key_type == KeyType.CONTROL and key_data.value == 'Shift':
                    # Handle shift keys specially
                    char = 'SHIFT'  # Special marker for shift keys
                elif key_data.key_type == KeyType.LAYER:
                    # Handle layer keys - use the layer name as the character for heatmap
                    char = key_data.value  # Use the layer name like "AltGr"
        
        # Fallback to key labels if no layout mapping
        if char is None:
            labels = key.get_labels()
            if labels and len(labels) > 0 and labels[0]:
                label = labels[0]
                # Try to map common labels to actual characters
                if label == 'Space':
                    char = ' '
                elif label == 'Tab':
                    char = '\t'
                elif label == 'Enter':
                    char = '\n'
                elif label == 'AltGr':
                    # Layer key (modifier) - use layer name for heatmap
                    char = 'AltGr'
                else:
                    char = label  # Use label as-is for other cases
        
        # Calculate total frequency for this character or shift key
        total_freq = 0.0
        if char == 'SHIFT' and layout:
            # For shift keys, calculate frequency based on uppercase characters
            shift_key_freq = 0.0
            uppercase_chars = [c for c in char_frequencies.keys() if c.isupper()]
            
            for upper_char in uppercase_chars:
                # Find the base key for this uppercase character
                base_key_id, _, _ = layout.find_key_for_char(upper_char.lower())
                if base_key_id:
                    # Get the appropriate shift key for this character (opposite hand)
                    shift_keys = layout.mapper.filter_data(
                        lambda k_id, l_id, value: value.key_type == KeyType.CONTROL and value.value == 'Shift'
                    )
                    typer = Typer(keyboard, None, layout, None, debug=False)  # We don't need distance for this
                    shift_key_for_char = typer.get_shift_key_for_char(upper_char, base_key_id, shift_keys)
                    
                    # If this shift key is used for this character, add its frequency
                    if shift_key_for_char == key_id:
                        shift_key_freq += char_frequencies[upper_char]['relative']
            
            total_freq = shift_key_freq
        elif char == 'AltGr' and layout:
            # For AltGr keys, calculate frequency based on layer 1 characters
            altgr_key_freq = 0.0
            
            # Get all AltGr layer 1 characters (target characters)
            layer1_chars = []
            for (char_key_id, layer_idx), key_data in layout.mapper.data.items():
                if layer_idx == 1 and key_data.key_type == KeyType.CHAR:
                    # For layer 1, we want the target characters (second element of tuple)
                    if isinstance(key_data.value, tuple) and len(key_data.value) >= 2:
                        layer1_chars.append(key_data.value[1])
                    else:
                        layer1_chars.append(key_data.value)
            
            # Get all AltGr modifier keys
            altgr_modifier_keys = layout.mapper.filter_data(
                lambda k_id, l_id, value: value.key_type == KeyType.LAYER and value.value == 'AltGr'
            )
            
            # For each layer 1 character, find if it maps to this AltGr key
            for layer1_char in layer1_chars:
                if layer1_char in char_frequencies:
                    # Find the base key for this layer 1 character
                    base_key_id, _, _ = layout.find_key_for_char(layer1_char)
                    if base_key_id:
                        # Get the appropriate AltGr key for this character
                        typer = Typer(keyboard, None, layout, None, debug=False)
                        altgr_key_for_char = typer.get_altgr_key_for_char(layer1_char, base_key_id, altgr_modifier_keys)
                        
                        # If this AltGr key is used for this character, add its frequency
                        if altgr_key_for_char == key_id:
                            altgr_key_freq += char_frequencies[layer1_char]['relative']
            
            total_freq = altgr_key_freq
        elif char and char in char_frequencies:
            # For regular characters, use their direct frequency
            total_freq = char_frequencies[char]['relative']
        
        if total_freq > 0:
            # EXCLUDE SPACEBAR from frequency normalization to make other keys more visible
            # First, calculate frequency range excluding space character
            non_space_freqs = []
            for ch, freq_data in char_frequencies.items():
                if isinstance(freq_data, dict) and ch != ' ':
                    non_space_freqs.append(freq_data.get('relative', 0))
            
            if non_space_freqs:
                min_freq_non_space = min(non_space_freqs)
                max_freq_non_space = max(non_space_freqs)
                freq_range_non_space = max_freq_non_space - min_freq_non_space if max_freq_non_space > min_freq_non_space else 1.0
            else:
                min_freq_non_space = 0.0
                freq_range_non_space = 1.0
            
            # For spacebar, use a separate scale or skip it entirely
            if char == ' ':
                # Skip spacebar heatmap to avoid dominating the visualization
                continue
                # Alternative: use reduced intensity for spacebar
                # normalized_freq = min(total_freq / max_freq_non_space, 1.0) * 0.3  # Reduced max intensity
            else:
                # Normalize frequency using non-space range for better visibility
                normalized_freq = (total_freq - min_freq_non_space) / freq_range_non_space
            
            # Calculate red intensity (light red to dark red)
            red_intensity = int(255 * normalized_freq)
            red_color = f"#{red_intensity:02x}0000"  # Red gradient from #ff0000 (bright red) to #000000 (black)
            
            # Calculate opacity (0.2 to 0.8 for better visibility)
            opacity = 0.2 + (normalized_freq * 0.6)
            
            # Get key render parameters
            parms = get_render_params(key, key_sizes)
            
            # Add solid red overlay using the same shape as the keycap
            if parms.get("jShaped", False):
                # For J-shaped keys, create heatmap path matching the keycap shape
                path_data = [
                    f"M {parms['innercapx']},{parms['innercapy']}",
                    f"L {parms['innercapx']},{parms['innercapy']+parms['innercapheight']}",
                    f"L {parms['innercapx']+parms['innercapwidth']},{parms['innercapy']+parms['innercapheight']}",
                    f"L {parms['innercapx2']+parms['innercapwidth2']},{parms['innercapy2']+parms['innercapheight2']}",
                    f"L {parms['innercapx2']+parms['innercapwidth2']},{parms['innercapy2']}",
                    f"L {parms['innercapx2']},{parms['innercapy2']}",
                    f"L {parms['innercapx']},{parms['innercapy']}",
                    "Z"
                ]
                heatmap_path = dwg.path(
                    d=" ".join(path_data),
                    fill=red_color,
                    fill_opacity=opacity,
                    stroke="none"
                )
                dwg.add(heatmap_path)
            else:
                # Simple rectangle for regular keys (inner cap area)
                heatmap_rect = dwg.rect(
                    insert=(parms["innercapx"], parms["innercapy"]),
                    size=(parms["innercapwidth"], parms["innercapheight"]),
                    rx=key_sizes["roundInner"],
                    ry=key_sizes["roundInner"],
                    fill=red_color,
                    fill_opacity=opacity,
                    stroke="none"
                )
                dwg.add(heatmap_rect)
    
    # Return as IPython SVG for Jupyter display
    return SVG(dwg.tostring())