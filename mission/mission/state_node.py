#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from mission import helper_func as hf

class StateNode(Node):
    def __init__(self):
        super().__init__("State_node")

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,  
            history=QoSHistoryPolicy.KEEP_LAST,  
            depth=10
        )
        
        self.publisher_ = self.create_publisher(String, 'go_vision', qos_profile)
        self.msg = String()
        self.get_logger().info("✅ State node started and listening.")

        # MAVLink Connection
        self.mav = hf.pymav()
        self.mav.connect('udp:127.0.0.1:14551')
        self.mav.set_mode('GUIDED')
        self.mav.arm()

        # Schedule takeoff using a timer instead of blocking the main thread
        self.timer_takeoff = self.create_timer(1.0, self.takeoff_callback)

    def takeoff_callback(self):
        """Takeoff command, scheduled to prevent blocking."""
        self.get_logger().info("🚀 Takeoff initiated...")
        self.mav.takeoff(20)
        
        self.timer_move = self.create_timer(2.0, self.move_callback)
        
        self.destroy_timer(self.timer_takeoff)

    def move_callback(self):
        """Move to the target position after takeoff."""
        self.get_logger().info("🎯 Moving to target location...")
        self.mav.local_target([100, 0, -10])
        
        
        self.destroy_timer(self.timer_move)

        self.start_vision()

    def start_vision(self):
        self.msg = String()
        self.msg.data = 'GO'
        self.publisher_.publish(self.msg)
        self.get_logger().info(f"VISION GO")



    

def main(args=None):
    rclpy.init(args=args)
    node = StateNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
