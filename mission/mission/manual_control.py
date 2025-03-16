import sys
import rclpy
from rclpy.node import Node
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QGroupBox, QGridLayout
from PyQt6.QtCore import QTimer
from std_msgs.msg import String

class DroneControlGUI(Node, QWidget):
    def __init__(self):
        Node.__init__(self, 'Drone_Control_Interface')
        QWidget.__init__(self)

        self.setWindowTitle("Drone Control Interface")
        self.setGeometry(500, 500, 400, 550)  # Increased window size

        # ROS 2 publishers
        self.vision_pub = self.create_publisher(String, '/go_vision', 10)
        self.winch_pub = self.create_publisher(String, '/go_winch', 10)
        self.water_source_pub = self.create_publisher(String, '/go_bucket_valve', 10)
        self.water_bucket_pub = self.create_publisher(String, '/go_bucket_valve', 10)
        self.manual_approach = self.create_publisher(String, '/manual', 10)
        self.finished_manual_approach_pub = self.create_publisher(String, '/task_end', 10)
        self.battery_changed_pub = self.create_publisher(String, '/battery_changed', 10)  # NEW Battery publisher

        # Main layout
        main_layout = QVBoxLayout()

        # ➡️ Vision Controls
        vision_box = QGroupBox("Vision Controls")
        vision_layout = QVBoxLayout()
        self.vision_btn = QPushButton('Start Vision Search')
        self.vision_btn.clicked.connect(self.send_vision)
        vision_layout.addWidget(self.vision_btn)
        vision_box.setLayout(vision_layout)
        main_layout.addWidget(vision_box)

        # ➡️ Approach Mode Controls (Manual/Auto)
        approach_box = QGroupBox("Approach Mode")
        approach_layout = QHBoxLayout()
        self.go_manual = QPushButton('Set to Manual')
        self.go_manual.clicked.connect(self.send_manual)
        approach_layout.addWidget(self.go_manual)

        self.go_auto = QPushButton('Set to Auto')
        self.go_auto.clicked.connect(self.send_auto)
        approach_layout.addWidget(self.go_auto)

        approach_box.setLayout(approach_layout)
        main_layout.addWidget(approach_box)

        # ➡️ Task Completion Controls
        task_box = QGroupBox("Task Completion")
        task_layout = QVBoxLayout()
        self.manual_btn = QPushButton('Finish Manual Approach')
        self.manual_btn.clicked.connect(self.finished_manual)
        task_layout.addWidget(self.manual_btn)

        task_box.setLayout(task_layout)
        main_layout.addWidget(task_box)

        # ➡️ Winch Controls
        winch_box = QGroupBox("Winch Controls")
        winch_layout = QHBoxLayout()
        self.winch_btn = QPushButton('Winch Down')
        self.winch_btn.clicked.connect(self.send_winch_down)
        winch_layout.addWidget(self.winch_btn)

        self.winch_btn_up = QPushButton('Winch Up')
        self.winch_btn_up.clicked.connect(self.send_winch_up)
        winch_layout.addWidget(self.winch_btn_up)

        winch_box.setLayout(winch_layout)
        main_layout.addWidget(winch_box)

        # ➡️ Water Controls
        water_box = QGroupBox("Water Controls")
        water_layout = QGridLayout()

        self.water_btn_bucket = QPushButton('Release Water')
        self.water_btn_bucket.clicked.connect(self.send_water_bucket)
        water_layout.addWidget(self.water_btn_bucket, 0, 0)

        self.water_btn_source = QPushButton('Water Refill')
        self.water_btn_source.clicked.connect(self.send_water_source)
        water_layout.addWidget(self.water_btn_source, 0, 1)

        # ➡️ Number of Buckets
        self.bucket_label = QLabel("Number of Buckets:")
        water_layout.addWidget(self.bucket_label, 1, 0)

        self.bucket_input = QLineEdit()
        water_layout.addWidget(self.bucket_input, 1, 1)

        self.set_bucket_btn = QPushButton('Set Buckets')
        self.set_bucket_btn.clicked.connect(self.send_buckets)
        water_layout.addWidget(self.set_bucket_btn, 2, 0, 1, 2)

        water_box.setLayout(water_layout)
        main_layout.addWidget(water_box)

        # ➡️ Battery Status Controls (NEW)
        battery_box = QGroupBox("Battery Status")
        battery_layout = QVBoxLayout()

        self.battery_btn = QPushButton('Battery Changed')
        self.battery_btn.clicked.connect(self.send_battery_changed)
        battery_layout.addWidget(self.battery_btn)

        battery_box.setLayout(battery_layout)
        main_layout.addWidget(battery_box)

        # Set main layout
        self.setLayout(main_layout)

        # Timer to process ROS callbacks
        self.timer = QTimer()
        self.timer.timeout.connect(self.ros_spin_once)
        self.timer.start(100)  # Every 100ms

    def ros_spin_once(self):
        """Process ROS 2 callbacks without blocking the UI."""
        rclpy.spin_once(self, timeout_sec=0.1)

    # ➡️ Vision Commands
    def send_vision(self):
        msg = String()
        msg.data = "GO"
        self.vision_pub.publish(msg)
        self.get_logger().info("Vision command sent.")

    # ➡️ Approach Commands
    def send_manual(self):
        msg = String()
        msg.data = "MANUAL"
        self.manual_approach.publish(msg)
        self.get_logger().info("Switched to manual approach.")

    def send_auto(self):
        msg = String()
        msg.data = "AUTO"
        self.manual_approach.publish(msg)
        self.get_logger().info("Switched to auto approach.")

    def finished_manual(self):
        msg = String()
        msg.data = "END"
        self.finished_manual_approach_pub.publish(msg)
        self.get_logger().info("Manual approach finished.")

    # ➡️ Winch Commands
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

    # ➡️ Water Commands
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

    # ➡️ NEW: Battery Status Command
    def send_battery_changed(self):
        msg = String()
        msg.data = "BATTERY_CHANGED"
        self.battery_changed_pub.publish(msg)
        self.get_logger().info("Battery changed message sent.")

def main(args=None):
    rclpy.init(args=args)
    app = QApplication(sys.argv)
    gui = DroneControlGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
