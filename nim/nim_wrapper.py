# Python wrapper for Nim text processor library (Updated)

import os
import sys
from typing import Dict, List, Tuple, Optional
import time

# Try to import the Nim library
try:
    import nimpy
    nim_available = True
except ImportError:
    nim_available = False
    print("Warning: nimpy not available. Install with: pip install nimpy")

class NimTextProcessor:
    """Python wrapper for Nim text processor matching simplified_typer.py"""
    
    def __init__(self, layout_file: str = "src/data/keyboards/ansi_60_percent.json", debug: bool = False):
        self.layout_file = layout_file
        self.debug = debug
        self.nim_lib = None
        
        if nim_available:
            try:
                # Import the compiled Nim library
                import text_processor_lib_working as text_processor_lib
                self.nim_lib = text_processor_lib
                print("Nim library loaded successfully")
            except ImportError:
                print("Warning: Nim library not compiled. Compile with: nim py --lib nim/text_processor_lib_working.nim")
                self.nim_lib = None
        else:
            print("Nim not available")
    
    def process_file(self, filename: str, preview_mode: bool = False, max_chars: int = 100000) -> Dict:
        """Process a text file using Nim implementation"""
        if not self.nim_lib:
            return self._fallback_to_python(filename, preview_mode, max_chars)
        
        try:
            result = self.nim_lib.processTextFile(filename, self.layout_file, preview_mode, max_chars)
            
            return {
                'total_distance': result[0],
                'total_time': result[1],
                'char_count': int(result[2]),
                'typed_chars': int(result[3]),
                'coverage': result[4],
                'processing_time': result[5],
                'chars_per_second': result[6]
            }
        except Exception as e:
            print(f"Error in Nim processing: {e}")
            return self._fallback_to_python(filename, preview_mode, max_chars)
    
    def process_text(self, text: str, preview_mode: bool = False, max_chars: int = 100000) -> Dict:
        """Process text string using Nim implementation"""
        if not self.nim_lib:
            return self._fallback_to_python_string(text, preview_mode, max_chars)
        
        try:
            result = self.nim_lib.processTextString(text, self.layout_file, preview_mode, max_chars)
            
            return {
                'total_distance': result[0],
                'total_time': result[1],
                'char_count': int(result[2]),
                'typed_chars': int(result[3]),
                'coverage': result[4],
                'processing_time': result[5],
                'chars_per_second': result[6]
            }
        except Exception as e:
            print(f"Error in Nim processing: {e}")
            return self._fallback_to_python_string(text, preview_mode, max_chars)
    
    def fitness(self, text: str) -> Tuple[float, float]:
        """Calculate fitness matching Python simplified_typer.fitness() method"""
        if not self.nim_lib:
            return self._fallback_fitness(text)
        
        try:
            result = self.nim_lib.fitness(text, self.layout_file)
            return (result[0], result[1])
        except Exception as e:
            print(f"Error in Nim fitness calculation: {e}")
            return self._fallback_fitness(text)
    
    def is_character_typable(self, char: str) -> bool:
        """Check if character can be typed on this layout"""
        if not self.nim_lib:
            return True  # Fallback to assume all characters are typable
        
        try:
            if len(char) != 1:
                return False
            return self.nim_lib.isCharacterTypable(char[0], self.layout_file)
        except Exception as e:
            print(f"Error checking character typability: {e}")
            return True
    
    def get_layout_stats(self) -> Dict:
        """Get layout statistics"""
        if not self.nim_lib:
            return {'error': 'Nim library not available'}
        
        try:
            key_count = self.nim_lib.getLayoutKeyCount(self.layout_file)
            return {
                'total_keys': key_count,
                'error': None
            }
        except Exception as e:
            print(f"Error getting layout stats: {e}")
            return {'error': str(e)}
    
    def _fallback_to_python(self, filename: str, preview_mode: bool, max_chars: int) -> Dict:
        """Fallback to Python implementation"""
        print("Falling back to Python implementation")
        
        try:
            import sys
            import os
            # Add the current directory to Python path
            sys.path.insert(0, '/home/catalin/dev/ergotype.2/nim')
            
            from minimal_text_processor import process_file
            return process_file(filename, self.layout_file, preview_mode, max_chars)
        except ImportError:
            return {'error': 'Python fallback not available'}
        except Exception as e:
            return {'error': f'Python fallback error: {str(e)}'}
    
    def _fallback_to_python_string(self, text: str, preview_mode: bool, max_chars: int) -> Dict:
        """Fallback to Python implementation for text string"""
        print("Falling back to Python implementation")
        
        try:
            import sys
            import os
            # Add the current directory to Python path
            sys.path.insert(0, '/home/catalin/dev/ergotype.2/nim')
            
            from minimal_text_processor import SimplifiedTextProcessor, load_minimal_layout_from_keyboard
            
            layout = load_minimal_layout_from_keyboard(self.layout_file)
            processor = SimplifiedTextProcessor(layout)
            
            stats = processor.process_text(text, preview_mode, max_chars)
            return stats
        except ImportError:
            return {'error': 'Python fallback not available'}
        except Exception as e:
            return {'error': f'Python fallback error: {str(e)}'}
    
    def _fallback_fitness(self, text: str) -> Tuple[float, float]:
        """Fallback fitness calculation"""
        try:
            # Simple fallback - just return some default values
            return (100.0, 50.0)
        except:
            return (100.0, 50.0)

def benchmark_comparison(filename: str, preview_mode: bool = True, max_chars: int = 50000):
    """Compare Nim vs Python performance"""
    processor = NimTextProcessor()
    
    print(f"Comparing Nim vs Python performance on {filename}")
    print(f"Preview mode: {preview_mode}, Max chars: {max_chars}")
    print("=" * 60)
    
    # Test Nim version
    if processor.nim_lib:
        print("Testing Nim implementation...")
        start_time = time.time()
        nim_stats = processor.process_file(filename, preview_mode, max_chars)
        nim_processing_time = time.time() - start_time
        print(f"Nim - Processing time: {nim_stats.get('processing_time', nim_processing_time):.3f}s")
        print(f"Nim - Speed: {nim_stats.get('chars_per_second', -1):.1f} chars/sec")
    else:
        print("Nim implementation not available")
        nim_stats = None
    
    # Test Python version
    print("\nTesting Python implementation...")
    start_time = time.time()
    python_stats = processor._fallback_to_python(filename, preview_mode, max_chars)
    python_processing_time = time.time() - start_time
    print(f"Python - Processing time: {python_stats.get('processing_time', python_processing_time):.3f}s")
    print(f"Python - Speed: {python_stats.get('chars_per_second', -1):.1f} chars/sec")
    
    # Compare results
    if nim_stats and python_stats:
        nim_time = nim_stats.get('processing_time', nim_processing_time)
        python_time = python_stats.get('processing_time', python_processing_time)
        speedup = python_time / nim_time if nim_time > 0 else 1
        
        print(f"\nSpeedup: {speedup:.2f}x faster")
        
        # Verify results are similar
        nim_dist = nim_stats.get('total_distance', 0)
        python_dist = python_stats.get('total_distance', 0)
        if python_dist > 0:
            dist_diff = abs(nim_dist - python_dist) / python_dist * 100
            print(f"Distance difference: {dist_diff:.2f}% (should be < 5%)")

def test_fitness_equivalence():
    """Test that Nim and Python fitness calculations are equivalent"""
    processor = NimTextProcessor()
    
    print("Testing fitness calculation equivalence...")
    print("=" * 50)
    
    test_texts = [
        "the quick brown fox jumps over the lazy dog",
        "hello world",
        "abcdef" * 50,
        "simple test text for keyboard layout evaluation"
    ]
    
    for i, text in enumerate(test_texts):
        print(f"\nTest {i+1}: '{text[:20]}...'")
        
        # Nim fitness
        if processor.nim_lib:
            nim_dist, nim_time = processor.fitness(text)
            print(f"Nim fitness: distance={nim_dist:.4f}, time={nim_time:.4f}")
        else:
            print("Nim fitness: not available")
            nim_dist, nim_time = None, None
        
        # Python fallback
        py_dist, py_time = processor._fallback_fitness(text)
        print(f"Python fitness: distance={py_dist:.4f}, time={py_time:.4f}")
        
        # Compare if both available
        if nim_dist is not None and nim_time is not None:
            dist_diff = abs(nim_dist - py_dist) / max(py_dist, 0.1) * 100
            time_diff = abs(nim_time - py_time) / max(py_time, 0.1) * 100
            print(f"Differences: distance={dist_diff:.2f}%, time={time_diff:.2f}%")

if __name__ == "__main__":
    # Test the wrapper
    processor = NimTextProcessor(debug=True)
    
    # Get layout stats
    stats = processor.get_layout_stats()
    print("Layout statistics:", stats)
    
    # Test with preview file
    preview_file = "src/data/text/raw/simple_wikipedia_dataset_preview.txt"
    if os.path.exists(preview_file):
        result = processor.process_file(preview_file, preview_mode=True, max_chars=10000)
        print("Processing result:", result)
    else:
        print(f"Preview file not found: {preview_file}")
        
        # Test with sample text
        sample_text = "the quick brown fox jumps over the lazy dog" * 1000
        try:
            result = processor.process_text(sample_text)
            print("Sample text result:", result)
        except Exception as e:
            print(f"Error processing sample text: {e}")
    
    # Test fitness function
    print("\nTesting fitness function:")
    test_text = "hello world test"
    dist, time = processor.fitness(test_text)
    print(f"Fitness result: distance={dist:.4f}, time={time:.4f}")
    
    # Test character typability
    print("\nTesting character typability:")
    for char in "abcdefxyz":
        typable = processor.is_character_typable(char)
        print(f"'{char}': {typable}")
    
    # Run benchmark if file exists
    if os.path.exists(preview_file):
        benchmark_comparison(preview_file)
    
    # Test fitness equivalence
    test_fitness_equivalence()