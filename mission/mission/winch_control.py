#!/usr/bin/env python3

import can
import sys
import time
from threading import Thread, Lock
from queue import Queue, Empty
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import String
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import MultiThreadedExecutor

class CANWinchNode(Node):
    """ROS2 node for controlling a winch via CAN bus with full reliability features."""

    def __init__(self):
        super().__init__('can_winch_node')
        
        # Configuration parameters
        self.declare_parameters(namespace='',
            parameters=[
                ('device', '/dev/ttyUSB0'),
                ('can_speed', 500000),
                ('baudrate', 2000000),
                ('motor_id', 1),
                ('movement_time', 2.0),
                ('keep_alive_interval', 0.3),
                ('bus_recovery_interval', 2.0),
                ('max_reconnect_attempts', 5)
            ])

        # Get parameters
        self.device = self.get_parameter('device').value
        self.can_speed = self.get_parameter('can_speed').value
        self.baudrate = self.get_parameter('baudrate').value
        self.motor_id = self.get_parameter('motor_id').value
        self.movement_time = self.get_parameter('movement_time').value
        self.keep_alive_interval = self.get_parameter('keep_alive_interval').value
        self.bus_recovery_interval = self.get_parameter('bus_recovery_interval').value
        self.max_reconnect_attempts = self.get_parameter('max_reconnect_attempts').value

        # State management
        self.bus = None
        self.bus_lock = Lock()
        self.reconnect_attempts = 0
        self.response_queue = Queue()
        self.last_command = None
        self.current_operation = None
        self.operation_step = 0
        self.operation_data = {}
        self.last_command_time = 0
        self.receiver_thread = None

        # Initialize system components
        self.setup_can_bus()
        self.setup_timers()
        self.setup_subscriptions()
        self.timer = None
        self.get_logger().info("CAN Winch Node initialized")

    def setup_subscriptions(self):
        """Initialize ROS2 subscriptions with proper QoS settings."""
        reliable_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        self.go_sub = self.create_subscription(
            String, '/go_winch', self.go_callback, reliable_qos,
            callback_group=MutuallyExclusiveCallbackGroup())

    def setup_timers(self):
        """Initialize all system timers."""
        # Bus health monitoring
        self.create_timer(
            self.bus_recovery_interval,
            self.check_bus_health,
            callback_group=MutuallyExclusiveCallbackGroup()
        )

        # Keep-alive mechanism
        self.create_timer(
            self.keep_alive_interval,
            self.send_keep_alive,
            callback_group=MutuallyExclusiveCallbackGroup()
        )

    def setup_can_bus(self):
        """Initialize or reinitialize CAN bus connection with locking."""
        with self.bus_lock:
            # Clean up existing connection
            if self.bus:
                try:
                    self.bus.shutdown()
                except Exception as e:
                    self.get_logger().error(f"Bus shutdown error: {e}")
                self.bus = None

            # Attempt new connection
            try:
                self.bus = can.interface.Bus(
                    interface='seeedstudio',
                    channel=self.device,
                    bitrate=self.can_speed,
                    baudrate=self.baudrate
                )
                self.reconnect_attempts = 0
                self.get_logger().info(f"Connected to CAN bus on {self.device}")
                self.start_receiver_thread()
            except Exception as e:
                self.bus = None
                self.get_logger().error(f"CAN bus initialization failed: {e}")
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    self.reconnect_attempts += 1
                    self.get_logger().info(f"Scheduling reconnect attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}")
                    self.create_timer(5.0, self.setup_can_bus)

    def start_receiver_thread(self):
        """Manage receiver thread lifecycle."""
        if self.receiver_thread and self.receiver_thread.is_alive():
            return

        self.receiver_thread = Thread(target=self.receive_messages, daemon=True)
        self.receiver_thread.start()
        self.get_logger().info("CAN receiver thread started")

    def check_bus_health(self):
        """Periodic bus health check and recovery."""
        if not self.bus or not self.receiver_thread.is_alive():
            self.get_logger().warning("CAN bus unhealthy, attempting recovery...")
            self.setup_can_bus()

    def send_keep_alive(self):
        """Maintain bus activity with empty messages during idle periods."""
        if self.current_operation is None and self.bus:
            try:
                with self.bus_lock:
                    empty_msg = can.Message(
                        arbitration_id=0x00,
                        data=[0x00]*8,
                        is_extended_id=False
                    )
                    self.bus.send(empty_msg)
                    self.get_logger().debug("Sent keep-alive message", 
                                          throttle_duration_sec=10)
            except Exception as e:
                self.get_logger().error(f"Keep-alive failed: {e}")
                self.bus = None

    def receive_messages(self):
        """Continuous CAN message reception with error handling."""
        self.get_logger().info("CAN receiver thread running")
        while rclpy.ok():
            if not self.bus:
                time.sleep(0.1)
                continue

            try:
                msg = self.bus.recv(0.1)
                if msg:
                    self.get_logger().debug(
                        f"RX id={msg.arbitration_id:#x} data={self.format_can_data(msg.data)}"
                    )
                    if self.last_command and msg.data[:2] == self.last_command:
                        self.response_queue.put(msg)
            except can.CanError as e:
                self.get_logger().error(f"CAN receive error: {e}")
                self.bus = None
            except Exception as e:
                self.get_logger().error(f"General receiver error: {e}")
                time.sleep(0.5)

    def format_can_data(self, data):
        """Format CAN data bytes as hexadecimal string."""
        return " ".join(f"{byte:02X}" for byte in data)

    def send_message(self, data, arbitration_id=None):
        """Thread-safe message sending with error recovery."""
        if not self.bus:
            self.get_logger().error("Message send failed: No active CAN bus")
            return False

        try:
            with self.bus_lock:
                message = can.Message(
                    arbitration_id=arbitration_id or self.motor_id,
                    data=data,
                    is_extended_id=False
                )
                self.bus.send(message)
                self.last_command = data[:2]
                self.last_command_time = time.time()
                self.get_logger().info(f"Sent message: {self.format_can_data(data)}")
                return True
        except can.CanError as e:
            self.get_logger().error(f"CAN send error: {e}")
            self.bus = None
            return False
        except Exception as e:
            self.get_logger().error(f"Unexpected send error: {e}")
            return False

    def parse_byte_string(self, byte_string):
        """Convert hex string to byte array."""
        try:
            return bytes.fromhex(byte_string)
        except ValueError as e:
            self.get_logger().error(f"Invalid byte string: {e}")
            return None

    def go_callback(self, msg):
        """Handle incoming movement commands."""
        self.get_logger().info(f"Received command: {msg.data}")
        if not self.bus:
            self.get_logger().error("CAN bus not available")
            return

        if self.current_operation:
            self.get_logger().warning(f"Operation {self.current_operation} already in progress")
            return

        if msg.data == 'UP':
            self.current_operation = 'UP'
            self.operation_step = 1
            self.execute_next_step()
        elif msg.data == 'DOWN':
            self.current_operation = 'DOWN'
            self.operation_step = 1
            self.execute_next_step()
        else:
            self.get_logger().warning(f"Invalid command: {msg.data}")

    def execute_next_step(self):
        """Execute the next step in the current operation sequence."""
        if not self.current_operation:
            return

        if self.current_operation == 'UP':
            self.execute_up_sequence()
        elif self.current_operation == 'DOWN':
            self.execute_down_sequence()

    def execute_up_sequence(self):
        """Full UP command sequence with error handling."""
        try:
            if self.operation_step == 1:
                # Initial UP command
                cmd = self.parse_byte_string("94 00 00 A0 C1 D0 07 00")
                if self.send_message(cmd):
                    self.create_timer_for_next_step(0.2)
                else:
                    self.reset_operation()

            elif self.operation_step == 2:
                # Secondary command
                cmd = self.parse_byte_string("91 00 00 00 00 00 00 00")
                if self.send_message(cmd):
                    self.create_timer_for_next_step(0.2)
                else:
                    self.reset_operation()

            elif self.operation_step == 3:
                # Movement delay
                self.get_logger().info(f"Waiting {self.movement_time}s for UP movement")
                self.create_timer_for_next_step(self.movement_time)

            elif self.operation_step == 4:
                # Position request
                cmd = self.parse_byte_string("B4 13 00 00 00 00 00 00")
                if self.send_message(cmd):
                    self.create_timer_for_next_step(0.1)
                else:
                    self.reset_operation()

            elif self.operation_step == 5:
                # Handle position response
                response = self.check_for_response()
                if response:
                    last_four = response.data[-4:]
                    self.operation_data['last_bytes'] = last_four
                    final_cmd = bytes([0x95]) + last_four + bytes([0x32, 0x14, 0x00])
                    final_cmd = final_cmd.ljust(8, b'\x00')
                    if self.send_message(final_cmd):
                        self.create_timer_for_next_step(0.2)
                    else:
                        self.reset_operation()
                else:
                    self.get_logger().error("No response for position request")
                    self.reset_operation()

            elif self.operation_step == 6:
                # Final confirmation
                self.get_logger().info("UP sequence completed")
                self.reset_operation()

        except Exception as e:
            self.get_logger().error(f"UP sequence error: {e}")
            self.reset_operation()

    def execute_down_sequence(self):
        """Full DOWN command sequence with error handling."""
        try:
            if self.operation_step == 1:
                # Initial DOWN command
                cmd = self.parse_byte_string("94 00 00 A0 41 D0 07 00")
                if self.send_message(cmd):
                    self.create_timer_for_next_step(0.2)
                else:
                    self.reset_operation()

            elif self.operation_step == 2:
                # Secondary command
                cmd = self.parse_byte_string("91 00 00 00 00 00 00 00")
                if self.send_message(cmd):
                    self.create_timer_for_next_step(0.2)
                else:
                    self.reset_operation()

            elif self.operation_step == 3:
                # Movement delay
                self.get_logger().info(f"Waiting {self.movement_time}s for DOWN movement")
                self.create_timer_for_next_step(self.movement_time)

            elif self.operation_step == 4:
                # Position request
                cmd = self.parse_byte_string("B4 13 00 00 00 00 00 00")
                if self.send_message(cmd):
                    self.create_timer_for_next_step(0.1)
                else:
                    self.reset_operation()

            elif self.operation_step == 5:
                # Handle position response
                response = self.check_for_response()
                if response:
                    last_four = response.data[-4:]
                    self.operation_data['last_bytes'] = last_four
                    final_cmd = bytes([0x95]) + last_four + bytes([0x32, 0x14, 0x00])
                    final_cmd = final_cmd.ljust(8, b'\x00')
                    if self.send_message(final_cmd):
                        self.create_timer_for_next_step(0.2)
                    else:
                        self.reset_operation()
                else:
                    self.get_logger().error("No response for position request")
                    self.reset_operation()

            elif self.operation_step == 6:
                # Final confirmation
                self.get_logger().info("DOWN sequence completed")
                self.reset_operation()

        except Exception as e:
            self.get_logger().error(f"DOWN sequence error: {e}")
            self.reset_operation()

    def create_timer_for_next_step(self, delay):
        """Schedule next operation step with safety checks."""
        if self.timer is not None:
            self.timer.cancel()
        self.operation_step += 1
        self.timer = self.create_timer(delay, self.execute_next_step)

    def check_for_response(self, wait_time=0.5):
        """Check for expected responses with timeout."""
        try:
            return self.response_queue.get(timeout=wait_time)
        except Empty:
            return None

    def reset_operation(self):
        """Reset operation state cleanly."""
        self.current_operation = None
        self.operation_step = 0
        self.operation_data = {}
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        self.get_logger().info("Operation reset")

    def shutdown(self):
        """Comprehensive shutdown procedure."""
        self.get_logger().info("Shutting down node...")
        if self.bus:
            with self.bus_lock:
                try:
                    self.bus.shutdown()
                except Exception as e:
                    self.get_logger().error(f"Bus shutdown error: {e}")
        self.destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = CANWinchNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        executor.shutdown()
        rclpy.shutdown()

if __name__ == '__main__':
    main()