from pythonnet import set_runtime
from clr_loader import get_coreclr
import sys
import os
import time
import json

# Track overall script start
script_start = time.time()

# TIMING POINT 1: Python imports and CLR setup
imports_start = time.time()
from src.core.map_json_exporter import CSharpFitnessConfig
from src.core.keyboard import FingerName
from src.core.mapper import KeyType

set_runtime(get_coreclr())
import clr

dll_dir = os.path.join(os.getcwd(), "cs", "bin", "Release", "net9.0")
sys.path.insert(0, dll_dir)
clr.AddReference("KeyboardFitness")

from FitnessNet import Fitness
from src.core.evaluator import Evaluator
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA

imports_time = time.time() - imports_start
print(f"[TIMING 1] Python imports + CLR setup: {imports_time:.3f}s")

# TIMING POINT 2: Python setup (evaluator, config generation)
setup_start = time.time()

ev = Evaluator(debug=False)
ev.load_keyoard('src/data/keyboards/ansi_60_percent.json')
ev.load_layout()
ev.layout.querty_based_remap(LAYOUT_DATA["qwerty"])

custom_coefficients = [
    0.07,  # Left pinky (slower)
    0.06,  # Left ring
    0.05,  # Left middle
    0.05,  # Left index
    0.05,  # Left thumb
    0.05,  # Right thumb
    0.05,  # Right index
    0.05,  # Right middle
    0.06,  # Right ring
    0.07,  # Right pinky (slower)
]
    
config_gen = CSharpFitnessConfig(
    keyboard=ev.keyboard,
    layout=ev.layout
)

json_string = config_gen.generate_json_string(
    text_file_path="src/data/text/raw/simple_wikipedia_dataset.txt",
    finger_coefficients=custom_coefficients,
    fitts_a=0.5,
    fitts_b=0.3
)

setup_time = time.time() - setup_start
print(f"[TIMING 2] Python setup (evaluator + JSON generation): {setup_time:.3f}s")

# TIMING POINT 3: C# Fitness initialization (JSON parsing + file reading)
init_start = time.time()
fitness_calculator = Fitness(json_string)
init_time = time.time() - init_start
print(f"[TIMING 3] C# Fitness init (JSON parse + file read): {init_time:.3f}s")

# TIMING POINT 4: C# Compute() - the actual computation
compute_start = time.time()
result = fitness_calculator.Compute()
compute_time = time.time() - compute_start
print(f"[TIMING 4] C# Compute() execution: {compute_time:.6f}s")

# TIMING POINT 5: C# ComputeStats() - detailed statistics generation
stats_start = time.time()
stats_json = fitness_calculator.ComputeStats()
stats_time = time.time() - stats_start
print(f"[TIMING 5] C# ComputeStats() execution: {stats_time:.6f}s")

# Total time summary
total_time = time.time() - script_start
print(f"\n=== TIMING SUMMARY ===")
print(f"1. Imports + CLR:     {imports_time:.3f}s ({imports_time/total_time*100:.1f}%)")
print(f"2. Python setup:      {setup_time:.3f}s ({setup_time/total_time*100:.1f}%)")
print(f"3. C# initialization: {init_time:.3f}s ({init_time/total_time*100:.1f}%)")
print(f"4. C# Compute():      {compute_time:.3f}s ({compute_time/total_time*100:.1f}%)")
print(f"5. C# ComputeStats(): {stats_time:.3f}s ({stats_time/total_time*100:.1f}%)")
print(f"Total runtime:        {total_time:.3f}s")
print(f"======================\n")

# Display basic fitness results
print(f"=== BASIC FITNESS RESULTS ===")
print(f"Total distance: {result.Item1:.2f} units")
print(f"Total time: {result.Item2:.2f} units")

# Distance conversion with smart unit selection
distance_mm = result.Item1 * 19.05
distance_m = distance_mm / 1000
distance_km = distance_m / 1000

if distance_km >= 1:
    distance_value, distance_unit = distance_km, "km"
elif distance_m >= 1:
    distance_value, distance_unit = distance_m, "m"
else:
    distance_value, distance_unit = distance_mm, "mm"

# Time conversion with smart unit selection
time_seconds = result.Item2
time_minutes = time_seconds / 60
time_hours = time_minutes / 60
time_days = time_hours / 24

if time_days >= 1:
    time_value, time_unit = time_days, "days"
elif time_hours >= 1:
    time_value, time_unit = time_hours, "hours"
elif time_minutes >= 1:
    time_value, time_unit = time_minutes, "minutes"
else:
    time_value, time_unit = time_seconds, "seconds"

print(f"Distance: {distance_value:.3f} {distance_unit}")
print(f"Time: {time_value:.3f} {time_unit}\n")

# Parse and display detailed statistics
print("=== DETAILED STATISTICS (ComputeStats) ===")
stats = json.loads(stats_json)

print(f"\nTotal Presses: {stats['total_presses']}")
print(f"Total Hover Samples: {stats.get('total_hover_samples', 'N/A')}")

# Finger statistics summary
print("\n--- Finger Statistics ---")
print(f"{'Finger':<8} {'Presses':>10} {'Press%':>7}")
print("-" * 35)

total_finger_presses = sum(f['press_count'] for f in stats['finger_stats'])

for finger in stats['finger_stats']:
    finger_idx = finger['finger_index']
    press_count = finger['press_count']
    
    # Calculate percentage
    press_pct = (press_count / total_finger_presses * 100) if total_finger_presses > 0 else 0
    
    print(f"Finger {finger_idx} {press_count:10d} {press_pct:6.2f}%")

print(f"\nTotal:   {total_finger_presses:10d} 100.00%")

# Character statistics - show top 20 most frequent
print("\n--- Top 20 Most Frequent Characters ---")
char_data = []
for char, data in stats['char_mappings'].items():
    occurrences = data['occurrences']
    hover_count = data['hover_count']
    press_count = data['press_count']
    char_data.append((char, occurrences, press_count, hover_count))

# Sort by occurrences (descending)
char_data.sort(key=lambda x: x[1], reverse=True)

total_char_hovers = sum(d['hover_count'] for d in stats['char_mappings'].values())

print(f"{'Char':<6} {'Occur':>9} {'Occur%':>7} {'Presses':>9} {'Hovers':>9} {'Hover%':>7}")
print("-" * 65)

for char, occ, presses, hovers in char_data[:20]:
    # Handle special characters for display
    if char == ' ':
        display_char = '<SP>'
    elif char == '\n':
        display_char = '<NL>'
    elif char == '\t':
        display_char = '<TB>'
    else:
        display_char = repr(char)[1:-1]  # Remove quotes from repr
    
    occ_pct = (occ / stats['total_presses'] * 100) if stats['total_presses'] > 0 else 0
    hover_pct = (hovers / total_char_hovers * 100) if total_char_hovers > 0 else 0
    
    print(f"{display_char:<6} {occ:9d} {occ_pct:6.2f}% {presses:9d} {hovers:9d} {hover_pct:6.2f}%")

# Calculate some interesting aggregate statistics
total_hover_samples = stats.get('total_hover_samples', 0)
total_presses_from_chars = sum(d['press_count'] for d in stats['char_mappings'].values())
unique_chars = len([d for d in stats['char_mappings'].values() if d['occurrences'] > 0])

print(f"\n--- Aggregate Statistics ---")
print(f"Total hover samples taken: {total_hover_samples:,}")
print(f"Total character hovers recorded: {total_char_hovers:,}")
print(f"Total presses (from chars): {total_presses_from_chars:,}")
print(f"Unique characters used: {unique_chars}")
if total_hover_samples > 0:
    print(f"Average character hovers per sample: {total_char_hovers / total_hover_samples:.2f}")

# Optionally save the full stats to a file
output_file = "fitness_stats_output.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(stats, f, indent=2, ensure_ascii=False)
print(f"\nFull statistics saved to: {output_file}")

print("\n=== SAMPLE OUTPUT STRUCTURE ===")
print("The JSON contains:")
print("  • total_presses: int - total characters in text")
print("  • total_hover_samples: int - how many times hover state was sampled")
print("  • char_mappings: dict - per-character data:")
print("      - key_presses: array of {x, y, finger}")
print("      - occurrences: how many times this char appeared")
print("      - hover_count: how many times fingers hovered over this key")
print("      - press_count: occurrences × keys_per_char")
print("  • finger_stats: array of per-finger:")
print("      - finger_index: 0-9")
print("      - press_count: actual presses by this finger")
print("\nThis enables generating:")
print("  ✓ Press heatmap (which keys are pressed most)")
print("  ✓ Hover heatmap (where fingers naturally rest)")
print("  ✓ Finger workload distribution")
print("  ✓ Character frequency analysis")
