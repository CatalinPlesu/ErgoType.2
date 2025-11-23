#!/usr/bin/env python3
"""
Test script for enhanced output structure
"""
import sys
import os
sys.path.insert(0, '/home/catalin/dev/ergotype.2')

from src.core.run_ga import run_genetic_algorithm
from pathlib import Path
import json

def test_enhanced_output():
    """Test the enhanced output structure"""
    print("Testing Enhanced Output Structure...")
    
    # Run a quick test with minimal parameters
    try:
        best = run_genetic_algorithm(
            keyboard_file='src/data/keyboards/ansi_60_percent.json',
            dataset_file='src/data/text/processed/frequency_analysis.pkl',
            dataset_name='newsgroup',
            population_size=5,  # Very small for quick test
            max_iterations=1,   # Just one iteration
            stagnant_limit=1
        )
        
        print("✅ Enhanced output structure test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_output()
    sys.exit(0 if success else 1)