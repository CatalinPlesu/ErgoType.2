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
