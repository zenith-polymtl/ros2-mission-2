#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Imu
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy


class WinchNode(Node):
    def __init__(self):
        super().__init__("Winch_Node")

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,  # Ensures message delivery
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.subscriber_ = self.create_subscription(String, '/go_winch', self.go_callback, qos_profile)

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,  # Ensures message delivery
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.subscriber_ = self.create_subscription(Imu, '/mavros/imu/data', self.v_accel, qos_profile)
        self.get_logger().info("Winch Subsriber started")

    def go_up(self):
        pass

    def go_down(self):
        pass

    def go_callback(self, msg):
        self.get_logger().info(f"GO MESSAGE : {msg.data}")
        if msg.data == 'UP':
            self.go_up()
        if msg.data == 'DOWN':
            self.go_down()
    
    def v_accel(self, msg):
        self.get_logger().info(f"Vertical accel : {msg.linear_acceleration.z}")

def main(args=None):
    rclpy.init(args=args)
    node = WinchNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()