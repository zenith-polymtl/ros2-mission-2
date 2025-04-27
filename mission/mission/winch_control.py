import can
import time
import struct
from collections import deque
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32, Float32
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from threading import Thread
from queue import Queue, Empty

class WinchNode(Node):
    def __init__(self):
        super().__init__('motor_control_node') # New node name

        # --- QoS Profiles ---
        reliable_qos = QoSProfile(
            depth=10, reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE
        )
        sensor_qos = QoSProfile( # For published sensor data
            depth=1, reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE # Use VOLATILE unless you need late joiners to get the last value
        )

        # --- Parameters (Combined from both nodes) ---
        self.declare_parameter('device', '/dev/ttyUSB0')
        self.declare_parameter('can_speed', 500000)
        self.declare_parameter('baudrate', 2000000)
        self.declare_parameter('motor_id', 1)
        self.declare_parameter('polling_rate', 2.0)  # Hz (from WaterNode)
        self.declare_parameter('filter_window', 11) # (from WaterNode)
        self.declare_parameter('debug_level', 1)     # 0=min, 1=norm, 2=verb, 3=max
        # Physics Constants (from WaterNode)
        self.declare_parameter('torque_constant', 0.065) # Nm/A
        self.declare_parameter('drum_radius', 0.0235)    # m
        self.declare_parameter('gear_ratio', 10.0)       # 10:1
        self.declare_parameter('dead_weight', 0.74)      # kg
        self.declare_parameter('water_density', 1.0)     # kg/L or g/mL

        # --- Get Parameters ---
        self.device = self.get_parameter('device').value
        self.can_speed = self.get_parameter('can_speed').value
        self.baudrate = self.get_parameter('baudrate').value
        self.motor_id = self.get_parameter('motor_id').value
        self.polling_rate = self.get_parameter('polling_rate').value
        self.filter_window = self.get_parameter('filter_window').value
        self.debug_level = self.get_parameter('debug_level').value
        self.torque_constant = self.get_parameter('torque_constant').value
        self.drum_radius = self.get_parameter('drum_radius').value
        self.gear_ratio = self.get_parameter('gear_ratio').value
        self.dead_weight = self.get_parameter('dead_weight').value
        self.water_density = self.get_parameter('water_density').value

        # --- Publishers (Combined) ---
        self.water_qty_pub = self.create_publisher(Int32, '/water_qty', sensor_qos)
        self.torque_pub = self.create_publisher(Float32, '/torque', sensor_qos)
        self.position_pub = self.create_publisher(Float32, '/motor_position', sensor_qos)

        # --- Subscribers (From WinchNode) ---
        self.go_sub = self.create_subscription(
            String, '/go_winch', self.go_callback, reliable_qos)
        self.init_sub = self.create_subscription(
            String, '/init_motor', self.init_callback, reliable_qos)
        self.stop_sub = self.create_subscription(
            String, '/close_motor', self.stop_callback, reliable_qos)

        # --- State Variables (Combined) ---
        self.current = 0.0          # Last measured current (A)
        self.torque = 0.0           # Last calculated filtered torque (Nm)
        self.volume = 0             # Last calculated water volume (mL)
        self.position = 0.0         # Last measured/known position (motor units)
        self.torque_buffer = deque(maxlen=self.filter_window) # For moving average
        self.current_operation = None # Tracks 'UP', 'DOWN', 'INIT' etc.
        self.send_iq_next = True    # For alternating polling
        self.movement_timer = None  # Timer used after UP/DOWN commands

        # --- CAN Commands (Combined) ---
        self.IQ_COMMAND = bytes([0xB4, 0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        self.GET_POSITION_COMMAND = bytes([0xB4, 0x13, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        self.STOP_COMMAND = bytes([0x92, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        self.START_COMMAND = bytes([0x91, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        self.UP_COMMAND = bytes([0x94, 0x00, 0x00, 0xA0, 0xC1, 0xD0, 0x07, 0x00])
        self.DOWN_COMMAND = bytes([0x94, 0x80, 0x00, 0xA0, 0x41, 0xD0, 0x07, 0x00])
        # SET_POSITION command (0x95) will be constructed dynamically

        # --- CAN Communication Setup ---
        self.can_message_queue = Queue()
        self._running = True
        self._receiver_thread = None
        self.bus = self.setup_can_bus() # Only one bus initialization

        if self.bus:
            self._receiver_thread = Thread(target=self._receive_can_messages, daemon=True)
            self._receiver_thread.start()
            self.debug_print("CAN receiver thread started", level=1)

            # Start the polling timer (from WaterNode)
            self.polling_timer = self.create_timer(
                1.0 / self.polling_rate, self.poll_motor_data
            )
            self.get_logger().info(f"Polling timer started ({self.polling_rate} Hz)")
        else:
            self.get_logger().error("CAN bus failed to initialize. Node functionality severely limited.")

        self.get_logger().info('Motor Control Node initialized')

    # --- Debugging and CAN Utilities (Mostly unchanged, use one copy) ---

    def debug_print(self, message, level=1):
        if self.debug_level >= level:
            self.get_logger().info(f"DEBUG[{level}]: {message}")

    def format_can_data(self, data):
        if not data: return "EMPTY_DATA"
        try:
            if isinstance(data, (bytes, bytearray, list)):
                return " ".join([f"{byte:02X}" for byte in data])
            else: return str(data)
        except Exception as e:
            self.get_logger().error(f"Error formatting CAN data: {e}")
            return "ERROR_FORMATTING_DATA"

    def setup_can_bus(self):
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
        """Single receiver thread for all incoming CAN messages."""
        self.debug_print("CAN receiver thread running", level=2)
        if not self.bus: return
        while self._running:
            try:
                msg = self.bus.recv(timeout=0.1)
                if msg and msg.data is not None:
                     self.can_message_queue.put(msg)
                     # Reduce verbosity of queue logging unless debugging deeply
                     if self.debug_level >= 3:
                         self.debug_print(f"Queued: ID={msg.arbitration_id}, data={self.format_can_data(msg.data)}", level=3)
            except can.CanError as e:
                self.get_logger().error(f"CAN receive error: {e}", throttle_duration_sec=5.0)
            except Exception as e:
                self.get_logger().error(f"Unexpected receiver error: {e}", throttle_duration_sec=5.0)
        self.debug_print("CAN receiver thread stopped", level=2)

    def send_message(self, data, arbitration_id=None):
        if not self.bus:
            self.get_logger().error("CAN bus not available. Cannot send.")
            return False
        if arbitration_id is None: arbitration_id = self.motor_id
        if not isinstance(data, bytes) or len(data) != 8:
            self.get_logger().error(f"Invalid CAN data format/length: {type(data)} len={len(data) if isinstance(data, (bytes, list)) else 'N/A'}")
            return False
        message = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)
        try:
            self.bus.send(message)
            self.debug_print(f"Sent: ID={arbitration_id}, data={self.format_can_data(data)}", level=1)
            return True
        except Exception as e:
            self.get_logger().error(f"Error sending CAN message: {e}")
            return False

    def get_response_from_queue(self, timeout=3.0, expected_arbitration_id=None, expected_data_prefix=None):
        """Gets a specific message from the queue (used mainly by init)."""
        self.debug_print(f"Waiting for queue: ID={expected_arbitration_id}, prefix={self.format_can_data(expected_data_prefix)} for {timeout}s", level=2)
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                msg = self.can_message_queue.get(block=False)
                if msg and hasattr(msg, 'arbitration_id') and hasattr(msg, 'data') and msg.data is not None:
                    match = True
                    if expected_arbitration_id is not None and msg.arbitration_id != expected_arbitration_id: match = False
                    if expected_data_prefix is not None and (len(msg.data) < len(expected_data_prefix) or not msg.data.startswith(expected_data_prefix)): match = False
                    if match:
                        self.debug_print(f"Found matching response in queue: ID={msg.arbitration_id}, data={self.format_can_data(msg.data)}", level=1)
                        return msg
                    else: # Message pulled but didn't match criteria, discard
                         if self.debug_level >= 3: self.debug_print(f"Discarded non-matching msg from queue: ID={msg.arbitration_id}", level=3)
            except Empty: time.sleep(0.01)
            except Exception as e:
                self.get_logger().error(f"Error getting from queue: {e}", throttle_duration_sec=1.0)
                time.sleep(0.01)
        self.debug_print("Timeout waiting for response in queue", level=1)
        return None

    def _clear_queue(self, clear_all=False):
        """Clears messages from the queue."""
        self.debug_print(f"Clearing CAN message queue {'(all)' if clear_all else '(stale)'}...", level=2)
        count = 0
        while True:
            try:
                # Non-blocking get
                msg = self.can_message_queue.get(block=False)
                count += 1
                # Optionally add logic here to only clear specific message types if not clear_all
            except Empty:
                break # Queue is empty
            except Exception as e:
                self.get_logger().error(f"Error clearing queue: {e}")
                break # Stop trying on error
        self.debug_print(f"Cleared {count} messages from queue.", level=2)

    def parse_float_from_response(self, data):
        """Parses little-endian float from bytes 4-7."""
        if len(data) < 8:
            self.get_logger().error(f"Parse float error: Data too short ({len(data)} bytes)")
            return None
        try:
            float_bytes = bytes(data[4:8])
            value = struct.unpack('<f', float_bytes)[0]
            self.debug_print(f"Parsed float: {value:.4f} from bytes {self.format_can_data(float_bytes)}", level=2)
            return value
        except struct.error as e:
            self.get_logger().error(f"Error unpacking float: {e}. Data: {self.format_can_data(data)}")
            return None
        except Exception as e:
            self.get_logger().error(f"Unexpected error parsing float: {e}")
            return None

    # --- Water Calculation Logic (From WaterNode) ---

    def apply_filter(self, new_value):
        """Applies moving average filter to torque."""
        self.torque_buffer.append(new_value)
        filtered_value = sum(self.torque_buffer) / len(self.torque_buffer)
        self.debug_print(f"Filter: in={new_value:.4f}, out={filtered_value:.4f}, N={len(self.torque_buffer)}", level=2)
        return filtered_value

    def calculate_water_volume(self, torque_val):
        """Calculates water volume from filtered torque."""
        force_n = abs(torque_val) * self.gear_ratio / self.drum_radius
        total_weight_g = (force_n / 9.81) * 1000
        water_weight_g = total_weight_g - (self.dead_weight * 1000)
        volume_ml = water_weight_g / self.water_density
        rounded_volume = round(volume_ml)
        result = max(0, rounded_volume) # Ensure non-negative
        self.debug_print(f"Water Calc: T={torque_val:.3f}Nm -> F={force_n:.2f}N -> W_tot={total_weight_g:.1f}g -> W_h2o={water_weight_g:.1f}g -> V={result}mL", level=1)
        return result

    # --- Polling Logic (From WaterNode, adapted) ---

    def poll_motor_data(self):
        """Periodically polls motor for Iq and Position."""
        # Avoid polling if a movement or init is actively in progress
        if self.current_operation is not None:
            self.debug_print(f"Polling skipped: Operation '{self.current_operation}' in progress.", level=2)
            return

        command_to_send = None
        expected_indicator = None

        if self.send_iq_next:
            command_to_send = self.IQ_COMMAND
            expected_indicator = 0x09
            self.debug_print("Polling for Iq (Current)", level=2)
        else:
            command_to_send = self.GET_POSITION_COMMAND
            expected_indicator = 0x13
            self.debug_print("Polling for Position", level=2)

        if not self.send_message(command_to_send):
            self.debug_print("Failed to send poll command.", level=1)
            # Flip flag anyway to try other command next time
            self.send_iq_next = not self.send_iq_next
            return

        # --- Process Responses (No blocking wait, check queue) ---
        # The receiver thread puts messages in the queue. We process them here
        # based on what we *expect* after sending the poll command.
        # This is less reliable than a blocking wait but avoids blocking the timer callback.
        # A better approach might be to process *all* messages from the queue here
        # regardless of the command just sent, and update state accordingly.

        # Let's try processing the queue directly in the polling loop for simplicity here:
        processed_response = False
        try:
            # Check queue briefly for expected response
            # Note: This is still racy. A message unrelated to the poll might be processed.
            # A more robust design would have the receiver thread parse known message types
            # and update state directly, or use a more sophisticated request/response matching.
            msg = self.can_message_queue.get(block=True, timeout=0.1) # Small block
            if msg and msg.data and msg.arbitration_id == self.motor_id and msg.data[0] == 0xB4:
                received_indicator = msg.data[1]
                value_raw = self.parse_float_from_response(msg.data)

                if value_raw is not None:
                    if received_indicator == 0x09: # Process Iq
                        self.current = value_raw
                        torque_raw = self.current * self.torque_constant
                        self.torque = self.apply_filter(torque_raw)
                        self.volume = self.calculate_water_volume(self.torque)
                        self.debug_print(f"Poll Update: I={self.current:.3f}A -> T={self.torque:.3f}Nm -> V={self.volume}mL", level=1)
                        self.publish_measurements() # Publish all results
                        processed_response = True
                    elif received_indicator == 0x13: # Process Position
                        self.position = value_raw
                        self.debug_print(f"Poll Update: Pos={self.position:.4f}", level=1)
                        self.publish_measurements() # Publish all results
                        processed_response = True
                    # else: ignore other indicators in this simple model

            # Put message back if it wasn't the one we were looking for (simplistic handling)
            if msg and not processed_response:
                 try: self.can_message_queue.put(msg, block=False)
                 except: pass # Ignore if queue is full

        except Empty:
            self.debug_print(f"No response in queue shortly after polling for {expected_indicator:02X}", level=2)
        except Exception as e:
            self.get_logger().error(f"Error processing queue in poll: {e}")

        # Flip flag for next poll cycle
        self.send_iq_next = not self.send_iq_next

    def publish_measurements(self):
        """Publishes the latest sensor readings."""
        # Torque
        torque_msg = Float32()
        torque_msg.data = self.torque
        self.torque_pub.publish(torque_msg)
        # Water Volume
        volume_msg = Int32()
        volume_msg.data = self.volume
        self.water_qty_pub.publish(volume_msg)
        # Position
        pos_msg = Float32()
        pos_msg.data = self.position
        self.position_pub.publish(pos_msg)
        self.debug_print(f"Published: T={self.torque:.3f}, V={self.volume}, P={self.position:.4f}", level=2)


    # --- Command Handling Logic (From WinchNode, adapted) ---

    def init_callback(self, msg):
        """Initialize motor using direct CAN sequence."""
        if msg.data == 'INIT':
            if self.current_operation:
                self.get_logger().warn(f"Ignoring INIT: Operation '{self.current_operation}' in progress.")
                return
            self.current_operation = 'INIT'
            self.get_logger().info("Motor Initialization Sequence Started")

            if not self.bus:
                self.get_logger().error("CAN bus not available for INIT.")
                self.current_operation = None
                return

            self._clear_queue(clear_all=True) # Clear queue before starting sequence

            # Step 1: Send Get Position
            if not self.send_message(self.GET_POSITION_COMMAND):
                self.get_logger().error("INIT Failed: Could not send GET_POSITION.")
                self.current_operation = None
                return
            self.debug_print("INIT: Sent GET_POSITION", level=1)

            # Step 2: Wait for response from queue
            response = self.get_response_from_queue(
                timeout=3.0,
                expected_arbitration_id=self.motor_id,
                expected_data_prefix=bytes([0xB4, 0x13])
            )

            if response and len(response.data) >= 8:
                response_bytes = response.data[4:8]
                self.debug_print(f"INIT: Received position bytes {self.format_can_data(response_bytes)}", level=1)

                # Step 3: Construct and Send Set Position
                set_pos_cmd = bytes([0x95]) + response_bytes + bytes([0x32, 0x14, 0x00])
                set_pos_cmd = (set_pos_cmd + b'\x00'*8)[:8] # Ensure 8 bytes

                if self.send_message(set_pos_cmd):
                    self.debug_print(f"INIT: Sent SET_POSITION {self.format_can_data(set_pos_cmd)}", level=1)

                    # Step 4: Send Start Command
                    if self.send_message(self.START_COMMAND):
                        self.debug_print("INIT: Sent START command.", level=1)
                        self.get_logger().info("Motor Initialization Sequence Completed")
                    else:
                        self.get_logger().error("INIT Failed: Could not send final START command.")
                else:
                    self.get_logger().error("INIT Failed: Could not send SET_POSITION command.")
            else:
                self.get_logger().error("INIT Failed: No valid response received for GET_POSITION.")
                # Attempt recovery
                self.send_message(self.START_COMMAND)

            self.current_operation = None # End of operation

    def stop_callback(self, msg):
        """Handle stop command."""
        if msg.data == 'CLOSE':
            self.get_logger().info("Motor Stop Command Received")
            if not self.bus:
                self.get_logger().error("CAN bus not available for STOP.")
                return

            # Cancel any pending movement timer
            if self.movement_timer:
                self.movement_timer.cancel()
                self.movement_timer = None
                self.debug_print("Cancelled movement timer on stop command", level=1)

            self._clear_queue() # Clear potentially stale messages

            # Send STOP command
            self.send_message(self.STOP_COMMAND)
            self.get_logger().info("Motor stop command sent")
            self.current_operation = None # Clear current operation

    def go_callback(self, msg):
        """Handle 'UP' or 'DOWN' commands."""
        self.get_logger().info(f"GO Command Received: {msg.data}")
        if not self.bus:
             self.get_logger().error("CAN bus not available for GO command.")
             return
        if self.current_operation is not None:
             self.get_logger().warn(f"Ignoring GO '{msg.data}': Operation '{self.current_operation}' in progress.")
             return

        command_to_send = None
        if msg.data == 'UP':
            self.current_operation = 'UP'
            command_to_send = self.UP_COMMAND
        elif msg.data == 'DOWN':
            self.current_operation = 'DOWN'
            command_to_send = self.DOWN_COMMAND
        else:
            self.get_logger().warn(f"Unknown GO command: '{msg.data}'. Expected 'UP' or 'DOWN'.")
            return

        self.get_logger().info(f"Starting {self.current_operation} movement sequence")
        self._clear_queue() # Clear queue before movement

        # Send UP/DOWN command
        if self.send_message(command_to_send):
            self.debug_print(f"Sent {self.current_operation} command", level=1)
            # Send START command immediately after
            if self.send_message(self.START_COMMAND):
                self.debug_print(f"Sent START command after {self.current_operation}", level=1)

                # Create a one-shot timer for 2 seconds to trigger position setting
                if self.movement_timer: self.movement_timer.cancel()
                self.movement_timer = self.create_timer(2.0, self.set_position_after_move)
                self.debug_print("Movement timer created (2.0s) for set_position_after_move", level=2)
            else:
                 self.get_logger().error(f"Failed to send START command after {self.current_operation}.")
                 self.current_operation = None # Reset state on failure
        else:
            self.get_logger().error(f"Failed to send {self.current_operation} command.")
            self.current_operation = None # Reset state on failure

    def set_position_after_move(self):
        """Callback for timer after UP/DOWN. Uses internally tracked position."""
        self.debug_print("set_position_after_move triggered by timer", level=1)

        # Cancel the timer that called this function
        if self.movement_timer:
            self.movement_timer.cancel()
            self.movement_timer = None

        if not self.bus:
            self.get_logger().error("CAN bus not available for set_position_after_move.")
            self.current_operation = None
            return

        # The polling loop should keep self.position updated.
        current_pos = self.position # Use the latest known position

        self.get_logger().info(f"Setting position after {self.current_operation} using internal value: {current_pos:.4f}")

        # --- Convert the float position to 4 bytes (little-endian) ---
        try:
            position_bytes = struct.pack('<f', current_pos)
            self.debug_print(f"Packed position {current_pos:.4f} to bytes: {self.format_can_data(position_bytes)}", level=2)
        except Exception as e:
            self.get_logger().error(f"Error packing position float {current_pos} to bytes: {e}")
            self.send_message(self.START_COMMAND) # Recovery attempt
            self.current_operation = None
            return

        # --- Construct and send the SET_POSITION command (0x95) ---
        set_pos_cmd = bytes([0x95]) + position_bytes + bytes([0x32, 0x14, 0x00])
        set_pos_cmd = (set_pos_cmd + b'\x00'*8)[:8] # Ensure 8 bytes

        if self.send_message(set_pos_cmd):
             self.debug_print(f"Sent SET_POSITION command: {self.format_can_data(set_pos_cmd)}", level=1)
             # --- Send the final START command ---
             if self.send_message(self.START_COMMAND):
                  self.debug_print("Sent final START command.", level=1)
                  self.get_logger().info(f"Completed {self.current_operation} movement sequence successfully.")
             else:
                  self.get_logger().error("Failed to send final START command.")
        else:
             self.get_logger().error("Failed to send SET_POSITION command.")
             self.send_message(self.START_COMMAND) # Recovery attempt

        # Operation finished
        self.current_operation = None

    # --- Node Shutdown ---
    def shutdown(self):
        """Clean shutdown procedures."""
        self.get_logger().info("Shutting down motor control node...")
        self._running = False # Signal threads to stop

        # Stop timers
        if hasattr(self, 'polling_timer') and self.polling_timer:
            self.polling_timer.cancel()
        if hasattr(self, 'movement_timer') and self.movement_timer:
            self.movement_timer.cancel()

        # Wait for receiver thread
        if self._receiver_thread and self._receiver_thread.is_alive():
             self.debug_print("Waiting for receiver thread...", level=2)
             self._receiver_thread.join(timeout=1.0)

        # Send stop command and shutdown CAN bus
        if hasattr(self, 'bus') and self.bus:
            self.get_logger().info("Sending final STOP command.")
            self.send_message(self.STOP_COMMAND)
            time.sleep(0.1) # Brief pause
            try:
                self.bus.shutdown()
                self.get_logger().info("CAN bus shut down.")
            except Exception as e:
                self.get_logger().error(f"Error shutting down CAN bus: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = WinchNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Keyboard interrupt received.")
    except Exception as e:
        node.get_logger().fatal(f"Unhandled exception during spin: {e}")
    finally:
        node.shutdown()
        if rclpy.ok(): # Check if context is still valid before destroying
             node.destroy_node()
        if rclpy.ok():
             rclpy.shutdown()

if __name__ == '__main__':
    main()
