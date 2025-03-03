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
        self.send_can_command("91 00 00 00 00 00 00 00", "Start Motor")
    
        # 2. Set speed control (clockwise rotation)
        # Using Speed Control command (0x94) with positive speed value
        # Example: 50 RPM for 2 seconds
        # 0x94 00 00 48 42 D0 07 00 = 50 RPM for 2000ms
        # Speed is in IEEE float format with LSB byte order
        self.send_can_command("94 00 00 48 42 D0 07 00", "Speed Control (50 RPM clockwise)")
        
        # 4. Stop the motor
        self.send_can_command("92 00 00 00 00 00 00 00", "Stop Motor")

    def go_down(self):
        self.send_can_command("91 00 00 00 00 00 00 00", "Start Motor")
    
        # 2. Set speed control (clockwise rotation)
        # Using Speed Control command (0x94) with positive speed value
        # Example: 50 RPM for 2 seconds
        # 0x94 00 00 48 42 D0 07 00 = 50 RPM for 2000ms
        # Speed is in IEEE float format with LSB byte order
        self.send_can_command("94 00 00 48 C2 D0 07 00", "Speed Control (50 RPM counter-clockwise)")

        
        # 4. Stop the motor
        self.send_can_command("92 00 00 00 00 00 00 00", "Stop Motor")

    def go_callback(self, msg):
        self.get_logger().info(f"GO MESSAGE : {msg.data}")
        if msg.data == 'UP':
            self.go_up()
        if msg.data == 'DOWN':
            self.go_down()
    
    def v_accel(self, msg):
        self.get_logger().info(f"Vertical accel : {msg.linear_acceleration.z}")

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