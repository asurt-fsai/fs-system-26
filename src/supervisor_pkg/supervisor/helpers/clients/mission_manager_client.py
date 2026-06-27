from std_msgs.msg import Bool, String


class MissionManagerClient:
    """ROS client for MissionManagerNode commands."""

    def __init__(self, node):
        self._node = node
        self._start_pub = node.create_publisher(String, "/mission_manager/start", 10)
        self._stop_pub = node.create_publisher(Bool, "/mission_manager/stop", 10)

    def start_mission(self, mission_type) -> None:
        if mission_type is None:
            return
        if hasattr(mission_type, "name"):
            mission_name = mission_type.name
        else:
            mission_name = str(mission_type)
        msg = String()
        msg.data = mission_name
        self._start_pub.publish(msg)

    def stop_mission(self) -> None:
        msg = Bool()
        msg.data = True
        self._stop_pub.publish(msg)
