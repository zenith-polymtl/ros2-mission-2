import can
import time
import struct
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_msgs.msg import Float32 # *** Import Float32 for the position topic ***
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy # Import more QoS options
from threading import Thread
from queue import Queue, Empty # Import Empty exception

class WinchNode(Node):
    def __init__(self):
        super().__init__('winch_node')

        # --- QoS Profiles ---
        # Reliable profile for commands where we want delivery confirmation (if supported by RMW)
        # Best effort might be suitable too depending on network conditions.
        reliable_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE # Doesn't need to persist old commands
        )
        # QoS for sensor data (like position) - often best effort is fine,
        # and keep last ensures we get the latest value if we connect late.
        sensor_qos = QoSProfile(
            depth=1, # Only keep the latest message
            reliability=ReliabilityPolicy.BEST_EFFORT, # Less overhead than reliable
            durability=DurabilityPolicy.VOLATILE # No need to store history
        )


        # --- ROS2 Subscribers ---
        self.subscriber_ = self.create_subscription(
            String, '/go_winch', self.go_callback, reliable_qos) # Use reliable for commands
        self.init_sub = self.create_subscription(
            String, '/init_motor', self.init_callback, reliable_qos) # Use reliable for commands
        self.stop_sub = self.create_subscription(
            String, '/close_motor', self.stop_callback, reliable_qos) # Use reliable for commands

        # *** NEW: Subscriber for the motor position topic from WaterNode ***
        self.position_sub = self.create_subscription(
            Float32,
            '/motor_position', # Topic name published by WaterNode
            self.position_topic_callback, # New callback function
            sensor_qos # Use sensor QoS profile
        )

        # --- Configuration Parameters ---
        self.declare_parameter('device', '/dev/ttyUSB0')
        self.declare_parameter('can_speed', 500000)
        self.declare_parameter('baudrate', 2000000)
        self.declare_parameter('motor_id', 1)
        self.declare_parameter('debug_level', 1)  # 0=minimal, 1=normal, 2=verbose, 3=most verbose

        # --- Get Parameters ---
        self.device = self.get_parameter('device').value
        self.can_speed = self.get_parameter('can_speed').value
        self.baudrate = self.get_parameter('baudrate').value
        self.motor_id = self.get_parameter('motor_id').value
        self.debug_level = self.get_parameter('debug_level').value

        # --- CAN Commands ---
        # Commands remain the same, including GET_POSITION for init_callback
        self.STOP_COMMAND = bytes([0x92, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        self.START_COMMAND = bytes([0x91, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        self.UP_COMMAND = bytes([0x94, 0x00, 0x00, 0xA0, 0xC1, 0xD0, 0x07, 0x00])
        self.DOWN_COMMAND = bytes([0x94, 0x80, 0x00, 0xA0, 0x41, 0xD0, 0x07, 0x00])
        self.GET_POSITION_COMMAND = bytes([0xB4, 0x13, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) # Still needed for init

        # --- State Tracking ---
        self.current_operation = None  # 'UP' or 'DOWN'
        self.position_timer = None
        # *** NEW: Variable to store the latest position received from the topic ***
        self.last_known_position = None # Initialize to None, indicating no position received yet

        # --- CAN Communication Setup ---
        self.can_message_queue = Queue()
        self._running = True
        self._receiver_thread = None
        self.bus = self.setup_can_bus()

        if self.bus:
            self._receiver_thread = Thread(target=self._receive_can_messages)
            self._receiver_thread.daemon = True
            self._receiver_thread.start()
            self.debug_print("CAN receiver thread started", level=1)
        else:
            self.get_logger().error("CAN bus failed to initialize. Node functionality will be limited.")

        self.get_logger().info('Winch Node initialized')

    # --- Debugging and CAN Utilities (mostly unchanged) ---

    def debug_print(self, message, level=1):
        """Print debug message based on debug level"""
        if self.debug_level >= level:
            self.get_logger().info(f"DEBUG[{level}]: {message}")

    def format_can_data(self, data):
        """Format CAN data as space-separated hex bytes"""
        if not data: return "EMPTY_DATA"
        try:
            if isinstance(data, (bytes, bytearray, list)):
                return " ".join([f"{byte:02X}" for byte in data])
            else: return str(data)
        except Exception as e:
            self.get_logger().error(f"Error formatting CAN data: {e}")
            return "ERROR_FORMATTING_DATA"

    def setup_can_bus(self):
        """Initialize the CAN bus connection"""
        try:
            bus = can.interface.Bus(
                interface='seeedstudio', channel=self.device,
                bitrate=self.can_speed, baudrate=self.baudrate,
                receive_own_messages=True
            )
            self.get_logger().info(f"Connected to CAN bus on {self.device}")
            return bus
        except Exception as e:
            self.get_logger().error(f"Error setting up CAN bus on {self.device}: {e}")
            return None

    def _receive_can_messages(self):
        """Continuous loop to receive CAN messages and put them in a queue"""
        self.debug_print("CAN receiver thread is running", level=2)
        if not self.bus:
             self.get_logger().error("Receiver thread cannot start, CAN bus not initialized.")
             self._running = False
             return
        while self._running:
            try:
                msg = self.bus.recv(timeout=0.1)
                if msg and msg.data is not None:
                     self.can_message_queue.put(msg)
                     self.debug_print(
                         f"Received and queued message: ID={msg.arbitration_id}, data={self.format_can_data(msg.data)}",
                         level=3
                     )
            except can.CanError as e:
                self.get_logger().error(f"CAN receive error in thread: {e}", throttle_duration_sec=1.0)
            except Exception as e:
                self.get_logger().error(f"Unexpected error in CAN receiver thread: {e}", throttle_duration_sec=1.0)
        self.debug_print("CAN receiver thread stopped", level=2)

    def send_message(self, data, arbitration_id=None):
        """Send a message with the specified data to the CAN bus"""
        if not self.bus:
            self.get_logger().error("CAN bus is not initialized. Cannot send message.")
            return False
        if arbitration_id is None: arbitration_id = self.motor_id
        if not isinstance(data, bytes) or len(data) != 8:
            self.get_logger().error(f"Error: Message data must be exactly 8 bytes (got {type(data)}, len={len(data) if isinstance(data, (bytes, list)) else 'N/A'})")
            return False
        message = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)
        try:
            self.bus.send(message)
            self.debug_print(f"Sent message: ID={arbitration_id}, data={self.format_can_data(data)}", level=1)
            return True
        except Exception as e:
            self.get_logger().error(f"Error sending message: {e}")
            return False

    def get_response_from_queue(self, timeout=3.0, expected_arbitration_id=None, expected_data_prefix=None):
        """Gets a message from the queue that matches criteria (used by init_callback)"""
        self.debug_print(f"Waiting for message in queue with ID={expected_arbitration_id}, prefix={self.format_can_data(expected_data_prefix) if expected_data_prefix else 'any'} for {timeout}s", level=1)
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                msg = self.can_message_queue.get(block=False)
                if msg and hasattr(msg, 'arbitration_id') and hasattr(msg, 'data') and msg.data is not None:
                    self.debug_print(f"Pulled message from queue for check: ID={msg.arbitration_id}, data={self.format_can_data(msg.data)}", level=3)
                    match = True
                    if expected_arbitration_id is not None and msg.arbitration_id != expected_arbitration_id: match = False
                    if expected_data_prefix is not None and (not msg.data or len(msg.data) < len(expected_data_prefix) or not msg.data.startswith(expected_data_prefix)): match = False
                    if match:
                        self.debug_print(f"Found matching response from queue: ID={msg.arbitration_id}, data={self.format_can_data(msg.data)}", level=1)
                        return msg
            except Empty: time.sleep(0.01)
            except Exception as e:
                self.get_logger().error(f"Error getting message from queue: {e}", throttle_duration_sec=1.0)
                time.sleep(0.01)
        self.debug_print("Timeout waiting for response in queue", level=1)
        return None

    def _clear_position_related_queue_messages(self):
        """Clears messages from the queue (used before waiting for specific responses)"""
        self.debug_print("Attempting to clear queue of potentially stale messages", level=2)
        count = 0
        while True:
            try:
                msg = self.can_message_queue.get(block=False)
                count += 1
                self.debug_print(f"Discarded message during clear: ID={msg.arbitration_id}, data={self.format_can_data(msg.data)}", level=3)
            except Empty:
                self.debug_print(f"Queue clear attempt finished. Discarded {count} messages.", level=2)
                break
            except Exception as e:
                self.get_logger().error(f"Error clearing queue: {e}", throttle_duration_sec=1.0)
                break

    # --- ROS2 Callbacks ---

    def init_callback(self, msg):
        """
        Initialize the motor using direct CAN communication.
        Sends GET_POSITION, waits for response, sends SET_POSITION.
        This remains unchanged as it's a one-time setup.
        """
        if msg.data == 'INIT':
            self.get_logger().info("Motor Initialization Command Received (using direct CAN)")
            if not self.bus:
                self.get_logger().error("CAN bus not initialized, cannot initialize motor.")
                return

            self._clear_position_related_queue_messages()
            self.send_message(self.GET_POSITION_COMMAND)
            self.debug_print("Sent initialization command (Get Position): B4 13...", level=1)

            response = self.get_response_from_queue(
                timeout=3.0,
                expected_arbitration_id=self.motor_id,
                expected_data_prefix=bytes([0xB4, 0x13])
            )

            if response:
                self.debug_print(f"Received response to Get Position from queue: {self.format_can_data(response.data)}", level=1)
                if len(response.data) >= 8:
                    response_bytes = response.data[4:8]
                    second_command = bytes([0x95]) + response_bytes + bytes([0x32, 0x14, 0x00])
                    # Ensure 8 bytes (padding/truncating)
                    if len(second_command) != 8:
                         padding = bytes([0x00] * (8 - len(second_command))) if len(second_command) < 8 else b''
                         second_command = (second_command + padding)[:8]
                         self.get_logger().warn(f"Adjusted Set Position command length to 8 bytes.")

                    self.send_message(second_command)
                    self.debug_print(f"Sent second command (Set Position): {self.format_can_data(second_command)}", level=1)
                    self.send_message(self.START_COMMAND) # Send START to finish init
                    self.debug_print("Sent idle command (Start) after init.", level=1)
                    self.get_logger().info("Motor initialization sequence completed (direct CAN)")
                else:
                    self.get_logger().error(f"Initialization response from queue too short ({len(response.data)} bytes).")
            else:
                self.get_logger().error("No response received for Get Position from queue during initialization.")
                self.send_message(self.START_COMMAND) # Recovery attempt
                self.debug_print("Sent START command as recovery after init response timeout.", level=1)

    def stop_callback(self, msg):
        """Stop the motor"""
        if msg.data == 'CLOSE':
            self.get_logger().info("Motor Stop Command Received")
            if not self.bus:
                self.get_logger().error("CAN bus not initialized, cannot send stop command.")
                return
            if self.position_timer:
                self.position_timer.cancel()
                self.position_timer = None
                self.debug_print("Cancelled position timer on stop command", level=1)
            self._clear_position_related_queue_messages() # Clear queue on stop
            self.send_message(self.STOP_COMMAND)
            self.debug_print("Sent stop command: 92 00...", level=1)
            self.get_logger().info("Motor stop command sent")
            self.current_operation = None

    def go_callback(self, msg):
        """Handle go up/down commands"""
        self.get_logger().info(f"GO MESSAGE Received: {msg.data}")
        if not self.bus:
             self.get_logger().error("CAN bus not initialized, cannot perform GO movement.")
             return
        if self.current_operation is not None:
             self.get_logger().warn(f"Ignoring GO command '{msg.data}', motor is currently performing '{self.current_operation}'")
             return
        if msg.data == 'UP': self.go_up()
        elif msg.data == 'DOWN': self.go_down()
        else: self.get_logger().warn(f"Received unknown GO command: '{msg.data}'. Expected 'UP' or 'DOWN'.")

    def go_up(self):
        """Command the winch to go up and start the timer for position setting"""
        self.current_operation = 'UP'
        self.get_logger().info("Starting UP movement sequence")
        self._clear_position_related_queue_messages() # Clear queue before move
        if self.send_message(self.UP_COMMAND):
            self.debug_print("Sent UP command: 94 00...", level=1)
            if self.send_message(self.START_COMMAND):
                self.debug_print("Sent START command after UP command.", level=1)
                if self.position_timer: self.position_timer.cancel()
                # Timer triggers get_position_callback which now uses the topic value
                self.position_timer = self.create_timer(2.0, self.get_position_callback)
                self.debug_print("Position timer created for 2.0 seconds (will use topic value)", level=2)
            else:
                 self.get_logger().error("Failed to send START command after UP.")
                 self.current_operation = None
        else:
            self.get_logger().error("Failed to send UP command.")
            self.current_operation = None

    def go_down(self):
        """Command the winch to go down and start the timer for position setting"""
        self.current_operation = 'DOWN'
        self.get_logger().info("Starting DOWN movement sequence")
        self._clear_position_related_queue_messages() # Clear queue before move
        if self.send_message(self.DOWN_COMMAND):
            self.debug_print("Sent DOWN command: 94 80...", level=1)
            if self.send_message(self.START_COMMAND):
                self.debug_print("Sent START command after DOWN command.", level=1)
                if self.position_timer: self.position_timer.cancel()
                # Timer triggers get_position_callback which now uses the topic value
                self.position_timer = self.create_timer(2.0, self.get_position_callback)
                self.debug_print("Position timer created for 2.0 seconds (will use topic value)", level=2)
            else:
                 self.get_logger().error("Failed to send START command after DOWN.")
                 self.current_operation = None
        else:
            self.get_logger().error("Failed to send DOWN command.")
            self.current_operation = None

    # *** NEW: Callback for the /motor_position topic subscription ***
    def position_topic_callback(self, msg):
        """Stores the latest position received from the /motor_position topic."""
        self.last_known_position = msg.data
        self.debug_print(f"Received position from topic: {self.last_known_position:.4f}", level=2)

    # *** MODIFIED: Callback for timer after movement ***
    def get_position_callback(self):
        """
        Callback for timer after UP/DOWN movement.
        Uses the position received from the /motor_position topic
        to send the SET_POSITION command.
        """
        self.debug_print("get_position_callback triggered by timer (using topic value)", level=1)

        # Cancel the timer
        if self.position_timer:
            self.position_timer.cancel()
            self.position_timer = None
            self.debug_print("Position timer cancelled within get_position_callback", level=2)

        if not self.bus:
            self.get_logger().error("CAN bus not initialized, cannot set position in callback.")
            self.current_operation = None
            return

        self.get_logger().info(f"Setting position after {self.current_operation if self.current_operation else 'timed'} movement phase using topic value.")

        # --- Get position from stored topic value ---
        if self.last_known_position is None:
            self.get_logger().error("Cannot set position: No position value received from /motor_position topic yet.")
            # Send START command as a recovery attempt? Or just fail? Let's try START.
            self.send_message(self.START_COMMAND)
            self.debug_print("Sent START command as recovery after failing to get topic position.", level=1)
            self.current_operation = None # Reset state
            return

        # --- Convert the float position to 4 bytes (little-endian) ---
        try:
            # '<f' means little-endian float (4 bytes)
            position_bytes = struct.pack('<f', self.last_known_position)
            self.debug_print(f"Packed position {self.last_known_position:.4f} to bytes: {self.format_can_data(position_bytes)}", level=2)
        except struct.error as e:
            self.get_logger().error(f"Error packing position float {self.last_known_position} to bytes: {e}")
            # Send START command as recovery
            self.send_message(self.START_COMMAND)
            self.debug_print("Sent START command as recovery after failing to pack position.", level=1)
            self.current_operation = None # Reset state
            return
        except Exception as e: # Catch any other unexpected errors during packing
             self.get_logger().error(f"Unexpected error packing position float: {e}")
             self.send_message(self.START_COMMAND)
             self.debug_print("Sent START command as recovery after unexpected packing error.", level=1)
             self.current_operation = None # Reset state
             return


        # --- Construct and send the SET_POSITION command (0x95) ---
        # Command structure: 0x95 + 4 position bytes + 0x32 + 0x14 + 0x00
        set_position_command_base = bytes([0x95]) + position_bytes + bytes([0x32, 0x14, 0x00])

        # Ensure it's exactly 8 bytes (padding/truncating)
        if len(set_position_command_base) != 8:
            padding = bytes([0x00] * (8 - len(set_position_command_base))) if len(set_position_command_base) < 8 else b''
            set_position_command = (set_position_command_base + padding)[:8] # Combine, pad if needed, then truncate if needed
            self.get_logger().warn(f"Adjusted Set Position command length to 8 bytes.")
        else:
            set_position_command = set_position_command_base

        if self.send_message(set_position_command):
             self.debug_print(f"Sent set position command using topic value: {self.format_can_data(set_position_command)}", level=1)

             # --- Send the final START command ---
             if self.send_message(self.START_COMMAND):
                  self.debug_print("Sent START command to complete movement sequence", level=1)
                  self.get_logger().info(f"Completed {self.current_operation if self.current_operation else 'timed'} movement sequence successfully (using topic position)")
             else:
                  self.get_logger().error("Failed to send final START command after setting position.")
                  self.get_logger().warn(f"Completed {self.current_operation if self.current_operation else 'timed'} movement sequence with errors in final step.")

        else:
             self.get_logger().error("Failed to send set position command (using topic value).")
             self.get_logger().warn(f"Completed {self.current_operation if self.current_operation else 'timed'} movement sequence with errors in set position step.")
             # Try sending START anyway?
             self.send_message(self.START_COMMAND)
             self.debug_print("Sent START command as recovery after failing to send set position.", level=1)


        # Always reset operation state at the end
        self.current_operation = None


    def shutdown(self):
        """Clean shutdown procedures"""
        self.get_logger().info("Shutting down winch node...")
        self._running = False
        if self._receiver_thread and self._receiver_thread.is_alive():
             self.debug_print("Waiting for receiver thread to join...", level=2)
             self._receiver_thread.join(timeout=1.0)
        if hasattr(self, 'bus') and self.bus:
            self.get_logger().info("Sending stop command before CAN bus shutdown.")
            self.send_message(self.STOP_COMMAND) # Send stop before closing bus
            time.sleep(0.1)
            try:
                self.bus.shutdown()
                self.get_logger().info("CAN bus shut down successfully")
            except Exception as e:
                self.get_logger().error(f"Error during CAN bus shutdown: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = WinchNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Keyboard interrupt received. Shutting down.")
    except Exception as e:
        node.get_logger().fatal(f"Unhandled exception during spin: {e}")
    finally:
        node.shutdown()
        # node.destroy_node() # Optional explicit destruction
        rclpy.shutdown()

if __name__ == '__main__':
    main()
