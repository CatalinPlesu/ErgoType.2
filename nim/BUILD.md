# Build instructions for Nim text processor

This directory contains a minimal Nim port of the performance-critical text processing code from the Python simplified typer.

## Files

- `text_processor.nim` - Main Nim implementation with core algorithms
- `text_processor_lib.nim` - Nim library interface for Python integration
- `minimal_python_structures.py` - Minimal Python data structures (reference)
- `minimal_text_processor.py` - Python test implementation 
- `nim_wrapper.py` - Python wrapper for Nim library
- `README.md` - Documentation

## Performance Comparison

The Python implementation processes text at ~500,000 characters/second. The Nim version should be significantly faster due to:

1. **Compiled execution** - No Python interpreter overhead
2. **Native data structures** - No object overhead
3. **Optimized loops** - Direct memory access
4. **Minimal allocations** - Stack-based operations

## Building the Nim Library

### 1. Install Nim
```bash
# Ubuntu/Debian
sudo apt-get install nim

# Or from https://nim-lang.org/install.html
```

### 2. Install nimpy for Python integration
```bash
pip install nimpy
```

### 3. Compile the library
```bash
cd nim
nim py --lib text_processor_lib.nim
```

This creates a Python-importable library that can be used from the wrapper.

### 4. Test the implementation
```bash
python3 nim_wrapper.py
```

## Usage

### Direct Nim usage:
```nim
import text_processor

let layout = loadLayoutFromJson("src/data/keyboards/ansi_60_percent.json")
var processor = initTextProcessor(layout, 0.0, 150.0)

let (dist, time, charCount, typedChars, coverage, procTime, speed) = 
  processor.processText("your text here")
```

### Python integration:
```python
from nim_wrapper import NimTextProcessor

processor = NimTextProcessor()
result = processor.process_file("text_file.txt", preview_mode=True, max_chars=100000)
print(f"Speed: {result['chars_per_second']:.1f} chars/sec")
```

## Minimal Data Structures

The Nim implementation uses minimal structures:

```nim
type
  KeyData = object
    id, finger: int
    char: char
    x, y: float
    
  FingerState = object
    fingerId, homingKeyId, currentKeyId: int
    totalDistance, totalTime: float
    keyCount: int
```

This avoids the complexity of the full Python keyboard/layout system while maintaining the core functionality needed for text processing and fitness calculation.

## Integration Points

The Nim code can be integrated into the existing Python workflow:

1. **File processing** - Replace `calculate_distance_and_time_from_raw_text()` 
2. **Preview mode** - Use for quick fitness estimation
3. **Batch processing** - Process large text files efficiently
4. **Real-time feedback** - Fast calculation during GA evolution

## Performance Targets

Expected improvements over Python:
- **2-5x faster** for text processing
- **Lower memory usage** due to minimal structures  
- **Better scalability** for large text files
- **Reduced GC pressure** from fewer allocations