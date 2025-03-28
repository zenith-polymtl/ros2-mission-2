#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
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
        self.chip = gpiod.Chip("gpiochip4")  # Use gpiochip4 for your Pi 5
        self.line1 = self.chip.get_line(servo_pin)
        self.line1.request(consumer="servo_control", type=gpiod.LINE_REQ_DIR_OUT)

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
    def set_servo_angle(self,angle):
        """
        Set the angle of the servo motor.
        
        :param angle: The desired angle between 0 and 180.
        """
        # Convert the angle to duty cycle
        # Duty cycle values may vary based on the servo model
        duty_cycle = 2 + (angle / 18)  # Example conversion for standard servos
        
        # Calculate high time (in seconds) for PWM
        high_time = duty_cycle / 100.0 * 0.02  # 20 ms period
        low_time = 0.02 - high_time

        # Send the PWM signal
        self.line1.set_value(1)  # Set high
        time.sleep(high_time)  # High duration
        self.line1.set_value(0)  # Set low
        time.sleep(low_time)  # Low duration
        
    def open_valve(self):
        self.set_servo_angle(180) #pas sur
        self.get_logger().info(f"Opened Valve")
        self.isClosed = False

    def close_valve(self):
        self.set_servo_angle(0) #pas sur
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