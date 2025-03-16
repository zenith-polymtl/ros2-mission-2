#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from std_msgs.msg import String
import itertools
import numpy as np
import time

from rclpy.executors import MultiThreadedExecutor

# Example import of your mission helper (for MAVLink connection, etc.)
import mission.helper_func as hf

"""
Brute force TSP approach
"""
def func_distance(pos1, pos2):
    if len(pos1) != len(pos2):
        raise TypeError("The two points must be of the same dimension")
    return np.linalg.norm(np.array(pos1) - np.array(pos2))

def calculate_cost(route, distances):
    total_cost = 0
    n = len(route)
    for i in range(n):
        current_point = route[i][0]
        next_point = route[(i + 1) % n][0]  # wrap around
        if (current_point, next_point) in distances:
            total_cost += distances[(current_point, next_point)]
        else:
            total_cost += distances[(next_point, current_point)]
    return total_cost

def tmp_solution(buckets):
    # Buckets is list of (name, [x, y, z]) or (name, [lat, lon, alt]) etc.
    distances = {}

    for i in range(len(buckets) - 1):
        for j in range(len(buckets)):
            if j <= i:
                continue
            distances[(buckets[i][0], buckets[j][0])] = func_distance(
                buckets[i][1], buckets[j][1]
            )

    all_permutations = itertools.permutations(buckets)
    min_cost = float('inf')
    optimal_route = None

    for perm in all_permutations:
        cost = calculate_cost(perm, distances)
        if cost < min_cost:
            min_cost = cost
            optimal_route = perm

    return (list(optimal_route), distances)


class StateNode(Node):
    """
    A refactored, non-blocking version using timers + a simple state machine.

    Summary of approach:
    - We'll cycle through mission 'states' in a timer callback (mission_timer).
    - We keep flags & subscriptions to know if certain events happened (e.g. "taken off", "manual approach ended," etc.).
    - We do not block or sleep. We rely on short, repeating timers & conditions to move us from one step to the next.
    """
    def __init__(self, position_dict):
        super().__init__("State_node")

        # QoS
        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )

        # Example “key points”
        self.ground_station = ("ground station", [0, 0, 0])
        self.water_source = ("water source", [50, 50, 20])

        # TSP route
        self.position_dict = position_dict
        self.optimal_route, self.distances = tmp_solution(self.position_dict)

        # Internal flags
        self.reached_target = False
        self.battery_changed = False
        self.taken_off = False
        self.armed = False
        self.manual = False
        self.finished_manual_approach = False

        # Example drone info
        self.drone_battery = 100.0   # in percent
        self.drone_travel_efficiency = 2  # distance units per % battery
        self.current_pos = self.ground_station  # We store e.g. (name, [x,y,z])

        # Publishers
        self.publisher_ = self.create_publisher(String, "/go_vision", qos_profile)
        self.msg = String()

        # Subs
        self.manual_sub = self.create_subscription(
            String, '/manual', self.manual_callback, qos_profile
        )
        self.finished_manual_sub = self.create_subscription(
            String, '/task_end', self.end_approach_callback, qos_profile
        )
        self.battery_sub = self.create_subscription(
            String, '/battery_changed', self.notify_battery, qos_profile
        )
        self.abort_sub = self.create_subscription(
            String, '/abort_state', self.abort, qos_profile
        )
        self.armed_sub = self.create_subscription(
            String, '/armed_confirmation', self.confirm_arming, qos_profile
        )

        # MAVLink
        self.mav = hf.pymav()
        self.mav.connect("udp:127.0.0.1:14551")

        # Set up repeated timers
        # 1) battery check: every 10s
        self.timer_battery = self.create_timer(10.0, self.charge_opportunity)
        # 2) mission “tick”: every 0.5s we’ll check self.state and do the next steps
        self.mission_timer = self.create_timer(0.5, self.mission_tick)

        # We'll track mission states in a simple enumerated pattern
        self.mission_state = 0
        self.bucket_index = 0

        self.get_logger().info("StateNode ready. Starting mission logic.")

        # Start the mission right away: arm & prepare
        self.setup_for_takeoff()

    # --------------------------------------------------------------------------
    # MAIN "STATE MACHINE" TICK
    # This callback runs on a short interval and transitions states as needed
    # --------------------------------------------------------------------------
    def mission_tick(self):
        """
        Called periodically; checks which step of the mission we’re in and transitions
        once conditions are satisfied.
        """
        if self.mission_state == 0:
            # WAIT FOR ARMED -> TAKE OFF
            # Once armed, we’ll command takeoff, then watch for 'taken_off'
            if self.armed and not self.taken_off:
                self.get_logger().info("Armed, now taking off to 10m.")
                self.mav.takeoff(10, wait_to_takeoff=False)  # example usage
                # We do not block. We'll rely on e.g. a telemetry callback to set self.taken_off when altitude is reached
                self.mission_state = 1

        elif self.mission_state == 1:
            # WAIT UNTIL taken_off == True
            if self.taken_off:
                self.get_logger().info("Takeoff complete => Going to water source.")
                # Start flying to water source (non-blocking)
                self.mav.global_target(self.water_source[1], wait_to_reach=False)
                self.mission_state = 2

        elif self.mission_state == 2:
            # WAIT TILL we have reached the water source
            # You would likely check your telemetry or a “reached_target” condition.
            # For demonstration, we use self.reached_target to simulate arrival.
            if self.reached_target:
                self.get_logger().info("Reached water source location.")
                self.reached_target = False
                # Next step: check if we are in manual or not
                if not self.manual:
                    self.start_vision()
                    self.mission_state = 3
                else:
                    self.get_logger().info("Manual approach needed; waiting for /task_end.")
                    self.mission_state = 4

        elif self.mission_state == 3:
            # WAIT FOR vision approach to finish automatically...
            # This might be signaled by a different subscription or callback
            # For demonstration, let's suppose the vision node sets self.reached_target = True
            if self.reached_target:
                self.get_logger().info("Auto approach done. Now proceed to bucket loop.")
                self.reached_target = False
                self.mission_state = 5

        elif self.mission_state == 4:
            # WAIT for manual approach done
            if self.finished_manual_approach:
                self.get_logger().info("Manual approach finished. Proceed to bucket loop.")
                self.finished_manual_approach = False
                self.mission_state = 5

        elif self.mission_state == 5:
            # Start traveling the TSP route
            if self.bucket_index >= len(self.optimal_route):
                # No more buckets, go home
                self.get_logger().info("All buckets visited => returning to launch.")
                self.mav.RTL(wait_to_land=False)
                self.mission_state = 99
                return
            # Else move to the next bucket
            route_name, route_coords = self.optimal_route[self.bucket_index]
            if self.possible_movement((route_name, route_coords)):
                self.get_logger().info(f"Moving to bucket {route_name} ...")
                self.mav.global_target(route_coords, wait_to_reach=False)
                self.mission_state = 6
            else:
                # Not enough battery => RTL
                self.get_logger().info("Battery insufficient => RTL.")
                self.mav.RTL(wait_to_land=False)
                self.mission_state = 99

        elif self.mission_state == 6:
            # WAIT for next bucket arrival
            if self.reached_target:
                self.get_logger().info("Arrived at bucket => do approach (auto or manual).")
                self.reached_target = False
                if not self.manual:
                    self.start_vision()
                    self.mission_state = 7
                else:
                    self.mission_state = 8

        elif self.mission_state == 7:
            # WAIT for auto approach done at the bucket
            if self.reached_target:
                self.get_logger().info("Auto approach done at bucket. Next bucket.")
                self.reached_target = False
                self.bucket_index += 1
                self.mission_state = 5  # loop back to traveling the route

        elif self.mission_state == 8:
            # WAIT for manual approach done at the bucket
            if self.finished_manual_approach:
                self.get_logger().info("Manual approach done at bucket. Next bucket.")
                self.finished_manual_approach = False
                self.bucket_index += 1
                self.mission_state = 5

        elif self.mission_state == 99:
            # End of mission
            self.get_logger().info("Mission complete or aborted.")
            # Could do self.destroy_node() or keep node alive
            pass

    # --------------------------------------------------------------------------
    # HELPER & CALLBACKS
    # --------------------------------------------------------------------------
    def setup_for_takeoff(self):
        """Commands arming, sets mode, etc."""
        self.get_logger().info("Launching mission: set mode GUIDED + arm request.")
        self.mav.set_mode('GUIDED')
        # or you can do self.mav.arm() right away
        # Then we wait for armed_sub to confirm_arming.

    def start_vision(self):
        """Publishes a message telling a 'vision' node to start approach."""
        msg = String()
        msg.data = "GO"
        self.publisher_.publish(msg)
        self.get_logger().info("VISION GO published.")

    def wait_for_manual_approach(self):
        """
        No longer blocking! We do not do while loop. Instead, we watch
        self.finished_manual_approach in mission_tick.
        """
        pass

    # Example subscription callbacks
    def end_approach_callback(self, msg):
        if msg.data == "END":
            self.finished_manual_approach = True
            self.get_logger().info("Received manual approach done.")

    def manual_callback(self, msg):
        if msg.data == "MANUAL":
            self.manual = True
        elif msg.data == "AUTO":
            self.manual = False

    def abort(self, msg):
        self.get_logger().info("Shutting down node (ABORT).")
        self.destroy_node()
        rclpy.shutdown()

    def confirm_arming(self, msg):
        self.armed = True
        self.get_logger().info("Received readiness for takeoff (armed).")

    def notify_battery(self, msg):
        if msg.data == "CHANGED":
            self.drone_battery = 100.0
            self.battery_changed = True
            self.get_logger().info("Battery changed => drone battery set to 100%.")

    def charge_opportunity(self):
        """
        Non-blocking battery check. If near ground station and battery <= 10%, we can RTL, wait, recharge, etc.
        In reality you’d want more robust approach for real flights.
        """
        # Use your local or global pos to see if we are near ground station
        # For simplicity, skip real geometry.
        if self.drone_battery <= 10:
            self.get_logger().info("Battery near 10%. Attempting RTL + re-charge.")
            self.mav.RTL(wait_to_land=False)
            # Once landed, you might set self.taken_off=False, do a short “charging” approach, etc.
            time.sleep(3)  # not recommended in real callbacks, but left for demonstration
            self.drone_battery = 100.0
            self.get_logger().info("Battery is charged => ready to fly again")

    def possible_movement(self, target_pos):
        """
        Checks if we have enough battery to get from self.current_pos to target, and
        then from target to base. This is simplified from your code. Also note that we
        do not block. 
        """
        # In real usage, we’d do the geometry or TSP-distances. 
        # Here is an example:
        route_name, route_coords = target_pos
        # if distance is large:
        #   return False
        # else:
        #   return True
        return True

    # Example simulation method for setting “taken_off” or “reached_target.”
    # In reality you’d have MAVLink telemetry with altitude to set self.taken_off
    # or a distance check to set self.reached_target.

def main(args=None):
    rclpy.init(args=args)

    # Example buckets
    buckets = [
        ("bucket_1", [50.101222, -110.738856, 10]),
        ("bucket_2", [50.101196, -110.739031, 10]),
        ("bucket_3", [50.101195, -110.738814, 10]),
        ("bucket_4", [50.101195, -110.738554, 10]),
        ("bucket_5", [50.101928, -110.738858, 10]),
        ("bucket_6", [50.101876, -110.738629, 10]),
    ]

    node = StateNode(buckets)
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
