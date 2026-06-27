from std_msgs.msg import String


class ModuleManagerClient:
    """ROS client for ModuleManagerNode commands."""

    def __init__(self, node):
        self._node = node
        self._command_pub = node.create_publisher(String, "/module_manager/command", 10)

    def launch_all(self) -> None:
        self._publish_command("launch")

    def shutdown_all(self) -> None:
        self._publish_command("shutdown")

    def restart_module(self, pkg: str) -> None:
        if not pkg:
            return
        self._publish_command(f"restart:{pkg}")

    def _publish_command(self, command: str) -> None:
        msg = String()
        msg.data = command
        self._command_pub.publish(msg)
