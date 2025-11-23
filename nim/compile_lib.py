import os
import sys
import subprocess

def compile_nim_library():
    """Compile the Nim library for Python import"""
    
    print("Compiling Nim library for Python import...")
    
    # Check if Nim is available
    try:
        result = subprocess.run(['nim', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("Error: Nim compiler not found")
            print("Please install Nim: https://nim-lang.org/install.html")
            return False
        print(f"Nim version: {result.stdout.strip()}")
    except FileNotFoundError:
        print("Error: Nim compiler not found in PATH")
        print("Please install Nim: https://nim-lang.org/install.html")
        return False
    
    # Change to nim directory
    nim_dir = "/home/catalin/dev/ergotype.2/nim"
    os.chdir(nim_dir)
    
    # Compile the library
    print("Compiling text_processor.nim...")
    result = subprocess.run(['nim', 'compile', 'text_processor.nim'], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error compiling text_processor.nim: {result.stderr}")
        return False
    print("✓ text_processor.nim compiled successfully")
    
    # Compile the Python library
    print("Compiling Python library...")
    result = subprocess.run(['nim', 'py', '--lib', 'text_processor_lib_working.nim'], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error compiling Python library: {result.stderr}")
        return False
    print("✓ Python library compiled successfully")
    
    # Check for generated files
    files_to_check = ['text_processor_lib_working.pyd', 'text_processor_lib_working.so', 
                     'text_processor_lib_working.dylib']
    
    lib_file = None
    for filename in files_to_check:
        if os.path.exists(filename):
            lib_file = filename
            break
    
    if lib_file:
        print(f"✓ Library file created: {lib_file}")
        print(f"✓ You can now import it directly in Python:")
        print(f"  import {lib_file.replace('.pyd', '').replace('.so', '').replace('.dylib', '')}")
    else:
        print("Warning: No library file found. Checking for .py files...")
        if os.path.exists('text_processor_lib_working.py'):
            print("✓ Found text_processor_lib_working.py")
            print("✓ You can import it directly:")
            print("  import text_processor_lib_working")
    
    return True

if __name__ == "__main__":
    success = compile_nim_library()
    if success:
        print("\n" + "="*50)
        print("SUCCESS: Nim library ready for Python import!")
        print("="*50)
        print("\nExample usage:")
        print("```python")
        print("import text_processor_lib_working")
        print("result = text_processor_lib_working.processTextString('hello world')")
        print("print(result)")
        print("```")
    else:
        print("\n" + "="*50)
        print("FAILED: Check the error messages above")
        print("="*50)