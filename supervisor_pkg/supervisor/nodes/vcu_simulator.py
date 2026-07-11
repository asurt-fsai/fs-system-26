"""
VCU / ros_can simulator for testing without the real vehicle.

Mimics the real C++ ros_can node:
  - Publishes /ros_can/state (CanState) with current as_state + ami_state
  - Publishes /ros_can/state_str (String) human-readable state name
  - Publishes /ros_can/twist (TwistWithCovarianceStamped) with current velocity
  - Subscribes to /state_machine/driving_flag, /ros_can/mission_completed, /cmd
  - Service /vcu_next_state  → step AS state forward  (AS_OFF→AS_READY→AS_DRIVING→AS_FINISHED)
  - Service /vcu_prev_state  → step AS state backward
  - Service /ros_can/ebs     → force AS_EBS immediately

Auto-transitions (VCU-side decisions the sim reproduces):
  - AS_READY → AS_DRIVING  : rising edge of /state_machine/driving_flag
  - AS_DRIVING → AS_FINISHED : mission_completed==True AND current_vel < 1.0 m/s

Usage:
  ros2 run supervisor_pkg vcu_simulator --ros-args -p ami_state:=18
  ros2 service call /vcu_next_state std_srvs/srv/Trigger {}
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, String
from eufs_msgs.msg import CanState, WheelSpeedsStamped
from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import TwistWithCovarianceStamped
from std_srvs.srv import Trigger


_AS_STATE_NAMES = {0: "AS_OFF", 1: "AS_READY", 2: "AS_DRIVING", 3: "AS_EBS", 4: "AS_FINISHED"}

# Forward path skips EBS (3); EBS is a separate branch entered only via /ros_can/ebs service.
_NEXT_STATE = {0: 1, 1: 2, 2: 4, 3: 3, 4: 4}
_PREV_STATE = {0: 0, 1: 0, 2: 1, 3: 2, 4: 2}

# Wheel-speed threshold for FINISHED transition (mirrors GUI: all wheels < 10 rpm).
# sim wheel_speed = current_vel * 10, so threshold in m/s = 1.0.
_FINISHED_VEL_THRESHOLD = 1.0


class VCUSimulator(Node):
    def __init__(self):
        super().__init__("vcu_simulator")

        self.declare_parameter("ami_state", 18)   # 18=Static A, 19=Static B, 15=AutoDemo
        self.declare_parameter("publish_hz", 10.0)

        self._ami_state = self.get_parameter("ami_state").get_parameter_value().integer_value
        hz = self.get_parameter("publish_hz").get_parameter_value().double_value

        self._as_state = 0   # starts AS_OFF
        self._driving_flag = False      # True only while AS_DRIVING and flag received
        self._mission_completed = False  # True only after received while AS_DRIVING
        self._cmd_vel = 0.0
        self._cmd_steer = 0.0
        self._current_vel = 0.0  # simulated actual velocity (ramps toward cmd_vel)

        # Publishers
        self._state_pub = self.create_publisher(CanState, "/ros_can/state", 10)
        self._state_str_pub = self.create_publisher(String, "/ros_can/state_str", 10)
        self._twist_pub = self.create_publisher(TwistWithCovarianceStamped, "/ros_can/twist", 10)
        self._wheel_speeds_pub = self.create_publisher(WheelSpeedsStamped, "/ros_can/wheel_speeds", 10)
        self._vcu_vel_pub = self.create_publisher(Float32, "/vcu/vel", 10)
        self._vcu_steer_pub = self.create_publisher(Float32, "/vcu/steer", 10)

        # Subscriptions — mirror what ros_can C++ reads
        self.create_subscription(Bool, "/state_machine/driving_flag", self._on_driving_flag, 10)
        self.create_subscription(Bool, "/ros_can/mission_completed", self._on_mission_completed, 10)
        self.create_subscription(AckermannDriveStamped, "/cmd", self._on_cmd, 10)

        # Services
        self.create_service(Trigger, "/vcu_next_state", self._next_state)
        self.create_service(Trigger, "/vcu_prev_state", self._prev_state)
        self.create_service(Trigger, "/ros_can/ebs", self._ebs)

        # Periodic publish
        self.create_timer(1.0 / hz, self._publish)

        self.get_logger().info(
            f"VCU Simulator started: ami_state={self._ami_state} ({hz}Hz)"
        )
        self.get_logger().info("  ros2 service call /vcu_next_state std_srvs/srv/Trigger {}")

    # ------------------------------------------------------------------
    # Subscriptions
    # ------------------------------------------------------------------

    def _on_driving_flag(self, msg: Bool) -> None:
        rising_edge = msg.data and not self._driving_flag

        # Rising edge while AS_READY → auto-advance to AS_DRIVING (VCU Go decision)
        if rising_edge and self._as_state == 1:
            self._as_state = 2
            self.get_logger().info("[VCU] driving_flag rising edge -> AS_DRIVING")

        # Flag latches true only while in AS_DRIVING; ignored/cleared in all other states
        self._driving_flag = msg.data and (self._as_state == 2)
        self.get_logger().info(f"[VCU] driving_flag={self._driving_flag}")

    def _on_mission_completed(self, msg: Bool) -> None:
        # Ignored outside AS_DRIVING (mirrors getMissionStatus: only flips while driving)
        if self._as_state == 2:
            self._mission_completed = msg.data
            self.get_logger().info(f"[VCU] mission_completed={msg.data}")

    def _on_cmd(self, msg: AckermannDriveStamped) -> None:
        # Accept commands only when AS_DRIVING AND driving_flag active
        if self._as_state == 2 and self._driving_flag:
            self._cmd_vel = msg.drive.speed
            self._cmd_steer = msg.drive.steering_angle
        else:
            self._cmd_vel = 0.0
            self._cmd_steer = 0.0

    # ------------------------------------------------------------------
    # Services
    # ------------------------------------------------------------------

    def _next_state(self, _request, response: Trigger.Response) -> Trigger.Response:
        old = self._as_state
        self._as_state = _NEXT_STATE[self._as_state]
        self.get_logger().info(
            f"[VCU] state: {_AS_STATE_NAMES[old]} -> {_AS_STATE_NAMES[self._as_state]}"
        )
        response.success = True
        response.message = _AS_STATE_NAMES[self._as_state]
        return response

    def _prev_state(self, _request, response: Trigger.Response) -> Trigger.Response:
        old = self._as_state
        self._as_state = _PREV_STATE[self._as_state]
        self.get_logger().info(
            f"[VCU] state: {_AS_STATE_NAMES[old]} -> {_AS_STATE_NAMES[self._as_state]}"
        )
        response.success = True
        response.message = _AS_STATE_NAMES[self._as_state]
        return response

    def _ebs(self, _request, response: Trigger.Response) -> Trigger.Response:
        self._as_state = 3  # AS_EBS
        self._driving_flag = False
        self.get_logger().info("[VCU] EBS triggered -> AS_EBS")
        response.success = True
        response.message = "AS_EBS"
        return response

    # ------------------------------------------------------------------
    # Periodic publish
    # ------------------------------------------------------------------

    def _publish(self) -> None:
        now = self.get_clock().now().to_msg()

        # Simulate velocity: ramp current_vel toward cmd_vel (simple first-order model)
        # Rate = 10Hz, so dt ≈ 0.1s. Ramp at 2 m/s² so step = 0.2 m/s per tick.
        step = 0.2
        if self._current_vel < self._cmd_vel:
            self._current_vel = min(self._current_vel + step, self._cmd_vel)
        elif self._current_vel > self._cmd_vel:
            self._current_vel = max(self._current_vel - step, self._cmd_vel)

        # AS_DRIVING → AS_FINISHED auto-transition:
        # Two conditions must both be met: mission_completed flag AND velocity below threshold.
        if (
            self._as_state == 2
            and self._mission_completed
            and self._current_vel < _FINISHED_VEL_THRESHOLD
        ):
            self._as_state = 4
            self._driving_flag = False
            self.get_logger().info("[VCU] mission completed + vel low -> AS_FINISHED")

        # /ros_can/state
        state_msg = CanState()
        state_msg.as_state = self._as_state
        state_msg.ami_state = self._ami_state
        self._state_pub.publish(state_msg)

        # /ros_can/state_str
        str_msg = String()
        str_msg.data = _AS_STATE_NAMES[self._as_state]
        self._state_str_pub.publish(str_msg)

        # /ros_can/twist  (used by Supervisor for velocity feedback)
        twist_msg = TwistWithCovarianceStamped()
        twist_msg.header.stamp = now
        twist_msg.twist.twist.linear.x = self._current_vel
        self._twist_pub.publish(twist_msg)

        # /ros_can/wheel_speeds  (used by GUI state machine for FINISHED/EBS transitions)
        # All four wheels get the same speed in RPM-like units.
        # GUI checks > 10 for EBS and < 10 for FINISHED, so we scale vel directly.
        wheel_speed = self._current_vel * 10.0   # crude: 1 m/s → 10 speed units
        ws_msg = WheelSpeedsStamped()
        ws_msg.header.stamp = now
        ws_msg.speeds.lf_speed = wheel_speed
        ws_msg.speeds.rf_speed = wheel_speed
        ws_msg.speeds.lb_speed = wheel_speed
        ws_msg.speeds.rb_speed = wheel_speed
        ws_msg.speeds.steering = self._cmd_steer
        self._wheel_speeds_pub.publish(ws_msg)

        # VCU wheel commands (for monitoring)
        vel_msg = Float32()
        vel_msg.data = float(self._cmd_vel)
        self._vcu_vel_pub.publish(vel_msg)

        steer_msg = Float32()
        steer_msg.data = float(self._cmd_steer)
        self._vcu_steer_pub.publish(steer_msg)


def main(args=None):
    rclpy.init(args=args)
    node = VCUSimulator()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
