# Visual Guide: New GA Menu Flow

## Main Menu Flow

```
┌─────────────────────────────────────────────────────────────┐
│  KEYBOARD LAYOUT OPTIMIZATION SYSTEM                        │
│  Distributed Simulation-Based with C# Fitness               │
└─────────────────────────────────────────────────────────────┘

  🚀 Run Genetic Algorithm (Master Mode)  ← SELECT THIS
  📋 Execute GA Runs Queue
  🔧 Run as Worker Node (Distributed Processing)
  🎯 Generate All Heuristic Heatmaps
  🔬 Analyze GA Runs
  ...

```

## Step-by-Step Menu Flow

### Step 1: Select Physical Keyboard
```
Available Keyboards:
  1. ANSI 60%
  2. ThinkPad
  3. Dactyl
  ...
```

### Step 2: Select Text File
```
Available Text Files:
  1. Simple Wikipedia Dataset (12.5 MB)
  2. Programming Code (5.2 MB)
  ...
```

### ⭐ Step 3: Select GA Run Mode (NEW!)
```
Select GA Run Mode:
  [1] Run as Normal - With heuristic layouts (QWERTY, Dvorak, etc.)
  [2] Random Only - Skip heuristic layouts, use only random individuals
  [3] Continue from Previous Run - Load and continue a previous GA run
```

#### If you select [3] Continue from Previous Run:
```
Loading Previous Runs...

Available Previous Runs:

ga_run_2025-12-16--10-00-00                        Pop:    50  Individuals:    523  Fitness: 0.234567
ga_run_2025-12-15--15-30-00                        Pop:    30  Individuals:    312  Fitness: 0.345678
ga_run_2025-12-15--10-00-00                        Pop:    50  Individuals:    489  Fitness: 0.256789

Select Run to Continue: [1-3]
```

### Step 4: Configure GA Execution Mode
```
Select GA Execution Mode:
  [1] Standard Mode - Fixed population and iterations
  [2] Population Phases Mode - Dynamic population with multiple phases
```

### Step 5: Configure GA Parameters
```
Main GA Parameters:
  Population size: 30
  Max iterations: 50
  Stagnation limit: 10
  Max parallel processes: 4
```

### Step 6: Configure Fitts's Law Parameters
```
Fitts's Law Parameters:
  Fitts's Law constant 'a': 0.5
  Fitts's Law constant 'b': 0.3
```

### Step 7: Configure Finger Coefficients
```
Left Hand Finger Coefficients:
  Left Finger 1 (pinky): 0.07
  Left Finger 2: 0.06
  ...

Right Hand Finger Coefficients:
  Right Finger 6 (thumb): 0.05
  ...
```

### Final Configuration Review
```
═══════════════════════════════════════════════════════════
Final Configuration
═══════════════════════════════════════════════════════════
  Keyboard file       src/data/keyboards/ansi_60_percent.json
  Text file           src/data/text/raw/simple_wikipedia_dataset.txt
  Stagnant limit      10
  Max concurrent      4
  Fitts a             0.5
  Fitts b             0.3
  Use rabbitmq        True
  Skip heuristics     False          ← NEW!
  Continue from run   None           ← NEW!
  Population size     30
  Max iterations      50
═══════════════════════════════════════════════════════════

Start Genetic Algorithm? [Y/n]
```

## What Happens Next

### Mode 1: Run as Normal
```
═══════════════════════════════════════════════════════════
KEYBOARD LAYOUT GENETIC ALGORITHM
═══════════════════════════════════════════════════════════
👑 MASTER MODE - Coordinating GA and processing jobs...
═══════════════════════════════════════════════════════════

Evaluator initialized successfully
Using up to 4 local concurrent processes

Added heuristic layout: qwerty
Added heuristic layout: dvorak
Added heuristic layout: colemak
Added heuristic layout: workman
Added heuristic layout: norman
Population initialized with 5 heuristic individuals
Adding 25 random individuals
Total population size: 30

Generation 1/50 starting...
```

### Mode 2: Random Only
```
═══════════════════════════════════════════════════════════
KEYBOARD LAYOUT GENETIC ALGORITHM
═══════════════════════════════════════════════════════════
👑 MASTER MODE - Coordinating GA and processing jobs...
═══════════════════════════════════════════════════════════

Evaluator initialized successfully
Using up to 4 local concurrent processes

Skipping heuristic layouts (random-only mode)     ← DIFFERENT!
Adding 30 random individuals
Total population size: 30

Generation 1/50 starting...
```

### Mode 3: Continue from Previous Run
```
═══════════════════════════════════════════════════════════
KEYBOARD LAYOUT GENETIC ALGORITHM
═══════════════════════════════════════════════════════════
👑 MASTER MODE - Coordinating GA and processing jobs...
═══════════════════════════════════════════════════════════

Evaluator initialized successfully
Using up to 4 local concurrent processes

═══════════════════════════════════════════════════════════
LOADING FROM PREVIOUS RUN: ga_run_2025-12-16--10-00-00
═══════════════════════════════════════════════════════════
Original run timestamp: 2025-12-16--10-00-00
Original best fitness: 0.234567
Last generation in loaded run: 20
Loaded 523 individuals from history
Current population size (from last generation): 30
Individual ID counter will continue from: 524        ← CONTINUES IDs!
Ready to continue from generation 21                ← CONTINUES GENERATION!
═══════════════════════════════════════════════════════════

Generation 21/50 starting...                        ← PICKS UP WHERE IT LEFT OFF!
```

## Output Directories

### Standard Run
```
output/ga_results/
└── ga_run_2025-12-16--10-00-00/
    ├── ga_run_metadata.json
    ├── ga_all_individuals.json
    ├── rank1_gen_20-345.json
    ├── rank2_gen_19-289.json
    ├── rank3_gen_20-346.json
    ├── fitness_evolution.png
    └── ...
```

### Continued Run
```
output/ga_results/
├── ga_run_2025-12-16--10-00-00/              ← ORIGINAL (preserved)
│   └── ...
│
└── ga_run_2025-12-16--12-00-00_continued_from_ga_run_2025-12-16--10-00-00/  ← NEW!
    ├── ga_run_metadata.json                   ← Contains link to original
    ├── ga_all_individuals.json                ← Full history including original + new
    ├── rank1_gen_50-678.json
    ├── rank2_gen_48-623.json
    ├── rank3_gen_50-680.json
    ├── fitness_evolution.png                  ← Shows complete evolution graph
    └── ...
```

## Summary

The new menu adds a crucial Step 3 that lets you choose HOW to initialize and run the GA:

1. **Normal** - The way it always worked (heuristics + random)
2. **Random** - Pure evolutionary search (no heuristics)
3. **Continue** - Pick up where a previous run left off

All three modes work seamlessly with the existing Standard/Phases execution modes!
