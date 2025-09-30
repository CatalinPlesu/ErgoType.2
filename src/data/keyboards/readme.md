# ErgoType/src/data/keyboards/README.md

## Keyboard Layouts

Collection of physical keyboard layout definitions in KLE (Keyboard Layout Editor) format.

### Source
Keyboard layouts can be obtained from:
- [keyboard-layout-editor.com](http://www.keyboard-layout-editor.com/) - Create and export custom layouts
- VIA keyboard repositories - Pre-made layouts for common keyboards
- QMK/ZMK firmware repositories - Open source keyboard configurations

### Format
All layouts use the KLE JSON format with additional annotations:
- `hand`: Left/Right/BOTH assignment for each key
- `finger`: Pinky/Ring/Middle/Index/Thumb assignment
- `homing`: Boolean indicating home row keys

### Processing
Raw KLE files require processing to add finger/hand annotations:
run `src/data_preparation/keyboards/keyboard_annotator_gui.py`
