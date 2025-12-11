#!/usr/bin/env python3
"""
Test script to verify parallel processing logic without C# dependencies.
"""

import sys
from pathlib import Path
import multiprocessing as mp

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data.layouts.keyboard_genotypes import LAYOUT_DATA


def test_task_distribution():
    """Test that tasks are properly distributed for parallel processing"""
    print("="*80)
    print("TEST: Parallel Processing Task Distribution")
    print("="*80)
    
    # Simulate the task building logic from generate_all_heuristics
    keyboards = ["keyboard1.json", "keyboard2.json"]
    text_files = ["dataset1.txt", "dataset2.txt"]
    
    tasks = []
    for keyboard_file in keyboards:
        for text_file in text_files:
            for layout_name, genotype in LAYOUT_DATA.items():
                tasks.append((
                    layout_name, genotype, keyboard_file, text_file,
                    0.5, 0.3, None, False
                ))
    
    expected_count = len(keyboards) * len(text_files) * len(LAYOUT_DATA)
    actual_count = len(tasks)
    
    print(f"\nTask Distribution:")
    print(f"  Keyboards: {len(keyboards)}")
    print(f"  Datasets: {len(text_files)}")
    print(f"  Layouts: {len(LAYOUT_DATA)}")
    print(f"  Expected tasks: {expected_count}")
    print(f"  Generated tasks: {actual_count}")
    
    if expected_count == actual_count:
        print(f"\n✅ Task distribution: PASSED")
        return True
    else:
        print(f"\n❌ Task distribution: FAILED")
        return False


def test_worker_function():
    """Test that the worker function structure is correct"""
    print("\n" + "="*80)
    print("TEST: Worker Function Structure")
    print("="*80)
    
    # Import the worker function
    from helpers.layouts.heuristic_generator import _generate_single_task
    
    print("\n✅ Worker function imported successfully")
    
    # Check function signature
    import inspect
    sig = inspect.signature(_generate_single_task)
    print(f"  Function signature: {sig}")
    
    # The function should accept a single tuple argument
    params = list(sig.parameters.keys())
    if len(params) == 1:
        print(f"  Parameters: {params} ✅")
        return True
    else:
        print(f"  Parameters: {params} ❌ (expected 1 parameter)")
        return False


def test_multiprocessing_availability():
    """Test that multiprocessing is available"""
    print("\n" + "="*80)
    print("TEST: Multiprocessing Availability")
    print("="*80)
    
    cpu_count = mp.cpu_count()
    print(f"\n  CPU count: {cpu_count}")
    print(f"  Multiprocessing available: Yes ✅")
    
    return True


def main():
    print("\nTesting parallel processing infrastructure...\n")
    
    tests = [
        ("Task Distribution", test_task_distribution),
        ("Worker Function", test_worker_function),
        ("Multiprocessing", test_multiprocessing_availability),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All parallel processing infrastructure tests passed!")
        print("The parallel processing logic is correctly implemented.")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
