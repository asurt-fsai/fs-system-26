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
from visualization_msgs.msg import Marker, MarkerArray
import matplotlib.pyplot as plt



class LidarNode(Node):
    def __init__(self):
        super().__init__('lidar_processor')

        self.declare_parameters(
            namespace='',
            parameters=[
                ('x', [-20.0, 20.0]),
                ('y', [-20.0, 20.0]),
                ('z', [-2.0, 2.0]),


                ('car_x', [-1.0, 1.0]),
                ('car_y', [-0.5, 0.5]),


                ('ground_level', 0.2),
                ('point_num', 10),
                ('distance_threshold', 0.15),
                ('ransac_n', 3),
                ('num_iterations', 200),
                ('horizontal_plane_gradient', 0.8),

                ('voxel_size', 0.03),

                ('cluster_distance_threshold', 0.5),
                ('cluster_min_size', 5),
                ('cluster_max_size', 500)
            ]
        )

        self.filter = Filter(
            viewableBounds={"x": self.get_parameter('x').value, "y": self.get_parameter('y').value, "z": self.get_parameter('z').value},
            carDimensions={"x": self.get_parameter('car_x').value, "y": self.get_parameter('car_y').value},
            ground_level= self.get_parameter('ground_level').get_parameter_value().double_value,
            point_num= self.get_parameter('point_num').get_parameter_value().integer_value,
            distance_threshold= self.get_parameter('distance_threshold').get_parameter_value().double_value,
            ransac_n= self.get_parameter('ransac_n').get_parameter_value().integer_value,
            num_iterations= self.get_parameter('num_iterations').get_parameter_value().integer_value,
            horizontal_plane_gradient= self.get_parameter('horizontal_plane_gradient').get_parameter_value().double_value,
        )


        self.cone= ConeClassifier(
            radius=0.1, 
            height=0.3, 
            minPoints=1, 
            l2LossTh=0.1, 
            linLossPerc=0.2
        )

        self.processing_times = []


        
        self.sub = self.create_subscription(PointCloud2,'/velodyne_points', self.callback, 10)

        self.pub = self.create_publisher(PointCloud2, '/filtered_points', 10)
        self.cone_dist = self.create_publisher(PointCloud2, '/cone_distances', 10)
        self.marker_pub = self.create_publisher(MarkerArray, '/cluster_markers', 10)
        self.get_logger().info('Lidar Processor Node (ROS 2) has started.')




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

        pcd= self.filter.removeIntensity(pcd)
        
        initial_count = len(pcd.points)
        self.get_logger().info(f'1. Raw Points: {initial_count}')




        pcd = self.filter.filterViewableArea(pcd)
        after_view_count = len(pcd.points)
        self.get_logger().info(f'2. After Viewable Filter: {after_view_count}')

        pcd = self.filter.removeCar(pcd)
        after_car_count = len(pcd.points)
        self.get_logger().info(f'3. After Car Removal: {after_car_count}')


        pcd= self.filter.removeGround(pcd)
        after_ground_count = len(pcd.points)
        self.get_logger().info(f'4.Ground Removed: {after_ground_count}')

        


        

        
        voxel_size = self.get_parameter('voxel_size').get_parameter_value().double_value
        pcd = pcd.voxel_down_sample(voxel_size=voxel_size)
        after_voxel_count = len(pcd.points) 
        self.get_logger().info(f'5. After Voxel Filter: {after_voxel_count}')




        points = np.asarray(pcd.points)

        df = pd.DataFrame(points, columns=["X", "Y", "Z"])

        processor = clustering(df)
        
        cluster_distance_threshold = self.get_parameter('cluster_distance_threshold').get_parameter_value().double_value
        cluster_min_size = self.get_parameter('cluster_min_size').get_parameter_value().integer_value
        cluster_max_size = self.get_parameter('cluster_max_size').get_parameter_value().integer_value
        
        clusters = processor.euclidean_clustering(
            distance_threshold=cluster_distance_threshold, 
            cluster_parameters={"min_size": cluster_min_size, "max_size": cluster_max_size}
        )

        self.get_logger().info(f'Found {len(clusters)} clusters (objects)')


        redper= 100.0 * (1- after_ground_count/after_car_count)  if initial_count > 0 else 0
        


        if after_voxel_count > 0:
            points_out = np.asarray(pcd.points).astype(np.float32)
            msg_out = pc2.create_cloud_xyz32(msg.header, points_out)
            self.pub.publish(msg_out)
            self.get_logger().info('Published filtered cloud.')
        else:
            self.get_logger().error('ZERO points remaining after filter')

        marker_array = MarkerArray()

        safe_lifetime = 0.12


        cone_distances = []
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

            marker.lifetime = rclpy.duration.Duration(seconds=0, nanoseconds=int(safe_lifetime * 1e9)).to_msg()
            
            marker_array.markers.append(marker)
            # Calculate distance to cone center and store in list
            distance = np.linalg.norm(center)
            cone_distances.append((center, distance))



        if marker_array.markers:
            self.marker_pub.publish(marker_array)
            self.cone_dist.publish(cone_distances)

        self.get_logger().info(f'Published {len(marker_array.markers)} markers and cone distances.')
         
        end_time = time.perf_counter_ns()

        duration = end_time - start_time

        ns= duration / 1e9
        

        fps = 1.0 / ns if ns > 0 else 0.0

        self.get_logger().info(f'Total rocessing Time: {ns} s ({fps:.2f} Hz)')

        self.processing_times.append(ns)
        
        if len(self.processing_times) > 0:
            avg_time = sum(self.processing_times) / len(self.processing_times)
            min_time = min(self.processing_times)
            max_time = max(self.processing_times)
            fpsmax = 1.0 / min_time if min_time > 0 else 0.0
            fpsmin = 1.0 / max_time if max_time > 0 else 0.0
            
            fps = 1.0 / ns if ns > 0 else 0.0

            avg_fps = 1.0 / avg_time if avg_time > 0 else 0.0

            self.get_logger().info(
                f'Overall performance (Last {len(self.processing_times)} frames):\n'
                f'  Min:     {min_time:.4f}s ({fpsmax:.1f} Hz)\n'
                f'  Max:     {max_time:.4f}s ({fpsmin:.1f} Hz)\n'
                f'  Avg:     {avg_time:.4f}s ({avg_fps:.1f} Hz)'
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
