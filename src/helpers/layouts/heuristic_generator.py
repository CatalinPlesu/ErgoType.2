"""
Module for generating and caching heuristic layout heatmaps.

This module generates heatmaps for standard layouts (QWERTY, Dvorak, Colemak, etc.)
across all keyboard and dataset combinations, storing them in a standardized cache
structure for reuse by the genetic algorithm.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, str(Path(PROJECT_ROOT) / "src"))

from data.layouts.keyboard_genotypes import LAYOUT_DATA
from core.evaluator import Evaluator
from core.map_json_exporter import CSharpFitnessConfig
from helpers.layouts.visualization import generate_all_visualizations


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string for safe use as a filename or directory name.
    Removes or replaces characters that could cause filesystem issues or path traversal.
    """
    # Replace path separators and parent directory references
    name = name.replace('/', '_').replace('\\', '_').replace('..', '_')
    # Remove other potentially problematic characters
    name = ''.join(c if c.isalnum() or c in '-_.' else '_' for c in name)
    # Ensure the name is not empty
    return name if name else 'unnamed'


def get_dataset_name(text_file_path: str) -> str:
    """Extract and sanitize dataset name from text file path."""
    path = Path(text_file_path)
    return sanitize_filename(path.stem)


def get_keyboard_name(keyboard_file_path: str) -> str:
    """Extract and sanitize keyboard name from keyboard file path."""
    path = Path(keyboard_file_path)
    return sanitize_filename(path.stem)


def get_heuristic_cache_path(
    dataset_name: str,
    keyboard_name: str,
    layout_name: str,
    heatmap_type: str
) -> Path:
    """
    Get the cache path for a heuristic layout heatmap.
    
    Structure: output/{dataset_name}/{keyboard_name}/{heatmap_type}/{layout_name}.svg
    
    Args:
        dataset_name: Name of the text dataset (will be sanitized)
        keyboard_name: Name of the keyboard (will be sanitized)
        layout_name: Name of the layout (e.g., 'qwerty', 'dvorak') (will be sanitized)
        heatmap_type: Type of heatmap ('press_heatmap', 'hover_heatmap', 'layout')
    
    Returns:
        Path object for the cache file
    """
    # Sanitize all path components to prevent path traversal
    safe_dataset = sanitize_filename(dataset_name)
    safe_keyboard = sanitize_filename(keyboard_name)
    safe_layout = sanitize_filename(layout_name)
    safe_heatmap_type = sanitize_filename(heatmap_type)
    
    cache_dir = Path(PROJECT_ROOT) / "output" / safe_dataset / safe_keyboard / safe_heatmap_type
    return cache_dir / f"{safe_layout}.svg"


def check_heuristic_cached(
    dataset_name: str,
    keyboard_name: str,
    layout_name: str
) -> bool:
    """
    Check if all heatmaps for a heuristic layout are already cached.
    
    Args:
        dataset_name: Name of the text dataset
        keyboard_name: Name of the keyboard
        layout_name: Name of the layout
    
    Returns:
        True if all heatmaps exist, False otherwise
    """
    heatmap_types = ['press_heatmap', 'hover_heatmap', 'layout']
    
    for heatmap_type in heatmap_types:
        cache_path = get_heuristic_cache_path(
            dataset_name, keyboard_name, layout_name, heatmap_type
        )
        if not cache_path.exists():
            return False
    
    return True


def generate_heuristic_layout(
    layout_name: str,
    genotype: List[str],
    keyboard_file: str,
    text_file: str,
    fitts_a: float = 0.5,
    fitts_b: float = 0.3,
    finger_coefficients: Optional[List[float]] = None,
    force_regenerate: bool = False
) -> Tuple[bool, str]:
    """
    Generate heatmaps for a single heuristic layout.
    
    Args:
        layout_name: Name of the layout (e.g., 'qwerty')
        genotype: Layout genotype (list of characters)
        keyboard_file: Path to keyboard JSON file
        text_file: Path to text dataset file
        fitts_a: Fitts's law parameter a
        fitts_b: Fitts's law parameter b
        finger_coefficients: List of finger coefficients
        force_regenerate: If True, regenerate even if cached
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    dataset_name = get_dataset_name(text_file)
    keyboard_name = get_keyboard_name(keyboard_file)
    
    # Check if already cached
    if not force_regenerate and check_heuristic_cached(dataset_name, keyboard_name, layout_name):
        return True, f"Already cached: {layout_name}"
    
    try:
        # Load C# fitness library
        from core.clr_loader_helper import load_csharp_fitness_library
        Fitness, _ = load_csharp_fitness_library(PROJECT_ROOT)
    except Exception as e:
        return False, f"Error loading C# library: {e}"
    
    try:
        # Create evaluator for this layout
        evaluator = Evaluator(debug=False)
        evaluator.load_keyoard(keyboard_file)
        evaluator.load_layout()
        
        # Remap to the target layout
        evaluator.layout.remap(LAYOUT_DATA["qwerty"], list(genotype))
        
        # Generate config
        config_gen = CSharpFitnessConfig(
            keyboard=evaluator.keyboard,
            layout=evaluator.layout
        )
        
        json_string = config_gen.generate_json_string(
            text_file_path=text_file if os.path.isabs(text_file) else os.path.join(PROJECT_ROOT, text_file),
            finger_coefficients=finger_coefficients or [0.07, 0.06, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.06, 0.07],
            fitts_a=fitts_a,
            fitts_b=fitts_b
        )
        
        # Compute statistics
        fitness_calculator = Fitness(json_string)
        stats_json = fitness_calculator.ComputeStats()
        
        # Create cache directory structure
        base_cache_dir = Path(PROJECT_ROOT) / "output" / dataset_name / keyboard_name
        base_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for each heatmap type
        for heatmap_type in ['press_heatmap', 'hover_heatmap', 'layout']:
            (base_cache_dir / heatmap_type).mkdir(exist_ok=True)
        
        # Generate all visualizations (without saving to avoid duplicate files)
        layout_svg, press_svg, hover_svg = generate_all_visualizations(
            stats_json=stats_json,
            keyboard=evaluator.keyboard,
            layout=evaluator.layout,
            layout_name=layout_name,
            layer_idx=0,
            save_dir=None  # Don't save during generation, we'll save to our cache structure
        )
        
        # Sanitize layout name for safe filename usage
        safe_layout_name = sanitize_filename(layout_name)
        
        # Save to cache structure
        with open(base_cache_dir / "layout" / f"{safe_layout_name}.svg", 'w') as f:
            f.write(layout_svg.data)
        with open(base_cache_dir / "press_heatmap" / f"{safe_layout_name}.svg", 'w') as f:
            f.write(press_svg.data)
        with open(base_cache_dir / "hover_heatmap" / f"{safe_layout_name}.svg", 'w') as f:
            f.write(hover_svg.data)
        
        # Also save stats JSON for reference
        stats_path = base_cache_dir / f"{safe_layout_name}_stats.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            f.write(stats_json)
        
        return True, f"Generated: {layout_name}"
        
    except Exception as e:
        import traceback
        error_msg = f"Error processing {layout_name}: {str(e)}\n{traceback.format_exc()}"
        return False, error_msg


def generate_all_heuristics(
    keyboards: Optional[List[str]] = None,
    text_files: Optional[List[str]] = None,
    fitts_a: float = 0.5,
    fitts_b: float = 0.3,
    finger_coefficients: Optional[List[float]] = None,
    force_regenerate: bool = False,
    verbose: bool = True
) -> Dict[str, Dict[str, Dict[str, bool]]]:
    """
    Generate heuristic heatmaps for all combinations of keyboards, datasets, and layouts.
    
    Args:
        keyboards: List of keyboard file paths (default: all keyboards in src/data/keyboards/)
        text_files: List of text file paths (default: all text files in src/data/text/)
        fitts_a: Fitts's law parameter a
        fitts_b: Fitts's law parameter b
        finger_coefficients: List of finger coefficients
        force_regenerate: If True, regenerate even if cached
        verbose: If True, print progress messages
    
    Returns:
        Dict mapping keyboard -> dataset -> layout -> success status
    """
    # Get default keyboard and text file lists if not provided
    if keyboards is None:
        keyboards_dir = Path(PROJECT_ROOT) / "src" / "data" / "keyboards"
        keyboards = [str(f) for f in keyboards_dir.glob("*.json")]
    
    if text_files is None:
        # Try both raw and processed directories
        text_files = []
        text_raw_dir = Path(PROJECT_ROOT) / "src" / "data" / "text" / "raw"
        text_processed_dir = Path(PROJECT_ROOT) / "src" / "data" / "text" / "processed"
        
        if text_raw_dir.exists():
            text_files.extend([str(f) for f in text_raw_dir.glob("*.txt")])
        if text_processed_dir.exists():
            text_files.extend([str(f) for f in text_processed_dir.glob("*.txt")])
    
    results = {}
    total_combinations = len(keyboards) * len(text_files) * len(LAYOUT_DATA)
    current = 0
    
    if verbose:
        print("=" * 80)
        print("GENERATING HEURISTIC LAYOUT HEATMAPS")
        print("=" * 80)
        print(f"Keyboards: {len(keyboards)}")
        print(f"Datasets: {len(text_files)}")
        print(f"Layouts: {len(LAYOUT_DATA)}")
        print(f"Total combinations: {total_combinations}")
        print("=" * 80)
        print()
    
    for keyboard_file in keyboards:
        keyboard_name = get_keyboard_name(keyboard_file)
        results[keyboard_name] = {}
        
        for text_file in text_files:
            dataset_name = get_dataset_name(text_file)
            results[keyboard_name][dataset_name] = {}
            
            if verbose:
                print(f"\n{'='*80}")
                print(f"Keyboard: {keyboard_name}")
                print(f"Dataset: {dataset_name}")
                print(f"{'='*80}")
            
            for layout_name, genotype in LAYOUT_DATA.items():
                current += 1
                
                if verbose:
                    print(f"\n[{current}/{total_combinations}] Processing: {layout_name}...")
                
                success, message = generate_heuristic_layout(
                    layout_name=layout_name,
                    genotype=genotype,
                    keyboard_file=keyboard_file,
                    text_file=text_file,
                    fitts_a=fitts_a,
                    fitts_b=fitts_b,
                    finger_coefficients=finger_coefficients,
                    force_regenerate=force_regenerate
                )
                
                results[keyboard_name][dataset_name][layout_name] = success
                
                if verbose:
                    status = "✅" if success else "❌"
                    print(f"{status} {message}")
    
    if verbose:
        print("\n" + "=" * 80)
        print("GENERATION COMPLETE")
        print("=" * 80)
        
        # Summary
        total_success = sum(
            1 for kb in results.values()
            for ds in kb.values()
            for success in ds.values()
            if success
        )
        total_failed = total_combinations - total_success
        
        print(f"Successful: {total_success}/{total_combinations}")
        print(f"Failed: {total_failed}/{total_combinations}")
        print("=" * 80)
    
    return results


if __name__ == "__main__":
    # When run directly, generate all heuristics
    results = generate_all_heuristics(verbose=True)
