#!/usr/bin/env python3
"""
ROS2 node to drive a CAN‑bus winch (UP/DOWN).
Stops cleanly before changing direction and waits until
the controller reports speed ≤ speed_tol before sending 95.
"""

import time, threading
from queue import Queue, Empty

import can
import rclpy
from rclpy.node   import Node
from std_msgs.msg import String
from rclpy.qos    import QoSProfile, ReliabilityPolicy


def fmt(b: bytes) -> str: return " ".join(f"{x:02X}" for x in b)


class SimpleWinch(Node):
    # ───────────────── init ───────────────────────────────────────
    def __init__(self):
        super().__init__("simple_winch")

        # -------- parameters you might tweak ----------
        self.declare_parameter("device",      "/dev/ttyUSB0")
        self.declare_parameter("can_speed",    500_000)
        self.declare_parameter("baudrate",   2_000_000)
        self.declare_parameter("motor_id",              1)
        self.declare_parameter("move_time",           2.0)   # run time
        self.declare_parameter("stop_timeout",        8.0)   # max wait
        self.declare_parameter("speed_tol",             3)   # ≤ count/s
        # -----------------------------------------------------------

        p          = self.get_parameter
        self.bus   = can.interface.Bus(
                        interface="seeedstudio",
                        channel  =p("device").value,
                        bitrate  =p("can_speed").value,
                        baudrate =p("baudrate").value)
        self.cid   = p("motor_id").value
        self.run_t = p("move_time").value
        self.stop_t= p("stop_timeout").value
        self.tol   = p("speed_tol").value

        self.log("Connected to CAN on %s" % p("device").value)

        # CAN listener ------------------------------------------------
        self.rx_q: Queue[can.Message] = Queue()
        self.last_prefix: bytes = b"\x00\x00"
        threading.Thread(target=self._rx_loop,
                         name="can_rx", daemon=True).start()

        # command subscription ---------------------------------------
        qos = QoSProfile(depth=10,
                         reliability=ReliabilityPolicy.RELIABLE)
        self.busy = threading.Lock()
        self.create_subscription(String, "/go_winch",
                                 self._on_cmd, qos)

    # ───────────────── CAN helpers ─────────────────────────────────
    def tx(self, data: bytes):
        self.last_prefix = data[:2]
        self.bus.send(can.Message(arbitration_id=self.cid,
                                  is_extended_id=False, data=data))
        self.log("TX " + fmt(data))

    def rx_match(self, tout=0.4):
        end = time.time() + tout
        while time.time() < end:
            try:
                msg = self.rx_q.get(timeout=end - time.time())
                if msg.data[:2] == self.last_prefix:
                    self.log("RX " + fmt(msg.data))
                    return msg
            except Empty:
                pass
        return None

    def _rx_loop(self):
        self.log("Listening …")
        while True:
            try:
                m = self.bus.recv(0.1)
                if m:
                    self.rx_q.put(m)
            except Exception as e:
                self.log(f"RX thread error: {e}", warn=True)

    # ───────────────── ROS callback ────────────────────────────────
    def _on_cmd(self, s: String):
        if s.data not in ("UP", "DOWN"):
            self.log(f"Bad cmd: {s.data}", warn=True); return
        if not self.busy.acquire(False):
            self.log("Winch busy, ignoring " + s.data, warn=True); return
        threading.Thread(target=self._run, args=(s.data,), daemon=True).start()

    # ───────────────── motion sequence ─────────────────────────────
    def _run(self, dir_: str):
        self.log(f"=== {dir_} START ===")
        try:
            rev = 0xC1 if dir_ == "UP" else 0x41

            # 1) preload direction
            self.tx(bytes.fromhex(f"94 00 00 A0 {rev:02X} D0 07 00"))
            self.rx_match()

            # 2) open brake / move
            self.tx(b"\x91\x00\x00\x00\x00\x00\x00\x00"); self.rx_match()
            time.sleep(self.run_t)

            # 3) close brake
            self.tx(b"\x91\x00\x00\x00\x00\x00\x00\x00")

            # 4) wait until speed byte ≤ tol   (or timeout)
            deadline = time.time() + self.stop_t
            while True:
                time.sleep(0.12)
                self.tx(b"\xB4\x13\x00\x00\x00\x00\x00\x00")
                rep = self.rx_match(0.25)
                if not rep:
                    if time.time() > deadline:
                        self.log("no B4 reply, abort", warn=True); return
                    continue
                speed = rep.data[4]
                if speed <= self.tol:
                    break
                self.log(f"speed=0x{speed:02X} (> {self.tol}), wait…")

            last4 = rep.data[-4:]
            self.log("pos bytes " + fmt(last4))

            # 5) commit
            self.tx(b"\x95" + last4 + b"\x32\x14\x00")
            if not self.rx_match(2.0):
                self.log("95 not acked – fault", warn=True); return

            self.log(f"=== {dir_} DONE ===")

        finally:
            self.busy.release()

    # ───────────────── misc ────────────────────────────────────────
    def log(self, msg, warn=False):
        (self.get_logger().warning if warn else self.get_logger().info)(msg)


def main():
    rclpy.init()
    node = SimpleWinch()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node(); rclpy.shutdown()


if __name__ == "__main__":
    main()
