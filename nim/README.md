# Nim Port for Text Processing and Fitness Calculation

This directory contains a minimal Nim port of the performance-critical text processing code from the Python simplified typer.

## Goal
Port the character-by-character text iteration and fitness calculation from `src/core/simplified_typer.py` to Nim for better performance.

## Key Components to Port

### 1. Core Data Structures
- Minimal key representation (char, finger, position)
- Finger state tracking
- Distance calculation between positions

### 2. Performance-Critical Functions
- `calculate_distance_and_time_from_raw_text()` - lines 280-313
- `process_parallel_typing()` - lines 140-177  
- `type_character_sequential()` - lines 179-217
- `move_finger_in_window()` - lines 93-138

### 3. Text Processing
- Character iteration through large text files
- Finger movement simulation
- Fitts law time calculation

## Input/Output
- Input: Text file path, preview mode flag, file size info
- Output: Distance, time, coverage statistics

## Minimal Structure
Keep only essential data:
- Character-to-key mapping
- Key position (x,y) 
- Finger assignment
- Basic distance/time calculations

Avoid porting:
- Full keyboard layout complexity
- Complex modifier handling
- Advanced caching systems
- Full configuration system