#!/usr/bin/env python3
"""
Evaluator Script
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

def main():
    """Main execution function for evaluator."""
    # Setup project path
    project_root = setup_project_path()
    print(f"Project root determined: {project_root}")
    
    # Change to project root directory to ensure relative paths work correctly
    original_cwd = os.getcwd()
    os.chdir(project_root)
    print(f"Changed working directory to: {os.getcwd()}")
    
    # Import the evaluator module
    try:
        from src.core.evaluator import Evaluator
    except ImportError as e:
        print(f"Error importing evaluator: {e}")
        print("Make sure you're running from the project root directory")
        os.chdir(original_cwd)  # Restore original directory
        sys.exit(1)
    
    # Define keyboard directory and output directory
    keyboards_dir = "src/data/keyboards"
    images_dir = "notebooks/output/evaluator_images"
    
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
            # Create evaluator instance and load keyboard
            ev = Evaluator(debug=True)
            ev.load_keyoard(keyboard_file=keyboard_path)
            ev.load_distance()
            ev.load_layout()
            
            # Generate SVG visualization using renderer
            from src.helpers.keyboards.renderer import render_keyboard
            svg_obj = render_keyboard(ev.keyboard)
            
            # Extract SVG data - try different methods to access the SVG content
            svg_content = None
            if hasattr(svg_obj, '_repr_svg_'):
                svg_content = svg_obj._repr_svg_()
            elif hasattr(svg_obj, 'data'):
                svg_content = svg_obj.data
            elif hasattr(svg_obj, '_data'):
                svg_content = svg_obj._data
            elif str(type(svg_obj)) == "<class 'IPython.core.display.SVG'>":
                # For IPython SVG objects, try to access the raw data
                svg_content = svg_obj._data if hasattr(svg_obj, '_data') else str(svg_obj)
            
            if svg_content is None:
                print(f"  Warning: Could not extract SVG data for {kb_file}, using string representation")
                svg_content = str(svg_obj)
            
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
    print("Evaluator completed successfully!")

if __name__ == "__main__":
    main()
