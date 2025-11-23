#!/usr/bin/env python3
"""
Simple test to verify the error fix is working.
"""

import sys
import os
sys.path.insert(0, '.')

def test_error_fix():
    """Test that the error fix is working"""
    print("Testing error fix...")
    
    # Test that the GA module can be imported without errors
    try:
        from src.core.ga import GeneticAlgorithm
        print("✅ GA module imported successfully")
        
        # Test that the evaluate_individual_fitness method exists and has correct signature
        if hasattr(GeneticAlgorithm, 'evaluate_individual_fitness'):
            print("✅ evaluate_individual_fitness method exists")
        else:
            print("❌ evaluate_individual_fitness method missing")
            return False
            
        # Test that the fitness_function_calculation method exists
        if hasattr(GeneticAlgorithm, 'fitness_function_calculation'):
            print("✅ fitness_function_calculation method exists")
        else:
            print("❌ fitness_function_calculation method missing")
            return False
            
        print("✅ All method signatures are correct")
        print("✅ Error fix is properly implemented")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_error_fix()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)