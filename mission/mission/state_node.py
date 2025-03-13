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


def func_distance(pos1: list[int], pos2: list[int]) -> float:
    """
    Function to find the distance between two points
    """
    if len(pos1) != len(pos2):
        raise TypeError("The two points must be of the same dimension")
    delta = 0.0
    for i in range(len(pos1)):
        delta += (pos2[i] - pos1[i]) ** 2

    return delta ** (0.5)


def calculate_cost(route: list[tuple], distances: dict) -> float:
    """
    Function to calculate the total cost of a route
    """
    total_cost = 0
    n = len(route)
    for i in range(n):
        current_point = route[i][0]
        next_point = route[(i + 1) % n][0]  # Wrap around to the start of the route
        # Look up the distance in both directions
        if (current_point, next_point) in distances:
            total_cost += distances[(current_point, next_point)]
        else:
            total_cost += distances[(next_point, current_point)]
    return total_cost


def tmp_solution(buckets: dict) -> list[tuple[str, list[int]]]:
    """
    Function that takes in a dict. (name: bucket postion) and outputs the optimal route to take
    """
    # Dict. that holds all distances
    distances = {}

    for i in range(len(buckets) - 1):
        for j in range(len(buckets)):
            if j <= i:
                pass
            else:
                distances[(buckets[i][0], buckets[j][0])] = func_distance(
                    buckets[i][1], buckets[j][1]
                )

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
    # answer.append(buckets[0]) # Assuming we come back to the starting point

    # Return the optimal route
    return answer


class StateNode(Node):
    def __init__(self, position_dict: dict):
        super().__init__("State_node")

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )

        # Let's define the important points in space
        self.water_source = ("water source", [50, 50, 20])
        # Optimal route to go to all buckets with the Travelling Marchant Problem brute force solution
        self.position_dict = position_dict
        self.optimal_route = tmp_solution(self.position_dict)

        self.publisher_ = self.create_publisher(String, "go_vision", qos_profile)
        self.msg = String()
        self.get_logger().info("✅ State node started and listening.")

        # MAVLink Connection
        self.mav = hf.pymav()
        # self.mav.connect('udp:127.0.0.1:14551')
        self.mav.set_mode("GUIDED")

        # Schedule takeoff using a timer instead of blocking the main thread
        self.timer_takeoff = self.create_timer(1.0, self.takeoff_callback)

        # Then destroying the takeoff timer and starting the vision node
        self.destroy_timer(self.timer_takeoff)
        self.start_vision()

        # Schedule moving to the water source using a timer instead of blocking the main thread
        self.timer_move = self.create_timer(
            2.0, self.move_callback(self.water_source[0][1], self.water_source[0][0])
        )
        # Starting the node to fill up the water tank
        self.start_filling_up()

        for _ in range(len(self.optimal_route)):
            # Schedule moving to the current bucket using a timer instead of blocking the main thread
            self.timer_move = self.create_timer(
                2.0,
                self.move_callback(self.optimal_route[0][1], self.optimal_route[0][0]),
            )
            # Starting the node to drop water
            self.start_dropping_water()
            # Removing the current bucket from the list
            self.optimal_route.pop(0)

        # If there are no buckets to go to, return to base
        if len(self.optimal_route) == 0:
            self.mav.RTL()

    def takeoff_callback(self) -> None:
        """Takeoff command, scheduled to prevent blocking."""
        self.get_logger().info("🚀 Takeoff initiated...")
        self.mav.arm()
        self.mav.takeoff(20)

    def move_callback(self, pos_coordinates: list[int], pos_name: str = "") -> None:
        """Move to the target position."""
        self.get_logger().info(f"🎯 Moving to target location {pos_name} ...")
        self.mav.global_target(pos_coordinates)

        # Destroying the "travel" timer
        self.destroy_timer(self.timer_move)

    def start_vision(self) -> None:
        self.msg = String()
        self.msg.data = "GO"
        self.publisher_.publish(self.msg)
        self.get_logger().info(f"VISION GO")

    def start_filling_up(self) -> None:
        self.msg = String()
        self.msg.data = "GO"
        self.publisher_.publish(self.msg)
        self.get_logger().info(f"FILLING UP GO")

    def start_dropping_water(self) -> None:
        self.msg = String()
        self.msg.data = "GO"
        self.publisher_.publish(self.msg)
        self.get_logger().info(f"DROPPING WATER GO")


# Define the buckets and their distances
# TODO Make it so this dict. is not hard coded. I believe this data would come from the first phase.
buckets = [
    ("bucket_1", [10, 0, 10]),
    ("bucket_2", [0, 10, 10]),
    ("bucket_3", [0, 5, 15]),
    ("bucket_4", [6, 0, 66]),
    ("bucket_5", [0, 40, 10]),
    ("bucket_6", [20, 30, 10]),
    ("bucket_7", [20, 234, 223]),
    ("bucket_8", [222, 10, 49]),
]


def main(args=None):
    rclpy.init(args=args)
    node = StateNode(buckets)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
