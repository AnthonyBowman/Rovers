# motor/test_motor.py
# Test script for motor HAL functions

import time
import sys
import json

# Dynamic HAL imports - only import what we need

def load_config():
    """Load motor configuration"""
    try:
        with open("motor_config.json", 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("motor_config.json not found, using default controller")
        return {"motor_controller": {"type": "motozero"}}

def create_motor_controller(controller_type):
    """Dynamically import and create appropriate motor controller"""
    controller_type = controller_type.lower()
    
    # Map controller types to their module and class names
    controller_map = {
        "motozero": ("motozero", "MotoZeroController"),
        "l298": ("l298", "L298Controller"),
        "camjam": ("camjam", "CamJamController")
    }
    
    if controller_type not in controller_map:
        print(f"Unknown controller type: {controller_type}, defaulting to MotoZero")
        controller_type = "motozero"
        
    module_name, class_name = controller_map[controller_type]
    
    try:
        # Import only the needed HAL module
        module = __import__(f"hal.{module_name}", fromlist=[class_name])
        controller_class = getattr(module, class_name)
        
        print(f"Testing {class_name}")
        return controller_class()
        
    except ImportError as e:
        print(f"Could not import {module_name}: {e}")
        print("Make sure you're running from motor directory with proper hardware.")
        sys.exit(1)

def test_basic_movements(motor):
    """Test basic movement functions"""
    print("\n=== Testing Basic Movements ===")
    
    # Test forward
    print("Testing forward movement...")
    motor.start_forward(50)
    print(f"Status: {motor.get_status()}")
    time.sleep(2)
    motor.stop()
    time.sleep(1)
    
    # Test backward
    print("Testing backward movement...")
    motor.start_backward(50)
    print(f"Status: {motor.get_status()}")
    time.sleep(2)
    motor.stop()
    time.sleep(1)
    
    # Test left turn
    print("Testing left turn...")
    motor.start_left(40)
    print(f"Status: {motor.get_status()}")
    time.sleep(1)
    motor.stop()
    time.sleep(1)
    
    # Test right turn
    print("Testing right turn...")
    motor.start_right(40)
    print(f"Status: {motor.get_status()}")
    time.sleep(1)
    motor.stop()
    time.sleep(1)
    
    print("Basic movement tests completed.")

def test_speed_control(motor):
    """Test speed control functions"""
    print("\n=== Testing Speed Control ===")
    
    # Test different speeds
    speeds = [25, 50, 75, 100]
    
    for speed in speeds:
        print(f"Testing forward at {speed}% speed...")
        motor.start_forward(speed)
        print(f"Status: {motor.get_status()}")
        time.sleep(1.5)
        motor.stop()
        time.sleep(1)
    
    # Test speed change while moving
    print("Testing speed change while moving...")
    motor.start_forward(30)
    time.sleep(1)
    
    print("Increasing speed to 60%...")
    motor.set_speed(60)
    print(f"Status: {motor.get_status()}")
    time.sleep(1)
    
    print("Increasing speed to 90%...")
    motor.set_speed(90)
    print(f"Status: {motor.get_status()}")
    time.sleep(1)
    
    motor.stop()
    print("Speed control tests completed.")

def test_continuous_movement(motor):
    """Test continuous movement (no automatic stopping)"""
    print("\n=== Testing Continuous Movement ===")
    
    print("Starting forward movement...")
    motor.start_forward(50)
    
    print("Movement should continue... waiting 3 seconds")
    for i in range(3):
        time.sleep(1)
        print(f"Status: {motor.get_status()}")
    
    print("Manually stopping...")
    motor.stop()
    print(f"Final status: {motor.get_status()}")
    
    print("Continuous movement test completed.")

def test_status_reporting(motor):
    """Test status reporting"""
    print("\n=== Testing Status Reporting ===")
    
    # Test status when stopped
    print("Status when stopped:")
    print(f"  {motor.get_status()}")
    
    # Test status when moving
    motor.start_forward(75)
    print("Status when moving forward at 75%:")
    print(f"  {motor.get_status()}")
    
    motor.start_left(40)
    print("Status when turning left at 40%:")
    print(f"  {motor.get_status()}")
    
    motor.stop()
    print("Status after stopping:")
    print(f"  {motor.get_status()}")
    
    print("Status reporting tests completed.")

def test_legacy_functions(motor):
    """Test legacy functions for backward compatibility"""
    print("\n=== Testing Legacy Functions ===")
    
    # Test legacy forward (should work like old version)
    print("Testing legacy forward() with duration...")
    motor.forward(1)  # Should move forward for 1 second then stop
    time.sleep(0.5)
    print(f"Status after legacy forward: {motor.get_status()}")
    
    # Test legacy functions without duration (continuous)
    print("Testing legacy forward() without duration...")
    motor.forward()  # Should start moving forward continuously
    time.sleep(2)
    motor.stop()
    
    print("Legacy function tests completed.")

def interactive_test(motor):
    """Interactive test mode"""
    print("\n=== Interactive Test Mode ===")
    print("Commands:")
    print("  f [speed] - Forward")
    print("  b [speed] - Backward") 
    print("  l [speed] - Left")
    print("  r [speed] - Right")
    print("  s         - Stop")
    print("  speed N   - Set speed to N%")
    print("  status    - Show status")
    print("  q         - Quit")
    
    while True:
        try:
            cmd = input("Enter command: ").strip().lower().split()
            
            if not cmd:
                continue
                
            if cmd[0] == 'q':
                break
            elif cmd[0] == 'f':
                speed = int(cmd[1]) if len(cmd) > 1 else 50
                motor.start_forward(speed)
                print(f"Started forward at {speed}%")
            elif cmd[0] == 'b':
                speed = int(cmd[1]) if len(cmd) > 1 else 50
                motor.start_backward(speed)
                print(f"Started backward at {speed}%")
            elif cmd[0] == 'l':
                speed = int(cmd[1]) if len(cmd) > 1 else 50
                motor.start_left(speed)
                print(f"Started left at {speed}%")
            elif cmd[0] == 'r':
                speed = int(cmd[1]) if len(cmd) > 1 else 50
                motor.start_right(speed)
                print(f"Started right at {speed}%")
            elif cmd[0] == 's':
                motor.stop()
                print("Stopped")
            elif cmd[0] == 'speed':
                speed = int(cmd[1])
                motor.set_speed(speed)
                print(f"Speed set to {speed}%")
            elif cmd[0] == 'status':
                print(f"Status: {motor.get_status()}")
            else:
                print("Unknown command")
                
        except (ValueError, IndexError):
            print("Invalid command format")
        except KeyboardInterrupt:
            break
    
    motor.stop()
    print("Interactive test completed.")

def main():
    """Main test function"""
    print("Motor HAL Test Script")
    print("====================")
    
    # Load configuration
    config = load_config()
    controller_type = config["motor_controller"]["type"]
    
    # Create motor controller
    try:
        motor = create_motor_controller(controller_type)
    except Exception as e:
        print(f"Error creating motor controller: {e}")
        print("Make sure you're running on a Raspberry Pi with proper hardware connected.")
        return
    
    # Menu for test selection
    while True:
        print("\nSelect test:")
        print("1. Basic movements")
        print("2. Speed control")
        print("3. Continuous movement")
        print("4. Status reporting")
        print("5. Legacy functions")
        print("6. Interactive test")
        print("7. Run all tests")
        print("0. Exit")
        
        try:
            choice = input("Enter choice (0-7): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                test_basic_movements(motor)
            elif choice == '2':
                test_speed_control(motor)
            elif choice == '3':
                test_continuous_movement(motor)
            elif choice == '4':
                test_status_reporting(motor)
            elif choice == '5':
                test_legacy_functions(motor)
            elif choice == '6':
                interactive_test(motor)
            elif choice == '7':
                test_basic_movements(motor)
                test_speed_control(motor)
                test_continuous_movement(motor)
                test_status_reporting(motor)
                test_legacy_functions(motor)
            else:
                print("Invalid choice")
                
        except KeyboardInterrupt:
            print("\nTest interrupted")
            break
    
    # Cleanup
    print("\nCleaning up...")
    motor.cleanup()
    print("Test script completed.")

if __name__ == "__main__":
    main()
