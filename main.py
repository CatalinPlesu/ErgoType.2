#!/usr/bin/env python3
"""
Main entry point for the Keyboard Layout Optimization project.
Uses simulation-based genetic algorithm with C# fitness calculation.
"""

import sys
from pathlib import Path
import os

# Add src to import path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ui.menu import Menu


def get_available_keyboards():
    """Get list of available physical keyboard layouts"""
    keyboards_dir = Path(__file__).parent / "src" / "data" / "keyboards"
    keyboard_files = []
    
    for file in keyboards_dir.glob("*.json"):
        if file.name != "readme.md":
            # Create a nice display name from filename
            name = file.stem.replace('_', ' ').title()
            keyboard_files.append((name, str(file.relative_to(Path(__file__).parent))))
    
    return keyboard_files


def get_available_text_files():
    """Get list of available text files for simulation"""
    text_dir = Path(__file__).parent / "src" / "data" / "text" / "raw"
    text_files = []
    
    for file in text_dir.glob("*.txt"):
        # Create a nice display name from filename
        name = file.stem.replace('_', ' ').title()
        size_mb = file.stat().st_size / (1024 * 1024)
        text_files.append((name, str(file.relative_to(Path(__file__).parent)), size_mb))
    
    return text_files


def print_header():
    print("\n" + "=" * 60)
    print("  KEYBOARD LAYOUT OPTIMIZATION SYSTEM")
    print("  (Simulation-Based with C# Fitness)")
    print("=" * 60)


# -----------------------------
#   MENU ITEM WRAPPERS
# -----------------------------

def item_run_genetic(show_title):
    if show_title:
        return "Run Genetic Algorithm (Optimize Keyboard Layout)"

    from core.run_ga import run_genetic_algorithm

    print("\n[Starting Genetic Algorithm...]")
    print("=" * 60)

    # Interactive keyboard selection
    print("\nAvailable Physical Keyboards:")
    keyboards = get_available_keyboards()
    if not keyboards:
        print("❌ No keyboard layouts found in src/data/keyboards/")
        print("Please ensure keyboard layout files are present.")
        return
    
    for i, (name, path) in enumerate(keyboards, 1):
        print(f"  {i}. {name}")
        print(f"     {path}")
    
    keyboard_file = None
    while keyboard_file is None:
        try:
            choice = input(f"\nSelect keyboard (1-{len(keyboards)}) or 'q' to quit: ")
            if choice.lower() == 'q':
                print("Cancelled.")
                return
            
            keyboard_choice = int(choice) - 1
            if keyboard_choice < 0 or keyboard_choice >= len(keyboards):
                print(f"Invalid selection. Please choose between 1 and {len(keyboards)}.")
            else:
                keyboard_file = keyboards[keyboard_choice][1]
                print(f"✅ Selected: {keyboards[keyboard_choice][0]}")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")

    # Interactive text file selection
    print("\nAvailable Text Files for Simulation:")
    text_files = get_available_text_files()
    if not text_files:
        print("❌ No text files found in src/data/text/raw/")
        print("Please ensure text files are present.")
        return
    
    for i, (name, path, size_mb) in enumerate(text_files, 1):
        print(f"  {i}. {name}")
        print(f"     {path} ({size_mb:.2f} MB)")
    
    text_file = None
    while text_file is None:
        try:
            choice = input(f"\nSelect text file (1-{len(text_files)}) or 'q' to quit: ")
            if choice.lower() == 'q':
                print("Cancelled.")
                return
            
            text_choice = int(choice) - 1
            if text_choice < 0 or text_choice >= len(text_files):
                print(f"Invalid selection. Please choose between 1 and {len(text_files)}.")
            else:
                text_file = text_files[text_choice][1]
                print(f"✅ Selected: {text_files[text_choice][0]} ({text_files[text_choice][2]:.2f} MB)")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")

    # Get user input for GA parameters with validation
    print("\nGenetic Algorithm Parameters:")
    
    def get_valid_int(prompt, default, min_val=1, max_val=1000):
        while True:
            try:
                value = input(f"{prompt} [{default}]: ") or str(default)
                num = int(value)
                if min_val <= num <= max_val:
                    return num
                else:
                    print(f"Please enter a value between {min_val} and {max_val}.")
            except ValueError:
                print("Please enter a valid number.")
    
    def get_valid_float(prompt, default, min_val=0.0, max_val=10.0):
        while True:
            try:
                value = input(f"{prompt} [{default}]: ") or str(default)
                num = float(value)
                if min_val <= num <= max_val:
                    return num
                else:
                    print(f"Please enter a value between {min_val} and {max_val}.")
            except ValueError:
                print("Please enter a valid number.")
    
    population_size = get_valid_int("Population size", 30, 1, 500)
    max_iterations = get_valid_int("Max iterations", 50, 1, 1000)
    stagnant_limit = get_valid_int("Stagnation limit", 10, 1, 100)
    max_processes = get_valid_int("Max parallel processes", 4, 1, 32)
    
    # Advanced parameters (optional)
    print("\nAdvanced Parameters (press Enter to use defaults):")
    fitts_a = get_valid_float("Fitts's Law constant 'a'", 0.5, 0.0, 5.0)
    fitts_b = get_valid_float("Fitts's Law constant 'b'", 0.3, 0.0, 5.0)

    CONFIG = {
        'keyboard_file': keyboard_file,
        'text_file': text_file,
        'population_size': population_size,
        'max_iterations': max_iterations,
        'stagnant_limit': stagnant_limit,
        'max_concurrent_processes': max_processes,
        'fitts_a': fitts_a,
        'fitts_b': fitts_b,
        'finger_coefficients': None  # Use defaults
    }

    print("\n" + "=" * 60)
    print("FINAL CONFIGURATION:")
    print("=" * 60)
    for k, v in CONFIG.items():
        if v is not None:
            print(f"  {k}: {v}")
    print("=" * 60)

    confirm = input("\nStart Genetic Algorithm? (y/N): ").lower().strip()
    if confirm not in ['y', 'yes']:
        print("Cancelled.")
        return

    try:
        print("\n🚀 Starting Genetic Algorithm...")
        best = run_genetic_algorithm(**CONFIG)
        print("\n" + "=" * 60)
        print("🎉 Genetic Algorithm Complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


def item_annotator(show_title):
    if show_title:
        return "Launch Keyboard Annotator GUI"

    print("\n[Launching Keyboard Annotator GUI...]")
    print("=" * 60)

    # Interactive keyboard selection
    print("\nAvailable Physical Keyboards:")
    keyboards = get_available_keyboards()
    if not keyboards:
        print("No keyboard layouts found!")
        return
    
    for i, (name, path) in enumerate(keyboards, 1):
        print(f"  {i}. {name}")
    
    try:
        keyboard_choice = int(input(f"\nSelect keyboard (1-{len(keyboards)}): ")) - 1
        if keyboard_choice < 0 or keyboard_choice >= len(keyboards):
            print("Invalid selection. Using default keyboard.")
            keyboard_file = 'src/data/keyboards/ansi_60_percent.json'
        else:
            keyboard_file = keyboards[keyboard_choice][1]
    except (ValueError, KeyboardInterrupt):
        print("Invalid input. Using default keyboard.")
        keyboard_file = 'src/data/keyboards/ansi_60_percent.json'

    print(f"\nLoading keyboard: {keyboard_file}")

    try:
        from helpers.keyboards.annotator_gui import KeyboardAnnotatorDPG
        app = KeyboardAnnotatorDPG()
        app.run()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


def item_text_analysis(show_title):
    if show_title:
        return "Analyze Text File"
    
    print("\n[Text File Analysis]")
    print("=" * 60)
    
    # Interactive text file selection
    print("\nAvailable Text Files:")
    text_files = get_available_text_files()
    if not text_files:
        print("❌ No text files found!")
        return
    
    for i, (name, path, size_mb) in enumerate(text_files, 1):
        print(f"  {i}. {name}")
        print(f"     {path} ({size_mb:.2f} MB)")
    
    text_file = None
    while text_file is None:
        try:
            choice = input(f"\nSelect text file (1-{len(text_files)}) or 'q' to quit: ")
            if choice.lower() == 'q':
                print("Cancelled.")
                return
            
            text_choice = int(choice) - 1
            if text_choice < 0 or text_choice >= len(text_files):
                print(f"Invalid selection. Please choose between 1 and {len(text_files)}.")
            else:
                text_file = text_files[text_choice][1]
                print(f"✅ Selected: {text_files[text_choice][0]}")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")
    
    print(f"\n📊 Analyzing text file: {text_files[text_choice][0]}")
    print(f"📁 File: {text_file}")
    print(f"💾 Size: {text_files[text_choice][2]:.2f} MB")
    print("\n📝 [Text Analysis - Coming soon!]")
    print("💡 This feature will provide detailed statistics about character frequencies,")
    print("   word distributions, bigrams, trigrams, and other text metrics.")


def item_keyboard_evaluator(show_title):
    if show_title:
        return "Evaluate Keyboard Layout"
    
    print("\n[Keyboard Layout Evaluator]")
    print("=" * 60)
    
    # Interactive keyboard selection
    print("\nAvailable Physical Keyboards:")
    keyboards = get_available_keyboards()
    if not keyboards:
        print("❌ No keyboard layouts found!")
        return
    
    for i, (name, path) in enumerate(keyboards, 1):
        print(f"  {i}. {name}")
        print(f"     {path}")
    
    keyboard_file = None
    keyboard_name = None
    while keyboard_file is None:
        try:
            choice = input(f"\nSelect keyboard (1-{len(keyboards)}) or 'q' to quit: ")
            if choice.lower() == 'q':
                print("Cancelled.")
                return
            
            keyboard_choice = int(choice) - 1
            if keyboard_choice < 0 or keyboard_choice >= len(keyboards):
                print(f"Invalid selection. Please choose between 1 and {len(keyboards)}.")
            else:
                keyboard_file = keyboards[keyboard_choice][1]
                keyboard_name = keyboards[keyboard_choice][0]
                print(f"✅ Selected: {keyboard_name}")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")
    
    # Interactive text file selection
    print("\nAvailable Text Files:")
    text_files = get_available_text_files()
    if not text_files:
        print("❌ No text files found!")
        return
    
    for i, (name, path, size_mb) in enumerate(text_files, 1):
        print(f"  {i}. {name}")
        print(f"     {path} ({size_mb:.2f} MB)")
    
    text_file = None
    while text_file is None:
        try:
            choice = input(f"\nSelect text file (1-{len(text_files)}) or 'q' to quit: ")
            if choice.lower() == 'q':
                print("Cancelled.")
                return
            
            text_choice = int(choice) - 1
            if text_choice < 0 or text_choice >= len(text_files):
                print(f"Invalid selection. Please choose between 1 and {len(text_files)}.")
            else:
                text_file = text_files[text_choice][1]
                print(f"✅ Selected: {text_files[text_choice][0]}")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")
    
    print(f"\n⌨️  Evaluating keyboard: {keyboard_name}")
    print(f"📊 Text file: {text_files[text_choice][0]}")
    print(f"📁 File: {text_file}")
    print("\n📝 [Keyboard Evaluator - Coming soon!]")
    print("💡 This feature will analyze keyboard layout efficiency using simulation,")
    print("   providing metrics like finger travel distance, typing time, and heatmaps.")


def item_layout_comparison(show_title):
    if show_title:
        return "Compare Standard Layouts"
    
    print("\n[Layout Comparison]")
    print("=" * 60)
    print("\n📝 [Layout Comparison - Coming soon!]")
    print("💡 This feature will compare standard layouts (QWERTY, Dvorak, Colemak, etc.)")
    print("   using simulation-based fitness calculation with detailed metrics and heatmaps.")


def item_visualize_layout(show_title):
    if show_title:
        return "Visualize Keyboard Layout"
    
    print("\n[Layout Visualization]")
    print("=" * 60)
    print("\n📝 [Layout Visualization - Coming soon!]")
    print("💡 This feature will generate SVG visualizations of keyboard layouts")
    print("   with optional heatmaps showing key usage patterns.")


# -----------------------------
#           MAIN
# -----------------------------

def main():
    print_header()

    menu = Menu("Main Menu")

    # Register all menu item functions
    menu.add_item(item_run_genetic)
    menu.add_item(item_keyboard_evaluator)
    menu.add_item(item_layout_comparison)
    menu.add_item(item_text_analysis)
    menu.add_item(item_visualize_layout)
    menu.add_item(item_annotator)

    # Interactive loop
    menu.run()

    print("\n[Exiting...]\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
