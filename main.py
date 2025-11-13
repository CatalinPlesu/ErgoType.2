#!/usr/bin/env python3
"""
Main entry point for the Keyboard Layout Optimization project.
Provides a menu interface to run different components of the system.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def print_header():
    """Print application header."""
    print("\n" + "=" * 60)
    print("  KEYBOARD LAYOUT OPTIMIZATION SYSTEM")
    print("=" * 60)


def print_menu():
    """Print main menu options."""
    print("\nMain Menu:")
    print("-" * 60)
    print("1. Run Genetic Algorithm (Optimize Keyboard Layout)")
    print("2. Launch Keyboard Annotator GUI")
    print("3. Run Dataset Analysis")
    print("4. Run Keyboard Evaluator")
    print("5. Run Keyboard Genotypes Visualization")
    print("6. Run Physical Keyboard Inspection")
    print("7. Run All Analysis Options")
    print("8. Exit")
    print("-" * 60)


def run_genetic_algorithm():
    """Run the genetic algorithm for keyboard optimization."""
    print("\n[Starting Genetic Algorithm...]")
    print("=" * 60)
    
    try:
        from core.run_ga import run_genetic_algorithm
        
        # Configuration
        CONFIG = {
            'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
            'dataset_file': 'src/data/text/processed/frequency_analysis.pkl',
            'dataset_name': 'simple_wikipedia',
            'population_size': 30,  # Smaller for faster testing
            'max_iterations': 50,
            'stagnant_limit': 10
        }
        
        print("\nConfiguration:")
        for key, value in CONFIG.items():
            print(f"  {key}: {value}")
        print()
        
        # Run GA
        best = run_genetic_algorithm(**CONFIG)
        
        print("\n" + "=" * 60)
        print("[Genetic Algorithm Complete]")
        print("\nTo use different parameters, modify CONFIG in main.py")
        print("=" * 60)
        
    except ImportError as e:
        print(f"\n[ERROR] Failed to import required modules: {e}")
        print("Make sure all dependencies are installed.")
    except FileNotFoundError as e:
        print(f"\n[ERROR] Required file not found: {e}")
        print("Check that all data files exist in the correct locations.")
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        import traceback
        traceback.print_exc()


def launch_annotator():
    """Launch the keyboard annotator GUI."""
    print("\n[Launching Keyboard Annotator GUI...]")
    print("=" * 60)
    
    try:
        from helpers.keyboards.annotator_gui import KeyboardAnnotatorDPG
        
        app = KeyboardAnnotatorDPG()
        app.run()
        
    except ImportError as e:
        print(f"\n[ERROR] Failed to import required modules: {e}")
        print("Make sure all dependencies are installed (dearpygui, etc.).")
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main application loop."""
    print_header()
    
    while True:
        print_menu()
        
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == '1':
                run_genetic_algorithm()
                input("\nPress Enter to return to main menu...")
                
            elif choice == '2':
                launch_annotator()
                print("\n[Annotator closed]")
                input("\nPress Enter to return to main menu...")
                
            elif choice == '3':
                print("\n[Exiting...]\n")
                sys.exit(0)
                
            else:
                print("\n[Invalid choice. Please enter 1, 2, or 3.]")
                
        except KeyboardInterrupt:
            print("\n\n[Interrupted by user. Exiting...]\n")
            sys.exit(0)
        except EOFError:
            print("\n\n[EOF detected. Exiting...]\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
