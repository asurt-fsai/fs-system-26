import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from supervisor.helpers.Module.Module import Module
from supervisor.helpers.Module.ModuleManager import ModuleManager
from supervisor.helpers.Module.LocalLauncher import LocalLauncher


class ModuleManagerNode(Node):
    def __init__(self):
        super().__init__("module_manager_node")
        self._manager = ModuleManager()
        self._launcher = LocalLauncher()

        self._register_sub = self.create_subscription(
            String, "/module_manager/register", self._on_register, 10
        )
        self._command_sub = self.create_subscription(
            String, "/module_manager/command", self._on_command, 10
        )
        self._status_pub = self.create_publisher(String, "/module_manager/status", 10)

    def _on_register(self, msg: String) -> None:
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self._publish_status(f"register_failed: invalid json ({exc})")
            return

        entries = payload.get("modules", []) if isinstance(payload, dict) else []
        modules = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if "pkg" not in entry or "launch_file" not in entry:
                continue
            module = Module(
                entry["pkg"],
                entry["launch_file"],
                None,
                self._launcher,
                entry.get("heartbeat_timeout", 5.0),
                entry.get("startup_timeout"),
                entry.get("heartbeats_topic") or entry.get("heartbeat_topic"),
            )
            modules.append(module)

        self._manager.registerModules(modules)
        self._publish_status(f"registered:{len(modules)}")

    def _on_command(self, msg: String) -> None:
        command = msg.data.strip()
        if not command:
            return

        if command == "launch":
            failed = self._manager.launchAll()
            if failed:
                failed_names = [m.pkg for m in failed]
                self._publish_status(f"launch_failed:{failed_names}")
            else:
                self._publish_status("launch_ok")
            return

        if command == "shutdown":
            failed = self._manager.shutdownAll()
            if failed:
                failed_names = [m.pkg for m in failed]
                self._publish_status(f"shutdown_failed:{failed_names}")
            else:
                self._publish_status("shutdown_ok")
            return

        if command.startswith("restart:"):
            pkg = command.split(":", 1)[1]
            module = self._manager.getModule(pkg)
            if module is None:
                self._publish_status(f"restart_failed:{pkg}")
                return
            module.restart()
            self._publish_status(f"restart_ok:{pkg}")
            return

    def _publish_status(self, text: str) -> None:
        msg = String()
        msg.data = text
        self._status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ModuleManagerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
