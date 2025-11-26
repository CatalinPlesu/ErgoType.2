#!/usr/bin/env python3
"""
Main entry point for the Keyboard Layout Optimization project.
Now uses the simplified Menu class (src/ui/menu.py).
"""

import sys
from pathlib import Path
import os

# Add src to import path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ui.menu import Menu   # <-- your new simplified menu


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


def get_available_datasets():
    """Get list of available datasets"""
    datasets_dir = Path(__file__).parent / "src" / "data" / "text" / "processed"
    dataset_files = []
    
    # Check the main pickle file which contains multiple datasets
    main_pickle = datasets_dir / "frequency_analysis.pkl"
    if main_pickle.exists():
        # Load the pickle to see what datasets it contains
        import pickle
        try:
            with open(main_pickle, 'rb') as f:
                data = pickle.load(f)
            
            dataset_names = {
                'simple_wikipedia': 'Simple Wikipedia',
                'gutenberg': 'Project Gutenberg',
                'cartigratis': 'CartiGratuit',
                'the_algorithms_code': 'The Algorithms Code',
                'newsgroup': '20 Newsgroups'
            }
            
            for key in data.keys():
                if key in dataset_names:
                    name = dataset_names[key]
                    # Use the main pickle file but indicate which dataset within it
                    path = f"src/data/text/processed/frequency_analysis.pkl:{key}"
                    dataset_files.append((name, path))
        except Exception as e:
            print(f"Warning: Could not read main dataset file: {e}")
    
    # Also check for individual JSON files
    individual_datasets = {
        'simple_wikipedia_analysis': 'Simple Wikipedia (Individual)',
        'gutenberg_analysis': 'Project Gutenberg (Individual)',
        'cartigratis_analysis': 'CartiGratuit (Individual)',
        'newsgroup_analysis': '20 Newsgroups (Individual)',
        'the_algorithms_code_analysis': 'The Algorithms Code (Individual)',
        'frequency_analysis': 'Frequency Analysis (Combined)'
    }
    
    for file in datasets_dir.glob("*_analysis.json"):
        stem = file.stem
        if stem in individual_datasets:
            name = individual_datasets[stem]
            path = str(file.relative_to(Path(__file__).parent))
            # Only add if not already in the list (pickle takes precedence)
            existing_names = [item[0] for item in dataset_files]
            if not any(name.replace(' (Individual)', '') in existing for existing in existing_names):
                dataset_files.append((name, path))
    
    # Sort by name for consistent ordering
    return sorted(dataset_files)


def interactive_menu_select(options, title):
    """Display an interactive menu for selecting from options"""
    if not options:
        return None
    
    menu = Menu(title)
    
    def create_item_func(option_name, option_value):
        def item_func(show_title):
            if show_title:
                return option_name
            return option_value
        return item_func
    
    # Add all options to menu
    for name, value in options:
        menu.add_item(create_item_func(name, value))
    
    # Run menu and return selected value
    print(f"\nPlease select {title.lower()}:")
    menu.run()
    return None  # User cancelled


def print_header():
    print("\n" + "=" * 60)
    print("  KEYBOARD LAYOUT OPTIMIZATION SYSTEM")
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

    # Interactive dataset selection
    print("\nAvailable Datasets:")
    datasets = get_available_datasets()
    if not datasets:
        print("❌ No datasets found in src/data/text/processed/")
        print("Please ensure dataset files are present.")
        return
    
    for i, (name, path) in enumerate(datasets, 1):
        print(f"  {i}. {name}")
        print(f"     {path}")
    
    dataset_file = None
    dataset_name = None
    while dataset_file is None:
        try:
            choice = input(f"\nSelect dataset (1-{len(datasets)}) or 'q' to quit: ")
            if choice.lower() == 'q':
                print("Cancelled.")
                return
            
            dataset_choice = int(choice) - 1
            if dataset_choice < 0 or dataset_choice >= len(datasets):
                print(f"Invalid selection. Please choose between 1 and {len(datasets)}.")
            else:
                full_path = datasets[dataset_choice][1]
                dataset_name = datasets[dataset_choice][0].lower().replace(' ', '_').replace('(individual)', '').strip()
                
                # Handle the case where dataset is in main pickle file
                if ':' in full_path:
                    parts = full_path.split(':')
                    dataset_file = parts[0]
                    inner_dataset = parts[1]
                    print(f"✅ Selected: {datasets[dataset_choice][0]} (from {inner_dataset})")
                    # Set the inner dataset name for the GA
                    dataset_name = inner_dataset
                else:
                    dataset_file = full_path
                    print(f"✅ Selected: {datasets[dataset_choice][0]}")
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
    
    population_size = get_valid_int("Population size", 30, 1, 500)
    max_iterations = get_valid_int("Max iterations", 50, 1, 1000)
    stagnant_limit = get_valid_int("Stagnation limit", 10, 1, 100)

    CONFIG = {
        'keyboard_file': keyboard_file,
        'dataset_file': dataset_file,
        'dataset_name': dataset_name,
        'population_size': population_size,
        'max_iterations': max_iterations,
        'stagnant_limit': stagnant_limit
    }

    print("\n" + "=" * 60)
    print("FINAL CONFIGURATION:")
    print("=" * 60)
    for k, v in CONFIG.items():
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
            keyboard_file = 'src/data/keyboards/dactyl_manuform_6x6_4.json'
        else:
            keyboard_file = keyboards[keyboard_choice][1]
    except (ValueError, KeyboardInterrupt):
        print("Invalid input. Using default keyboard.")
        keyboard_file = 'src/data/keyboards/dactyl_manuform_6x6_4.json'

    print(f"\nLoading keyboard: {keyboard_file}")

    try:
        from helpers.keyboards.annotator_gui import KeyboardAnnotatorDPG
        app = KeyboardAnnotatorDPG()
        # Pass the selected keyboard file to the annotator if it supports it
        # For now, we'll just launch it and let the user load the file manually
        app.run()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


def item_dataset_analysis(show_title):
    if show_title:
        return "Run Dataset Analysis"
    
    print("\n[Dataset Analysis]")
    print("=" * 60)
    
    # Interactive dataset selection
    print("\nAvailable Datasets:")
    datasets = get_available_datasets()
    if not datasets:
        print("❌ No datasets found!")
        return
    
    for i, (name, path) in enumerate(datasets, 1):
        print(f"  {i}. {name}")
        print(f"     {path}")
    
    dataset_file = None
    dataset_name = None
    while dataset_file is None:
        try:
            choice = input(f"\nSelect dataset (1-{len(datasets)}) or 'q' to quit: ")
            if choice.lower() == 'q':
                print("Cancelled.")
                return
            
            dataset_choice = int(choice) - 1
            if dataset_choice < 0 or dataset_choice >= len(datasets):
                print(f"Invalid selection. Please choose between 1 and {len(datasets)}.")
            else:
                full_path = datasets[dataset_choice][1]
                dataset_name = datasets[dataset_choice][0].lower().replace(' ', '_').replace('(individual)', '').strip()
                
                # Handle the case where dataset is in main pickle file
                if ':' in full_path:
                    parts = full_path.split(':')
                    dataset_file = parts[0]
                    inner_dataset = parts[1]
                    print(f"✅ Selected: {datasets[dataset_choice][0]} (from {inner_dataset})")
                    dataset_name = inner_dataset
                else:
                    dataset_file = full_path
                    print(f"✅ Selected: {datasets[dataset_choice][0]}")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")
    
    print(f"\n📊 Analyzing dataset: {datasets[dataset_choice][0]}")
    print(f"📁 File: {dataset_file}")
    print(f"🏷️  Dataset name: {dataset_name}")
    print("\n📝 [Dataset Analysis - Coming soon!]")
    print("💡 This feature will provide detailed statistics about character frequencies,")
    print("   word distributions, and other text analysis metrics.")


def item_keyboard_evaluator(show_title):
    if show_title:
        return "Run Keyboard Evaluator"
    
    print("\n[Keyboard Evaluator]")
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
    
    # Interactive dataset selection
    print("\nAvailable Datasets:")
    datasets = get_available_datasets()
    if not datasets:
        print("❌ No datasets found!")
        return
    
    for i, (name, path) in enumerate(datasets, 1):
        print(f"  {i}. {name}")
        print(f"     {path}")
    
    dataset_file = None
    dataset_name = None
    while dataset_file is None:
        try:
            choice = input(f"\nSelect dataset (1-{len(datasets)}) or 'q' to quit: ")
            if choice.lower() == 'q':
                print("Cancelled.")
                return
            
            dataset_choice = int(choice) - 1
            if dataset_choice < 0 or dataset_choice >= len(datasets):
                print(f"Invalid selection. Please choose between 1 and {len(datasets)}.")
            else:
                full_path = datasets[dataset_choice][1]
                dataset_name = datasets[dataset_choice][0].lower().replace(' ', '_').replace('(individual)', '').strip()
                
                # Handle the case where dataset is in main pickle file
                if ':' in full_path:
                    parts = full_path.split(':')
                    dataset_file = parts[0]
                    inner_dataset = parts[1]
                    print(f"✅ Selected: {datasets[dataset_choice][0]} (from {inner_dataset})")
                    dataset_name = inner_dataset
                else:
                    dataset_file = full_path
                    print(f"✅ Selected: {datasets[dataset_choice][0]}")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")
    
    print(f"\n⌨️  Evaluating keyboard: {keyboard_name}")
    print(f"📊 Dataset: {datasets[dataset_choice][0]}")
    print(f"📁 File: {dataset_file}")
    print(f"🏷️  Dataset name: {dataset_name}")
    print("\n📝 [Keyboard Evaluator - Coming soon!]")
    print("💡 This feature will analyze keyboard layout efficiency using the selected dataset,")
    print("   providing metrics like finger travel distance, hand alternation, and more.")


def item_genotype_visualization(show_title):
    if show_title:
        return "Run Keyboard Genotypes Visualization"
    print("\n[Keyboard Genotypes Visualization - Not implemented yet]")


def item_physical_inspection(show_title):
    if show_title:
        return "Run Physical Keyboard Inspection"
    print("\n[Physical Keyboard Inspection - Not implemented yet]")


def item_run_all(show_title):
    if show_title:
        return "Run All Analysis Options"
    print("\n[Running All Analysis Options - Not implemented yet]")


# -----------------------------
#           MAIN
# -----------------------------

def main():
    print_header()

    menu = Menu("Main Menu")

    # Register all menu item functions
    menu.add_item(item_run_genetic)
    menu.add_item(item_annotator)
    menu.add_item(item_dataset_analysis)
    menu.add_item(item_keyboard_evaluator)
    menu.add_item(item_genotype_visualization)
    menu.add_item(item_physical_inspection)
    menu.add_item(item_run_all)

    # Interactive loop
    menu.run()

    print("\n[Exiting...]\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
