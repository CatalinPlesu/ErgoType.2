#!/usr/bin/env python3
"""
Main entry point for the Keyboard Layout Optimization project.
Now uses the simplified Menu class (src/ui/menu.py).
"""

from run_simplified_ga import  run_simplified_ga
import sys
from pathlib import Path

# Add src to import path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ui.menu import Menu   # <-- your new simplified menu


def print_header():
    print("\n" + "=" * 60)
    print("  KEYBOARD LAYOUT OPTIMIZATION SYSTEM")
    print("=" * 60)


# -----------------------------
#   MENU ITEM WRAPPERS
# -----------------------------
run_simplified_ga

def item_run_simplified_genetic(show_title):
    if show_title:
        return "Run Genetic Algorithm (Simplified)"
    run_simplified_ga()

def item_run_frequency_based_ga(show_title):
    if show_title:
        return "Run GA - Frequency Based"
    
    print("\n" + "=" * 60)
    print("FREQUENCY-BASED GENETIC ALGORITHM")
    print("=" * 60)
    print("Using pre-processed frequency analysis data for fitness calculation.")
    print("Fast evaluation with statistical text analysis.")
    print()
    
    from core.run_ga import run_genetic_algorithm
    
    print("[Starting Frequency-Based Genetic Algorithm...]")
    print("=" * 60)
    
    CONFIG = {
        'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
        'dataset_file': 'src/data/text/processed/frequency_analysis.pkl',
        'dataset_name': 'simple_wikipedia',
        'population_size': 25,
        'max_iterations': 15,
        'stagnant_limit': 5
    }
    
    print("Configuration (Frequency-Based):")
    for k, v in CONFIG.items():
        print(f"  {k}: {v}")
    print()
    
    try:
        best = run_genetic_algorithm(**CONFIG)
        print("\n" + "=" * 60)
        print("[Frequency-Based GA Complete]")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

def item_run_raw_text_ga(show_title):
    if show_title:
        return "Run GA - Raw Text Based"
    
    print("\n" + "=" * 60)
    print("RAW TEXT-BASED GENETIC ALGORITHM")  
    print("=" * 60)
    print("Using raw text files directly for fitness calculation.")
    print("Processes actual text content without frequency preprocessing.")
    print()
    
    try:
        from run_ga_raw_text import run_ga_with_raw_text
        best = run_ga_with_raw_text()
        print("\n" + "=" * 60)
        print("[Raw Text-Based GA Complete]")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

def item_run_nim_ga(show_title):
    if show_title:
        return "Run GA - Nim Library Based"
    
    print("\n" + "=" * 60)
    print("NIM LIBRARY-BASED GENETIC ALGORITHM")
    print("=" * 60)
    print("Using compiled Nim library for high-performance text processing.")
    print("Fastest evaluation with compiled Nim code.")
    print()
    
    try:
        from run_ga_nim import run_ga_with_nim_processor
        best = run_ga_with_nim_processor()
        print("\n" + "=" * 60)
        print("[Nim Library-Based GA Complete]")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

def item_run_genetic(show_title):
    if show_title:
        return "Run Genetic Algorithm (Optimize Keyboard Layout)"

    from core.run_ga import run_genetic_algorithm

    print("\n[Starting Genetic Algorithm...]")
    print("=" * 60)

    CONFIG = {
        'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
        'dataset_file': 'src/data/text/processed/frequency_analysis.pkl',
        'dataset_name': 'simple_wikipedia',
        'population_size': 30,
        'max_iterations': 50,
        'stagnant_limit': 10
    }

    print("\nConfiguration:")
    for k, v in CONFIG.items():
        print(f"  {k}: {v}")
    print()

    try:
        best = run_genetic_algorithm(**CONFIG)
        print("\n" + "=" * 60)
        print("[Genetic Algorithm Complete]")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


def item_annotator(show_title):
    if show_title:
        return "Launch Keyboard Annotator GUI"

    print("\n[Launching Keyboard Annotator GUI...]")
    print("=" * 60)

    try:
        from helpers.keyboards.annotator_gui import KeyboardAnnotatorDPG
        app = KeyboardAnnotatorDPG()
        app.run()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


def item_dataset_analysis(show_title):
    if show_title:
        return "Run Dataset Analysis"
    print("\n[Dataset Analysis - Not implemented yet]")


def item_keyboard_evaluator(show_title):
    if show_title:
        return "Run Keyboard Evaluator"
    print("\n[Keyboard Evaluator - Not implemented yet]")


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

    menu = Menu("Keyboard Layout Optimization - GA Variations")

    # Register all menu item functions
    menu.add_item(item_run_frequency_based_ga)
    menu.add_item(item_run_raw_text_ga)
    menu.add_item(item_run_nim_ga)
    menu.add_item(item_run_simplified_genetic)
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
