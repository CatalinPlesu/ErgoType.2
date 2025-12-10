"""
Helper module for safely initializing the CLR runtime.

The pythonnet library only allows set_runtime() to be called once per Python process.
This module provides a safe way to initialize the runtime that can be called multiple times
without raising errors.
"""

import sys
import os

# Constants
DEFAULT_ASSEMBLY_NAME = "KeyboardFitness"

# Flag to track if runtime has been initialized
_runtime_initialized = False


def initialize_clr_runtime():
    """
    Safely initialize the CLR runtime.
    
    This function can be called multiple times safely. It will only initialize
    the runtime on the first call. Subsequent calls will be no-ops.
    
    Returns:
        bool: True if runtime was initialized (first call), False if already initialized
    """
    global _runtime_initialized
    
    if _runtime_initialized:
        return False
    
    try:
        from pythonnet import set_runtime
        from clr_loader import get_coreclr
        set_runtime(get_coreclr())
        _runtime_initialized = True
        return True
    except (RuntimeError, ValueError) as e:
        # If the runtime is already set by another mechanism, that's okay
        # Check for common error messages that indicate the runtime is already loaded
        error_msg = str(e).lower()
        if "already" in error_msg and ("loaded" in error_msg or "set" in error_msg):
            _runtime_initialized = True
            return False
        # Re-raise if it's a different error
        raise
    except Exception:
        # Re-raise any other unexpected exceptions
        raise


def load_csharp_fitness_library(project_root=None, assembly_name=None):
    """
    Load the C# KeyboardFitness library after ensuring runtime is initialized.
    
    Args:
        project_root: Path to project root. If None, will be auto-detected.
        assembly_name: Name of the C# assembly to load. If None, uses DEFAULT_ASSEMBLY_NAME.
    
    Returns:
        tuple: (Fitness class, was_newly_initialized)
    """
    # Initialize runtime first
    was_newly_initialized = initialize_clr_runtime()
    
    # Now import clr (safe to do after runtime is set)
    import clr
    
    # Determine project root if not provided
    if project_root is None:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Add DLL directory to path
    dll_dir = os.path.join(project_root, "cs", "bin", "Release", "net9.0")
    if dll_dir not in sys.path:
        sys.path.insert(0, dll_dir)
    
    # Load the C# assembly
    if assembly_name is None:
        assembly_name = DEFAULT_ASSEMBLY_NAME
    clr.AddReference(assembly_name)
    
    # Import and return the Fitness class
    from FitnessNet import Fitness
    
    return Fitness, was_newly_initialized


def is_runtime_initialized():
    """
    Check if the CLR runtime has been initialized.
    
    Returns:
        bool: True if runtime is initialized, False otherwise
    """
    return _runtime_initialized
