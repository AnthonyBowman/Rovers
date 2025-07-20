#!/usr/bin/env python3
"""
MQTT Robot Controller Interface for Raspberry Pi Robots
A tkinter-based GUI for sending MQTT commands and receiving telemetry
Compatible with UMC.py and enhanced motor controller system
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import paho.mqtt.client as mqtt
import json
import threading
import time
from datetime import datetime

class MQTTRobotController:
    def __init__(self, root):
        self.root = root
        self.root.title("MQTT Robot Controller Interface")
        self.root.geometry("900x700")
        
        # MQTT Configuration
        self.mqtt_client = None
        self.connected = False
        self.broker_host = tk.StringVar(value="localhost")
        self.broker_port = tk.IntVar(value=1883)
        
        # Topics configuration
        self.command_topic = tk.StringVar(value="CommandChannel")  # Legacy topic
        self.enhanced_command_topic = tk.StringVar(value="hov/motor/command")  # Enhanced topic
        self.status_topic = tk.StringVar(value="hov/motor/status")
        self.telemetry_topic = tk.StringVar(value="hov/telemetry")
        
        # Control mode
        self.use_enhanced_commands = tk.BooleanVar(value=True)
        self.current_speed = tk.IntVar(value=50)
        
        # Telemetry data
        self.telemetry_data = {
            "battery": 0,
            "temperature": 0,
            "position": {"x": 0, "y": 0},
            "speed": 0,
            "status": "Disconnected",
            "controller_type": "unknown"
        }
        
        # Create GUI
        self.create_widgets()
        
        # Bind keyboard events
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.focus_set()
        
        # Start telemetry update thread
        self.telemetry_thread = threading.Thread(target=self.update_telemetry_display, daemon=True)
        self.telemetry_thread.start()

    def create_widgets(self):
        # Main container with notebook for tabs
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Connection frame
        self.create_connection_frame(main_frame)
        
        # Notebook for different control modes
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Control tab
        control_frame = ttk.Frame(notebook, padding="10")
        notebook.add(control_frame, text="Robot Control")
        self.create_control_tab(control_frame)
        
        # Configuration tab
        config_frame = ttk.Frame(notebook, padding="10")
        notebook.add(config_frame, text="Configuration")
        self.create_config_tab(config_frame)

    def create_connection_frame(self, parent):
        conn_frame = ttk.LabelFrame(parent, text="MQTT Connection", padding="5")
        conn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Connection settings
        ttk.Label(conn_frame, text="Broker:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(conn_frame, textvariable=self.broker_host, width=15).grid(row=0, column=1, padx=(5, 10))
        
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(conn_frame, textvariable=self.broker_port, width=8).grid(row=0, column=3, padx=(5, 10))
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=4, padx=(10, 0))
        
        self.status_label = ttk.Label(conn_frame, text="Status: Disconnected", foreground="red")
        self.status_label.grid(row=0, column=5, padx=(20, 0))
        
        # Command mode selection
        ttk.Label(conn_frame, text="Mode:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        mode_frame = ttk.Frame(conn_frame)
        mode_frame.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        ttk.Radiobutton(mode_frame, text="Enhanced Commands", variable=self.use_enhanced_commands, 
                       value=True, command=self.on_mode_change).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="Legacy Commands", variable=self.use_enhanced_commands, 
                       value=False, command=self.on_mode_change).pack(side=tk.LEFT, padx=(10, 0))

    def create_control_tab(self, parent):
        # Main control layout
        control_container = ttk.Frame(parent)
        control_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        control_container.columnconfigure(1, weight=1)
        control_container.rowconfigure(0, weight=1)
        
        # Left side - Controls
        self.create_robot_controls(control_container)
        
        # Right side - Telemetry and Log
        self.create_telemetry_panel(control_container)

    def create_robot_controls(self, parent):
        control_frame = ttk.LabelFrame(parent, text="Robot Controls", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Speed control
        speed_frame = ttk.Frame(control_frame)
        speed_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(speed_frame, text="Speed:").grid(row=0, column=0, sticky=tk.W)
        speed_scale = ttk.Scale(speed_frame, from_=0, to=100, variable=self.current_speed, 
                               orient='horizontal', length=200)
        speed_scale.grid(row=0, column=1, padx=(10, 10))
        self.speed_label = ttk.Label(speed_frame, text="50%")
        self.speed_label.grid(row=0, column=2)
        
        # Update speed label when scale changes
        def update_speed_label(*args):
            self.speed_label.config(text=f"{self.current_speed.get()}%")
        self.current_speed.trace('w', update_speed_label)
        
        # Movement controls
        move_frame = ttk.LabelFrame(control_frame, text="Movement", padding="10")
        move_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Arrow key layout
        button_frame = ttk.Frame(move_frame)
        button_frame.grid(row=0, column=0)
        
        ttk.Button(button_frame, text="↑\nForward (W)", width=12, 
                  command=lambda: self.send_movement_command('forward')).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(button_frame, text="←\nLeft (A)", width=12,
                  command=lambda: self.send_movement_command('left')).grid(row=1, column=0, padx=2, pady=2)
        ttk.Button(button_frame, text="STOP\n(S)", width=12,
                  command=lambda: self.send_movement_command('stop')).grid(row=1, column=1, padx=2, pady=2)
        ttk.Button(button_frame, text="→\nRight (D)", width=12,
                  command=lambda: self.send_movement_command('right')).grid(row=1, column=2, padx=2, pady=2)
        ttk.Button(button_frame, text="↓\nBackward (X)", width=12,
                  command=lambda: self.send_movement_command('backward')).grid(row=2, column=1, padx=2, pady=2)
        
        # Additional controls
        extra_frame = ttk.LabelFrame(control_frame, text="Additional Controls", padding="10")
        extra_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        controls_grid = ttk.Frame(extra_frame)
        controls_grid.grid(row=0, column=0)
        
        ttk.Button(controls_grid, text="Rotate Left (Q)", width=15,
                  command=lambda: self.send_custom_command('q')).grid(row=0, column=0, padx=2, pady=2)
        ttk.Button(controls_grid, text="Rotate Right (E)", width=15,
                  command=lambda: self.send_custom_command('e')).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(controls_grid, text="Emergency Stop", width=15,
                  command=lambda: self.send_enhanced_command('EMERGENCY_STOP')).grid(row=1, column=0, padx=2, pady=2)
        ttk.Button(controls_grid, text="Request Status", width=15,
                  command=lambda: self.send_enhanced_command('STATUS')).grid(row=1, column=1, padx=2, pady=2)
        
        # Speed presets
        preset_frame = ttk.LabelFrame(control_frame, text="Speed Presets", padding="10")
        preset_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        preset_buttons = ttk.Frame(preset_frame)
        preset_buttons.grid(row=0, column=0)
        
        ttk.Button(preset_buttons, text="Slow (25%)", width=12,
                  command=lambda: self.set_speed_preset(25)).grid(row=0, column=0, padx=2)
        ttk.Button(preset_buttons, text="Medium (50%)", width=12,
                  command=lambda: self.set_speed_preset(50)).grid(row=0, column=1, padx=2)
        ttk.Button(preset_buttons, text="Fast (75%)", width=12,
                  command=lambda: self.set_speed_preset(75)).grid(row=0, column=2, padx=2)
        
        # Custom command entry
        custom_frame = ttk.LabelFrame(control_frame, text="Custom Command", padding="10")
        custom_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        cmd_frame = ttk.Frame(custom_frame)
        cmd_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        cmd_frame.columnconfigure(1, weight=1)
        
        ttk.Label(cmd_frame, text="Command:").grid(row=0, column=0, sticky=tk.W)
        self.custom_cmd = tk.StringVar()
        cmd_entry = ttk.Entry(cmd_frame, textvariable=self.custom_cmd)
        cmd_entry.grid(row=0, column=1, padx=(10, 10), sticky=(tk.W, tk.E))
        cmd_entry.bind('<Return>', lambda e: self.send_custom_command_from_entry())
        
        ttk.Button(cmd_frame, text="Send", command=self.send_custom_command_from_entry).grid(row=0, column=2)

    def create_telemetry_panel(self, parent):
        right_frame = ttk.Frame(parent)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Telemetry display
        telemetry_frame = ttk.LabelFrame(right_frame, text="Robot Telemetry", padding="5")
        telemetry_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        telemetry_frame.columnconfigure(0, weight=1)
        telemetry_frame.rowconfigure(0, weight=1)
        
        self.telemetry_text = scrolledtext.ScrolledText(telemetry_frame, width=50, height=12, state='disabled')
        self.telemetry_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Command log
        log_frame = ttk.LabelFrame(right_frame, text="Command Log", padding="5")
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=50, height=8, state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    def create_config_tab(self, parent):
        config_container = ttk.Frame(parent)
        config_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=20, pady=20)
        
        # MQTT Topics configuration
        topics_frame = ttk.LabelFrame(config_container, text="MQTT Topics", padding="10")
        topics_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(topics_frame, text="Legacy Command Topic:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(topics_frame, textvariable=self.command_topic, width=30).grid(row=0, column=1, padx=(10, 0), sticky=tk.W)
        
        ttk.Label(topics_frame, text="Enhanced Command Topic:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Entry(topics_frame, textvariable=self.enhanced_command_topic, width=30).grid(row=1, column=1, padx=(10, 0), pady=(5, 0), sticky=tk.W)
        
        ttk.Label(topics_frame, text="Status Topic:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Entry(topics_frame, textvariable=self.status_topic, width=30).grid(row=2, column=1, padx=(10, 0), pady=(5, 0), sticky=tk.W)
        
        ttk.Label(topics_frame, text="Telemetry Topic:").grid(row=3, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Entry(topics_frame, textvariable=self.telemetry_topic, width=30).grid(row=3, column=1, padx=(10, 0), pady=(5, 0), sticky=tk.W)
        
        # Help text
        help_frame = ttk.LabelFrame(config_container, text="Command Reference", padding="10")
        help_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        help_text = """
Enhanced Commands (recommended):
• START_FORWARD:50 - Move forward at 50% speed
• START_BACKWARD:75 - Move backward at 75% speed  
• START_LEFT:40 - Turn left at 40% speed
• START_RIGHT:60 - Turn right at 60% speed
• STOP - Stop all motors
• SPEED:80 - Change speed to 80%
• STATUS - Request status update
• EMERGENCY_STOP - Emergency stop

Legacy Commands (single character):
• F - Forward    • B - Backward
• L - Left       • R - Right
• S - Stop       • E - Exit/Emergency

Keyboard Shortcuts:
• W/A/S/D - Movement controls
• Q/E - Rotation    • Space - Stop
        """
        
        help_display = tk.Text(help_frame, width=60, height=16, wrap=tk.WORD, state='disabled')
        help_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        help_display.config(state='normal')
        help_display.insert(1.0, help_text)
        help_display.config(state='disabled')

    def on_mode_change(self):
        mode = "Enhanced" if self.use_enhanced_commands.get() else "Legacy"
        self.log_message(f"Switched to {mode} command mode")

    def set_speed_preset(self, speed):
        self.current_speed.set(speed)
        if self.use_enhanced_commands.get():
            self.send_enhanced_command(f"SPEED:{speed}")

    def toggle_connection(self):
        if not self.connected:
            self.connect_to_broker()
        else:
            self.disconnect_from_broker()

    def connect_to_broker(self):
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            
            self.mqtt_client.connect(self.broker_host.get(), self.broker_port.get(), 60)
            self.mqtt_client.loop_start()
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to MQTT broker: {str(e)}")
            self.log_message(f"Connection failed: {str(e)}")

    def disconnect_from_broker(self):
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.mqtt_client = None
        
        self.connected = False
        self.connect_btn.config(text="Connect")
        self.status_label.config(text="Status: Disconnected", foreground="red")
        self.log_message("Disconnected from MQTT broker")

    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.connect_btn.config(text="Disconnect")
            self.status_label.config(text="Status: Connected", foreground="green")
            self.log_message("Connected to MQTT broker")
            
            # Subscribe to telemetry and status topics
            client.subscribe(self.status_topic.get())
            client.subscribe(self.telemetry_topic.get())
            self.log_message(f"Subscribed to: {self.status_topic.get()}, {self.telemetry_topic.get()}")
        else:
            self.log_message(f"MQTT connection failed with code: {rc}")

    def on_mqtt_disconnect(self, client, userdata, rc):
        self.connected = False
        self.connect_btn.config(text="Connect")
        self.status_label.config(text="Status: Disconnected", foreground="red")
        self.log_message("Disconnected from MQTT broker")

    def on_mqtt_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            # Try to parse as JSON for structured data
            try:
                data = json.loads(payload)
                if topic == self.status_topic.get():
                    # Update telemetry with status data
                    self.telemetry_data.update(data)
                elif topic == self.telemetry_topic.get():
                    # Update telemetry with sensor data
                    self.telemetry_data.update(data)
                
                self.log_message(f"Received from {topic}: {payload[:100]}...")
                
            except json.JSONDecodeError:
                # Handle plain text messages
                self.log_message(f"Received from {topic}: {payload}")
                
        except Exception as e:
            self.log_message(f"Error processing message: {str(e)}")

    def send_movement_command(self, direction):
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to MQTT broker first")
            return
        
        if self.use_enhanced_commands.get():
            # Enhanced command format
            speed = self.current_speed.get()
            if direction == 'forward':
                command = f"START_FORWARD:{speed}"
            elif direction == 'backward':
                command = f"START_BACKWARD:{speed}"
            elif direction == 'left':
                command = f"START_LEFT:{speed}"
            elif direction == 'right':
                command = f"START_RIGHT:{speed}"
            elif direction == 'stop':
                command = "STOP"
            
            self.send_enhanced_command(command)
        else:
            # Legacy single character commands
            legacy_map = {
                'forward': 'F',
                'backward': 'B',
                'left': 'L',
                'right': 'R',
                'stop': 'S'
            }
            if direction in legacy_map:
                self.send_legacy_command(legacy_map[direction])

    def send_enhanced_command(self, command):
        if self.mqtt_client and self.connected:
            topic = self.enhanced_command_topic.get()
            self.mqtt_client.publish(topic, command)
            self.log_message(f"Enhanced command sent: {command}")

    def send_legacy_command(self, command):
        if self.mqtt_client and self.connected:
            topic = self.command_topic.get()
            self.mqtt_client.publish(topic, command)
            self.log_message(f"Legacy command sent: {command}")

    def send_custom_command(self, command):
        if self.use_enhanced_commands.get():
            self.send_enhanced_command(command)
        else:
            self.send_legacy_command(command)

    def send_custom_command_from_entry(self):
        cmd = self.custom_cmd.get().strip()
        if cmd:
            self.send_custom_command(cmd)
            self.custom_cmd.set("")

    def on_key_press(self, event):
        """Handle keyboard input for robot control"""
        key = event.char.lower()
        
        # Map keys to movement commands
        key_commands = {
            'w': 'forward',
            'a': 'left', 
            's': 'stop',
            'd': 'right',
            'x': 'backward',
            ' ': 'stop'  # Space bar for stop
        }
        
        if key in key_commands:
            self.send_movement_command(key_commands[key])
        elif key == 'q':
            self.send_custom_command('q')
        elif key == 'e':
            self.send_custom_command('e')

    def update_telemetry_display(self):
        """Update telemetry display every second"""
        while True:
            if self.connected:
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                telemetry_str = f"""ROBOT TELEMETRY
===============
Timestamp: {timestamp}
Status: {self.telemetry_data.get('status', 'Unknown')}
Controller: {self.telemetry_data.get('controller_type', 'Unknown')}
Battery: {self.telemetry_data.get('battery', 0)}%
Temperature: {self.telemetry_data.get('temperature', 0)}°C
Speed: {self.telemetry_data.get('speed_percent', 0)}%
Direction: {self.telemetry_data.get('direction', 'Unknown')}
Moving: {self.telemetry_data.get('is_moving', False)}

Position:
  X: {self.telemetry_data.get('position', {}).get('x', 0)}
  Y: {self.telemetry_data.get('position', {}).get('y', 0)}

MOTOR STATUS
============
Left Motor: {self.telemetry_data.get('left_motor_speed', 'N/A')}
Right Motor: {self.telemetry_data.get('right_motor_speed', 'N/A')}

ADDITIONAL SENSORS
=================="""
                
                # Add any additional sensor data
                excluded_keys = {'status', 'battery', 'temperature', 'speed_percent', 'position', 
                               'controller_type', 'direction', 'is_moving', 'left_motor_speed', 
                               'right_motor_speed', 'timestamp'}
                
                for key, value in self.telemetry_data.items():
                    if key not in excluded_keys:
                        telemetry_str += f"\n{key}: {value}"
                
                # Update display
                self.telemetry_text.config(state='normal')
                self.telemetry_text.delete(1.0, tk.END)
                self.telemetry_text.insert(1.0, telemetry_str)
                self.telemetry_text.config(state='disabled')
            
            time.sleep(1)

    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

def main():
    root = tk.Tk()
    app = MQTTRobotController(root)
    
    # Handle window closing
    def on_closing():
        if app.connected:
            app.disconnect_from_broker()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
