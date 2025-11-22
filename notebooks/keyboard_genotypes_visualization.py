#!/usr/bin/env python3
"""
Genotype Visualization Script
This script loads different keyboard layouts and applies various genotypes/layouts to generate SVG visualizations.
"""

import sys
import os
import json
from pathlib import Path

def setup_project_path():
    """Add the project root directory to Python path for imports."""
    # Get the project root (execution from project root level)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # If we're executing from notebooks directory, adjust accordingly
    if os.path.basename(os.path.dirname(__file__)) == 'notebooks':
        project_root = os.path.dirname(os.path.dirname(__file__))
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    return project_root

def extract_svg_content(svg_obj):
    """
    Extract SVG content from an IPython SVG object using multiple methods.
    """
    # Method 1: Try _repr_svg_ method (most common for IPython SVG objects)
    if hasattr(svg_obj, '_repr_svg_'):
        try:
            svg_content = svg_obj._repr_svg_()
            if svg_content and isinstance(svg_content, str) and svg_content.strip().startswith('<svg'):
                return svg_content
        except:
            pass
    
    # Method 2: Try data attribute
    if hasattr(svg_obj, 'data'):
        try:
            data_content = svg_obj.data
            if data_content and isinstance(data_content, str) and data_content.strip().startswith('<svg'):
                return data_content
        except:
            pass
    
    # Method 3: Try _data attribute
    if hasattr(svg_obj, '_data'):
        try:
            _data_content = svg_obj._data
            if _data_content and isinstance(_data_content, str) and _data_content.strip().startswith('<svg'):
                return _data_content
        except:
            pass
    
    # Method 4: Try string conversion
    try:
        str_content = str(svg_obj)
        if str_content and str_content.strip().startswith('<svg'):
            return str_content
    except:
        pass
    
    return None

def main():
    """Main execution function for genotype visualization."""
    # Setup project path
    project_root = setup_project_path()
    print(f"Project root determined: {project_root}")
    
    # Change to project root directory to ensure relative paths work correctly
    original_cwd = os.getcwd()
    os.chdir(project_root)
    print(f"Changed working directory to: {os.getcwd()}")
    
    # Import the evaluator and keyboard modules
    try:
        from src.core.evaluator import Evaluator
        from src.core.keyboard import Serial
        from src.data.layouts.keyboard_genotypes import LAYOUT_DATA
        from src.core.mapper import KeyType
    except ImportError as e:
        print(f"Error importing evaluator modules: {e}")
        print("Make sure you're running from the project root directory")
        os.chdir(original_cwd)  # Restore original directory
        sys.exit(1)
    
    # Define keyboard directory and output directory
    keyboards_dir = "src/data/keyboards"
    images_dir = "notebooks/output/genotype_visualizations"
    
    # Create output directory for images
    os.makedirs(images_dir, exist_ok=True)
    
    # Get all keyboard JSON files
    keyboard_files = [f for f in os.listdir(keyboards_dir) if f.endswith('.json')]
    
    print(f"Found {len(keyboard_files)} keyboard files to process:")
    for kb_file in keyboard_files:
        print(f"  - {kb_file}")
    
    # Process each keyboard file with different genotypes
    for kb_file in keyboard_files:
        if kb_file == "readme.md":  # Skip readme file
            continue
            
        keyboard_path = os.path.join(keyboards_dir, kb_file)
        print(f"\nProcessing keyboard: {kb_file}")
        
        try:
            # Create evaluator instance and load keyboard
            ev = Evaluator(debug=False)  # Set debug to False to reduce output
            ev.load_keyoard(keyboard_file=keyboard_path)
            ev.load_distance()
            ev.load_layout()
            
            # Get keyboard name without extension for file naming
            kb_name = Path(kb_file).stem
            
            # Apply different genotypes/layouts and save visualizations
            print(f"  Available genotypes: {list(LAYOUT_DATA.keys())}")
            
            for layout_name, layout_value in LAYOUT_DATA.items():
                try:
                    # Create a fresh evaluator instance for each layout
                    ev_layout = Evaluator(debug=False)
                    ev_layout.load_keyoard(keyboard_file=keyboard_path)
                    ev_layout.load_distance()
                    ev_layout.load_layout()
                    
                    # Apply the layout
                    ev_layout.layout.querty_based_remap(layout_value)
                    
                    # UPDATE KEYBOARD KEY LABELS - THIS IS THE FIX
                    layer_idx = 0  # Base layer
                    
                    # Clear all labels first
                    for key_obj in ev_layout.keyboard.keys:
                        key_obj.clear_labels()
                    
                    # Set labels based on the layout mapping
                    for key_obj in ev_layout.keyboard.keys:
                        key_id = key_obj.id
                        
                        if (key_id, layer_idx) in ev_layout.layout.mapper.data:
                            key_data = ev_layout.layout.mapper.data[(key_id, layer_idx)]
                            if key_data.key_type == KeyType.CHAR:
                                key_obj.set_labels(key_data.value)
                            elif key_data.key_type in [KeyType.SPECIAL_CHAR, KeyType.CONTROL, KeyType.LAYER]:
                                if isinstance(key_data.value, tuple):
                                    key_obj.set_labels((key_data.value[1],) if len(key_data.value) > 1 else (key_data.value[0],))
                                else:
                                    key_obj.set_labels((key_data.value,))
                    
                    # Generate SVG visualization using renderer
                    from src.helpers.keyboards.renderer import render_keyboard
                    svg_obj = render_keyboard(ev_layout.keyboard)
                    
                    # Extract SVG content from the IPython SVG object
                    svg_content = extract_svg_content(svg_obj)
                    
                    if svg_content is None:
                        print(f"    Warning: Could not extract SVG data for {layout_name}")
                        continue
                    
                    # Verify that the SVG content is valid
                    svg_content = svg_content.strip()
                    if not svg_content.startswith('<svg'):
                        print(f"    Warning: Invalid SVG content for {layout_name}")
                        continue
                    
                    # Save SVG to file with keyboard and layout names
                    output_file = os.path.join(images_dir, f"{kb_name}_{layout_name}.svg")
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(svg_content)
                    
                    print(f"    Saved visualization to: {output_file}")
                    
                except Exception as e:
                    print(f"    Error processing layout {layout_name}: {e}")
                    continue
            
        except Exception as e:
            print(f"  Error processing {kb_file}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Restore original working directory
    os.chdir(original_cwd)
    
    print(f"\nAll genotype visualizations saved to: {images_dir}")
    print("Genotype visualization completed successfully!")

if __name__ == "__main__":
    main()
