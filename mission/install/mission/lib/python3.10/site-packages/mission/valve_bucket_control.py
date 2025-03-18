#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
import time
#import RPi.GPIO as GPIO

class ValveNode(Node):
    def __init__(self):
        super().__init__("bucket_valve_Node")
        # GPIO.setmode(GPIO.BCM)
        # self.PWM_PIN = 18
        # self.OPEN_VALVE = 10
        # self.CLOSE_VALVE = 5
        # self.PWM_FREQ = 50

        # GPIO.setup(self.PWM_PIN, GPIO.OUT)
        # self.PWM = GPIO.PWM(self.PWM_PIN, self.PWM_FREQ)
        # self.PWM.start(self.CLOSE_VALVE)

        self.bucketsQty = 5
        self.waterVolume = 4000
        self.openTime = 0
        self.isClosed = True

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,  # Ensures message delivery
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.subscriber_ = self.create_subscription(String, '/go_bucket_valve', self.go_callback, qos_profile)

    def open_valve(self):
        # self.PWM.ChangeDutyCycle(self.OPEN_VALVE)
        self.get_logger().info(f"Opened Valve")
        self.isClosed = False

    def close_valve(self):
        # self.pwm.ChangeDutyCycle(self.CLOSE_VALVE)
        self.get_logger().info(f"Closed Valve")
        self.isClosed = True

    def go_callback(self, msg):
        if msg.data == 'RELEASE' and self.isClosed:
            self.calculate_open_time()
            self.get_logger().info(f"Opening Valve for {self.openTime}")
            self.start_timer()
        elif msg.data == "REFILL":
            self.get_logger().info(f"REFILLING")
            self.openTime = 10
            self.start_timer()
            self.waterVolume = 4000
        else :
            try:
                int(msg.data)
            except:
                self.get_logger().info(f"Unexpected command sent")
            else:
                self.bucketsQty = int(msg.data)
                self.get_logger().info(f"Set number of buckets to {msg.data}")

    def calculate_open_time(self):
        """Calculates the time the valve should stay open based on the amount of water left"""
        maxWater = 4000 

        "faire la fonction de temps ici!!"
        self.openTime = (maxWater / max(self.waterVolume, 0.5)) * (8/self.bucketsQty)
        self.waterVolume = self.waterVolume - (maxWater / self.bucketsQty)
        self.get_logger().info(f"Water volume {self.waterVolume}")
        if self.waterVolume <= 0:
            self.waterVolume = maxWater

    def start_timer(self):
        self.open_valve()
        time.sleep(self.openTime)
        self.close_valve()

        
def main(args=None):
    rclpy.init(args=args)
    node = ValveNode()
    rclpy.spin(node)
    node.destroy_node()
    # GPIO.cleanup()
    rclpy.shutdown()

if __name__ == "__main__":
    main()