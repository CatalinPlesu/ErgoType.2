# keyboard_renderer.py
"""
Keyboard renderer module for displaying keyboard layouts in Jupyter notebooks.
"""

import math
import svgwrite
from typing import List, Dict, Any
from IPython.display import SVG, display

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
    
    # Dimensions of the top of the cap
    parms["innercapwidth"] = parms["outercapwidth"] - sizes["bevelMargin"] * 2
    parms["innercapheight"] = parms["outercapheight"] - sizes["bevelMargin"] * 2 - (sizes["bevelOffsetBottom"] - sizes["bevelOffsetTop"])
    parms["innercapx"] = parms["outercapx"] + sizes["bevelMargin"]
    parms["innercapy"] = parms["outercapy"] + sizes["bevelMargin"] - sizes["bevelOffsetTop"]
    
    if parms["jShaped"]:
        parms["innercapwidth2"] = parms["outercapwidth2"] - sizes["bevelMargin"] * 2
        parms["innercapheight2"] = parms["outercapheight2"] - sizes["bevelMargin"] * 2
        parms["innercapx2"] = parms["outercapx2"] + sizes["bevelMargin"]
        parms["innercapy2"] = parms["outercapy2"] + sizes["bevelMargin"] - sizes["bevelOffsetTop"]
    
    # Dimensions of the text part of the cap
    parms["textcapwidth"] = parms["innercapwidth"] - sizes["padding"] * 2
    parms["textcapheight"] = parms["innercapheight"] - sizes["padding"] * 2
    parms["textcapx"] = parms["innercapx"] + sizes["padding"]
    parms["textcapy"] = parms["innercapy"] + sizes["padding"]
    
    # Colors
    parms["darkColor"] = key.color
    parms["lightColor"] = lighten_color(key.color, 1.2)
    
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
    
    # Draw outer cap (bottom part)
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
    
    # Draw inner cap (top part)
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