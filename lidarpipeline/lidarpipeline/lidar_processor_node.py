import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import sensor_msgs_py.point_cloud2 as pc2
import open3d as o3d
import numpy as np
from .Filter import Filter
from .EuclideanClustering import clustering
import pandas as pd
from .ConeClassifier import ConeClassifier
from .LUTBoundingBoxFilter import LUTBoundingBoxFilter
from visualization_msgs.msg import Marker, MarkerArray


class LidarNode(Node):
    def __init__(self):
        super().__init__('lidar_processor')

        self.declare_parameters(
            namespace='',
            parameters=[
                # Algorithm selection: 'box' (original) or 'lut'
                ('filter_algorithm', 'lut'),

                # Box filter / shared spatial bounds
                ('x', [-20.0, 20.0]),
                ('y', [-20.0, 20.0]),
                ('z', [-2.0, 2.0]),

                # Car exclusion zone
                ('car_x', [-1.0, 1.0]),
                ('car_y', [-0.5, 0.5]),

                # Ground removal (RANSAC)
                ('ground_level', 0.2),
                ('point_num', 10),
                ('distance_threshold', 0.15),
                ('ransac_n', 3),
                ('num_iterations', 200),
                ('horizontal_plane_gradient', 0.8),

                # Voxel downsampling
                ('voxel_size', 0.03),

                # Euclidean clustering
                ('cluster_distance_threshold', 0.5),
                ('cluster_min_size', 5),
                ('cluster_max_size', 500),

                # LUT filter — spatial bounds
                ('lut_max_distance', 20.0),
                ('lut_z', [-2.0, 2.0]),

                # LUT filter — cone gating
                ('lut_max_cone_lateral', 2.5),
                ('lut_max_track_half_width', 2.0),

                # LUT filter — cone classifier used for corridor building
                # (independent from the final-classification classifier)
                ('lut_cone_radius', 0.1),
                ('lut_cone_height', 0.3),
                ('lut_min_cone_points', 5),
                ('lut_l2_loss_threshold', 0.05),
                ('lut_lin_loss_percentage', 0.1),

                # LUT building
                ('lut_resolution', 0.1),
                ('lut_ema_alpha', 0.2),
                ('lut_max_width_change', 0.2),
                ('lut_tolerance_multiplier', 5.0),

                # LUT corridor filtering margins
                ('lut_filter_margin', 1.5),
                ('lut_filter_x_margin_before', 1.0),
                ('lut_filter_x_margin_after', 2.0),
            ]
        )

        # ── Shared Filter (box ROI + car/ground removal) ─────────────────
        self.filter = Filter(
            viewableBounds={
                "x": self.get_parameter('x').value,
                "y": self.get_parameter('y').value,
                "z": self.get_parameter('z').value,
            },
            carDimensions={
                "x": self.get_parameter('car_x').value,
                "y": self.get_parameter('car_y').value,
            },
            ground_level=self.get_parameter('ground_level').get_parameter_value().double_value,
            point_num=self.get_parameter('point_num').get_parameter_value().integer_value,
            distance_threshold=self.get_parameter('distance_threshold').get_parameter_value().double_value,
            ransac_n=self.get_parameter('ransac_n').get_parameter_value().integer_value,
            num_iterations=self.get_parameter('num_iterations').get_parameter_value().integer_value,
            horizontal_plane_gradient=self.get_parameter('horizontal_plane_gradient').get_parameter_value().double_value,
        )

        # ── Cone classifier for LUT corridor building ─────────────────────
        # Created FIRST and passed into LUTBoundingBoxFilter so it owns a
        # completely independent instance from self.cone below.
        lut_cone_classifier = ConeClassifier(
            radius=self.get_parameter('lut_cone_radius').get_parameter_value().double_value,
            height=self.get_parameter('lut_cone_height').get_parameter_value().double_value,
            minPoints=self.get_parameter('lut_min_cone_points').get_parameter_value().integer_value,
            l2LossTh=self.get_parameter('lut_l2_loss_threshold').get_parameter_value().double_value,
            linLossPerc=self.get_parameter('lut_lin_loss_percentage').get_parameter_value().double_value,
        )

        lut_z = self.get_parameter('lut_z').value

        # ── LUT Bounding Box Filter ───────────────────────────────────────
        self.lut_filter = LUTBoundingBoxFilter(
            max_distance=self.get_parameter('lut_max_distance').get_parameter_value().double_value,
            z_min=lut_z[0],
            z_max=lut_z[1],
            ground_level=self.get_parameter('ground_level').get_parameter_value().double_value,
            point_num=self.get_parameter('point_num').get_parameter_value().integer_value,
            distance_threshold=self.get_parameter('distance_threshold').get_parameter_value().double_value,
            ransac_n=self.get_parameter('ransac_n').get_parameter_value().integer_value,
            num_iterations=self.get_parameter('num_iterations').get_parameter_value().integer_value,
            horizontal_plane_gradient=self.get_parameter('horizontal_plane_gradient').get_parameter_value().double_value,
            max_cone_lateral=self.get_parameter('lut_max_cone_lateral').get_parameter_value().double_value,
            max_track_half_width=self.get_parameter('lut_max_track_half_width').get_parameter_value().double_value,
            cone_classifier=lut_cone_classifier,
            lut_resolution=self.get_parameter('lut_resolution').get_parameter_value().double_value,
            lut_ema_alpha=self.get_parameter('lut_ema_alpha').get_parameter_value().double_value,
            lut_max_width_change=self.get_parameter('lut_max_width_change').get_parameter_value().double_value,
            lut_tolerance_multiplier=self.get_parameter('lut_tolerance_multiplier').get_parameter_value().double_value,
            lut_filter_margin=self.get_parameter('lut_filter_margin').get_parameter_value().double_value,
            lut_filter_x_margin_before=self.get_parameter('lut_filter_x_margin_before').get_parameter_value().double_value,
            lut_filter_x_margin_after=self.get_parameter('lut_filter_x_margin_after').get_parameter_value().double_value,
        )

        # ── Final cone classifier (for marker publishing) ─────────────────
        # Separate instance — different parameters, no singleton conflict.
        self.cone = ConeClassifier(
            radius=0.1,
            height=0.3,
            minPoints=1,
            l2LossTh=0.1,
            linLossPerc=0.2,
        )

        self.processing_times = []

        self.sub = self.create_subscription(
            PointCloud2, '/velodyne_points', self.callback, 10
        )
        self.pub = self.create_publisher(PointCloud2, '/filtered_points', 10)
        self.marker_pub = self.create_publisher(MarkerArray, '/cluster_markers', 10)
        self.get_logger().info('Lidar Processor Node (ROS 2) has started.')

    # ------------------------------------------------------------------ #
    # Callback
    # ------------------------------------------------------------------ #

    def callback(self, msg):
        self.get_logger().info('--- New Packet Received ---')
        start_time = time.perf_counter_ns()

        gen = pc2.read_points(msg, field_names=("x", "y", "z"), skip_nans=True)
        points_list = [[p[0], p[1], p[2]] for p in gen]
        points = np.array(points_list, dtype=np.float64)

        if points.size == 0:
            self.get_logger().warn("Empty cloud received")
            return

        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        pcd = self.filter.removeIntensity(pcd)

        initial_count = len(pcd.points)
        self.get_logger().info(f'1. Raw Points: {initial_count}')

        filter_algorithm = (
            self.get_parameter('filter_algorithm')
            .get_parameter_value()
            .string_value
        )

        # ── ROI step ─────────────────────────────────────────────────────
        if filter_algorithm == 'lut':
            # Apply LUT corridor filter (falls back to basic distance/z
            # bounds on early frames before the LUT is populated).
            pcd = self.lut_filter.filterWithLUT(pcd)
            self.get_logger().info(
                f'2. After LUT Filter: {len(pcd.points)} pts '
                f'(LUT size: {len(self.lut_filter.lut_centerline)})'
            )
        else:
            # Original axis-aligned box filter
            pcd = self.filter.filterViewableArea(pcd)
            self.get_logger().info(f'2. After Viewable Filter: {len(pcd.points)}')

        # ── Car removal ───────────────────────────────────────────────────
        pcd = self.filter.removeCar(pcd)
        after_car_count = len(pcd.points)
        self.get_logger().info(f'3. After Car Removal: {after_car_count}')

        # ── Ground removal ────────────────────────────────────────────────
        pcd = self.filter.removeGround(pcd)
        after_ground_count = len(pcd.points)
        self.get_logger().info(f'4. Ground Removed: {after_ground_count}')

        # ── Voxel downsampling ────────────────────────────────────────────
        voxel_size = self.get_parameter('voxel_size').get_parameter_value().double_value
        pcd = pcd.voxel_down_sample(voxel_size=voxel_size)
        after_voxel_count = len(pcd.points)
        self.get_logger().info(f'5. After Voxel Filter: {after_voxel_count}')

        # ── Publish filtered cloud ────────────────────────────────────────
        if after_voxel_count > 0:
            points_out = np.asarray(pcd.points).astype(np.float32)
            msg_out = pc2.create_cloud_xyz32(msg.header, points_out)
            self.pub.publish(msg_out)
            self.get_logger().info('Published filtered cloud.')
        else:
            self.get_logger().error('ZERO points remaining after filter')
            return

        # ── Euclidean clustering ──────────────────────────────────────────
        points_arr = np.asarray(pcd.points)
        df = pd.DataFrame(points_arr, columns=["X", "Y", "Z"])
        processor = clustering(df)

        cluster_distance_threshold = self.get_parameter('cluster_distance_threshold').get_parameter_value().double_value
        cluster_min_size = self.get_parameter('cluster_min_size').get_parameter_value().integer_value
        cluster_max_size = self.get_parameter('cluster_max_size').get_parameter_value().integer_value

        clusters = processor.euclidean_clustering(
            distance_threshold=cluster_distance_threshold,
            cluster_parameters={"min_size": cluster_min_size, "max_size": cluster_max_size},
        )
        self.get_logger().info(f'Found {len(clusters)} clusters')

        # ── LUT update from current clusters ─────────────────────────────
        # After clustering, feed the detected cones back into the LUT so
        # the corridor improves frame by frame.
        if filter_algorithm == 'lut' and len(clusters) > 0:
            cluster_arrays = [
                np.array(list(idx_set), dtype=int)
                for idx_set in clusters.values()
            ]
            cones = self.lut_filter.detectCones(pcd, cluster_arrays)
            if cones:
                self.lut_filter.buildLUT(cones)
                self.get_logger().info(
                    f'LUT updated: {len(cones)} cones detected, '
                    f'LUT size={len(self.lut_filter.lut_centerline)}'
                )

        # ── Cone classification and marker publishing ─────────────────────
        marker_array = MarkerArray()
        safe_lifetime = 0.12

        for cluster_id, indices in clusters.items():
            cluster_np = df.iloc[list(indices)][["X", "Y", "Z"]].values.astype(np.float64)
            classified_cones, _ = self.cone.isCone(cluster_np)

            if not classified_cones[0]:
                continue

            cluster_pcd = o3d.geometry.PointCloud()
            cluster_pcd.points = o3d.utility.Vector3dVector(cluster_np)
            aabb = cluster_pcd.get_axis_aligned_bounding_box()
            center = aabb.get_center()

            marker = Marker()
            marker.header = msg.header
            marker.ns = "cone_detection"
            marker.id = int(cluster_id)
            marker.type = Marker.CUBE
            marker.action = Marker.ADD

            marker.pose.position.x = float(center[0])
            marker.pose.position.y = float(center[1])
            marker.pose.position.z = float(center[2])

            marker.scale.x, marker.scale.y, marker.scale.z = 0.3, 0.3, 0.3
            marker.color.r, marker.color.g, marker.color.b, marker.color.a = 1.0, 1.0, 0.0, 1.0
            marker.lifetime = rclpy.duration.Duration(
                seconds=0, nanoseconds=int(safe_lifetime * 1e9)
            ).to_msg()

            marker_array.markers.append(marker)

        if marker_array.markers:
            self.marker_pub.publish(marker_array)

        self.get_logger().info(
            f'Published {len(marker_array.markers)} cone markers.'
        )

        # ── Timing ───────────────────────────────────────────────────────
        end_time = time.perf_counter_ns()
        ns = (end_time - start_time) / 1e9
        fps = 1.0 / ns if ns > 0 else 0.0
        self.get_logger().info(f'Total processing time: {ns:.4f} s ({fps:.2f} Hz)')

        self.processing_times.append(ns)

        if self.processing_times:
            avg_time = sum(self.processing_times) / len(self.processing_times)
            min_time = min(self.processing_times)
            max_time = max(self.processing_times)
            self.get_logger().info(
                f'Overall performance (Last {len(self.processing_times)} frames):\n'
                f'  Min: {min_time:.4f}s ({1.0/min_time:.1f} Hz)\n'
                f'  Max: {max_time:.4f}s ({1.0/max_time:.1f} Hz)\n'
                f'  Avg: {avg_time:.4f}s ({1.0/avg_time:.1f} Hz)'
            )


def main(args=None):
    rclpy.init(args=args)
    node = LidarNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
