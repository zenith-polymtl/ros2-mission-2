#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Imu
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
import time

class ValveNode(Node):
    def __init__(self):
        super().__init__("bucket_valve_Node")

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,  # Ensures message delivery
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.subscriber_ = self.create_subscription(String, '/go_source_valve', self.go_callback, qos_profile)

    def open_valve(self):
        self.get_logger().info(f"Opened Valve")

    def close_valve(self):
        self.get_logger().info(f"Closed Valve")

    def go_callback(self, msg):
        self.get_logger().info(f"GO MESSAGE BUCKET VALVE: {msg.data}")
        if msg.data == 'GO':
            self.open_valve()
            time.sleep(10)
            self.close_valve()
    

def main(args=None):
    rclpy.init(args=args)
    node = ValveNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()