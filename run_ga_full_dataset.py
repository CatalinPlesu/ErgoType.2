#!/usr/bin/env python3

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.core.run_ga import run_genetic_algorithm
from src.config.config import Config

def run_ga_with_full_dataset():
    """Run GA with full dataset instead of preview"""
    
    print("SIMPLIFIED GENETIC ALGORITHM CONFIGURATION (FULL DATASET)")
    print(f"Use simplified fitness: True")
    print(f"Distance weight: 0.5")
    print(f"Time weight: 0.5")
    print(f"Finger state persistence: True")
    print(f"Simulation window size: 256")
    print(f"Parallel typing enabled: True")
    print(f"Fitness caching enabled: True")
    print(f"Using full dataset (no preview mode)")
    print()
    
    # Run GA with simplified parameters and full dataset
    CONFIG = {
        'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
        'dataset_file': 'src/data/text/processed/frequency_analysis.pkl',
        'dataset_name': 'simple_wikipedia',  # Using full dataset
        'population_size': 10,  # Small for testing
        'max_iterations': 3,    # Few iterations for testing
        'stagnant_limit': 2     # Lower stagnation limit
    }
    
    print("Starting simplified GA optimization with full dataset...")
    best = run_genetic_algorithm(**CONFIG)
    
    print(f"\nBest layout found: {best.name}")
    print(f"Fitness: {best.fitness:.6f}")
    
    return best

if __name__ == "__main__":
    best = run_ga_with_full_dataset()