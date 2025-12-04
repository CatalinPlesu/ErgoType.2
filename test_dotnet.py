from pythonnet import set_runtime
from clr_loader import get_coreclr
import sys
import os



from src.core.map_json_exporter import CSharpFitnessConfig
from src.core.keyboard import FingerName
from src.core.mapper import KeyType
# Configure pythonnet to use .NET (CoreCLR) instead of Mono
# This must be done BEFORE importing clr
# Use get_coreclr() without arguments to find the default .NET runtime
set_runtime(get_coreclr())

# NOW import clr
import clr

# Add the directory containing the DLL to the path
dll_dir = os.path.join(os.getcwd(), "cs", "bin", "Release", "net9.0")
sys.path.insert(0, dll_dir)

# Add reference to the assembly
clr.AddReference("KeyboardFitness")

# Import from the namespace (FitnessNet), not the assembly name
from FitnessNet import Fitness

from src.core.evaluator import Evaluator
from src.data.layouts.keyboard_genotypes import LAYOUT_DATA

# Initialize evaluator (only need keyboard and layout)
ev = Evaluator(debug=False)
ev.load_keyoard('src/data/keyboards/ansi_60_percent.json')
ev.load_layout()

# Apply a layout
ev.layout.querty_based_remap(LAYOUT_DATA["qwerty"])

# Create configuration generator (no distance calculator needed!)
config_gen = CSharpFitnessConfig(
    keyboard=ev.keyboard,
    layout=ev.layout
)

# Generate JSON string to pass to C# library
json_string = config_gen.generate_json_string(
    text_file_path="src/data/text/raw/simple_wikipedia_dataset.txt",
    fitts_a=0.5,
    fitts_b=0.3
)

# Now you can use your .NET classes in Python
fitness_calculator = Fitness(json_string )
result = fitness_calculator.Compute()
print(f"total distance: {result.Item1} total time: {result.Item2}")


# Distance conversion with smart unit selection
distance_mm = result.Item1 * 19.05
distance_m = distance_mm / 1000
distance_km = distance_m / 1000

# Select most appropriate distance unit
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

# Select most appropriate time unit
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
# char_positions = {'a': Point(0, 0), 'b': Point(1, 1)}  # Example character positions
# result = fitness_calculator.FitnessComponents("ab", char_positions)
# print(result)
