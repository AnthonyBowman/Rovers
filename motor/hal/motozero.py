# motor/hal/motozero.py
# Enhanced MotoZero HAL with continuous control and speed management

from gpiozero import Motor, OutputDevice
import time

class MotoZeroController:
    def __init__(self):
        # MotoZero motor pin configuration
        self.motorRR = Motor(24, 27)
        self.motorRR_enable = OutputDevice(5, initial_value=1)
        self.motorFR = Motor(6, 22)
        self.motorFR_enable = OutputDevice(17, initial_value=1)
        self.motorFL = Motor(23, 16)
        self.motorFL_enable = OutputDevice(12, initial_value=1)
        self.motorRL = Motor(13, 18)
        self.motorRL_enable = OutputDevice(25, initial_value=1)
        
        # State tracking
        self.current_speed = 0.0  # 0.0 to 1.0
        self.current_direction = "STOPPED"  # FORWARD, BACKWARD, LEFT, RIGHT, STOPPED
        self.is_moving = False
        
    def set_speed(self, speed_percent):
        """Set motor speed as percentage (0-100)"""
        if speed_percent < 0:
            speed_percent = 0
        elif speed_percent > 100:
            speed_percent = 100
            
        self.current_speed = speed_percent / 100.0
        
        # If currently moving, apply new speed immediately
        if self.is_moving:
            self._apply_current_movement()
            
    def start_forward(self, speed_percent=50):
        """Start moving forward at specified speed"""
        self.set_speed(speed_percent)
        self.current_direction = "FORWARD"
        self.is_moving = True
        self._apply_current_movement()
        
    def start_backward(self, speed_percent=50):
        """Start moving backward at specified speed"""
        self.set_speed(speed_percent)
        self.current_direction = "BACKWARD"
        self.is_moving = True
        self._apply_current_movement()
        
    def start_left(self, speed_percent=50):
        """Start turning left at specified speed"""
        self.set_speed(speed_percent)
        self.current_direction = "LEFT"
        self.is_moving = True
        self._apply_current_movement()
        
    def start_right(self, speed_percent=50):
        """Start turning right at specified speed"""
        self.set_speed(speed_percent)
        self.current_direction = "RIGHT"
        self.is_moving = True
        self._apply_current_movement()
        
    def stop(self):
        """Stop all motors immediately"""
        self.motorFR.stop()
        self.motorFL.stop()
        self.motorRL.stop()
        self.motorRR.stop()
        self.current_direction = "STOPPED"
        self.is_moving = False
        
    def _apply_current_movement(self):
        """Apply current direction and speed to motors"""
        if self.current_direction == "FORWARD":
            self.motorFR.forward(self.current_speed)
            self.motorFL.forward(self.current_speed)
            self.motorRL.forward(self.current_speed)
            self.motorRR.forward(self.current_speed)
        elif self.current_direction == "BACKWARD":
            self.motorFR.backward(self.current_speed)
            self.motorFL.backward(self.current_speed)
            self.motorRL.backward(self.current_speed)
            self.motorRR.backward(self.current_speed)
        elif self.current_direction == "LEFT":
            self.motorFR.backward(self.current_speed)
            self.motorFL.forward(self.current_speed)
            self.motorRL.forward(self.current_speed)
            self.motorRR.backward(self.current_speed)
        elif self.current_direction == "RIGHT":
            self.motorFR.forward(self.current_speed)
            self.motorFL.backward(self.current_speed)
            self.motorRL.backward(self.current_speed)
            self.motorRR.forward(self.current_speed)
            
    def get_status(self):
        """Return current motor status"""
        return {
            "speed_percent": int(self.current_speed * 100),
            "direction": self.current_direction,
            "is_moving": self.is_moving
        }
        
    def cleanup(self):
        """Safe shutdown of motor controller"""
        self.stop()
        # Additional cleanup if needed
        
    # Legacy functions for backward compatibility (deprecated)
    def forward(self, duration=0):
        """Legacy function - use start_forward() instead"""
        if duration > 0:
            self.start_forward()
            time.sleep(duration)
            self.stop()
        else:
            self.start_forward()
            
    def backward(self, duration=0):
        """Legacy function - use start_backward() instead"""
        if duration > 0:
            self.start_backward()
            time.sleep(duration)
            self.stop()
        else:
            self.start_backward()
            
    def left(self, duration=0):
        """Legacy function - use start_left() instead"""
        if duration > 0:
            self.start_left()
            time.sleep(duration)
            self.stop()
        else:
            self.start_left()
            
    def right(self, duration=0):
        """Legacy function - use start_right() instead"""
        if duration > 0:
            self.start_right()
            time.sleep(duration)
            self.stop()
        else:
            self.start_right()
