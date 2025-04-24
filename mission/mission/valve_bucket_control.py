#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_msgs.msg import Int32
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
import time
import gpiod
import time
import numpy as np
#import RPi.GPIO as GPIO

class ValveNode(Node):
    def __init__(self):
        super().__init__("bucket_valve_Node")
        servo_pin = 3
        # Create a chip instance (adjust the chip number if needed)
        self.chip = gpiod.Chip("gpiochip0")  # Use gpiochip0 for your Pi 5
        self.line1 = self.chip.get_line(servo_pin)
        self.line1.request(consumer="servo_control", type=gpiod.LINE_REQ_DIR_OUT)

        self.bucketsQty = None
        self.waterVolume = 0
        self.openTime = None
        self.isClosed = True

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,  # Ensures message delivery
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.subscriber_ = self.create_subscription(String, '/go_bucket_valve', self.go_callback, qos_profile)
        self.bucket_number_sub = self.create_subscription(Int32, '/bucket_number', self.bucket_number_callback, qos_profile)
        self.water_sub = self.create_subscription(Int32, '/water_qty', self.water_sub_callback)

        self.set_servo_angle(90)  # Initialize the servo to 0 degrees
        self.get_logger().info(f"Valve Initialized")
        
    def set_servo_angle(self, angle, duration=1.0):
        #Ici duration est set par défault à 1 seconde,
        # mais on peut le changer pour dequoi de plus court,
        # représente le temps d'application du pm

        duty_cycle = 2 + (angle / 18)
        period = 0.02  # 20 ms
        high_time = duty_cycle / 100.0 * period
        low_time = period - high_time

        end_time = time.time() + duration
        #Loop while blocante, un peu un NoNo ROS, mais c'est court
        #TODO Faire dequoi de mieux

        while time.time() < end_time:
            self.line1.set_value(1)
            time.sleep(high_time)
            self.line1.set_value(0)
            time.sleep(low_time)
    
    def bucket_number_callback(self, msg):
        self.bucketsQty = msg.data
        self.get_logger().info(f"Set number of buckets to {msg.data}")

        
    def open_valve(self):
        self.set_servo_angle(180)
        self.get_logger().info(f"Opened Valve")
        self.isClosed = False

    def close_valve(self):
        self.set_servo_angle(0)
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
        else :
            try:
                int(msg.data)
            except:
                self.get_logger().info(f"Unexpected command sent")
            else:
                self.bucketsQty = int(msg.data)
                self.get_logger().info(f"Set number of buckets to {msg.data}")

    def water_sub_callback(self, msg):
        self.waterVolume = msg.data
        self.get_logger().info(f"Water volume updated to {self.waterVolume}")

        if self.waterVolume <= 500:
            self.waterVolume = 0
            self.get_logger().info(f"Water volume reset to {self.waterVolume}")

    def calculate_open_time(self):
        """Calculates the time the valve should stay open based on the amount of water left"""

        "faire la fonction de temps ici!!"
        currentWaterVol = self.waterVolume

        self.openTime = (690 / max(self.waterVolume, 0.5)) * (8/self.bucketsQty)
        self.get_logger().info(f"Valve open time calculated to {self.openTime:.2f} seconds")

        #Safety logic to make sure the open time is not too long, or too short
        min_bound = 0.2
        max_bound = 10
        if not (self.openTime > min_bound) and (self.openTime < max_bound):
            val = self.openTime
            self.openTime = 0
            self.get_logger().info(f"Valve open time set to 0 seconds, cause out of bounds")
            self.get_logger().info(f"Current val : {val}, bounds : {min_bound} - {max_bound}")

    def start_timer(self):
        self.open_valve()
        self.create_timer(self.openTime, self.timer_callback)

    def timer_callback(self):
        self.close_valve()
        self.get_logger().info(f"Valve closed after {self.openTime:.2f} seconds")	    

        
def main(args=None):
    rclpy.init(args=args)
    node = ValveNode()
    rclpy.spin(node)
    node.destroy_node()
    # GPIO.cleanup()
    rclpy.shutdown()

if __name__ == "__main__":
    main()