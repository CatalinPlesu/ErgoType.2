#!/usr/bin/env python3
"""
Test script for population phases feature
"""

import sys
from pathlib import Path

# Add src to import path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.run_ga import run_genetic_algorithm

def test_standard_mode():
    """Test standard mode (backward compatibility)"""
    print("\n" + "="*80)
    print("TEST 1: Standard Mode")
    print("="*80)
    
    CONFIG = {
        'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
        'text_file': 'src/data/text/raw/simple_wikipedia_dataset.txt',
        'population_size': 5,
        'max_iterations': 3,
        'stagnant_limit': 2,
        'max_concurrent_processes': 2,
        'fitts_a': 0.5,
        'fitts_b': 0.3,
        'use_rabbitmq': False,  # Use in-memory queue for testing
        'save_heuristics': False,
        'population_phases': None
    }
    
    try:
        best = run_genetic_algorithm(**CONFIG)
        print(f"\n✅ Standard mode test passed")
        print(f"   Best fitness: {best.fitness:.6f}")
        return True
    except Exception as e:
        print(f"\n❌ Standard mode test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_population_phases_mode():
    """Test population phases mode"""
    print("\n" + "="*80)
    print("TEST 2: Population Phases Mode")
    print("="*80)
    
    # Example: shake things up
    # Start with 2 iterations of 5 population
    # Expand to 1 iteration of 10 population
    # Back to 2 iterations of 5 population
    population_phases = [
        (2, 5),   # 2 iterations, max pop 5
        (1, 10),  # 1 iteration, max pop 10 (expansion)
        (2, 5)    # 2 iterations, max pop 5 (contraction)
    ]
    
    CONFIG = {
        'keyboard_file': 'src/data/keyboards/ansi_60_percent.json',
        'text_file': 'src/data/text/raw/simple_wikipedia_dataset.txt',
        'stagnant_limit': 10,  # High enough to let all phases run
        'max_concurrent_processes': 2,
        'fitts_a': 0.5,
        'fitts_b': 0.3,
        'use_rabbitmq': False,  # Use in-memory queue for testing
        'save_heuristics': False,
        'population_phases': population_phases,
        'population_size': 5,  # For compatibility
        'max_iterations': 5    # For compatibility
    }
    
    try:
        best = run_genetic_algorithm(**CONFIG)
        print(f"\n✅ Population phases mode test passed")
        print(f"   Best fitness: {best.fitness:.6f}")
        return True
    except Exception as e:
        print(f"\n❌ Population phases mode test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metadata_saving():
    """Test that metadata is saved correctly for both modes"""
    import json
    from pathlib import Path
    
    print("\n" + "="*80)
    print("TEST 3: Metadata Saving")
    print("="*80)
    
    # Find the most recent GA run
    output_dir = Path("output/ga_results")
    if not output_dir.exists():
        print("❌ No output directory found")
        return False
    
    run_dirs = sorted([d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith("ga_run_")], reverse=True)
    
    if not run_dirs:
        print("❌ No GA run directories found")
        return False
    
    # Check the most recent run
    latest_run = run_dirs[0]
    metadata_file = latest_run / "ga_run_metadata.json"
    
    if not metadata_file.exists():
        print(f"❌ Metadata file not found: {metadata_file}")
        return False
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    print(f"\n📄 Latest run: {latest_run.name}")
    print(f"   Mode: {metadata.get('mode', 'unknown')}")
    
    if metadata.get('mode') == 'population_phases':
        print(f"   Population phases: {metadata.get('population_phases')}")
        print(f"   Total max iterations: {metadata.get('total_max_iterations')}")
        print(f"   Average population: {metadata.get('average_population')}")
    else:
        print(f"   Population size: {metadata.get('population_size')}")
        print(f"   Max iterations: {metadata.get('max_iterations')}")
    
    print(f"   Actual iterations: {metadata.get('actual_iterations', 'N/A')}")
    print(f"   Best fitness: {metadata.get('best_fitness')}")
    
    print(f"\n✅ Metadata saving test passed")
    return True

if __name__ == "__main__":
    print("\n" + "="*80)
    print("POPULATION PHASES FEATURE TEST SUITE")
    print("="*80)
    
    results = []
    
    # Test 1: Standard mode (backward compatibility)
    results.append(("Standard Mode", test_standard_mode()))
    
    # Test 2: Population phases mode
    results.append(("Population Phases Mode", test_population_phases_mode()))
    
    # Test 3: Metadata saving
    results.append(("Metadata Saving", test_metadata_saving()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("="*80)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
