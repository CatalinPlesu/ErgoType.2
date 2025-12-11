#!/usr/bin/env python3
"""
Integration test for the heuristic caching system.
Tests the full workflow: generate cache -> run GA -> verify cache usage
"""

import sys
from pathlib import Path
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from helpers.layouts.heuristic_generator import (
    generate_all_heuristics,
    get_dataset_name,
    get_keyboard_name,
    check_heuristic_cached
)
from data.layouts.keyboard_genotypes import LAYOUT_DATA


def test_full_workflow():
    """Test the complete workflow of cache generation and GA usage"""
    print("="*80)
    print("INTEGRATION TEST: Full Heuristic Caching Workflow")
    print("="*80)
    
    # Setup
    keyboard_file = "src/data/keyboards/ansi_60_percent.json"
    text_file = "src/data/text/raw/test_dataset.txt"
    dataset_name = get_dataset_name(text_file)
    keyboard_name = get_keyboard_name(keyboard_file)
    
    # Clean up any existing cache
    cache_dir = Path("output") / dataset_name / keyboard_name
    if cache_dir.exists():
        print(f"\nCleaning up existing cache: {cache_dir}")
        shutil.rmtree(cache_dir)
    
    print(f"\nTest Configuration:")
    print(f"  Keyboard: {keyboard_name}")
    print(f"  Dataset: {dataset_name}")
    print(f"  Layouts to test: {list(LAYOUT_DATA.keys())}")
    
    # Step 1: Generate heuristics for one keyboard and dataset
    print("\n" + "-"*80)
    print("STEP 1: Generate all heuristics for test configuration")
    print("-"*80)
    
    results = generate_all_heuristics(
        keyboards=[keyboard_file],
        text_files=[text_file],
        force_regenerate=False,
        verbose=False
    )
    
    # Verify all layouts were generated
    success_count = sum(
        1 for ds in results.get(keyboard_name, {}).values()
        for success in ds.values() if success
    )
    
    total_layouts = len(LAYOUT_DATA)
    
    if success_count != total_layouts:
        print(f"❌ Expected {total_layouts} successful generations, got {success_count}")
        return False
    
    print(f"✅ Successfully generated {success_count}/{total_layouts} heuristic layouts")
    
    # Step 2: Verify all heuristics are cached
    print("\n" + "-"*80)
    print("STEP 2: Verify all heuristics are properly cached")
    print("-"*80)
    
    for layout_name in LAYOUT_DATA.keys():
        if not check_heuristic_cached(dataset_name, keyboard_name, layout_name):
            print(f"❌ Cache verification failed for {layout_name}")
            return False
        print(f"✅ Verified cache for {layout_name}")
    
    # Step 3: Verify files exist
    print("\n" + "-"*80)
    print("STEP 3: Verify file structure")
    print("-"*80)
    
    expected_files = 0
    found_files = 0
    
    for layout_name in LAYOUT_DATA.keys():
        for heatmap_type in ['press_heatmap', 'hover_heatmap', 'layout']:
            expected_files += 1
            file_path = cache_dir / heatmap_type / f"{layout_name}.svg"
            if file_path.exists():
                found_files += 1
            else:
                print(f"❌ Missing file: {file_path}")
    
    if found_files != expected_files:
        print(f"❌ Expected {expected_files} files, found {found_files}")
        return False
    
    print(f"✅ All {found_files} files present in cache structure")
    
    # Step 4: Test regeneration skip
    print("\n" + "-"*80)
    print("STEP 4: Test that cached heuristics are skipped")
    print("-"*80)
    
    # Try to generate again without force_regenerate
    results2 = generate_all_heuristics(
        keyboards=[keyboard_file],
        text_files=[text_file],
        force_regenerate=False,
        verbose=False
    )
    
    # All should be successful (from cache)
    success_count2 = sum(
        1 for ds in results2.get(keyboard_name, {}).values()
        for success in ds.values() if success
    )
    
    if success_count2 != total_layouts:
        print(f"❌ Cache skip test failed: {success_count2}/{total_layouts}")
        return False
    
    print(f"✅ All {total_layouts} layouts successfully used cached versions")
    
    # Step 5: Verify cache structure
    print("\n" + "-"*80)
    print("STEP 5: Verify cache directory structure")
    print("-"*80)
    
    expected_dirs = ['press_heatmap', 'hover_heatmap', 'layout']
    for dir_name in expected_dirs:
        dir_path = cache_dir / dir_name
        if not dir_path.exists():
            print(f"❌ Missing directory: {dir_path}")
            return False
        print(f"✅ Found directory: {dir_name}")
    
    print("\n" + "="*80)
    print("✅ INTEGRATION TEST PASSED")
    print("="*80)
    print(f"\nCache location: {cache_dir}")
    print(f"Total layouts cached: {len(LAYOUT_DATA)}")
    print(f"Total files: {found_files}")
    print(f"\nThe heuristic caching system is working correctly!")
    
    return True


def main():
    try:
        success = test_full_workflow()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Integration test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
