# motor/hal/camjam.py
# Enhanced CamJam HAL with continuous control and speed management

from gpiozero import CamJamKitRobot
import time

class CamJamController:
    def __init__(self):
        # CamJam robot initialization
        self.robot = CamJamKitRobot()
        
        # State tracking
        self.current_speed = 0.5  # 0.0 to 1.0 (CamJam uses this range)
        self.current_direction = "STOPPED"
        self.is_moving = False
        
        # Motor speed tuples for different directions
        self.left_motor_speed = 0.5
        self.right_motor_speed = 0.5
        
    def set_speed(self, speed_percent):
        """Set motor speed as percentage (0-100)"""
        if speed_percent < 0:
            speed_percent = 0
        elif speed_percent > 100:
            speed_percent = 100
            
        self.current_speed = speed_percent / 100.0
        self.left_motor_speed = self.current_speed
        self.right_motor_speed = self.current_speed
        
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
        self.robot.stop()
        self.current_direction = "STOPPED"
        self.is_moving = False
        
    def _apply_current_movement(self):
        """Apply current direction and speed to motors"""
        if self.current_direction == "FORWARD":
            self.robot.value = (self.left_motor_speed, self.right_motor_speed)
        elif self.current_direction == "BACKWARD":
            self.robot.value = (-self.left_motor_speed, -self.right_motor_speed)
        elif self.current_direction == "LEFT":
            self.robot.value = (self.left_motor_speed, 0)
        elif self.current_direction == "RIGHT":
            self.robot.value = (0, self.right_motor_speed)
            
    def get_status(self):
        """Return current motor status"""
        return {
            "speed_percent": int(self.current_speed * 100),
            "direction": self.current_direction,
            "is_moving": self.is_moving,
            "left_motor_speed": self.left_motor_speed,
            "right_motor_speed": self.right_motor_speed
        }
        
    def cleanup(self):
        """Safe shutdown of motor controller"""
        self.stop()
        
    # Motor calibration functions
    def set_motor_speeds(self, left_speed_percent, right_speed_percent):
        """Set individual motor speeds for calibration"""
        self.left_motor_speed = left_speed_percent / 100.0
        self.right_motor_speed = right_speed_percent / 100.0
        
        if self.is_moving:
            self._apply_current_movement()
            
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
