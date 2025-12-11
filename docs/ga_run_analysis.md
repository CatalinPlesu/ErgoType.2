# GA Run Analysis

This document describes the GA Run Analysis feature added to ErgoType.2.

## Overview

The GA Run Analysis feature allows you to inspect and compare genetic algorithm runs. It provides two main capabilities:

1. **Single Run Inspection**: Browse and analyze a single GA run
2. **Multi-Run Comparison**: Compare multiple GA runs to analyze parameter impact

## Accessing the Feature

From the main menu, select:
```
🔬 Analyze GA Runs
```

This opens a sub-menu with two options:
- 🔍 Single Run Inspection
- 📊 Multi-Run Comparison

## Single Run Inspection

### Features

- Browse all generations in a GA run
- View individual chromosomes with detailed metrics:
  - Layout visualization (text representation)
  - Fitness score breakdown
  - Distance and time metrics
  - Parent information
- Generate and save SVG heatmaps for selected chromosomes

### Output Location

Selected chromosome visualizations are saved to:
```
output/analysis/{run_timestamp}/cherry_picked/gen_{N}_chr_{M}/
```

Each directory contains:
- `{chromosome_name}_stats.json` - Statistical data
- `{chromosome_name}_layer{N}_layout.svg` - Layout visualization
- `{chromosome_name}_layer{N}_press.svg` - Press heatmap
- `{chromosome_name}_layer{N}_hover.svg` - Hover heatmap

### Usage

1. Select "Single Run Inspection" from the analysis menu
2. Choose a GA run from the list
3. View the run summary
4. Select a generation to browse
5. Select an individual chromosome
6. View detailed metrics
7. Optionally generate SVG heatmaps

## Multi-Run Comparison

### Features

- Compare multiple GA runs simultaneously
- Re-normalize fitness values across all runs for fair comparison
- Analyze parameter impact:
  - Population size vs. best fitness achieved
  - Number of generations vs. convergence speed/quality
  - Runtime vs. fitness improvement
- Generate comprehensive visualizations:
  - Fitness progression overlay charts
  - Parameter correlation scatter plots
  - Statistical summary tables

### Output Location

Comparison results are saved to:
```
output/analysis/multi_run_{timestamp}/
```

Each directory contains:
- `fitness_progression.png` - Fitness evolution over generations
- `parameter_correlations.png` - Parameter impact analysis (4 scatter plots)
- `comparison_summary.json` - Detailed statistics in JSON format
- `comparison_summary.csv` - Detailed statistics in CSV format
- `analysis_report.md` - Comprehensive markdown report

### Usage

1. Select "Multi-Run Comparison" from the analysis menu
2. View the list of available GA runs
3. Select runs to compare (enter numbers separated by commas, or "all")
4. Review the comparison summary table
5. Confirm to generate and export analysis
6. Results are saved to the timestamped output directory

## Data Requirements

### Input Data Structure

The analysis tools expect GA runs to be saved in:
```
output/ga_results/ga_run_{timestamp}/
```

Each GA run directory must contain:
- `ga_run_metadata.json` - Run configuration and results
- `ga_all_individuals.json` - All evaluated individuals

### Metadata Format

The `ga_run_metadata.json` file should contain:
```json
{
  "timestamp": "YYYY-MM-DD--HH-MM-SS",
  "keyboard_file": "path/to/keyboard.json",
  "text_file": "path/to/text.txt",
  "population_size": 30,
  "max_iterations": 50,
  "stagnant_limit": 10,
  "best_fitness": 0.345678,
  "best_layout_name": "gen_5-42",
  "total_unique_individuals": 120,
  "fitts_a": 0.5,
  "fitts_b": 0.3,
  "finger_coefficients": [...]
}
```

### Individuals Format

The `ga_all_individuals.json` file should contain:
```json
{
  "all_individuals": [
    {
      "id": 1,
      "name": "gen_0-1",
      "fitness": 0.456789,
      "distance": 1234.5,
      "time": 567.8,
      "chromosome": "qwertyuiop...",
      "generation": 0,
      "parents": []
    },
    ...
  ],
  "best_individual": { ... }
}
```

## Technical Details

### Module Structure

```
src/analysis/
├── __init__.py              # Module initialization
├── ga_run_loader.py         # Load and parse GA run data
├── single_run_inspector.py  # Single run inspection
└── multi_run_comparator.py  # Multi-run comparison
```

### Key Classes

- **GARunLoader**: Loads GA run metadata and individuals from disk
- **SingleRunInspector**: Interactive single run browser
- **MultiRunComparator**: Multi-run comparison and visualization

### Dependencies

- `numpy` - Numerical operations for normalization
- `matplotlib` - Visualization generation
- `pandas` - CSV export (optional, falls back to JSON only)
- `rich` - Console UI components

## Examples

### Example: Comparing Two Runs

```
🔬 Analyze GA Runs → 📊 Multi-Run Comparison

Available runs:
1. ga_run_2024-01-01--12-00-00 (Best: 0.345678)
2. ga_run_2024-01-02--14-00-00 (Best: 0.312345)

Selection: 1,2

Multi-Run Comparison (2 runs selected)
┌───┬────────────────────────┬──────────┬──────────┬──────┬──────────────┬────────────┐
│ # │ Run                    │ Pop Size │ Max Iter │ Gens │ Best Fitness │ Total Inds │
├───┼────────────────────────┼──────────┼──────────┼──────┼──────────────┼────────────┤
│ 1 │ ga_run_2024-01-01...   │ 30       │ 50       │ 6    │ 0.345678     │ 120        │
│ 2 │ ga_run_2024-01-02...   │ 50       │ 30       │ 9    │ 0.312345     │ 160        │
└───┴────────────────────────┴──────────┴──────────┴──────┴──────────────┴────────────┘

Generate and export comparison analysis? [Y/n]: y

✓ Re-normalized 280 individuals across 2 runs
✓ Analyzed parameter impact
✓ Generated fitness_progression.png
✓ Generated parameter_correlations.png
✓ Generated comparison_summary.json
✓ Generated comparison_summary.csv
✓ Generated analysis_report.md
✅ Export complete! Results saved to: output/analysis/multi_run_2024-01-03--10-30-00/
```

## Troubleshooting

### No GA Runs Found

If you see "No GA runs found", make sure:
1. You have run the genetic algorithm at least once
2. The output directory exists: `output/ga_results/`
3. GA run directories follow the naming pattern: `ga_run_{timestamp}`

### Missing Dependencies

If you encounter import errors for `numpy`, `matplotlib`, or `pandas`, install them:
```bash
pip install numpy matplotlib pandas
```

### Visualization Generation Fails

For single run inspection, if SVG generation fails:
1. Ensure the C# fitness library is compiled
2. Check that the keyboard and text files referenced in metadata exist
3. Verify the layout data can be loaded from `src/data/layouts/keyboard_genotypes.py`

## Future Enhancements

Potential improvements:
- Interactive selection of specific parameters to compare
- Statistical significance testing for parameter differences
- Export to additional formats (HTML, PDF)
- Real-time comparison as GA runs complete
- Parameter optimization suggestions based on historical data
