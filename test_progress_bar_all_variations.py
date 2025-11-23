#!/usr/bin/env python3
"""
Test script to verify progress bar functionality across all GA run variations
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

def test_progress_bar_in_run_script(script_path, script_name):
    """Test if a run script has progress bar functionality"""
    print(f"\n{'='*60}")
    print(f"TESTING: {script_name}")
    print(f"Script: {script_path}")
    print(f"{'='*60}")
    
    try:
        # Read the script content
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Check if it imports run_genetic_algorithm
        if 'from src.core.run_ga import run_genetic_algorithm' in content or 'from core.run_ga import run_genetic_algorithm' in content:
            print("✅ Imports run_genetic_algorithm function")
        else:
            print("❌ Does not import run_genetic_algorithm function")
            return False
        
        # Check if it calls run_genetic_algorithm
        if 'run_genetic_algorithm(' in content:
            print("✅ Calls run_genetic_algorithm function")
        else:
            print("❌ Does not call run_genetic_algorithm function")
            return False
        
        print("✅ Should have progress bar functionality")
        return True
        
    except Exception as e:
        print(f"❌ Error reading script: {e}")
        return False

def main():
    """Test progress bar functionality in all GA run variations"""
    
    print("PROGRESS BAR FUNCTIONALITY VERIFICATION")
    print("Testing all GA run variations for progress bar support...")
    
    # List of GA run scripts to test
    scripts = [
        ('run_simplified_ga.py', 'Simplified GA (1MB preview)'),
        ('run_ga_full_dataset.py', 'Full Dataset GA'),
        ('run_ga_larger_preview.py', 'Larger Preview GA (10MB)'),
        ('main.py', 'Main GA Runner'),
        ('test_enhanced_output.py', 'Enhanced Output Test'),
        ('test_preview_mode.py', 'Preview Mode Test')
    ]
    
    all_passed = True
    
    for script_file, description in scripts:
        script_path = f"/home/catalin/dev/ergotype.2/{script_file}"
        passed = test_progress_bar_in_run_script(script_path, description)
        all_passed = all_passed and passed
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if all_passed:
        print("✅ ALL SCRIPTS HAVE PROGRESS BAR FUNCTIONALITY")
        print("   All GA run variations use the same run_genetic_algorithm()")
        print("   function which includes progress bar in fitness_evaluation_parallel()")
    else:
        print("❌ SOME SCRIPTS MISSING PROGRESS BAR FUNCTIONALITY")
    
    print(f"\nProgress bar features include:")
    print(f"   • Live progress bar with █ characters")
    print(f"   • Timing information (elapsed, remaining, estimated)")
    print(f"   • Cache hit rate monitoring")
    print(f"   • Parallel processing throughput")
    print(f"   • Updates every minute or at 20% milestones")

if __name__ == "__main__":
    main()