#!/usr/bin/env python3
"""
Keyboard Visualization Script
This script loads different keyboard layouts and generates SVG visualizations for each.
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
    """Main execution function for keyboard visualization."""
    # Setup project path
    project_root = setup_project_path()
    print(f"Project root determined: {project_root}")
    
    # Change to project root directory to ensure relative paths work correctly
    original_cwd = os.getcwd()
    os.chdir(project_root)
    print(f"Changed working directory to: {os.getcwd()}")
    
    # Import the keyboard modules
    try:
        from src.core.keyboard import Key, Keyboard, KeyboardMetadata, Serial
        from src.helpers.keyboards.renderer import show_keyboard, render_keyboard
    except ImportError as e:
        print(f"Error importing keyboard modules: {e}")
        print("Make sure you're running from the project root directory")
        os.chdir(original_cwd)  # Restore original directory
        sys.exit(1)
    
    # Define keyboard directory and output directory
    keyboards_dir = "src/data/keyboards"
    images_dir = "notebooks/output/keyboard_visualizations"
    
    # Create output directory for images
    os.makedirs(images_dir, exist_ok=True)
    
    # Get all keyboard JSON files
    keyboard_files = [f for f in os.listdir(keyboards_dir) if f.endswith('.json')]
    
    print(f"Found {len(keyboard_files)} keyboard files to process:")
    for kb_file in keyboard_files:
        print(f"  - {kb_file}")
    
    # Process each keyboard file
    for kb_file in keyboard_files:
        if kb_file == "readme.md":  # Skip readme file
            continue
            
        keyboard_path = os.path.join(keyboards_dir, kb_file)
        print(f"\nProcessing keyboard: {kb_file}")
        
        try:
            # Load the keyboard from JSON file
            with open(keyboard_path, 'r', encoding='utf-8') as f:
                keyboard_data = f.read()
            
            keyboard = Serial.parse(keyboard_data)
            
            # Generate SVG visualization using render_keyboard function instead of show_keyboard
            svg_obj = render_keyboard(keyboard)
            
            # Extract SVG content from the IPython SVG object
            svg_content = extract_svg_content(svg_obj)
            
            if svg_content is None:
                print(f"  Warning: Could not extract SVG data for {kb_file}")
                continue
            
            # Verify that the SVG content is valid
            svg_content = svg_content.strip()
            if not svg_content.startswith('<svg'):
                print(f"  Warning: Invalid SVG content for {kb_file}")
                continue
            
            # Save SVG to file
            kb_name = Path(kb_file).stem  # Remove .json extension
            output_file = os.path.join(images_dir, f"{kb_name}.svg")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            print(f"  Saved visualization to: {output_file}")
            
        except Exception as e:
            print(f"  Error processing {kb_file}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Restore original working directory
    os.chdir(original_cwd)
    
    print(f"\nAll keyboard visualizations saved to: {images_dir}")
    print("Keyboard visualization completed successfully!")

if __name__ == "__main__":
    main()
