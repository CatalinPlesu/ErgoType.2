#!/usr/bin/env python3

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.core.run_ga import run_genetic_algorithm
from src.config.config import Config

def run_ga_with_larger_preview():
    """Run GA with larger preview to test layout differentiation"""
    
    # Create larger preview
    import random
    
    dataset_name = 'simple_wikipedia'
    preview_size_mb = 10  # 10MB instead of 1MB
    
    # Create preview dataset
    raw_text_path = f"src/data/text/raw/{dataset_name}_dataset.txt"
    preview_path = f"src/data/text/raw/{dataset_name}_dataset_preview.txt"
    
    if os.path.exists(raw_text_path):
        print(f"🎬 CREATING LARGER PREVIEW MODE")
        print(f"   Preview size: {preview_size_mb} MB")
        
        try:
            # Get file size and calculate target size
            file_size = os.path.getsize(raw_text_path)
            target_size = preview_size_mb * 1024 * 1024  # Convert MB to bytes
            
            print(f"📊 Creating {preview_size_mb}MB preview dataset...")
            print(f"   Original file size: {file_size / (1024*1024):.1f} MB")
            
            if target_size < file_size:
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
                
                print(f"✅ {preview_size_mb}MB preview dataset created")
                print(f"   Preview size: {len(preview_data)} bytes")
            else:
                print("   File is smaller than preview size, using full file")
        except Exception as e:
            print(f"❌ Error creating preview dataset: {e}")
    
    print()
    print("SIMPLIFIED GENETIC ALGORITHM CONFIGURATION (LARGER PREVIEW)")
    print(f"Use simplified fitness: True")
    print(f"Distance weight: 0.5")
    print(f"Time weight: 0.5")
    print(f"Simulation window size: 256")
    print(f"Parallel typing enabled: True")
    print(f"Fitness caching enabled: True")
    print(f"Preview mode enabled: True ({preview_size_mb}MB)")
    print()
    
    # Configure for simplified evaluation
    Config.fitness.use_simplified_fitness = True
    Config.fitness.distance_weight = 0.5
    Config.fitness.time_weight = 0.5
    Config.cache.fitness_cache_enabled = True
    
    # Run GA with simplified parameters
    CONFIG = {
        'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
        'dataset_file': 'src/data/text/processed/frequency_analysis.pkl',
        'dataset_name': dataset_name,
        'population_size': 10,  # Small for testing
        'max_iterations': 3,    # Few iterations for testing
        'stagnant_limit': 2     # Lower stagnation limit
    }
    
    print("Starting simplified GA optimization with larger preview...")
    best = run_genetic_algorithm(**CONFIG)
    
    print(f"\nBest layout found: {best.name}")
    print(f"Fitness: {best.fitness:.6f}")
    
    # Cleanup preview file
    if os.path.exists(preview_path):
        os.remove(preview_path)
        print(f"🧹 Cleaned up preview file: {preview_path}")
    
    return best

if __name__ == "__main__":
    best = run_ga_with_larger_preview()