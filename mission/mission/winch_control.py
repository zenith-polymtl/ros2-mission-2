import can
import time
import struct
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32  # Assuming you publish position as Int32

class WinchControlNode(Node):
    def __init__(self):
        super().__init__('winch_control_node')

        # ROS2 publisher (assuming you publish position)
        self.position_pub = self.create_publisher(Int32, '/winch_position', 10)

        # Configuration parameters
        self.declare_parameter('device', '/dev/ttyUSB0')
        self.declare_parameter('can_speed', 500000)
        self.declare_parameter('baudrate', 2000000)
        self.declare_parameter('motor_id', 1)
        self.declare_parameter('polling_rate', 5.0)  # Polling rate for position
        self.declare_parameter('debug_level', 1) # 0=minimal, 1=normal, 2=verbose

        # Get parameters
        self.device = self.get_parameter('device').value
        self.can_speed = self.get_parameter('can_speed').value
        self.baudrate = self.get_parameter('baudrate').value
        self.motor_id = self.get_parameter('motor_id').value
        self.polling_rate = self.get_parameter('polling_rate').value
        self.debug_level = self.get_parameter('debug_level').value

        # Initialize values
        self.current_position = 0

        # Commands
        # Assuming this is the command to get the motor's current position
        # **You'll need to replace this with the actual command for your motor**
        self.GET_POSITION_COMMAND = bytes([0xB4, 0x0C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) # Example command

        # Initialize CAN bus
        self.bus = self.setup_can_bus()

        # Create timer for polling position at specified rate
        self.timer = self.create_timer(1.0 / self.polling_rate, self.poll_motor_position)

        self.get_logger().info('Winch Control Node initialized')

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
            # It's generally better to let ROS 2's lifecycle management handle
            # shutdown, but for a simple script, this is acceptable.
            rclpy.shutdown()
            return None # Return None if bus setup fails

    def send_message(self, data, arbitration_id=None):
        """Send a message with the specified data to the CAN bus"""
        if self.bus is None:
            self.get_logger().error("CAN bus not initialized.")
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
                level=2,
            )
            return True
        except Exception as e:
            self.get_logger().error(f"Error sending message: {e}")
            return False

    def parse_position_from_response(self, data):
        """
        Parse position data from the CAN response.
        **You need to implement this based on your motor's response format.**
        This is a placeholder assuming position is a signed 32-bit integer
        starting from byte 4, little-endian.
        """
        try:
            # Example: Assuming position is a signed 32-bit integer (int32)
            # in little-endian format starting from byte 4.
            position_bytes = bytes(data[4:8])
            position = struct.unpack('<i', position_bytes)[0]
            self.debug_print(
                f"Parsed position: {position} from bytes {position_bytes.hex()}",
                level=2,
            )
            return position
        except Exception as e:
            self.get_logger().error(f"Error parsing position: {e}")
            return None

    def poll_motor_position(self):
        """Poll motor for position and publish it."""
        if self.bus is None:
            self.get_logger().error("CAN bus not initialized. Cannot poll.")
            return

        # Send request for position
        if not self.send_message(self.GET_POSITION_COMMAND):
            self.get_logger().warning("Failed to send GET_POSITION_COMMAND.")
            return

        # Wait for response with a timeout
        # Adjust the timeout (0.1 seconds here) based on your motor's response time
        message = self.bus.recv(0.1) # 100ms timeout

        if message:
            self.debug_print(
                f"Received message: ID={message.arbitration_id}, data={self.format_can_data(message.data)}",
                level=2,
            )

            # **Add checks here to confirm this is the expected position response**
            # You'll need to consult your motor's documentation for the specific
            # message ID and data format of the position response.
            # Example check (replace with your motor's specifics):
            # if message.arbitration_id == self.motor_id + 1 and message.data[0] == 0xC0:

            # Assuming the message is the position response, parse it
            position_raw = self.parse_position_from_response(message.data)

            if position_raw is not None:
                self.current_position = position_raw

                # Log and publish data
                self.debug_print(
                    f"Received Position: {self.current_position}",
                    level=0,
                )
                self.publish_position()

        else:
            self.debug_print("No position response received within timeout", level=1)

    def publish_position(self):
        """Publish motor position to the /winch_position topic"""
        msg = Int32()
        msg.data = self.current_position
        self.position_pub.publish(msg)
        self.debug_print(f"Published position: {msg.data}", level=2)


    def shutdown(self):
        """Clean shutdown"""
        self.get_logger().info("Shutting down winch control node...")
        if hasattr(self, 'bus') and self.bus is not None:
            self.bus.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = WinchControlNode()

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
