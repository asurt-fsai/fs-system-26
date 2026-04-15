#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import numpy as np
from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import Header, ColorRGBA, Bool
from rclpy.duration import Duration
import sys
import os
from tf_helper.StatusPublisher import StatusPublisher

# Import the TFHelper for frame transformation
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Tf_helper'))
from tf_helper.TFHelper import TFHelper


# ================================
# Color Detection Helpers
# ================================
def is_blue(color):
    return color.b > 0.8 and color.r < 0.2 and color.g < 0.2

def is_yellow(color):
    return color.r > 0.8 and color.g > 0.8 and color.b < 0.2

def is_orange(color):
    return (0.9 <= color.r <= 1.0 and
            0.3 <= color.g <= 0.6 and
            0.0 <= color.b <= 0.2)


class ConeMapper(Node):
    def __init__(self):
        super().__init__('cone_mapper')

        # Parameters
        self.declare_parameter('alpha', 0.2)
        self.declare_parameter('association_threshold', 1.0)

        self.alpha = self.get_parameter('alpha').value
        self.threshold = self.get_parameter('association_threshold').value

        # Internal state
        self.cone_map = {}       # cone_id: (position, color)
        self.match_counts = {}   # cone_id: int
        self.next_id = 0
        self.loop_closure_handled = False  # Flag to only reset once

        # TF Helper
        self.tf_helper = TFHelper(self)

        # Status publisher
        self.status_pub = StatusPublisher("/status/conemap", self)
        self.status_pub.starting()
        self.status_pub.ready()
        self.create_timer(0.01, self.status_pub.running)

        # ROS I/O
        self.map_pub = self.create_publisher(MarkerArray, '/cone_map', 10)
        self.create_subscription(MarkerArray, '/perception/smornn/detected_markers', self.cone_callback, 10)
        self.create_timer(0.1, self.visualize_map)

        # Loop closure flag subscriber
        self.loopClosureTopic = '/loop_closure_flag'
        self.loopClosureSub = self.create_subscription(
            Bool,
            self.loopClosureTopic,
            self.loop_closure_callback,
            10
        )

    def loop_closure_callback(self, msg):
        if msg.data and not self.loop_closure_handled:
            self.get_logger().info("Loop closure triggered — resetting cone map.")
            self.cone_map.clear()
            self.match_counts.clear()
            self.next_id = 0
            self.loop_closure_handled = True  # Prevent future resets

    def cone_callback(self, msg):
        current_cones = []
        colors = []

        # Filter known cone colors
        for marker in msg.markers:
            if is_blue(marker.color):
                color = 'blue'
            elif is_yellow(marker.color):
                color = 'yellow'
            elif is_orange(marker.color):
                color = 'orange'
            else:
                color = 'black'

            x = marker.pose.position.x
            y = marker.pose.position.y
            current_cones.append(np.array([x, y]))
            colors.append(color)

        if not current_cones:
            return

        current_cones = np.array(current_cones)

        # Transform from 'velodyne' to 'map'
        transformed = self.tf_helper.transformArr2d(current_cones, 'velodyne', 'map')
        if transformed is None:
            self.get_logger().warn("Could not transform cones from 'velodyne' to 'map'")
            return

        current_cones = transformed

        # Initialize map on first detection
        if not self.cone_map:
            for i, pos in enumerate(current_cones):
                self.cone_map[self.next_id] = (pos, colors[i])
                self.match_counts[self.next_id] = 1
                self.next_id += 1
            return

        map_ids = list(self.cone_map.keys())
        map_cones = np.array([pos for pos, _ in self.cone_map.values()])
        distances = np.linalg.norm(current_cones[:, None, :] - map_cones[None, :, :], axis=2)

        used_current = set()
        used_map = set()

        # Associate cones using nearest-neighbor threshold
        while True:
            min_dist = np.min(distances)
            if min_dist > self.threshold:
                break
            i, j = np.unravel_index(np.argmin(distances), distances.shape)
            cone_id = map_ids[j]

            new_position = (
                self.alpha * current_cones[i] +
                (1 - self.alpha) * self.cone_map[cone_id][0]
            )
            original_color = self.cone_map[cone_id][1]
            self.cone_map[cone_id] = (new_position, original_color)
            self.match_counts[cone_id] += 1

            used_current.add(i)
            used_map.add(j)

            distances[i, :] = np.inf
            distances[:, j] = np.inf

        # Add unmatched cones
        for i in range(len(current_cones)):
            if i not in used_current:
                self.cone_map[self.next_id] = (current_cones[i], colors[i])
                self.match_counts[self.next_id] = 1
                self.next_id += 1

    def visualize_map(self):
        marker_array = MarkerArray()

        for cone_id, (position, color) in self.cone_map.items():
            if self.match_counts[cone_id] < 2:
                continue

            marker = Marker()
            marker.header = Header(frame_id='map')
            marker.ns = 'cones'
            marker.id = cone_id
            marker.type = Marker.SPHERE
            marker.action = Marker.ADD
            marker.pose.position.x = float(position[0])
            marker.pose.position.y = float(position[1])
            marker.pose.position.z = 0.0
            marker.pose.orientation.w = 1.0
            marker.scale.x = 0.4
            marker.scale.y = 0.4
            marker.scale.z = 0.6
            marker.lifetime = Duration(seconds=0).to_msg()

            if color == 'blue':
                marker.type = Marker.CUBE
                marker.color = ColorRGBA(r=0.0, g=0.0, b=1.0, a=1.0)
            elif color == 'yellow':
                marker.type = Marker.CYLINDER
                marker.color = ColorRGBA(r=1.0, g=1.0, b=0.0, a=1.0)
            elif color == 'orange':
                marker.type = Marker.SPHERE
                marker.color = ColorRGBA(r=1.0, g=0.5, b=0.0, a=1.0)
            else:
                marker.color = ColorRGBA(r=0.5, g=0.5, b=0.5, a=1.0)

            marker_array.markers.append(marker)

        self.map_pub.publish(marker_array)


def main(args=None):
    rclpy.init(args=args)
    node = ConeMapper()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
