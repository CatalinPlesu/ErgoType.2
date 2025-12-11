# Distributed GA Path Handling

## Overview

The distributed Genetic Algorithm (GA) system uses RabbitMQ to distribute fitness evaluation jobs across multiple worker nodes. To support workers on different machines with different filesystem layouts, the system uses **relative paths** when transmitting configuration over the network.

## Problem

Previously, the master node would send absolute file paths (e.g., `/home/user/ErgoType.2/src/data/keyboards/ansi_60_percent.json`) to worker nodes. This caused issues when:
- Workers were on different machines
- Workers had the repository cloned to different locations
- Workers used different operating systems (Linux vs Windows paths)

## Solution

The system now:
1. **Master node**: Converts absolute paths to relative paths before sending config
2. **Network transmission**: Only relative paths are sent over RabbitMQ
3. **Worker nodes**: Convert relative paths back to absolute based on their local PROJECT_ROOT

## Implementation Details

### Master Node (`ga.py`)

When the master pushes configuration to the job queue:

```python
# Push configuration with relative paths for distributed workers
config = {
    'keyboard_file': self._to_relative_path(self.keyboard_file),
    'text_file': self._to_relative_path(self.text_file),
    # ... other config
}
self.job_queue.push_config(config)
```

### Worker Node (`ga.py`)

When a worker receives configuration from the queue:

```python
# Update local config - convert relative paths to absolute
self.keyboard_file = self._to_absolute_path(current_config.get('keyboard_file'))
self.text_file = self._to_absolute_path(current_config.get('text_file'))
```

### Helper Methods

Two helper methods handle the conversion:

#### `_to_relative_path(absolute_path)`
- Converts an absolute path to a path relative to PROJECT_ROOT
- Used by master when pushing config
- Example: `/home/user/ErgoType.2/src/data/keyboards/ansi_60_percent.json` → `src/data/keyboards/ansi_60_percent.json`

#### `_to_absolute_path(relative_path)`
- Converts a relative path to an absolute path based on the local PROJECT_ROOT
- Used by workers when receiving config
- Returns the path unchanged if it's already absolute (backward compatibility)
- Example: `src/data/keyboards/ansi_60_percent.json` → `/opt/ergotype/src/data/keyboards/ansi_60_percent.json`

## Setup Requirements

For this to work correctly, all nodes (master and workers) must:

1. Have the repository cloned with the same directory structure
2. Have the data files in the same relative locations (`src/data/keyboards/`, `src/data/text/raw/`, etc.)
3. Set PROJECT_ROOT correctly (automatically handled in `ga.py`)

## Example Scenario

### Master Node Setup
```
Master machine:
  PROJECT_ROOT: /home/alice/projects/ErgoType.2/
  Files at:
    /home/alice/projects/ErgoType.2/src/data/keyboards/ansi_60_percent.json
    /home/alice/projects/ErgoType.2/src/data/text/raw/simple_wikipedia_dataset.txt
```

### Worker Node Setup (Different Machine)
```
Worker machine:
  PROJECT_ROOT: /opt/ergotype/
  Files at:
    /opt/ergotype/src/data/keyboards/ansi_60_percent.json
    /opt/ergotype/src/data/text/raw/simple_wikipedia_dataset.txt
```

### Configuration Transmission

1. Master converts to relative paths:
   - `keyboard_file: src/data/keyboards/ansi_60_percent.json`
   - `text_file: src/data/text/raw/simple_wikipedia_dataset.txt`

2. Config sent over RabbitMQ (portable across machines)

3. Worker converts to its local absolute paths:
   - `keyboard_file: /opt/ergotype/src/data/keyboards/ansi_60_percent.json`
   - `text_file: /opt/ergotype/src/data/text/raw/simple_wikipedia_dataset.txt`

## Testing

Two test files verify the path handling:

### `tests/path_conversion_test.py`
Tests the basic path conversion methods in isolation.

### `tests/distributed_path_test.py`
Simulates a complete distributed scenario with master and worker on different machines.

Run tests:
```bash
python tests/path_conversion_test.py
python tests/distributed_path_test.py
```

## Backward Compatibility

The implementation is backward compatible:
- If a path is already absolute, `_to_absolute_path()` returns it unchanged
- Single-machine setups (master processing its own jobs) work without changes
- In-memory queue (when RabbitMQ is unavailable) continues to work

## Benefits

✅ Workers can be on any machine with any filesystem layout  
✅ No need to synchronize absolute paths across nodes  
✅ Works across different operating systems (Linux, Windows, macOS)  
✅ Configuration is portable and machine-independent  
✅ Easier to add/remove worker nodes dynamically  
