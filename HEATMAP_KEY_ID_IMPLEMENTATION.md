# Heatmap Implementation with Key ID Support

## Overview

This document describes the implementation of proper press and hover heatmap visualization with key ID support, allowing accurate reconstruction of keyboard information from C# ComputeStats output.

## Problem Statement

Previously, the heatmap visualization relied on character-to-key mapping through the layout system, which could lead to ambiguity about which physical keys were being used. The issue requested:

1. Pass key_id to the C# library to enable easy reconstruction of keyboard info from ComputeStats
2. Update heatmap rendering to include legend/keycaps to verify the correct keyboard layout is applied

## Solution Architecture

### 1. Data Flow

```
Python (Layout) → JSON Config → C# Library → Stats JSON → Python (Visualization)
                  with key_id             with key_id
```

### 2. Key Changes

#### A. Python JSON Exporter (`src/core/map_json_exporter.py`)

**Modified:** `_get_key_position()` method

```python
def _get_key_position(self, key_id, prefer_finger=None):
    """Get key center position as (x, y) with key_id."""
    key = self.keyboard.keys[key_id]
    center = key.get_key_center_position()
    return {
        "x": float(center[0]),
        "y": float(center[1]),
        "finger": self._get_finger_int(key_id, prefer_finger),
        "key_id": key_id  # ← NEW: Include key_id
    }
```

#### B. C# Library (`cs/Class.cs`)

**Modified:** `KeyPress` record and JSON parsing

```csharp
// OLD: public record KeyPress(Point Position, int Finger);
// NEW:
public record KeyPress(Point Position, int Finger, int KeyId);
```

**Modified:** JSON output in `ComputeStats()`

```csharp
keyPressesArray.Add(new Dictionary<string, object>
{
    ["x"] = kp.Position.X,
    ["y"] = kp.Position.Y,
    ["finger"] = kp.Finger,
    ["key_id"] = kp.KeyId  // ← NEW: Include key_id in output
});
```

#### C. Python Visualization (`src/helpers/layouts/visualization.py`)

**Modified:** `generate_all_visualizations()`

Extracts key_id from stats and builds frequency mappings:

```python
# Build key_id-based frequency mappings
key_id_to_press_freq = {}
key_id_to_hover_freq = {}

for char, char_data in char_mappings.items():
    key_presses = char_data.get('key_presses', [])
    if key_presses:
        # Last key press is the actual character key (modifiers come first)
        char_key_id = key_presses[-1].get('key_id', None)
        
        if char_key_id is not None:
            # Accumulate frequencies by key_id
            key_id_to_press_freq[char_key_id] = ...
            key_id_to_hover_freq[char_key_id] = ...
```

**Modified:** `render_keyboard_heatmap()`

Added parameter and logic to use key_id-based frequency lookup:

```python
def render_keyboard_heatmap(
    keyboard: Keyboard,
    char_frequencies: Dict,
    layer_idx: int = 0,
    layout=None,
    heatmap_type: str = "press",
    exclude_space: bool = True,
    key_id_to_freq: Optional[Dict[int, float]] = None  # ← NEW parameter
) -> SVG:
    # ...
    # Use key_id_to_freq if available for accurate key mapping
    if key_id_to_freq is not None and key.id in key_id_to_freq:
        max_char_freq = key_id_to_freq[key.id]
    else:
        # Fallback: use character-based lookup
        # ...
```

## Benefits

### 1. Accurate Key Mapping
- Physical keys are identified by their key_id, not by character mapping
- No ambiguity about which key on the keyboard is being used
- Handles modifier keys (Shift, AltGr) correctly

### 2. Layout Verification
- Heatmaps include key labels (characters) on each key
- Visual confirmation that the correct layout is applied
- Legend shows frequency scale with clear labels

### 3. Performance
- Key_id-based lookup is direct (O(1)) vs character-based mapping
- More efficient for large text corpora

### 4. Maintainability
- Single source of truth for key positions (key_id)
- Easier to debug heatmap issues
- Clear data flow from input to visualization

## Usage Example

```python
from src.core.evaluator import Evaluator
from src.core.map_json_exporter import CSharpFitnessConfig
from src.helpers.layouts.visualization import generate_all_visualizations
from FitnessNet import Fitness

# Setup
ev = Evaluator(debug=False)
ev.load_keyoard('src/data/keyboards/ansi_60_percent.json')
ev.load_layout()
ev.layout.querty_based_remap(LAYOUT_DATA["qwerty"])

# Generate config with key_id
config_gen = CSharpFitnessConfig(keyboard=ev.keyboard, layout=ev.layout)
json_string = config_gen.generate_json_string(
    text_file_path="path/to/text.txt",
    finger_coefficients=[0.07] * 10,
    fitts_a=0.5,
    fitts_b=0.3
)

# Compute stats (includes key_id)
fitness_calculator = Fitness(json_string)
stats_json = fitness_calculator.ComputeStats()

# Generate visualizations with key_id-based heatmaps
layout_svg, press_svg, hover_svg = generate_all_visualizations(
    stats_json=stats_json,
    keyboard=ev.keyboard,
    layout=ev.layout,
    layout_name="my_layout",
    layer_idx=0,
    save_dir="output"
)
```

## Testing

Comprehensive tests verify:
1. key_id is present in C# library output
2. Visualization correctly uses key_id for heatmap coloring
3. Labels and legends are properly rendered
4. No security vulnerabilities introduced

## Future Enhancements

Potential improvements:
- Support for multi-layer heatmaps in single visualization
- Interactive heatmaps with tooltips showing exact frequencies
- Comparative heatmaps between different layouts
- Animation of typing patterns over time

## References

- Original Issue: "Implement Propre Press/Hover Heatmap"
- C# Library: `cs/Class.cs`
- Python Exporter: `src/core/map_json_exporter.py`
- Visualization: `src/helpers/layouts/visualization.py`
