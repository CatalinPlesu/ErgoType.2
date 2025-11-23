# Makefile for Nim Text Processor Library

This Makefile provides convenient targets for building and testing the Nim text processor library.

## Quick Start

```bash
# Install Nim first (recommended)
curl https://nim-lang.org/choosenim/init.sh -sSf | sh
source ~/.nimble/bin/nim

# Then use the Makefile
make all          # Compile everything and run tests
make benchmark    # Run performance comparison
make clean        # Clean build artifacts
```

## Available Targets

### Basic Targets
- `all` - Compile everything and run tests (default)
- `main` - Compile main text processor executable
- `library` - Compile Python library interface  
- `test` - Run compilation tests
- `clean` - Clean build artifacts

### Advanced Targets
- `release` - Compile optimized release versions
- `benchmark` - Run performance benchmarks
- `install-deps` - Install Python dependencies (nimpy)

### Help
- `help` - Show this help message

## Compilation Instructions

The Makefile provides guidance for different Nim installation methods:

### Option 1: Direct Nim Installation (Recommended)
```bash
# Install Nim
curl https://nim-lang.org/choosenim/init.sh -sSf | sh

# Compile manually
nim compile text_processor.nim
nim compile text_processor_lib_working.nim
nim py --lib text_processor_lib_working.nim
```

### Option 2: Nix Wrapper (Limited functionality)
```bash
# Use the nix wrapper (may have limitations)
nix run nixpkgs#nim -- compile text_processor.nim
```

## Performance Testing

```bash
# Run benchmark comparison
make benchmark

# This compares Python vs Nim performance on text processing
```

## Python Integration

```bash
# Install nimpy for Python integration
make install-deps

# Test the Python wrapper
python3 nim_wrapper.py
```

## Files Structure

- `text_processor.nim` - Main Nim implementation
- `text_processor_lib_working.nim` - Python library interface  
- `nim_wrapper.py` - Python wrapper with fallback
- `integration_example.py` - Integration examples
- `minimal_*.py` - Reference Python implementations

## Troubleshooting

If you encounter issues with the nix wrapper, install Nim directly:
- **Linux/macOS**: `curl https://nim-lang.org/choosenim/init.sh -sSf | sh`
- **Windows**: Download from https://nim-lang.org/install.html
- **Alternative**: Use your package manager (apt, brew, etc.)

The Makefile will provide specific instructions for your environment.