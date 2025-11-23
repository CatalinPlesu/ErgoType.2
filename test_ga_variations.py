#!/usr/bin/env python3
"""
Test script to verify all three GA variations are working
"""

import sys
import os

# Add paths
sys.path.insert(0, '/home/catalin/dev/ergotype.2')
sys.path.insert(0, '/home/catalin/dev/ergotype.2/src')

def test_frequency_based():
    """Test frequency-based GA"""
    print("Testing Frequency-Based GA...")
    try:
        from main import item_run_frequency_based_ga
        title = item_run_frequency_based_ga(True)
        print(f"✓ Frequency-based GA: {title}")
        return True
    except Exception as e:
        print(f"✗ Frequency-based GA error: {e}")
        return False

def test_raw_text():
    """Test raw text-based GA"""
    print("Testing Raw Text-Based GA...")
    try:
        from main import item_run_raw_text_ga
        title = item_run_raw_text_ga(True)
        print(f"✓ Raw text GA: {title}")
        
        # Test the actual function import
        from run_ga_raw_text import run_ga_with_raw_text
        print("✓ Raw text GA function imported")
        return True
    except Exception as e:
        print(f"✗ Raw text GA error: {e}")
        return False

def test_nim_based():
    """Test Nim-based GA"""
    print("Testing Nim-Based GA...")
    try:
        from main import item_run_nim_ga
        title = item_run_nim_ga(True)
        print(f"✓ Nim-based GA: {title}")
        
        # Test the actual function import
        from run_ga_nim import run_ga_with_nim_processor
        print("✓ Nim GA function imported")
        
        # Test Nim wrapper import
        sys.path.insert(0, '/home/catalin/dev/ergotype.2/nim')
        from nim_wrapper import NimTextProcessor
        print("✓ Nim wrapper imported")
        
        # Test Nim processor creation
        processor = NimTextProcessor()
        print("✓ Nim processor created")
        
        return True
    except Exception as e:
        print(f"✗ Nim-based GA error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_menu_registration():
    """Test that all menu items are properly registered"""
    print("Testing Menu Registration...")
    try:
        from main import Menu, item_run_frequency_based_ga, item_run_raw_text_ga, item_run_nim_ga
        
        menu = Menu("Test Menu")
        menu.add_item(item_run_frequency_based_ga)
        menu.add_item(item_run_raw_text_ga) 
        menu.add_item(item_run_nim_ga)
        
        print(f"✓ Menu created with {len(menu.items)} new GA variations")
        print("✓ Menu items:")
        for i, item in enumerate(menu.items):
            print(f"  {i+1}. {item(True)}")
        
        return True
    except Exception as e:
        print(f"✗ Menu registration error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("GA VARIATIONS INTEGRATION TEST")
    print("=" * 50)
    
    tests = [
        ("Frequency-Based GA", test_frequency_based),
        ("Raw Text-Based GA", test_raw_text),
        ("Nim-Based GA", test_nim_based),
        ("Menu Registration", test_menu_registration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{test_name:25} {status}")
        all_passed = all_passed and success
    
    print()
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("All three GA variations are ready to use.")
        print("\nTo run the system:")
        print("  python3 main.py")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)