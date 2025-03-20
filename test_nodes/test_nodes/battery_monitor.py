import rclpy
from rclpy.node import Node
from sensor_msgs.msg import BatteryState
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy

class BatteryMonitor(Node):
    def __init__(self):
        super().__init__('battery_monitor')

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.subscription = self.create_subscription(
            BatteryState,
            '/mavros/battery',
            self.battery_callback,
            qos_profile
        )
    
    def battery_callback(self, msg):
        self.get_logger().info(f"Voltage: {msg.voltage:.2f}V, Current: {msg.current:.2f}A, Percentage: {msg.percentage*100:.2f}%")

def main(args=None):
    rclpy.init(args=args)
    node = BatteryMonitor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
