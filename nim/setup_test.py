# Compile and test the Nim text processor

import os
import subprocess

# Create a simple test script to compile and run Nim code
nim_code = '''
echo "Testing Nim compilation..."

# Simple test
let x = 42
echo "Nim works! x = ", x
'''

# Write test file
with open('/home/catalin/dev/ergotype.2/nim/test.nim', 'w') as f:
    f.write(nim_code)

print("Created Nim test file")

# Check if Nim is available
try:
    result = subprocess.run(['nim', '--version'], capture_output=True, text=True)
    if result.returncode == 0:
        print("Nim is available:")
        print(result.stdout.strip())
    else:
        print("Nim not found in PATH")
        print("You may need to install Nim: https://nim-lang.org/install.html")
except FileNotFoundError:
    print("Nim compiler not found")
    print("Install Nim to compile the text processor")

print("\nNim files created:")
print("- text_processor.nim - Main Nim implementation")
print("- minimal_python_structures.py - Python reference")
print("- minimal_text_processor.py - Python test implementation")
print("- README.md - Documentation")

print("\nTo compile the Nim code:")
print("cd nim && nim compile --run text_processor.nim")