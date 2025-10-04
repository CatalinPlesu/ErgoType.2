# Project Structure Simplification Proposal

## Current Issues:
1. **Overcomplicated directory structure** - Too many nested directories for a genetic algorithm project
2. **Mixed concerns** - Data processing mixed with core algorithms
3. **Inconsistent naming** - `data` vs `helpers`, unclear module boundaries
4. **Redundant files** - README files in subdirectories, unnecessary complexity

## Proposed Simplified Structure:

```
src/
├── core/                    # Core algorithms and domain models
│   ├── genetic_algorithm.py
│   ├── keyboard.py
│   ├── layout_phenotype.py
│   ├── evaluation/
│   │   ├── fitness_calculator.py
│   │   └── layout_evaluator.py
│   └── simulation/
│       ├── finger_manager.py
│       └── typing_simulator.py
├── data/                    # All data assets in one place
│   ├── keyboards/           # KLE JSON files
│   ├── layouts/             # Keyboard genotype data
│   ├── languages/           # Language configs
│   ├── text/                # Processed text data
│   └── config/              # Global config files
├── utils/                   # Helper utilities (was helpers)
│   ├── keyboard_renderer.py
│   ├── text_processor.py
│   ├── scraper.py
│   └── visualization.py
└── main.py                  # CLI entry point
```

## Key Improvements:
1. **Clear separation** - Core algorithms vs data vs utilities
2. **Flatter structure** - Remove unnecessary nesting
3. **Consistent naming** - All modules have clear purposes
4. **Single README** - Consolidate documentation
5. **Better modularity** - Each module has a single responsibility

## Benefits:
- Easier to navigate and understand
- Reduced cognitive load for new developers
- Better testability and maintainability
- Preserves all existing functionality
- More intuitive project structure

## Migration Steps:
1. Create new directory structure
2. Move files to appropriate locations
3. Update import statements
4. Consolidate README files
5. Test functionality after migration
