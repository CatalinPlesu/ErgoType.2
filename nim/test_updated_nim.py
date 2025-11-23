#!/usr/bin/env python3
"""
Test script for updated Nim text processor
"""

import os
import sys
import time

# Add the nim directory to Python path
sys.path.insert(0, '/home/catalin/dev/ergotype.2/nim')

def test_nim_compilation():
    """Test if Nim code compiles successfully"""
    print("Testing Nim compilation...")
    
    os.chdir('/home/catalin/dev/ergotype.2/nim')
    
    # Test main Nim file
    print("1. Testing main Nim file...")
    result = os.system("nim c --out:text_processor_test text_processor.nim")
    if result == 0:
        print("✓ Main Nim file compiles successfully")
    else:
        print("✗ Main Nim file compilation failed")
        return False
    
    # Test library file
    print("2. Testing Nim library file...")
    result = os.system("nim py --lib --out:text_processor_lib_test.so text_processor_lib_working.nim")
    if result == 0:
        print("✓ Nim library file compiles successfully")
    else:
        print("✗ Nim library file compilation failed")
        return False
    
    return True

def test_python_wrapper():
    """Test Python wrapper functionality"""
    print("\nTesting Python wrapper...")
    
    try:
        from nim_wrapper import NimTextProcessor
        processor = NimTextProcessor(debug=True)
        print("✓ NimTextProcessor created successfully")
        
        # Test layout stats
        stats = processor.get_layout_stats()
        print(f"✓ Layout stats: {stats}")
        
        # Test character typability
        for char in "abcdef":
            result = processor.is_character_typable(char)
            print(f"✓ Character '{char}' typable: {result}")
        
        # Test simple text processing
        sample_text = "hello world"
        result = processor.process_text(sample_text)
        print(f"✓ Text processing result: {result}")
        
        # Test fitness calculation
        dist, time_val = processor.fitness(sample_text)
        print(f"✓ Fitness calculation: distance={dist:.4f}, time={time_val:.4f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Python wrapper test failed: {e}")
        return False

def test_performance():
    """Test performance comparison"""
    print("\nTesting performance...")
    
    try:
        from nim_wrapper import benchmark_comparison
        
        # Create a test file
        test_content = "the quick brown fox jumps over the lazy dog\n" * 1000
        test_file = "/tmp/test_text.txt"
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        print(f"Created test file: {test_file}")
        
        # Run benchmark
        benchmark_comparison(test_file, preview_mode=True, max_chars=50000)
        
        # Clean up
        os.remove(test_file)
        print("✓ Performance test completed")
        
        return True
        
    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Nim Text Processor Test Suite")
    print("=" * 40)
    
    all_passed = True
    
    # Test 1: Compilation
    if not test_nim_compilation():
        all_passed = False
    
    # Test 2: Python wrapper
    if not test_python_wrapper():
        all_passed = False
    
    # Test 3: Performance
    if not test_performance():
        all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)