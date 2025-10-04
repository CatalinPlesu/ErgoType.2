from .keyboard import FingerName
from .cost_calculator import CostCalculatorPlugin, MovementContext


class Finger:
    def __init__(self, homing_key, cost_calculator_plugin):
        self.homing_position = homing_key.get_key_center_position()
        self.current_position = homing_key.get_key_center_position()
        self.cost_calculator = cost_calculator_plugin
        self.last_key = None
        self.finger_name = None  # Will be set on first press
    
    def press(self, physical_key, presses, fingername):
        new_position = physical_key.get_key_center_position()
        
        # Build context for cost calculation
        ctx = MovementContext(
            physical_key=physical_key,
            finger=fingername,
            from_position=self.current_position,
            to_position=new_position,
            press_count=presses,
            previous_key=self.last_key,
            previous_finger=self.finger_name
        )
        
        # Calculate cost (also records in accumulator)
        cost = self.cost_calculator.calculate_press_cost(ctx)
        
        # Update state for next press
        self.current_position = new_position
        self.last_key = physical_key
        self.finger_name = fingername
    
    def reset_position(self):
        self.current_position = self.homing_position
        # Keep last_key for sequence tracking
    
    def reset(self):
        self.current_position = self.homing_position
        self.last_key = None
        self.finger_name = None


class FingerManager:
    def __init__(self, physical_keyboard, cost_calculator_plugin):
        self.fingers = {}
        self.list_alternation = 0
        self.cost_calculator = cost_calculator_plugin
        
        for item in FingerName:
            self.fingers[item] = Finger(
                physical_keyboard.get_homing_key_for_finger_name(item),
                cost_calculator_plugin
            )
    
    def press(self, key, presses):
        fingername = key.get_finger_name()
        if isinstance(fingername, list):
            self.fingers[fingername[self.list_alternation]].press(
                key, presses, fingername[0])
            self.list_alternation = 1 if self.list_alternation == 0 else 0
        else:
            self.fingers[fingername].press(key, presses, fingername)
    
    def get_total_cost(self):
        """Get total cost from accumulator"""
        return self.cost_calculator.accumulator.total()
    
    def get_accumulator(self):
        """Expose accumulator for detailed analysis"""
        return self.cost_calculator.accumulator
    
    def reset_position(self):
        for key in self.fingers.keys():
            self.fingers[key].reset_position()
    
    def reset(self):
        for key in self.fingers.keys():
            self.fingers[key].reset()
        # Reset accumulator and alternation
        self.cost_calculator.reset()
        self.list_alternation = 0