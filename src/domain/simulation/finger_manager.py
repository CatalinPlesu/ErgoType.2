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
        # Reset accumulator
        self.cost_calculator.reset()
