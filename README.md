# ErgoType 2

Keyboard layout optimization using genetic algorithms with multi-layer support.

## How It Works

1. Read physical keyboard (with QWERTY on it)
2. Create a layout phenotype (with QWERTY)
3. Map a different layout in relationship with QWERTY
4. Create a symbol-key mapping (including multi-layer support)
5. Evaluate fitness function based on input data

## Features

- **Multi-Layer Support**: Optimize keyboards with multiple layers (e.g., Romanian with diacritics)
- **Genetic Algorithm**: Evolutionary optimization with crossover and mutation
- **Distributed Processing**: RabbitMQ-based distributed fitness evaluation
- **C# Fitness Library**: High-performance fitness calculation
- **Visualization**: Generate heatmaps and layout visualizations

## Multi-Layer Keyboard Support

The genetic algorithm now supports multi-layer keyboard layouts, enabling optimization of keyboards that use modifier keys (like AltGr) to access additional character sets.

**Key features:**
- Layer-to-layer crossover maintains layer hierarchy
- Per-layer mutation with layer importance weighting
- Dynamic layer addition/removal during evolution
- Configurable initial and maximum layer counts

See [docs/MULTI_LAYER_SUPPORT.md](docs/MULTI_LAYER_SUPPORT.md) for detailed documentation.

**Quick example:**
```python
from src.core.run_ga import run_genetic_algorithm

# Optimize Romanian layout with 2 layers
best = run_genetic_algorithm(
    keyboard_file='src/data/keyboards/ansi_60_percent.json',
    text_file='src/data/text/raw/romanian_dataset.txt',
    num_layers=2,      # Start with 2 layers
    max_layers=3       # Allow up to 3 layers
)
```

## Testing

Run the test suite:
```bash
# Run all tests
python3 -m pytest tests/

# Run multi-layer tests specifically
python3 tests/multi_layer_test.py
```
