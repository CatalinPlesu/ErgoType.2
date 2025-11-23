# Integration Example: Using Nim Text Processor in GA Fitness Calculation

import sys
import os
import time

# Add nim directory to path
sys.path.insert(0, '/home/catalin/dev/ergotype.2/nim')

def integrate_nim_processor():
    """Example of integrating Nim text processor into the existing GA workflow"""
    
    try:
        from nim_wrapper import NimTextProcessor
        print("✓ Nim wrapper imported successfully")
    except ImportError:
        print("✗ Nim wrapper not available")
        return
    
    # Initialize processor
    processor = NimTextProcessor()
    
    # Get layout statistics
    stats = processor.get_layout_stats()
    print(f"Layout stats: {stats}")
    
    # Test with sample text (similar to what simplified_typer.py does)
    sample_text = "the quick brown fox jumps over the lazy dog" * 1000
    
    # Time the Nim implementation
    start_time = time.time()
    nim_result = processor.process_text(sample_text)
    nim_time = time.time() - start_time
    
    print(f"\nNim Results:")
    print(f"  Processing time: {nim_time:.4f}s")
    print(f"  Characters: {nim_result['char_count']}")
    print(f"  Typed: {nim_result['typed_chars']}")
    print(f"  Speed: {nim_result['chars_per_second']:.1f} chars/sec")
    print(f"  Distance: {nim_result['total_distance']:.1f} mm")
    print(f"  Time: {nim_result['total_time']:.1f} ms")
    
    # Compare with original Python implementation
    print(f"\n" + "="*50)
    print("COMPARISON WITH ORIGINAL PYTHON IMPLEMENTATION")
    print("="*50)
    
    try:
        # Simulate the original simplified_typer.py approach
        from minimal_text_processor import SimplifiedTextProcessor, load_minimal_layout_from_keyboard
        
        layout = load_minimal_layout_from_keyboard("/home/catalin/dev/ergotype.2/src/data/keyboards/ansi_60_percent.json")
        original_processor = SimplifiedTextProcessor(layout)
        
        start_time = time.time()
        original_result = original_processor.process_text(sample_text)
        original_time = time.time() - start_time
        
        print(f"Python Results:")
        print(f"  Processing time: {original_time:.4f}s")
        print(f"  Characters: {original_result['char_count']}")
        print(f"  Typed: {original_result['typed_chars']}")
        print(f"  Speed: {original_result['chars_per_second']:.1f} chars/sec")
        print(f"  Distance: {original_result['total_distance']:.1f} mm")
        print(f"  Time: {original_result['total_time']:.1f} ms")
        
        # Calculate improvement
        if nim_time > 0:
            speedup = original_time / nim_time
            print(f"\nPerformance Improvement:")
            print(f"  Speedup: {speedup:.2f}x")
            print(f"  Time saved: {original_time - nim_time:.4f}s ({(original_time - nim_time)/original_time*100:.1f}%)")
        
        # Verify results are similar
        dist_diff = abs(nim_result['total_distance'] - original_result['total_distance'])
        dist_pct = dist_diff / max(original_result['total_distance'], 1) * 100
        print(f"  Distance difference: {dist_pct:.2f}% (should be < 1%)")
        
    except Exception as e:
        print(f"Error comparing with Python: {e}")

def fitness_function_integration_example():
    """Example of how to integrate Nim processor into fitness calculation"""
    
    print(f"\n" + "="*50)
    print("FITNESS CALCULATION INTEGRATION EXAMPLE")
    print("="*50)
    
    try:
        from nim_wrapper import NimTextProcessor
        
        processor = NimTextProcessor()
        
        # Simulate fitness calculation workflow from simplified_typer.py
        def calculate_fitness_with_nim(layout_name='simple_wikipedia', preview_mode=True, max_chars=100000):
            """Fitness calculation using Nim processor"""
            
            # Determine file path (like in simplified_typer.py lines 420-428)
            base_path = "/home/catalin/dev/ergotype.2/src/data/text/raw/"
            preview_file = f"{base_path}{layout_name}_dataset_preview.txt"
            full_file = f"{base_path}{layout_name}_dataset.txt"
            
            # Choose file (like lines 424-429)
            if os.path.exists(preview_file) and preview_mode:
                text_file = preview_file
                data_size = "preview"
            elif os.path.exists(full_file):
                text_file = full_file
                data_size = "full"
            else:
                # Fallback to simple calculation
                return {
                    'fitness': 1.0,  # Default fitness
                    'distance': 100.0,
                    'time': 50.0,
                    'calculation_time': 0.001
                }
            
            # Process with Nim (replacing lines 453-465)
            result = processor.process_file(text_file, preview_mode, max_chars)
            
            # Normalize and calculate fitness (like lines 510-536)
            # Use baseline normalization for simplicity
            baseline_distance = 400.0  # mm
            baseline_time = 50.0       # seconds
            
            normalized_distance = min(result['total_distance'] / baseline_distance, 1.0)
            normalized_time = min(result['total_time'] / baseline_time, 1.0)
            
            # Apply sickness function, then invert to get fitness (line 535-536)
            distance_weight = 0.5  # Config.fitness.distance_weight
            time_weight = 0.5      # Config.fitness.time_weight
            
            sickness_score = (distance_weight * normalized_distance + 
                           time_weight * normalized_time)
            fitness_score = 1.0 - sickness_score  # Invert to get fitness
            
            return {
                'fitness': fitness_score,
                'sickness': sickness_score,  # Also return sickness for debugging
                'distance': result['total_distance'],
                'time': result['total_time'],
                'calculation_time': result['processing_time'],
                'coverage': result['coverage'],
                'data_size': data_size
            }
        
        # Test the integration
        print("Testing fitness calculation integration...")
        
        start_time = time.time()
        fitness_result = calculate_fitness_with_nim('simple_wikipedia', preview_mode=True, max_chars=50000)
        total_time = time.time() - start_time
        
        print(f"Fitness calculation results:")
        print(f"  Fitness score: {fitness_result['fitness']:.6f}")
        print(f"  Distance: {fitness_result['distance']:.1f} mm")
        print(f"  Time: {fitness_result['time']:.1f} ms")
        print(f"  Calculation time: {fitness_result['calculation_time']:.4f}s")
        print(f"  Total time (including file selection): {total_time:.4f}s")
        print(f"  Coverage: {fitness_result['coverage']:.2f}%")
        print(f"  Data size: {fitness_result['data_size']}")
        
        print(f"\nThis demonstrates how the Nim processor can replace the")
        print(f"character-by-character processing in simplified_typer.py")
        print(f"while maintaining compatibility with the existing fitness workflow.")
        
    except Exception as e:
        print(f"Error in fitness integration: {e}")

if __name__ == "__main__":
    print("Nim Text Processor Integration Demo")
    print("="*50)
    
    integrate_nim_processor()
    fitness_function_integration_example()
    
    print(f"\n" + "="*50)
    print("INTEGRATION SUMMARY")
    print("="*50)
    print("The Nim text processor provides:")
    print("• Faster text processing for fitness calculations")
    print("• Drop-in replacement for simplified_typer.py")
    print("• Minimal data structures for efficiency")
    print("• Python integration via nimpy")
    print("• Compatible output format for GA workflow")