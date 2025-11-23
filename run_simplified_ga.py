#!/usr/bin/env python3
"""
Simplified Genetic Algorithm Runner
Uses the new simplified fitness function for keyboard layout optimization
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.core.run_ga import run_genetic_algorithm
from src.config.config import Config

# ==================== CONFIGURATION PARAMETERS ====================
# Preview mode settings
PREVIEW_MODE = True          # Set to True to enable preview mode
PREVIEW_SIZE_MB = 1          # Size of preview chunk in MB
# =================================================================

def create_preview_dataset(dataset_name='simple_wikipedia', preview_size_mb=1):
    """Create a preview dataset by sampling from raw text file"""
    import random
    
    # Define paths
    raw_text_path = f"src/data/text/raw/{dataset_name}_dataset.txt"
    preview_path = f"src/data/text/raw/{dataset_name}_dataset_preview.txt"
    
    if not os.path.exists(raw_text_path):
        print(f"❌ Raw text file not found: {raw_text_path}")
        print("   Preview mode requires raw text file to exist")
        return dataset_name
    
    try:
        # Get file size and calculate target size
        file_size = os.path.getsize(raw_text_path)
        target_size = preview_size_mb * 1024 * 1024  # Convert MB to bytes
        
        print(f"📊 Creating preview dataset...")
        print(f"   Original file size: {file_size / (1024*1024):.1f} MB")
        print(f"   Preview size: {target_size / (1024*1024):.1f} MB")
        
        if target_size >= file_size:
            print("   File is smaller than preview size, using full file")
            return dataset_name
        
        # Sample random starting position
        max_start = file_size - target_size
        start_pos = random.randint(0, max_start)
        
        # Read preview chunk
        with open(raw_text_path, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(start_pos)
            preview_data = f.read(target_size)
        
        # Write preview file
        os.makedirs(os.path.dirname(preview_path), exist_ok=True)
        with open(preview_path, 'w', encoding='utf-8') as f:
            f.write(preview_data)
        
        print(f"✅ Preview dataset created: {preview_path}")
        print(f"   Preview size: {len(preview_data)} bytes")
        
        return dataset_name  # Return original dataset name, preview file will be used by typer
        
    except Exception as e:
        print(f"❌ Error creating preview dataset: {e}")
        return dataset_name

def run_simplified_ga():
    """Run GA with simplified fitness function"""
    
    # Configure for simplified evaluation
    Config.fitness.use_simplified_fitness = True
    Config.fitness.distance_weight = 0.5
    Config.fitness.time_weight = 0.5
    Config.cache.fitness_cache_enabled = True  # Enable fitness caching
    
    dataset_name = 'simple_wikipedia'
    
    if PREVIEW_MODE:
        print("🎬 PREVIEW MODE ENABLED")
        print(f"   Preview size: {PREVIEW_SIZE_MB} MB")
        dataset_name = create_preview_dataset('simple_wikipedia', PREVIEW_SIZE_MB)
        print(f"   Using dataset: {dataset_name}")
        print()
    
    print("SIMPLIFIED GENETIC ALGORITHM CONFIGURATION")
    print(f"Use simplified fitness: {Config.fitness.use_simplified_fitness}")
    print(f"Distance weight: {Config.fitness.distance_weight}")
    print(f"Time weight: {Config.fitness.time_weight}")
    print(f"Finger state persistence: {Config.fitness.finger_state_persistence}")
    print(f"Simulation window size: {Config.fitness.simulation_window_size}")
    print(f"Parallel typing enabled: {Config.fitness.parallel_typing_enabled}")
    print(f"Fitness caching enabled: {Config.cache.fitness_cache_enabled}")
    if PREVIEW_MODE:
        print(f"Preview mode enabled: {PREVIEW_MODE} ({PREVIEW_SIZE_MB}MB)")
    print()
    
    # Run GA with simplified parameters
    CONFIG = {
        'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
        'dataset_file': 'src/data/text/processed/frequency_analysis.pkl',
        'dataset_name': dataset_name,
        'population_size': 20,  # Much smaller for faster testing
        'max_iterations': 10,    # Fewer iterations
        'stagnant_limit': 3     # Lower stagnation limit
    }
    
    # Enable debug mode for simplified typer
    Config.debug = True
    
    print("Starting simplified GA optimization...")
    best = run_genetic_algorithm(**CONFIG)
    
    print(f"\nBest layout found: {best.name}")
    print(f"Fitness: {best.fitness:.6f}")
    
    # Cleanup preview file if created
    if PREVIEW_MODE:
        preview_path = f"src/data/text/raw/simple_wikipedia_dataset_preview.txt"
        if os.path.exists(preview_path):
            os.remove(preview_path)
            print(f"🧹 Cleaned up preview file: {preview_path}")

if __name__ == "__main__":
    run_simplified_ga()
