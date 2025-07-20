# motor/umc.py
# Enhanced Universal Motor Controller with MQTT
# Supports continuous movement and real-time speed control

import paho.mqtt.client as mqtt
import json
import time
import threading
import sys
import os

# Dynamic HAL imports - only import what we need

class UniversalMotorController:
    def __init__(self, config_file="motor_config.json"):
        # Load configuration first
        self.config = self.load_config(config_file)
        
        # Initialize motor controller based on config (dynamic import)
        controller_type = self.config["motor_controller"]["type"].lower()
        self.motor_hal = self._create_motor_controller(controller_type)
        
    def _create_motor_controller(self, controller_type):
        """Dynamically import and create the appropriate motor controller"""
        
        # Map controller types to their module and class names
        controller_map = {
            "motozero": ("motozero", "MotoZeroController"),
            "l298": ("l298", "L298Controller"),
            "camjam": ("camjam", "CamJamController")
        }
        
        if controller_type not in controller_map:
            raise ValueError(f"Unknown motor controller type: {controller_type}")
            
        module_name, class_name = controller_map[controller_type]
        
        try:
            # Try importing from motor.hal first (when running from main directory)
            module = __import__(f"motor.hal.{module_name}", fromlist=[class_name])
        except ImportError:
            try:
                # Fall back to hal.module (when running from motor directory)
                module = __import__(f"hal.{module_name}", fromlist=[class_name])
            except ImportError:
                raise ImportError(f"Could not import {module_name} for {controller_type}")
        
        # Get the controller class and instantiate it
        controller_class = getattr(module, class_name)
        return controller_class()
    
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
        
        # Heartbeat monitoring
        self.last_heartbeat = time.time()
        self.heartbeat_timeout = self.config["mqtt"]["heartbeat_timeout_seconds"]
        self.heartbeat_monitoring = self.config["safety"]["heartbeat_monitoring"]
        
        # Status publishing
        self.status_thread = None
        self.running = False
        
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file {config_file} not found, using defaults")
            return self.get_default_config()
            
    def get_default_config(self):
        """Return default configuration"""
        return {
            "motor_controller": {"type": "motozero"},
            "mqtt": {
                "broker": "localhost",
                "port": 1883,
                "topics": {
                    "command": "hov/motor/command",
                    "status": "hov/motor/status"
                },
                "heartbeat_timeout_seconds": 10
            },
            "motor_settings": {
                "default_speed_percent": 50,
                "max_speed_percent": 100
            },
            "safety": {
                "emergency_stop_enabled": True,
                "heartbeat_monitoring": True,
                "auto_stop_on_disconnect": True
            }
        }
        
    def on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            print("Connected to MQTT broker")
            # Subscribe to command topic
            command_topic = self.config["mqtt"]["topics"]["command"]
            client.subscribe(command_topic)
            print(f"Subscribed to {command_topic}")
        else:
            print(f"Failed to connect to MQTT broker, code: {rc}")
            
    def on_disconnect(self, client, userdata, rc):
        """MQTT disconnect callback"""
        print("Disconnected from MQTT broker")
        if self.config["safety"]["auto_stop_on_disconnect"]:
            print("Auto-stopping motors due to disconnect")
            self.motor_hal.stop()
            
    def on_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            command = msg.payload.decode('utf-8').strip()
            print(f"Received command: {command}")
            
            # Update heartbeat
            self.last_heartbeat = time.time()
            
            # Process command
            self.process_command(command)
            
        except Exception as e:
            print(f"Error processing message: {e}")
            
    def process_command(self, command):
        """Process incoming motor commands"""
        command = command.upper()
        
        # Parse command format: COMMAND:VALUE or just COMMAND
        if ":" in command:
            cmd, value = command.split(":", 1)
            try:
                value = int(value)
            except ValueError:
                print(f"Invalid value in command: {command}")
                return
        else:
            cmd = command
            value = self.config["motor_settings"]["default_speed_percent"]
            
        # Execute commands
        try:
            if cmd == "START_FORWARD" or cmd == "FORWARD":
                self.motor_hal.start_forward(value)
                print(f"Started forward at {value}% speed")
                
            elif cmd == "START_BACKWARD" or cmd == "BACKWARD":
                self.motor_hal.start_backward(value)
                print(f"Started backward at {value}% speed")
                
            elif cmd == "START_LEFT" or cmd == "LEFT":
                self.motor_hal.start_left(value)
                print(f"Started left turn at {value}% speed")
                
            elif cmd == "START_RIGHT" or cmd == "RIGHT":
                self.motor_hal.start_right(value)
                print(f"Started right turn at {value}% speed")
                
            elif cmd == "STOP":
                self.motor_hal.stop()
                print("Motors stopped")
                
            elif cmd == "SPEED":
                self.motor_hal.set_speed(value)
                print(f"Speed changed to {value}%")
                
            elif cmd == "STATUS":
                self.publish_status()
                
            elif cmd == "EMERGENCY_STOP" or cmd == "E_STOP":
                self.motor_hal.stop()
                print("EMERGENCY STOP activated")
                
            # Legacy single-character commands for backward compatibility
            elif cmd == "F":
                self.motor_hal.start_forward()
                print("Started forward (legacy command)")
                
            elif cmd == "B":
                self.motor_hal.start_backward()
                print("Started backward (legacy command)")
                
            elif cmd == "L":
                self.motor_hal.start_left()
                print("Started left turn (legacy command)")
                
            elif cmd == "R":
                self.motor_hal.start_right()
                print("Started right turn (legacy command)")
                
            elif cmd == "S":
                self.motor_hal.stop()
                print("Stopped (legacy command)")
                
            else:
                print(f"Unknown command: {cmd}")
                
        except Exception as e:
            print(f"Error executing command {cmd}: {e}")
            
    def publish_status(self):
        """Publish current motor status"""
        try:
            status = self.motor_hal.get_status()
            status["timestamp"] = time.time()
            status["controller_type"] = self.config["motor_controller"]["type"]
            
            status_topic = self.config["mqtt"]["topics"]["status"]
            self.mqtt_client.publish(status_topic, json.dumps(status))
            
        except Exception as e:
            print(f"Error publishing status: {e}")
            
    def heartbeat_monitor(self):
        """Monitor heartbeat and stop motors if timeout"""
        while self.running:
            if self.heartbeat_monitoring:
                time_since_heartbeat = time.time() - self.last_heartbeat
                if time_since_heartbeat > self.heartbeat_timeout:
                    print(f"Heartbeat timeout ({time_since_heartbeat:.1f}s), stopping motors")
                    self.motor_hal.stop()
                    # Reset heartbeat to prevent repeated stops
                    self.last_heartbeat = time.time()
                    
            time.sleep(1)
            
    def start_status_publisher(self):
        """Start background thread for status publishing"""
        def status_publisher():
            while self.running:
                self.publish_status()
                time.sleep(2)  # Publish status every 2 seconds
                
        self.status_thread = threading.Thread(target=status_publisher, daemon=True)
        self.status_thread.start()
        
    def start_heartbeat_monitor(self):
        """Start background thread for heartbeat monitoring"""
        if self.heartbeat_monitoring:
            heartbeat_thread = threading.Thread(target=self.heartbeat_monitor, daemon=True)
            heartbeat_thread.start()
            
    def run(self):
        """Main run loop"""
        try:
            # Connect to MQTT broker
            broker = self.config["mqtt"]["broker"]
            port = self.config["mqtt"]["port"]
            
            print(f"Connecting to MQTT broker at {broker}:{port}")
            self.mqtt_client.connect(broker, port, 60)
            
            # Start background threads
            self.running = True
            self.start_status_publisher()
            self.start_heartbeat_monitor()
            
            print("Universal Motor Controller started")
            print("Available commands:")
            print("  START_FORWARD:50  - Start forward at 50% speed")
            print("  START_BACKWARD:75 - Start backward at 75% speed")
            print("  START_LEFT:40     - Start left turn at 40% speed")
            print("  START_RIGHT:60    - Start right turn at 60% speed")
            print("  STOP              - Stop all motors")
            print("  SPEED:80          - Change speed to 80%")
            print("  STATUS            - Request status update")
            print("  EMERGENCY_STOP    - Emergency stop")
            
            # Blocking call for MQTT
            self.mqtt_client.loop_forever()
            
        except KeyboardInterrupt:
            print("\nShutting down...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean shutdown"""
        self.running = False
        self.motor_hal.stop()
        self.motor_hal.cleanup()
        self.mqtt_client.disconnect()
        print("Motor controller stopped")

if __name__ == "__main__":
    # Allow config file to be specified as command line argument
    config_file = sys.argv[1] if len(sys.argv) > 1 else "motor_config.json"
    
    umc = UniversalMotorController(config_file)
    umc.run()
