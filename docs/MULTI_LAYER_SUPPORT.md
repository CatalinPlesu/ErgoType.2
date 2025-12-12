# Multi-Layer Keyboard Layout Support

## Overview

The genetic algorithm now supports multi-layer keyboard layouts, enabling optimization of keyboards that use modifier keys (like AltGr) to access additional character sets. This is particularly useful for:

- **Romanian keyboards** with diacritics (ă, â, î, ș, ț) on a second layer
- **Multi-language keyboards** with Latin and non-Latin characters
- **Programming-optimized layouts** with symbols on dedicated layers
- **Any keyboard design** that requires more characters than available physical keys

## Key Concepts

### Chromosome Representation

**Before (Single Layer):**
```python
chromosome = ['a', 'b', 'c', 'd', 'e', ...]  # Flat list of characters
```

**After (Multi-Layer):**
```python
chromosome = [
    ['a', 'b', 'c', 'd', 'e', ...],  # Layer 0 (base layer)
    ['ă', 'â', 'î', 'ș', 'ț', ...],  # Layer 1 (AltGr layer)
    ['@', '#', '$', '%', '^', ...],  # Layer 2 (additional layer)
]
```

### Layer Hierarchy

- **Layer 0 (Base Layer)**: Most frequently used characters
  - Always present, never removed
  - Gets more conservative mutations (50% of normal mutation rate)
  - Should contain the most common characters in the language

- **Layer 1+**: Less frequently used characters
  - Accessed via modifier keys (AltGr, Fn, etc.)
  - Can be added or removed during evolution
  - Standard mutation rate applied

## Configuration

### Basic Usage

```python
from core.run_ga import run_genetic_algorithm

# Single-layer layout (default)
best = run_genetic_algorithm(
    keyboard_file='src/data/keyboards/ansi_60_percent.json',
    text_file='src/data/text/raw/simple_wikipedia_dataset.txt',
    population_size=30,
    num_layers=1,      # Start with 1 layer
    max_layers=1       # Don't allow layer growth
)

# Multi-layer layout (Romanian with diacritics)
best = run_genetic_algorithm(
    keyboard_file='src/data/keyboards/ansi_60_percent.json',
    text_file='src/data/text/raw/romanian_dataset.txt',
    population_size=30,
    num_layers=2,      # Start with 2 layers
    max_layers=3       # Allow up to 3 layers
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `num_layers` | int | 1 | Initial number of layers for chromosomes |
| `max_layers` | int | 3 | Maximum layers allowed during evolution |

## Genetic Operations

### Initialization

When creating the initial population:
1. Heuristic layouts (QWERTY, Dvorak, etc.) get their genotype as layer 0
2. Additional layers (if `num_layers > 1`) are created as shuffled copies
3. Random individuals get random permutations for each layer

### Crossover

**Layer-to-layer crossover** maintains the layer structure:
- Each layer crosses over with the corresponding layer from the parent
- Layer 0 with Layer 0, Layer 1 with Layer 1, etc.
- Uniform crossover algorithm applied independently to each layer
- Ensures no duplicate genes within each layer

### Mutation

**Per-layer mutation** with special handling:
- Base layer (layer 0): 50% of normal mutation rate
- Other layers: Standard mutation rate
- Swap mutation within each layer independently

**Layer addition mutation** (1% probability):
- Adds a new layer if under `max_layers`
- New layer is a shuffled copy of base layer
- Allows GA to discover that additional layers are beneficial

**Layer removal mutation** (1% probability):
- Removes a random layer (never base layer)
- Only if more than 1 layer present
- Allows GA to prune underutilized layers

## Output Format

### Console Output

```
BEST INDIVIDUAL FOUND
====================
Name: gen_5-42
Fitness: 0.123456
Raw Distance: 1234.56
Raw Time: 567.89
Layers: 2
Layer 0: qwfpgjluy;[]arsndhoeit'zxcbvkm,./`1234567890-=\
Layer 1: ăâîșț[]{};:'"\|<>?~!@#$%^&*()_+
====================
```

### JSON Output

```json
{
  "best_individual": {
    "id": 42,
    "name": "gen_5-42",
    "fitness": 0.123456,
    "chromosome": [
      "qwfpgjluy;[]arsndhoeit'zxcbvkm,./`1234567890-=\\",
      "ăâîșț[]{};:'\"\\|<>?~!@#$%^&*()_+"
    ],
    "num_layers": 2,
    "generation": 5
  }
}
```

## Examples

### Example 1: English Single-Layer Optimization

```python
# Optimize a standard English layout
from core.run_ga import run_genetic_algorithm

best = run_genetic_algorithm(
    keyboard_file='src/data/keyboards/ansi_60_percent.json',
    text_file='src/data/text/raw/simple_wikipedia_dataset.txt',
    population_size=50,
    max_iterations=100,
    stagnant_limit=15,
    num_layers=1,      # Single layer only
    max_layers=1       # No layer growth
)
```

### Example 2: Romanian Two-Layer Optimization

```python
# Optimize Romanian layout with diacritics on second layer
from core.run_ga import run_genetic_algorithm

best = run_genetic_algorithm(
    keyboard_file='src/data/keyboards/ansi_60_percent.json',
    text_file='src/data/text/raw/romanian_dataset.txt',
    population_size=50,
    max_iterations=100,
    stagnant_limit=15,
    num_layers=2,      # Start with 2 layers
    max_layers=2       # Keep 2 layers fixed
)
```

### Example 3: Dynamic Layer Evolution

```python
# Let the GA discover optimal number of layers
from core.run_ga import run_genetic_algorithm

best = run_genetic_algorithm(
    keyboard_file='src/data/keyboards/ansi_60_percent.json',
    text_file='src/data/text/raw/multilingual_dataset.txt',
    population_size=50,
    max_iterations=100,
    stagnant_limit=15,
    num_layers=1,      # Start with 1 layer
    max_layers=4       # Allow up to 4 layers
)
# GA will add/remove layers based on fitness
```

## Implementation Details

### Backwards Compatibility

The implementation maintains backwards compatibility with single-layer layouts:
- Single-layer chromosomes are automatically wrapped in a list internally
- Existing code that assumes flat lists will work with `individual.chromosome[0]`
- All serialization handles both formats

### Current Limitations

1. **Fitness Evaluation**: Currently only uses base layer (layer 0) for remapping
   - Multi-layer layout remapping is not yet implemented in `Layout.remap()`
   - Fitness calculation doesn't account for layer-switching costs
   - This will be addressed in future updates

2. **Visualization**: Layer-specific visualizations are not yet implemented
   - Only base layer is visualized
   - Per-layer heatmaps are planned

3. **Character Mapping**: Manual layer assignment required
   - Automatic character-to-layer assignment not implemented
   - Characters should be manually assigned to appropriate layers based on frequency

## Testing

Run the multi-layer tests:

```bash
python3 tests/multi_layer_test.py
```

Tests cover:
- Single and multi-layer Individual creation
- Crossover with single and multi-layer chromosomes
- Mutation operations
- Layer addition and removal
- Serialization/deserialization

## Future Enhancements

### Planned Features

1. **Smart Character Assignment**
   - Automatic assignment of characters to layers based on frequency
   - Characters used more often go to base layer

2. **Layer-Switching Cost Model**
   - Account for the time cost of pressing modifier keys
   - Optimize for minimizing layer switches

3. **Full Multi-Layer Layout Support**
   - Update `Layout.remap()` to handle all layers
   - Update character mapping generation for multi-layer
   - Update fitness calculation to include layer-switching costs

4. **Per-Layer Visualizations**
   - Generate separate heatmaps for each layer
   - Visual representation of layer utilization

5. **Layer Usage Statistics**
   - Track how often each layer is accessed
   - Identify underutilized layers for removal

## Contributing

When working with multi-layer support:

1. Always use `len(individual.chromosome)` to get layer count
2. Access layers with `individual.chromosome[layer_idx]`
3. Use `individual.get_layer(idx)` for safe layer access
4. Test with both single and multi-layer chromosomes
5. Ensure serialization preserves layer structure

## References

- Issue: [Multi-Layer Keyboard Layout Support for Genetic Algorithm](#)
- Test Suite: `tests/multi_layer_test.py`
- Core Implementation: `src/core/ga.py`
- Output Handling: `src/core/run_ga.py`
