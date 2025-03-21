#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
import mission.helper_func as hf
import itertools
import numpy as np
import time

def func_distance(pos1, pos2):
    return np.linalg.norm(np.array(pos1) - np.array(pos2))

def calculate_cost(route, distances):
    total_cost = 0
    n = len(route)
    for i in range(n):
        current_pt = route[i][0]
        next_pt = route[(i + 1) % n][0]  # wrap around
        if (current_pt, next_pt) in distances:
            total_cost += distances[(current_pt, next_pt)]
        else:
            total_cost += distances[(next_pt, current_pt)]
    return total_cost

def tmp_solution(buckets):
    distances = {}
    # Build up a dictionary of pairwise distances
    for i in range(len(buckets) - 1):
        for j in range(i + 1, len(buckets)):
            d = func_distance(buckets[i][1], buckets[j][1])
            distances[(buckets[i][0], buckets[j][0])] = d

    all_permutations = itertools.permutations(buckets)
    min_cost = float("inf")
    optimal_route = None
    for perm in all_permutations:
        cost = calculate_cost(perm, distances)
        if cost < min_cost:
            min_cost = cost
            optimal_route = perm

    # Return the best route plus the distance dict
    return list(optimal_route), distances

# ---------------------------
#   Define mission STATES
# ---------------------------
class MissionState:
    IDLE                = 0
    TAKEOFF             = 1
    WAIT_FOR_TAKEOFF    = 2
    GOTO_WATER_SOURCE   = 3
    WAIT_FOR_WP         = 4
    SOURCE_APPROACH     = 5
    GOTO_NEXT_BUCKET    = 6
    WAIT_FOR_BUCKET     = 7
    BUCKET_APPROACH     = 8
    WAIT_FINISH         = 9
    FINISHED            = 99
    # You can add states for manual override if you want, e.g. MANUAL_OVERRIDE = 100

class StateNode(Node):
    def __init__(self, position_dict):
        super().__init__("State_node")

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        # TSP route setup
        self.position_dict = position_dict
        self.optimal_route, self.distances = tmp_solution(self.position_dict)

        # Some fixed references
        self.ground_station = ("ground station", [0, 0, 0])
        self.water_source   = ("water source", [50.1013, -110.734, 20])
        self.current_pos    = None   # store last known drone position
        self.current_target = None   # whichever waypoint we’re currently trying to reach

        # We track mission states
        self.state = MissionState.IDLE
        self.finished_manual_approach = False  # from your example
        self.manual       = False
        self.taken_off    = False
        self.reached_wp   = False
        self.ready_to_fly = False

        # Battery info
        self.drone_battery = 100.0
        self.drone_travel_efficiency = 2.0  # distance units per 1% battery

        # Create Publishers / Subscribers
        self.publisher_vision = self.create_publisher(String, "/go_vision", qos_profile)
        self.manual_sub       = self.create_subscription(String, '/manual', self.manual_callback, qos_profile)
        self.finished_manual_sub = self.create_subscription(String, '/task_end', self.end_approach_callback, qos_profile)
        self.battery_sub      = self.create_subscription(String, '/battery_changed', self.notify_battery, qos_profile)
        self.abort_sub        = self.create_subscription(String, '/abort_state', self.abort, qos_profile)
        self.armed_sub = self.create_subscription(String, '/confirm_arming', self.confirm_arming, qos_profile)

        # We remove “armed_sub” for brevity, or keep it if you have code for that
        # self.armed_sub = self.create_subscription(...)

        # MAVLink Connection
        self.mav = hf.pymav()
        self.mav.connect("udp:127.0.0.1:14551")

        # Start a short, frequent timer for mission logic
        self.main_timer = self.create_timer(0.5, self.mission_step)
        # Start a less frequent timer for battery checks
        self.batt_timer = self.create_timer(10.0, self.charge_opportunity)

        self.get_logger().info("✅ State node started (non-blocking).")

    def abort(self, msg):
        self.get_logger().info('Shutting down node...')
        self.destroy_node()
        rclpy.shutdown()

    def notify_battery(self, msg):
        if msg.data == "CHANGED":
            self.drone_battery = 100.0

    def manual_callback(self, msg):
        if msg.data == "MANUAL":
            self.manual = True
        elif msg.data == "AUTO":
            self.manual = False

    def end_approach_callback(self, msg):
        if msg.data == "END":
            self.finished_manual_approach = True

    # -----------------------------------------------------
    #  The main state machine logic runs in mission_step()
    # -----------------------------------------------------
    def mission_step(self):
        # At each timer tick, we check which state we are in,
        # see if we have completed it, or if we need to do something else.

        # Example manual override check:
        if self.manual:
            # If you want a dedicated override state, you can set self.state
            # to something like MANUAL_OVERRIDE. Or you can let your normal
            # steps keep going, but rely on other logic. That’s up to you.
            #self.get_logger().info("Manual override: user can take control if needed.")
            # For now, we’ll just keep going. 
            # If you want to do something special, do it here.

            pass

        if self.state == MissionState.IDLE:
            self.get_logger().info("🚀 Waiting for arming and guided.")
            # We want to start by takeoff
            if self.ready_to_fly:
                self.mav.takeoff(20, wait_to_takeoff=False)  # Non-blocking call
                self.taken_off = False
                self.state = MissionState.WAIT_FOR_TAKEOFF
                self.get_logger().info("🚀 Takeoff initiated. Transition to WAIT_FOR_TAKEOFF.")

        elif self.state == MissionState.WAIT_FOR_TAKEOFF:
            # Check if we are at ~alt=20
            N,E, D = self.mav.get_local_pos()
            # Suppose we consider "taken_off" if alt >= 18
            if -18 >= D:
                self.taken_off = True 
                self.get_logger().info("Takeoff complete! Transition to GOTO_WATER_SOURCE.")
                self.state = MissionState.GOTO_WATER_SOURCE

        elif self.state == MissionState.GOTO_WATER_SOURCE:
            # we just set a global target
            self.current_target = self.water_source
            self.send_global_target(self.water_source, label="WATER SOURCE")
            self.reached_wp = False
            self.state = MissionState.WAIT_FOR_WP

        elif self.state == MissionState.WAIT_FOR_WP:
            # Check if near the current_target
            if self.mav.is_near_waypoint(self.current_target[1], self.mav.get_global_pos(), 0.00001):
                self.reached_wp = True
                self.get_logger().info("Reached water source. Next: VISION/APPROACH.")
                self.state = MissionState.SOURCE_APPROACH

        elif self.state == MissionState.SOURCE_APPROACH:
            # This is where your code does the "start_vision()"
            # Possibly check if you want manual approach or not:
            if not self.manual:
                self.finished_bucket = False
                self.start_vision('source')
                # we assume it completes instantly or triggers something
                # you could set a short wait or event
                self.state = MissionState.WAIT_FINISH
                self.target_is_source = True
            else:
                # If manual, we wait for /task_end:
                if self.finished_manual_approach:
                    self.state = MissionState.GOTO_NEXT_BUCKET
                    self.finished_manual_approach = False
                else:
                    self.get_logger().info("Waiting for manual approach to end...")

        elif self.state == MissionState.WAIT_FINISH:
            if self.finished_bucket:
                self.get_logger().info("Target treated successfully")
                self.state = MissionState.GOTO_NEXT_BUCKET
                self.finished_bucket = False
                if not self.target_is_source:
                    self.optimal_route.pop(0)

        elif self.state == MissionState.GOTO_NEXT_BUCKET:
            if len(self.optimal_route) == 0:
                # No more buckets, we are done
                self.get_logger().info("No more buckets => Return to base (RTL).")
                self.mav.RTL()
                self.state = MissionState.FINISHED
                return

            # Grab the next bucket
            next_bucket = self.optimal_route[0]
            if not self.possible_movement(next_bucket):
                self.get_logger().warn("Not enough battery to reach next bucket + return; RTL now.")
                self.mav.RTL()
                self.state = MissionState.FINISHED
                return

            # We do have enough battery, so go
            self.current_target = next_bucket
            self.send_global_target(next_bucket, label=next_bucket[0])
            self.reached_wp = False
            self.state = MissionState.WAIT_FOR_BUCKET

        elif self.state == MissionState.WAIT_FOR_BUCKET:
            if self.mav.is_near_waypoint(self.current_target[1], self.mav.get_global_pos(), 0.00001):
                self.reached_wp = True
                self.get_logger().info(f"Arrived at {self.current_target[0]} => bucket approach")
                self.state = MissionState.BUCKET_APPROACH

        elif self.state == MissionState.BUCKET_APPROACH:
            # Start vision, or do manual approach again
            if not self.manual:
                self.finished_bucket = False
                self.start_vision('bucket')
                # we assume it completes instantly or triggers something
                # you could set a short wait or event
                self.state = MissionState.WAIT_FINISH
            else:
                # If manual, we wait for /task_end:
                if self.finished_manual_approach:
                    self.state = MissionState.GOTO_NEXT_BUCKET
                    self.finished_manual_approach = False
                    self.optimal_route.pop(0)
                else:
                    self.get_logger().info("Waiting for manual approach to end...")

        elif self.state == MissionState.FINISHED:
            # We do nothing. The mission is ended. Possibly keep spinning
            pass

        else:
            # No other states
            pass

    # -----------
    #  Helpers
    # -----------

    def confirm_arming(self, msg):
        if msg.data == "ARM":
            self.ready_to_fly = True


    def send_global_target(self, waypoint, label=""):
        """
        Non-blocking: just sends the target once via helper_func.
        """
        coords = waypoint[1]  # (lat, lon, alt)
        self.get_logger().info(f"Moving to target {label} => {coords}")
        self.mav.global_target(coords, wait_to_reach=False)

    def start_vision(self, type = 'bucket'):
        if type == 'bucket':
            msg = String()
            msg.data = "BUCKET"
            self.publisher_vision.publish(msg)
            self.get_logger().info("VISION GO")
        elif type == 'source':
            msg = String()
            msg.data = "SOURCE"
            self.publisher_vision.publish(msg)
            self.get_logger().info("VISION GO")

    def charge_opportunity(self):
        # This is the 10 second timer for battery checks
        # If near ground station and battery <10, do RTL, etc.
        drone_pos = self.mav.get_local_pos()
        # For example:
        if self.mav.is_near_waypoint(drone_pos, self.ground_station[1], 100) and (self.drone_battery <= 10):
            self.get_logger().warn("Battery low => returning to launch for charge.")
            self.mav.RTL()
            self.state = MissionState.FINISHED
            # If you want to do a real charge cycle, you can set self.drone_battery = 100 later
        # Otherwise do nothing

    def possible_movement(self, target_pos):
        # This code is essentially your same function 
        # but we skip the while loops
        try:
            next_distance = self.distances[(self.current_target[0], target_pos[0])]
        except KeyError:
            # fallback
            next_distance = func_distance(self.current_target[1], target_pos[1])

        distance_target_to_base = func_distance(target_pos[1], self.ground_station[1])
        # approximate battery usage
        battery_at_target = self.drone_battery - (next_distance / self.drone_travel_efficiency)
        autonomy_at_target = battery_at_target * self.drone_travel_efficiency
        return autonomy_at_target > distance_target_to_base

def main(args=None):
    rclpy.init(args=args)
    buckets = [
        ("bucket_1", [50.101222, -110.738856, 10]),
        ("bucket_2", [50.101796, -110.739031, 10]),
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
