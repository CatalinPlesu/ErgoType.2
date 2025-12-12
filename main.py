#!/usr/bin/env python3
"""
Main entry point for the Keyboard Layout Optimization project.
Uses simulation-based genetic algorithm with C# fitness calculation.
Supports distributed processing via RabbitMQ.
"""

import sys
from pathlib import Path
import os

# Add src to import path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ui.rich_menu import (
    RichMenu, console, select_from_list, get_parameter,
    display_config, confirm_action, print_header, print_success,
    print_error, print_info, print_warning
)
from ui.preferences import Preferences


def get_available_keyboards():
    """Get list of available physical keyboard layouts"""
    keyboards_dir = Path(__file__).parent / "src" / "data" / "keyboards"
    keyboard_files = []
    
    for file in keyboards_dir.glob("*.json"):
        if file.name != "readme.md":
            name = file.stem.replace('_', ' ').title()
            keyboard_files.append((name, str(file.relative_to(Path(__file__).parent))))
    
    return keyboard_files


def get_available_text_files():
    """Get list of available text files for simulation"""
    text_dir = Path(__file__).parent / "src" / "data" / "text" / "raw"
    text_files = []
    
    for file in text_dir.glob("*.txt"):
        name = file.stem.replace('_', ' ').title()
        size_mb = file.stat().st_size / (1024 * 1024)
        text_files.append((name, str(file.relative_to(Path(__file__).parent)), size_mb))
    
    return text_files


def get_available_language_layouts():
    """Get list of available language layout remappings"""
    layouts_dir = Path(__file__).parent / "src" / "data" / "languages"
    language_layouts = [("None (English/Default)", None)]  # Add default option
    
    if not layouts_dir.exists():
        return language_layouts
    
    for file in layouts_dir.glob("*.py"):
        if file.name == "__init__.py":
            continue
        
        # Convert filename to display name
        # e.g., "romanian_programmers.py" -> "Romanian Programmers"
        name = file.stem.replace('_', ' ').title()
        module_path = f"data.languages.{file.stem}"
        language_layouts.append((name, module_path))
    
    return language_layouts


def print_app_header():
    """Print application header"""
    print_header(
        "KEYBOARD LAYOUT OPTIMIZATION SYSTEM",
        "Distributed Simulation-Based with C# Fitness"
    )


# -----------------------------
#   MENU ITEM WRAPPERS
# -----------------------------

def item_run_genetic():
    """Run Genetic Algorithm (Master Mode)"""
    from core.run_ga import run_genetic_algorithm
    
    prefs = Preferences()
    
    print_header("Genetic Algorithm - Master Mode", "Configure and run the genetic algorithm")
    
    # Get available keyboards
    keyboards = get_available_keyboards()
    if not keyboards:
        print_error("No keyboard layouts found in src/data/keyboards/")
        return
    
    # Keyboard selection
    console.print("[bold]Step 1: Select Physical Keyboard[/bold]\n")
    default_keyboard = prefs.get_last_keyboard()
    result = select_from_list("Available Keyboards", keyboards, default_keyboard)
    if result is None:
        print_warning("Cancelled")
        return
    _, keyboard_file = result
    prefs.set_last_keyboard(keyboard_file)
    print_success(f"Selected: {keyboard_file}")
    console.print()

    # Text file selection
    console.print("[bold]Step 2: Select Text File[/bold]\n")
    text_files = get_available_text_files()
    if not text_files:
        print_error("No text files found in src/data/text/raw/")
        return
    
    default_text = prefs.get_last_text_file()
    result = select_from_list("Available Text Files", text_files, default_text, show_size=True)
    if result is None:
        print_warning("Cancelled")
        return
    _, text_file = result
    prefs.set_last_text_file(text_file)
    print_success(f"Selected: {text_file}")
    console.print()

    # Language layout selection
    console.print("[bold]Step 3: Select Language Layout Remapping (Optional)[/bold]\n")
    language_layouts = get_available_language_layouts()
    
    default_language = prefs.get_last_language_layout()
    result = select_from_list("Available Language Layouts", language_layouts, default_language)
    if result is None:
        print_warning("Cancelled")
        return
    _, language_layout = result
    prefs.set_last_language_layout(language_layout)
    
    if language_layout:
        print_success(f"Selected: {language_layout}")
    else:
        print_success("Selected: None (English/Default)")
    console.print()

    # Get GA parameters
    console.print("[bold]Step 4: Configure GA Parameters[/bold]\n")
    saved_params = prefs.get_ga_params()
    
    # Import the new function
    from ui.rich_menu import get_parameter_group
    
    # Group 1: Main GA Parameters
    ga_params = get_parameter_group(
        "Main GA Parameters",
        [
            {'name': 'Population size', 'default': 30, 'param_type': 'int', 'min_val': 1, 'max_val': 500},
            {'name': 'Max iterations', 'default': 50, 'param_type': 'int', 'min_val': 1, 'max_val': 1000},
            {'name': 'Stagnation limit', 'default': 10, 'param_type': 'int', 'min_val': 1, 'max_val': 100},
            {'name': 'Max parallel processes', 'default': 4, 'param_type': 'int', 'min_val': 1, 'max_val': 32},
        ],
        saved_params
    )
    
    population_size = ga_params['Population size']
    max_iterations = ga_params['Max iterations']
    stagnant_limit = ga_params['Stagnation limit']
    max_processes = ga_params['Max parallel processes']
    
    # Group 2: Fitts's Law Parameters
    fitts_params = get_parameter_group(
        "Fitts's Law Parameters",
        [
            {'name': "Fitts's Law constant 'a'", 'default': 0.5, 'param_type': 'float', 'min_val': 0.0, 'max_val': 5.0},
            {'name': "Fitts's Law constant 'b'", 'default': 0.3, 'param_type': 'float', 'min_val': 0.0, 'max_val': 5.0},
        ],
        saved_params
    )
    
    fitts_a = fitts_params["Fitts's Law constant 'a'"]
    fitts_b = fitts_params["Fitts's Law constant 'b'"]
    
    # Group 3: Finger Coefficients - Left Hand (fingers 1-5)
    # Default finger coefficients for 10 fingers
    default_finger_coeffs = [0.07, 0.06, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.06, 0.07]
    saved_finger_coeffs = saved_params.get('finger_coefficients', default_finger_coeffs)
    
    finger_left_params = get_parameter_group(
        "Left Hand Finger Coefficients (fingers 1-5: pinky to thumb)",
        [
            {'name': f'Left Finger {i+1}', 'default': default_finger_coeffs[i], 
             'param_type': 'float', 'min_val': 0.0, 'max_val': 1.0}
            for i in range(5)
        ],
        {f'Left Finger {i+1}': saved_finger_coeffs[i] if i < len(saved_finger_coeffs) else default_finger_coeffs[i] for i in range(5)}
    )
    
    # Group 4: Finger Coefficients - Right Hand (fingers 6-10)
    finger_right_params = get_parameter_group(
        "Right Hand Finger Coefficients (fingers 6-10: thumb to pinky)",
        [
            {'name': f'Right Finger {i+1}', 'default': default_finger_coeffs[i], 
             'param_type': 'float', 'min_val': 0.0, 'max_val': 1.0}
            for i in range(5, 10)
        ],
        {f'Right Finger {i+1}': saved_finger_coeffs[i] if i < len(saved_finger_coeffs) else default_finger_coeffs[i] for i in range(5, 10)}
    )
    
    # Combine both hands
    finger_coefficients = [finger_left_params[f'Left Finger {i+1}'] for i in range(5)] + \
                          [finger_right_params[f'Right Finger {i+1}'] for i in range(5, 10)]
    
    # Simply use rabbitmq if it is on
    use_rabbitmq = True

    # Save parameters for next time
    prefs.set_ga_params({
        'Population size': population_size,
        'Max iterations': max_iterations,
        'Stagnation limit': stagnant_limit,
        'Max parallel processes': max_processes,
        "Fitts's Law constant 'a'": fitts_a,
        "Fitts's Law constant 'b'": fitts_b,
        'finger_coefficients': finger_coefficients
    })
    prefs.save()
    
    CONFIG = {
        'keyboard_file': keyboard_file,
        'text_file': text_file,
        'language_layout': language_layout,
        'population_size': population_size,
        'max_iterations': max_iterations,
        'stagnant_limit': stagnant_limit,
        'max_concurrent_processes': max_processes,
        'fitts_a': fitts_a,
        'fitts_b': fitts_b,
        'finger_coefficients': finger_coefficients,
        'use_rabbitmq': use_rabbitmq
    }
    
    console.print()
    display_config("Final Configuration", CONFIG)
    console.print()
    
    if not confirm_action("Start Genetic Algorithm?", default=True):
        print_warning("Cancelled")
        return
    
    try:
        console.print()
        print_info("Starting Genetic Algorithm...")
        best = run_genetic_algorithm(**CONFIG)
        console.print()
        print_success("Genetic Algorithm Complete!")
    
    except Exception as e:
        console.print()
        print_error(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


def item_run_worker():
    """Run as Worker Node (Distributed Processing)"""
    import multiprocessing as mp
    from core.ga import GeneticAlgorithmSimulation
    
    prefs = Preferences()
    
    print_header("Worker Node", "Process jobs from the distributed queue")
    
    saved_params = prefs.get_worker_params()
    
    console.print("[bold]Worker Configuration[/bold]\n")
    
    # Simply use rabbitmq if it is on
    use_rabbitmq = True
    
    if not use_rabbitmq:
        print_warning("Worker mode requires RabbitMQ or will use in-memory queue (only useful for testing)")
        if not confirm_action("Continue anyway?", default=False):
            print_warning("Cancelled")
            return
    
    max_processes = get_parameter(
        "Max parallel processes",
        saved_params.get('max_processes', mp.cpu_count()),
        param_type="int",
        min_val=1,
        max_val=64
    )
    
    # Save parameters
    prefs.set_worker_params({
        'use_rabbitmq': use_rabbitmq,
        'max_processes': max_processes
    })
    prefs.save()
    
    console.print()
    display_config("Worker Configuration", {
        'use_rabbitmq': use_rabbitmq,
        'max_processes': max_processes
    })
    console.print()
    
    if not confirm_action("Start Worker Node? This will run indefinitely until stopped.", default=True):
        print_warning("Cancelled")
        return
    
    try:
        console.print()
        print_info("Starting Worker Node...")
        print_info("Worker will wait for jobs from master...")
        print_info("Press Ctrl+C to stop the worker")
        console.print()
        
        # Initialize in worker mode - this will block and process jobs
        worker = GeneticAlgorithmSimulation(
            keyboard_file='src/data/keyboards/ansi_60_percent.json',  # Will be overridden by config from master
            text_file='src/data/text/raw/simple_wikipedia_dataset.txt',  # Will be overridden
            max_concurrent_processes=max_processes,
            use_rabbitmq=use_rabbitmq,
            is_worker=True  # This makes it run in worker mode
        )
        
        # Worker runs indefinitely in __init__, won't reach here unless interrupted
        
    except KeyboardInterrupt:
        console.print()
        print_warning("Worker stopped by user")
    except Exception as e:
        console.print()
        print_error(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


def item_annotator():
    """Launch Keyboard Annotator GUI"""
    print_header("Keyboard Annotator GUI", "Interactive keyboard layout editor")
    
    keyboards = get_available_keyboards()
    if not keyboards:
        print_error("No keyboard layouts found!")
        return
    
    result = select_from_list("Available Keyboards", keyboards)
    if result is None:
        keyboard_file = 'src/data/keyboards/ansi_60_percent.json'
        print_warning(f"Using default keyboard: {keyboard_file}")
    else:
        _, keyboard_file = result
        print_success(f"Loading keyboard: {keyboard_file}")
    
    try:
        from helpers.keyboards.annotator_gui import KeyboardAnnotatorDPG
        app = KeyboardAnnotatorDPG()
        app.run()
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()


def item_text_analysis():
    """Analyze Text File"""
    print_header("Text File Analysis", "Analyze character frequencies and text metrics")
    
    text_files = get_available_text_files()
    if not text_files:
        print_error("No text files found!")
        return
    
    result = select_from_list("Available Text Files", text_files, show_size=True)
    if result is None:
        print_warning("Cancelled")
        return
    
    idx, text_file = result
    name, _, size_mb = text_files[idx]
    
    console.print()
    print_success(f"Selected: {name}")
    print_info(f"File: {text_file}")
    print_info(f"Size: {size_mb:.2f} MB")
    console.print()
    print_warning("[Text Analysis - Coming soon!]")
    console.print("[dim]This feature will provide detailed statistics about character frequencies,[/dim]")
    console.print("[dim]word distributions, bigrams, trigrams, and other text metrics.[/dim]")


def item_keyboard_evaluator():
    """Evaluate Keyboard Layout"""
    print_header("Keyboard Layout Evaluator", "Analyze keyboard layout efficiency")
    
    keyboards = get_available_keyboards()
    if not keyboards:
        print_error("No keyboard layouts found!")
        return
    
    result = select_from_list("Available Keyboards", keyboards)
    if result is None:
        print_warning("Cancelled")
        return
    idx, keyboard_file = result
    keyboard_name = keyboards[idx][0]
    print_success(f"Selected: {keyboard_name}")
    console.print()
    
    text_files = get_available_text_files()
    if not text_files:
        print_error("No text files found!")
        return
    
    result = select_from_list("Available Text Files", text_files, show_size=True)
    if result is None:
        print_warning("Cancelled")
        return
    idx, text_file = result
    text_name = text_files[idx][0]
    
    console.print()
    print_info(f"Keyboard: {keyboard_name}")
    print_info(f"Text: {text_name}")
    console.print()
    print_warning("[Keyboard Evaluator - Coming soon!]")
    console.print("[dim]This feature will analyze keyboard layout efficiency using simulation,[/dim]")
    console.print("[dim]providing metrics like finger travel distance, typing time, and heatmaps.[/dim]")


def item_layout_comparison():
    """Compare Standard Layouts"""
    print_header("Layout Comparison", "Compare QWERTY, Dvorak, Colemak, etc.")
    
    print_warning("[Layout Comparison - Coming soon!]")
    console.print("[dim]This feature will compare standard layouts (QWERTY, Dvorak, Colemak, etc.)[/dim]")
    console.print("[dim]using simulation-based fitness calculation with detailed metrics and heatmaps.[/dim]")


def item_visualize_layout():
    """Visualize Keyboard Layout"""
    print_header("Layout Visualization", "Generate SVG visualizations")
    
    print_warning("[Layout Visualization - Coming soon!]")
    console.print("[dim]This feature will generate SVG visualizations of keyboard layouts[/dim]")
    console.print("[dim]with optional heatmaps showing key usage patterns.[/dim]")


def item_generate_heuristics():
    """Generate all heuristic layout heatmaps"""
    from helpers.layouts.heuristic_generator import generate_all_heuristics
    
    prefs = Preferences()
    
    print_header("Generate Heuristic Heatmaps", "Pre-generate heatmaps for all standard layouts")
    
    console.print("[bold]About this feature:[/bold]")
    console.print("This will generate heatmaps for all combinations of:")
    console.print("  • Keyboards (ANSI 60%, ThinkPad, Dactyl, Ferris, etc.)")
    console.print("  • Datasets (text files used for analysis)")
    console.print("  • Layouts (QWERTY, Dvorak, Colemak, Workman, etc.)")
    console.print()
    console.print("[dim]Generated heatmaps are cached and reused by the GA to speed up startup.[/dim]")
    console.print()
    
    # Get available keyboards
    keyboards = get_available_keyboards()
    if not keyboards:
        print_error("No keyboard layouts found in src/data/keyboards/")
        return
    
    # Get available text files
    text_files = get_available_text_files()
    if not text_files:
        print_error("No text files found in src/data/text/")
        return
    
    # Show what will be generated
    from data.layouts.keyboard_genotypes import LAYOUT_DATA
    total_combinations = len(keyboards) * len(text_files) * len(LAYOUT_DATA)
    
    console.print(f"[bold]Summary:[/bold]")
    console.print(f"  • {len(keyboards)} keyboards")
    console.print(f"  • {len(text_files)} datasets")
    console.print(f"  • {len(LAYOUT_DATA)} layouts")
    console.print(f"  • [yellow]{total_combinations}[/yellow] total combinations")
    console.print()
    
    # Ask for confirmation
    if not confirm_action("Generate all heuristic heatmaps?", default=True):
        print_warning("Cancelled")
        return
    
    # Get Fitts's law parameters (same as GA)
    console.print("\n[bold]Fitts's Law Parameters[/bold]")
    console.print("[dim]These should match your typical GA parameters for consistency.[/dim]\n")
    
    saved_params = prefs.get_ga_params()
    
    from ui.rich_menu import get_parameter_group
    
    fitts_params = get_parameter_group(
        "Fitts's Law Parameters",
        [
            {'name': "Fitts's Law constant 'a'", 'default': 0.5, 'param_type': 'float', 'min_val': 0.0, 'max_val': 5.0},
            {'name': "Fitts's Law constant 'b'", 'default': 0.3, 'param_type': 'float', 'min_val': 0.0, 'max_val': 5.0},
        ],
        saved_params
    )
    
    fitts_a = fitts_params["Fitts's Law constant 'a'"]
    fitts_b = fitts_params["Fitts's Law constant 'b'"]
    
    # Get finger coefficients
    default_finger_coeffs = [0.07, 0.06, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.06, 0.07]
    saved_finger_coeffs = saved_params.get('finger_coefficients', default_finger_coeffs)
    
    # Get parallel processing parameters
    console.print("\n[bold]Parallel Processing Configuration[/bold]")
    console.print("[dim]Use multiple CPU cores to speed up generation.[/dim]\n")
    
    import multiprocessing as mp
    cpu_count = mp.cpu_count()
    
    parallel_params = get_parameter_group(
        "Parallel Processing",
        [
            {'name': 'Max parallel workers', 'default': cpu_count, 'param_type': 'int', 'min_val': 1, 'max_val': cpu_count * 2},
        ],
        saved_params
    )
    
    max_workers = parallel_params['Max parallel workers']
    
    # Ask if user wants to regenerate existing heatmaps
    console.print()
    force_regenerate = confirm_action(
        "Regenerate heatmaps that already exist?",
        default=False
    )
    
    console.print()
    display_config("Generation Configuration", {
        'keyboards': len(keyboards),
        'datasets': len(text_files),
        'layouts': len(LAYOUT_DATA),
        'total_combinations': total_combinations,
        'fitts_a': fitts_a,
        'fitts_b': fitts_b,
        'max_workers': max_workers,
        'force_regenerate': force_regenerate
    })
    console.print()
    
    if not confirm_action("Start generation?", default=True):
        print_warning("Cancelled")
        return
    
    try:
        console.print()
        print_info("Starting heuristic generation...")
        console.print()
        
        # Convert keyboard and text file tuples to paths
        keyboard_paths = [kb[1] for kb in keyboards]
        text_paths = [tf[1] for tf in text_files]
        
        results = generate_all_heuristics(
            keyboards=keyboard_paths,
            text_files=text_paths,
            fitts_a=fitts_a,
            fitts_b=fitts_b,
            finger_coefficients=saved_finger_coeffs,
            force_regenerate=force_regenerate,
            verbose=True,
            max_workers=max_workers
        )
        
        # Count successes and failures
        total_success = sum(
            1 for kb in results.values()
            for ds in kb.values()
            for success in ds.values()
            if success
        )
        total_failed = total_combinations - total_success
        
        console.print()
        if total_failed == 0:
            print_success(f"All {total_success} heuristic heatmaps generated successfully!")
        else:
            print_warning(f"Completed: {total_success} successful, {total_failed} failed")
        
        console.print()
        print_info("Heatmaps are cached in: output/{dataset}/{keyboard}/{heatmap_type}/")
        console.print()
        
    except Exception as e:
        console.print()
        print_error(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
def item_analyze_ga_runs():
    """Analyze GA Runs - Sub-menu for inspection and comparison"""
    print_header("Analyze GA Runs", "Inspect and compare genetic algorithm results")
    
    # Create a sub-menu for analysis options
    submenu = RichMenu("🔬 GA Run Analysis - Select Option")
    submenu.add_item("🔍 Single Run Inspection", item_single_run_inspection)
    submenu.add_item("📊 Multi-Run Comparison", item_multi_run_comparison)
    
    submenu.display()


def item_single_run_inspection():
    """Single GA Run Inspector"""
    from src.analysis.single_run_inspector import run_single_run_inspector
    run_single_run_inspector()


def item_multi_run_comparison():
    """Multi-Run GA Comparator"""
    from src.analysis.multi_run_comparator import run_multi_run_comparator
    run_multi_run_comparator()


# -----------------------------
#           MAIN
# -----------------------------

def main():
    print_app_header()
    
    menu = RichMenu("🎹 Keyboard Layout Optimization - Main Menu")
    
    # Register all menu item functions
    menu.add_item("🚀 Run Genetic Algorithm (Master Mode)", item_run_genetic)
    menu.add_item("🔧 Run as Worker Node (Distributed Processing)", item_run_worker)
    menu.add_item("🎯 Generate All Heuristic Heatmaps", item_generate_heuristics)
    menu.add_item("🔬 Analyze GA Runs", item_analyze_ga_runs)
    menu.add_item("⌨️  Evaluate Keyboard Layout", item_keyboard_evaluator)
    menu.add_item("📊 Compare Standard Layouts", item_layout_comparison)
    menu.add_item("📝 Analyze Text File", item_text_analysis)
    menu.add_item("🎨 Visualize Keyboard Layout", item_visualize_layout)
    menu.add_item("🖊️  Launch Keyboard Annotator GUI", item_annotator)
    
    # Run interactive menu
    menu.display()
    
    console.print("\n[yellow]Goodbye![/yellow]\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
