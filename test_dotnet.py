import clr
import sys
import os

# Add the directory containing the DLL to the path
dll_dir = os.path.join(os.getcwd(), "cs", "bin", "Release", "net9.0")
sys.path.insert(0, dll_dir)

# Add reference to the assembly
clr.AddReference("KeyboardFitness")

# Import from the namespace (FitnessNet), not the assembly name
from FitnessNet import Fitness, Point, FingerName

# Now you can use your .NET classes in Python
fitness_calculator = Fitness()
print(fitness_calculator.SayHay())
# char_positions = {'a': Point(0, 0), 'b': Point(1, 1)}  # Example character positions
# result = fitness_calculator.FitnessComponents("ab", char_positions)
# print(result)
