#!/bin/bash

# Rover System Setup Script
# Sets up controllers or rovers with appropriate configurations

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root for system operations
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root. This is recommended for system setup."
    else
        log_info "Not running as root. Some operations may require sudo."
    fi
}

# Update system packages
update_system() {
    log_info "Updating system packages..."
    sudo apt update
    sudo apt upgrade -y
    log_success "System updated"
}

# Install common dependencies
install_common_deps() {
    log_info "Installing common dependencies..."
    
    # Python and pip
    sudo apt install -y python3 python3-pip python3-venv
    
    # Git for version control
    sudo apt install -y git
    
    # I2C tools for sensor communication
    sudo apt install -y i2c-tools
    
    # Network tools
    sudo apt install -y net-tools wireless-tools
    
    log_success "Common dependencies installed"
}

# Install MQTT broker and client
install_mqtt() {
    log_info "Installing MQTT broker and client tools..."
    
    # Install Mosquitto broker and clients
    sudo apt install -y mosquitto mosquitto-clients
    
    # Install Python MQTT client
    pip3 install paho-mqtt
    
    # Configure Mosquitto to allow anonymous connections
    log_info "Configuring MQTT broker..."
    sudo tee -a /etc/mosquitto/mosquitto.conf <<EOF

# Custom configuration for rover system
listener 1883
allow_anonymous true
EOF
    
    # Enable and start Mosquitto service
    sudo systemctl enable mosquitto
    sudo systemctl restart mosquitto
    
    log_success "MQTT broker and client installed and configured"
}

# Install rover-specific dependencies
install_rover_deps() {
    log_info "Installing rover-specific dependencies..."
    
    # GPIO libraries for Raspberry Pi
    if command -v gpio >/dev/null 2>&1; then
        log_info "Raspberry Pi detected, installing GPIO libraries..."
        pip3 install RPi.GPIO gpiozero
    fi
    
    # Camera libraries
    sudo apt install -y python3-picamera
    pip3 install picamera
    
    # OpenCV for computer vision
    sudo apt install -y python3-opencv
    
    # Additional sensor libraries
    pip3 install smbus2
    
    # PySerial for serial communication
    pip3 install pyserial
    
    log_success "Rover dependencies installed"
}

# Install controller-specific dependencies  
install_controller_deps() {
    log_info "Installing controller-specific dependencies..."
    
    # GUI libraries for tkinter-based control interface
    sudo apt install -y python3-tk python3-pil python3-pil.imagetk
    
    # VLC for media streaming/viewing
    sudo apt install -y vlc python3-vlc
    
    # Additional networking tools for rover discovery
    sudo apt install -y nmap arp-scan
    
    # Optional: Kivy if user wants alternative GUI frameworks
    read -p "Install Kivy GUI framework as alternative? (y/n): " install_kivy
    if [[ "$install_kivy" =~ ^[Yy]$ ]]; then
        pip3 install kivy kivymd
        log_success "Kivy installed as optional GUI framework"
    fi
    
    log_success "Controller dependencies installed"
}

# Configure system settings
configure_system() {
    local device_type=$1
    
    log_info "Configuring system settings for $device_type..."
    
    if [[ "$device_type" == "rover" ]]; then
        # Enable I2C, SPI, Camera (for Raspberry Pi)
        if command -v raspi-config >/dev/null 2>&1; then
            log_info "Enabling hardware interfaces..."
            sudo raspi-config nonint do_i2c 0    # Enable I2C
            sudo raspi-config nonint do_spi 0    # Enable SPI  
            sudo raspi-config nonint do_camera 0 # Enable camera
            sudo raspi-config nonint do_ssh 0    # Enable SSH
        fi
        
        # Add user to gpio and i2c groups
        sudo usermod -a -G gpio,i2c,spi $USER
    fi
    
    # Set up hostname
    read -p "Enter hostname for this device (default: ${device_type}-$(hostname -s)): " new_hostname
    if [[ -n "$new_hostname" ]]; then
        sudo hostnamectl set-hostname "$new_hostname"
        log_info "Hostname set to: $new_hostname"
    fi
    
    log_success "System configuration completed"
}

# Set up project directory structure
setup_project_structure() {
    local device_type=$1
    
    log_info "Setting up project structure..."
    
    # Create main project directory
    PROJECT_DIR="$HOME/rover_system"
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    if [[ "$device_type" == "rover" ]]; then
        # Rover directory structure
        mkdir -p motor/{hal,configs,logs}
        mkdir -p sensors/{configs,logs}
        mkdir -p camera/{configs,logs}
        mkdir -p communication/{configs,logs}
        mkdir -p systemd
        
        # Copy motor HAL files (these would need to be provided)
        log_info "Motor HAL files should be placed in $PROJECT_DIR/motor/hal/"
        
    if [[ "$device_type" == "controller" ]]; then
        # Controller directory structure  
        mkdir -p control_interface/gui
        mkdir -p control_interface/configs
        mkdir -p control_interface/logs
        mkdir -p communication/configs
        mkdir -p communication/logs
        mkdir -p logs
        
        # Create a README for controller setup
        cat > "$PROJECT_DIR/control_interface/README.md" <<EOF
# Robot Controller Interface

## Setup
1. Copy your controller.py to this directory
2. Install dependencies: pip3 install paho-mqtt tkinter
3. Run: python3 controller.py

## Features
- tkinter-based GUI with tabbed interface
- Real-time telemetry display
- Support for enhanced and legacy MQTT commands
- Keyboard controls (WASD + QE for rotation)
- Speed presets and custom commands
- Connection management

## Configuration
- Default broker: localhost:1883
- Enhanced commands: hov/motor/command
- Legacy commands: CommandChannel
- Status topic: hov/motor/status
- Telemetry topic: hov/telemetry

EOF
        
        log_info "Controller interface structure created"
        log_info "Copy your controller.py to: $PROJECT_DIR/control_interface/"
    fi
    
    # Common directories
    mkdir -p scripts configs logs
    
    log_success "Project structure created at $PROJECT_DIR"
    echo "Project directory: $PROJECT_DIR"
}

# Configure motor controller for rovers
configure_motor_controller() {
    log_info "Configuring motor controller..."
    
    echo "Available motor controllers:"
    echo "1. CamJam EduKit 3 Robotics Kit"
    echo "2. L298N Dual H-Bridge Motor Driver"  
    echo "3. MotoZero 4-Motor Controller"
    echo "4. Custom/Other"
    
    read -p "Select motor controller (1-4): " motor_choice
    
    case $motor_choice in
        1)
            motor_type="camjam"
            log_info "Selected: CamJam EduKit 3"
            ;;
        2)
            motor_type="l298"
            log_info "Selected: L298N Motor Driver"
            ;;
        3)
            motor_type="motozero"
            log_info "Selected: MotoZero Controller"
            ;;
        4)
            motor_type="custom"
            log_info "Selected: Custom controller"
            ;;
        *)
            motor_type="motozero"
            log_warning "Invalid selection, defaulting to MotoZero"
            ;;
    esac
    
    # Create motor configuration file
    cat > "$PROJECT_DIR/motor/configs/motor_config.json" <<EOF
{
  "motor_controller": {
    "type": "$motor_type",
    "comment": "Motor controller configuration for this rover"
  },
  "mqtt": {
    "broker": "localhost",
    "port": 1883,
    "topics": {
      "command": "rover/motor/command",
      "status": "rover/motor/status"
    },
    "heartbeat_timeout_seconds": 10
  },
  "motor_settings": {
    "default_speed_percent": 50,
    "max_speed_percent": 100,
    "turn_speed_percent": 40,
    "acceleration_enabled": false,
    "acceleration_step": 5
  },
  "calibration": {
    "left_motor_factor": 1.0,
    "right_motor_factor": 1.0,
    "turn_adjustment": 1.0,
    "comment": "Adjust these values to compensate for motor differences"
  },
  "safety": {
    "emergency_stop_enabled": true,
    "heartbeat_monitoring": true,
    "auto_stop_on_disconnect": true
  }
}
EOF
    
    log_success "Motor controller configured as: $motor_type"
}

# Set up systemd services for rovers
setup_systemd_services() {
    log_info "Setting up systemd services..."
    
    # Universal Motor Controller service
    sudo tee /etc/systemd/system/rover-motor.service <<EOF
[Unit]
Description=Rover Motor Controller
After=network.target mosquitto.service
Requires=mosquitto.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR/motor
ExecStart=/usr/bin/python3 umc.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Stream Server service (if camera is available)
    if command -v vcgencmd >/dev/null 2>&1; then
        sudo tee /etc/systemd/system/rover-camera.service <<EOF
[Unit]
Description=Rover Camera Stream Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR/camera
ExecStart=/usr/bin/python3 StreamServer.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    fi
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Ask if services should be enabled
    read -p "Enable services to start automatically on boot? (y/n): " enable_services
    if [[ "$enable_services" =~ ^[Yy]$ ]]; then
        sudo systemctl enable rover-motor.service
        if [[ -f /etc/systemd/system/rover-camera.service ]]; then
            sudo systemctl enable rover-camera.service
        fi
        log_success "Services enabled for automatic startup"
    fi
    
    log_success "Systemd services configured"
}

# Configure Wi-Fi networks
configure_wifi() {
    log_info "Configuring Wi-Fi networks..."
    
    read -p "Add Wi-Fi networks? (y/n): " add_wifi
    if [[ "$add_wifi" =~ ^[Yy]$ ]]; then
        
        # Add common networks
        read -p "Add PiLab network? (y/n): " add_pilab
        if [[ "$add_pilab" =~ ^[Yy]$ ]]; then
            read -s -p "Enter PiLab password: " pilab_pass
            echo
            nmcli connection add con-name "PiLab" ifname wlan0 type wifi ssid "PiLab"
            nmcli connection modify "PiLab" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$pilab_pass"
            log_success "PiLab network added"
        fi
        
        read -p "Add CrossBow network? (y/n): " add_crossbow  
        if [[ "$add_crossbow" =~ ^[Yy]$ ]]; then
            read -s -p "Enter CrossBow password: " crossbow_pass
            echo
            nmcli connection add con-name "CrossBow" ifname wlan0 type wifi ssid "CrossBow"
            nmcli connection modify "CrossBow" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$crossbow_pass"
            log_success "CrossBow network added"
        fi
        
        # Add custom network
        read -p "Add custom Wi-Fi network? (y/n): " add_custom
        if [[ "$add_custom" =~ ^[Yy]$ ]]; then
            read -p "Enter network SSID: " custom_ssid
            read -s -p "Enter network password: " custom_pass
            echo
            nmcli connection add con-name "$custom_ssid" ifname wlan0 type wifi ssid "$custom_ssid"
            nmcli connection modify "$custom_ssid" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$custom_pass"
            log_success "Custom network $custom_ssid added"
        fi
    fi
}

# Set up development environment
setup_development() {
    log_info "Setting up development environment..."
    
    # Git configuration
    read -p "Configure Git? (y/n): " setup_git
    if [[ "$setup_git" =~ ^[Yy]$ ]]; then
        read -p "Enter Git username: " git_user
        read -p "Enter Git email: " git_email
        
        git config --global user.name "$git_user"
        git config --global user.email "$git_email"
        log_success "Git configured"
    fi
    
    # Create useful aliases
    log_info "Creating useful aliases..."
    cat >> ~/.bashrc <<EOF

# Rover system aliases
alias rover-logs='journalctl -u rover-motor.service -f'
alias rover-camera-logs='journalctl -u rover-camera.service -f'
alias rover-status='systemctl status rover-*.service'
alias rover-restart='sudo systemctl restart rover-*.service'
alias mqtt-listen='mosquitto_sub -h localhost -t "#" -v'
alias rover-project='cd $PROJECT_DIR'
EOF
    
    log_success "Development environment configured"
}

# Test installation
test_installation() {
    local device_type=$1
    
    log_info "Testing installation..."
    
    # Test MQTT
    if systemctl is-active --quiet mosquitto; then
        log_success "MQTT broker is running"
        
        # Test MQTT publish/subscribe
        timeout 2 mosquitto_sub -h localhost -t "test/topic" &
        sleep 1
        mosquitto_pub -h localhost -t "test/topic" -m "test message"
        wait
        log_success "MQTT communication test passed"
    else
        log_error "MQTT broker is not running"
    fi
    
    # Test Python imports
    python3 -c "import paho.mqtt.client; print('MQTT client import: OK')" 2>/dev/null && log_success "Python MQTT client: OK" || log_error "Python MQTT client: FAILED"
    
    if [[ "$device_type" == "rover" ]]; then
        # Test GPIO (if available)
        if command -v gpio >/dev/null 2>&1; then
            python3 -c "import RPi.GPIO; print('GPIO import: OK')" 2>/dev/null && log_success "GPIO library: OK" || log_warning "GPIO library: Not available (normal on non-Pi systems)"
        fi
        
        # Test I2C
        if command -v i2cdetect >/dev/null 2>&1; then
            log_success "I2C tools: Available"
        else
            log_warning "I2C tools: Not available"
        fi
    fi
    
    log_success "Installation test completed"
}

# Create startup script
create_startup_script() {
    local device_type=$1
    
    log_info "Creating startup script..."
    
    cat > "$PROJECT_DIR/start_rover.sh" <<EOF
#!/bin/bash
# Rover system startup script

echo "Starting rover system..."

# Start MQTT broker
sudo systemctl start mosquitto

# Start rover services
if [[ "$device_type" == "rover" ]]; then
    sudo systemctl start rover-motor.service
    sudo systemctl start rover-camera.service 2>/dev/null || echo "Camera service not available"
fi

echo "Rover system started. Check status with: systemctl status rover-*.service"
EOF

    chmod +x "$PROJECT_DIR/start_rover.sh"
    log_success "Startup script created: $PROJECT_DIR/start_rover.sh"
}

# Main setup function
main() {
    echo "=================================================="
    echo "       Rover System Setup Script"
    echo "=================================================="
    echo
    
    check_root
    
    # Device type selection
    echo "Select device type:"
    echo "1. Rover (mobile robot with motors, sensors, camera)"
    echo "2. Controller (stationary control station)"
    echo
    read -p "Select device type (1-2): " device_choice
    
    case $device_choice in
        1)
            device_type="rover"
            log_info "Setting up ROVER"
            ;;
        2)
            device_type="controller"
            log_info "Setting up CONTROLLER"
            ;;
        *)
            log_error "Invalid selection"
            exit 1
            ;;
    esac
    
    echo
    log_info "Starting setup for $device_type..."
    echo
    
    # Core installation steps
    update_system
    install_common_deps
    install_mqtt
    
    # Device-specific installation
    if [[ "$device_type" == "rover" ]]; then
        install_rover_deps
        configure_motor_controller
        setup_systemd_services
    elif [[ "$device_type" == "controller" ]]; then
        install_controller_deps
    fi
    
    # Common configuration
    configure_system "$device_type"
    setup_project_structure "$device_type"
    configure_wifi
    setup_development
    create_startup_script "$device_type"
    
    # Test everything
    test_installation "$device_type"
    
    echo
    echo "=================================================="
    log_success "Setup completed for $device_type!"
    echo "=================================================="
    echo
    echo "Next steps:"
    echo "1. Reboot the system: sudo reboot"
    echo "2. Test MQTT: mosquitto_pub -h localhost -t 'test' -m 'hello'"
    
    if [[ "$device_type" == "rover" ]]; then
        echo "3. Place motor HAL files in: $PROJECT_DIR/motor/hal/"
        echo "4. Start motor service: sudo systemctl start rover-motor.service"
        echo "5. Test motor commands: mosquitto_pub -h localhost -t 'rover/motor/command' -m 'FORWARD:50'"
    elif [[ "$device_type" == "controller" ]]; then
        echo "3. Copy your controller.py to: $PROJECT_DIR/control_interface/"
        echo "4. Run controller: cd $PROJECT_DIR/control_interface && python3 controller.py"
        echo "5. Configure rover connections in the GUI"
    fi
    
    echo
    echo "Project directory: $PROJECT_DIR"
    echo "Log files: $PROJECT_DIR/logs/"
    echo "Configuration files: $PROJECT_DIR/configs/"
    echo
    echo "For support, check the documentation or logs in journalctl"
    
    read -p "Reboot now? (y/n): " reboot_now
    if [[ "$reboot_now" =~ ^[Yy]$ ]]; then
        log_info "Rebooting..."
        sudo reboot
    fi
}

# Error handling
trap 'log_error "Setup failed at line $LINENO. Check the output above for details."' ERR

# Run main function
main "$@"