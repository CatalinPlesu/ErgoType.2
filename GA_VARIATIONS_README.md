# Keyboard Layout Optimization - GA Variations

This system now provides **3 distinct Genetic Algorithm variations** for keyboard layout optimization, each using different approaches for fitness calculation.

## Menu Options

### 1. Frequency-Based GA
**Menu Item**: "Run GA - Frequency Based"

- **Approach**: Uses pre-processed frequency analysis data
- **Data Source**: `src/data/text/processed/frequency_analysis.pkl`
- **Method**: Statistical analysis of character/word frequencies
- **Performance**: Fast evaluation, good for initial exploration
- **Best For**: Quick optimization with statistical accuracy

**Characteristics**:
- Pre-computed frequency tables
- Efficient fitness calculation
- Stable results across runs
- Lower memory usage

### 2. Raw Text-Based GA  
**Menu Item**: "Run GA - Raw Text Based"

- **Approach**: Processes raw text files directly
- **Data Source**: `src/data/text/raw/*.txt` files
- **Method**: Character-by-character text processing
- **Performance**: Moderate speed, high accuracy
- **Best For**: Real-world text analysis

**Characteristics**:
- Processes actual text content
- More accurate for specific datasets
- Handles text variations well
- Requires raw text files

### 3. Nim Library-Based GA
**Menu Item**: "Run GA - Nim Library Based"

- **Approach**: Uses compiled Nim library for text processing
- **Data Source**: Raw text files with Nim optimization
- **Method**: High-performance compiled code
- **Performance**: Fastest evaluation speed
- **Best For**: Large-scale optimization

**Characteristics**:
- Compiled Nim code for speed
- Drop-in replacement for Python processing
- Significant performance improvements
- Requires Nim compilation

## Technical Implementation

### Core Components

1. **Frequency-Based**: `src/core/run_ga.py` with frequency data
2. **Raw Text-Based**: `run_ga_raw_text.py` with direct text processing  
3. **Nim-Based**: `run_ga_nim.py` with Nim library integration

### Configuration

All variations use the same core configuration:
- Keyboard layout: `src/data/keyboards/ansi_60_percent.json`
- Fitness weights: 0.5 distance, 0.5 time
- Population size: 15-30 (depending on variation)
- Progress bar: Available in all variations
- Fitness caching: Enabled where applicable

### Performance Comparison

| Variation | Speed | Accuracy | Memory | Setup |
|-----------|--------|----------|---------|-------|
| Frequency | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Raw Text | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Nim | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

## Usage

### Running the System

```bash
python3 main.py
```

### Menu Navigation

1. Use **UP/DOWN** arrow keys to navigate
2. Press **ENTER** to select an option
3. Press **ESC** or **Ctrl+C** to exit

### Recommended Workflow

1. **Start with Frequency-Based** for quick exploration
2. **Use Raw Text-Based** for specific dataset optimization  
3. **Use Nim-Based** for final high-performance optimization

## File Structure

```
/home/catalin/dev/ergotype.2/
├── main.py                    # Main menu system
├── run_ga_raw_text.py         # Raw text GA implementation
├── run_ga_nim.py             # Nim library GA implementation
├── src/core/run_ga.py        # Core GA (used by frequency-based)
├── nim/                      # Nim library source code
│   ├── nim_wrapper.py        # Python-Nim interface
│   ├── text_processor_lib_working.nim  # Compiled Nim library
│   └── integration_example.py # Integration examples
└── src/data/text/            # Text data directory
    ├── raw/                  # Raw text files
    └── processed/            # Frequency analysis data
```

## Requirements

### Core Requirements
- Python 3.8+
- All existing Python dependencies

### Nim Requirements (for Nim variation)
- Nim compiler
- nimpy library: `pip install nimpy`
- Compiled Nim library: `nim py --lib nim/text_processor_lib_working.nim`

### Data Requirements
- Raw text files in `src/data/text/raw/`
- Frequency analysis in `src/data/text/processed/`

## Output Structure

All variations create organized output in:
```
output/ga_results/ga_run_YYYY-MM-DD--HH:MM:SS/
├── ga_run_metadata.json
├── predefined_layouts/
├── winning_layouts/
└── discarded_layouts/
```

## Troubleshooting

### Nim Library Issues
- Ensure Nim is installed and compiled
- Check `nim/nim_wrapper.py` for import errors
- Verify `text_processor_lib_working.nim` compiles

### Data File Issues
- Check `src/data/text/raw/` for required text files
- Verify `src/data/text/processed/frequency_analysis.pkl` exists
- Ensure proper file permissions

### Performance Issues
- Use smaller population sizes for testing
- Enable preview mode for large datasets
- Monitor memory usage with large text files

## Development Notes

The system maintains backward compatibility while adding new variations. Each variation can be run independently and produces comparable results with different performance characteristics.