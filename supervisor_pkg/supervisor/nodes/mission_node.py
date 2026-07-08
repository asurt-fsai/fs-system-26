import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float64, Int16, String
from std_srvs.srv import Trigger
from ackermann_msgs.msg import AckermannDriveStamped

from eufs_msgs.msg import CanState
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.AccelerationMission import AccelerationMission
from supervisor.helpers.Missions.SkidpadMission import SkidpadMission
from supervisor.helpers.Missions.AutocrossMission import AutocrossMission
from supervisor.helpers.Missions.TrackdriveMission import TrackdriveMission
from supervisor.helpers.Missions.StaticAMission import StaticAMission
from supervisor.helpers.Missions.StaticBMission import StaticBMission
from supervisor.helpers.Missions.AutoDemoMission import AutoDemoMission


_MISSION_MAP = {
    "acceleration": AccelerationMission,
    "skidpad": SkidpadMission,
    "autocross": AutocrossMission,
    "trackdrive": TrackdriveMission,
    "static_a": StaticAMission,
    "staticb": StaticBMission,
    "static_b": StaticBMission,
    "autodemo": AutoDemoMission,
    "auto_demo": AutoDemoMission,
}


class MissionComms:
    def __init__(self, node: Node):
        self._node = node
        self._cmd_pub = node.create_publisher(AckermannDriveStamped, "/cmd", 10)
        self._mission_flag_pub = node.create_publisher(Bool, "/ros_can/mission_completed", 10)
        self._mission_state_pub = node.create_publisher(String, "/static_mission/state", 10)
        self._ebs_client = node.create_client(Trigger, "/ros_can/ebs")

    def publishDriveCommand(self, cmd_msg: AckermannDriveStamped) -> None:
        self._cmd_pub.publish(cmd_msg)

    def publishMissionFlag(self, flag: bool) -> None:
        msg = Bool()
        msg.data = flag
        self._mission_flag_pub.publish(msg)

    def publishMissionState(self, state: str) -> None:
        msg = String()
        msg.data = state
        self._mission_state_pub.publish(msg)

    def triggerEBS(self) -> None:
        if not self._ebs_client.wait_for_service(timeout_sec=1.0):
            self._node.get_logger().error("EBS service not available")
            return
        req = Trigger.Request()
        self._ebs_client.call_async(req)


class MissionReporter:
    def __init__(self, node: Node):
        self._node = node
        self._result_pub = node.create_publisher(String, "/mission_manager/result", 10)

    def onMissionFinished(self, result) -> None:
        payload = {"status": "FINISHED", "result": str(result)}
        msg = String()
        msg.data = json.dumps(payload)
        self._result_pub.publish(msg)

    def onMissionFailed(self, reason: str) -> None:
        payload = {"status": "FAILED", "reason": str(reason)}
        msg = String()
        msg.data = json.dumps(payload)
        self._result_pub.publish(msg)


class MissionNode(Node):
    def __init__(self):
        super().__init__("mission_node")

        self.declare_parameter("mission", "")
        self.declare_parameter("heartbeat_topic", "")
        mission_name = self.get_parameter("mission").get_parameter_value().string_value
        heartbeat_topic = self.get_parameter("heartbeat_topic").get_parameter_value().string_value

        normalized = mission_name.strip().lower().replace(" ", "_")
        mission_cls = _MISSION_MAP.get(normalized)
        if mission_cls is None:
            self.get_logger().error(f"Unknown mission: {mission_name}")
            raise RuntimeError(f"Unknown mission: {mission_name}")

        self._reporter = MissionReporter(self)
        self._comms = MissionComms(self)
        self._mission = mission_cls(self._comms, self._reporter)

        # Start in IDLE — mission will transition to RUNNING once
        # required external conditions are met (driving flag and CAN state).
        self._mission.missionStatus = MissionStatus.IDLE

        # Startup gating flags
        self._driving_flag_received = False
        self._driving_flag = False
        self._can_state_ok = False
        self._required_as_state = 2

        self._setup_heartbeat(heartbeat_topic, normalized)
        self._setup_subscriptions()

        # Timer for mission tick
        self._tick_timer = self.create_timer(0.05, self._tick)

        # Periodically check whether start conditions are satisfied
        self._start_check_timer = self.create_timer(0.5, self._attempt_start)

        self.get_logger().info(f"Mission node started (waiting to start mission): {mission_name}")

    def _setup_heartbeat(self, heartbeat_topic: str, mission_name: str) -> None:
        topic = heartbeat_topic or f"/status/mission_{mission_name}"
        try:
            from tf_helper.StatusPublisher import StatusPublisher
        except Exception:
            StatusPublisher = None

        if StatusPublisher is None:
            self.get_logger().warning("StatusPublisher unavailable; mission heartbeat disabled")
            return

        self._status_pub = StatusPublisher(topic, self)
        self._status_pub.starting()
        self._status_timer = self.create_timer(0.5, self._status_pub.running)

    def _setup_subscriptions(self) -> None:
        self.create_subscription(Bool, "/perception/cone_detection", self._on_cone, 10)
        self.create_subscription(Bool, "/slam/loop_closure", self._on_loop_closure, 10)
        self.create_subscription(Float64, "/slam/distance", self._on_distance, 10)
        self.create_subscription(Int16, "/slam/loop_closure_count", self._on_loop_closure_count, 10)
        # External coordination required before mission RUNNING
        # Driving flag from Supervisor (/ros_can/driving_flag) — authoritative
        self.create_subscription(Bool, "/state_machine/driving_flag", self._on_driving_flag, 10)
        # CAN state published by ros_can
        self.create_subscription(CanState, "/ros_can/state", self._on_can_state, 10)

    def _on_cone(self, msg: Bool) -> None:
        if hasattr(self._mission, "onConeDetected"):
            self._mission.onConeDetected(msg.data)

    def _on_loop_closure(self, msg: Bool) -> None:
        if hasattr(self._mission, "onLoopClosure"):
            self._mission.onLoopClosure(msg.data)

    def _on_distance(self, msg: Float64) -> None:
        if hasattr(self._mission, "onDistance"):
            self._mission.onDistance(msg.data)

    def _on_loop_closure_count(self, msg: Int16) -> None:
        if hasattr(self._mission, "onLoopClosureCount"):
            self._mission.onLoopClosureCount(msg.data)

    def _tick(self) -> None:
        if hasattr(self._mission, "tick"):
            self._mission.tick()

    def _on_driving_flag(self, msg: Bool) -> None:
        self.get_logger().info(f"[FLOW] _on_driving_flag entered: data={msg.data}")
        self._driving_flag_received = True
        self._driving_flag = bool(msg.data)

    def _on_can_state(self, msg: CanState) -> None:
        self.get_logger().info(f"[FLOW] _on_can_state entered: as_state={msg.as_state}")
        try:
            as_state = getattr(msg, "as_state", None)
            if as_state is not None and int(as_state) == int(self._required_as_state):
                self._can_state_ok = True
            else:
                self._can_state_ok = False
        except Exception:
            self._can_state_ok = False

    def _attempt_start(self) -> None:
        self.get_logger().info(f"[FLOW] _attempt_start entered: driving_flag={self._driving_flag} can_state_ok={self._can_state_ok} status={self._mission.missionStatus}")
        # If already running, nothing to do
        if self._mission.missionStatus == MissionStatus.RUNNING:
            return

        # Require driving flag to be published and True
        if not (self._driving_flag_received and self._driving_flag):
            return

        # Require CAN AS state to match required value
        if not self._can_state_ok:
            return

        # All conditions satisfied -> start mission
        self.get_logger().info("Start conditions satisfied — setting mission RUNNING")
        self._mission.missionStatus = MissionStatus.RUNNING
        try:
            # stop this check timer (no longer needed)
            self._start_check_timer.cancel()
        except Exception:
            pass


def main(args=None):
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    rclpy.init(args=args)
    node = MissionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()