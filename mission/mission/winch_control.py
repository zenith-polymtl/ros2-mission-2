import can
import time
import struct
from collections import deque
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32, Float32
# Import QoS policies for finer control
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
# Import Thread for background tasks and Queue for message passing
from threading import Thread, Lock # Added Lock for potential future thread-safety needs
from queue import Queue, Empty

class MotorControlNode(Node):
    def __init__(self):
        super().__init__('motor_control_node') # Name of the ROS 2 node

        # --- QoS Profiles ---
        # QoS for command topics: Reliable delivery is usually desired.
        reliable_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST, # Keep only the last command
            depth=1,                         # Queue depth of 1
            reliability=ReliabilityPolicy.RELIABLE, # Try hard to deliver
            durability=DurabilityPolicy.VOLATILE # No need to persist commands for late joiners
        )
        # QoS for sensor data topics: Often best-effort is okay, but if subscribers
        # demand reliable, the publisher must provide it. Let's switch to RELIABLE.
        # Keep last 1 ensures subscribers joining late get the most recent value.
        sensor_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            # *** CHANGED TO RELIABLE to fix QoS warning ***
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE # Sensor data is usually transient
        )

        # --- Parameters (Combined from both nodes) ---
        # Declare parameters to allow configuration via launch files or command line
        self.declare_parameter('device', '/dev/ttyUSB0') # Serial port for CAN adapter
        self.declare_parameter('can_speed', 500000)     # CAN bus speed (bits per second)
        self.declare_parameter('baudrate', 2000000)    # Serial port speed for adapter
        self.declare_parameter('motor_id', 1)          # CAN ID of the target motor
        self.declare_parameter('polling_rate', 2.0)    # How often to request data (Hz)
        self.declare_parameter('filter_window', 11)    # Size of moving average filter
        self.declare_parameter('debug_level', 2)       # Verbosity: 0=min, 1=norm, 2=verb, 3=max
        # Physics Constants for water calculation
        self.declare_parameter('torque_constant', 0.065) # Motor torque constant (Nm/A)
        self.declare_parameter('drum_radius', 0.0235)    # Winch drum radius (meters)
        self.declare_parameter('gear_ratio', 10.0)       # Gearbox reduction ratio (e.g., 10:1)
        self.declare_parameter('dead_weight', 0.74)      # Weight of empty sampler (kg)
        self.declare_parameter('water_density', 1.0)     # Density of water (kg/L or g/mL)

        # --- Get Parameters ---
        # Retrieve the declared parameter values
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
        # Create publishers for the calculated/measured data
        self.water_qty_pub = self.create_publisher(Int32, '/water_qty', sensor_qos)
        self.torque_pub = self.create_publisher(Float32, '/torque', sensor_qos)
        self.position_pub = self.create_publisher(Float32, '/motor_position', sensor_qos)

        # --- Subscribers (From WinchNode) ---
        # Create subscribers for incoming commands
        self.go_sub = self.create_subscription(
            String, '/go_winch', self.go_callback, reliable_qos)
        self.init_sub = self.create_subscription(
            String, '/init_motor', self.init_callback, reliable_qos)
        self.stop_sub = self.create_subscription(
            String, '/close_motor', self.stop_callback, reliable_qos)

        # --- State Variables (Combined) ---
        # Variables to hold the current state of the system
        self.current = 0.0          # Last measured motor current (Amps)
        self.torque = 0.0           # Last calculated filtered torque (Nm)
        self.volume = 0             # Last calculated water volume (mL)
        self.position = 0.0         # Last measured position (float, from CAN response)
        # *** NEW: Store the raw bytes needed for the SET_POSITION command ***
        # These are bytes 4, 5, 6 from the 0xB4 0x13 response message
        self.last_position_raw_bytes = None # Initialize to None

        # Buffer for the moving average filter on torque
        self.torque_buffer = deque(maxlen=self.filter_window)
        # Track the current high-level operation (prevents command conflicts)
        self.current_operation = None # e.g., 'UP', 'DOWN', 'INIT', None
        # Flag to alternate polling between Iq and Position
        self.send_iq_next = True
        # Timer used for the delay after UP/DOWN before sending SET_POSITION
        self.movement_timer = None
        # Lock for potential thread-safe access to shared state (optional for now)
        self.state_lock = Lock()

        # --- CAN Commands (Combined) ---
        # Define the byte sequences for CAN commands
        self.IQ_COMMAND = bytes([0xB4, 0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) # Request Iq current
        self.GET_POSITION_COMMAND = bytes([0xB4, 0x13, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) # Request position
        self.STOP_COMMAND = bytes([0x92, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) # Stop motor immediately
        self.START_COMMAND = bytes([0x91, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) # Enable motor / idle state
        self.UP_COMMAND = bytes([0x94, 0x00, 0x00, 0xA0, 0xC1, 0xD0, 0x07, 0x00]) # Command motor UP
        self.DOWN_COMMAND = bytes([0x94, 0x80, 0x00, 0xA0, 0x41, 0xD0, 0x07, 0x00]) # Command motor DOWN
        # SET_POSITION command (0x95) is constructed dynamically using raw bytes

        # --- CAN Communication Setup ---
        # Queue for passing received CAN messages from the receiver thread to the main thread
        self.can_message_queue = Queue()
        # Flag to signal the receiver thread to stop
        self._running = True
        # Placeholder for the receiver thread object
        self._receiver_thread = None
        # Initialize the CAN bus interface (only one instance)
        self.bus = self.setup_can_bus()

        # Start background threads only if CAN bus initialized successfully
        if self.bus:
            # Create and start the thread that continuously listens for CAN messages
            self._receiver_thread = Thread(target=self._receive_can_messages, daemon=True)
            self._receiver_thread.start()
            self.debug_print("CAN receiver thread started", level=1)

            # Create and start the timer that periodically polls the motor state
            self.polling_timer = self.create_timer(
                1.0 / self.polling_rate, # Timer period based on polling rate
                self.poll_motor_data      # Function to call periodically
            )
            self.get_logger().info(f"Polling timer started ({self.polling_rate} Hz)")
        else:
            # Log a critical error if the CAN bus setup failed
            self.get_logger().error("CAN bus failed to initialize. Node functionality severely limited.")

        # Log that the node initialization is complete
        self.get_logger().info('Motor Control Node initialized')

    # --- Debugging and CAN Utilities ---

    def debug_print(self, message, level=1):
        """Prints a message if the node's debug level is high enough."""
        # Compare requested level with node's configured level
        if self.debug_level >= level:
            # Use the ROS 2 logger for consistent output
            self.get_logger().info(f"DEBUG[{level}]: {message}")

    def format_can_data(self, data):
        """Formats CAN message data bytes into a readable hex string."""
        # Handle cases where data might be None or empty
        if not data: return "EMPTY_DATA"
        try:
            # Check if data is a byte-like object or list
            if isinstance(data, (bytes, bytearray, list)):
                # Format each byte as a two-digit uppercase hex number
                return " ".join([f"{byte:02X}" for byte in data])
            else:
                # Attempt to convert other types to string
                return str(data)
        except Exception as e:
            # Log any errors during formatting
            self.get_logger().error(f"Error formatting CAN data: {e}")
            return "ERROR_FORMATTING_DATA"

    def setup_can_bus(self):
        """Initializes and returns the CAN bus interface object."""
        try:
            # Attempt to create a CAN bus instance using python-can
            bus = can.interface.Bus(
                interface='seeedstudio', # Specify the adapter type
                channel=self.device,     # Specify the serial port
                bitrate=self.can_speed,  # Specify the CAN bus speed
                baudrate=self.baudrate,  # Specify the adapter's serial speed
                receive_own_messages=True # Useful for debugging: see messages you send
            )
            # Log success
            self.get_logger().info(f"Successfully connected to CAN bus on {self.device}")
            return bus
        except Exception as e:
            # Log failure and return None
            self.get_logger().error(f"Fatal Error setting up CAN bus on {self.device}: {e}")
            return None

    def _receive_can_messages(self):
        """
        Background thread function. Continuously receives CAN messages
        and puts them into the shared queue.
        """
        self.debug_print("CAN receiver thread running", level=2)
        # Ensure the bus object exists
        if not self.bus:
            self.get_logger().error("Receiver thread cannot start, CAN bus not initialized.")
            return # Exit thread if bus is not available

        # Loop until the main node signals shutdown (_running = False)
        while self._running:
            try:
                # Wait for a message with a short timeout (0.1 seconds)
                # This allows the loop to check the _running flag periodically
                msg = self.bus.recv(timeout=0.1)
                # Check if a message was actually received (recv returns None on timeout)
                if msg:
                    # *** ADDED PRINT: Log every received message at high debug level ***
                    self.debug_print(f"Receiver Thread Raw Recv: ID={msg.arbitration_id}, Data={self.format_can_data(msg.data)}", level=3)
                    # Ensure message has data before queueing
                    if msg.data is not None:
                         # Put the valid message into the thread-safe queue
                         self.can_message_queue.put(msg)
                    else:
                         self.debug_print(f"Receiver Thread discarded message with None data: ID={msg.arbitration_id}", level=3)

            except can.CanError as e:
                # Log CAN-specific errors, potentially throttling if they occur frequently
                self.get_logger().error(f"CAN receive error in thread: {e}", throttle_duration_sec=5.0)
            except Exception as e:
                # Log any other unexpected errors in the receiver thread
                self.get_logger().error(f"Unexpected error in CAN receiver thread: {e}", throttle_duration_sec=5.0)

        # Log when the thread is exiting
        self.debug_print("CAN receiver thread stopped", level=2)

    def send_message(self, data, arbitration_id=None):
        """Constructs and sends a CAN message."""
        # Check if the CAN bus is available
        if not self.bus:
            self.get_logger().error("CAN bus not available. Cannot send message.")
            return False
        # Default to the configured motor ID if none is provided
        if arbitration_id is None: arbitration_id = self.motor_id
        # Validate data format (must be 8 bytes)
        if not isinstance(data, bytes) or len(data) != 8:
            self.get_logger().error(f"Invalid CAN data format/length: type={type(data)}, len={len(data) if isinstance(data, (bytes, list)) else 'N/A'}")
            return False
        # Create the CAN message object
        message = can.Message(
            arbitration_id=arbitration_id, # CAN ID
            data=data,                     # 8-byte payload
            is_extended_id=False           # Use standard 11-bit IDs
        )
        try:
            # Send the message via the CAN bus
            self.bus.send(message)
            # Log the sent message
            self.debug_print(f"Sent: ID={arbitration_id}, data={self.format_can_data(data)}", level=1)
            return True # Indicate success
        except Exception as e:
            # Log any errors during sending
            self.get_logger().error(f"Error sending CAN message: {e}")
            return False # Indicate failure

    def get_response_from_queue(self, timeout=3.0, expected_arbitration_id=None, expected_data_prefix=None):
        """
        Waits for and retrieves a specific message from the CAN message queue.
        Used primarily during the synchronous `init_callback`.
        """
        self.debug_print(f"Waiting for queue: ID={expected_arbitration_id}, prefix={self.format_can_data(expected_data_prefix)} for {timeout}s", level=2)
        start_time = time.time()
        # Loop until the timeout is reached
        while time.time() - start_time < timeout:
            try:
                # Try to get a message from the queue without blocking indefinitely
                msg = self.can_message_queue.get(block=True, timeout=0.05) # Short block

                # *** ADDED PRINT: Log message pulled from queue for checking ***
                self.debug_print(f"Queue Check: Pulled ID={msg.arbitration_id}, Data={self.format_can_data(msg.data)}", level=3)

                # Basic validation of the pulled message
                if msg and hasattr(msg, 'arbitration_id') and hasattr(msg, 'data') and msg.data is not None:
                    # Check if the message matches the specified criteria
                    match = True
                    # Check arbitration ID if specified
                    if expected_arbitration_id is not None and msg.arbitration_id != expected_arbitration_id:
                        match = False
                    # Check data prefix if specified (and data is long enough)
                    if expected_data_prefix is not None:
                        if len(msg.data) < len(expected_data_prefix) or not msg.data.startswith(expected_data_prefix):
                            match = False

                    # If all criteria match, return the message
                    if match:
                        self.debug_print(f"Found matching response in queue: ID={msg.arbitration_id}, data={self.format_can_data(msg.data)}", level=1)
                        return msg
                    else:
                        # Message pulled but didn't match, log if debugging deeply
                        if self.debug_level >= 3:
                            self.debug_print(f"Queue Check: Discarded non-matching msg ID={msg.arbitration_id}", level=3)
                        # Note: This message is now consumed from the queue. Consider if it should be put back.
                        # For init, we probably only care about the specific response.
                else:
                     # Log if an invalid/empty message was somehow pulled
                     self.debug_print(f"Queue Check: Pulled invalid message: {msg}", level=3)

            except Empty:
                # Queue was empty during the short block, loop again
                pass # Continue waiting until timeout
            except Exception as e:
                # Log errors encountered while getting from the queue
                self.get_logger().error(f"Error getting from queue: {e}", throttle_duration_sec=1.0)
                time.sleep(0.01) # Small delay to prevent spamming errors

        # If the loop finishes without returning, timeout occurred
        self.debug_print("Timeout waiting for response in queue", level=1)
        return None # Indicate timeout

    def _clear_queue(self, clear_all=False):
        """Clears messages from the input CAN message queue."""
        # Log the action
        self.debug_print(f"Clearing CAN message queue {'(all)' if clear_all else '(stale)'}...", level=2)
        count = 0
        # Loop until the queue is empty
        while True:
            try:
                # Get a message without blocking
                msg = self.can_message_queue.get(block=False)
                count += 1
                # Optional: Log discarded messages at high debug level
                if self.debug_level >= 3:
                    self.debug_print(f"Queue Clear: Discarded ID={msg.arbitration_id}", level=3)
            except Empty:
                # Queue is empty, stop clearing
                break
            except Exception as e:
                # Log errors during clearing
                self.get_logger().error(f"Error clearing queue: {e}")
                break # Stop trying on error
        # Log how many messages were cleared
        self.debug_print(f"Cleared {count} messages from queue.", level=2)

    def parse_float_from_response(self, data):
        """Parses a little-endian IEEE 754 float from bytes 4-7 of CAN data."""
        # Check if data is long enough (needs at least 8 bytes)
        if len(data) < 8:
            self.get_logger().error(f"Parse float error: Data too short ({len(data)} bytes)")
            return None
        try:
            # Extract bytes 4, 5, 6, 7 (0-indexed)
            float_bytes = bytes(data[4:8])
            # Unpack using struct, '<f' specifies little-endian float
            value = struct.unpack('<f', float_bytes)[0]
            # Log the parsed value
            self.debug_print(f"Parsed float: {value:.4f} from bytes {self.format_can_data(float_bytes)}", level=2)
            return value
        except struct.error as e:
            # Log errors during unpacking
            self.get_logger().error(f"Error unpacking float: {e}. Data: {self.format_can_data(data)}")
            return None
        except Exception as e:
            # Log any other unexpected errors
            self.get_logger().error(f"Unexpected error parsing float: {e}")
            return None

    # --- Water Calculation Logic ---

    def apply_filter(self, new_value):
        """Applies a simple moving average filter to the torque value."""
        # Add the new value to the right side of the deque
        self.torque_buffer.append(new_value)
        # Calculate the average of all values currently in the deque
        filtered_value = sum(self.torque_buffer) / len(self.torque_buffer)
        # Log the filter operation
        self.debug_print(f"Filter: in={new_value:.4f}, out={filtered_value:.4f}, N={len(self.torque_buffer)}", level=2)
        return filtered_value

    def calculate_water_volume(self, torque_val):
        """Calculates the estimated water volume based on filtered torque."""
        # Torque at drum = Motor Torque * Gear Ratio
        # Force = Torque at drum / Drum Radius
        force_n = abs(torque_val) * self.gear_ratio / self.drum_radius
        # Mass (kg) = Force (N) / gravity (m/s^2)
        # Weight (g) = Mass (kg) * 1000
        total_weight_g = (force_n / 9.81) * 1000
        # Subtract the weight of the empty sampler (converted to grams)
        water_weight_g = total_weight_g - (self.dead_weight * 1000)
        # Volume (mL) = Mass (g) / Density (g/mL)
        volume_ml = water_weight_g / self.water_density
        # Round to the nearest integer mL
        rounded_volume = round(volume_ml)
        # Ensure the result is not negative (can happen with noise or upward movement)
        result = max(0, rounded_volume)
        # Log the calculation steps
        self.debug_print(f"Water Calc: T={torque_val:.3f}Nm -> F={force_n:.2f}N -> W_tot={total_weight_g:.1f}g -> W_h2o={water_weight_g:.1f}g -> V={result}mL", level=1)
        return result

    # --- Polling Logic ---

    def poll_motor_data(self):
        """
        Periodically called by a timer. Sends requests for motor data (Iq/Position)
        and processes responses found in the queue.
        """
        # Check if a high-priority operation (like movement or init) is running
        if self.current_operation is not None:
            # Skip polling if motor is busy with a command sequence
            self.debug_print(f"Polling skipped: Operation '{self.current_operation}' in progress.", level=2)
            return

        # --- Determine Command for this Poll Cycle ---
        command_to_send = None
        expected_indicator = None # The expected second byte in the response (0x09 or 0x13)
        if self.send_iq_next:
            command_to_send = self.IQ_COMMAND
            expected_indicator = 0x09 # Expecting Iq response
            self.debug_print("Polling: Requesting Iq (Current)", level=2)
        else:
            command_to_send = self.GET_POSITION_COMMAND
            expected_indicator = 0x13 # Expecting Position response
            self.debug_print("Polling: Requesting Position", level=2)

        # --- Send the Command ---
        if not self.send_message(command_to_send):
            # Log failure to send poll command
            self.debug_print("Polling: Failed to send poll command.", level=1)
            # Flip the flag anyway to try the other command next time
            self.send_iq_next = not self.send_iq_next
            return # Exit this poll cycle

        # --- Process Responses from Queue ---
        # Instead of blocking/waiting, we process any relevant messages
        # that the receiver thread has placed in the queue since the last check.
        # This is asynchronous processing.
        processed_this_cycle = 0
        max_to_process = 5 # Limit processing to avoid blocking timer for too long
        while processed_this_cycle < max_to_process:
            try:
                # Get a message from the queue *without* blocking
                msg = self.can_message_queue.get(block=False)
                processed_this_cycle += 1

                # *** ADDED PRINT: Log every message processed from queue in poll ***
                self.debug_print(f"Poll Processing Queue Msg: ID={msg.arbitration_id}, Data={self.format_can_data(msg.data)}", level=3)

                # Check if it's a response from our motor (ID match and starts with 0xB4)
                if msg and msg.data and msg.arbitration_id == self.motor_id and msg.data[0] == 0xB4:
                    received_indicator = msg.data[1]
                    # Attempt to parse the float value (assuming format is consistent)
                    value_raw = self.parse_float_from_response(msg.data)

                    if value_raw is not None:
                        # Process based on the indicator byte
                        if received_indicator == 0x09: # Process Iq response
                            # Update current, calculate torque, filter, calculate volume
                            self.current = value_raw
                            torque_raw = self.current * self.torque_constant
                            # Use lock if state updates need to be atomic (optional here)
                            # with self.state_lock:
                            self.torque = self.apply_filter(torque_raw)
                            self.volume = self.calculate_water_volume(self.torque)
                            self.debug_print(f"Poll Update (Iq): I={self.current:.3f}A -> T={self.torque:.3f}Nm -> V={self.volume}mL", level=1)
                            # Publish updated measurements
                            self.publish_measurements()

                        elif received_indicator == 0x13: # Process Position response
                            # Update position float value
                            self.position = value_raw
                            # *** ADDED: Store raw bytes 4, 5, 6 for SET_POSITION command ***
                            if len(msg.data) >= 7: # Need bytes up to index 6
                                self.last_position_raw_bytes = msg.data[4:7] # Indices 4, 5, 6
                                self.debug_print(f"Poll Update (Pos): Pos={self.position:.4f}, RawBytes={self.format_can_data(self.last_position_raw_bytes)}", level=1)
                            else:
                                self.get_logger().warn("Position response too short to extract raw bytes.")
                                self.last_position_raw_bytes = None # Invalidate raw bytes
                            # Publish updated measurements
                            self.publish_measurements()
                        else:
                            # Log if an unknown indicator byte is received
                            self.debug_print(f"Poll: Received unknown indicator {received_indicator:02X}", level=2)
                    else:
                        # Log if float parsing failed for a received message
                         self.debug_print(f"Poll: Failed to parse float for indicator {received_indicator:02X}", level=1)
                # else: Message was not for us or not a B4 response, ignore it here.

            except Empty:
                # Queue is empty, stop processing for this cycle
                self.debug_print(f"Poll: Queue empty after processing {processed_this_cycle} messages.", level=3)
                break
            except Exception as e:
                # Log errors during queue processing
                self.get_logger().error(f"Error processing queue in poll: {e}")
                break # Stop processing on error

        # --- Flip Flag for Next Poll ---
        # Alternate between Iq and Position for the next polling cycle
        self.send_iq_next = not self.send_iq_next

    def publish_measurements(self):
        """Publishes the latest torque, volume, and position values."""
        # Create and publish Torque message
        torque_msg = Float32()
        torque_msg.data = self.torque
        self.torque_pub.publish(torque_msg)
        # Create and publish Water Volume message
        volume_msg = Int32()
        volume_msg.data = self.volume
        self.water_qty_pub.publish(volume_msg)
        # Create and publish Position message
        pos_msg = Float32()
        pos_msg.data = self.position
        self.position_pub.publish(pos_msg)
        # Log the published values
        self.debug_print(f"Published: T={self.torque:.3f}, V={self.volume}, P={self.position:.4f}", level=2)


    # --- Command Handling Logic ---

    def init_callback(self, msg):
        """Handles the 'INIT' command message."""
        # Check if the message data is 'INIT'
        if msg.data == 'INIT':
            # Prevent starting INIT if another operation is already running
            if self.current_operation:
                self.get_logger().warn(f"Ignoring INIT: Operation '{self.current_operation}' in progress.")
                return
            # Set current operation state
            self.current_operation = 'INIT'
            self.get_logger().info("Motor Initialization Sequence Started")

            # Check if CAN bus is available
            if not self.bus:
                self.get_logger().error("CAN bus not available for INIT.")
                self.current_operation = None # Reset state
                return

            # Clear the message queue to avoid processing old messages
            self._clear_queue(clear_all=True)

            # --- Step 1: Send Get Position Command ---
            if not self.send_message(self.GET_POSITION_COMMAND):
                self.get_logger().error("INIT Failed: Could not send GET_POSITION.")
                self.current_operation = None # Reset state
                return
            self.debug_print("INIT: Sent GET_POSITION (B4 13 ...)", level=1)

            # --- Step 2: Wait for the specific response from the queue ---
            response = self.get_response_from_queue(
                timeout=3.0, # Wait up to 3 seconds
                expected_arbitration_id=self.motor_id, # Match our motor's ID
                expected_data_prefix=bytes([0xB4, 0x13]) # Match the command response prefix
            )

            # --- Step 3: Process response and send Set Position ---
            # Check if a valid response was received
            if response and len(response.data) >= 7: # Need bytes up to index 6
                # *** MODIFIED: Extract bytes 4, 5, 6 (indices) ***
                position_bytes_to_set = response.data[4:7]
                self.debug_print(f"INIT: Received position bytes for SET: {self.format_can_data(position_bytes_to_set)}", level=1)

                # Construct the SET_POSITION command: 0x95 + 3 pos bytes + 0x32 + 0x14 + 0x00 + padding
                # Total length needs to be 8 bytes. 1 + 3 + 3 = 7 bytes so far. Need 1 padding byte.
                set_pos_cmd = bytes([0x95]) + position_bytes_to_set + bytes([0x32, 0x14, 0x00, 0x00]) # Added padding byte

                # Send the constructed command
                if self.send_message(set_pos_cmd):
                    self.debug_print(f"INIT: Sent SET_POSITION {self.format_can_data(set_pos_cmd)}", level=1)

                    # --- Step 4: Send Start Command to finish ---
                    if self.send_message(self.START_COMMAND):
                        self.debug_print("INIT: Sent final START command.", level=1)
                        self.get_logger().info("Motor Initialization Sequence Completed Successfully")
                    else:
                        # Log error if final START command fails
                        self.get_logger().error("INIT Failed: Could not send final START command.")
                else:
                    # Log error if SET_POSITION command fails
                    self.get_logger().error("INIT Failed: Could not send SET_POSITION command.")
            else:
                # Log error if no valid response was received for GET_POSITION
                self.get_logger().error("INIT Failed: No valid response received for GET_POSITION.")
                # Attempt recovery by sending START command
                self.send_message(self.START_COMMAND)
                self.debug_print("INIT: Sent START command as recovery attempt.", level=1)

            # Reset operation state regardless of success/failure
            self.current_operation = None

    def stop_callback(self, msg):
        """Handles the 'CLOSE' command message."""
        # Check if the message data is 'CLOSE'
        if msg.data == 'CLOSE':
            self.get_logger().info("Motor Stop Command Received")
            # Check if CAN bus is available
            if not self.bus:
                self.get_logger().error("CAN bus not available for STOP.")
                return

            # If a movement timer was running, cancel it
            if self.movement_timer:
                self.movement_timer.cancel()
                self.movement_timer = None
                self.debug_print("Cancelled movement timer on stop command", level=1)

            # Clear the queue of potentially stale messages
            self._clear_queue()

            # Send the STOP command
            self.send_message(self.STOP_COMMAND)
            self.get_logger().info("Motor stop command sent")
            # Reset the current operation state
            self.current_operation = None

    def go_callback(self, msg):
        """Handles 'UP' or 'DOWN' command messages."""
        self.get_logger().info(f"GO Command Received: {msg.data}")
        # Check if CAN bus is available
        if not self.bus:
             self.get_logger().error("CAN bus not available for GO command.")
             return
        # Prevent starting a new movement if one is already in progress
        if self.current_operation is not None:
             self.get_logger().warn(f"Ignoring GO '{msg.data}': Operation '{self.current_operation}' in progress.")
             return

        # Determine which command to send based on message data
        command_to_send = None
        operation_name = None
        if msg.data == 'UP':
            operation_name = 'UP'
            command_to_send = self.UP_COMMAND
        elif msg.data == 'DOWN':
            operation_name = 'DOWN'
            command_to_send = self.DOWN_COMMAND
        else:
            # Log if the command is unrecognized
            self.get_logger().warn(f"Unknown GO command: '{msg.data}'. Expected 'UP' or 'DOWN'.")
            return

        # Set the current operation state
        self.current_operation = operation_name
        self.get_logger().info(f"Starting {self.current_operation} movement sequence")
        # Clear the queue before starting the sequence
        self._clear_queue()

        # --- Send Movement Command (UP or DOWN) ---
        if self.send_message(command_to_send):
            self.debug_print(f"Sent {self.current_operation} command", level=1)
            # --- Send START Command Immediately After ---
            # This seems to be required by the motor protocol based on original scripts
            if self.send_message(self.START_COMMAND):
                self.debug_print(f"Sent START command after {self.current_operation}", level=1)

                # --- Start Timer for Post-Movement Action ---
                # Cancel any existing timer first
                if self.movement_timer: self.movement_timer.cancel()
                # Create a new one-shot timer that will call `set_position_after_move` after 2 seconds
                self.movement_timer = self.create_timer(2.0, self.set_position_after_move)
                self.debug_print("Movement timer created (2.0s) for set_position_after_move", level=2)
            else:
                 # Log error if START command fails
                 self.get_logger().error(f"Failed to send START command after {self.current_operation}.")
                 self.current_operation = None # Reset state on failure
        else:
            # Log error if movement command fails
            self.get_logger().error(f"Failed to send {self.current_operation} command.")
            self.current_operation = None # Reset state on failure

    def set_position_after_move(self):
        """
        Callback executed by timer 2 seconds after UP/DOWN command.
        Sends the SET_POSITION command using the last known raw position bytes.
        """
        self.debug_print("set_position_after_move triggered by timer", level=1)

        # Cancel the timer that called this function (it's one-shot)
        if self.movement_timer:
            self.movement_timer.cancel()
            self.movement_timer = None

        # Check CAN bus availability
        if not self.bus:
            self.get_logger().error("CAN bus not available for set_position_after_move.")
            self.current_operation = None # Reset state
            return

        # Retrieve the last known raw position bytes stored by the polling loop
        # Use lock if accessing shared state from multiple threads (optional here)
        # with self.state_lock:
        raw_bytes_to_set = self.last_position_raw_bytes

        # Check if we have valid raw bytes stored
        if raw_bytes_to_set is None or len(raw_bytes_to_set) != 3:
            self.get_logger().error(f"Cannot set position after {self.current_operation}: Invalid or missing raw position bytes ({raw_bytes_to_set}). Polling might not have updated yet.")
            # Attempt recovery by sending START
            self.send_message(self.START_COMMAND)
            self.current_operation = None # Reset state
            return

        self.get_logger().info(f"Setting position after {self.current_operation} using raw bytes: {self.format_can_data(raw_bytes_to_set)}")

        # --- Construct and send the SET_POSITION command (0x95) ---
        # Structure: 0x95 + 3 raw pos bytes + 0x32 + 0x14 + 0x00 + padding (1 byte)
        set_pos_cmd = bytes([0x95]) + raw_bytes_to_set + bytes([0x32, 0x14, 0x00, 0x00]) # Added padding

        # Send the command
        if self.send_message(set_pos_cmd):
             self.debug_print(f"Sent SET_POSITION command: {self.format_can_data(set_pos_cmd)}", level=1)
             # --- Send the final START command ---
             if self.send_message(self.START_COMMAND):
                  self.debug_print("Sent final START command.", level=1)
                  self.get_logger().info(f"Completed {self.current_operation} movement sequence successfully.")
             else:
                  # Log error if final START fails
                  self.get_logger().error("Failed to send final START command after SET_POSITION.")
        else:
             # Log error if SET_POSITION fails
             self.get_logger().error("Failed to send SET_POSITION command.")
             # Attempt recovery
             self.send_message(self.START_COMMAND)

        # Reset operation state, indicating the sequence is complete (or failed)
        self.current_operation = None

    # --- Node Shutdown ---
    def shutdown(self):
        """Performs cleanup actions when the node is shutting down."""
        self.get_logger().info("Shutting down motor control node...")
        # Signal the receiver thread to stop its loop
        self._running = False

        # Stop any active timers
        if hasattr(self, 'polling_timer') and self.polling_timer:
            self.polling_timer.cancel()
            self.debug_print("Polling timer cancelled.", level=2)
        if hasattr(self, 'movement_timer') and self.movement_timer:
            self.movement_timer.cancel()
            self.debug_print("Movement timer cancelled.", level=2)

        # Wait for the receiver thread to finish
        if self._receiver_thread and self._receiver_thread.is_alive():
             self.debug_print("Waiting for receiver thread to join...", level=2)
             self._receiver_thread.join(timeout=1.0) # Wait up to 1 second
             if self._receiver_thread.is_alive():
                 self.get_logger().warn("Receiver thread did not join cleanly.")

        # Send a final STOP command and shut down the CAN bus if it exists
        if hasattr(self, 'bus') and self.bus:
            self.get_logger().info("Sending final STOP command before CAN bus shutdown.")
            # Use a direct send attempt, ignoring potential errors during shutdown
            try:
                stop_msg = can.Message(arbitration_id=self.motor_id, data=self.STOP_COMMAND, is_extended_id=False)
                self.bus.send(stop_msg, timeout=0.1) # Short timeout send
                self.debug_print("Sent final STOP command during shutdown.", level=1)
                time.sleep(0.1) # Brief pause
            except Exception as e:
                 self.get_logger().warn(f"Ignoring error sending final STOP command: {e}")

            # Shutdown the CAN interface
            try:
                self.bus.shutdown()
                self.get_logger().info("CAN bus shut down successfully.")
            except Exception as e:
                self.get_logger().error(f"Error during CAN bus shutdown: {e}")


def main(args=None):
    # Initialize the ROS 2 Python client library
    rclpy.init(args=args)
    # Create an instance of the node
    node = MotorControlNode()
    try:
        # Keep the node running, processing callbacks (timers, subscriptions)
        rclpy.spin(node)
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        node.get_logger().info("Keyboard interrupt received. Initiating shutdown.")
    except Exception as e:
        # Log any other unexpected exceptions during runtime
        node.get_logger().fatal(f"Unhandled exception during spin: {e}")
    finally:
        # --- Cleanup ---
        # Call the node's custom shutdown method
        node.shutdown()
        # Destroy the node explicitly (optional but good practice)
        if rclpy.ok(): # Check if context is still valid
             node.destroy_node()
        # Shutdown the ROS 2 client library
        if rclpy.ok():
             rclpy.shutdown()

if __name__ == '__main__':
    # Entry point for the script
    main()
