"""
Keyboard renderer with heatmap support for press and hover data.
Single clean interface for generating all visualizations.
"""

from src.core.keyboard import Keyboard
from typing import Dict, Optional, Tuple
from IPython.display import SVG
import svgwrite
from pathlib import Path
import json


def get_heatmap_color(normalized_freq: float, color_scheme: str = 'blue-red') -> str:
    """
    Get color based on normalized frequency (0-1).
    Gradient from white (0%) to full color (100%).
    
    Args:
        normalized_freq: Frequency value normalized to 0-1 range (0=min, 1=max)
        color_scheme: 'blue-red' (default), 'grey-green', or 'white-blue'
    
    Returns:
        Hex color string
    """
    freq = max(0.0, min(1.0, normalized_freq))
    
    if color_scheme == 'grey-green':
        # White (low) → green (high)
        red = int(255 - 55 * freq)    # 255 → 200
        green = 255                    # Always 255
        blue = int(255 - 55 * freq)    # 255 → 200
        return f"#{red:02x}{green:02x}{blue:02x}"
    elif color_scheme == 'white-blue':
        # White (low) → yellow (high) - for non-ASCII keys
        # Yellow has less intensity and doesn't interfere with blue/green
        red = 255                       # Always 255
        green = 255                     # Always 255
        blue = int(255 * (1 - freq))   # 255 → 0
        return f"#{red:02x}{green:02x}{blue:02x}"
    else:  # blue-red
        # White (low) → red (high)
        red = 255                      # Always 255
        green = int(255 * (1 - freq))  # 255 → 0
        blue = int(255 * (1 - freq))   # 255 → 0
        return f"#{red:02x}{green:02x}{blue:02x}"


def render_keyboard_heatmap(
    keyboard: Keyboard,
    key_frequencies: Dict[int, float],
    layer_idx: int = 0,
    layout=None,
    heatmap_type: str = "press",
    exclude_space: bool = True
) -> SVG:
    """
    Render keyboard with heatmap overlay using key_id mapping.
    
    Args:
        keyboard: Keyboard object with keys
        key_frequencies: Dict mapping key_id to frequency value
            Format: {key_id: float, ...}
        layer_idx: Layer index to render
        layout: Layout object (for getting key labels)
        heatmap_type: "press" (blue-red) or "hover" (grey-green)
        exclude_space: Whether to exclude spacebar from normalization
    
    Returns:
        IPython SVG display object
    """
    from src.helpers.keyboards.renderer import UNIT_SIZES, get_profile, get_render_params
    from src.core.mapper import KeyType
    
    # Get sizes for the unit system
    unit_config = UNIT_SIZES["px"]
    sizes_base = unit_config["profiles"]
    
    # Calculate overall bounding box
    bbox = {"x": float('inf'), "y": float('inf'), "x2": float('-inf'), "y2": float('-inf')}
    
    for key in keyboard.keys:
        profile = get_profile(key)
        key_sizes = sizes_base.get(profile, sizes_base[""])
        key_sizes["unit"] = unit_config["unit"]
        key_sizes["strokeWidth"] = unit_config["strokeWidth"]
        
        parms = get_render_params(key, key_sizes)
        bbox["x"] = min(bbox["x"], parms["bbox"]["x"])
        bbox["y"] = min(bbox["y"], parms["bbox"]["y"])
        bbox["x2"] = max(bbox["x2"], parms["bbox"]["x2"])
        bbox["y2"] = max(bbox["y2"], parms["bbox"]["y2"])
    
    # Add margins
    margin = 10
    legend_height = 60
    bbox["x"] -= margin
    bbox["y"] -= margin
    bbox["x2"] += margin
    bbox["y2"] += margin + legend_height
    width = bbox["x2"] - bbox["x"]
    height = bbox["y2"] - bbox["y"]
    
    # Create SVG drawing
    dwg = svgwrite.Drawing(
        size=(f"{width}px", f"{height}px"),
        viewBox=f"{bbox['x']} {bbox['y']} {width} {height}"
    )
    
    # Add background
    dwg.add(dwg.rect(
        insert=(bbox["x"], bbox["y"]),
        size=(width, height),
        fill='#f8f8f8',
        stroke='none'
    ))
    
    # Identify non-ASCII keys (control/modifier keys) vs alphanumeric keys
    # Non-ASCII keys: Space, Shift, Tab, Enter, Ctrl, Alt, Backspace, etc.
    # These will be scaled separately with blue color
    non_ascii_key_ids = set()
    ascii_key_ids = set()
    
    # Common non-ASCII key labels
    non_ascii_labels = {
        'shift', 'tab', 'enter', 'backspace', 'ctrl', 'alt', 'altgr',
        'caps lock', 'win', 'menu', 'esc', 'escape', 'delete', 'del',
        'home', 'end', 'page up', 'page down', 'insert', 'ins',
        'print screen', 'scroll lock', 'pause', 'break'
    }
    
    # Find spacebar (widest key) - also non-ASCII
    max_width = 0
    spacebar_key_id = None
    for key in keyboard.keys:
        if key.width > max_width:
            max_width = key.width
            spacebar_key_id = key.id
    if spacebar_key_id:
        non_ascii_key_ids.add(spacebar_key_id)
    
    # Categorize keys by label
    for key_obj in keyboard.keys:
        if hasattr(key_obj, 'labels') and key_obj.labels:
            label = str(key_obj.labels[0]).lower() if key_obj.labels else ''
            # Check if it's a non-ASCII key
            if label in non_ascii_labels or len(label) > 1:  # Multi-char labels are typically special keys
                non_ascii_key_ids.add(key_obj.id)
            else:
                ascii_key_ids.add(key_obj.id)
    
    # Calculate frequency ranges for each group
    # Alphanumeric keys (ASCII) - scale 0-90%
    ascii_freqs = [
        freq for key_id, freq in key_frequencies.items() 
        if freq > 0 and key_id in ascii_key_ids
    ]
    
    if ascii_freqs:
        ascii_min_freq = min(ascii_freqs)
        ascii_max_freq = max(ascii_freqs)
        ascii_freq_range = ascii_max_freq - ascii_min_freq if ascii_max_freq > ascii_min_freq else 1.0
    else:
        ascii_min_freq = 0.0
        ascii_freq_range = 1.0
    
    # Non-ASCII keys - scale 0-100%
    non_ascii_freqs = [
        freq for key_id, freq in key_frequencies.items() 
        if freq > 0 and key_id in non_ascii_key_ids
    ]
    
    if non_ascii_freqs:
        non_ascii_min_freq = min(non_ascii_freqs)
        non_ascii_max_freq = max(non_ascii_freqs)
        non_ascii_freq_range = non_ascii_max_freq - non_ascii_min_freq if non_ascii_max_freq > non_ascii_min_freq else 1.0
    else:
        non_ascii_min_freq = 0.0
        non_ascii_freq_range = 1.0
    
    # Choose color scheme based on heatmap type
    color_scheme = 'grey-green' if heatmap_type == 'hover' else 'blue-red'
    
    # Draw keys with heatmap overlay
    for i, key in enumerate(keyboard.keys):
        profile = get_profile(key)
        key_sizes = sizes_base.get(profile, sizes_base[""])
        key_sizes["unit"] = unit_config["unit"]
        key_sizes["strokeWidth"] = unit_config["strokeWidth"]
        
        parms = get_render_params(key, key_sizes)
        
        # Get frequency for this key directly using key_id
        key_freq = key_frequencies.get(key.id, 0.0)
        
        # Normalize frequency and choose color scheme
        normalized_freq = 0.0
        key_color_scheme = color_scheme
        
        if key.id in non_ascii_key_ids:
            # Non-ASCII keys (Space, Shift, Tab, Enter, etc.) - separate scale with blue color
            if non_ascii_freq_range > 0 and key_freq > 0:
                normalized_freq = (key_freq - non_ascii_min_freq) / non_ascii_freq_range
            # Use blue color scheme for non-ASCII keys
            key_color_scheme = 'white-blue'
        elif key.id in ascii_key_ids:
            # ASCII keys (alphanumeric, symbols) - scale to 0-90%
            if ascii_freq_range > 0 and key_freq > 0:
                normalized_freq = ((key_freq - ascii_min_freq) / ascii_freq_range) * 0.9
            # Use red/green color scheme for ASCII keys
            key_color_scheme = color_scheme
        
        # Get color based on frequency and scheme
        fill_color = get_heatmap_color(normalized_freq, key_color_scheme) if normalized_freq > 0 else '#e0e0e0'
        
        # Create key group
        key_group = dwg.g(id=f"key-{i}")
        
        # Apply rotation if needed
        if key.rotation_angle != 0:
            transform = f"rotate({key.rotation_angle}, {parms['origin_x']}, {parms['origin_y']})"
            key_group.attribs['transform'] = transform
        
        # Draw outer cap (border)
        outer_rect = dwg.rect(
            insert=(parms["outercapx"], parms["outercapy"]),
            size=(parms["outercapwidth"], parms["outercapheight"]),
            rx=key_sizes["roundOuter"],
            ry=key_sizes["roundOuter"],
            fill='#c0c0c0',
            stroke='#333333',
            stroke_width=key_sizes["strokeWidth"]
        )
        key_group.add(outer_rect)
        
        # Draw inner cap with heatmap color
        inner_rect = dwg.rect(
            insert=(parms["innercapx"], parms["innercapy"]),
            size=(parms["innercapwidth"], parms["innercapheight"]),
            rx=key_sizes["roundInner"],
            ry=key_sizes["roundInner"],
            fill=fill_color,
            stroke='#333333',
            stroke_width=key_sizes["strokeWidth"] * 0.5
        )
        key_group.add(inner_rect)
        
        # Draw key labels (only first label to avoid overlap)
        if hasattr(key, 'labels') and key.labels:
            # Only show the first label (lowercase letter) to avoid overlap
            label = key.labels[0] if key.labels else None
            if label:
                text_x = parms["textcapx"] + parms["textcapwidth"] / 2
                text_y = parms["textcapy"] + parms["textcapheight"] / 2
                
                # Always use black text for better visibility on heatmap
                text_color = '#000000'
                
                key_group.add(dwg.text(
                    str(label),
                    insert=(text_x, text_y),
                    text_anchor='middle',
                    dominant_baseline='middle',
                    font_size='12px',
                    font_family='monospace',
                    fill=text_color,
                    font_weight='bold'
                ))
        
        dwg.add(key_group)
    
    # Add gradient legend with key labels
    legend_x = bbox["x"] + margin
    legend_y = bbox["y2"] - legend_height + 10
    legend_width = width - 2 * margin
    legend_bar_height = 15
    
    # Create gradient definition
    gradient = dwg.defs.add(dwg.linearGradient(id='heatmap_gradient'))
    for i in range(21):
        freq = i / 20.0
        color = get_heatmap_color(freq, color_scheme)
        gradient.add_stop_color(offset=f'{i*5}%', color=color)
    
    # Draw legend bar
    dwg.add(dwg.rect(
        insert=(legend_x, legend_y),
        size=(legend_width, legend_bar_height),
        fill='url(#heatmap_gradient)',
        stroke='#333333',
        stroke_width=1
    ))
    
    # Add legend labels
    heatmap_label = "Key Press Frequency" if heatmap_type == "press" else "Key Hover Frequency"
    
    dwg.add(dwg.text(
        heatmap_label,
        insert=(legend_x + legend_width / 2, legend_y - 5),
        text_anchor='middle',
        font_size='14px',
        font_family='sans-serif',
        font_weight='bold',
        fill='#333333'
    ))
    
    dwg.add(dwg.text(
        'Low',
        insert=(legend_x, legend_y + legend_bar_height + 12),
        text_anchor='start',
        font_size='11px',
        font_family='sans-serif',
        fill='#666666'
    ))
    
    dwg.add(dwg.text(
        'High',
        insert=(legend_x + legend_width, legend_y + legend_bar_height + 12),
        text_anchor='end',
        font_size='11px',
        font_family='sans-serif',
        fill='#666666'
    ))
    
    # Convert to SVG string
    svg_string = dwg.tostring()
    return SVG(data=svg_string)


def generate_all_visualizations(
    stats_json: str,
    keyboard: Keyboard,
    layout,
    layout_name: str,
    layer_idx: int = 0,
    save_dir: Optional[Path] = None
) -> Tuple[SVG, SVG, SVG]:
    """
    Generate all visualizations (layout, press heatmap, hover heatmap) from C# stats.
    
    Args:
        stats_json: JSON string from C# ComputeStats()
        keyboard: Keyboard object
        layout: Layout object
        layout_name: Name for output files
        layer_idx: Layer index to render
        save_dir: Optional directory to save SVG files to
    
    Returns:
        Tuple of (layout_svg, press_svg, hover_svg)
    """
    from src.helpers.keyboards.renderer import render_keyboard
    from src.core.mapper import KeyType
    
    # Parse stats
    stats = json.loads(stats_json)
    char_mappings = stats.get('char_mappings', {})
    total_presses = stats.get('total_presses', 0)
    total_chars = stats.get('total_chars_processed', total_presses)
    
    # Build key_id-based frequency dicts
    press_key_frequencies = {}  # key_id -> frequency
    hover_key_frequencies = {}  # key_id -> frequency
    
    for char, char_data in char_mappings.items():
        press_count = char_data.get('press_count', 0)
        hover_count = char_data.get('hover_count', 0)
        key_presses = char_data.get('key_presses', [])
        
        # For each key press in the sequence, accumulate frequencies by key_id
        for key_press in key_presses:
            key_id = key_press.get('key_id')
            if key_id is not None:
                # Accumulate press frequency
                if press_count > 0:
                    relative_press = press_count / total_presses if total_presses > 0 else 0
                    press_key_frequencies[key_id] = press_key_frequencies.get(key_id, 0.0) + relative_press
                
                # Accumulate hover frequency
                if hover_count > 0:
                    total_hover_samples = total_chars
                    relative_hover = hover_count / total_hover_samples if total_hover_samples > 0 else 0
                    hover_key_frequencies[key_id] = hover_key_frequencies.get(key_id, 0.0) + relative_hover
    
    # Update keyboard labels for this layer
    for key_obj in keyboard.keys:
        key_obj.clear_labels()
    
    for key_obj in keyboard.keys:
        key_id = key_obj.id
        if (key_id, layer_idx) in layout.mapper.data:
            key_data = layout.mapper.data[(key_id, layer_idx)]
            if key_data.key_type == KeyType.CHAR:
                key_obj.set_labels(key_data.value)
            elif key_data.key_type in [KeyType.SPECIAL_CHAR, KeyType.CONTROL, KeyType.LAYER]:
                if isinstance(key_data.value, tuple):
                    key_obj.set_labels((key_data.value[1],) if len(key_data.value) > 1 else (key_data.value[0],))
                else:
                    key_obj.set_labels((key_data.value,))
    
    # Generate plain layout view
    layout_svg = render_keyboard(keyboard)
    
    # Generate press heatmap (blue-red)
    press_svg = render_keyboard_heatmap(
        keyboard=keyboard,
        key_frequencies=press_key_frequencies,
        layer_idx=layer_idx,
        layout=layout,
        heatmap_type="press",
        exclude_space=True
    )
    
    # Generate hover heatmap (grey-green)
    hover_svg = render_keyboard_heatmap(
        keyboard=keyboard,
        key_frequencies=hover_key_frequencies,
        layer_idx=layer_idx,
        layout=layout,
        heatmap_type="hover",
        exclude_space=True
    )
    
    # Save to files if directory provided
    if save_dir:
        save_dir = Path(save_dir)
        
        # Create subdirectories
        (save_dir / "layouts").mkdir(exist_ok=True)
        (save_dir / "heatmaps_press").mkdir(exist_ok=True)
        (save_dir / "heatmaps_hover").mkdir(exist_ok=True)
        
        # Extract SVG content and save
        for svg_obj, subdir, name_suffix in [
            (layout_svg, "layouts", ""),
            (press_svg, "heatmaps_press", ""),
            (hover_svg, "heatmaps_hover", "")
        ]:
            if hasattr(svg_obj, 'data'):
                svg_content = svg_obj.data
            elif hasattr(svg_obj, '_repr_svg_'):
                svg_content = svg_obj._repr_svg_()
            else:
                svg_content = str(svg_obj)
            
            file_path = save_dir / subdir / f"{layout_name}_layer_{layer_idx}.svg"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
    
    return layout_svg, press_svg, hover_svg


# Usage example
if __name__ == "__main__":
    print("Keyboard Visualization Module")
    print("=" * 60)
    print("\nMain function: generate_all_visualizations()")
    print("  - Creates layout view (colored by finger)")
    print("  - Creates press heatmap (blue→red)")
    print("  - Creates hover heatmap (grey→green)")
    print("  - Optionally saves to organized folders")
    print("\nUsage:")
    print("  layout, press, hover = generate_all_visualizations(")
    print("      stats_json, keyboard, layout, 'layout_name',")
    print("      layer_idx=0, save_dir='output/run_001')")
