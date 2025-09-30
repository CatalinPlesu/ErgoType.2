# ErgoType/src/data/README.md

## Data Directory

Contains all data assets for keyboard optimization.

### Structure
- `keyboards/` - KLE JSON files for physical keyboard layouts
- `languages/` - Language-specific configuration files
- `text/raw/` - Raw text files from scrapers (not committed due to size)
- `text/processed/` - Processed corpus data 

### Data Flow
1. Raw text collected by scrapers → `text/raw/`
2. Processors transform raw → `text/processed/` 
3. Application uses processed data for optimization

### File Formats
- **KLE files**: Keyboard Layout Editor format with finger/hand annotations
    - https://keyboard-layout-editor.com/
- **Processed text**: Pickle/JSON files with frequency statistics
- **Language configs**: YAML/JSON with diacritic mappings and weights
