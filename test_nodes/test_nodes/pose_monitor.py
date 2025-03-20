import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from mission_interfaces.srv import GetPose

class PoseSubscriber(Node):
    def __init__(self):
        super().__init__('pose_subscriber')
        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.latest_pose = None

        self.subscription = self.create_subscription(
            PoseStamped,
            '/ap/pose/filtered',  # Topic name
            self.pose_callback,
            qos_profile  # Queue size
        )

        # Create a service that returns the latest pose
        self.srv = self.create_service(
            GetPose,  # Custom service type
            'get_pose',  # Service name
            self.get_pose_callback
        )
        self.get_logger().info("Pose subscriber initialized, listening to /ap/pose/filtered")

    def pose_callback(self, msg):
        self.latest_pose = msg.pose
        x = msg.pose.position.x
        y = msg.pose.position.y
        z = msg.pose.position.z
        qx = msg.pose.orientation.x
        qy = msg.pose.orientation.y
        qz = msg.pose.orientation.z
        qw = msg.pose.orientation.w

        self.get_logger().info(
            f"Position -> x: {x:.2f}, y: {y:.2f}, z: {z:.2f}\n"
            f"Orientation -> qx: {qx:.2f}, qy: {qy:.2f}, qz: {qz:.2f}, qw: {qw:.2f}"
        )
    
    def get_pose_callback(self, request, response):
        if self.latest_pose is None:
            response.success = False
            response.message = "No pose received yet."
            return response

        response.success = True
        response.message = "Latest pose retrieved."
        response.position_x = self.latest_pose.position.x
        response.position_y = self.latest_pose.position.y
        response.position_z = self.latest_pose.position.z
        response.orientation_x = self.latest_pose.orientation.x
        response.orientation_y = self.latest_pose.orientation.y
        response.orientation_z = self.latest_pose.orientation.z
        response.orientation_w = self.latest_pose.orientation.w

        self.get_logger().info('Latest pose sent.')
        return response

def main(args=None):
    rclpy.init(args=args)
    node = PoseSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
