#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
import helper_func as hf
import itertools

# Taken from https://medium.com/@davidlfliang/intro-python-algorithms-traveling-salesman-problem-ffa61f0bd47b
"""
Brute force approach to the tmp
"""

def func_distance(pos1,pos2):
    """
    Function to find the distance between two points
    """
    if len(pos1) != len(pos2):
        raise TypeError("The two points must be of the same dimension")
    delta = 0
    for i in range(len(pos1)):
        delta += (pos2[i]-pos1[i])**2

    return delta**(0.5)

def calculate_cost(route, distances):
    """
    Function to calculate the total cost of a route
    """
    total_cost = 0
    n = len(route)
    for i in range(n):
        current_city = route[i][0]
        next_city = route[(i + 1) % n][0]  # Wrap around to the start of the route
        # Look up the distance in both directions
        if (current_city, next_city) in distances:
            total_cost += distances[(current_city, next_city)]
        else:
            total_cost += distances[(next_city, current_city)]
    return total_cost

def tmp_solution(buckets: dict) -> list[tuple[str, list[int]]]:
    """
    Function that takes in a dict. (name: bucket postion) and outputs the optimal route to take
    """
    # Dict. that holds all distances
    distances = {}

    for i in range(len(buckets)-1):
        for j in range(len(buckets)):
            if j<=i:
                pass
            else:
                distances[(buckets[i][0],buckets[j][0])] = func_distance(buckets[i][1],buckets[j][1])

    # Generate all permutations of the buckets
    all_permutations = itertools.permutations(buckets)

    # Initialize variables to track the minimum cost and corresponding route
    min_cost = float("inf")
    optimal_route = None

    # Iterate over all permutations and calculate costs
    for perm in all_permutations:
        cost = calculate_cost(perm, distances)
        if cost < min_cost:
            min_cost = cost
            optimal_route = perm

    answer = []
    for bucket in optimal_route:
        answer.append(bucket)
    #answer.append(buckets[0]) # Assuming we come back to the starting point

    # Return the optimal route
    return answer

class StateNode(Node):
    def __init__(self, 
                 position_dict: dict):
        super().__init__("State_node")

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,  
            history=QoSHistoryPolicy.KEEP_LAST,  
            depth=10
        )

        self.position_dict = position_dict
        self.optimal_route = tmp_solution(self.position_dict)
        
        self.publisher_ = self.create_publisher(String, 'go_vision', qos_profile)
        self.msg = String()
        self.get_logger().info("✅ State node started and listening.")

        # MAVLink Connection
        self.mav = hf.pymav()
        self.mav.connect('udp:127.0.0.1:14551')
        self.mav.set_mode('GUIDED')
        

        # Schedule takeoff using a timer instead of blocking the main thread
        self.timer_takeoff = self.create_timer(1.0, self.takeoff_callback)

    def takeoff_callback(self):
        """Takeoff command, scheduled to prevent blocking."""
        self.get_logger().info("🚀 Takeoff initiated...")
        self.mav.arm()
        self.mav.takeoff(20)
        
        self.timer_move = self.create_timer(2.0, self.move_callback)
        
        self.destroy_timer(self.timer_takeoff)

    def move_callback(self):
        """Move to the target position after takeoff."""
        self.get_logger().info("🎯 Moving to target location...")
        self.mav.global_target(self.optimal_route[0][1])
        
        
        self.destroy_timer(self.timer_move)

        self.start_vision()

    def start_vision(self):
        self.msg = String()
        self.msg.data = 'GO'
        self.publisher_.publish(self.msg)
        self.get_logger().info(f"VISION GO")

# Define the buckets and their distances
#TODO Make it so this dict. is not hard coded
buckets = [("bucket_1", [10,0,10]),
          ("bucket_2", [0,10,10]),
          ("bucket_3", [0,5,15]),
          ("bucket_4", [6,0,66]),
          ("bucket_5", [0,40,10]),
          ("bucket_6", [20,30,10]),
          ("bucket_7", [20,234,223]),
          ("bucket_8", [222,10,49])]

def main(args=None):
    rclpy.init(args=args)
    node = StateNode(buckets)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
