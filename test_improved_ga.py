#!/usr/bin/env python3
"""
Test the improved progress display and simplified fitness
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.config.config import Config
from run_simplified_ga import run_simplified_ga

def test_improved_ga():
    """Test the improved GA with progress display"""
    
    print("🧪 Testing Improved GA Progress Display")
    print("=" * 50)
    
    # Enable simplified fitness and caching
    Config.fitness.use_simplified_fitness = True
    Config.cache.fitness_cache_enabled = True
    
    # Set preview mode for faster testing
    print("🎬 Enabling preview mode for faster testing...")
    
    # Temporarily modify the constants in the file
    original_file = "run_simplified_ga.py"
    
    try:
        # Read the file
        with open(original_file, 'r') as f:
            content = f.read()
        
        # Modify preview settings
        content = content.replace("PREVIEW_MODE = False", "PREVIEW_MODE = True")
        content = content.replace("PREVIEW_SIZE_MB = 1", "PREVIEW_SIZE_MB = 0.1")  # Smaller for testing
        
        # Write modified version
        with open(original_file, 'w') as f:
            f.write(content)
        
        print("✅ Preview mode enabled (0.1MB sample)")
        
        # Run the GA
        print("\n🚀 Starting GA with improved progress display...")
        run_simplified_ga()
        
    finally:
        # Restore original file
        content = content.replace("PREVIEW_MODE = True", "PREVIEW_MODE = False")
        content = content.replace("PREVIEW_SIZE_MB = 0.1", "PREVIEW_SIZE_MB = 1")
        
        with open(original_file, 'w') as f:
            f.write(content)
        
        print("\n✅ Original settings restored")

if __name__ == "__main__":
    test_improved_ga()