#!/usr/bin/env python3
"""
ROS2 Local Cone Mapping Node
Formula Student Driverless - SLAM Subsystem

Implements a local, landmark-based cone filtering pipeline that:
- Subscribes to local cone detections in the sensor frame.
- Tracks and filters landmarks in the local frame using Kalman filtering.
- Removes global map maintenance, coordinate transformations, and global data associations.
"""

import rclpy
from rclpy.node import Node
import numpy as np
import math
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

# ROS2 imports
from geometry_msgs.msg import Point
from std_msgs.msg import Header
from visualization_msgs.msg import Marker, MarkerArray

# Custom message types
try:
    from cone_mapping.msg import Landmark, LandmarkArray
except ImportError:
    class Landmark:
        def __init__(self):
            self.position = Point()
            self.type = 0
            self.identifier = 0
            self.probability = 0.0

    class LandmarkArray:
        def __init__(self):
            self.header = Header()
            self.landmarks = []

# Try to import the perception message type from asurt_msgs if available
try:
    from asurt_msgs.msg import Landmark as AsurtLandmark, LandmarkArray as AsurtLandmarkArray
except ImportError:
    AsurtLandmark = None
    AsurtLandmarkArray = None

# Color mapping helper
class ConeType:
    BLUE = 0
    YELLOW = 1
    ORANGE = 2
    UNKNOWN = 3

def type_to_color_string(cone_type):
    mapping = {
        ConeType.BLUE: "blue",
        ConeType.YELLOW: "yellow",
        ConeType.ORANGE: "orange",
        ConeType.UNKNOWN: "unknown"
    }
    return mapping.get(cone_type, "unknown")


class LocalKalmanLandmark:
    """
    Represents a single locally tracked cone landmark with Kalman filter state estimation.
    State vector: x = [x, y]^T (2D position in the sensor/local frame)
    """
    def __init__(self, identifier, position, cone_type, initial_covariance, current_time):
        self.id = identifier
        self.state = np.array(position[:2], dtype=np.float64)  # 2D position [x, y]
        self.covariance = np.eye(2, dtype=np.float64) * initial_covariance
        self.cone_type = cone_type
        self.observation_count = 1
        self.last_seen_time = current_time

    def predict(self, Q):
        """Kalman prediction step (identity motion model in local frame)."""
        self.covariance += Q

    def update(self, measurement, R):
        """Kalman update step."""
        H = np.eye(2)
        S = self.covariance + R
        try:
            S_inv = np.linalg.inv(S)
            K = self.covariance @ S_inv
            innovation = measurement[:2] - self.state
            
            # State update
            new_state = self.state + K @ innovation
            # Covariance update
            new_covariance = (np.eye(2) - K) @ self.covariance
            
            if np.isfinite(new_state).all() and np.isfinite(new_covariance).all():
                self.state = new_state
                self.covariance = new_covariance
                self.observation_count += 1
                return True
            return False
        except np.linalg.LinAlgError:
            return False


class ConeMappingNodeLocally(Node):
    """
    ROS2 Node for local cone mapping and filtering.
    """
    def __init__(self):
        super().__init__('cone_mapping_node_locally')

        # Declare parameters
        self.declare_parameter('max_detection_range', 30.0)  # meters
        self.declare_parameter('sigma_0_squared', 0.01)
        self.declare_parameter('noise_scale_factor', 0.02)
        self.declare_parameter('process_noise_q', 0.005)
        self.declare_parameter('observations_for_confirmation', 3)
        self.declare_parameter('timeout_until_deleted', 0.5)  # seconds
        self.declare_parameter('initial_covariance', 1.0)
        self.declare_parameter('association_gate_radius', 2.0)  # meters
        self.declare_parameter('mahalanobis_threshold', 2.45)  # sqrt(5.99) for 2 DOF

        # Get parameter values
        self.max_detection_range = self.get_parameter('max_detection_range').value
        self.sigma_0_squared = self.get_parameter('sigma_0_squared').value
        self.noise_scale_factor = self.get_parameter('noise_scale_factor').value
        self.process_noise_q = self.get_parameter('process_noise_q').value
        self.observations_for_confirmation = self.get_parameter('observations_for_confirmation').value
        self.timeout_until_deleted = self.get_parameter('timeout_until_deleted').value
        self.initial_covariance = self.get_parameter('initial_covariance').value
        self.association_gate_radius = self.get_parameter('association_gate_radius').value
        self.mahalanobis_threshold = self.get_parameter('mahalanobis_threshold').value

        self.get_logger().info(
            f"Initialized local node with params: range={self.max_detection_range}m, "
            f"timeout={self.timeout_until_deleted}s, "
            f"confirm_thresh={self.observations_for_confirmation}, "
            f"gate_radius={self.association_gate_radius}m"
        )

        # Process noise covariance (2D)
        self.Q = np.eye(2) * self.process_noise_q

        # Tracked landmarks dictionary: {identifier: LocalKalmanLandmark}
        self.landmarks = {}
        self.next_landmark_id = 0
        self.published_marker_ids = set()

        # Subscriber (subscribes directly to local landmarks from perception)
        self.landmark_sub = self.create_subscription(
            LandmarkArray,
            '/perception/landmarks',
            self.landmarks_callback,
            10
        )

        # Publishers
        self.map_pub = self.create_publisher(
            LandmarkArray,
            '/slam/local_cones',
            10
        )
        self.marker_pub = self.create_publisher(
            MarkerArray,
            '/slam/local_cones_markers',
            10
        )

    def associate_detections(self, detections):
        """
        Associate 2D detections with existing landmarks using Mahalanobis distance.
        
        Args:
            detections: List of np.array([x, y])
            
        Returns:
            matches: List of tuples (detection_idx, landmark_id)
            unmatched_detections: List of detection indices
        """
        if not self.landmarks:
            return [], list(range(len(detections)))

        landmark_ids = list(self.landmarks.keys())
        landmark_list = list(self.landmarks.values())
        
        # Extract positions of active landmarks
        landmark_positions = np.array([lm.state for lm in landmark_list])
        tree = cKDTree(landmark_positions)
        
        num_detections = len(detections)
        num_landmarks = len(landmark_list)
        
        # Build cost matrix
        LARGE_COST = 1e9
        cost_matrix = np.full((num_detections, num_landmarks), LARGE_COST)
        
        for det_idx, det_pos in enumerate(detections):
            # Query ball point for candidates within search radius
            candidates = tree.query_ball_point(det_pos, self.association_gate_radius)
            
            # Compute distance-dependent noise R for Mahalanobis gating
            dist = np.linalg.norm(det_pos)
            R = (self.sigma_0_squared + self.noise_scale_factor * (dist**2)) * np.eye(2)
            
            for lm_idx in candidates:
                lm = landmark_list[lm_idx]
                
                # Compute innovation
                innovation = det_pos - lm.state
                S = lm.covariance + R
                try:
                    S_inv = np.linalg.inv(S)
                    mahal_dist_sq = innovation.T @ S_inv @ innovation
                    mahal_dist = np.sqrt(mahal_dist_sq)
                    
                    if mahal_dist < self.mahalanobis_threshold:
                        cost_matrix[det_idx, lm_idx] = mahal_dist
                except np.linalg.LinAlgError:
                    continue

        # Solve assignment using Hungarian algorithm
        row_indices, col_indices = linear_sum_assignment(cost_matrix)
        
        matches = []
        for r, c in zip(row_indices, col_indices):
            if cost_matrix[r, c] < LARGE_COST:
                matches.append((r, landmark_ids[c]))
                
        matched_det_indices = set(m[0] for m in matches)
        unmatched_detections = [i for i in range(num_detections) if i not in matched_det_indices]
        
        return matches, unmatched_detections

    def landmarks_callback(self, msg):
        """
        Callback for incoming local cone detections.
        """
        current_time = self.get_clock().now()
        
        # 1. Filter incoming detections and extract valid 2D coordinates
        detections = []
        detection_types = []
        for landmark in msg.landmarks:
            # Check for NaN / Inf in incoming landmark position
            if not (math.isfinite(landmark.position.x) and math.isfinite(landmark.position.y)):
                continue

            # Gating by 2D distance
            dist = math.sqrt(landmark.position.x**2 + landmark.position.y**2)
            if dist > self.max_detection_range:
                continue

            detections.append(np.array([landmark.position.x, landmark.position.y]))
            detection_types.append(landmark.type)

        # 2. Perform spatial data association
        matches, unmatched_detections = self.associate_detections(detections)

        # Predict step for all current landmarks
        for lm in self.landmarks.values():
            lm.predict(self.Q)

        observed_ids = set()

        # 3. Update matched landmarks
        for det_idx, lm_id in matches:
            det_pos = detections[det_idx]
            det_type = detection_types[det_idx]
            dist = np.linalg.norm(det_pos)
            R = (self.sigma_0_squared + self.noise_scale_factor * (dist**2)) * np.eye(2)
            
            lm = self.landmarks[lm_id]
            if lm.update(det_pos, R):
                lm.cone_type = det_type
                lm.last_seen_time = current_time
                observed_ids.add(lm_id)

        # 4. Initialize unmatched detections as new landmarks
        for det_idx in unmatched_detections:
            det_pos = detections[det_idx]
            det_type = detection_types[det_idx]
            
            new_id = self.next_landmark_id
            self.next_landmark_id += 1
            
            new_lm = LocalKalmanLandmark(
                identifier=new_id,
                position=det_pos,
                cone_type=det_type,
                initial_covariance=self.initial_covariance,
                current_time=current_time
            )
            self.landmarks[new_id] = new_lm
            observed_ids.add(new_id)

        # 5. Check timeout for landmarks not observed in this frame
        lost_ids = []
        for lm_id, lm in self.landmarks.items():
            if lm_id not in observed_ids:
                # Check how long it has been since we last saw this landmark
                time_since_seen = (current_time - lm.last_seen_time).nanoseconds / 1e9
                if time_since_seen > self.timeout_until_deleted:
                    lost_ids.append(lm_id)

        # Prune timed out landmarks
        for lm_id in lost_ids:
            del self.landmarks[lm_id]

        # 6. Publish the updated local cone map and RViz markers
        self.publish_map(msg.header.frame_id, current_time)

    def publish_map(self, frame_id, current_time):
        """
        Publishes confirmed local landmarks and their visualization markers.
        """
        # LandmarkArray message
        msg = LandmarkArray()
        msg.header.stamp = current_time.to_msg()
        msg.header.frame_id = frame_id  # Publish in the same frame as input

        # MarkerArray message
        marker_array_msg = MarkerArray()
        active_marker_ids = set()

        for ident, lm in self.landmarks.items():
            # Only publish/visualize confirmed landmarks
            if lm.observation_count < self.observations_for_confirmation:
                continue

            # Ensure the state and covariance are finite before publishing
            if not (np.isfinite(lm.state).all() and np.isfinite(lm.covariance).all()):
                continue

            # Add to local map message
            landmark_msg = Landmark()
            landmark_msg.position.x = float(lm.state[0])
            landmark_msg.position.y = float(lm.state[1])
            landmark_msg.position.z = 0.0  # Constant Z for cones
            landmark_msg.type = lm.cone_type
            landmark_msg.probability = 1.0 / (1.0 + np.trace(lm.covariance))
            landmark_msg.identifier = lm.id
            msg.landmarks.append(landmark_msg)

            # Add to RViz Marker message
            marker = Marker()
            marker.header = msg.header
            marker.ns = "local_cones"
            marker.id = lm.id
            marker.type = Marker.CYLINDER
            marker.action = Marker.ADD

            marker.pose.position.x = float(lm.state[0])
            marker.pose.position.y = float(lm.state[1])
            marker.pose.position.z = 0.15  # Half of 0.3m height, so base is at z=0.0

            marker.pose.orientation.w = 1.0
            
            # FS Cone dimensions
            marker.scale.x = 0.20
            marker.scale.y = 0.20
            marker.scale.z = 0.30

            # Color assignment
            if lm.cone_type == ConeType.BLUE:
                marker.color.r = 0.0
                marker.color.g = 0.0
                marker.color.b = 1.0
            elif lm.cone_type == ConeType.YELLOW:
                marker.color.r = 1.0
                marker.color.g = 1.0
                marker.color.b = 0.0
            elif lm.cone_type == ConeType.ORANGE:
                marker.color.r = 1.0
                marker.color.g = 0.5
                marker.color.b = 0.0
            else:
                marker.color.r = 0.5
                marker.color.g = 0.5
                marker.color.b = 0.5
            
            marker.color.a = 1.0  # Opaque
            marker.lifetime = rclpy.duration.Duration(seconds=0).to_msg()

            marker_array_msg.markers.append(marker)
            active_marker_ids.add(lm.id)

        # Formally delete any markers that are no longer active
        deleted_ids = self.published_marker_ids - active_marker_ids
        for del_id in deleted_ids:
            del_marker = Marker()
            del_marker.header = msg.header
            del_marker.ns = "local_cones"
            del_marker.id = del_id
            del_marker.action = Marker.DELETE
            marker_array_msg.markers.append(del_marker)

        self.published_marker_ids = active_marker_ids

        # Publish topics
        self.map_pub.publish(msg)
        self.marker_pub.publish(marker_array_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ConeMappingNodeLocally()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()