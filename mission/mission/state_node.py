#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
import itertools
import numpy as np
import time
import asyncio

def func_distance(pos1, pos2):
    return np.linalg.norm(np.array(pos1) - np.array(pos2))

def calculate_cost(route, distances):
    total_cost = 0
    n = len(route)
    for i in range(n):
        current_point = route[i][0]
        next_point = route[(i + 1) % n][0]
        if (current_point, next_point) in distances:
            total_cost += distances[(current_point, next_point)]
        else:
            total_cost += distances[(next_point, current_point)]
    return total_cost

async def tmp_solution(buckets):
    distances = {}

    for i in range(len(buckets) - 1):
        for j in range(len(buckets)):
            if j <= i:
                continue
            distances[(buckets[i][0], buckets[j][0])] = func_distance(
                buckets[i][1], buckets[j][1]
            )

    all_permutations = itertools.permutations(buckets)
    
    min_cost = float("inf")
    optimal_route = None

    for perm in all_permutations:
        cost = calculate_cost(perm, distances)
        if cost < min_cost:
            min_cost = cost
            optimal_route = perm

    answer = []
    for bucket in optimal_route:
        answer.append(bucket)

    return (answer, distances)

class StateNode(Node):
    def __init__(self, position_dict):
        super().__init__("State_node")

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.ground_station = ("ground station", [0, 0, 0])
        self.water_source = ("water source", [50, 50, 20])

        # Drone status
        self.reached_target = False
        self.taken_off = False
        self.manual = False
        self.finished_manual_approach = False

        # Subscribers
        self.manual_sub = self.create_subscription(String, '/manual', self.manual_callback, qos_profile)
        self.finished_manual_sub = self.create_subscription(String, '/task_end', self.end_approach_callback, qos_profile)
        self.publisher_ = self.create_publisher(String, "/go_vision", qos_profile)

        # MAVLink Connection
        self.get_logger().info("✅ Connecting to MAVLink...")
        self.drone_battery = 100.0
        self.mav = None

        # Start mission without blocking!
        asyncio.create_task(self.start_mission(position_dict))

    async def start_mission(self, position_dict):
        # ✅ Non-blocking TSP calculation
        self.get_logger().info("🚀 Solving TSP...")
        self.optimal_route, self.distances = await tmp_solution(position_dict)
        self.get_logger().info("✅ TSP solved!")

        await self.takeoff()
        await self.move_to(self.water_source)

        for target in self.optimal_route:
            if not self.possible_movement(target):
                self.get_logger().warn("⚠️ Battery too low — returning to base")
                await self.mav.RTL()
                break

            await self.move_to(target)
            await self.start_vision()
            self.optimal_route.pop(0)

        if not self.optimal_route:
            self.get_logger().info("✅ All targets completed — returning to base")
            await self.mav.RTL()

    async def takeoff(self):
        self.get_logger().info("🚀 Takeoff initiated...")
        await asyncio.sleep(2)  # Simulate takeoff time
        self.taken_off = True

    async def move_to(self, target):
        self.get_logger().info(f"🎯 Moving to {target[0]}...")
        await asyncio.sleep(2)  # Simulate movement time
        self.reached_target = True

    async def start_vision(self):
        self.get_logger().info("👀 Starting vision...")
        msg = String()
        msg.data = "GO"
        self.publisher_.publish(msg)
        await asyncio.sleep(1)  # Simulate vision delay

    async def possible_movement(self, target_pos):
        next_distance = self.distances.get(
            (self.ground_station[0], target_pos[0]),
            func_distance(self.ground_station[1], target_pos[1])
        )
        distance_to_base = func_distance(target_pos[1], self.ground_station[1])
        battery_at_target = self.drone_battery - (next_distance / 2)
        autonomy_at_target = battery_at_target * 2
        return autonomy_at_target > distance_to_base

    def manual_callback(self, msg):
        self.manual = msg.data == "MANUAL"

    def end_approach_callback(self, msg):
        if msg.data == "END":
            self.finished_manual_approach = True

def main(args=None):
    rclpy.init(args=args)
    buckets = [
        ("bucket_1", [50.101222, -110.738856, 10]),
        ("bucket_2", [50.101196, -110.739031, 10]),
        ("bucket_3", [50.101195, -110.738814, 10]),
        ("bucket_4", [50.101195, -110.738554, 10]),
        ("bucket_5", [50.101928, -110.738858, 10]),
        ("bucket_6", [50.101876,-110.738629, 10]),
    ]
    node = StateNode(buckets)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
