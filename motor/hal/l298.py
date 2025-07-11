# motor/hal/l298.py
# Enhanced L298 HAL with continuous control and speed management

import RPi.GPIO as GPIO
import time

class L298Controller:
    def __init__(self):
        # L298 motor pin configuration
        # 1st motor
        self.in1 = 21
        self.in2 = 20
        self.ena = 16
        
        # 2nd motor  
        self.in3 = 19
        self.in4 = 26
        self.enb = 13
        
        # GPIO setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.in1, GPIO.OUT)
        GPIO.setup(self.in2, GPIO.OUT)
        GPIO.setup(self.in3, GPIO.OUT)
        GPIO.setup(self.in4, GPIO.OUT)
        GPIO.setup(self.ena, GPIO.OUT)
        GPIO.setup(self.enb, GPIO.OUT)
        
        # Initialize all outputs to LOW
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)
        GPIO.output(self.in3, GPIO.LOW)
        GPIO.output(self.in4, GPIO.LOW)
        
        # PWM setup
        self.pwm_a = GPIO.PWM(self.ena, 1000)
        self.pwm_b = GPIO.PWM(self.enb, 1000)
        self.pwm_a.start(0)
        self.pwm_b.start(0)
        
        # State tracking
        self.current_speed = 50  # 0-100 percent
        self.current_direction = "STOPPED"
        self.is_moving = False
        
    def set_speed(self, speed_percent):
        """Set motor speed as percentage (0-100)"""
        if speed_percent < 0:
            speed_percent = 0
        elif speed_percent > 100:
            speed_percent = 100
            
        self.current_speed = speed_percent
        
        # Apply new speed to PWM if currently moving
        if self.is_moving:
            self.pwm_a.ChangeDutyCycle(self.current_speed)
            self.pwm_b.ChangeDutyCycle(self.current_speed)
            
    def start_forward(self, speed_percent=50):
        """Start moving forward at specified speed"""
        self.set_speed(speed_percent)
        self.current_direction = "FORWARD"
        self.is_moving = True
        
        GPIO.output(self.in1, GPIO.HIGH)
        GPIO.output(self.in2, GPIO.LOW)
        GPIO.output(self.in3, GPIO.HIGH)
        GPIO.output(self.in4, GPIO.LOW)
        self.pwm_a.ChangeDutyCycle(self.current_speed)
        self.pwm_b.ChangeDutyCycle(self.current_speed)
        
    def start_backward(self, speed_percent=50):
        """Start moving backward at specified speed"""
        self.set_speed(speed_percent)
        self.current_direction = "BACKWARD"
        self.is_moving = True
        
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.HIGH)
        GPIO.output(self.in3, GPIO.LOW)
        GPIO.output(self.in4, GPIO.HIGH)
        self.pwm_a.ChangeDutyCycle(self.current_speed)
        self.pwm_b.ChangeDutyCycle(self.current_speed)
        
    def start_left(self, speed_percent=50):
        """Start turning left at specified speed"""
        self.set_speed(speed_percent)
        self.current_direction = "LEFT"
        self.is_moving = True
        
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.HIGH)
        GPIO.output(self.in3, GPIO.HIGH)
        GPIO.output(self.in4, GPIO.LOW)
        self.pwm_a.ChangeDutyCycle(self.current_speed)
        self.pwm_b.ChangeDutyCycle(self.current_speed)
        
    def start_right(self, speed_percent=50):
        """Start turning right at specified speed"""
        self.set_speed(speed_percent)
        self.current_direction = "RIGHT"
        self.is_moving = True
        
        GPIO.output(self.in1, GPIO.HIGH)
        GPIO.output(self.in2, GPIO.LOW)
        GPIO.output(self.in3, GPIO.LOW)
        GPIO.output(self.in4, GPIO.HIGH)
        self.pwm_a.ChangeDutyCycle(self.current_speed)
        self.pwm_b.ChangeDutyCycle(self.current_speed)
        
    def stop(self):
        """Stop all motors immediately"""
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)
        GPIO.output(self.in3, GPIO.LOW)
        GPIO.output(self.in4, GPIO.LOW)
        self.pwm_a.ChangeDutyCycle(0)
        self.pwm_b.ChangeDutyCycle(0)
        self.current_direction = "STOPPED"
        self.is_moving = False
        
    def get_status(self):
        """Return current motor status"""
        return {
            "speed_percent": self.current_speed,
            "direction": self.current_direction,
            "is_moving": self.is_moving
        }
        
    def cleanup(self):
        """Safe shutdown of motor controller"""
        self.stop()
        self.pwm_a.stop()
        self.pwm_b.stop()
        GPIO.cleanup()
        
    # Speed presets for compatibility
    def low(self):
        """Set speed to 25%"""
        self.set_speed(25)
        
    def medium(self):
        """Set speed to 50%"""
        self.set_speed(50)
        
    def high(self):
        """Set speed to 75%"""
        self.set_speed(75)
        
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
