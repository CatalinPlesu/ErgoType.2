#!/usr/bin/env python3
"""
Test script for parallel heuristic generation.
"""

import sys
from pathlib import Path
import time
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from helpers.layouts.heuristic_generator import generate_all_heuristics


def test_parallel_generation():
    """Test parallel generation with multiple workers"""
    print("="*80)
    print("TEST: Parallel Heuristic Generation")
    print("="*80)
    
    # Setup
    keyboard_file = "src/data/keyboards/ansi_60_percent.json"
    text_file = "src/data/text/raw/test_dataset.txt"
    
    # Clean up any existing cache
    cache_dir = Path("output/test_dataset/ansi_60_percent")
    if cache_dir.exists():
        print(f"\nCleaning up existing cache: {cache_dir}")
        shutil.rmtree(cache_dir)
    
    print(f"\nTest Configuration:")
    print(f"  Keyboard: ansi_60_percent")
    print(f"  Dataset: test_dataset")
    print(f"  Workers: 2")
    
    # Test with 2 workers
    print("\n" + "-"*80)
    print("Running parallel generation with 2 workers...")
    print("-"*80)
    
    start_time = time.time()
    
    results = generate_all_heuristics(
        keyboards=[keyboard_file],
        text_files=[text_file],
        force_regenerate=True,
        verbose=True,
        max_workers=2
    )
    
    elapsed_time = time.time() - start_time
    
    # Verify results
    from data.layouts.keyboard_genotypes import LAYOUT_DATA
    total_layouts = len(LAYOUT_DATA)
    
    success_count = sum(
        1 for ds in results.get('ansi_60_percent', {}).values()
        for success in ds.values() if success
    )
    
    print("\n" + "="*80)
    if success_count == total_layouts:
        print(f"✅ TEST PASSED")
        print(f"   Generated: {success_count}/{total_layouts} layouts")
        print(f"   Time: {elapsed_time:.2f} seconds")
        print(f"   Workers: 2 (parallel)")
        return True
    else:
        print(f"❌ TEST FAILED")
        print(f"   Generated: {success_count}/{total_layouts} layouts")
        return False


def main():
    try:
        success = test_parallel_generation()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
