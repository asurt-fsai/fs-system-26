#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import numpy as np
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point, PoseStamped
from std_msgs.msg import Header, ColorRGBA
from builtin_interfaces.msg import Duration
import csv
import os
import math
import time

def create_color(r, g, b, a=1.0):
    c = ColorRGBA()
    c.r = r
    c.g = g
    c.b = b
    c.a = a
    return c

class GeneratedConesPublisher(Node):
    def __init__(self):
        super().__init__('generated_cones_publisher')

        self.pub = self.create_publisher(MarkerArray, '/generated_cones', 10)
        self.pose_pub = self.create_publisher(PoseStamped, '/car_pose', 10)

        # Setup CSV to save data to Desktop
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.csv_file = open(os.path.join(desktop_path, "generated_cones_data.csv"), 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['timestamp', 'car_x', 'car_y', 'cone_id', 'cone_color', 'cone_x', 'cone_y'])

        self.timer = self.create_timer(0.1, self.timer_callback)

        self.start_time = time.time()
        self.t = 0.0  # time in seconds for simulation

        # Parameters for path & cones
        self.car_speed = 1.5  # m/s approx
        self.distance_between_cones_along_path = 2.0
        self.horizontal_cone_offset = 1.5  # Half of 3m gap (left/right offset from path center)
        self.noise_std = 0.1  # noise in meters for cone position

        self.cones_per_side = 20

        # Pre-generate a non-straight path (a simple sinusoidal path)
        self.path_length = self.distance_between_cones_along_path * self.cones_per_side
        self.path_points = self.generate_path()

    def generate_path(self):
        # Generate (x,y) along path: x increases, y = sin(x/5)*2 for curvature
        xs = np.linspace(0, self.path_length, self.cones_per_side)
        ys = 2.0 * np.sin(xs / 5.0)
        return np.stack([xs, ys], axis=1)

    def timer_callback(self):
        # Update simulated time
        self.t += 0.1  # 10 Hz

        # Calculate car position on path by distance = speed * time
        dist = self.car_speed * self.t

        # Clamp dist to path length
        if dist > self.path_length:
            dist = self.path_length

        # Find closest index on path
        idx = int(dist / self.distance_between_cones_along_path)
        if idx >= len(self.path_points) - 1:
            idx = len(self.path_points) - 2

        p0 = self.path_points[idx]
        p1 = self.path_points[idx + 1]

        # Interpolate between p0 and p1
        local_ratio = (dist - idx * self.distance_between_cones_along_path) / self.distance_between_cones_along_path
        car_pos = (1 - local_ratio) * p0 + local_ratio * p1

        # Compute heading angle of path segment (yaw)
        delta = p1 - p0
        yaw = math.atan2(delta[1], delta[0])

        # Publish car pose as PoseStamped
        car_pose = PoseStamped()
        car_pose.header.stamp = self.get_clock().now().to_msg()
        car_pose.header.frame_id = 'map'
        car_pose.pose.position.x = float(car_pos[0])
        car_pose.pose.position.y = float(car_pos[1])
        car_pose.pose.position.z = 0.0
        # For simplicity, no rotation quaternion calculation (can be improved)
        car_pose.pose.orientation.w = 1.0
        self.pose_pub.publish(car_pose)

        # Generate cones positions relative to path centerline with noise
        marker_array = MarkerArray()
        cone_id = 0
        timestamp = time.time()

        for i, base_pos in enumerate(self.path_points):
            # For each cone index, place left and right cones

            # Direction vector along path segment for this cone
            if i == len(self.path_points) - 1:
                direction = self.path_points[i] - self.path_points[i-1]
            else:
                direction = self.path_points[i+1] - self.path_points[i]
            direction /= np.linalg.norm(direction)

            # Perpendicular vector to direction (left side)
            left_offset = np.array([-direction[1], direction[0]])
            right_offset = -left_offset

            # Left cone position (yellow)
            left_cone_pos = base_pos + left_offset * self.horizontal_cone_offset
            # Add noise
            left_cone_pos += np.random.normal(0, self.noise_std, 2)

            m_left = Marker()
            m_left.header.frame_id = 'map'
            m_left.header.stamp = self.get_clock().now().to_msg()
            m_left.ns = 'cones'
            m_left.id = cone_id
            m_left.type = Marker.CYLINDER
            m_left.action = Marker.ADD
            m_left.pose.position.x = float(left_cone_pos[0])
            m_left.pose.position.y = float(left_cone_pos[1])
            m_left.pose.position.z = 0.0
            m_left.scale.x = 0.3
            m_left.scale.y = 0.3
            m_left.scale.z = 0.5
            m_left.color = create_color(1.0, 1.0, 0.0, 1.0)  # Yellow
            m_left.lifetime = Duration(sec=1)

            marker_array.markers.append(m_left)
            self.csv_writer.writerow([timestamp, car_pos[0], car_pos[1], cone_id, 'yellow', left_cone_pos[0], left_cone_pos[1]])
            cone_id += 1

            # Right cone position (blue)
            right_cone_pos = base_pos + right_offset * self.horizontal_cone_offset
            right_cone_pos += np.random.normal(0, self.noise_std, 2)

            m_right = Marker()
            m_right.header.frame_id = 'map'
            m_right.header.stamp = self.get_clock().now().to_msg()
            m_right.ns = 'cones'
            m_right.id = cone_id
            m_right.type = Marker.CYLINDER
            m_right.action = Marker.ADD
            m_right.pose.position.x = float(right_cone_pos[0])
            m_right.pose.position.y = float(right_cone_pos[1])
            m_right.pose.position.z = 0.0
            m_right.scale.x = 0.3
            m_right.scale.y = 0.3
            m_right.scale.z = 0.5
            m_right.color = create_color(0.0, 0.0, 1.0, 1.0)  # Blue
            m_right.lifetime = Duration(sec=1)

            marker_array.markers.append(m_right)
            self.csv_writer.writerow([timestamp, car_pos[0], car_pos[1], cone_id, 'blue', right_cone_pos[0], right_cone_pos[1]])
            cone_id += 1

        self.pub.publish(marker_array)
        self.csv_file.flush()

def main(args=None):
    rclpy.init(args=args)
    node = GeneratedConesPublisher()
    rclpy.spin(node)
    node.csv_file.close()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
