import can
import time
import struct
from collections import deque
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32


class WaterNode(Node):
    def __init__(self):
        super().__init__('water_node')

        # ROS2 publisher
        self.water_qty_pub = self.create_publisher(Int32, '/water_qty', 2)
        self.torque_pub = self.create_publisher(Int32, '/torque', 2)
        # Configuration parameters
        self.declare_parameter('device', '/dev/ttyUSB0')
        self.declare_parameter('can_speed', 500000)
        self.declare_parameter('baudrate', 2000000)
        self.declare_parameter('motor_id', 1)
        self.declare_parameter('polling_rate', 5.0)  # Hz
        self.declare_parameter('filter_window', 11)
        self.declare_parameter('debug_level', 1)  # 0=minimal, 1=normal, 2=verbose

        # Physics constants
        self.declare_parameter('torque_constant', 0.065)  # Nm/A
        self.declare_parameter('drum_radius', 0.0235)  # m
        self.declare_parameter('gear_ratio', 10.0)  # 10:1 reduction
        self.declare_parameter('dead_weight', 0.74)  # kg
        self.declare_parameter('water_density', 1.0)  # kg/mL

        # Get parameters
        self.device = self.get_parameter('device').value
        self.can_speed = self.get_parameter('can_speed').value
        self.baudrate = self.get_parameter('baudrate').value
        self.motor_id = self.get_parameter('motor_id').value
        self.polling_rate = self.get_parameter('polling_rate').value
        self.filter_window = self.get_parameter('filter_window').value
        self.debug_level = self.get_parameter('debug_level').value

        # Physics constants
        self.torque_constant = self.get_parameter('torque_constant').value
        self.drum_radius = self.get_parameter('drum_radius').value
        self.gear_ratio = self.get_parameter('gear_ratio').value
        self.dead_weight = self.get_parameter('dead_weight').value
        self.water_density = self.get_parameter('water_density').value

        # Initialize values
        self.current = 0.0
        self.torque = 0.0
        self.volume = 0

        # Initialize the filter buffer
        self.torque_buffer = deque(maxlen=self.filter_window)

        # Commands
        self.IQ_COMMAND = bytes(
            [0xB4, 0x0B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        )

        # Print configuration
        self.debug_print(
            f"Configuration: torque_constant={self.torque_constant}, "
            f"drum_radius={self.drum_radius}, gear_ratio={self.gear_ratio}, "
            f"dead_weight={self.dead_weight}",
            level=0,
        )

        # Initialize CAN bus
        self.bus = self.setup_can_bus()

        # Create timer for polling at specified rate
        self.timer = self.create_timer(
            1.0 / self.polling_rate, self.poll_motor_torque
        )

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
                level=2,
            )
            return True
        except Exception as e:
            self.get_logger().error(f"Error sending message: {e}")
            return False

    def parse_float_from_response(self, data):
        """Parse IEEE 754 float from bytes 4-7 of the response, little-endian"""
        try:
            float_bytes = bytes(data[4:8])
            value = struct.unpack('<f', float_bytes)[0]
            self.debug_print(
                f"Parsed float: {value} from bytes {float_bytes.hex()}",
                level=2,
            )
            return value
        except Exception as e:
            self.get_logger().error(f"Error parsing float: {e}")
            return None

    def apply_filter(self, new_value):
        """Apply Moving average filter to the new value"""
        self.torque_buffer.append(new_value)
        if len(self.torque_buffer) < self.filter_window:
            return new_value

        # Simple moving average for efficiency
        filtered = sum(self.torque_buffer) / len(self.torque_buffer)
        self.debug_print(
            f"Filter: input={new_value:.4f}, output={filtered:.4f}", level=2
        )
        return filtered

    def calculate_water_volume(self, torque):
        """Calculate water volume from torque"""
        # Weight = Torque / (radius * gear_ratio * gravity)
        force = torque * self.gear_ratio / (self.drum_radius)
        weight_g = force / 9.81 * 1000

        # Subtract dead weight
        water_weight = weight_g - (self.dead_weight * 1000)

        # Convert to volume (1kg water = 1L)
        volume_ml = water_weight / self.water_density

        # Print intermediate calculations
        self.debug_print(
            f"Water calc: torque={torque:.4f}Nm, force={force:.4f}N, "
            f"weight={weight_g:.4f}g, water_weight={water_weight:.4f}g, "
            f"volume={volume_ml:.4f}mL",
            level=1,
        )

        # Round to integer but keep sign for debugging
        rounded_volume = round(volume_ml)

        # Return positive volume or zero
        result = rounded_volume

        # if result == 0 and volume_ml < 0:
        #     self.debug_print(
        #         f"NOTE: Negative water volume calculated: {volume_ml:.4f}mL",
        #         level=0,
        #     )

        return result

    def poll_motor_torque(self):
        """Poll motor for torque and update water volume"""
        # Send request for Iq
        self.send_message(self.IQ_COMMAND)

        # Wait for response
        message = self.bus.recv(0.2)  # 200ms timeout

        if message:
            self.debug_print(
                f"Received message: ID={message.arbitration_id}, data={self.format_can_data(message.data)}",
                level=2,
            )

            if message.data[0] == 0xB4:
                indicator_id = message.data[1]

                if indicator_id == 0x09:  # Iq
                    current_raw = self.parse_float_from_response(
                        message.data
                    )
                    if current_raw is not None:
                        # Calculate raw torque
                        torque_raw = current_raw * self.torque_constant

                        # Apply filter
                        self.torque = self.apply_filter(torque_raw)
                        self.current = current_raw

                        # Debug torque calculation
                        self.debug_print(
                            f"Torque: current={current_raw:.4f}A, raw_torque={torque_raw:.4f}Nm, filtered_torque={self.torque:.4f}Nm",
                            level=1,
                        )

                        # Calculate water volume
                        self.volume = self.calculate_water_volume(
                            self.torque
                        )
                        
                        
                        # Log and publish data
                        self.debug_print(
                            f"Result: Current={self.current:.2f}A | Torque={self.torque:.4f}Nm | Water={self.volume}mL",
                            level=0,
                        )

                        self.send_torque()
                        self.send_water_volume()
                else:
                    self.debug_print(
                        f"Received non-Iq indicator: {indicator_id}",
                        level=1,
                    )
            else:
                self.debug_print(
                    f"Received non-command response: {message.data[0]}",
                    level=1,
                )
        else:
            self.debug_print("No response received within timeout", level=1)

    def send_water_volume(self):
        """Publish water volume to the /water_qty topic"""
        msg = Int32()
        msg.data = self.volume
        self.water_qty_pub.publish(msg)

    def send_torque(self):
        msg = Int32()
        msg.data = self.torque
        self.get_logger().info(f"Torque: {self.torque}")
        self.torque_pub.publish(msg)

    def shutdown(self):
        """Clean shutdown"""
        self.get_logger().info("Shutting down winch node...")
        if hasattr(self, 'bus'):
            self.bus.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = WaterNode()

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
