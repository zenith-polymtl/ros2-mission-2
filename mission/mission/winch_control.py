
import time
import threading
from queue import Queue, Empty

import can
import rclpy
from rclpy.node         import Node
from std_msgs.msg       import String
from rclpy.qos          import QoSProfile, ReliabilityPolicy


def fmt(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


class Winch(Node):
    # -------------------- init / infrastructure --------------------
    def __init__(self):
        super().__init__("can_winch_simple")

        # ── parameters ────────────────────────────────────────────
        self.declare_parameter("device",      "/dev/ttyUSB0")
        self.declare_parameter("can_speed",    500_000)
        self.declare_parameter("baudrate",   2_000_000)
        self.declare_parameter("motor_id",              1)
        self.declare_parameter("move_time",           2.0)

        p = self.get_parameter
        self.bus       = can.interface.Bus(
                            interface="seeedstudio",
                            channel  =p("device").value,
                            bitrate  =p("can_speed").value,
                            baudrate =p("baudrate").value)
        self.id        = p("motor_id").value
        self.move_time = p("move_time").value

        self.get_logger().info("Connected to CAN on %s" %
                               p("device").value)

        # ── background CAN listener ───────────────────────────────
        self.rx_queue: Queue[can.Message] = Queue()
        self.last_cmd_prefix: bytes = b"\x00\x00"

        threading.Thread(target=self._rx_loop,
                         name="can_rx", daemon=True).start()

        # ── command subscription ─────────────────────────────────
        qos = QoSProfile(depth=5, reliability=ReliabilityPolicy.RELIABLE)
        self.busy = threading.Lock()          # one motion at a time
        self.create_subscription(String, "/go_winch",
                                 self._on_cmd, qos)

    # --------------------- CAN helpers -----------------------------
    def _send(self, data: bytes):
        """send 8‑byte frame, remember first two bytes"""
        assert len(data) == 8
        self.last_cmd_prefix = data[:2]
        self.bus.send(can.Message(arbitration_id=self.id,
                                  is_extended_id=False,
                                  data=data))
        self.get_logger().info("TX %s" % fmt(data))

    def _wait_reply(self, timeout=0.4) -> can.Message | None:
        """return first frame whose first 2 bytes match last cmd"""
        t_end = time.time() + timeout
        while time.time() < t_end:
            try:
                msg = self.rx_queue.get(timeout=t_end - time.time())
                if msg.data[:2] == self.last_cmd_prefix:
                    self.get_logger().info("RX %s" % fmt(msg.data))
                    return msg
            except Empty:
                pass
        return None

    def _rx_loop(self):
        self.get_logger().info("Listening for CAN frames …")
        while True:
            try:
                msg = self.bus.recv(0.1)
                if msg:
                    self.rx_queue.put(msg)
            except Exception as e:
                self.get_logger().error(f"RX thread error: {e}")

    # --------------------- ROS callback ---------------------------
    def _on_cmd(self, msg: String):
        if msg.data not in ("UP", "DOWN"):
            self.get_logger().warn("Expected 'UP' or 'DOWN', got %s"
                                   % msg.data)
            return
        if not self.busy.acquire(blocking=False):
            self.get_logger().warn("Winch busy – ignoring %s" % msg.data)
            return
        threading.Thread(target=self._run_sequence,
                         args=(msg.data,),
                         daemon=True).start()

    # --------------------- motion sequence ------------------------
    def _run_sequence(self, direction: str):
        log = self.get_logger().info
        try:
            rev = 0xC1 if direction == "UP"   else 0x41
            dir_str = "UP" if direction == "UP" else "DOWN"
            log(f"=== {dir_str} SEQUENCE START ===")

            # 1) preload direction, brake engaged
            self._send(bytes.fromhex(f"94 00 00 A0 {rev:02X} D0 07 00"))
            self._wait_reply()          # optional – ignore if None

            # 2) open brake / start motion
            self._send(b"\x91\x00\x00\x00\x00\x00\x00\x00")
            self._wait_reply()          # many drives send nothing here

            # 3) let the winch run
            log(f"running for {self.move_time}s …")
            time.sleep(self.move_time)

            # 4) close brake, make speed go to 0
            self._send(b"\x91\x00\x00\x00\x00\x00\x00\x00")

            # 5) wait until B4 reports speed = 0  (≤ 3 s or abort)
            for _ in range(30):                 # 30 × 0.1 s  ≈ 3 s max
                time.sleep(0.10)
                self._send(b"\xB4\x13\x00\x00\x00\x00\x00\x00")
                reply = self._wait_reply(0.2)
                if not reply:
                    continue                    # nothing came back, try again
                speed = reply.data[4]
                if speed == 0:
                    break                       # brake engaged, shaft stopped
                self.get_logger().debug(f"speed = 0x{speed:02X}, waiting…")
            else:
                self.get_logger().error("shaft never stopped – aborting")
                return

            last4 = reply.data[-4:]
            self.get_logger().info("pos bytes = %s" % fmt(last4))

            # 6) commit absolute position
            final = b"\x95" + last4 + b"\x32\x14\x00"
            self._send(final)
            if not self._wait_reply(2.0):
                self.get_logger().error("95 still not acknowledged – controller fault")
                return

            log(f"=== {dir_str} DONE ===")

        finally:
            self.busy.release()


def main():
    rclpy.init()
    node = Winch()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()