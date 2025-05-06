#!/usr/bin/env python3

import can
import sys
import time
<<<<<<< HEAD
from threading import Thread
from queue import Queue, Empty

=======
from threading import Thread, Lock
from queue import Queue, Empty
>>>>>>> 890ee81 (mega haithem fix)
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import String
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import MultiThreadedExecutor

class CANWinchNode(Node):
    """ROS2 node for controlling a winch via CAN bus with reliability improvements."""

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
                ('keep_alive_interval', 0.3),  # 300ms between keep-alives
                ('bus_recovery_interval', 2.0),  # Check bus health every 2s
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
        self.keep_alive_active = False

        # Initialize system
        self.setup_can_bus()
        self.setup_timers()
        self.setup_subscriptions()

        self.get_logger().info("CAN Winch Node initialized")

    def setup_subscriptions(self):
        """Initialize ROS2 subscriptions with QoS settings."""
        reliable_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        self.go_sub = self.create_subscription(
            String, '/go_winch', self.go_callback, reliable_qos,
            callback_group=MutuallyExclusiveCallbackGroup())

    def setup_timers(self):
        """Initialize all timers with proper callback groups."""
        # Health check timer
        self.create_timer(
            self.bus_recovery_interval,
            self.check_bus_health,
            callback_group=MutuallyExclusiveCallbackGroup()
        )

        # Keep-alive timer
        self.create_timer(
            self.keep_alive_interval,
            self.send_keep_alive,
            callback_group=MutuallyExclusiveCallbackGroup()
        )

    def setup_can_bus(self):
        """Initialize or reinitialize CAN bus connection."""
        with self.bus_lock:
            if self.bus:
                try:
                    self.bus.shutdown()
                except Exception as e:
                    self.get_logger().error(f"Error shutting down bus: {e}")
                self.bus = None

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
                    self.get_logger().info("Scheduling reconnection attempt...")
                    self.reconnect_attempts += 1
                    self.create_timer(5.0, self.setup_can_bus)  # Retry after 5s

    def start_receiver_thread(self):
        """Start or restart the CAN message receiver thread."""
        if self.receiver_thread and self.receiver_thread.is_alive():
            return

        self.receiver_thread = Thread(target=self.receive_messages, daemon=True)
        self.receiver_thread.start()
        self.get_logger().info("CAN receiver thread started")

    def check_bus_health(self):
        """Periodically check and maintain bus connectivity."""
        if not self.bus or not self.receiver_thread.is_alive():
            self.get_logger().warning("CAN bus unhealthy, attempting recovery...")
            self.setup_can_bus()

    def send_keep_alive(self):
        """Maintain bus activity with empty messages when idle."""
        if self.current_operation is None and self.bus:
            try:
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

<<<<<<< HEAD
    '''def receive_messages(self):
        """Continuously receive messages from the CAN bus"""
        self.get_logger().info("Listening for CAN messages...")
        
        while rclpy.ok() and self.bus:
            try:
                message = self.bus.recv(0.1)  # Use timeout to allow clean thread exit
                if message:
                    current_time = time.time()
                    time_since_command = current_time - self.last_command_time
                    self.get_logger().info(f"Received from ID {message.arbitration_id}: {self.format_can_data(message.data)} (delay: {time_since_command:.3f}s)")
                    
                    # Add any message received to the queue if we're in an operation
                    # The check_for_response method will filter as needed
                    if self.current_operation is not None:
                        self.response_queue.put(message)
            except Exception as e:
                self.get_logger().error(f"Error in receiver thread: {e}")
                # Brief pause to avoid tight loop in case of persistent errors
                time.sleep(0.1)'''

    def receive_messages(self):
        """Continuously receive messages from the CAN bus."""
        self.get_logger().info("Listening for CAN messages...")
        while rclpy.ok() and self.bus:
            try:
                message = self.bus.recv(0.1)
                if not message:
                    continue

                self.get_logger().debug(
                    f"RX id={message.arbitration_id:#x} data={self.format_can_data(message.data)}")

                # Only enqueue if it is a response to the last command we sent
                if self.last_command and message.data[:2] == self.last_command:
                    self.response_queue.put(message)

            except Exception as exc:
                self.get_logger().error(f"Receiver error: {exc}")
=======
    def receive_messages(self):
        """Continuous CAN message receiver with bus health monitoring."""
        self.get_logger().info("CAN receiver thread started")
        while rclpy.ok():
            if not self.bus:
>>>>>>> 890ee81 (mega haithem fix)
                time.sleep(0.1)
                continue

<<<<<<< HEAD

    def check_for_response(self, wait_time=0.2):
        try:
            return self.response_queue.get(timeout=wait_time)
        except Empty:
            return None

=======
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
                self.get_logger().error(f"Receiver error: {e}")
                time.sleep(0.5)

    # ... (Keep existing message handling and command methods from original code) ...

    def send_message(self, data, arbitration_id=None):
        """Enhanced message sending with bus health checks."""
        if not self.bus:
            self.get_logger().error("Send failed: No active CAN bus")
            return False
>>>>>>> 890ee81 (mega haithem fix)

        try:
            with self.bus_lock:
                msg = can.Message(
                    arbitration_id=arbitration_id or self.motor_id,
                    data=data,
                    is_extended_id=False
                )
                self.bus.send(msg)
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

    def go_callback(self, msg):
        """Command handler with bus availability check."""
        if not self.bus:
            self.get_logger().error("Ignoring command: No active CAN bus")
            return

<<<<<<< HEAD
        # Determine which command to send based on message data
        if msg.data == 'UP':
            self.execute_command_sequence_up()
        elif msg.data == 'DOWN':
            self.execute_command_sequence_down()
        else:
            # Log if the command is unrecognized
            self.get_logger().warn(f"Unknown GO command: '{msg.data}'. Expected 'UP' or 'DOWN'.")

    def execute_command_sequence_up(self):
        """Start the UP command sequence using timers"""
        self.current_operation = 'UP'
        self.operation_step = 1
        self.operation_data = {}
        
        # Start the sequence with the first step
        self.get_logger().info("Starting UP sequence")
        self.execute_next_step()

    def execute_command_sequence_down(self):
        """Start the DOWN command sequence using timers"""
        self.current_operation = 'DOWN'
        self.operation_step = 1
        self.operation_data = {}
        
        # Start the sequence with the first step
        self.get_logger().info("Starting DOWN sequence")
        self.execute_next_step()

    def execute_next_step(self):
        """Execute the next step in the current operation sequence"""
        if not self.current_operation:
            return
            
        if self.current_operation == 'UP':
            if self.operation_step == 1:
                # Step 1: Send command 94 00 00 A0 C1 D0 07 00
                self.get_logger().info("Step 1: Sending initial UP command")
                data = self.parse_byte_string("94 00 00 A0 C1 D0 07 00")
                if data and self.send_message(data):
                    # Give some time to capture response before moving to next step
                    # We'll check for this response in the next step
                    self.create_timer_for_next_step(0.2)
                else:
                    self.reset_operation()
                    
            elif self.operation_step == 2:
                # Check for response to previous command
                response = self.check_for_response()
                if not response:
                    self.get_logger().warn("No response to UP command 1, continuing anyway")
                else:
                    self.get_logger().info(f"Response to command 1: {self.format_can_data(response.data)}")
                
                # Step 2: Send command 91 00 00 00 00 00 00 00
                self.get_logger().info("Step 2: Sending second UP command")
                data = self.parse_byte_string("91 00 00 00 00 00 00 00")
                if data and self.send_message(data):
                    # Set timer to check for response and move to next step
                    self.create_timer_for_next_step(0.2)
                else:
                    self.reset_operation()
                    
            elif self.operation_step == 3:
                # Check for response to previous command
                response = self.check_for_response()
                if not response:
                    self.get_logger().warn("No response to UP command 2, continuing anyway")
                else:
                    self.get_logger().info(f"Response to command 2: {self.format_can_data(response.data)}")
                
                # Wait for movement_time seconds before proceeding
                self.get_logger().info(f"Waiting {self.movement_time} seconds for UP movement...")
                self.create_timer_for_next_step(self.movement_time)
                
            elif self.operation_step == 4:
                # Step 3: Send command B4 13 00 00 00 00 00 00
                
                self.get_logger().info("Step 3: Sending command to get data for UP")
                data = self.parse_byte_string("B4 13 00 00 00 00 00 00")
                if data and self.send_message(data):
                    # IMPORTANT: Use a short delay to check for response to B4 command
                    # This ensures we don't miss the response which may come quickly
                    self.create_timer_for_next_step(0.1)
                else:
                    self.reset_operation()
                    
            elif self.operation_step == 5:
                # Check for response to B4 command - wait a bit longer to ensure we catch it
                self.get_logger().info("Waiting for response to B4 command...")
                response = self.check_for_response(wait_time=0.5)
                
                if response:
                    self.get_logger().info(f"Received response to B4: {self.format_can_data(response.data)}")
                    # Extract last 4 bytes from response
                    last_four_bytes = response.data[-4:]
                    self.get_logger().info(f"Extracted 4 bytes: {self.format_can_data(last_four_bytes)}")
                    self.operation_data['last_four_bytes'] = last_four_bytes
                    
                    # Step 4: Send command 95 [4 bytes] 32 14 00
                    self.get_logger().info("Step 4: Sending final UP command with extracted bytes")
                    final_command = bytes([0x95]) + last_four_bytes + bytes([0x32, 0x14, 0x00])
                    
                    # Ensure it's exactly 8 bytes
                    if len(final_command) > 8:
                        final_command = final_command[:8]
                    elif len(final_command) < 8:
                        final_command = final_command + bytes([0x00] * (8 - len(final_command)))
                    
                    self.get_logger().info(f"Final UP command: {self.format_can_data(final_command)}")
                    if self.send_message(final_command):
                        # Set timer to check for response and finish
                        self.create_timer_for_next_step(0.2)
                    else:
                        self.reset_operation()
                else:
                    # Try looking for any message in the queue that might have the format we need
                    self.get_logger().error("Error: No direct response to UP command B4")
                    self.get_logger().info("Checking if there are any messages we can use...")
                    
                    # If no response, check if we have any received messages from ID 0
                    # Send a dummy command to ping the device and get any response
                    data = self.parse_byte_string("91 00 00 00 00 00 00 00")
                    if data and self.send_message(data):
                        # Wait a bit to see if we get any response
                        response = self.check_for_response(wait_time=0.3)
                        if response:
                            self.get_logger().info(f"Found usable response: {self.format_can_data(response.data)}")
                            # Try to use this response
                            last_four_bytes = response.data[-4:]
                            self.operation_data['last_four_bytes'] = last_four_bytes
                            
                            # Continue with final command
                            final_command = bytes([0x95]) + last_four_bytes + bytes([0x32, 0x14, 0x00])
                            if len(final_command) > 8:
                                final_command = final_command[:8]
                            elif len(final_command) < 8:
                                final_command = final_command + bytes([0x00] * (8 - len(final_command)))
                            
                            self.get_logger().info(f"Final UP command (from alternate response): {self.format_can_data(final_command)}")
                            if self.send_message(final_command):
                                self.create_timer_for_next_step(0.2)
                                return
                    
                    self.get_logger().error("Could not find any usable response data")
                    self.reset_operation()
                    
            elif self.operation_step == 6:
                # Check for response to final command
                response = self.check_for_response(wait_time= 2)
                if response:
                    self.get_logger().info(f"Final UP response: {self.format_can_data(response.data)}")
                    self.get_logger().info("UP command sequence completed successfully")
                else:
                    self.get_logger().warn("No response to final UP command")
                
                # Operation complete
                self.reset_operation()
                
        elif self.current_operation == 'DOWN':
            if self.operation_step == 1:
                # Step 1: Send command 94 00 00 A0 41 D0 07 00
                self.get_logger().info("Step 1: Sending initial DOWN command")
                data = self.parse_byte_string("94 00 00 A0 41 D0 07 00")
                if data and self.send_message(data):
                    # Give some time to capture response before moving to next step
                    # self.create_timer_for_next_step(0.2)
                    self.create_timer_for_next_step(200)
                else:
                    self.reset_operation()
                    
            elif self.operation_step == 2:
                # Check for response to previous command
                response = self.check_for_response()
                if not response:
                    self.get_logger().warn("No response to DOWN command 1, continuing anyway")
                else:
                    self.get_logger().info(f"Response to command 1: {self.format_can_data(response.data)}")
                
                # Step 2: Send command 91 00 00 00 00 00 00 00
                self.get_logger().info("Step 2: Sending second DOWN command")
                data = self.parse_byte_string("91 00 00 00 00 00 00 00")
                if data and self.send_message(data):
                    # Set timer to check for response and move to next step
                    # self.create_timer_for_next_step(0.2)
                    self.create_timer_for_next_step(200)

                else:
                    self.reset_operation()
                    
            elif self.operation_step == 3:
                # Check for response to previous command
                response = self.check_for_response()
                if not response:
                    self.get_logger().warn("No response to DOWN command 2, continuing anyway")
                else:
                    self.get_logger().info(f"Response to command 2: {self.format_can_data(response.data)}")
                
                # Wait for movement_time seconds before proceeding
                self.get_logger().info(f"Waiting {self.movement_time} seconds for DOWN movement...")
                self.create_timer_for_next_step(self.movement_time)
                
            elif self.operation_step == 4:
                # Step 3: Send command B4 13 00 00 00 00 00 00
                self.get_logger().info("Step 3: Sending command to get data for DOWN")
                data = self.parse_byte_string("B4 13 00 00 00 00 00 00")
                if data and self.send_message(data):
                    # IMPORTANT: Use a short delay to check for response to B4 command
                    # This ensures we don't miss the response which may come quickly
                    self.create_timer_for_next_step(0.1)
                else:
                    self.reset_operation()
                    
            elif self.operation_step == 5:
                # Check for response to B4 command - wait a bit longer to ensure we catch it
                self.get_logger().info("Waiting for response to B4 command...")
                response = self.check_for_response(wait_time=0.5)
                
                if response:
                    self.get_logger().info(f"Received response to B4: {self.format_can_data(response.data)}")
                    # Extract last 4 bytes from response
                    last_four_bytes = response.data[-4:]
                    self.get_logger().info(f"Extracted 4 bytes: {self.format_can_data(last_four_bytes)}")
                    self.operation_data['last_four_bytes'] = last_four_bytes
                    
                    # Step 4: Send command 95 [4 bytes] 32 14 00
                    self.get_logger().info("Step 4: Sending final DOWN command with extracted bytes")
                    final_command = bytes([0x95]) + last_four_bytes + bytes([0x32, 0x14, 0x00])
                    
                    # Ensure it's exactly 8 bytes
                    if len(final_command) > 8:
                        final_command = final_command[:8]
                    elif len(final_command) < 8:
                        final_command = final_command + bytes([0x00] * (8 - len(final_command)))
                    
                    self.get_logger().info(f"Final DOWN command: {self.format_can_data(final_command)}")
                    if self.send_message(final_command):
                        # Set timer to check for response and finish
                        self.create_timer_for_next_step(0.2)
                    else:
                        self.reset_operation()
                else:
                    # Try looking for any message in the queue that might have the format we need
                    self.get_logger().error("Error: No direct response to DOWN command B4")
                    self.get_logger().info("Checking if there are any messages we can use...")
                    
                    # If no response, check if we have any received messages from ID 0
                    # Send a dummy command to ping the device and get any response
                    data = self.parse_byte_string("91 00 00 00 00 00 00 00")
                    if data and self.send_message(data):
                        # Wait a bit to see if we get any response
                        response = self.check_for_response(wait_time=0.3)
                        if response:
                            self.get_logger().info(f"Found usable response: {self.format_can_data(response.data)}")
                            # Try to use this response
                            last_four_bytes = response.data[-4:]
                            self.operation_data['last_four_bytes'] = last_four_bytes
                            
                            # Continue with final command
                            final_command = bytes([0x95]) + last_four_bytes + bytes([0x32, 0x14, 0x00])
                            if len(final_command) > 8:
                                final_command = final_command[:8]
                            elif len(final_command) < 8:
                                final_command = final_command + bytes([0x00] * (8 - len(final_command)))
                            
                            self.get_logger().info(f"Final DOWN command (from alternate response): {self.format_can_data(final_command)}")
                            if self.send_message(final_command):
                                self.create_timer_for_next_step(0.2)
                                return
                    
                    self.get_logger().error("Could not find any usable response data")
                    self.reset_operation()
                    
            elif self.operation_step == 6:
                # Check for response to final command
                response = self.check_for_response(wait_time=2)
                if response:
                    self.get_logger().info(f"Final DOWN response: {self.format_can_data(response.data)}")
                    self.get_logger().info("DOWN command sequence completed successfully")
                else:
                    self.get_logger().warn("No response to final DOWN command")
                
                # Operation complete
                self.reset_operation()

    def create_timer_for_next_step(self, delay):
        """Create a one-shot timer to execute the next step after a delay"""
        # Cancel any existing timer
        if self.timer:
            self.timer.cancel()
        
        # Increment step counter
        self.operation_step += 1

        # Create new timer
        self.timer = self.create_timer(
            delay, 
            self.timer_callback,
            callback_group=self.timer_callback_group
        )

    def timer_callback(self):
        """Called when the timer expires"""
        # Cancel the timer since we only want it to fire once
        self.timer.cancel()
        self.timer = None
        
        # Execute the next step in the sequence
        self.execute_next_step()

    def reset_operation(self):
        """Reset the operation state"""
        self.current_operation = None
        self.operation_step = 0
        self.operation_data = {}
        
        # Cancel any pending timer
        if self.timer:
            self.timer.cancel()
            self.timer = None
=======
        # ... (Keep existing command handling logic) ...
>>>>>>> 890ee81 (mega haithem fix)

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