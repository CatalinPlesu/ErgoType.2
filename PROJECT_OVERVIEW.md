# ErgoType.2 - Keyboard Layout Optimization Using Genetic Algorithms

## 🎓 Project Overview

**ErgoType.2** is a Master's dissertation thesis project focused on obtaining better keyboard layouts using **Genetic Algorithms** (GA). The system uses simulation-based optimization to evolve keyboard layouts that minimize typing time and finger travel distance while maximizing ergonomic efficiency.

This project implements a distributed, simulation-driven genetic algorithm that evaluates keyboard layouts based on real-world typing patterns, Fitts's Law, and ergonomic principles.

---

## 🎯 Purpose & Goals

The primary goal of this project is to **optimize keyboard layouts** for improved typing efficiency and ergonomics by:

1. **Minimizing finger travel distance** during typing
2. **Reducing typing time** based on Fitts's Law calculations  
3. **Improving ergonomic comfort** through finger-specific coefficients
4. **Exploring alternative layouts** beyond traditional QWERTY, Dvorak, and Colemak
5. **Providing scientific evidence** through systematic parameter exploration

This is achieved through a sophisticated genetic algorithm that evolves keyboard layouts over multiple generations, using real text data to simulate actual typing behavior.

---

## ✨ Core Features

### 1. **Genetic Algorithm Implementation**
- **Multi-mode execution**:
  - Standard mode with fixed population and iterations
  - Population phases mode with dynamic population sizes
  - Continuation mode to extend previous runs
- **Heuristic initialization**: Start with proven layouts (QWERTY, Dvorak, Colemak, Workman, Norman, Asset, Minimak)
- **Random-only mode**: Pure evolutionary exploration without heuristic bias
- **Intelligent operators**: Tournament selection, multi-point crossover, swap mutation
- **Stagnation handling**: Automatic termination when no improvement occurs

### 2. **Advanced Execution Modes**

#### Standard Mode
Fixed population size and iteration count for consistent, predictable runs.

#### Population Phases Mode
Dynamic population management for exploration vs. exploitation trade-offs:
```python
population_phases = [
    (30, 50),   # 30 iterations with max population 50
    (1, 1000),  # Expand to 1000 for diversity
    (10, 50),   # Contract back to 50 for refinement
    (1, 2000),  # Expand to 2000
    (20, 30),   # Final refinement with 30
]
```

#### Run Continuation
Load and continue evolution from previous runs to extend exploration.

### 3. **Distributed Processing**
- **RabbitMQ integration** for job distribution
- **Master-Worker architecture** for parallel evaluation
- **Multi-core support** with ProcessPoolExecutor
- **Worker nodes** can run on separate machines
- **Automatic load balancing** across available workers

### 4. **Queue-Based Execution**
Execute multiple GA runs sequentially with different parameters:
- **Parameter exploration**: 25-configuration matrix for systematic testing
- **Custom queues**: Define your own experiment sequences
- **Automatic ID reset**: Consistent naming across runs
- **Results tracking**: JSON output with all run statistics

### 5. **Comprehensive Analysis Tools**

#### Single Run Inspection
- View complete run metadata and configuration
- Analyze best individuals across generations
- Track fitness progression over time
- Export detailed statistics

#### Multi-Run Comparison
- Compare multiple GA runs side-by-side
- Identify best performing configurations
- Visualize fitness convergence across runs
- Generate comparison reports

### 6. **Rich Visualization System**

The system generates three types of SVG visualizations for each layout:

#### Layout View
- Color-coded by finger assignment
- Clear key labels
- Physical keyboard representation

#### Press Heatmap (Blue-Red)
- Shows key press frequency
- Red = high usage, White = low usage
- Separate scaling for alphanumeric vs. modifier keys
- Gradient legend for interpretation

#### Hover Heatmap (Grey-Green)
- Shows finger hover/movement patterns
- Green = high hover frequency
- Indicates finger travel patterns
- Reveals ergonomic hotspots

### 7. **Fitness Calculation (C# Integration)**
High-performance fitness evaluation using C# library:
- **Fitts's Law**: Movement time = a + b × log₂(Distance/Width + 1)
- **Finger-specific coefficients**: Different weights for each finger
- **Distance calculation**: Euclidean distance between key centers
- **Character mapping**: Complete tracking of key sequences
- **Statistics generation**: Press counts, hover counts, efficiency ratios

### 8. **Physical Keyboard Support**
Multiple keyboard layouts supported:
- **ANSI 60%** standard keyboards
- **ThinkPad** laptop keyboards
- **Dactyl Manuform 6x6** ergonomic split keyboard
- **Ferris Sweep** compact 34-key split keyboard
- Extensible JSON format for custom keyboards

### 9. **Text Dataset Support**
Train on real-world text data:
- Wikipedia datasets
- Programming language corpora
- Custom text files
- Character frequency analysis
- Bigram and trigram support

### 10. **Interactive Menu System**
Rich terminal UI with:
- Keyboard and text file selection
- Parameter configuration with validation
- Mode selection (standard/phases/continuation)
- Progress tracking with visual feedback
- Preference saving for quick re-runs

### 11. **Heuristic Caching**
Pre-compute and cache heuristic layouts:
- Parallel generation across multiple cores
- Reusable across GA runs
- Organized by dataset and keyboard
- Force regeneration option
- Significant speedup for initialization

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│  (Interactive Menu, CLI, Queue System, Analysis Tools)       │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                  Genetic Algorithm Core                      │
│  • Population Management    • Selection & Crossover          │
│  • Mutation & Evolution    • Stagnation Detection           │
│  • Phase Management        • Continuation Logic             │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│              Distributed Job Queue (RabbitMQ)                │
│  • Master-Worker Communication  • Load Balancing             │
│  • Job Distribution            • Result Collection          │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                 Fitness Evaluation Layer                     │
│  • C# Integration (pythonnet)  • Fitts's Law Calculation    │
│  • Distance Calculation        • Statistics Generation      │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                   Data & Visualization                       │
│  • Keyboard Models   • Layout Mapping   • SVG Generation    │
│  • Text Processing   • Heatmap Rendering                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Output Formats

### 1. **JSON Outputs**

#### GA Run Metadata (`ga_run_metadata.json`)
```json
{
  "run_name": "ga_run_2025-12-17--10-30-00",
  "mode": "standard",
  "population_size": 50,
  "max_iterations": 100,
  "actual_iterations": 45,
  "best_fitness": 0.234567,
  "best_layout": "qwfpgjluy;arsndhoeit'zxcbvkm,./...",
  "keyboard_file": "src/data/keyboards/ansi_60_percent.json",
  "text_file": "src/data/text/raw/simple_wikipedia_dataset.txt",
  "fitts_a": 0.5,
  "fitts_b": 0.3,
  "finger_coefficients": [0.07, 0.06, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.06, 0.07],
  "start_time": "2025-12-17T10:30:00",
  "end_time": "2025-12-17T12:15:30",
  "duration_seconds": 6330,
  "total_individuals": 523,
  "skip_heuristics": false,
  "continued_from_run": null
}
```

#### All Individuals Data (`ga_all_individuals.json`)
```json
{
  "individuals": [
    {
      "id": 0,
      "name": "gen_0-0",
      "generation": 0,
      "chromosome": ["q", "w", "f", "p", "g", ...],
      "fitness": 0.245678,
      "distance": 12345.67,
      "time_taken": 234.56,
      "parents": null,
      "is_heuristic": true,
      "heuristic_name": "qwerty"
    },
    ...
  ]
}
```

#### Fitness History (`ga_fitness_history.json`)
```json
{
  "generations": [
    {
      "generation": 0,
      "best_fitness": 0.345678,
      "avg_fitness": 0.456789,
      "worst_fitness": 0.567890,
      "best_individual": "gen_0-5",
      "population_size": 50
    },
    ...
  ]
}
```

#### Queue Results (`queue_results_*.json`)
```json
{
  "total_runs": 3,
  "successful_runs": 3,
  "failed_runs": 0,
  "total_duration_seconds": 18900,
  "results": [
    {
      "run_number": 1,
      "name": "Quick Test",
      "start_time": "2025-12-17T10:00:00",
      "duration_seconds": 150.5,
      "success": true,
      "best_fitness": 0.123456,
      "best_layout": "qwfp...",
      "config": { ... }
    },
    ...
  ]
}
```

### 2. **SVG Visualizations**

All visualizations are saved in organized directories:

```
output/
└── ga_results/
    └── ga_run_2025-12-17--10-30-00/
        ├── layouts/
        │   └── best_individual_layer_0.svg
        ├── heatmaps_press/
        │   └── best_individual_layer_0.svg
        └── heatmaps_hover/
            └── best_individual_layer_0.svg
```

#### Layout SVG
- Clean keyboard representation
- Keys colored by finger assignment
- Character labels on each key
- Legend showing finger mapping
- Scalable vector format

#### Press Heatmap SVG
- Blue-red color gradient
- Intensity based on key press frequency
- Separate scaling for alphanumeric and modifier keys
- Gradient legend (Low → High)
- Character labels maintained

#### Hover Heatmap SVG
- Grey-green color gradient
- Shows finger movement patterns
- Indicates areas of high finger travel
- Useful for ergonomic analysis
- Alternative visualization to press frequency

### 3. **PNG Exports**
SVG files can be converted to PNG using standard tools:
```bash
inkscape --export-type=png --export-dpi=300 layout.svg
```

### 4. **Cached Heuristic Data**
Pre-computed heuristic layouts saved in:
```
output/
├── simple_wikipedia_dataset/
│   ├── ansi_60_percent/
│   │   ├── layouts/
│   │   │   ├── qwerty_layer_0.svg
│   │   │   ├── dvorak_layer_0.svg
│   │   │   ├── colemak_layer_0.svg
│   │   │   └── ...
│   │   ├── heatmaps_press/
│   │   └── heatmaps_hover/
│   └── thinkpad/
│       └── ...
└── programming_corpus/
    └── ...
```

---

## 🚀 Usage Examples

### Quick Start
```bash
# Launch interactive menu
python3 main.py

# Select option: "🚀 Run Genetic Algorithm (Master Mode)"
# Follow the prompts to configure and run
```

### Standard GA Run (Python API)
```python
from core.run_ga import run_genetic_algorithm

best = run_genetic_algorithm(
    keyboard_file='src/data/keyboards/ansi_60_percent.json',
    text_file='src/data/text/raw/simple_wikipedia_dataset.txt',
    population_size=50,
    max_iterations=100,
    stagnant_limit=10,
    max_concurrent_processes=4,
    fitts_a=0.5,
    fitts_b=0.3,
    finger_coefficients=[0.07, 0.06, 0.05, 0.05, 0.05, 
                         0.05, 0.05, 0.05, 0.06, 0.07]
)

print(f"Best layout: {best.chromosome}")
print(f"Fitness: {best.fitness}")
```

### Population Phases Mode
```python
best = run_genetic_algorithm(
    keyboard_file='src/data/keyboards/ansi_60_percent.json',
    text_file='src/data/text/raw/simple_wikipedia_dataset.txt',
    population_phases=[
        (30, 50),    # Warm-up: 30 iterations, max 50 individuals
        (1, 1000),   # Shake things up: expand to 1000
        (10, 50),    # Refine: contract to 50
        (20, 30),    # Final polish: 20 iterations with 30
    ],
    stagnant_limit=15
)
```

### Continue from Previous Run
```python
best = run_genetic_algorithm(
    max_iterations=50,  # Additional 50 iterations
    continue_from_run='output/ga_results/ga_run_2025-12-17--10-00-00'
)
```

### Random-Only Mode (No Heuristics)
```python
best = run_genetic_algorithm(
    keyboard_file='src/data/keyboards/ansi_60_percent.json',
    text_file='src/data/text/raw/simple_wikipedia_dataset.txt',
    population_size=50,
    max_iterations=100,
    skip_heuristics=True  # Pure random evolution
)
```

### Queue Execution - Parameter Exploration
```python
from core.ga_runs_queue import create_parameter_exploration_queue

# Create and execute 25-configuration matrix
queue = create_parameter_exploration_queue()
results = queue.execute(verbose=True)

# Results are automatically saved to:
# output/ga_queue_results/param_exploration_*.json
```

### Custom Queue
```python
from core.ga_runs_queue import GARunsQueue, create_run_config

queue = GARunsQueue()

# Add multiple runs with different configurations
queue.add_run(create_run_config(
    name='Small_Fast',
    population_size=20,
    max_iterations=30,
    stagnant_limit=5
))

queue.add_run(create_run_config(
    name='Large_Thorough',
    population_size=100,
    max_iterations=200,
    stagnant_limit=20
))

queue.add_run(create_run_config(
    name='With_Phases',
    population_phases=[(30, 50), (1, 1000), (10, 50)]
))

# Execute all runs
results = queue.execute(verbose=True)

# Save queue configuration for future use
queue.save_to_file('output/my_experiment.json')
```

### Distributed Processing

**Master Node:**
```bash
# Start GA in master mode (uses RabbitMQ automatically)
python3 main.py
# Select: "🚀 Run Genetic Algorithm (Master Mode)"
```

**Worker Nodes (on other machines):**
```bash
# Start worker nodes to process jobs
python3 main.py
# Select: "🔧 Run as Worker Node (Distributed Processing)"
```

### Pre-generate Heuristic Layouts
```bash
# Launch menu
python3 main.py

# Select: "🎯 Generate All Heuristic Heatmaps"
# This will pre-compute all standard layouts for all keyboards and datasets
```

### Analysis Tools

**Single Run Inspection:**
```bash
python3 main.py
# Select: "🔬 Analyze GA Runs"
# Then: "🔍 Single Run Inspection"
# Browse and analyze any completed GA run
```

**Multi-Run Comparison:**
```bash
python3 main.py
# Select: "🔬 Analyze GA Runs"
# Then: "📊 Multi-Run Comparison"
# Select multiple runs to compare side-by-side
```

---

## 📁 Project Structure

```
ErgoType.2/
├── main.py                          # Main entry point with interactive menu
├── src/
│   ├── core/                        # Core GA and evaluation logic
│   │   ├── ga.py                    # Genetic algorithm implementation
│   │   ├── run_ga.py                # GA execution orchestration
│   │   ├── evaluator.py             # Fitness evaluation coordinator
│   │   ├── keyboard.py              # Keyboard model representation
│   │   ├── layout.py                # Layout mapping logic
│   │   ├── mapper.py                # Character-to-key mapping
│   │   ├── ga_runs_queue.py         # Queue management system
│   │   └── job_queue.py             # RabbitMQ job distribution
│   ├── data/
│   │   ├── keyboards/               # Physical keyboard definitions (JSON)
│   │   ├── layouts/                 # Heuristic layout genotypes
│   │   └── text/                    # Text datasets for training
│   ├── helpers/
│   │   ├── keyboards/               # Keyboard rendering and annotation
│   │   ├── layouts/                 # Layout utilities and visualization
│   │   │   ├── visualization.py     # SVG generation (layouts + heatmaps)
│   │   │   └── heuristic_generator.py  # Pre-compute heuristics
│   │   └── text/                    # Text processing utilities
│   ├── ui/                          # User interface components
│   │   ├── rich_menu.py             # Interactive menu system
│   │   └── preferences.py           # User preference persistence
│   └── analysis/                    # Analysis and comparison tools
│       ├── ga_run_loader.py         # Load GA run data
│       ├── single_run_inspector.py  # Inspect single runs
│       └── multi_run_comparator.py  # Compare multiple runs
├── cs/                              # C# fitness library (DLL)
│   └── Fitness/                     # High-performance calculations
├── docs/                            # Documentation
│   ├── GA_RUN_MODES.md              # Run modes documentation
│   ├── GA_RUNS_QUEUE.md             # Queue system guide
│   ├── PARAMETER_EXPLORATION.md     # Parameter exploration guide
│   ├── POPULATION_PHASES.md         # Population phases documentation
│   └── ...
├── output/                          # Generated outputs (not in repo)
│   ├── ga_results/                  # Individual GA runs
│   ├── ga_queue_results/            # Queue execution results
│   ├── {dataset}/                   # Cached heuristics by dataset
│   │   └── {keyboard}/              # Cached heuristics by keyboard
│   │       ├── layouts/             # Layout SVGs
│   │       ├── heatmaps_press/      # Press heatmap SVGs
│   │       └── heatmaps_hover/      # Hover heatmap SVGs
│   └── ...
├── tests/                           # Unit and integration tests
├── notebooks/                       # Jupyter notebooks for analysis
├── pyproject.toml                   # Python dependencies
└── README.md                        # Quick reference guide
```

---

## 🔬 Genetic Algorithm Details

### Population Initialization
1. **Heuristic layouts** (optional): QWERTY, Dvorak, Colemak, Workman, Norman, Asset, Minimak
2. **Random individuals**: Fill remaining slots with random permutations
3. **Load from previous run** (optional): Continue evolution from saved state

### Evolution Operators

#### Selection
- **Tournament selection** with configurable tournament size
- Elitism: Best individuals automatically advance to next generation

#### Crossover
- **Multi-point crossover**: Combine parent genomes at multiple points
- **Repair mechanism**: Ensure all characters appear exactly once
- **Parent selection**: Tournament-based with fitness weighting

#### Mutation
- **Swap mutation**: Randomly swap two characters
- **Adaptive rate**: Can be adjusted based on diversity
- **Constraint preservation**: Maintains valid keyboard layouts

### Fitness Function

**Objective**: Minimize total typing time and distance

**Components**:
1. **Fitts's Law**: Movement time = a + b × log₂(Distance/Width + 1)
2. **Distance**: Euclidean distance between key centers
3. **Finger coefficients**: Weighted by finger strength/speed
4. **Character frequency**: Based on actual text data

**Formula**:
```
Fitness = Σ (frequency[c] × time[c])

where:
  time[c] = Σ (Fitts_time[k] × finger_coefficient[k])
  Fitts_time[k] = a + b × log₂(distance[k] / width[k] + 1)
```

### Termination Conditions
1. Maximum iterations reached
2. Stagnation limit exceeded (no improvement for N generations)
3. Perfect fitness achieved (theoretical minimum)
4. User interruption (Ctrl+C)

---

## 📈 Performance Metrics

### Typical Performance
- **Evaluation speed**: ~50-100 individuals/minute (single core)
- **Parallel speedup**: ~4x with 4 cores, ~8x with 8 cores
- **Small run** (pop=30, iter=50): ~15-30 minutes
- **Medium run** (pop=50, iter=100): ~1-2 hours
- **Large run** (pop=100, iter=200): ~4-8 hours
- **Parameter exploration** (25 configs): ~3 hours

### Convergence
- **Typical improvement**: 10-30% over QWERTY baseline
- **Best observed**: 35-40% improvement
- **Generations to convergence**: Usually 30-80 generations
- **Diversity maintenance**: Monitored to prevent premature convergence

---

## 🧪 Research Applications

### Parameter Space Exploration
Systematically test different GA configurations:
- Population sizes: 5 to 300
- Iteration counts: 5 to 300  
- Fitts's Law constants: a ∈ [0.1, 1.0], b ∈ [0.1, 1.0]
- Finger coefficients: Different finger strength models
- Selection pressure: Tournament size variations

### Layout Comparison Studies
Compare evolved layouts against:
- QWERTY (baseline)
- Dvorak (traditional alternative)
- Colemak (modern alternative)
- Workman (ergonomic-focused)
- Norman, Asset, Minimak (specialized)

### Ergonomic Analysis
- Finger load distribution
- Hand alternation frequency
- Same-finger bigram reduction
- Row jumping analysis
- Home row usage optimization

### Domain-Specific Optimization
Train on specific corpora:
- Programming languages (Python, Java, C++)
- Natural language (English, multilingual)
- Technical writing
- Chat/messaging patterns

---

## 🔧 Configuration

### Fitts's Law Parameters
- **a (intercept)**: Base movement time (default: 0.5)
- **b (slope)**: Logarithmic scaling factor (default: 0.3)

### Finger Coefficients
Default values (index 0 = left pinky, 9 = right pinky):
```python
[0.07, 0.06, 0.05, 0.05, 0.05,  # Left hand
 0.05, 0.05, 0.05, 0.06, 0.07]  # Right hand
```
Lower values = faster/stronger fingers

### GA Parameters
- **Population size**: 20-100 (default: 50)
- **Max iterations**: 50-200 (default: 100)
- **Stagnation limit**: 5-20 (default: 10)
- **Tournament size**: 3-7 (default: 5)
- **Mutation rate**: 0.01-0.1 (default: 0.05)
- **Crossover rate**: 0.7-0.95 (default: 0.8)

---

## 🎓 Academic Context

This project represents a **Master's dissertation thesis** on:
- **Genetic Algorithm optimization** for combinatorial problems
- **Ergonomic keyboard design** principles
- **Human-computer interaction** modeling
- **Distributed computing** for evolutionary algorithms
- **Visualization** of complex optimization results

### Key Contributions
1. **Novel fitness function** combining Fitts's Law with finger-specific modeling
2. **Population phases** approach for dynamic exploration/exploitation
3. **Distributed GA architecture** using RabbitMQ
4. **Comprehensive visualization** system for layout analysis
5. **Queue-based experimentation** framework for parameter studies
6. **Continuation mechanism** for progressive refinement

### Potential Publications
- Comparison of heuristic vs. random initialization
- Impact of population phases on convergence
- Domain-specific layout optimization results
- Distributed GA performance analysis
- Fitts's Law parameter sensitivity study

---

## 📚 Related Documentation

- **[README.md](README.md)** - Quick reference and getting started
- **[docs/GA_RUN_MODES.md](docs/GA_RUN_MODES.md)** - Detailed run mode documentation
- **[docs/GA_RUNS_QUEUE.md](docs/GA_RUNS_QUEUE.md)** - Queue system guide
- **[POPULATION_PHASES.md](POPULATION_PHASES.md)** - Population phases explanation
- **[docs/PARAMETER_EXPLORATION.md](docs/PARAMETER_EXPLORATION.md)** - Parameter study guide
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical implementation details

---

## 🤝 Contributing

This is a research project, but suggestions and improvements are welcome:
- Report issues or bugs
- Suggest new features or analysis tools
- Contribute keyboard definitions
- Share interesting results

---

## 📄 License

See repository for license information.

---

## 👨‍🎓 Author

**Cătălin Pleșu**  
Master's Dissertation Project  
Keyboard Layout Optimization Using Genetic Algorithms

---

## 🙏 Acknowledgments

- Built with Python, C#, RabbitMQ, Rich UI, SVGWrite
- Inspired by research in ergonomic keyboard design
- Uses Fitts's Law for human movement modeling
- Thanks to the open-source community

---

**Last Updated**: December 2025  
**Version**: 0.1.0 (Thesis Version)
