import dearpygui.dearpygui as dpg
import json
import json5  # pip install json5
import os
# Import your classes - using the single consolidated module
from src.domain.keyboard import *

# --- Configuration ---
# Define the default directory for keyboard layouts
DEFAULT_KEYBOARD_DIR = os.path.join(
    os.path.dirname(__file__), "../../data", "keyboards")
# --- End Configuration ---


class KeyboardAnnotatorDPG:
    def __init__(self):
        self.keyboard = None
        self.current_file_path = None
        self.selected_key_index = None
        self.dirty = False  # Flag to indicate unsaved changes
        self.paint_mode = False
        self.current_finger = "UNKNOWN"
        self.current_hand = "UNKNOWN"
        self.current_homing = False
        self.key_buttons = []  # Track key button tags for updates
        self.sticky_finger = False
        self.sticky_hand = False
        self.sticky_homing = False
        self.key_bounds = []  # For draw_list click detection
        self.keyboard_drawlist = None  # Reference to draw list
        self.scale = 1
        self.min_x = 0
        self.min_y = 0

    def load_keyboard_callback(self, sender, app_data, user_data):
        """Callback for the Load menu item."""
        if app_data and 'file_path_name' in app_data:
            file_path = app_data['file_path_name']
            try:
                with open(file_path, 'r') as f:
                    data = json5.load(f)

                self.keyboard = Serial.deserialize(data)
                self.current_file_path = file_path
                self.selected_key_index = None
                self.dirty = False
                dpg.set_value("file_path_text", f"Loaded: { os.path.basename(file_path)}")
                print(f"Successfully loaded keyboard from {file_path}")
                # Show success message
                dpg.set_value("status_text", f"Loaded: { os.path.basename(file_path)}")
                dpg.configure_item("status_text", color=[0, 255, 0])  # Green

                # Clear inspector
                self.clear_inspector()

                # Render keyboard preview
                self.render_keyboard_preview()

            except Exception as e:
                error_msg = f"Failed to load keyboard: {e}"
                print(error_msg)
                dpg.set_value("status_text", error_msg)
                dpg.configure_item("status_text", color=[255, 0, 0])  # Red

    def show_load_dialog(self, sender, app_data, user_data):
        """Show the load file dialog"""
        dpg.show_item("load_file_dialog")

    def show_save_dialog(self, sender, app_data, user_data):
        """Show the save file dialog"""
        if not self.keyboard:
            # If no keyboard is loaded, inform the user and do nothing
            dpg.set_value("status_text", "No keyboard layout loaded.")
            dpg.configure_item("status_text", color=[255, 165, 0])  # Orange
            print("Save As: No keyboard loaded.")
            return  # Early return, don't show dialog

        # If a keyboard is loaded, proceed to show the save dialog
        dpg.show_item("save_file_dialog")

    def save_dialog_callback(self, sender, app_data, user_data):
        """Callback when the save file dialog is confirmed."""
        if app_data and 'file_path_name' in app_data:
            file_path = app_data['file_path_name']
            # Ensure .json extension
            if not file_path.endswith('.json'):
                file_path += '.json'
            try:
                # Load original structure
                if not self.current_file_path:
                    raise ValueError(
                        "Original file path unknown. Please load from a file first.")

                with open(self.current_file_path, 'r') as f:
                    original_rows = json5.load(f)

                # Create a copy to modify
                modified_rows = self.deep_copy_structure(original_rows)

                # --- Inject Properties Logic ---
                key_counter = [0]  # Use list for mutability in nested function

                def inject_properties(rows):
                    align = 4
                    for r_idx, row in enumerate(rows):
                        if isinstance(row, list):
                            new_row = []
                            local_k_idx = 0
                            for item_in_row in row:
                                if isinstance(item_in_row, dict):
                                    if local_k_idx != 0 and ("r" in item_in_row or "rx" in item_in_row or "ry" in item_in_row):
                                        pass  # Parser handles error, we just copy
                                    if "a" in item_in_row:
                                        align = item_in_row["a"]
                                    new_row.append(item_in_row)
                                elif isinstance(item_in_row, str):
                                    if key_counter[0] < len(self.keyboard.keys):
                                        annotated_key = self.keyboard.keys[key_counter[0]]
                                        has_annotations = (
                                            annotated_key.finger != Finger.UNKNOWN or
                                            annotated_key.hand != Hand.UNKNOWN or
                                            annotated_key.homing != False
                                        )
                                        prop_dict_to_add = {}
                                        if annotated_key.finger != Finger.UNKNOWN:
                                            prop_dict_to_add["finger"] = annotated_key.finger.name
                                        if annotated_key.hand != Hand.UNKNOWN:
                                            prop_dict_to_add["hand"] = annotated_key.hand.name
                                        if annotated_key.homing:
                                            prop_dict_to_add["homing"] = annotated_key.homing

                                        if has_annotations:
                                            if new_row and isinstance(new_row[-1], dict):
                                                # Merge into existing prop dict
                                                # Create a copy to avoid modifying the original during iteration
                                                updated_props = new_row[-1].copy()
                                                updated_props.update(
                                                    prop_dict_to_add)
                                                new_row[-1] = updated_props
                                            else:
                                                # Prepend the new property dict
                                                # Append a copy
                                                new_row.append(
                                                    prop_dict_to_add.copy())

                                        new_row.append(item_in_row)
                                        key_counter[0] += 1
                                    else:
                                        new_row.append(item_in_row)
                                    local_k_idx += 1
                                else:
                                    new_row.append(item_in_row)
                            modified_rows[r_idx] = new_row
                        elif isinstance(row, dict):
                            modified_rows[r_idx] = row
                # --- End Inject Properties Logic ---

                inject_properties(modified_rows)

                with open(file_path, 'w') as f:
                    json.dump(modified_rows, f, indent=2)

                self.dirty = False
                dpg.set_value("file_path_text", f"Saved: { os.path.basename(file_path)}")
                print(f"Successfully saved annotated keyboard to {file_path}")
                dpg.set_value("status_text", f"Saved: { os.path.basename(file_path)}")
                dpg.configure_item("status_text", color=[0, 255, 0])  # Green

            except Exception as e:
                error_msg = f"Failed to save keyboard: {e}"
                print(error_msg)
                dpg.set_value("status_text", error_msg)
                dpg.configure_item("status_text", color=[255, 0, 0])  # Red

    def update_inspector_view(self):
        """Populates the inspector with the selected key's details."""
        if self.selected_key_index is not None and self.keyboard:
            key = self.keyboard.keys[self.selected_key_index]
            dpg.configure_item("inspector_group", show=True)
            dpg.set_value("key_info_text", f"Editing Key { self.selected_key_index}: {key.labels[0] or '(No Label)'}")
            dpg.set_value("finger_combo", key.finger.name)
            dpg.set_value("hand_combo", key.hand.name)
            dpg.set_value("homing_checkbox", key.homing)
        else:
            self.clear_inspector()

    def clear_inspector(self):
        """Hides the inspector widgets."""
        dpg.configure_item("inspector_group", show=False)
        dpg.set_value("key_info_text", "Click a key to edit")

    def deep_copy_structure(self, obj):
        """Creates a deep copy of lists and dicts."""
        if isinstance(obj, list):
            return [self.deep_copy_structure(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self.deep_copy_structure(v) for k, v in obj.items()}
        else:
            return obj

    def toggle_sticky_finger(self, sender, app_data, user_data):
        """Toggle sticky finger mode"""
        self.sticky_finger = not self.sticky_finger
        dpg.set_value("sticky_finger_btn",
                      "LOCKED FINGER" if self.sticky_finger else "FINGER")
        self.update_status_sticky()

    def toggle_sticky_hand(self, sender, app_data, user_data):
        """Toggle sticky hand mode"""
        self.sticky_hand = not self.sticky_hand
        dpg.set_value("sticky_hand_btn",
                      "LOCKED HAND" if self.sticky_hand else "HAND")
        self.update_status_sticky()

    def toggle_sticky_homing(self, sender, app_data, user_data):
        """Toggle sticky homing mode"""
        self.sticky_homing = not self.sticky_homing
        dpg.set_value("sticky_homing_btn",
                      "LOCKED HOMING" if self.sticky_homing else "HOMING")
        self.update_status_sticky()

    def update_status_sticky(self):
        """Update status text with sticky mode info"""
        sticky_modes = []
        if self.sticky_finger:
            sticky_modes.append(f"Finger: {dpg.get_value('paint_finger_combo')}")
        if self.sticky_hand:
            sticky_modes.append(f"Hand: {dpg.get_value('paint_hand_combo')}")
        if self.sticky_homing:
            sticky_modes.append("Homing")

        if sticky_modes:
            dpg.set_value("status_text", f"Sticky Mode: { ' | '.join(sticky_modes)}")
            dpg.configure_item("status_text", color=[255, 255, 0])
        else:
            dpg.set_value(
                "status_text", "Ready - Click keys to assign attributes")
            dpg.configure_item("status_text", color=[255, 255, 255])

    def paint_key_callback(self, sender, app_data, user_data):
        """Callback when a key is clicked"""
        if not self.keyboard:
            return

        key_index = user_data
        key = self.keyboard.keys[key_index]

        changes_made = False

        # Apply sticky attributes
        if self.sticky_finger:
            current_finger = dpg.get_value("paint_finger_combo")
            key.finger = Finger[current_finger]
            changes_made = True

        if self.sticky_hand:
            current_hand = dpg.get_value("paint_hand_combo")
            key.hand = Hand[current_hand]
            changes_made = True

        if self.sticky_homing:
            current_homing = dpg.get_value("paint_homing_checkbox")
            key.homing = current_homing
            changes_made = True

        # Update color if changes were made
        if changes_made:
            self.dirty = True
            # Update the specific key's color immediately
            self.update_single_key_color(key_index)

            dpg.set_value( "status_text", f"Applied attributes to key {key_index}")
            dpg.configure_item("status_text", color=[0, 255, 0])

        # If no sticky modes are active, select the key for inspection
        if not any([self.sticky_finger, self.sticky_hand, self.sticky_homing]):
            self.selected_key_index = key_index
            self.update_inspector_view()

            dpg.set_value("status_text", f"Selected key {key_index}: { key.labels[0] or '(No Label)'}")
            dpg.configure_item("status_text", color=[255, 255, 255])
            return

    def apply_changes_callback(self, sender, app_data, user_data):
        """Callback for the Apply Changes button."""
        if self.selected_key_index is not None and self.keyboard:
            try:
                key = self.keyboard.keys[self.selected_key_index]
                # Get values from DPG widgets
                finger_name = dpg.get_value("finger_combo")
                hand_name = dpg.get_value("hand_combo")
                homing_state = dpg.get_value("homing_checkbox")

                # Update Key object
                key.finger = Finger[finger_name]
                key.hand = Hand[hand_name]
                key.homing = homing_state

                self.dirty = True  # Mark as changed

                # Update key color immediately
                self.update_single_key_color(self.selected_key_index)

                # Update inspector (in case repr changes or confirmation is needed)
                self.update_inspector_view()

                print(f"Applied changes to key {self.selected_key_index}")
                dpg.set_value("status_text", f"Applied changes to key { self.selected_key_index}")
                dpg.configure_item("status_text", color=[0, 255, 0])  # Green

            except Exception as e:
                error_msg = f"Failed to apply changes: {e}"
                print(error_msg)
                dpg.set_value("status_text", error_msg)
                dpg.configure_item("status_text", color=[255, 0, 0])  # Red

    def clear_key_callback(self, sender, app_data, user_data):
        """Clear attributes from selected key"""
        if self.selected_key_index is not None and self.keyboard:
            key = self.keyboard.keys[self.selected_key_index]
            key.finger = Finger.UNKNOWN
            key.hand = Hand.UNKNOWN
            key.homing = False

            self.dirty = True
            self.update_inspector_view()

            # Update key color
            self.update_single_key_color(self.selected_key_index)

            dpg.set_value("status_text", f"Cleared attributes from key { self.selected_key_index}")
            dpg.configure_item("status_text", color=[0, 255, 0])

    def render_keyboard_preview(self):
        """Render the keyboard preview with colored rectangles using draw_list"""
        if not self.keyboard:
            return

        # Clear previous preview
        dpg.delete_item("keyboard_preview_group", children_only=True)
        self.key_buttons = []
        self.key_bounds = []  # Store bounds for click detection

        # Create container group
        with dpg.group(parent="keyboard_preview_group"):
            try:
                # Calculate keyboard bounds
                positions_x = [key.x for key in self.keyboard.keys]
                positions_y = [key.y for key in self.keyboard.keys]
                sizes_x = [key.x + key.width for key in self.keyboard.keys]
                sizes_y = [key.y + key.height for key in self.keyboard.keys]

                if not positions_x:  # Handle empty keyboard
                    return

                self.min_x = min(positions_x)
                self.min_y = min(positions_y)
                max_x = max(sizes_x)
                max_y = max(sizes_y)

                # Add padding
                padding = 0.5
                self.min_x -= padding
                self.min_y -= padding
                max_x += padding
                max_y += padding

                # Calculate scaling
                preview_width = 900
                preview_height = 500
                scale_x = preview_width / \
                    (max_x - self.min_x) if (max_x - self.min_x) > 0 else 1
                scale_y = preview_height / \
                    (max_y - self.min_y) if (max_y - self.min_y) > 0 else 1
                self.scale = min(scale_x, scale_y, 30)

                # Create draw list
                self.keyboard_drawlist = dpg.add_drawlist(
                    width=preview_width, height=preview_height)

                # Draw keys as colored rectangles
                for i, key in enumerate(self.keyboard.keys):
                    try:
                        # Calculate position and size
                        x = (key.x - self.min_x) * self.scale
                        y = (key.y - self.min_y) * self.scale
                        width = max(key.width * self.scale, 25)
                        height = max(key.height * self.scale, 25)

                        # Store bounds for click detection
                        self.key_bounds.append({
                            'index': i,
                            'x1': x, 'y1': y,
                            'x2': x + width, 'y2': y + height
                        })

                        # Get colors based on key attributes
                        bg_color, border_color, homing_symbol = self.get_key_visuals(
                            key)

                        # Validate coordinates
                        if not (0 <= x <= preview_width and 0 <= y <= preview_height):
                            continue
                        if width <= 0 or height <= 0:
                            continue

                        # Draw filled rectangle with colored border
                        dpg.draw_rectangle([x, y], [x + width, y + height],
                                           color=border_color, fill=bg_color, thickness=3,
                                           parent=self.keyboard_drawlist, tag=f"key_rect_{i}")

                        # --- FIXED: Create homing symbol for ALL keys, control visibility ---
                        center_x = x + width / 2
                        center_y = y + height / 2
                        symbol_radius = min(width, height) / 6
                        # Create the circle for EVERY key, but set initial visibility with 'show'
                        dpg.draw_circle([center_x, center_y], symbol_radius,
                                        color=[0, 0, 0, 255], fill=[255, 255, 255, 255],
                                        thickness=2, parent=self.keyboard_drawlist,
                                        tag=f"homing_{i}", show=homing_symbol)
                        # --- END FIXED SECTION ---

                        # Draw key label
                        label = key.labels[0] if key.labels[0] else ""
                        if len(label) > 6:
                            label = label[:4] + "..."

                        # Center text in rectangle (simple approach)
                        text_x = x + width/2 - len(label) * 2
                        text_y = y + height/2 - 6

                        # Ensure text is within bounds
                        text_x = max(
                            x + 2, min(text_x, x + width - len(label) * 4))
                        text_y = max(y + 2, min(text_y, y + height - 12))

                        dpg.draw_text([text_x, text_y], label, size=10,
                                      color=[0, 0, 0, 255], parent=self.keyboard_drawlist, tag=f"key_text_{i}")

                    except Exception as e:
                        print(f"Warning: Could not draw key {i}: {e}")
                        continue

                # Add mouse click handler
                with dpg.item_handler_registry(tag=f"mouse_handler_reg_{id(self)}"):
                    dpg.add_item_clicked_handler(
                        callback=self.on_keyboard_click)
                dpg.bind_item_handler_registry(
                    self.keyboard_drawlist, f"mouse_handler_reg_{id(self)}")

            except Exception as e:
                print(f"Error creating keyboard preview: {e}")
                dpg.add_text("Error loading keyboard preview",
                             color=[255, 0, 0])

    def on_keyboard_click(self, sender, app_data):
        """Handle clicks on the keyboard drawlist"""
        if not self.keyboard or not hasattr(self, 'key_bounds') or not self.key_bounds:
            return

        try:
            # Get mouse position in global coordinates
            mouse_pos = dpg.get_mouse_pos()

            # Get the position of the drawlist relative to the viewport
            drawlist_pos = dpg.get_item_pos(self.keyboard_drawlist)

            # Get the position of the parent window (Primary Window)
            primary_window_pos = dpg.get_item_pos("Primary Window")

            # Get the position of the preview group relative to its parent
            preview_group_pos = dpg.get_item_pos("keyboard_preview_group")

            # Calculate the absolute position of the drawlist
            # It's: primary_window + preview_group + drawlist_pos
            absolute_drawlist_x = primary_window_pos[0] + \
                preview_group_pos[0] + drawlist_pos[0]
            absolute_drawlist_y = primary_window_pos[1] + \
                preview_group_pos[1] + drawlist_pos[1]

            if mouse_pos and len(mouse_pos) >= 2:
                # Calculate relative mouse position within the drawlist
                relative_x = mouse_pos[0] - absolute_drawlist_x
                relative_y = mouse_pos[1] - absolute_drawlist_y

                # Debug output (you can remove this after testing)
                # print(f"Mouse: {mouse_pos}, Drawlist: {absolute_drawlist_x}, {absolute_drawlist_y}, Relative: {relative_x}, {relative_y}")

                # Check which key was clicked
                for bounds in reversed(self.key_bounds):  # Check topmost first
                    if (bounds['x1'] <= relative_x <= bounds['x2'] and
                            bounds['y1'] <= relative_y <= bounds['y2']):
                        self.paint_key_callback(None, None, bounds['index'])
                        return
        except Exception as e:
            print(f"Error handling mouse click: {e}")
            pass  # Handle case where positions can't be determined

    def update_key_colors(self):
        """Update colors of all key rectangles"""
        if not self.keyboard or not hasattr(self, 'keyboard_drawlist'):
            return

        for i, key in enumerate(self.keyboard.keys):
            try:
                bg_color, border_color, homing_symbol = self.get_key_visuals(
                    key)
                rect_tag = f"key_rect_{i}"
                if dpg.does_item_exist(rect_tag):
                    dpg.configure_item(
                        rect_tag, fill=bg_color, color=border_color)

                # Update homing symbol visibility
                homing_tag = f"homing_{i}"
                if dpg.does_item_exist(homing_tag):
                    dpg.configure_item(homing_tag, show=homing_symbol)
            except Exception as e:
                print(f"Could not update color for key {i}: {e}")
                pass  # Key might not exist yet

    def update_single_key_color(self, key_index):
        """Update color of a single key"""
        if not self.keyboard or key_index >= len(self.keyboard.keys):
            return
        try:
            key = self.keyboard.keys[key_index]
            bg_color, border_color, homing_symbol = self.get_key_visuals(key)
            # For draw_list approach:
            if hasattr(self, 'keyboard_drawlist'):
                rect_tag = f"key_rect_{key_index}"
                if dpg.does_item_exist(rect_tag):
                    dpg.configure_item(
                        rect_tag, fill=bg_color, color=border_color)
                # Update homing symbol visibility - it should always exist now
                homing_tag = f"homing_{key_index}"
                if dpg.does_item_exist(homing_tag):
                    # Only update the visibility state
                    dpg.configure_item(homing_tag, show=homing_symbol)
                # --- REMOVED the 'elif homing_symbol:' block ---
                # It's no longer needed because the item is created in render_keyboard_preview
        except Exception as e:
            print(f"Could not update color for key {key_index}: {e}")

    def get_key_visuals(self, key):
        """Determine the background color, border color, and homing symbol for a key"""
        # Background color represents FINGER
        finger_colors = {
            Finger.THUMB: [255, 200, 150, 255],    # Light orange
            Finger.INDEX: [200, 255, 200, 255],    # Light green
            Finger.MIDDLE: [200, 240, 255, 255],   # Light blue
            Finger.RING: [240, 200, 255, 255],     # Light purple
            Finger.PINKY: [255, 200, 240, 255],    # Light pink
            Finger.UNKNOWN: [220, 220, 220, 255]   # Light gray
        }
        bg_color = finger_colors.get(key.finger, [220, 220, 220, 255])

        # Border color represents HAND
        hand_border_colors = {
            Hand.LEFT: [0, 100, 255, 255],        # Blue border
            Hand.RIGHT: [255, 50, 100, 255],      # Red border
            Hand.BOTH: [150, 50, 200, 255],       # Purple border
            Hand.UNKNOWN: [100, 100, 100, 255]    # Gray border
        }
        border_color = hand_border_colors.get(key.hand, [100, 100, 100, 255])

        # Homing is represented by a white circle symbol
        homing_symbol = key.homing

        return bg_color, border_color, homing_symbol

    def run(self):
        """Creates the DPG context, UI, and starts the event loop."""
        dpg.create_context()

        # --- Create File Dialogs ---
        # --- Ensure default directory exists or use fallback ---
        load_dir = DEFAULT_KEYBOARD_DIR if os.path.isdir(
            DEFAULT_KEYBOARD_DIR) else "."
        save_dir = DEFAULT_KEYBOARD_DIR if os.path.isdir(
            DEFAULT_KEYBOARD_DIR) else "."

        # Load Dialog - FIXED: Added missing closing parenthesis
        with dpg.file_dialog(directory_selector=False, show=False, callback=self.load_keyboard_callback, tag="load_file_dialog", width=700, height=400, default_path=load_dir):
            dpg.add_file_extension(".json", color=(
                255, 255, 0, 255))  # Yellow for .json
            dpg.add_file_extension(".*")

        # Save Dialog - FIXED: Added missing closing parenthesis
        with dpg.file_dialog(directory_selector=False, show=False, callback=self.save_dialog_callback, tag="save_file_dialog", width=700, height=400, default_path=save_dir):
            dpg.add_file_extension(".json", color=(
                255, 255, 0, 255))  # Yellow for .json

        # --- Create Main Window ---
        with dpg.window(tag="Primary Window", width=1400, height=900):
            # Top button bar (instead of menu)
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="📁 Load Layout", callback=self.show_load_dialog, width=120, height=30)
                dpg.add_button(
                    label="💾 Save As", callback=self.show_save_dialog, width=120, height=30)
                dpg.add_separator()

            # Status Bar
            with dpg.group(horizontal=True):
                dpg.add_text("Status:", tag="status_label",
                             color=[200, 200, 200])
                dpg.add_text("Ready - Load a keyboard layout to begin",
                             tag="status_text", color=[255, 255, 255])

            # File Info
            dpg.add_text("No file loaded", tag="file_path_text",
                         color=[150, 150, 150])
            dpg.add_separator()

            # Main layout - horizontal split
            with dpg.group(horizontal=True):
                # Left panel - Controls
                with dpg.child_window(width=480, height=800):
                    dpg.add_text("🎨 STICKY PAINT CONTROLS",
                                 color=[255, 255, 100])
                    dpg.add_separator()

                    # Sticky controls section
                    with dpg.group():
                        dpg.add_text("Finger Assignment:",
                                     color=[255, 255, 255])
                        with dpg.group(horizontal=True):
                            dpg.add_combo(items=[f.name for f in Finger], tag="paint_finger_combo",
                                          default_value="INDEX", width=120)
                            sticky_finger_btn = dpg.add_button(label="FINGER", tag="sticky_finger_btn",
                                                               callback=self.toggle_sticky_finger, width=80)

                        dpg.add_spacer(height=5)

                        dpg.add_text("Hand Assignment:", color=[255, 255, 255])
                        with dpg.group(horizontal=True):
                            dpg.add_combo(items=[h.name for h in Hand], tag="paint_hand_combo",
                                          default_value="LEFT", width=120)
                            sticky_hand_btn = dpg.add_button(label="HAND", tag="sticky_hand_btn",
                                                             callback=self.toggle_sticky_hand, width=80)

                        dpg.add_spacer(height=5)

                        dpg.add_text("Homing Key:", color=[255, 255, 255])
                        with dpg.group(horizontal=True):
                            dpg.add_checkbox(
                                label="Enable", tag="paint_homing_checkbox")
                            sticky_homing_btn = dpg.add_button(label="HOMING", tag="sticky_homing_btn",
                                                               callback=self.toggle_sticky_homing, width=80)

                    dpg.add_separator()

                    # Instructions
                    with dpg.group():
                        dpg.add_text("🔧 INSTRUCTIONS", color=[100, 255, 100])
                        dpg.add_text("1. Click the attribute buttons above to enable 'sticky mode'",
                                     color=[200, 200, 200], wrap=450)
                        dpg.add_text("2. When sticky mode is ON (green), click keys to apply attributes",
                                     color=[200, 200, 200], wrap=450)
                        dpg.add_text("3. When sticky mode is OFF, click keys to select and edit individually",
                                     color=[200, 200, 200], wrap=450)
                        dpg.add_text("4. Use the inspector below for precise single-key editing",
                                     color=[200, 200, 200], wrap=450)

                    dpg.add_separator()

                    # Inspector Group (initially hidden)
                    with dpg.group(tag="inspector_group", show=False):
                        dpg.add_text("🔍 KEY INSPECTOR", color=[255, 200, 100])
                        dpg.add_text("Click a key to edit",
                                     tag="key_info_text", color=[255, 255, 255])
                        dpg.add_spacer(height=5)

                        dpg.add_text("Finger:", color=[255, 255, 255])
                        dpg.add_combo(
                            items=[f.name for f in Finger], tag="finger_combo", width=200)
                        dpg.add_spacer(height=5)

                        dpg.add_text("Hand:", color=[255, 255, 255])
                        dpg.add_combo(
                            items=[h.name for h in Hand], tag="hand_combo", width=200)
                        dpg.add_spacer(height=5)

                        dpg.add_checkbox(label="Homing Key",
                                         tag="homing_checkbox")
                        dpg.add_spacer(height=10)

                        with dpg.group(horizontal=True):
                            apply_button = dpg.add_button(
                                label="Apply Changes", callback=self.apply_changes_callback, width=120)
                            clear_button = dpg.add_button(
                                label="Clear", callback=self.clear_key_callback, width=80)

                    # Color legend
                    dpg.add_separator()
                    with dpg.group():
                        dpg.add_text("🎨 COLOR LEGEND", color=[200, 150, 255])
                        dpg.add_text("Background Colors = Fingers:",
                                     color=[255, 255, 255])
                        dpg.add_text("● Light Orange: Thumb",
                                     color=[255, 200, 150])
                        dpg.add_text("● Light Green: Index Finger",
                                     color=[200, 255, 200])
                        dpg.add_text("● Light Blue: Middle Finger",
                                     color=[200, 240, 255])
                        dpg.add_text("● Light Purple: Ring Finger",
                                     color=[240, 200, 255])
                        dpg.add_text("● Light Pink: Pinky",
                                     color=[255, 200, 240])
                        dpg.add_text("● Light Gray: Unassigned",
                                     color=[220, 220, 220])

                        dpg.add_spacer(height=5)
                        dpg.add_text("Border Colors = Hands:",
                                     color=[255, 255, 255])
                        dpg.add_text("● Blue Border: Left Hand",
                                     color=[0, 100, 255])
                        dpg.add_text("● Red Border: Right Hand",
                                     color=[255, 50, 100])
                        dpg.add_text("● Purple Border: Both Hands",
                                     color=[150, 50, 200])
                        dpg.add_text("● Gray Border: Unassigned",
                                     color=[100, 100, 100])

                        dpg.add_spacer(height=5)
                        dpg.add_text("● White Circle: Homing Key",
                                     color=[255, 255, 255])

                # Right panel - Keyboard Preview
                with dpg.child_window(width=900, height=800):
                    dpg.add_text("⌨️ KEYBOARD PREVIEW", color=[100, 200, 255])
                    dpg.add_text("Click keys to assign attributes or select for editing",
                                 color=[150, 150, 150])
                    dpg.add_separator()

                    with dpg.child_window(tag="keyboard_preview_group", width=880, height=750,
                                          border=True):
                        dpg.add_text("Load a keyboard layout to see preview", color=[
                                     100, 100, 100])

        # Set the primary window
        dpg.create_viewport(
            title='Enhanced Keyboard Layout Annotator', width=1400, height=900)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("Primary Window", True)

        # Main loop
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()

        dpg.destroy_context()


# --- Run the application ---
if __name__ == "__main__":
    app = KeyboardAnnotatorDPG()
    app.run()
