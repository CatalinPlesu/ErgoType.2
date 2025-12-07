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
    
    Args:
        normalized_freq: Frequency value normalized to 0-1 range (0=min, 1=max)
        color_scheme: 'blue-red' (default) or 'grey-green'
    
    Returns:
        Hex color string
    """
    freq = max(0.0, min(1.0, normalized_freq))
    
    if color_scheme == 'grey-green':
        # Subtle grey (low) → green (high) with better visibility
        base = 220
        red = int(base * (1 - 0.3 * freq))
        green = int(200 + 55 * freq)  # 200 → 255
        blue = int(base * (1 - 0.3 * freq))
        return f"#{red:02x}{green:02x}{blue:02x}"
    else:  # blue-red
        # Subtle blue (low) → red (high) with better visibility
        base = 220
        red = int(200 + 55 * freq)  # 200 → 255
        blue = int(200 * (1 - freq))  # 200 → 0
        green = int(180 * (1 - freq))  # 180 → 0
        return f"#{red:02x}{green:02x}{blue:02x}"


def render_keyboard_heatmap(
    keyboard: Keyboard,
    char_frequencies: Dict,
    layer_idx: int = 0,
    layout=None,
    heatmap_type: str = "press",
    exclude_space: bool = True
) -> SVG:
    """
    Render keyboard with heatmap overlay.
    
    Args:
        keyboard: Keyboard object with keys
        char_frequencies: Dict mapping characters to frequency data
            Format: {char: {'count': int, 'relative': float}, ...}
        layer_idx: Layer index to render
        layout: Layout object (for getting key characters)
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
    
    # Calculate frequency range (optionally excluding space)
    if exclude_space:
        non_space_freqs = [
            data.get('relative', 0) 
            for char, data in char_frequencies.items() 
            if isinstance(data, dict) and char != ' '
        ]
        if non_space_freqs:
            min_freq = min(non_space_freqs)
            max_freq = max(non_space_freqs)
            freq_range = max_freq - min_freq if max_freq > min_freq else 1.0
        else:
            min_freq = 0.0
            freq_range = 1.0
    else:
        all_freqs = [data.get('relative', 0) for data in char_frequencies.values() if isinstance(data, dict)]
        min_freq = min(all_freqs) if all_freqs else 0.0
        max_freq = max(all_freqs) if all_freqs else 1.0
        freq_range = max_freq - min_freq if max_freq > min_freq else 1.0
    
    # Choose color scheme based on heatmap type
    color_scheme = 'grey-green' if heatmap_type == 'hover' else 'blue-red'
    
    # Draw keys with heatmap overlay
    for i, key in enumerate(keyboard.keys):
        profile = get_profile(key)
        key_sizes = sizes_base.get(profile, sizes_base[""])
        key_sizes["unit"] = unit_config["unit"]
        key_sizes["strokeWidth"] = unit_config["strokeWidth"]
        
        parms = get_render_params(key, key_sizes)
        
        # Get key character(s) for this layer
        key_chars = []
        if layout and hasattr(layout, 'mapper'):
            if (key.id, layer_idx) in layout.mapper.data:
                key_data = layout.mapper.data[(key.id, layer_idx)]
                if key_data.key_type == KeyType.CHAR:
                    if isinstance(key_data.value, tuple):
                        key_chars = [key_data.value[0]]  # Unshifted char
                    else:
                        key_chars = [key_data.value]
        
        # Calculate frequency for this key
        max_char_freq = 0.0
        is_spacebar = False
        for char in key_chars:
            if char == ' ':
                is_spacebar = True
            if char in char_frequencies:
                freq_data = char_frequencies[char]
                relative_freq = freq_data.get('relative', 0.0) if isinstance(freq_data, dict) else freq_data
                if relative_freq > max_char_freq:
                    max_char_freq = relative_freq
        
        # Skip spacebar if exclude_space is True
        if exclude_space and is_spacebar:
            max_char_freq = 0.0
        
        # Normalize frequency
        normalized_freq = 0.0
        if freq_range > 0 and max_char_freq > 0:
            normalized_freq = (max_char_freq - min_freq) / freq_range
        
        # Get color based on frequency
        fill_color = get_heatmap_color(normalized_freq, color_scheme) if normalized_freq > 0 else '#e0e0e0'
        
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
        
        # Draw key labels
        if hasattr(key, 'labels') and key.labels:
            for label in key.labels:
                if label:
                    text_x = parms["textcapx"] + parms["textcapwidth"] / 2
                    text_y = parms["textcapy"] + parms["textcapheight"] / 2
                    
                    # Choose text color based on background brightness
                    text_color = '#ffffff' if normalized_freq > 0.5 else '#000000'
                    
                    dwg.add(dwg.text(
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
    
    # Build frequency dicts
    press_frequencies = {}
    hover_frequencies = {}
    
    for char, char_data in char_mappings.items():
        press_count = char_data.get('press_count', 0)
        hover_count = char_data.get('hover_count', 0)
        
        if press_count > 0:
            press_frequencies[char] = {
                'count': press_count,
                'relative': press_count / total_presses if total_presses > 0 else 0
            }
        
        if hover_count > 0:
            total_hover_samples = total_chars  # Each char = 1 hover sample
            hover_frequencies[char] = {
                'count': hover_count,
                'relative': hover_count / total_hover_samples if total_hover_samples > 0 else 0
            }
    
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
        char_frequencies=press_frequencies,
        layer_idx=layer_idx,
        layout=layout,
        heatmap_type="press",
        exclude_space=True
    )
    
    # Generate hover heatmap (grey-green)
    hover_svg = render_keyboard_heatmap(
        keyboard=keyboard,
        char_frequencies=hover_frequencies,
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
