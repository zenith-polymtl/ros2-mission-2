#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Imu
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
import subprocess
import time

# Configuration
DEVICE = "/dev/ttyUSB0"  # Change this to your actual device
CAN_SPEED = 500000       # 500kbps
BAUDRATE = 2000000       # 2Mbps
MOTOR_ID = 1             # Motor ID

class WinchNode(Node):
    def __init__(self):
        super().__init__("Winch_Node")

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,  # Ensures message delivery
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.subscriber_ = self.create_subscription(String, '/go_winch', self.go_callback, qos_profile)

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,  # Ensures message delivery
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.subscriber_ = self.create_subscription(Imu, '/mavros/imu/data', self.v_accel, qos_profile)
        self.get_logger().info("Winch Subsriber started")

    def go_up(self):
        """Move motor clockwise (positive speed)"""
        self.control_motor("speed", 20, 2)
        self.control_motor("start")

        # 2. Set speed control (clockwise rotation)
        # Using Speed Control command (0x94) with positive speed value
        # Example: 50 RPM for 2 seconds
        # 0x94 00 00 48 42 D0 07 00 = 50 RPM for 2000ms
        # Speed is in IEEE float format with LSB byte order
        
        time.sleep(2)
        
        # 4. Stop the motor
        self.control_motor("stop")

    def go_down(self):
        """Move motor counter-clockwise (negative speed)"""
        self.control_motor("speed", -20, 2)
        self.control_motor("start")

        # 2. Set speed control (clockwise rotation)
        # Using Speed Control command (0x94) with positive speed value
        # Example: 50 RPM for 2 seconds
        # 0x94 00 00 48 42 D0 07 00 = 50 RPM for 2000ms
        # Speed is in IEEE float format with LSB byte order
        
        time.sleep(2)
        
        # 4. Stop the motor
        self.control_motor("stop")

    def go_callback(self, msg):
        self.get_logger().info(f"GO MESSAGE : {msg.data}")
        if msg.data == 'UP':
            self.go_up()
        if msg.data == 'DOWN':
            self.go_down()
    
    def v_accel(self, msg):
        self.get_logger().info(f"Vertical accel : {msg.linear_acceleration.z}")

    def control_motor(self, control_type, value=0.0, time_seconds=0.0, description=None):
        """
        General motor control function that handles different control types
        
        Args:
            control_type: String indicating the control type ("start", "stop", "speed", "position", "torque")
            value: Float value for speed (RPM), position (radians), or torque (N.m)
            time_seconds: Duration in seconds (not used for start/stop)
            description: Optional custom description for logging
        """
        import struct
        
        # Convert time from seconds to milliseconds
        time_ms = int(time_seconds * 1000)
        time_bytes = struct.pack("<I", time_ms)[:3]  # Only need 3 bytes for 24-bit duration
        
        # Prepare command based on control type
        if control_type.lower() == "start":
            cmd_hex = "91 00 00 00 00 00 00 00"
            desc = description or "Start Motor"
        elif control_type.lower() == "stop":
            cmd_hex = "92 00 00 00 00 00 00 00"
            desc = description or "Stop Motor"
        elif control_type.lower() == "torque":
            # Convert torque value to IEEE float and format as hex
            value_bytes = struct.pack("<f", value)
            value_hex = " ".join([f"{b:02X}" for b in value_bytes])
            time_hex = " ".join([f"{b:02X}" for b in time_bytes]) + " 00"
            cmd_hex = f"93 {value_hex} {time_hex}"
            desc = description or f"Torque Control ({value} N.m for {time_seconds}s)"
        elif control_type.lower() == "speed":
            # Convert speed value to IEEE float and format as hex
            value_bytes = struct.pack("<f", value)
            value_hex = " ".join([f"{b:02X}" for b in value_bytes])
            time_hex = " ".join([f"{b:02X}" for b in time_bytes]) + " 00"
            cmd_hex = f"94 {value_hex} {time_hex}"
            desc = description or f"Speed Control ({value} RPM for {time_seconds}s)"
        elif control_type.lower() == "position":
            # Convert position value to IEEE float and format as hex
            value_bytes = struct.pack("<f", value)
            value_hex = " ".join([f"{b:02X}" for b in value_bytes])
            time_hex = " ".join([f"{b:02X}" for b in time_bytes]) + " 00"
            cmd_hex = f"95 {value_hex} {time_hex}"
            desc = description or f"Position Control ({value} rad for {time_seconds}s)"
        else:
            raise ValueError(f"Unsupported control type: {control_type}")
        
        # Send the command using the existing method
        return self.send_can_command(cmd_hex, desc)


    def send_can_command(self, command_hex, description):
        """Send a CAN command and print details"""
        print(f"\n--- Sending: {description} ---")
        print(f"Command (hex): {command_hex}")
        
        # Convert hex string to bytes for display
        bytes_array = bytearray.fromhex(command_hex)
        print(f"Bytes: {' '.join(f'0x{b:02X}' for b in bytes_array)}")
        
        # Build the canusb command
        cmd = [
            "./mission/mission/canusb",
            "-d", DEVICE,
            "-s", str(CAN_SPEED),
            "-b", str(BAUDRATE),
            "-i", f"{MOTOR_ID:x}",  # Motor ID in hex
            "-j", command_hex,
            "-n", "1",              # Send once
            "-m", "2"               # Fixed payload mode
        ]
        
        # Execute the command
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(f"Command executed: {' '.join(cmd)}")
            
            if result.stdout:
                print(f"Stdout: {result.stdout}")
            if result.stderr:
                print(f"Stderr: {result.stderr}")
                
            # Wait a bit for the command to be processed
            time.sleep(0.1)
            return result
        except Exception as e:
            print(f"Error executing command: {e}")
            return None

def main(args=None):
    rclpy.init(args=args)
    node = WinchNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()