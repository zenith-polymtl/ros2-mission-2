import can
import time
import struct
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.qos import QoSProfile


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

        # Commands
        self.INIT_COMMAND = bytes([0xB4, 0x13, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        self.STOP_COMMAND = bytes([0x92, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        self.IDLE_COMMAND = bytes([0x91, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        self.UP_COMMAND = bytes([0x94, 0x00, 0x00, 0xA0, 0xC1, 0xD0, 0x07, 0x00])
        self.DOWN_COMMAND = bytes([0x94, 0x80, 0x00, 0xA0, 0xC1, 0xD0, 0x07, 0x00])
        self.GET_POSITION_COMMAND = bytes([0xB4, 0x13, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

        # State tracking
        self.current_operation = None  # Will be 'UP' or 'DOWN' during operations
        self.position_timer = None
        
        # Initialize CAN bus
        self.bus = self.setup_can_bus()

        self.get_logger().info('Winch Node initialized')

    def debug_print(self, message, level=1):
        """Print debug message based on debug level"""
        if self.debug_level >= level:
            self.get_logger().info(f"DEBUG: {message}")

    def format_can_data(self, data):
        """Format CAN data as space-separated hex bytes"""
        return " ".join([f"{byte:02X}" for byte in data])

    def setup_can_bus(self):
        """Initialize the CAN bus connection"""
        try:
            bus = can.interface.Bus(
                interface='seeedstudio',
                channel=self.device,
                bitrate=self.can_speed,
                baudrate=self.baudrate,
            )
            self.get_logger().info(f"Connected to CAN bus on {self.device}")
            return bus
        except Exception as e:
            self.get_logger().error(f"Error setting up CAN bus: {e}")
            rclpy.shutdown()

    def send_message(self, data, arbitration_id=None):
        """Send a message with the specified data to the CAN bus"""
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

    def init_callback(self, msg):
        """Initialize the motor with the required command sequence"""
        if msg.data == 'INIT':
            self.get_logger().info("Motor Initialization Command Received")
            
            # Step 1: Send initialization command
            self.send_message(self.INIT_COMMAND)
            self.debug_print("Sent initialization command: B4 13 00 00 00 00 00 00", level=1)
            
            # Step 2: Wait for response and extract 4 bytes
            try:
                response = self.bus.recv(1.0)  # 1 second timeout
                if response:
                    self.debug_print(
                        f"Received response: {self.format_can_data(response.data)}", 
                        level=1
                    )
                    
                    # Extract the 4 bytes from the response (bytes 4-7)
                    response_bytes = response.data[4:8]
                    
                    # Step 3: Send second command with the extracted 4 bytes
                    second_command = bytes([0x95]) + response_bytes + bytes([0x32, 0x14, 0x00])
                    self.send_message(second_command)
                    self.debug_print(
                        f"Sent second command: {self.format_can_data(second_command)}", 
                        level=1
                    )
                    
                    # Step 4: Send idle command
                    self.send_message(self.IDLE_COMMAND)
                    self.debug_print(
                        "Sent idle command: 91 00 00 00 00 00 00 00", 
                        level=1
                    )
                    
                    self.get_logger().info("Motor initialization sequence completed")
                else:
                    self.get_logger().error("No response received during initialization")
            except Exception as e:
                self.get_logger().error(f"Error during motor initialization: {e}")

    def stop_callback(self, msg):
        """Stop the motor by sending the stop command"""
        self.get_logger().info("Motor Stop Command Received")
        if msg.data == 'STOP':
            # Cancel any ongoing position timer
            if self.position_timer:
                self.position_timer.cancel()
                self.position_timer = None
                
            self.send_message(self.STOP_COMMAND)
            self.debug_print("Sent stop command: 92 00 00 00 00 00 00 00", level=1)
            self.get_logger().info("Motor stop command sent")
            self.current_operation = None

    def go_callback(self, msg):
        """Handle go up/down commands"""
        self.get_logger().info(f"GO MESSAGE : {msg.data}")
        if msg.data == 'UP':
            self.go_up()
        if msg.data == 'DOWN':
            self.go_down()

    def go_up(self):
        """Command the winch to go up"""
        self.current_operation = 'UP'
        self.get_logger().info("Starting UP movement")
        
        # Send the UP command
        self.send_message(self.UP_COMMAND)
        self.debug_print("Sent UP command: 94 00 00 A0 C1 D0 07 00", level=1)
        
        # Create a one-shot timer for 2 seconds
        if self.position_timer:
            self.position_timer.cancel()
        self.position_timer = self.create_timer(2.0, self.get_position_callback)

    def go_down(self):
        """Command the winch to go down"""
        self.current_operation = 'DOWN'
        self.get_logger().info("Starting DOWN movement")
        
        # Send the DOWN command
        self.send_message(self.DOWN_COMMAND)
        self.debug_print("Sent DOWN command: 94 80 00 A0 C1 D0 07 00", level=1)
        
        # Create a one-shot timer for 2 seconds
        if self.position_timer:
            self.position_timer.cancel()
        self.position_timer = self.create_timer(2.0, self.get_position_callback)

    def get_position_callback(self):
        """Callback for timer to get position and set it"""
        # Cancel the timer since this is a one-shot operation
        self.position_timer.cancel()
        self.position_timer = None
        
        self.get_logger().info(f"Getting position after {self.current_operation} movement")
        
        # Send the get position command
        self.send_message(self.GET_POSITION_COMMAND)
        self.debug_print("Sent get position command: B4 13 00 00 00 00 00 00", level=1)
        
        # Wait for response and process it
        try:
            response = self.bus.recv(1.0)  # 1 second timeout
            if response:
                self.debug_print(
                    f"Received position response: {self.format_can_data(response.data)}", 
                    level=1
                )
                
                # Extract the 4 bytes from the response (bytes 4-7)
                response_bytes = response.data[4:8]
                
                # Send set position command with the extracted 4 bytes
                set_position_command = bytes([0x95]) + response_bytes + bytes([0x32, 0x14, 0x00])
                self.send_message(set_position_command)
                self.debug_print(
                    f"Sent set position command: {self.format_can_data(set_position_command)}", 
                    level=1
                )
                
                self.get_logger().info(f"Completed {self.current_operation} movement")
                self.current_operation = None
            else:
                self.get_logger().error("No response received for position query")
        except Exception as e:
            self.get_logger().error(f"Error during position setting: {e}")
            self.current_operation = None

    def shutdown(self):
        """Clean shutdown"""
        self.get_logger().info("Shutting down winch node...")
        if hasattr(self, 'bus'):
            # Send stop command before shutting down
            self.send_message(self.STOP_COMMAND)
            self.debug_print("Sent stop command during shutdown", level=1)
            self.bus.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = WinchNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
