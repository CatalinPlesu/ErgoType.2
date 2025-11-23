#!/usr/bin/env python3
"""
Raw Text-based GA Runner
Uses raw text files directly for fitness calculation without frequency analysis
"""

import sys
import os
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.core.run_ga import run_genetic_algorithm
from src.config.config import Config

def run_ga_with_raw_text():
    """Run GA using raw text files for fitness calculation"""
    
    print("RAW TEXT-BASED GENETIC ALGORITHM")
    print("=" * 60)
    print("Using raw text files directly for fitness calculation")
    print("without frequency analysis preprocessing.")
    print()
    
    # Configure for raw text evaluation
    Config.fitness.use_simplified_fitness = True
    Config.fitness.distance_weight = 0.5
    Config.fitness.time_weight = 0.5
    Config.cache.fitness_cache_enabled = True
    
    # Test available datasets
    base_path = "src/data/text/raw/"
    available_datasets = []
    
    datasets_to_check = [
        'simple_wikipedia',
        'cartigratis', 
        'newsgroup'
    ]
    
    print("Checking available raw text datasets:")
    for dataset in datasets_to_check:
        preview_file = f"{base_path}{dataset}_dataset_preview.txt"
        full_file = f"{base_path}{dataset}_dataset.txt"
        
        if os.path.exists(preview_file):
            available_datasets.append(dataset)
            print(f"  ✓ {dataset} (preview available)")
        elif os.path.exists(full_file):
            available_datasets.append(dataset)
            print(f"  ✓ {dataset} (full dataset available)")
        else:
            print(f"  ✗ {dataset} (not found)")
    
    if not available_datasets:
        print("\n❌ No datasets found. Please ensure raw text files exist.")
        print("Expected files:")
        for dataset in datasets_to_check:
            print(f"  - {base_path}{dataset}_dataset.txt")
            print(f"  - {base_path}{dataset}_dataset_preview.txt")
        return None
    
    dataset_name = available_datasets[0]  # Use first available dataset
    
    print(f"\nUsing dataset: {dataset_name}")
    print()
    
    print("CONFIGURATION:")
    print(f"  Fitness function: Simplified (raw text)")
    print(f"  Distance weight: {Config.fitness.distance_weight}")
    print(f"  Time weight: {Config.fitness.time_weight}")
    print(f"  Dataset: {dataset_name} (raw text)")
    print(f"  Fitness caching: {Config.cache.fitness_cache_enabled}")
    print(f"  Parallel processing: 8 processes")
    print()
    
    # Run GA with raw text configuration
    CONFIG = {
        'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
        'dataset_file': 'src/data/text/processed/frequency_analysis.pkl',  # Still needed for some GA functions
        'dataset_name': dataset_name,
        'population_size': 20,
        'max_iterations': 8,
        'stagnant_limit': 3
    }
    
    print("Starting Genetic Algorithm with raw text processing...")
    best = run_genetic_algorithm(**CONFIG)
    
    print(f"\nBest layout found: {best.name}")
    print(f"Fitness: {best.fitness:.6f}")
    print(f"Dataset used: {dataset_name} (raw text)")
    
    return best

if __name__ == "__main__":
    best = run_ga_with_raw_text()