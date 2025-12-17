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

    # Get GA parameters
    console.print("[bold]Step 3: Select Run Mode[/bold]\n")
    saved_params = prefs.get_ga_params()
    
    # Import the new function
    from ui.rich_menu import get_parameter_group
    from rich.prompt import Prompt, Confirm
    
    # Choose run mode
    console.print("[bold cyan]Select GA Run Mode:[/bold cyan]")
    console.print("  [1] Run as Normal - With heuristic layouts (QWERTY, Dvorak, etc.)")
    console.print("  [2] Random Only - Skip heuristic layouts, use only random individuals")
    console.print("  [3] Continue from Previous Run - Load and continue a previous GA run")
    console.print()
    
    run_mode = Prompt.ask("Choose run mode", choices=["1", "2", "3"], default="1")
    
    skip_heuristics = (run_mode == "2")
    continue_from_run = None
    
    # If mode 3, let user select a previous run
    if run_mode == "3":
        from analysis.ga_run_loader import GARunLoader
        from pathlib import Path
        
        console.print("\n[bold]Loading Previous Runs...[/bold]\n")
        
        run_dirs = GARunLoader.find_ga_runs()
        
        if not run_dirs:
            print_error("No previous GA runs found in output/ga_results/")
            return
        
        # Display runs with their stats
        console.print("[bold]Available Previous Runs:[/bold]\n")
        
        # First, collect all run summaries with their fitness for sorting
        run_data = []
        for run_dir in run_dirs:
            try:
                loader = GARunLoader(run_dir)
                summary = loader.get_run_summary()
                
                run_name = run_dir.name
                pop_size = summary.get('population_size', 'N/A')
                total_individuals = summary.get('total_individuals', 'N/A')
                best_fitness = summary.get('best_fitness', 'N/A')
                
                # Store for sorting
                run_data.append({
                    'run_dir': run_dir,
                    'run_name': run_name,
                    'pop_size': pop_size,
                    'total_individuals': total_individuals,
                    'best_fitness': best_fitness
                })
                
            except Exception as e:
                print_warning(f"Could not load {run_dir.name}: {e}")
                continue
        
        # Sort by best fitness (lower is better), with N/A runs at the end
        def fitness_sort_key(item):
            fitness = item['best_fitness']
            if fitness == 'N/A' or fitness is None:
                return float('inf')
            return fitness
        
        run_data.sort(key=fitness_sort_key)
        
        # Now build the display options from sorted data (limit to 20)
        run_options = []
        for item in run_data[:20]:
            best_fitness = item['best_fitness']
            if isinstance(best_fitness, (int, float)):
                fitness_str = f"{best_fitness:.6f}"
            else:
                fitness_str = str(best_fitness)
            
            # Format display with consistent spacing
            display_text = (
                f"{item['run_name']:<50} "
                f"Pop: {str(item['pop_size']):>5}  "
                f"Individuals: {str(item['total_individuals']):>6}  "
                f"Fitness: {fitness_str}"
            )
            run_options.append((display_text, str(item['run_dir'])))
        
        if not run_options:
            print_error("No valid runs found to continue from")
            return
        
        result = select_from_list("Select Run to Continue", run_options)
        if result is None:
            print_warning("Cancelled")
            return
        
        _, continue_from_run = result
        print_success(f"Selected: {Path(continue_from_run).name}")
        console.print()
    
    # Choose between standard and population phases mode
    console.print("\n[bold]Step 4: Configure GA Execution Mode[/bold]\n")
    console.print("[bold cyan]Select GA Execution Mode:[/bold cyan]")
    console.print("  [1] Standard Mode - Fixed population and iterations")
    console.print("  [2] Population Phases Mode - Dynamic population with multiple phases")
    console.print()
    
    use_phases = saved_params.get('use_population_phases', False)
    default_mode = "2" if use_phases else "1"
    
    mode_choice = Prompt.ask("Choose mode", choices=["1", "2"], default=default_mode)
    use_population_phases = (mode_choice == "2")
    
    population_phases = None
    population_size = None
    max_iterations = None
    
    if use_population_phases:
        # Population Phases Mode
        console.print("\n[bold]Step 5: Define Population Phases[/bold]\n")
        console.print("[dim]Define phases as (iterations, max_population) tuples.[/dim]")
        console.print("[dim]Example: Phase 1: 30 iterations with 50 max population[/dim]\n")
        
        # Load saved phases if they exist
        saved_phases = saved_params.get('population_phases', [])
        
        if saved_phases:
            console.print("[bold]Previously saved phases:[/bold]")
            for i, (iters, pop) in enumerate(saved_phases, 1):
                console.print(f"  Phase {i}: {iters} iterations, max population {pop}")
            console.print()
            use_saved = Confirm.ask("Use saved phases?", default=True)
            if use_saved:
                population_phases = saved_phases
        
        if not population_phases:
            population_phases = []
            console.print("[bold]Add phases (enter 0 for iterations to finish):[/bold]\n")
            
            phase_num = 1
            while True:
                console.print(f"[cyan]Phase {phase_num}:[/cyan]")
                
                iterations = get_parameter(
                    "  Iterations",
                    default=30 if phase_num == 1 else 10,
                    param_type="int",
                    min_val=0,
                    max_val=1000
                )
                
                if iterations == 0:
                    break
                
                max_pop = get_parameter(
                    "  Max population",
                    default=50,
                    param_type="int",
                    min_val=1,
                    max_val=5000
                )
                
                population_phases.append((iterations, max_pop))
                console.print(f"  ✅ Added phase {phase_num}: {iterations} iterations, max population {max_pop}\n")
                phase_num += 1
            
            if not population_phases:
                console.print("[yellow]⚠️  No phases defined, switching to standard mode[/yellow]\n")
                use_population_phases = False
    
    if not use_population_phases:
        # Standard Mode - Group 1: Main GA Parameters
        console.print("\n[bold]Step 5: Configure GA Parameters[/bold]\n")
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
    else:
        # For phases mode, only get stagnation limit and processes
        console.print("\n[bold]Step 6: Configure Additional Parameters[/bold]\n")
        ga_params = get_parameter_group(
            "GA Control Parameters",
            [
                {'name': 'Stagnation limit', 'default': 10, 'param_type': 'int', 'min_val': 1, 'max_val': 100},
                {'name': 'Max parallel processes', 'default': 4, 'param_type': 'int', 'min_val': 1, 'max_val': 32},
            ],
            saved_params
        )
        
        stagnant_limit = ga_params['Stagnation limit']
        max_processes = ga_params['Max parallel processes']
    
    # Group 2: Fitts's Law Parameters (same for both modes)
    step_num = 6 if not use_population_phases else 7
    console.print(f"\n[bold]Step {step_num}: Configure Fitts's Law Parameters[/bold]\n")
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
    
    # Group 3 & 4: Finger Coefficients (same for both modes)
    step_num = 7 if not use_population_phases else 8
    console.print(f"\n[bold]Step {step_num}: Configure Finger Coefficients[/bold]\n")
    
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
    save_params = {
        'use_population_phases': use_population_phases,
        'Stagnation limit': stagnant_limit,
        'Max parallel processes': max_processes,
        "Fitts's Law constant 'a'": fitts_a,
        "Fitts's Law constant 'b'": fitts_b,
        'finger_coefficients': finger_coefficients
    }
    
    if use_population_phases:
        save_params['population_phases'] = population_phases
    else:
        save_params['Population size'] = population_size
        save_params['Max iterations'] = max_iterations
    
    prefs.set_ga_params(save_params)
    prefs.save()
    
    CONFIG = {
        'keyboard_file': keyboard_file,
        'text_file': text_file,
        'stagnant_limit': stagnant_limit,
        'max_concurrent_processes': max_processes,
        'fitts_a': fitts_a,
        'fitts_b': fitts_b,
        'finger_coefficients': finger_coefficients,
        'use_rabbitmq': use_rabbitmq,
        'skip_heuristics': skip_heuristics,
        'continue_from_run': continue_from_run
    }
    
    # Add mode-specific parameters
    if use_population_phases:
        # Validate that we have at least one phase
        if not population_phases or len(population_phases) == 0:
            print_error("No population phases defined!")
            return
            
        CONFIG['population_phases'] = population_phases
        # Set initial population size from first phase for GA initialization
        CONFIG['population_size'] = population_phases[0][1]
        # Set total iterations for display/compatibility (sum of all phase iterations)
        CONFIG['max_iterations'] = sum(p[0] for p in population_phases)
    else:
        CONFIG['population_size'] = population_size
        CONFIG['max_iterations'] = max_iterations
    
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
def item_run_ga_queue():
    """Execute a queue of GA runs sequentially"""
    try:
        from core.ga_runs_queue import GARunsQueue, create_run_config, create_parameter_exploration_queue
        from pathlib import Path
        
        print_header("Execute GA Runs Queue", "Run multiple GA configurations sequentially")
        
        console.print("[bold]About this feature:[/bold]")
        console.print("Execute multiple GA runs with different parameters sequentially.")
        console.print("The Individual ID counter is automatically reset between runs.")
        console.print()
        
        # Create a sub-menu for queue options
        submenu = RichMenu("📋 GA Runs Queue - Select Option")
        submenu.add_item("1️⃣  Run Parameter Exploration (25 configs, ~3 hours)", lambda: _execute_parameter_exploration())
        submenu.add_item("2️⃣  Load Queue from File", lambda: _execute_queue_from_file())
        submenu.add_item("3️⃣  Create Custom Queue Interactively", lambda: _create_custom_queue())
        
        submenu.display()
    
    except Exception as e:
        print_error(f"Error loading GA queue functionality: {e}")
        import traceback
        traceback.print_exc()


def _execute_parameter_exploration():
    """Execute the 25-configuration parameter exploration matrix"""
    from core.ga_runs_queue import create_parameter_exploration_queue
    from datetime import datetime
    
    print_header("Parameter Exploration Matrix", "25 configurations covering iteration/population space")
    
    queue = create_parameter_exploration_queue()
    
    console.print(f"[bold]Parameter Exploration Queue:[/bold]")
    console.print(f"Total configurations: {len(queue.runs)}")
    console.print(f"Estimated runtime: ~3 hours")
    console.print(f"All runs use: stagnant_limit=3, max_concurrent_processes=1")
    console.print()
    
    console.print("[bold]Configuration matrix:[/bold]\n")
    
    # Display in a table format
    from rich.table import Table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Iterations", justify="right", width=10)
    table.add_column("Population", justify="right", width=10)
    table.add_column("Purpose", width=30)
    
    for i, run in enumerate(queue.runs, 1):
        table.add_row(
            str(i),
            str(run['max_iterations']),
            str(run['population_size']),
            run['name'].split('_', 3)[-1].replace('_', ' ')
        )
    
    console.print(table)
    console.print()
    
    if not confirm_action("Execute all 25 configurations?", default=True):
        print_warning("Cancelled")
        return
    
    try:
        console.print()
        print_info("Starting parameter exploration...")
        results = queue.execute(verbose=True)
        
        # Save results
        timestamp = datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
        results_file = f"output/ga_queue_results/param_exploration_{timestamp}.json"
        queue.save_results(results_file)
        
        console.print()
        print_success(f"Parameter exploration complete! Results saved to {results_file}")
        
    except Exception as e:
        console.print()
        print_error(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


def _execute_queue_from_file():
    """Load and execute a queue from a JSON file"""
    from core.ga_runs_queue import GARunsQueue
    from datetime import datetime
    # Import Prompt locally to avoid dependency when queue feature isn't used
    from rich.prompt import Prompt
    import os
    
    print_header("Load Queue from File", "Execute a saved queue configuration")
    
    # Check for saved queue files
    queue_dir = Path("output/ga_queues")
    if queue_dir.exists():
        queue_files = list(queue_dir.glob("*.json"))
        if queue_files:
            console.print("[bold]Available queue files:[/bold]\n")
            for i, qf in enumerate(queue_files, 1):
                console.print(f"  {i}. {qf.name}")
            console.print()
    
    # Ask for file path
    file_path = Prompt.ask("Enter queue file path", default="output/example_ga_queue.json")
    
    if not os.path.exists(file_path):
        print_error(f"File not found: {file_path}")
        return
    
    try:
        queue = GARunsQueue()
        queue.load_from_file(file_path)
        
        print_success(f"Loaded queue from {file_path}")
        console.print(f"\n[bold]Queue contains {len(queue.runs)} runs:[/bold]\n")
        for i, run in enumerate(queue.runs, 1):
            console.print(f"  {i}. [cyan]{run['name']}[/cyan]")
            console.print(f"     Population: {run['population_size']}, Iterations: {run['max_iterations']}")
        console.print()
        
        if not confirm_action("Execute this queue?", default=True):
            print_warning("Cancelled")
            return
        
        console.print()
        print_info("Starting queue execution...")
        results = queue.execute(verbose=True)
        
        # Save results
        timestamp = datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
        results_file = f"output/ga_queue_results/queue_{timestamp}.json"
        queue.save_results(results_file)
        
        console.print()
        print_success(f"Queue execution complete! Results saved to {results_file}")
        
    except Exception as e:
        console.print()
        print_error(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


def _create_custom_queue():
    """Interactively create and execute a custom queue"""
    from core.ga_runs_queue import GARunsQueue, create_run_config
    from datetime import datetime
    # Import Prompt locally to avoid dependency when queue feature isn't used
    from rich.prompt import Prompt
    
    print_header("Create Custom Queue", "Define multiple GA runs interactively")
    
    prefs = Preferences()
    queue = GARunsQueue()
    
    # Get available keyboards and text files
    keyboards = get_available_keyboards()
    text_files = get_available_text_files()
    
    if not keyboards or not text_files:
        print_error("No keyboards or text files found!")
        return
    
    console.print("[bold]Add runs to the queue[/bold]")
    console.print("[dim]You can add multiple runs with different parameters[/dim]\n")
    
    while True:
        run_number = len(queue.runs) + 1
        console.print(f"\n[bold cyan]Configuring Run #{run_number}[/bold cyan]\n")
        
        # Get run name
        default_name = f"Run {run_number}"
        run_name = Prompt.ask("Run name", default=default_name)
        
        # Keyboard selection
        console.print("\n[bold]Select Keyboard:[/bold]")
        default_keyboard = prefs.get_last_keyboard()
        result = select_from_list("Available Keyboards", keyboards, default_keyboard)
        if result is None:
            print_warning("Using default keyboard")
            keyboard_file = 'src/data/keyboards/ansi_60_percent.json'
        else:
            _, keyboard_file = result
        
        # Text file selection
        console.print("\n[bold]Select Text File:[/bold]")
        default_text = prefs.get_last_text_file()
        result = select_from_list("Available Text Files", text_files, default_text, show_size=True)
        if result is None:
            print_warning("Using default text file")
            text_file = 'src/data/text/raw/simple_wikipedia_dataset.txt'
        else:
            _, text_file = result
        
        # Get GA parameters
        console.print("\n[bold]GA Parameters:[/bold]")
        saved_params = prefs.get_ga_params()
        
        from ui.rich_menu import get_parameter_group
        
        ga_params = get_parameter_group(
            "GA Parameters",
            [
                {'name': 'Population size', 'default': saved_params.get('Population size', 30), 
                 'param_type': 'int', 'min_val': 1, 'max_val': 500},
                {'name': 'Max iterations', 'default': saved_params.get('Max iterations', 50), 
                 'param_type': 'int', 'min_val': 1, 'max_val': 1000},
                {'name': 'Stagnation limit', 'default': saved_params.get('Stagnation limit', 10), 
                 'param_type': 'int', 'min_val': 1, 'max_val': 100},
                {'name': 'Max parallel processes', 'default': saved_params.get('Max parallel processes', 4), 
                 'param_type': 'int', 'min_val': 1, 'max_val': 32},
            ],
            saved_params
        )
        
        # Create run configuration as a dictionary
        run_config = create_run_config(
            name=run_name,
            keyboard_file=keyboard_file,
            text_file=text_file,
            population_size=ga_params['Population size'],
            max_iterations=ga_params['Max iterations'],
            stagnant_limit=ga_params['Stagnation limit'],
            max_concurrent_processes=ga_params['Max parallel processes']
        )
        
        queue.add_run(run_config)
        print_success(f"Added run: {run_name}")
        
        # Ask if user wants to add more runs
        console.print()
        if not confirm_action("Add another run to the queue?", default=False):
            break
    
    # Show queue summary
    console.print(f"\n[bold]Queue Summary:[/bold]")
    console.print(f"Total runs: {len(queue.runs)}\n")
    for i, run in enumerate(queue.runs, 1):
        console.print(f"  {i}. [cyan]{run['name']}[/cyan]")
        console.print(f"     Population: {run['population_size']}, Iterations: {run['max_iterations']}")
    console.print()
    
    # Ask to save queue configuration
    if confirm_action("Save queue configuration to file?", default=True):
        timestamp = datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
        queue_file = f"output/ga_queues/custom_queue_{timestamp}.json"
        Path(queue_file).parent.mkdir(parents=True, exist_ok=True)
        queue.save_to_file(queue_file)
        print_success(f"Queue saved to {queue_file}")
        console.print()
    
    # Execute the queue
    if confirm_action("Execute this queue now?", default=True):
        try:
            console.print()
            print_info("Starting queue execution...")
            results = queue.execute(verbose=True)
            
            # Save results
            timestamp = datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
            results_file = f"output/ga_queue_results/queue_{timestamp}.json"
            queue.save_results(results_file)
            
            console.print()
            print_success(f"Queue execution complete! Results saved to {results_file}")
            
        except Exception as e:
            console.print()
            print_error(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    else:
        print_warning("Queue execution cancelled")


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
    menu.add_item("📋 Execute GA Runs Queue", item_run_ga_queue)
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
