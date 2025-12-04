from pythonnet import set_runtime
from clr_loader import get_coreclr
import sys
import os
import time

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

config_gen = CSharpFitnessConfig(
    keyboard=ev.keyboard,
    layout=ev.layout
)

json_string = config_gen.generate_json_string(
    text_file_path="src/data/text/raw/simple_wikipedia_dataset.txt",
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

# Total time summary
total_time = time.time() - script_start
print(f"\n=== TIMING SUMMARY ===")
print(f"1. Imports + CLR:     {imports_time:.3f}s ({imports_time/total_time*100:.1f}%)")
print(f"2. Python setup:      {setup_time:.3f}s ({setup_time/total_time*100:.1f}%)")
print(f"3. C# initialization: {init_time:.3f}s ({init_time/total_time*100:.1f}%)")
print(f"4. C# computation:    {compute_time:.3f}s ({compute_time/total_time*100:.1f}%)")
print(f"Total runtime:        {total_time:.3f}s")
print(f"======================\n")

print(f"total distance: {result.Item1} total time: {result.Item2}")

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

print(f"distance: {distance_value:.3f} {distance_unit}")
print(f"time: {time_value:.3f} {time_unit}")
