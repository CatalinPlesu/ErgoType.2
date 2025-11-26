#!/usr/bin/env python3
"""
Main entry point for the Keyboard Layout Optimization project.
Now uses the simplified Menu class (src/ui/menu.py).
"""

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

def item_run_genetic(show_title):
    if show_title:
        return "Run Genetic Algorithm (Optimize Keyboard Layout)"

    from core.run_ga import run_genetic_algorithm

    print("\n[Starting Genetic Algorithm...]")
    print("=" * 60)

    CONFIG = {
        'keyboard_file': 'src/data/keyboards/dactyl_manuform_6x6_4.json',
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
