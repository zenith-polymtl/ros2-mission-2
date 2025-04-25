import can
import time
import struct
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.qos import QoSProfile
from threading import Thread
from queue import Queue, Empty # Import Empty exception

class WinchNode(Node):
    def __init__(self):
        super().__init__('winch_node')

        # QoS profile for subscriptions
        qos_profile = QoSProfile(depth=10)

        # ROS2 subscribers
        self.subscriber_ = self.create_subscription(
            String, '/go_winch', self.go_callback, qos_profile)
        self.init_sub = self.create_subscription(
            String, '/init_motor', self.init_callback, 10)
        self.stop_sub = self.create_subscription(
            String, '/close_motor', self.stop_callback, 10)

        # Configuration parameters
        self.declare_parameter('device', '/dev/ttyUSB0')
        self.declare_parameter('can_speed', 500000)
        self.declare_parameter('baudrate', 2000000)
        self.declare_parameter('motor_id', 1)
        self.declare_parameter('debug_level', 1)  # 0=minimal, 1=normal, 2=verbose, 3=most verbose

        # Get parameters
        self.device = self.get_parameter('device').value
        self.can_speed = self.get_parameter('can_speed').value
        self.baudrate = self.get_parameter('baudrate').value
        self.motor_id = self.get_parameter('motor_id').value
        self.debug_level = self.get_parameter('debug_level').value

        # Commands (Corrected based on your updated list)
        self.STOP_COMMAND = bytes([0x92, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        self.START_COMMAND = bytes([0x91, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        # Note: Corrected DOWN_COMMAND based on typical byte representation.
        # Your original DOWN_COMMAND had 0xA0 41 D0 07 00 - A0 and 41 are bit flags.
        # Based on the UP command, 94 00 is likely 'Move Up' and 94 80 is 'Move Down'.
        # The remaining bytes seem to represent speed/parameters.
        # Let's assume the original sequence intended to use 94 80 for DOWN.
        # If the motor documentation provides the exact bytes, use those.
        # Assuming the 94 80 00 A0 41 D0 07 00 from your execute_command_sequence_down
        # is correct for your specific motor model:
        self.UP_COMMAND = bytes([0x94, 0x00, 0x00, 0xA0, 0xC1, 0xD0, 0x07, 0x00]) # Move Up
        self.DOWN_COMMAND = bytes([0x94, 0x80, 0x00, 0xA0, 0x41, 0xD0, 0x07, 0x00]) # Move Down
        
        self.GET_POSITION_COMMAND = bytes([0xB4, 0x13, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) # Get Position

        # State tracking
        self.current_operation = None  # Will be 'UP' or 'DOWN' during operations
        self.position_timer = None
        
        # Queue for incoming CAN messages and flag for receiver thread
        self.can_message_queue = Queue()
        self._running = True
        self._receiver_thread = None

        # Initialize CAN bus
        self.bus = self.setup_can_bus()

        # Start the continuous receiver thread only if the bus initialized successfully
        if self.bus:
            self._receiver_thread = Thread(target=self._receive_can_messages)
            self._receiver_thread.daemon = True  # Allow thread to exit when main program exits
            self._receiver_thread.start()
            self.debug_print("CAN receiver thread started", level=1)
        else:
            self.get_logger().error("CAN bus failed to initialize. Node functionality will be limited.")


        self.get_logger().info('Winch Node initialized')

    def debug_print(self, message, level=1):
        """Print debug message based on debug level"""
        if self.debug_level >= level:
            # Use get_logger().info for all ROS logging levels except for critical errors
            # This ensures the messages appear correctly in the ROS2 log system.
            self.get_logger().info(f"DEBUG[{level}]: {message}")


    def format_can_data(self, data):
        """Format CAN data as space-separated hex bytes, with safer handling of None or empty data"""
        if not data:
            return "EMPTY_DATA"
        
        try:
            if isinstance(data, bytes) or isinstance(data, bytearray):
                return " ".join([f"{byte:02X}" for byte in data])
            elif isinstance(data, list):
                return " ".join([f"{byte:02X}" for byte in data])
            else:
                # Attempt to represent other types gracefully
                return str(data)
        except Exception as e:
            self.get_logger().error(f"Error formatting CAN data: {e}")
            return "ERROR_FORMATTING_DATA"


    def setup_can_bus(self):
        """Initialize the CAN bus connection"""
        try:
            # Use a non-blocking approach for receiving in the dedicated thread
            # receive_own_messages=True is often useful for debugging to see messages you send
            bus = can.interface.Bus(
                interface='seeedstudio', # Ensure this matches your CAN adapter type
                channel=self.device,
                bitrate=self.can_speed,
                baudrate=self.baudrate,
                receive_own_messages=True 
            )
            self.get_logger().info(f"Connected to CAN bus on {self.device}")
            return bus
        except Exception as e:
            self.get_logger().error(f"Error setting up CAN bus on {self.device}: {e}")
            # Return None if setup fails
            return None

    def _receive_can_messages(self):
        """Continuous loop to receive CAN messages and put them in a queue"""
        self.debug_print("CAN receiver thread is running", level=2)
        if not self.bus:
             self.get_logger().error("Receiver thread cannot start, CAN bus not initialized.")
             self._running = False # Stop the thread if bus is not available
             return

        while self._running:
            try:
                # Use a small timeout to allow the thread to check the _running flag periodically
                # without blocking indefinitely if no messages are received.
                msg = self.bus.recv(timeout=0.1) 
                if msg: # can.Bus.recv returns None on timeout
                    if msg.data is not None: # Ensure message data is not None
                         # Put the received message into the queue
                         self.can_message_queue.put(msg)
                         self.debug_print(
                             f"Received and queued message: ID={msg.arbitration_id}, data={self.format_can_data(msg.data)}",
                             level=3 # Use a higher level for frequent messages
                         )
                    else:
                         self.debug_print(f"Received message with None data: ID={msg.arbitration_id}", level=3)
                         
            except can.CanError as e:
                # Log CAN errors, but don't necessarily stop the thread unless critical
                self.get_logger().error(f"CAN receive error in thread: {e}", throttle_duration_sec=1.0)
            except Exception as e:
                # Log unexpected errors and potentially break the loop if it's a critical failure
                self.get_logger().error(f"Unexpected error in CAN receiver thread: {e}", throttle_duration_sec=1.0)
                # Decide if this error should stop the thread. For now, we log and continue.
                # self._running = False # Uncomment to stop thread on any unexpected error

        self.debug_print("CAN receiver thread stopped", level=2)


    def send_message(self, data, arbitration_id=None):
        """Send a message with the specified data to the CAN bus"""
        if not self.bus:
            self.get_logger().error("CAN bus is not initialized. Cannot send message.")
            return False

        if arbitration_id is None:
            arbitration_id = self.motor_id

        if not isinstance(data, bytes) or len(data) != 8:
            self.get_logger().error(f"Error: Message data must be exactly 8 bytes (got {type(data)}, len={len(data) if isinstance(data, (bytes, list)) else 'N/A'})")
            return False

        message = can.Message(
            arbitration_id=arbitration_id, data=data, is_extended_id=False
        )

        try:
            self.bus.send(message)
            self.debug_print(
                f"Sent message: ID={arbitration_id}, data={self.format_can_data(data)}",
                level=1,
            )
            return True
        except Exception as e:
            self.get_logger().error(f"Error sending message: {e}")
            return False

    def get_response_from_queue(self, timeout=3.0, expected_arbitration_id=None, expected_data_prefix=None):
        """
        Gets a message from the queue that matches the criteria within a timeout.
        Reads from the queue populated by the _receiver_thread.
        
        Args:
            timeout (float): Maximum time to wait for a matching message.
            expected_arbitration_id (int, optional): Filter by arbitration ID.
            expected_data_prefix (bytes, optional): Filter by the start of the data payload.
            
        Returns:
            can.Message or None: The received matching message or None if timeout.
        """
        self.debug_print(
            f"Waiting for message in queue with ID={expected_arbitration_id}, prefix={self.format_can_data(expected_data_prefix) if expected_data_prefix else 'any'} for {timeout}s",
            level=1
        )
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Try to get a message from the queue immediately (non-blocking)
                # If queue is empty, it will raise Empty.
                msg = self.can_message_queue.get(block=False)
                
                # Safely process the received message
                if msg and hasattr(msg, 'arbitration_id') and hasattr(msg, 'data') and msg.data is not None:
                    
                    self.debug_print(
                        f"Pulled message from queue for check: ID={msg.arbitbation_id}, data={self.format_can_data(msg.data)}",
                        level=3
                    )
                    
                    # Check if message matches criteria
                    match = True
                    if expected_arbitration_id is not None and msg.arbitration_id != expected_arbitration_id:
                        match = False
                        self.debug_print(f"Queue message ID mismatch: expected {expected_arbitration_id}, got {msg.arbitration_id}", level=3)
                        
                    # Check prefix only if data exists and is long enough
                    if expected_data_prefix is not None and (not msg.data or len(msg.data) < len(expected_data_prefix) or not msg.data.startswith(expected_data_prefix)):
                        match = False
                        self.debug_print(
                            f"Queue message prefix mismatch: expected {self.format_can_data(expected_data_prefix)}, got {self.format_can_data(msg.data[:len(expected_data_prefix) if msg.data else b''])}",
                            level=3
                        )
                        
                    if match:
                        self.debug_print(
                            f"Found matching response from queue: ID={msg.arbitration_id}, data={self.format_can_data(msg.data)}",
                            level=1
                        )
                        # task_done() is used with JoinableQueue, but simple Queue is fine without it here.
                        return msg # Found the matching message!
                    else:
                        # If the message doesn't match, it's discarded from this check.
                        # The receiver thread keeps queueing all messages.
                        pass

                else:
                     self.debug_print(f"Pulled invalid or empty message from queue: {msg}", level=3)
                     # Discard invalid messages
                     pass
                     
            except Empty:
                # Queue is empty, wait a bit before checking again
                time.sleep(0.01) 
            except Exception as e:
                # Log errors getting from the queue
                self.get_logger().error(f"Error getting message from queue: {e}", throttle_duration_sec=1.0)
                time.sleep(0.01) # Avoid tight error loop

        self.debug_print("Timeout waiting for response in queue", level=1)
        return None # Timeout occurred, no matching message found

    def _clear_position_related_queue_messages(self):
        """Clears messages that might be position-related from the queue before a critical wait."""
        self.debug_print("Attempting to clear queue of potentially stale messages", level=2)
        count = 0
        while True:
            try:
                # Get messages with a very short timeout, non-blocking
                msg = self.can_message_queue.get(block=False)
                count += 1
                # Optional: Add logic here to check if the message data/ID matches
                # expected responses you want to clear (e.g., B4 13, 95).
                # For a simpler approach, just clear a few messages regardless of content.
                # If you are clearing *all* messages, be mindful of important messages
                # you might miss.
                self.debug_print(
                    f"Discarded message during clear: ID={msg.arbitration_id}, data={self.format_can_data(msg.data)}",
                    level=3 # Use a high level as this can be frequent
                )
            except Empty:
                # Queue is empty, we're done clearing
                self.debug_print(f"Queue clear attempt finished. Discarded {count} messages.", level=2)
                break
            except Exception as e:
                self.get_logger().error(f"Error clearing queue: {e}", throttle_duration_sec=1.0)
                break


    def init_callback(self, msg):
        """Initialize the motor with the required command sequence"""
        if msg.data == 'INIT':
            self.get_logger().info("Motor Initialization Command Received")
            
            if not self.bus:
                self.get_logger().error("CAN bus not initialized, cannot initialize motor.")
                return

            # Before sending the command and waiting for a response, clear the queue
            # to avoid processing stale messages that might match our expected response.
            self._clear_position_related_queue_messages()

            # Step 1: Send initialization command (Get Position)
            self.send_message(self.GET_POSITION_COMMAND)
            self.debug_print("Sent initialization command (Get Position): B4 13 00 00 00 00 00 00", level=1)
            
            # Step 2: Wait for response FROM THE QUEUE and extract 4 bytes
            # Increased timeout slightly for reliability
            response = self.get_response_from_queue(
                timeout=3.0, 
                expected_arbitration_id=self.motor_id,
                expected_data_prefix=bytes([0xB4, 0x13])
            )
            
            if response:
                self.debug_print(
                    f"Received response to Get Position from queue: {self.format_can_data(response.data)}", 
                    level=1
                )
                
                # Extract the 4 bytes from the response (bytes 4-7)
                if len(response.data) >= 8:
                    response_bytes = response.data[4:8]
                else:
                    self.get_logger().error(f"Initialization response from queue too short ({len(response.data)} bytes). Cannot extract position.")
                    return # Exit initialization
                
                # Step 3: Send second command (Set Position) with the extracted 4 bytes
                second_command = bytes([0x95]) + response_bytes + bytes([0x32, 0x14, 0x00])
                # Ensure it's exactly 8 bytes - though with 4 bytes + 3 bytes + 1 byte = 8 bytes,
                # this padding logic might not be strictly necessary if the lengths are fixed,
                # but it's good defensive programming.
                if len(second_command) != 8:
                    if len(second_command) > 8:
                        second_command = second_command[:8]
                        self.get_logger().warn("Truncated Set Position command to 8 bytes.")
                    else:
                        padding = bytes([0x00] * (8 - len(second_command)))
                        second_command = second_command + padding
                        self.get_logger().warn(f"Padded Set Position command with {len(padding)} bytes.")
                        
                self.send_message(second_command)
                self.debug_print(
                    f"Sent second command (Set Position): {self.format_can_data(second_command)}", 
                    level=1
                )

                # Step 4: Send idle command (Start) - This is crucial to leave the motor
                # in an operational state after initialization/setting position.
                self.send_message(self.START_COMMAND)
                self.debug_print(
                    "Sent idle command (Start): 91 00 00 00 00 00 00 00",
                    level=1
                )
                
                self.get_logger().info("Motor initialization sequence completed")
            else:
                self.get_logger().error("No response received for Get Position from queue during initialization within timeout.")
                # Consider sending the START command anyway as a recovery attempt
                self.send_message(self.START_COMMAND)
                self.debug_print("Sent START command as recovery after init response timeout.", level=1)

    
    def stop_callback(self, msg):
        """Stop the motor by sending the stop command"""
        if msg.data == 'CLOSE':
            self.get_logger().info("Motor Stop Command Received")
            
            if not self.bus:
                self.get_logger().error("CAN bus not initialized, cannot send stop command.")
                return

            # Cancel any ongoing position timer if a movement was in progress
            if self.position_timer:
                self.position_timer.cancel()
                self.position_timer = None
                self.debug_print("Cancelled position timer on stop command", level=1)
                
            # Clear any pending messages in the queue that might be responses
            # to a movement command or position query that was interrupted.
            self._clear_position_related_queue_messages()

            self.send_message(self.STOP_COMMAND)
            self.debug_print("Sent stop command: 92 00 00 00 00 00 00 00", level=1)
            self.get_logger().info("Motor stop command sent")
            self.current_operation = None # Reset operation state

    def go_callback(self, msg):
        """Handle go up/down commands"""
        self.get_logger().info(f"GO MESSAGE Received: {msg.data}")
        
        if not self.bus:
             self.get_logger().error("CAN bus not initialized, cannot perform GO movement.")
             return

        if self.current_operation is not None:
             self.get_logger().warn(f"Ignoring GO command '{msg.data}', motor is currently performing '{self.current_operation}'")
             return # Prevent overlapping movements

        if msg.data == 'UP':
            self.go_up()
        elif msg.data == 'DOWN':
            self.go_down()
        else:
            self.get_logger().warn(f"Received unknown GO command: '{msg.data}'. Expected 'UP' or 'DOWN'.")


    def go_up(self):
        """Command the winch to go up"""
        self.current_operation = 'UP'
        self.get_logger().info("Starting UP movement sequence")
        
        # Before sending the move command, clear the queue to prevent old messages
        # from interfering with the response we expect after the timer.
        self._clear_position_related_queue_messages()

        # Send the UP command
        # Note: The plain script sends the START command immediately after the move.
        # We'll follow that sequence.
        if self.send_message(self.UP_COMMAND):
            self.debug_print("Sent UP command: 94 00 00 A0 C1 D0 07 00", level=1)
            
            # Send the START command immediately after the move command.
            if self.send_message(self.START_COMMAND):
                self.debug_print("Sent START command after UP command.", level=1)
                
                # Create a one-shot timer for 2 seconds to trigger the position get/set
                # This timer acts as the delay between sending the move command
                # and then getting the resulting position.
                if self.position_timer:
                    self.position_timer.cancel() # Should not be active if current_operation is None, but safe check
                self.position_timer = self.create_timer(2.0, self.get_position_callback)
                self.debug_print("Position timer created for 2.0 seconds after UP command", level=2)
            else:
                 self.get_logger().error("Failed to send START command after UP.")
                 self.current_operation = None # Reset state on failure
        else:
            self.get_logger().error("Failed to send UP command.")
            self.current_operation = None # Reset state on failure


    def go_down(self):
        """Command the winch to go down"""
        self.current_operation = 'DOWN'
        self.get_logger().info("Starting DOWN movement sequence")

        # Before sending the move command, clear the queue.
        self._clear_position_related_queue_messages()

        # Send the DOWN command
        if self.send_message(self.DOWN_COMMAND):
            self.debug_print("Sent DOWN command: 94 80 00 A0 41 D0 07 00", level=1)
            
            # Send the START command immediately after the move command.
            if self.send_message(self.START_COMMAND):
                self.debug_print("Sent START command after DOWN command.", level=1)

                # Create a one-shot timer for 2 seconds to trigger the position get/set
                if self.position_timer:
                    self.position_timer.cancel()
                self.position_timer = self.create_timer(2.0, self.get_position_callback)
                self.debug_print("Position timer created for 2.0 seconds after DOWN command", level=2)
            else:
                 self.get_logger().error("Failed to send START command after DOWN.")
                 self.current_operation = None # Reset state on failure
        else:
            self.get_logger().error("Failed to send DOWN command.")
            self.current_operation = None # Reset state on failure


    def get_position_callback(self):
        """Callback for timer to get position and then set it."""
        self.debug_print("get_position_callback triggered by timer", level=1)

        # Cancel the timer since this is a one-shot operation initiated by the timer
        if self.position_timer:
            self.position_timer.cancel()
            self.position_timer = None
            self.debug_print("Position timer cancelled within get_position_callback", level=2)
        
        if not self.bus:
            self.get_logger().error("CAN bus not initialized, cannot get position in callback.")
            self.current_operation = None # Reset operation state
            return

        self.get_logger().info(f"Getting position after {self.current_operation if self.current_operation else 'timed'} movement phase")
        
        # Before sending the get position command, clear the queue.
        self._clear_position_related_queue_messages()

        # Send the get position command
        if not self.send_message(self.GET_POSITION_COMMAND):
            self.get_logger().error("Failed to send get position command in callback")
            self.current_operation = None # Reset operation state
            return
            
        self.debug_print("Sent get position command: B4 13 00 00 00 00 00 00", level=1)
        
        # Wait for response FROM THE QUEUE for the get position command
        response = self.get_response_from_queue(
            timeout=3.0,  # Increased timeout for reliability
            expected_arbitration_id=self.motor_id,
            expected_data_prefix=bytes([0xB4, 0x13])
        )

        if response:
            self.debug_print(
                f"Received position response from queue: {self.format_can_data(response.data)}",
                level=1
            )

            # Extract the 4 bytes from the response (bytes 4-7)
            if response.data and len(response.data) >= 8: # Check if data exists and is long enough
                response_bytes = response.data[4:8]
                self.debug_print(f"Extracted 4 position bytes: {self.format_can_data(response_bytes)}", level=2)
            else:
                self.get_logger().error(f"Position response from queue too short or data is None ({len(response.data) if response.data else 0} bytes). Cannot extract position.")
                self.current_operation = None # Reset operation state
                return # Exit callback

            # Send set position command with the extracted 4 bytes
            set_position_command_base = bytes([0x95]) + response_bytes + bytes([0x32, 0x14, 0x00])
            
            # Ensure it's exactly 8 bytes
            if len(set_position_command_base) != 8:
                if len(set_position_command_base) > 8:
                    set_position_command = set_position_command_base[:8]
                    self.get_logger().warn("Truncated Set Position command to 8 bytes.")
                else:
                    padding = bytes([0x00] * (8 - len(set_position_command_base)))
                    set_position_command = set_position_command_base + padding
                    self.get_logger().warn(f"Padded Set Position command with {len(padding)} bytes.")
            else:
                set_position_command = set_position_command_base

            if self.send_message(set_position_command):
                 self.debug_print(
                     f"Sent set position command: {self.format_can_data(set_position_command)}",
                     level=1
                 )

                 # Send the START command to complete the sequence and leave the motor
                 # in an operational idle state.
                 if self.send_message(self.START_COMMAND):
                      self.debug_print("Sent START command to complete movement sequence", level=1)
                      self.get_logger().info(f"Completed {self.current_operation if self.current_operation else 'timed'} movement sequence successfully")
                 else:
                      self.get_logger().error("Failed to send final START command.")
                      self.get_logger().warn(f"Completed {self.current_operation if self.current_operation else 'timed'} movement sequence with errors in final step.")
                 
            else:
                 self.get_logger().error("Failed to send set position command.")
                 self.get_logger().warn(f"Completed {self.current_operation if self.current_operation else 'timed'} movement sequence with errors in set position step.")

        else:
            self.get_logger().error("No position response received from queue within timeout in callback.")
            # Try to recover by sending a START command anyway
            self.send_message(self.START_COMMAND)
            self.debug_print("Sent START command as recovery action after position response timeout.", level=1)
            self.get_logger().warn(f"Completed {self.current_operation if self.current_operation else 'timed'} movement sequence with response timeout.")

        # Always reset operation state at the end of the sequence or on failure paths
        self.current_operation = None 


    def shutdown(self):
        """Clean shutdown procedures for the node."""
        self.get_logger().info("Shutting down winch node...")
        
        # Signal the receiver thread to stop and wait for it to finish
        self._running = False
        if self._receiver_thread and self._receiver_thread.is_alive():
             self.debug_print("Waiting for receiver thread to join...", level=2)
             self._receiver_thread.join(timeout=1.0) # Wait for the thread gracefully

        # Send stop command before shutting down the CAN bus
        if hasattr(self, 'bus') and self.bus:
            self.get_logger().info("Sending stop command before CAN bus shutdown.")
            self.send_message(self.STOP_COMMAND)
            self.debug_print("Sent stop command during shutdown", level=1)
            time.sleep(0.1) # Give the command a moment to send
            try:
                self.bus.shutdown()
                self.get_logger().info("CAN bus shut down successfully")
            except Exception as e:
                self.get_logger().error(f"Error during CAN bus shutdown: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = WinchNode()

    try:
        # Use spin() which will handle callbacks and timers
        rclpy.spin(node)
    except KeyboardInterrupt:
        # Handle Ctrl+C
        node.get_logger().info("Keyboard interrupt received. Shutting down.")
    except Exception as e:
        # Catch other exceptions during spin
        node.get_logger().fatal(f"Unhandled exception during spin: {e}")
    finally:
        # Ensure shutdown is called whether spinning finishes or an exception occurs
        node.shutdown()
        # rclpy.shutdown() is usually called after the node is destroyed.
        # If you destroy the node here, ensure shutdown is called first.
        # node.destroy_node() # Uncomment if you want to explicitly destroy the node
        rclpy.shutdown() # Clean up ROS2 resources

if __name__ == '__main__':
    main()
