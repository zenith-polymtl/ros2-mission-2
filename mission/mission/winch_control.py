#!/usr/bin/env python3
"""
Winch driver node, third revision:
* explicit STOP (92) + BRAKE (9A) before polling speed
* waits until speed byte <= speed_tol or hard timeout
* no multi‑thread logger conflict
"""

import time, threading
from queue import Queue, Empty
import can, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.qos import QoSProfile, ReliabilityPolicy


def fmt(b: bytes) -> str:        # 8‑byte to "AA BB …"
    return " ".join(f"{x:02X}" for x in b)


class Winch(Node):
    # ───────────────── init ──────────────────────────────────────
    def __init__(self):
        super().__init__("winch_v3")

        # ----- parameters you might tweak -------
        self.declare_parameter("device",      "/dev/ttyUSB0")
        self.declare_parameter("can_speed",    500_000)
        self.declare_parameter("baudrate",   2_000_000)
        self.declare_parameter("motor_id",              1)
        self.declare_parameter("move_time",           2.0)
        self.declare_parameter("stop_timeout",        10.0)
        self.declare_parameter("speed_tol",             3)
        # ----------------------------------------

        p     = self.get_parameter
        self.bus = can.interface.Bus(
            interface="seeedstudio",
            channel=p("device").value,
            bitrate=p("can_speed").value,
            baudrate=p("baudrate").value)

        self.cid    = p("motor_id").value
        self.run_t  = p("move_time").value
        self.stop_t = p("stop_timeout").value
        self.tol    = p("speed_tol").value

        self.log(f"Connected to CAN on {p('device').value}")

        # background CAN listener -----------------
        self.rx_q: Queue[can.Message] = Queue()
        self.last_prefix = b"\x00\x00"
        threading.Thread(target=self._rx_loop, daemon=True).start()

        # command subscription --------------------
        qos = QoSProfile(depth=5, reliability=ReliabilityPolicy.RELIABLE)
        self.busy = threading.Lock()
        self.create_subscription(String, "/go_winch", self._on_cmd, qos)

    # ───────────────── CAN helpers ──────────────
    def tx(self, data: bytes):
        self.last_prefix = data[:2]
        self.bus.send(can.Message(arbitration_id=self.cid,
                                  is_extended_id=False, data=data))
        self.log("TX " + fmt(data))

    def rx_match(self, tout=0.4):
        end = time.time() + tout
        while time.time() < end:
            try:
                m = self.rx_q.get(timeout=end - time.time())
                if m.data[:2] == self.last_prefix:
                    self.log("RX " + fmt(m.data))
                    return m
            except Empty:
                pass
        return None

    def _rx_loop(self):
        self.log("Listener started")
        while True:
            try:
                m = self.bus.recv(0.1)
                if m:
                    self.rx_q.put(m)
            except Exception as e:
                self.log(f"WARN: RX error {e}")

    # ───────────────── ROS callback ─────────────
    def _on_cmd(self, s: String):
        if s.data not in ("UP", "DOWN"):
            self.log(f"WARN: bad cmd {s.data}"); return
        if not self.busy.acquire(False):
            self.log("WARN: winch busy – ignored " + s.data); return
        threading.Thread(target=self._run, args=(s.data,), daemon=True).start()

    # ───────────────── motion sequence ──────────
    def _run(self, dir_: str):
        try:
            self.log(f"=== {dir_} START ===")
            rev = 0xC1 if dir_ == "UP" else 0x41

            # 1. preload dir (94)
            self.tx(bytes.fromhex(f"94 00 00 A0 {rev:02X} D0 07 00"))
            self.rx_match()

            # 2. brake open & run (91)
            self.tx(b"\x91\x00\x00\x00\x00\x00\x00\x00"); self.rx_match()
            time.sleep(self.run_t)

            # 3. STOP torque (92)  + wait 40 ms
            self.tx(b"\x92\x00\x00\x00\x00\x00\x00\x00")
            time.sleep(0.04)

            # 4. close brake (9A)
            self.tx(b"\x9A\x00\x00\x00\x00\x00\x00\x00")

            # 5. poll speed until <= tol
            deadline = time.time() + self.stop_t
            while True:
                time.sleep(0.12)
                self.tx(b"\xB4\x13\x00\x00\x00\x00\x00\x00")
                rep = self.rx_match(0.25)
                if not rep:
                    if time.time() > deadline:
                        self.log("WARN: no B4, abort"); return
                    continue
                speed = rep.data[4]
                if speed <= self.tol:
                    last4 = rep.data[-4:]
                    break
                self.log(f"speed 0x{speed:02X} > tol, wait")

            # 6. commit (95)
            self.log("pos bytes " + fmt(last4))
            self.tx(b"\x95" + last4 + b"\x32\x14\x00")
            if not self.rx_match(2.0):
                self.log("WARN: 95 not acked"); return

            self.log(f"=== {dir_} DONE ===")

        finally:
            self.busy.release()

    # ───────────────── logger helper ────────────
    def log(self, msg: str):
        self.get_logger().info(msg)


def main():
    rclpy.init()
    node = Winch()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node(); rclpy.shutdown()


if __name__ == "__main__":
    main()
