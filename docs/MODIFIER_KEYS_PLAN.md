# Modifier Keys Implementation Plan

## Current Status

### What's Implemented
- ✅ Multi-layer chromosome structure (list of lists)
- ✅ Sparse layer initialization (upper layers mostly None)
- ✅ 7 mutation strategies including layer addition/removal
- ✅ Layer-to-layer crossover
- ✅ Configurable mutation rates
- ✅ Chromosome validation

### What's Missing
- ❌ Modifier key assignment when layers are added
- ❌ Validation that layers are accessible
- ❌ Fitness accounting for modifier key presses
- ❌ Visual representation of modifier->layer mappings

## Problem Statement

For a multi-layer keyboard to be functional:
1. Each layer (except layer 0) must have at least one modifier key that activates it
2. Modifier keys must exist on a lower layer (typically layer 0)
3. The fitness function must account for the cost of pressing modifiers
4. Users need to know which keys activate which layers

## Proposed Solution

### Phase 1: Modifier Key Metadata (Current)
Add modifier key tracking without changing chromosome structure:

```python
class Individual:
    def __init__(self, ...):
        self.chromosome = [layer0, layer1, ...]
        self.layer_modifiers = {
            1: 'AltGr',      # Layer 1 accessed via AltGr
            2: 'Ctrl+Alt',   # Layer 2 accessed via Ctrl+Alt
            # etc.
        }
```

**Advantages:**
- Doesn't break existing chromosome operations
- Easy to serialize/deserialize
- Can be evolved separately

**Disadvantages:**
- Modifiers not part of chromosome (not evolved by GA)
- Fixed modifier assignments

### Phase 2: Modifier Keys in Chromosome (Future)
Make modifiers part of the evolved layout:

```python
# Chromosome includes modifier key positions
chromosome = [
    ['q', 'w', 'e', ..., 'AltGr'],  # Layer 0 with modifier
    [None, 'ă', None, ..., None],    # Layer 1 accessed by AltGr
]
```

**Advantages:**
- GA can evolve optimal modifier positions
- More realistic simulation

**Disadvantages:**
- Major refactoring required
- Complex validation
- Fitness function changes

## Implementation Plan

### Step 1: Add Metadata Infrastructure ✅
- Add `layer_modifiers` dict to Individual class
- Assign default modifiers when layers are created:
  - Layer 1: 'AltGr'
  - Layer 2: 'Shift+AltGr'
  - Layer 3: 'Ctrl+Alt'
  
### Step 2: Validation ⏳
- `validate_layer_accessibility()`: Check all layers have modifiers
- Add to chromosome validation
- Warn if layer is unreachable

### Step 3: Serialization ⏳
- Include `layer_modifiers` in JSON output
- Save/load modifier assignments
- Display in console output

### Step 4: Fitness Integration (Future)
- Pass modifier info to C# fitness calculator
- Account for modifier key press time/distance
- This requires C# library changes

### Step 5: Visualization (Future)
- Show modifier assignments in SVG output
- Display "Layer 1 (AltGr)" in heatmaps
- Update keyboard annotator

## Current Implementation

For now, we use a simple default assignment:
- **Layer 1**: Always accessed via AltGr (standard for diacritics)
- **Layer 2**: Accessed via Shift+AltGr
- **Layer 3**: Accessed via Ctrl+Alt

This allows:
- ✅ Multi-layer layouts to work
- ✅ Serialization to include layer info
- ✅ Future extension to evolved modifiers
- ❌ No optimization of modifier positions yet
- ❌ No fitness penalty for modifier presses yet

## Timeline

1. **Now**: Metadata + default assignments
2. **Next**: Validation + serialization
3. **Later**: Fitness integration (requires C# changes)
4. **Future**: Evolved modifier positions

## Notes

- The current approach is pragmatic: get multi-layer working with fixed modifiers
- Future evolution can optimize modifier positions
- Fitness integration requires coordination with C# library
- Romanian layouts use AltGr for diacritics (layer 1) which matches our defaults
