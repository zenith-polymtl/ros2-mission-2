import sys
import rclpy
from rclpy.node import Node
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLineEdit, QLabel
from PyQt6.QtCore import QTimer
from std_msgs.msg import String

class DroneControlGUI(Node, QWidget):
    def __init__(self):
        Node.__init__(self, 'Drone_Control_Interface')
        QWidget.__init__(self)

        self.setWindowTitle("Drone Control Interface")
        self.setGeometry(500, 500, 400, 700)  # Increased window size

        # ROS 2 publishers
        self.vision_pub = self.create_publisher(String, '/go_vision', 10)
        self.winch_pub = self.create_publisher(String, '/go_winch', 10)
        self.water_source_pub = self.create_publisher(String, '/go_bucket_valve', 10)
        self.water_bucket_pub = self.create_publisher(String, '/go_bucket_valve', 10)
        self.finished_manual_approach_pub = self.create_publisher(String, '/task_end', 10)

        # GUI Layout
        layout = QVBoxLayout()

        # Vision Button
        self.vision_btn = QPushButton('Vision search')
        self.vision_btn.clicked.connect(self.send_vision)
        layout.addWidget(self.vision_btn)

        # Manual End Button
        self.manual_btn = QPushButton('Finished Manual Approach')
        self.manual_btn.clicked.connect(self.finished_manual)
        layout.addWidget(self.manual_btn)

        # Winch Controls
        self.winch_btn = QPushButton('Winch Down')
        self.winch_btn.clicked.connect(self.send_winch_down)
        layout.addWidget(self.winch_btn)

        self.winch_btn_up = QPushButton('Winch Up')
        self.winch_btn_up.clicked.connect(self.send_winch_up)
        layout.addWidget(self.winch_btn_up)

        # Water Controls
        self.water_btn_bucket = QPushButton('Release Water')
        self.water_btn_bucket.clicked.connect(self.send_water_bucket)
        layout.addWidget(self.water_btn_bucket)

        self.water_btn_source = QPushButton('Water Refill')
        self.water_btn_source.clicked.connect(self.send_water_source)
        layout.addWidget(self.water_btn_source)

        # ➡️ New: Input for Number of Buckets
        self.bucket_label = QLabel("Number of Buckets:")
        layout.addWidget(self.bucket_label)
        self.bucket_label.show()

        self.bucket_input = QLineEdit()
        layout.addWidget(self.bucket_input)
        self.bucket_input.show()

        self.set_bucket_btn = QPushButton('Set Number of Buckets')
        self.set_bucket_btn.clicked.connect(self.send_buckets)
        layout.addWidget(self.set_bucket_btn)
        self.set_bucket_btn.show()

        self.setLayout(layout)

        # Timer to process ROS callbacks
        self.timer = QTimer()
        self.timer.timeout.connect(self.ros_spin_once)
        self.timer.start(100)  # Every 100ms

    def ros_spin_once(self):
        """Process ROS 2 callbacks without blocking the UI."""
        rclpy.spin_once(self, timeout_sec=0.1)

    def send_vision(self):
        msg = String()
        msg.data = "GO"
        self.vision_pub.publish(msg)
        self.get_logger().info("Vision command sent.")

    def finished_manual(self):
        msg = String()
        msg.data = "Finished Manual Approach"
        self.finished_manual_approach_pub.publish(msg)
        self.get_logger().info("Manual approach finished.")

    def send_winch_down(self):
        msg = String()
        msg.data = "DOWN"
        self.winch_pub.publish(msg)
        self.get_logger().info("Winch DOWN command sent.")

    def send_winch_up(self):
        msg = String()
        msg.data = "UP"
        self.winch_pub.publish(msg)
        self.get_logger().info("Winch UP command sent.")

    def send_water_source(self):
        msg = String()
        msg.data = "REFILL"
        self.water_source_pub.publish(msg)
        self.get_logger().info("Water Refill command sent.")

    def send_water_bucket(self):
        msg = String()
        msg.data = "RELEASE"
        self.water_bucket_pub.publish(msg)
        self.get_logger().info("Water release command sent.")

    def send_buckets(self):
        num_buckets = self.bucket_input.text().strip()
        if num_buckets.isdigit():
            msg = String()
            msg.data = num_buckets
            self.water_bucket_pub.publish(msg)
            self.get_logger().info(f"Number of buckets set to: {num_buckets}")
        else:
            self.get_logger().error("Invalid number of buckets. Please enter a valid number.")

def main(args=None):
    rclpy.init(args=args)
    app = QApplication(sys.argv)
    gui = DroneControlGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
