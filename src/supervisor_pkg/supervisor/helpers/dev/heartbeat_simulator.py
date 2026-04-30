import argparse
import itertools
import logging
import time

import rclpy
from rclpy.node import Node

from asurt_msgs.msg import NodeStatus


DEFAULT_NODES = [
    "supervisor",
    "mission_manager",
    "module_manager",
    "camera_node",
    "lidar_node",
]


class HeartbeatSimulator(Node):
    def __init__(self, node_names, period, drop_node=None, drop_after=0.0, drop_duration=0.0):
        super().__init__("heartbeat_simulator")
        self._publisher = self.create_publisher(NodeStatus, "/module_heartbeat", 10)
        self._node_names = node_names
        self._node_cycle = itertools.cycle(self._node_names)
        self._status_cycle = itertools.cycle([
            NodeStatus.STARTING,
            NodeStatus.READY,
            NodeStatus.RUNNING,
        ])
        self._start_time = time.time()
        self._drop_node = drop_node
        self._drop_after = max(0.0, drop_after)
        self._drop_duration = max(0.0, drop_duration)

        self._timer = self.create_timer(period, self._tick)
        self.get_logger().info(f"Heartbeat simulator running for: {', '.join(node_names)}")
        if self._drop_node:
            self.get_logger().info(
                f"Drop plan enabled: node={self._drop_node} after={self._drop_after}s duration={self._drop_duration}s"
            )

    def _in_drop_window(self) -> bool:
        if not self._drop_node:
            return False
        elapsed = time.time() - self._start_time
        return self._drop_after <= elapsed < (self._drop_after + self._drop_duration)

    def _tick(self):
        node_name = next(self._node_cycle)
        if self._in_drop_window() and node_name == self._drop_node:
            self.get_logger().info(f"dropping heartbeat for {node_name}")
            return

        message = NodeStatus()
        message.header.stamp = self.get_clock().now().to_msg()
        message.message = node_name
        message.status = next(self._status_cycle)
        self._publisher.publish(message)
        self.get_logger().info(f"published {message.message} -> {message.status}")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    parser = argparse.ArgumentParser(description="Publish fake module heartbeats to /module_heartbeat")
    parser.add_argument("--nodes", nargs="*", default=DEFAULT_NODES, help="Node names to simulate")
    parser.add_argument("--period", type=float, default=1.0, help="Seconds between heartbeats")
    parser.add_argument("--drop-node", default="", help="Node name to pause heartbeats for")
    parser.add_argument("--drop-after", type=float, default=0.0, help="When to start dropping (seconds)")
    parser.add_argument("--drop-duration", type=float, default=0.0, help="How long to drop (seconds)")
    args = parser.parse_args()

    rclpy.init()
    node = HeartbeatSimulator(
        args.nodes,
        args.period,
        drop_node=args.drop_node if args.drop_node else None,
        drop_after=args.drop_after,
        drop_duration=args.drop_duration,
    )
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()