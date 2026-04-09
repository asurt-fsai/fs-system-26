import re

with open('src/SLAM_Camera/src/cone_mapping/cone_mapping/cone_mapping_node.py', 'r') as f:
    code = f.read()

# 1. Imports
code = code.replace(
    'from tf2_ros import Buffer, TransformListener\nfrom std_msgs.msg import Bool',
    'from tf2_ros import Buffer, TransformListener\nfrom tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster\nfrom std_msgs.msg import Bool'
)

# 2. Add MapMaintenance fix
code = code.replace(
    'if dist < MappingConstants.MERGE_DISTANCE_THRESHOLD and current.cone_type == confirmed[j].cone_type:',
    'if dist < MappingConstants.MERGE_DISTANCE_THRESHOLD and current.assigned_type == confirmed[j].assigned_type:'
)
code = code.replace(
    'merged_type = current.cone_type',
    'merged_type = current.assigned_type'
)

# 3. Add CoordinateTransformer fixes
target_1 = '''    def transform_and_gate(self, landmarks_sensor, pose_map_base):
        """
        Transform cone detections from sensor frame to map frame and apply gating.
        
        Args:
            landmarks_sensor: List of Landmark objects in sensor frame
            pose_map_base: geometry_msgs.msg.Pose (vehicle pose in map)
            
        Returns:
            List of dicts: [{'position': np.array([x,y]), 'type': int, 'distance': float, 'probability': float}, ...]
        """
        if self.T_base_sensor is None:
            self.logger.warn("Static transform not available")
            return []
        
        # Get T_map_base
        T_map_base = self._pose_to_matrix(pose_map_base)
        
        # Complete transformation: T_map_sensor = T_map_base · T_base_sensor
        T_map_sensor = T_map_base @ self.T_base_sensor'''

replacement_1 = '''    def get_T_map_sensor(self, pose_map_base, global_frame_id):
        # Base representation of the vehicle path
        T_camera_init_camera = self._pose_to_matrix(pose_map_base)
        
        if global_frame_id == 'camera_init':
            # LeGO-LOAM mapping
            # Convert velodyne (X-fwd, Y-left, Z-up) to camera (Z-fwd, X-left, Y-up)
            T_camera_velodyne = np.array([
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [1, 0, 0, 0],
                [0, 0, 0, 1]
            ], dtype=np.float64)
            
            # Convert camera_init (Z-fwd, X-left, Y-up) to standard map (X-fwd, Y-left, Z-up)
            T_map_camera_init = np.array([
                [0, 0, 1, 0],
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1]
            ], dtype=np.float64)
            
            return T_map_camera_init @ T_camera_init_camera @ T_camera_velodyne
        else:
            if self.T_base_sensor is None:
                return None
            return T_camera_init_camera @ self.T_base_sensor

    def get_T_map_base(self, pose_map_base, global_frame_id):
        T_camera_init_camera = self._pose_to_matrix(pose_map_base)
        if global_frame_id == 'camera_init':
            T_map_camera_init = np.array([
                [0, 0, 1, 0],
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1]
            ], dtype=np.float64)
            return T_map_camera_init @ T_camera_init_camera
        else:
            return T_camera_init_camera

    def transform_and_gate(self, landmarks_sensor, pose_map_base, global_frame_id):
        """
        Transform cone detections from sensor frame to map frame and apply gating.
        
        Args:
            landmarks_sensor: List of Landmark objects in sensor frame
            pose_map_base: geometry_msgs.msg.Pose (vehicle pose in map)
            global_frame_id: string of the frame the odometry arrived in
            
        Returns:
            List of dicts: [{'position': np.array([x,y]), 'type': int, 'distance': float, 'probability': float}, ...]
        """
        T_map_sensor = self.get_T_map_sensor(pose_map_base, global_frame_id)
        if T_map_sensor is None:
            self.logger.warn("Static transform not available")
            return []'''
code = code.replace(target_1, replacement_1)


# 4. Add __init__ broadcaster
code = code.replace(
    'self.tf_listener = TransformListener(self.tf_buffer, self)\n        \n        perception_topic = self.get_parameter(\'perception_topic\').value',
    'self.tf_listener = TransformListener(self.tf_buffer, self)\n        self.static_broadcaster = StaticTransformBroadcaster(self)\n        self.publish_loam_map_tf()\n        \n        perception_topic = self.get_parameter(\'perception_topic\').value'
)

# 5. Add broadcast def
code = code.replace(
    '        if self.transformer.T_base_sensor is None:\n            self.transformer.lookup_static_transform()',
    '        if self.transformer.T_base_sensor is None:\n            self.transformer.lookup_static_transform()\n            \n    def publish_loam_map_tf(self):\n        """Broadcasts static TF from standard \'map\' to \'camera_init\'"""\n        t = TransformStamped()\n        t.header.stamp = self.get_clock().now().to_msg()\n        t.header.frame_id = \'map\'\n        t.child_frame_id = \'camera_init\'\n        t.transform.translation.x = 0.0\n        t.transform.translation.y = 0.0\n        t.transform.translation.z = 0.0\n        t.transform.rotation.x = 0.5\n        t.transform.rotation.y = 0.5\n        t.transform.rotation.z = 0.5\n        t.transform.rotation.w = 0.5\n        self.static_broadcaster.sendTransform(t)'
)

# 6. Change calls to transform_and_gate and T_map_base
code = code.replace(
    '        detections = self.transformer.transform_and_gate(\n            landmarks_msg.landmarks,\n            odom_msg.pose.pose\n        )',
    '        detections = self.transformer.transform_and_gate(\n            landmarks_msg.landmarks,\n            odom_msg.pose.pose,\n            self.global_frame_id\n        )'
)

code = code.replace(
    'T_map_base = self.transformer._pose_to_matrix(odom_msg.pose.pose)',
    'T_map_base = self.transformer.get_T_map_base(odom_msg.pose.pose, self.global_frame_id)'
)

# 7. RViz map fix
code = code.replace(
    'msg.header.frame_id = self.global_frame_id  # Dynamic global frame!',
    'msg.header.frame_id = \'map\'  # Publish in standard map! (Z-up)'
)

# 8. Trajectory callback
code = code.replace(
    'Tpose_new = self.transformer._pose_to_matrix(best_pose.pose)',
    'Tpose_new = self.transformer.get_T_map_base(best_pose.pose, best_pose.header.frame_id)'
)

with open('src/SLAM_Camera/src/cone_mapping/cone_mapping/cone_mapping_node.py', 'w') as f:
    f.write(code)

print("Done string replacement")
