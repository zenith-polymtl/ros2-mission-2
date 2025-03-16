#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time 
from geometry_msgs.msg import PoseStamped
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
from mission.msg import approach_info

class VisionNode(Node):
    def __init__(self):
        super().__init__("Vision_Node")

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,  # Try RELIABLE if publisher is strict
            history=QoSHistoryPolicy.KEEP_LAST,  # Change to KEEP_ALL if missing messages
            depth=10
        )

        self.go_vision_sub = self.create_subscription(
            String,
            'go_vision',
            self.go_callback,
            qos_profile)

        self.position_sub = self.create_subscription(
            PoseStamped, 
            '/ap/pose/filtered', 
            self.position_callback, 
            qos_profile
        )

        self.bridge = CvBridge()

        self.image_sub = self.create_subscription(
            Image,
            '/camera/image',
            self.image_callback,
            10
        )

        self.go_publisher = self.create_publisher(approach_info, 'go_approach', qos_profile)

        self.image_pub = self.create_publisher(Image, '/camera/image_modified', 10)

        self.position = None
        self.status = False
        self.analysis_time = None

        self.get_logger().info("Vision Node initialized")

    def position_callback(self, msg):
        """Always listening for pose updates while navigation is happening."""
        #self.get_logger().info(f"Position -> X: {msg.pose.position.x}, Y: {msg.pose.position.y}, Z: {msg.pose.position.z}")

        self.position = msg.pose.position
          
    def go_callback(self, msg):
        go_message = msg.data
        self.get_logger().info(f"Received notice : {go_message}")

        if go_message == 'GO':
            self.status = True
            self.analysis_timer = self.create_timer(0.01, self.analysis)
        elif go_message == 'NO GO':
            self.status = False
        else:
            self.get_logger().warning(f"INVALID COMMAND MESSAGE RECEIVED : {go_message}")


    def analysis(self):
        if self.analysis_time == None:
             self.analysis_time = time.time()
        elif ((time.time() - self.analysis_time) < 30):
            self.get_logger().info(f"SIMULATING VISION")
        else:
            self.go_for_approach = approach_info()
            self.go_for_approach.status = 'GO'
            self.go_for_approach.x = 69
            self.go_for_approach.y = 69
            self.go_for_approach.z = -10
            self.go_publisher.publish(self.go_for_approach)
            self.get_logger().info(f"LAUNCHED APPROACH")
            self.analysis_time = None
            self.destroy_timer(self.analysis_timer)

    def image_callback(self, msg):
        self.get_logger().info(f"IMAGE RECEIVED")
        cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")

        # Convert to grayscale
        modified_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # Convert back to ROS2 Image message
        ros_image = self.bridge.cv2_to_imgmsg(modified_image, "mono8")
        ros_image.header.frame_id = "camera_frame"  # Important for RViz


        self.image_pub.publish(ros_image)
        self.get_logger().info(f"IMAGE SENT")

                

def main(args=None):
    rclpy.init(args=args)
    node = VisionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()