import json
import os
import subprocess
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String
from ament_index_python.packages import get_package_share_directory


_MISSION_JSON_MAP = {
    "acceleration": "acceleration",
    "skidpad": "skidpad",
    "autocross": "autocross",
    "trackdrive": "trackdrive",
    "static_a": "static_a",
    "staticb": "static_b",
    "static_b": "static_b",
    "autodemo": "autonomousdemo",
    "auto_demo": "autonomousdemo",
}


class MissionManagerNode(Node):
    def __init__(self):
        super().__init__("mission_manager_node")
        self._start_sub = self.create_subscription(
            String, "/mission_manager/start", self._on_start, 10
        )
        self._stop_sub = self.create_subscription(
            Bool, "/mission_manager/stop", self._on_stop, 10
        )
        self._modules_pub = self.create_publisher(String, "/mission_manager/modules", 10)
        self._status_pub = self.create_publisher(String, "/mission_manager/status", 10)
        self._register_pub = self.create_publisher(String, "/module_manager/register", 10)
        self._command_pub = self.create_publisher(String, "/module_manager/command", 10)

        self._mission_process = None
        self._active_mission = None

    def _on_start(self, msg: String) -> None:
        mission_name = msg.data.strip()
        if not mission_name:
            return
        normalized = mission_name.lower().replace(" ", "_")
        json_key = _MISSION_JSON_MAP.get(normalized)
        if json_key is None:
            self._publish_status(f"start_failed: unknown mission {mission_name}")
            return

        payload = self._load_mission_modules(json_key)
        if payload is None:
            self._publish_status(f"start_failed: missing json {json_key}")
            return

        self._publish_modules(payload)
        self._send_module_manager_command("launch")
        self._start_mission_node(normalized)

        self._active_mission = normalized
        self._publish_status(f"started:{normalized}")

    def _on_stop(self, msg: Bool) -> None:
        if not msg.data:
            return
        self._publish_modules({"modules": []})
        self._send_module_manager_command("shutdown")
        self._stop_mission_node()
        self._active_mission = None
        self._publish_status("stopped")

    def _load_mission_modules(self, json_key: str):
        try:
            share_dir = get_package_share_directory("supervisor_pkg")
        except Exception:
            return None

        json_path = os.path.join(share_dir, "json", f"{json_key}.json")
        if not os.path.exists(json_path):
            return None

        with open(json_path, "r") as handle:
            return json.load(handle)

    def _publish_modules(self, payload: dict) -> None:
        msg = String()
        msg.data = json.dumps(payload)
        self._modules_pub.publish(msg)
        self._register_pub.publish(msg)

    def _send_module_manager_command(self, command: str) -> None:
        msg = String()
        msg.data = command
        self._command_pub.publish(msg)

    def _start_mission_node(self, normalized: str) -> None:
        self._stop_mission_node()
        heartbeat_topic = f"/status/mission_{normalized}"
        self._mission_process = subprocess.Popen(
            [
                "ros2",
                "run",
                "supervisor_pkg",
                "mission_node",
                "--ros-args",
                "-p",
                f"mission:={normalized}",
                "-p",
                f"heartbeat_topic:={heartbeat_topic}",
            ]
        )

    def _stop_mission_node(self) -> None:
        if self._mission_process is None:
            return
        self._mission_process.terminate()
        self._mission_process = None

    def _publish_status(self, text: str) -> None:
        msg = String()
        msg.data = text
        self._status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = MissionManagerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
