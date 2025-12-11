#!/usr/bin/env python3
"""
Test script for heuristic caching functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from helpers.layouts.heuristic_generator import (
    generate_heuristic_layout,
    check_heuristic_cached,
    get_dataset_name,
    get_keyboard_name,
    get_heuristic_cache_path
)
from data.layouts.keyboard_genotypes import LAYOUT_DATA


def test_cache_structure():
    """Test the cache path structure"""
    print("="*80)
    print("TEST 1: Cache Path Structure")
    print("="*80)
    
    dataset_name = "test_dataset"
    keyboard_name = "ansi_60_percent"
    layout_name = "qwerty"
    
    for heatmap_type in ['press_heatmap', 'hover_heatmap', 'layout']:
        cache_path = get_heuristic_cache_path(
            dataset_name, keyboard_name, layout_name, heatmap_type
        )
        print(f"{heatmap_type}: {cache_path}")
    
    print("✅ Cache structure test passed\n")
    return True


def test_generate_single_heuristic():
    """Test generating a single heuristic layout"""
    print("="*80)
    print("TEST 2: Generate Single Heuristic")
    print("="*80)
    
    keyboard_file = "src/data/keyboards/ansi_60_percent.json"
    text_file = "src/data/text/raw/test_dataset.txt"
    layout_name = "qwerty"
    genotype = LAYOUT_DATA["qwerty"]
    
    print(f"Keyboard: {keyboard_file}")
    print(f"Dataset: {text_file}")
    print(f"Layout: {layout_name}")
    print()
    
    # Test generation
    success, message = generate_heuristic_layout(
        layout_name=layout_name,
        genotype=genotype,
        keyboard_file=keyboard_file,
        text_file=text_file,
        force_regenerate=True
    )
    
    if success:
        print(f"✅ {message}")
        
        # Verify files were created
        dataset_name = get_dataset_name(text_file)
        keyboard_name = get_keyboard_name(keyboard_file)
        
        for heatmap_type in ['press_heatmap', 'hover_heatmap', 'layout']:
            cache_path = get_heuristic_cache_path(
                dataset_name, keyboard_name, layout_name, heatmap_type
            )
            if cache_path.exists():
                print(f"  ✓ Created: {cache_path.name}")
            else:
                print(f"  ✗ Missing: {cache_path.name}")
                return False
        
        print("✅ Single heuristic generation test passed\n")
        return True
    else:
        print(f"❌ {message}")
        return False


def test_cache_detection():
    """Test cache detection"""
    print("="*80)
    print("TEST 3: Cache Detection")
    print("="*80)
    
    keyboard_file = "src/data/keyboards/ansi_60_percent.json"
    text_file = "src/data/text/raw/test_dataset.txt"
    
    dataset_name = get_dataset_name(text_file)
    keyboard_name = get_keyboard_name(keyboard_file)
    
    # Should be cached from previous test
    layout_name = "qwerty"
    is_cached = check_heuristic_cached(dataset_name, keyboard_name, layout_name)
    
    if is_cached:
        print(f"✅ Cache detected for {layout_name}")
        print("✅ Cache detection test passed\n")
        return True
    else:
        print(f"❌ Cache not detected for {layout_name}")
        return False


def test_skip_cached():
    """Test that cached heuristics are skipped"""
    print("="*80)
    print("TEST 4: Skip Cached Heuristics")
    print("="*80)
    
    keyboard_file = "src/data/keyboards/ansi_60_percent.json"
    text_file = "src/data/text/raw/test_dataset.txt"
    layout_name = "qwerty"
    genotype = LAYOUT_DATA["qwerty"]
    
    # Try to generate again without force_regenerate
    success, message = generate_heuristic_layout(
        layout_name=layout_name,
        genotype=genotype,
        keyboard_file=keyboard_file,
        text_file=text_file,
        force_regenerate=False
    )
    
    if success and "Already cached" in message:
        print(f"✅ {message}")
        print("✅ Skip cached test passed\n")
        return True
    else:
        print(f"❌ Expected 'Already cached' message, got: {message}")
        return False


def main():
    print("\n" + "="*80)
    print("HEURISTIC CACHING SYSTEM TESTS")
    print("="*80 + "\n")
    
    tests = [
        test_cache_structure,
        test_generate_single_heuristic,
        test_cache_detection,
        test_skip_cached
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))
    
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
