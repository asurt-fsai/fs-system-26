#!/usr/bin/env python3
"""
Initialization of Pure Pursuit node for vehicle control
"""
import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from nav_msgs.msg import Path
from ackermann_msgs.msg import AckermannDriveStamped
from visualization_msgs.msg import Marker
from simple_pure_pursuit.simple_purepursuitcontroller import SimplePurePursuit
from tf_helper.StatusPublisher import StatusPublisher

class SimplePurePursuitNode(Node):
    """Node for simple pure pursuit control"""

    def __init__(self):
        super().__init__("simple_pure_pursuit_node")
        # Enable debug logs
        self.get_logger().set_level(rclpy.logging.LoggingSeverity.DEBUG)

        self.status = StatusPublisher("/status/simple_pure_pursuit", self)
        self.status.starting()
        self.status_timer = self.create_timer(0.1, self.status.running)
        self.status.ready()
        # Track last time a Path message arrived
        self.last_path_time = self.get_clock().now()
        # Timeout for auto‐stop if no new Path arrives
        self.timeout = Duration(seconds=0.5)

        # Declare & read parameters
        self.declare_parameter("planning.waypoints_clean", "/planner/path")
        self.declare_parameter("control.cmd", "/control/ackermann_cmd")
        self.declare_parameter("control.marker_viz", "/visualization/marker")
        path_topic = self.get_parameter("planning.waypoints_clean").value
        cmd_topic  = self.get_parameter("control.cmd").value
        viz_topic  = self.get_parameter("control.marker_viz").value

        # Set up controller, publishers, subscriber
        self.controller  = SimplePurePursuit(self)
        self.steeringPub = self.create_publisher(AckermannDriveStamped, cmd_topic, 10)
        self.markerPub   = self.create_publisher(Marker, viz_topic, 10)
        self.create_subscription(Path, path_topic, self._path_callback, 10)

        # Watchdog timer at 10 Hz
        self.create_timer(0.1, self._watchdog_callback)

    def _path_callback(self, msg: Path) -> None:
        """Handle incoming Path messages"""
        self.get_logger().debug(f"Path callback: received {len(msg.poses)} poses")
        self.last_path_time = self.get_clock().now()

        cmd = AckermannDriveStamped()
        cmd.drive.steering_angle = 0.0

        # Case 1: empty path → stop immediately
        if not msg.poses:
            self.get_logger().info("Empty path → publishing stop")
            cmd.drive.speed = 0.0
            self.steeringPub.publish(cmd)
            return

        # Case 2: normal pure pursuit
        self.controller.add(msg)
        delta, ind = self.controller.purepursuitSteercontrol()
        cmd.drive.steering_angle = delta
        cmd.drive.speed = 1.5
        self.steeringPub.publish(cmd)

        # Publish visualization marker
        viz = Marker()
        viz.header.frame_id = self.controller.frameId
        viz.ns = "pure_pursuit"
        viz.id = 0
        viz.type = Marker.SPHERE
        viz.action = Marker.ADD
        viz.pose.position.x = self.controller.xList[ind]
        viz.pose.position.y = self.controller.yList[ind]
        viz.pose.position.z = 0.0
        viz.pose.orientation.w = 1.0
        viz.scale.x = viz.scale.y = viz.scale.z = 0.5
        viz.color.r = 1.0
        viz.color.a = 1.0
        self.markerPub.publish(viz)
	
    def _watchdog_callback(self) -> None:
        """If no Path msg for > timeout, send zero‐speed command."""
        self.status_timer = self.create_timer(0.1, self.status.running)
        now = self.get_clock().now()
        delta = now - self.last_path_time
        seconds = delta.nanoseconds * 1e-9
        self.get_logger().debug(f"Watchdog: {seconds:.3f}s since last Path")
        if delta > self.timeout:
            self.get_logger().info("Timeout exceeded → publishing stop")
            stop = AckermannDriveStamped()
            stop.drive.steering_angle = 0.0
            stop.drive.speed = 0.0
            self.steeringPub.publish(stop)

def main():
    rclpy.init()
    node = SimplePurePursuitNode()
    
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
