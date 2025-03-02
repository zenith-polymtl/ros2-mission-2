import sys
import rclpy
from rclpy.node import Node
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from PyQt6.QtCore import QTimer
from std_msgs.msg import String

class DroneControlGUI(Node, QWidget):
    def __init__(self):
        Node.__init__(self, 'Drone_Control_Interface')
        QWidget.__init__(self)

        self.setWindowTitle("Drone Control Interface")
        self.setGeometry(100, 100, 400, 300)

        # ROS 2 publishers
        self.vision_pub = self.create_publisher(String, '/go_vision', 10)
        self.winch_pub = self.create_publisher(String, '/go_winch', 10)
        self.water_source_pub = self.create_publisher(String, '/go_source_valve', 10)
        self.water_bucket_pub = self.create_publisher(String, '/go_bucket_valve', 10)

        # GUI Layout
        layout = QVBoxLayout()

        self.vision_btn = QPushButton('Vision search')
        self.vision_btn.clicked.connect(self.send_vision)
        layout.addWidget(self.vision_btn)

        self.winch_btn = QPushButton('Winch Down')
        self.winch_btn.clicked.connect(self.send_winch_down)
        layout.addWidget(self.winch_btn)

        self.winch_btn_up = QPushButton('Winch Up')
        self.winch_btn_up.clicked.connect(self.send_winch_up)
        layout.addWidget(self.winch_btn_up)

        self.water_btn_bucket = QPushButton('Release Water')
        self.water_btn_bucket.clicked.connect(self.send_water_bucket)
        layout.addWidget(self.water_btn_bucket)

        self.water_btn_source = QPushButton('Water Refill')
        self.water_btn_source.clicked.connect(self.send_water_source)
        layout.addWidget(self.water_btn_source)

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
        msg.data = "GO"
        self.water_source_pub.publish(msg)
        self.get_logger().info("Water Refill command sent.")

    def send_water_bucket(self):
        msg = String()
        msg.data = "GO"
        self.water_bucket_pub.publish(msg)
        self.get_logger().info("Water release command sent.")

def main(args=None):
    rclpy.init(args=args)
    app = QApplication(sys.argv)
    gui = DroneControlGUI()
    gui.show()
    sys.exit(app.exec())  # Start GUI event loop

if __name__ == '__main__':
    main()