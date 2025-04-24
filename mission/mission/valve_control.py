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
from gpiozero import Servo
#import RPi.GPIO as GPIO

class ValveNode(Node):
    def __init__(self):
        super().__init__("bucket_valve_Node")
        '''servo_pin = 3
        # Create a chip instance (adjust the chip number if needed)
        self.chip = gpiod.Chip("gpiochip0")  # Use gpiochip0 for your Pi 5
        self.line1 = self.chip.get_line(servo_pin)
        self.line1.request(consumer="servo_control", type=gpiod.LINE_REQ_DIR_OUT)'''

        self.servo = Servo(18, min_pulse_width=0.0005, max_pulse_width=0.0025)
        self.min_pulse_us = 500  # 500 µs
        self.max_pulse_us = 2500  # 2500 µs
        self.target_pulse_us = 600  # 900 µs

        self.position_900 = (self.target_pulse_us - self.min_pulse_us) / (self.max_pulse_us - self.min_pulse_us) * 2 - 1

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
        self.water_sub = self.create_subscription(String, '/valve_state', self.state_callback)

        self.set_servo_angle(90)  # Initialize the servo to 0 degrees
        self.get_logger().info(f"Valve Initialized")

    def state_callback(self, msg):
        if msg.data == "OPEN":
            self.open_valve()
            self.get_logger().info(f"Opened Valve")
        elif msg.data == "CLOSE":
            self.close_valve()
            self.get_logger().info(f"Closed Valve")
        else:
            self.get_logger().info(f"Unexpected command sent")

    
    def bucket_number_callback(self, msg):
        self.bucketsQty = msg.data
        self.get_logger().info(f"Set number of buckets to {msg.data}")

        
    def open_valve(self):
        self.servo.value = self.position_900  # Applique la position calculée
        self.get_logger().info(f"Opened Valve")
        self.isClosed = False

    def close_valve(self):
        self.servo.mid()
        self.create_timer(0.5, self.detach_servo)
        self.get_logger().info(f"Closed Valve")
        self.isClosed = True

    def detach_servo(self):
        self.servo.detach()
        self.get_logger().info(f"Detached Servo")

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