# Simplified Keyboard Layout Evaluation

This repository now includes a simplified evaluation workflow for keyboard layout optimization with the following key features:

## Simplified Fitness Function

The new fitness function uses a straightforward formula:
```
fitness = weight1 * normalized_distance + weight2 * normalized_time
```

### Key Components:

1. **Distance Calculation**:
   - Simulates typing in a 256-character sliding window
   - Finger state is preserved within the window (not guaranteed to return to home row)
   - More realistic simulation of actual typing patterns

2. **Time Calculation**:
   - Based on Fitts' Law: `MT = a + b * log2(D + 1)`
   - Incorporates finger strength factors for different fingers
   - Accounts for finger-specific typing speed differences

3. **Parallel Typing**:
   - Allows parallel finger movements for faster typing
   - Movements end synchronously for even finger usage distribution
   - Better models real-world typing where fingers can move simultaneously

## Configuration

The simplified evaluation is controlled by parameters in `src/config/config.py`:

```python
class FitnessConfig:
    use_simplified_fitness = True  # Enable simplified evaluation
    distance_weight = 0.5          # Weight for distance component
    time_weight = 0.5             # Weight for time component
    simulation_window_size = 256  # Character window size
    finger_state_persistence = True  # Keep finger state in window
    parallel_typing_enabled = True   # Allow parallel movements
    synchronous_end = True        # Synchronous movement endings
```

## Finger Strength Parameters

Different fingers have different typing speeds:
- Index fingers: Fastest (factor = 1.0)
- Middle fingers: Slightly slower (factor = 1.2)
- Ring fingers: Slower (factor = 1.5)
- Pinky fingers: Slowest (factor = 1.8)
- Thumbs: Medium speed (factor = 1.3)

## Usage

### Run Simplified GA
```bash
python run_simplified_ga.py
```

### Test Simplified Evaluation
```bash
python test_simplified_evaluation.py
```

### Run Full GA with Simplified Fitness
```bash
python -c "
from src.config.config import Config
Config.fitness.use_simplified_fitness = True
from src.core.run_ga import run_genetic_algorithm
run_genetic_algorithm(population_size=50, max_iterations=100)
"
```

## Output

The simplified evaluation produces:

1. **Fitness Scores**: Combined distance and time metrics
2. **SVG Heatmaps**: Keyboard layouts with frequency-based heatmaps
3. **Finger Statistics**: Usage distribution across fingers
4. **Layout Comparisons**: Rankings against standard layouts

## Files Created

- `output/ga_results/`: GA optimization results with top 3 layouts
- `layouts_comparison/`: Predefined layouts for visual comparison
- SVG files with heatmaps showing character frequency usage
- JSON files with detailed layout and fitness data

## Benefits

1. **Simpler**: Reduced complexity compared to multi-component fitness functions
2. **More Realistic**: Better models actual typing behavior
3. **Parallel Processing**: Accounts for simultaneous finger movements
4. **Finger-Specific**: Different finger capabilities are considered
5. **Window-Based**: More realistic simulation of typing patterns

The simplified approach focuses on the two most important aspects of typing ergonomics: physical effort (distance) and time efficiency, while providing a more accurate model of real-world typing behavior.