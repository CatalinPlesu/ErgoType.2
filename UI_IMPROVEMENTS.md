# UI Improvements - ErgoType.2

This document describes the user interface improvements made to the ErgoType.2 Keyboard Layout Optimization System.

## Overview

The UI has been completely redesigned using the `rich` library to provide a modern, colorful, and user-friendly terminal interface with persistent preferences.

## Key Features

### 1. **Rich Terminal UI**

The application now uses the `rich` library for enhanced terminal output:
- **Colored menus** with emojis for better visual organization
- **Formatted tables** for displaying options and data
- **Status messages** with color-coded icons (✓, ℹ, ⚠, ✗)
- **Panels and boxes** for configuration display
- **Professional styling** with consistent color schemes

### 2. **Persistent User Preferences**

All user choices are now automatically saved to a JSON configuration file (`~/.ergotype_config.json`):

#### Saved Preferences Include:
- Last selected keyboard layout
- Last selected text file
- GA parameters (population size, max iterations, etc.)
- Worker configuration (RabbitMQ settings, max processes)

#### Benefits:
- **Quick workflow**: Press Enter to use saved values
- **No repetitive input**: Previous choices are remembered
- **Flexible editing**: Values can be changed when needed
- **Session persistence**: Settings survive between runs

### 3. **Improved Menu System**

The main menu now features:
- Numbered options with intuitive icons
- Clear, descriptive titles
- Easy navigation with number keys
- Visual feedback for selections

```
       🎹 Keyboard Layout Optimization - Main Menu       
╭──────┬────────────────────────────────────────────────╮
│    # │ Option                                         │
├──────┼────────────────────────────────────────────────┤
│    1 │ 🚀 Run Genetic Algorithm (Master Mode)         │
│    2 │ 🔧 Run as Worker Node (Distributed Processing) │
│    3 │ ⌨️  Evaluate Keyboard Layout                    │
│    4 │ 📊 Compare Standard Layouts                    │
│    5 │ 📝 Analyze Text File                           │
│    6 │ 🎨 Visualize Keyboard Layout                   │
│    7 │ 🖊️  Launch Keyboard Annotator GUI               │
│    0 │ Exit                                           │
╰──────┴────────────────────────────────────────────────╯
```

### 4. **Enhanced Selection Interface**

When selecting keyboards, text files, or other options:
- **Table format** showing all available options
- **File sizes** displayed for text files
- **Default highlighting** shows last used option in green
- **Quick confirmation** - press Enter to accept default
- **Easy cancellation** - exit at any point

Example:
```
     Available Text Files     
╭──────┬───────────┬─────────╮
│    # │ Name      │    Size │
├──────┼───────────┼─────────┤
│    1 │ Test File │ 0.00 MB │
╰──────┴───────────┴─────────╯
Last used: Test File (Option 1)
```

### 5. **Smart Parameter Input**

GA parameter configuration now features:
- **Default values** shown for each parameter
- **Range validation** to prevent invalid inputs
- **Type checking** (int, float, bool)
- **Helpful prompts** with valid ranges displayed
- **Saved defaults** from previous runs

Example workflow:
```
Step 3: Configure GA Parameters

Press Tab/Enter to use saved values or type new values

Population size [1-500] (30): ▊
```

### 6. **Configuration Preview**

Before running the GA or worker, the system displays a formatted configuration panel:

```
╭────────────────── Final Configuration ──────────────────╮
│                                                          │
│    Keyboard File           src/data/keyboards/...       │
│    Text File               src/data/text/raw/...        │
│    Population Size         30                           │
│    Max Iterations          50                           │
│    Stagnant Limit          10                           │
│    Max Processes           4                            │
│    Fitts A                 0.50                         │
│    Fitts B                 0.30                         │
│    Use Rabbitmq            ✓                            │
│                                                          │
╰──────────────────────────────────────────────────────────╯

Start Genetic Algorithm? [Y/n]:
```

### 7. **Color-Coded Status Messages**

The system now provides clear visual feedback:
- ✓ **Green checkmarks** for successful operations
- ℹ **Blue info icons** for informational messages
- ⚠ **Yellow warning icons** for warnings
- ✗ **Red error icons** for errors

### 8. **Enhanced GA Execution Output**

The `run_ga.py` module now uses rich formatting for:
- **Startup configuration** display in a clean table
- **Progress indicators** with colors
- **Completion summary** with formatted results
- **Fallback support** - works without rich if unavailable

## Technical Implementation

### New Modules

1. **`src/ui/preferences.py`**
   - Manages user preferences
   - Handles JSON serialization/deserialization
   - Provides convenience methods for common settings
   - Stores config in user's home directory

2. **`src/ui/rich_menu.py`**
   - Implements rich-based menu system
   - Provides helper functions for UI elements
   - Handles user input with validation
   - Supports table rendering and panels

### Updated Modules

1. **`main.py`**
   - Migrated from simple Menu class to RichMenu
   - Integrated preferences system
   - Enhanced all menu item functions
   - Added step-by-step workflows

2. **`src/core/run_ga.py`**
   - Added rich output formatting
   - Maintained backward compatibility
   - Enhanced visual feedback during execution

3. **`pyproject.toml`**
   - Added `rich>=13.0.0` dependency

## Usage Examples

### First-Time User
1. Run the application: `python3 main.py`
2. Select option 1 (Run Genetic Algorithm)
3. Choose a keyboard layout from the list
4. Choose a text file from the list
5. Configure GA parameters
6. Confirm and run

### Returning User
1. Run the application: `python3 main.py`
2. Select option 1
3. Press Enter to accept the last keyboard layout
4. Press Enter to accept the last text file
5. Press Enter for each parameter to use saved values
6. Confirm and run

The system remembers all previous choices!

### Resetting Preferences

To clear saved preferences, delete the config file:
```bash
rm ~/.ergotype_config.json
```

Or use the preferences API:
```python
from ui.preferences import Preferences
prefs = Preferences()
prefs.clear()
```

## Benefits Summary

✅ **Faster workflow** - saved preferences reduce repetitive input
✅ **Better UX** - colorful, organized, professional appearance
✅ **Clear feedback** - visual status indicators
✅ **Easier to use** - intuitive navigation and prompts
✅ **Less error-prone** - validation and range checking
✅ **More professional** - modern terminal UI with rich formatting
✅ **Backward compatible** - falls back gracefully without rich library

## Screenshots

Main Menu:
```
       🎹 Keyboard Layout Optimization - Main Menu       
╭──────┬────────────────────────────────────────────────╮
│    # │ Option                                         │
├──────┼────────────────────────────────────────────────┤
│    1 │ 🚀 Run Genetic Algorithm (Master Mode)         │
│    2 │ 🔧 Run as Worker Node (Distributed Processing) │
│    3 │ ⌨️  Evaluate Keyboard Layout                    │
│    4 │ 📊 Compare Standard Layouts                    │
│    5 │ 📝 Analyze Text File                           │
│    6 │ 🎨 Visualize Keyboard Layout                   │
│    7 │ 🖊️  Launch Keyboard Annotator GUI               │
│    0 │ Exit                                           │
╰──────┴────────────────────────────────────────────────╯
```

## Future Enhancements

Potential improvements for future versions:
- Progress bars for long-running operations
- Live updates during GA execution
- Interactive parameter tuning with sliders
- Graph visualization in terminal
- Export/import configuration profiles
- Multiple saved configuration presets
