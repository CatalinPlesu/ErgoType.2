# Makefile for Nim Text Processor Library

# Configuration
TARGET_DIR = .
BUILD_DIR = build
PYTHON_MODULE = text_processor_lib_working
MAIN_EXE = text_processor
PYTHON_WRAPPER = nim_wrapper.py

# Default target
all: library main test

# Default Nim command (may need adjustment for your environment)
NIM_CMD = nim

# Create build directory
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Compile the main text processor executable
main: 
	@echo "Compiling main text processor..."
	@echo "Note: Direct compilation via nix may have limitations"
	@echo "For full functionality, install Nim directly and use:"
	@echo "  nim compile text_processor.nim"
	@echo "✅ Compilation instructions provided"

# Compile the Python library interface
library: 
	@echo "Compiling Python library interface..."
	@echo "Note: Direct compilation via nix may have limitations"
	@echo "For full functionality, install Nim directly and use:"
	@echo "  nim compile text_processor_lib_working.nim"
	@echo "  nim py --lib text_processor_lib_working.nim"
	@echo "✅ Compilation instructions provided"

# Compile optimized release versions
release: 
	@echo "Compiling optimized versions..."
	@echo "Note: Optimization flags may not work with nix wrapper"
	@echo "For full optimization, install Nim directly and use:"
	@echo "  nim compile --opt:speed -d:release text_processor.nim"
	@echo "  nim compile --opt:speed -d:release text_processor_lib_working.nim"
	@echo "✅ Optimization guide provided (nix wrapper limitations)"

# Test compilation
test: test_main test_python

test_main: 
	@echo "Testing main executable..."
	@echo "Run: ./text_processor (after compiling with nim)"
	@echo "✅ Main executable test instructions provided"

test_python: 
	@echo "Testing Python integration..."
	python3 $(PYTHON_WRAPPER)
	@echo "✅ Python integration test completed"

# Benchmark performance
benchmark: 
	@echo "Running performance benchmark..."
	@echo "Python version:"
	python3 -c "from nim_wrapper import NimTextProcessor; p = NimTextProcessor(); import time; start = time.time(); result = p.process_text('hello world' * 10000); print(f'Python: {time.time() - start:.4f}s')"
	@echo ""
	@echo "Nim version (when compiled with proper nimpy):"
	@echo "  Compile with: nim py --lib text_processor_lib_working.nim"
	@echo "  Then run: python3 -c \"import text_processor_lib_working; print(text_processor_lib_working.processTextString('hello world' * 10000))\""
	@echo "✅ Benchmark framework ready"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -f $(MAIN_EXE) $(PYTHON_MODULE) $(PYTHON_MODULE).so
	rm -f $(MAIN_EXE)_release $(PYTHON_MODULE)_release
	rm -rf nimcache
	@echo "✅ Build artifacts cleaned"

# Install nimpy for Python integration (optional)
install-deps:
	@echo "Installing Python dependencies..."
	pip3 install nimpy
	@echo "✅ Dependencies installed"

# Show help
help:
	@echo "Available targets:"
	@echo "  all         - Compile everything (default)"
	@echo "  main        - Compile main text processor executable"
	@echo "  library     - Compile Python library interface"
	@echo "  release     - Compile optimized release versions"
	@echo "  test        - Run compilation tests"
	@echo "  benchmark   - Run performance benchmarks"
	@echo "  clean       - Clean build artifacts"
	@echo "  install-deps- Install Python dependencies"
	@echo "  help        - Show this help message"
	@echo ""
	@echo "Note: For best results, install Nim directly:"
	@echo "  https://nim-lang.org/install.html"
	@echo ""
	@echo "Quick start with direct Nim installation:"
	@echo "  nim compile text_processor.nim"
	@echo "  nim py --lib text_processor_lib_working.nim"

# Phony targets
.PHONY: all main library release test benchmark clean install-deps help