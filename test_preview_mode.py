#!/usr/bin/env python3
"""
Test preview mode functionality
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.core.run_ga import run_genetic_algorithm
from src.config.config import Config
from run_simplified_ga import create_preview_dataset

def test_preview_mode():
    """Test preview mode with different sample sizes"""
    
    print("🎬 Testing Preview Mode")
    print("=" * 40)
    
    # Test different preview sizes
    test_sizes = [0.5, 1, 2]  # MB
    
    for size in test_sizes:
        print(f"\n📊 Testing {size}MB preview...")
        
        # Create preview dataset
        dataset_name = create_preview_dataset('simple_wikipedia', size)
        
        if dataset_name.endswith('_preview'):
            print(f"✅ Preview dataset created: {dataset_name}")
            
            # Quick test with small population
            Config.fitness.use_simplified_fitness = True
            Config.fitness.distance_weight = 0.5
            Config.fitness.time_weight = 0.5
            Config.cache.fitness_cache_enabled = True
            
            try:
                # Run a very small test
                CONFIG = {
                    'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
                    'dataset_file': 'src/data/text/processed/frequency_analysis.pkl',
                    'dataset_name': dataset_name,
                    'population_size': 3,  # Very small for testing
                    'max_iterations': 1,   # Just one iteration
                    'stagnant_limit': 1
                }
                
                print(f"   Running quick test with {CONFIG['population_size']} individuals...")
                best = run_genetic_algorithm(**CONFIG)
                print(f"   ✅ Test completed: Best fitness = {best.fitness:.6f}")
                
                # Cleanup preview file
                preview_path = f"src/data/text/raw/simple_wikipedia_dataset_preview.txt"
                if os.path.exists(preview_path):
                    os.remove(preview_path)
                    print(f"   🧹 Cleaned up: {preview_path}")
                    
            except Exception as e:
                print(f"   ❌ Test failed: {e}")
        else:
            print(f"⚠️  Could not create preview dataset")
            break
    
    print(f"\n🎉 Preview mode testing completed!")
    print(f"💡 Preview mode helps prevent overfitting by using different")
    print(f"   random samples from the full dataset for each optimization run.")

if __name__ == "__main__":
    test_preview_mode()