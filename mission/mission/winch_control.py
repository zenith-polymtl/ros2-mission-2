import can
import time
import struct
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.qos import QoSProfile
from threading import Thread
from queue import Queue, Empty

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
        self.declare_parameter('debug_level', 1)  # 0=minimal, 1=normal, 2=verbose

        # Get parameters
        self.device = self.get_parameter('device').value
        self.can_speed = self.get_parameter('can_speed').value
        self.baudrate = self.get_parameter('baudrate').value
        self.motor_id = self.get_parameter('motor_id').value
        self.debug_level = self.get_parameter('debug_level').value

        # Commands (Corrected based on your updated list)
        self.STOP_COMMAND = bytes([0x92, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        self.START_COMMAND = bytes([0x91, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        self.UP_COMMAND = bytes([0x94, 0x00, 0x00, 0xA0, 0xC1, 0xD0, 0x07, 0x00])
        self.DOWN_COMMAND = bytes([0x94, 0x80, 0x00, 0xA0, 0x41, 0xD0, 0x07, 0x00])
        self.GET_POSITION_COMMAND = bytes([0xB4, 0x13, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

        # State tracking
        self.current_operation = None  # Will be 'UP' or 'DOWN' during operations
        self.position_timer = None
        
        # Initialize CAN bus
        self.bus = self.setup_can_bus()

        # Queue for incoming CAN messages and flag for receiver thread
        self.can_message_queue = Queue()
        self._running = True
        self._receiver_thread = None

        # Start the continuous receiver thread
        if self.bus:
            self._receiver_thread = Thread(target=self._receive_can_messages)
            self._receiver_thread.daemon = True  # Allow thread to exit when main program exits
            self._receiver_thread.start()
            self.debug_print("CAN receiver thread started", level=1)

        self.get_logger().info('Winch Node initialized')

    def debug_print(self, message, level=1):
        """Print debug message based on debug level"""
        if self.debug_level >= level:
            self.get_logger().info(f"DEBUG: {message}")

    def receive_direct(self, timeout=1.0):
        """
        Low-level direct reception from CAN bus with better error handling.
        
        Args:
            timeout (float): Maximum time to wait for a message
            
        Returns:
            can.Message or None: The received message or None if timeout/error
        """
        if not self.bus:
            self.get_logger().error("CAN bus not initialized. Cannot receive messages.")
            return None
        
        try:
            # Use direct bus.recv() with timeout
            return self.bus.recv(timeout)
        except can.CanError as e:
            self.get_logger().error(f"CAN direct receive error: {e}")
            return None
        except Exception as e:
            self.get_logger().error(f"Unexpected error in direct receive: {e}")
            return None


    def format_can_data(self, data):
        """Format CAN data as space-separated hex bytes"""
        if isinstance(data, bytes) or isinstance(data, list):
             return " ".join([f"{byte:02X}" for byte in data])
        return str(data)


    def setup_can_bus(self):
        """Initialize the CAN bus connection"""
        try:
            # Use a non-blocking approach for receiving
            bus = can.interface.Bus(
                interface='seeedstudio',
                channel=self.device,
                bitrate=self.can_speed,
                baudrate=self.baudrate,
                receive_own_messages=True
            )
            self.get_logger().info(f"Connected to CAN bus on {self.device}")
            return bus
        except Exception as e:
            self.get_logger().error(f"Error setting up CAN bus: {e}")
            # Consider whether to gracefully exit or attempt reconnect
            # For now, we'll log and the node might not function correctly
            return None

    def _receive_can_messages(self):
        """Continuous loop to receive CAN messages and put them in a queue"""
        self.debug_print("CAN receiver thread is running", level=2)
        while self._running and self.bus:
            try:
                # Use a small timeout to allow the thread to check the _running flag
                msg = self.bus.recv(timeout=0.1)
                if msg and msg.data:  # Make sure msg and msg.data are not empty
                    # Put the received message into the queue
                    self.can_message_queue.put(msg)
                    self.debug_print(
                        f"Received message in thread: ID={msg.arbitration_id}, data={self.format_can_data(msg.data)}",
                        level=2
                    )
            except can.CanError as e:
                self.get_logger().error(f"CAN receive error: {e}", throttle_duration_sec=1.0)
            except Exception as e:
                self.get_logger().error(f"Unexpected error in CAN receiver thread: {e}", throttle_duration_sec=1.0)
                # Sleep briefly to avoid tight error loop
                time.sleep(0.1)


    def send_message(self, data, arbitration_id=None):
        """Send a message with the specified data to the CAN bus"""
        if not self.bus:
            self.get_logger().error("CAN bus is not initialized. Cannot send message.")
            return False

        if arbitration_id is None:
            arbitration_id = self.motor_id

        if len(data) != 8:
            self.get_logger().error("Error: Message must be exactly 8 bytes")
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

    def get_response_direct(self, timeout=1.0, expected_arbitration_id=None, expected_data_prefix=None):
        """
        Directly receive a message from the CAN bus, bypassing the queue for critical operations.
        
        Args:
            timeout (float): How long to wait for a message.
            expected_arbitration_id (int, optional): Filter by arbitration ID.
            expected_data_prefix (bytes, optional): Filter by the start of the data payload.
            
        Returns:
            can.Message or None: The received message or None if timeout.
        """
        if not self.bus:
            self.get_logger().error("CAN bus not initialized. Cannot receive messages.")
            return None
            
        start_time = time.time()
        
        # Log that we're waiting for a message
        self.debug_print(
            f"Waiting directly for message with ID={expected_arbitration_id}, prefix={self.format_can_data(expected_data_prefix) if expected_data_prefix else 'any'}",
            level=1
        )
        
        while time.time() - start_time < timeout:
            try:
                msg = self.bus.recv(timeout=0.1)
                if not msg:
                    continue
                    
                # Log all received messages for debugging
                self.debug_print(
                    f"Received message: ID={msg.arbitration_id}, data={self.format_can_data(msg.data)}",
                    level=1
                )
                
                # Check if message matches criteria
                match = True
                if expected_arbitration_id is not None and msg.arbitration_id != expected_arbitration_id:
                    match = False
                if expected_data_prefix is not None and not msg.data.startswith(expected_data_prefix):
                    match = False
                    
                if match:
                    self.debug_print(
                        f"Found matching response: ID={msg.arbitration_id}, data={self.format_can_data(msg.data)}",
                        level=1
                    )
                    return msg
                    
            except can.CanError as e:
                self.get_logger().error(f"CAN receive error: {e}")
            except Exception as e:
                self.get_logger().error(f"Unexpected error receiving CAN message: {e}")
                
        self.debug_print("Timeout waiting for direct response", level=1)
        return None

    def get_response_direct(self, timeout=1.0, expected_arbitration_id=None, expected_data_prefix=None):
        """
        Directly receive a message from the CAN bus, with robust error handling.
        
        Args:
            timeout (float): How long to wait for a message.
            expected_arbitration_id (int, optional): Filter by arbitration ID.
            expected_data_prefix (bytes, optional): Filter by the start of the data payload.
            
        Returns:
            can.Message or None: The received message or None if timeout.
        """
        if not self.bus:
            self.get_logger().error("CAN bus not initialized. Cannot receive messages.")
            return None
            
        start_time = time.time()
        
        # Log that we're waiting for a message
        self.debug_print(
            f"Waiting directly for message with ID={expected_arbitration_id}, prefix={self.format_can_data(expected_data_prefix) if expected_data_prefix else 'any'}",
            level=1
        )
        
        # For the case where we expect a specific response, let's flush the existing queue
        # to avoid processing old messages
        try:
            while not self.can_message_queue.empty():
                self.can_message_queue.get_nowait()
                self.debug_print("Cleared a message from queue before direct receive", level=2)
        except Empty:
            pass
        
        while time.time() - start_time < timeout:
            # Use our safer receive function
            msg = self.receive_direct(timeout=0.1)
            
            if not msg:
                # No message received or error occurred
                continue
                
            # Safely extract data
            try:
                # Log all received messages for debugging
                self.debug_print(
                    f"Received direct message: ID={msg.arbitration_id}, data={self.format_can_data(msg.data)}",
                    level=1
                )
                
                # Check if message matches criteria
                match = True
                if expected_arbitration_id is not None and msg.arbitration_id != expected_arbitration_id:
                    match = False
                    self.debug_print(f"ID mismatch: expected {expected_arbitration_id}, got {msg.arbitration_id}", level=2)
                    
                if expected_data_prefix is not None and (not msg.data or not msg.data.startswith(expected_data_prefix)):
                    match = False
                    self.debug_print(
                        f"Prefix mismatch: expected {self.format_can_data(expected_data_prefix)}, got {self.format_can_data(msg.data[:len(expected_data_prefix) if msg.data else b''])}",
                        level=2
                    )
                    
                if match:
                    self.debug_print(
                        f"Found matching response: ID={msg.arbitration_id}, data={self.format_can_data(msg.data)}",
                        level=1
                    )
                    return msg
                    
            except Exception as e:
                self.get_logger().error(f"Error processing received message: {e}")
                
        self.debug_print("Timeout waiting for direct response", level=1)
        return None

    def format_can_data(self, data):
        """Format CAN data as space-separated hex bytes, with safer handling of None or empty data"""
        if not data:
            return "EMPTY"
        
        try:
            if isinstance(data, bytes) or isinstance(data, bytearray):
                return " ".join([f"{byte:02X}" for byte in data])
            elif isinstance(data, list):
                return " ".join([f"{byte:02X}" for byte in data])
            else:
                return str(data)
        except Exception as e:
            self.get_logger().error(f"Error formatting CAN data: {e}")
            return "ERROR_FORMATTING"


    def debug_print(self, message, level=1):
        """Print debug message based on debug level"""
        if self.debug_level >= level:
            self.get_logger().info(f"DEBUG: {message}")

    def init_callback(self, msg):
        """Initialize the motor with the required command sequence"""
        if msg.data == 'INIT':
            self.get_logger().info("Motor Initialization Command Received")
            
            if not self.bus:
                self.get_logger().error("CAN bus not initialized, cannot initialize motor.")
                return

            # Step 1: Send initialization command (Get Position)
            self.send_message(self.GET_POSITION_COMMAND)
            self.debug_print("Sent initialization command (Get Position): B4 13 00 00 00 00 00 00", level=1)
            
            # Step 2: Wait for response DIRECTLY and extract 4 bytes
            response = self.get_response_direct(
                timeout=2.0,  # Increased timeout for reliability
                expected_arbitration_id=self.motor_id,
                expected_data_prefix=bytes([0xB4, 0x13])
            )
            
            if response:
                self.debug_print(
                    f"Received response to Get Position: {self.format_can_data(response.data)}", 
                    level=1
                )
                
                # Extract the 4 bytes from the response (bytes 4-7)
                if len(response.data) >= 8:
                    response_bytes = response.data[4:8]
                else:
                    self.get_logger().error(f"Initialization response too short ({len(response.data)} bytes). Cannot extract position.")
                    return # Exit initialization
                
                # Step 3: Send second command (Set Position) with the extracted 4 bytes
                second_command = bytes([0x95]) + response_bytes + bytes([0x32, 0x14, 0x00])
                if len(second_command) != 8:
                    # Ensure it's exactly 8 bytes
                    if len(second_command) > 8:
                        second_command = second_command[:8]
                    else:
                        second_command = second_command + bytes([0x00] * (8 - len(second_command)))
                        
                self.send_message(second_command)
                self.debug_print(
                    f"Sent second command (Set Position): {self.format_can_data(second_command)}", 
                    level=1
                )

                # Step 4: Send idle command (Start)
                self.send_message(self.START_COMMAND)
                self.debug_print(
                    "Sent idle command (Start): 91 00 00 00 00 00 00 00",
                    level=1
                )
                
                self.get_logger().info("Motor initialization sequence completed")
            else:
                self.get_logger().error("No response received for Get Position during initialization")

    
    def stop_callback(self, msg):
        """Stop the motor by sending the stop command"""
        self.get_logger().info("Motor Stop Command Received")
        if msg.data == 'CLOSE':
            # Cancel any ongoing position timer
            if self.position_timer:
                self.position_timer.cancel()
                self.position_timer = None
                self.debug_print("Cancelled position timer", level=1)
                
            # Clear any pending messages related to the last movement from the queue
            self._clear_position_related_queue_messages()

            self.send_message(self.STOP_COMMAND)
            self.debug_print("Sent stop command: 92 00 00 00 00 00 00 00", level=1)
            self.get_logger().info("Motor stop command sent")
            self.current_operation = None

    def _clear_position_related_queue_messages(self):
        """Clears messages likely related to the position get/set from the queue"""
        self.debug_print("Attempting to clear position-related messages from queue", level=2)
        while True:
            try:
                # Get messages with a very short timeout, non-blocking
                msg = self.can_message_queue.get(block=False)
                # You might add logic here to check if the message is related to
                # the position query (e.g., starts with B4 13 or 95).
                # For now, we'll just discard all messages to be safe.
                self.debug_print(
                    f"Discarded message during stop: ID={msg.arbitration_id}, data={self.format_can_data(msg.data)}",
                    level=3
                )
            except Empty:
                # Queue is empty, we're done
                self.debug_print("Queue is clear of position-related messages", level=2)
                break
            except Exception as e:
                self.get_logger().error(f"Error clearing queue: {e}", throttle_duration_sec=1.0)
                break


    def go_callback(self, msg):
        """Handle go up/down commands"""
        self.get_logger().info(f"GO MESSAGE : {msg.data}")
        if msg.data == 'UP':
            self.go_up()
        elif msg.data == 'DOWN': # Use elif to avoid potential issues if message is neither
            self.go_down()
        else:
            self.get_logger().warn(f"Received unknown GO command: {msg.data}")


    def go_up(self):
        """Command the winch to go up"""
        if self.current_operation is not None:
             self.get_logger().warn(f"Ignoring UP command, motor is currently {self.current_operation}")
             return

        self.current_operation = 'UP'
        self.get_logger().info("Starting UP movement")
        
        if not self.bus:
             self.get_logger().error("CAN bus not initialized, cannot start UP movement.")
             self.current_operation = None
             return

        # Send the UP command
        self.send_message(self.UP_COMMAND)
        self.debug_print("Sent UP command: 94 00 00 A0 C1 D0 07 00", level=1)
        
        # The standard script sends the idle command immediately after the move command.
        # Let's replicate that behavior here before the timer starts.
        self.send_message(self.START_COMMAND)
        self.debug_print("Sent START command after UP", level=1)

        # Create a one-shot timer for 2 seconds to trigger the position get/set
        # Cancel any existing timer first (though go_callback should prevent overlap)
        if self.position_timer:
            self.position_timer.cancel()
        self.position_timer = self.create_timer(2.0, self.get_position_callback)
        self.debug_print("Position timer created for 2.0 seconds", level=2)


    def go_down(self):
        """Command the winch to go down"""
        if self.current_operation is not None:
             self.get_logger().warn(f"Ignoring DOWN command, motor is currently {self.current_operation}")
             return

        self.current_operation = 'DOWN'
        self.get_logger().info("Starting DOWN movement")

        if not self.bus:
             self.get_logger().error("CAN bus not initialized, cannot start DOWN movement.")
             self.current_operation = None
             return

        # Send the DOWN command
        self.send_message(self.DOWN_COMMAND)
        self.debug_print("Sent DOWN command: 94 80 00 A0 41 D0 07 00", level=1)
        
        # Replicate standard script behavior: Send idle command after move command
        self.send_message(self.START_COMMAND)
        self.debug_print("Sent START command after DOWN", level=1)

        # Create a one-shot timer for 2 seconds to trigger the position get/set
        # Cancel any existing timer first
        if self.position_timer:
            self.position_timer.cancel()
        self.position_timer = self.create_timer(2.0, self.get_position_callback)
        self.debug_print("Position timer created for 2.0 seconds", level=2)


    def get_position_callback(self):
        """Callback for timer to get position and set it"""
        self.debug_print("get_position_callback triggered", level=1)

        # Cancel the timer since this is a one-shot operation
        if self.position_timer:
            self.position_timer.cancel()
            self.position_timer = None
            self.debug_print("Position timer cancelled within callback", level=2)
        
        if not self.bus:
            self.get_logger().error("CAN bus not initialized, cannot get position.")
            self.current_operation = None
            return

        self.get_logger().info(f"Getting position after {self.current_operation} movement")
        
        # Send the get position command
        success = self.send_message(self.GET_POSITION_COMMAND)
        if not success:
            self.get_logger().error("Failed to send get position command")
            self.current_operation = None
            return
            
        self.debug_print("Sent get position command: B4 13 00 00 00 00 00 00", level=1)
        
        # Wait for response DIRECTLY from the CAN bus (not using the queue)
        # This is more reliable for critical operations
        response = self.get_response_direct(
            timeout=2.0,  # Increased timeout for reliability
            expected_arbitration_id=self.motor_id,
            expected_data_prefix=bytes([0xB4, 0x13])
        )

        if response:
            self.debug_print(
                f"Received position response: {self.format_can_data(response.data)}",
                level=1
            )

            # Extract the 4 bytes from the response (bytes 4-7)
            if len(response.data) >= 8:
                response_bytes = response.data[4:8]
            else:
                self.get_logger().error(f"Position response too short ({len(response.data)} bytes). Cannot extract position.")
                self.current_operation = None
                return # Exit callback

            # Send set position command with the extracted 4 bytes
            set_position_command = bytes([0x95]) + response_bytes + bytes([0x32, 0x14, 0x00])
            if len(set_position_command) != 8:
                # Ensure it's exactly 8 bytes
                if len(set_position_command) > 8:
                    set_position_command = set_position_command[:8]
                else:
                    set_position_command = set_position_command + bytes([0x00] * (8 - len(set_position_command)))

            self.send_message(set_position_command)
            self.debug_print(
                f"Sent set position command: {self.format_can_data(set_position_command)}",
                level=1
            )

            # Send the START command to complete the sequence
            self.send_message(self.START_COMMAND)
            self.debug_print("Sent START command to complete movement", level=1)

            self.get_logger().info(f"Completed {self.current_operation} movement sequence")
            self.current_operation = None
        else:
            self.get_logger().error("No position response received within timeout")
            # Try to recover by sending a START command anyway
            self.send_message(self.START_COMMAND)
            self.debug_print("Sent START command as recovery action", level=1)
            self.current_operation = None



    def shutdown(self):
        """Clean shutdown"""
        self.get_logger().info("Shutting down winch node...")
        
        # Signal the receiver thread to stop
        self._running = False
        if self._receiver_thread and self._receiver_thread.is_alive():
             self._receiver_thread.join(timeout=1.0) # Wait for thread to finish

        if hasattr(self, 'bus') and self.bus:
            # Send stop command before shutting down
            self.send_message(self.STOP_COMMAND)
            self.debug_print("Sent stop command during shutdown", level=1)
            self.bus.shutdown()
            self.get_logger().info("CAN bus shut down")


def main(args=None):
    rclpy.init(args=args)
    node = WinchNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        # node.destroy_node() # shutdown() handles resource cleanup, avoid double-free
        rclpy.shutdown()


if __name__ == '__main__':
    main()
