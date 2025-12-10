# CLR Runtime Initialization Fix

## Problem

When running the Genetic Algorithm from the menu multiple times in the same application instance, users would encounter the following error:

```
❌ Error loading C# library: The runtime <clr_loader.hostfxr.DotnetCoreRuntime object at 0x...> has already been loaded
```

This prevented users from running multiple GA iterations without restarting the entire application.

## Root Cause

The `pythonnet` library, which bridges Python and .NET, only allows the CLR (Common Language Runtime) to be initialized once per Python process. The code was calling `set_runtime(get_coreclr())` in multiple places:

1. `src/core/run_ga.py` - in the `save_heuristic_layouts` function
2. `src/core/ga.py` - in the `_evaluate_individual_worker` function
3. `src/core/ga.py` - in the `_run_worker` method

Each time a user selected "Run GA" from the menu, these initialization calls would be executed again, causing the error on the second and subsequent runs.

## Solution

We created a centralized CLR runtime helper module (`src/core/clr_loader_helper.py`) that:

1. **Tracks initialization state**: Uses a module-level flag to remember if the runtime has already been initialized
2. **Provides safe initialization**: The `initialize_clr_runtime()` function can be called multiple times safely
3. **Handles errors gracefully**: Catches and handles the "already loaded" error if it occurs
4. **Provides a convenient loader**: The `load_csharp_fitness_library()` function combines runtime initialization with library loading

### Key Functions

#### `initialize_clr_runtime()`
Safely initializes the CLR runtime. Returns `True` on first call (when it actually initializes), `False` on subsequent calls.

```python
from core.clr_loader_helper import initialize_clr_runtime

was_initialized = initialize_clr_runtime()
if was_initialized:
    print("Runtime initialized for the first time")
else:
    print("Runtime already initialized, skipped")
```

#### `load_csharp_fitness_library(project_root=None, assembly_name=None)`
Initializes the runtime (if needed) and loads the C# KeyboardFitness library.

```python
from core.clr_loader_helper import load_csharp_fitness_library

Fitness, was_newly_initialized = load_csharp_fitness_library()
# Use Fitness class for calculations
```

#### `is_runtime_initialized()`
Checks if the runtime has been initialized.

```python
from core.clr_loader_helper import is_runtime_initialized

if is_runtime_initialized():
    print("Runtime is ready")
```

## Migration Guide

### Before (Old Code)
```python
from pythonnet import set_runtime
from clr_loader import get_coreclr
set_runtime(get_coreclr())
import clr

dll_dir = os.path.join(PROJECT_ROOT, "cs", "bin", "Release", "net9.0")
sys.path.insert(0, dll_dir)
clr.AddReference("KeyboardFitness")
from FitnessNet import Fitness
```

### After (New Code)
```python
from core.clr_loader_helper import load_csharp_fitness_library

Fitness, _ = load_csharp_fitness_library(PROJECT_ROOT)
```

## Testing

The fix has been tested with:

1. **Unit tests**: Verified that multiple calls to `initialize_clr_runtime()` don't raise errors
2. **Integration tests**: Simulated loading the C# library multiple times
3. **End-to-end tests**: Simulated the user workflow of running GA from menu multiple times

All tests pass successfully, confirming that:
- The first initialization works correctly
- Subsequent initializations are safely skipped
- The C# library can be loaded multiple times without errors
- Users can now run the GA as many times as needed from the same application instance

## Benefits

✅ **No more runtime errors**: Users can run the GA multiple times without restarting
✅ **Better user experience**: Seamless workflow from the menu
✅ **Cleaner code**: Centralized initialization logic
✅ **Maintainable**: Single source of truth for CLR runtime management
✅ **Extensible**: Can be used for other C# interop needs in the future

## Implementation Details

### Error Handling

The helper catches specific exception types (`RuntimeError`, `ValueError`) and checks if the error message indicates the runtime is already loaded. This is more robust than the previous approach.

```python
try:
    set_runtime(get_coreclr())
    _runtime_initialized = True
    return True
except (RuntimeError, ValueError) as e:
    error_msg = str(e).lower()
    if "already" in error_msg and ("loaded" in error_msg or "set" in error_msg):
        _runtime_initialized = True
        return False
    raise
```

### Configuration

The assembly name is now configurable via the `DEFAULT_ASSEMBLY_NAME` constant, making it easier to adapt for other C# assemblies if needed.

## Related Files

- `src/core/clr_loader_helper.py` - The new helper module
- `src/core/ga.py` - Updated to use the helper
- `src/core/run_ga.py` - Updated to use the helper
