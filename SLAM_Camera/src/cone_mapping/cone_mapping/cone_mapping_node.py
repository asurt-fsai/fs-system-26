#!/usr/bin/env python3
"""
ROS2 Cone Mapping Node
Formula Student Driverless - SLAM Subsystem

Implements a robust, landmark-based cone mapping pipeline with:
- Visual-inertial SLAM pose estimation
- Probabilistic data association
- Kalman filtering for landmark state estimation
- Lifecycle management for output stability
"""
import pyzed as sl
import rclpy
from rclpy.node import Node
from rclpy.time import Time
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree
from scipy.stats import chi2
import threading
from collections import deque
from enum import Enum

# ROS2 imports
from geometry_msgs.msg import PoseStamped, TransformStamped, Point
from std_msgs.msg import Header
from nav_msgs.msg import Path  # [NEW] For corrected trajectory
from tf2_ros import Buffer, TransformListener
from std_msgs.msg import Bool, Float64
import tf2_geometry_msgs
import message_filters
import time
from visualization_msgs.msg import Marker, MarkerArray
from tf_helper.StatusPublisher import StatusPublisher

try:
    from zed_msgs.msg import PosTrackStatus
except ImportError:
    print("Warning: Could not import zed_msgs.msg.PosTrackStatus")
    PosTrackStatus = None

# Custom message types
try:
    from cone_mapping.msg import Landmark, LandmarkArray
except ImportError:
    # Fallback for testing without building messages
    print("Warning: Could not import custom messages, using placeholders")
    
    class Landmark:
        """Placeholder for custom Landmark message"""
        def __init__(self):
            self.position = Point()
            self.type = 0  # 0 = Blue, 1 = Yellow, etc.
            self.identifier = 0  # Ignored as per design
            self.probability = 0.0

    class LandmarkArray:
        """Placeholder for custom LandmarkArray message"""
        def __init__(self):
            self.header = Header()
            self.landmarks = []

# Try to import the perception message type from asurt_msgs if available
try:
    from asurt_msgs.msg import Landmark as AsurtLandmark, LandmarkArray as AsurtLandmarkArray
except Exception:
    AsurtLandmark = None
    AsurtLandmarkArray = None


# ============================================================================
# COLOR MAPPING
# ============================================================================

class ConeType:
    """Cone type/color enumeration"""
    BLUE = 0
    YELLOW = 1
    ORANGE = 2
    ORANGE_LARGE = 3
    UNKNOWN = 4

def type_to_color_string(cone_type):
    """Convert cone type integer to color string"""
    mapping = {
        ConeType.BLUE: "blue",
        ConeType.YELLOW: "yellow",
        ConeType.ORANGE: "orange",
        ConeType.ORANGE_LARGE: "orange_large",
        ConeType.UNKNOWN: "unknown"
    }
    return mapping.get(cone_type, "unknown")

def color_string_to_type(color_string):
    """Convert color string to cone type integer"""
    mapping = {
        "blue": ConeType.BLUE,
        "yellow": ConeType.YELLOW,
        "orange": ConeType.ORANGE,
        "orange_large": ConeType.ORANGE_LARGE,
        "large": ConeType.ORANGE_LARGE,
        "unknown": ConeType.UNKNOWN
    }
    return mapping.get(color_string.lower(), ConeType.UNKNOWN)


# ============================================================================
# ENUMERATIONS AND CONSTANTS
# ============================================================================

class LandmarkState(Enum):
    """Finite state machine states for landmark lifecycle"""
    TENTATIVE = 1
    CONFIRMED = 2
    LOST = 3
    DELETED = 4


class MappingConstants:
    """System-wide configuration parameters"""
    # Distance gating
    MAX_DETECTION_RANGE = 1.0  # meters (r_max)
    
    # Height validation
    MAX_CONE_HEIGHT_DEVIATION = 2.0  # meters, increased to handle floating cones (camera z=0 issue)
    
    # Data association
    ASSOCIATION_GATE_RADIUS = 2.0  # meters (d_gate)
    MAHALANOBIS_THRESHOLD = 5.991  # Chi-squared 95% confidence, 2 DOF
    
    # Measurement noise model: σ²(d) = σ₀² + k·d²
    SIGMA_0_SQUARED = 0.01  # Base measurement noise (m²)
    NOISE_SCALE_FACTOR = 0.02 # Distance-dependent scaling
    
    # Process noise
    PROCESS_NOISE_Q = 0.001  # Static landmark model
    
    # Lifecycle thresholds
    OBSERVATIONS_FOR_CONFIRMATION = 20
    COVARIANCE_THRESHOLD_CONFIRMATION = 0.1 # meters²
    FRAMES_UNTIL_LOST = 10
    TIMEOUT_UNTIL_DELETED = 5.0  # seconds
    
    # Map maintenance
    MERGE_DISTANCE_THRESHOLD = 1.0  # meters
    MERGE_CHECK_INTERVAL = 1.0  # seconds
    
    # Initial covariance for new landmarks
    INITIAL_COVARIANCE = 10.0  # meters²


# ============================================================================
# KALMAN FILTER LANDMARK CLASS
# ============================================================================

class KalmanLandmark:
    """
    Represents a single cone landmark with Kalman filter state estimation.
    
    State vector: x = [x, y]^T (2D position in map frame)
    Motion model: x_{k+1} = F·x_k + w_k (static, F = I)
    Measurement model: z_k = H·x_k + v_k (direct observation, H = I)
    """
    
    _id_counter = 0
    _id_lock = threading.Lock()
    
    def __init__(self, position, cone_type, initial_covariance):
        """
        Initialize a new landmark.
        
        Args:
            position: np.array([x, y]) in map frame
            cone_type: int (ConeType enum value)
            initial_covariance: float, initial uncertainty
        """
        with KalmanLandmark._id_lock:
            self.id = KalmanLandmark._id_counter
            KalmanLandmark._id_counter += 1
        
        # State: 2D position
        self.state = np.array(position, dtype=np.float64)
        
        # Covariance: 2x2 matrix
        self.covariance = np.eye(2, dtype=np.float64) * initial_covariance
        
        # Attributes
        self.cone_type = cone_type
        self.assigned_type = cone_type  # Fixed at first confirmation
        
        # Lifecycle
        self.lifecycle_state = LandmarkState.TENTATIVE
        self.observation_count = 1
        self.frames_not_seen = 0
        self.last_seen_time = None
        
        # Color consistency tracking
        self.type_mismatch_count = 0
        
        # [NEW] Graph-SLAM Anchoring Fields
        self.anchor_pose = None
        self.anchor_timestamp = None
        self.relative_state = None
        
    def predict(self, Q):
        """
        Kalman prediction step.
        
        For static landmarks: x̂_{k|k-1} = F·x̂_{k-1|k-1} = x̂_{k-1|k-1}
        P_{k|k-1} = F·P_{k-1|k-1}·F^T + Q = P_{k-1|k-1} + Q
        
        Args:
            Q: Process noise covariance (2x2)
        """
        # State prediction (identity motion model)
        # self.state remains unchanged
        
        # Covariance prediction
        self.covariance = self.covariance + Q
        
    def update(self, measurement, R):
        """
        Kalman update step with innovation gating.
        
        Args:
            measurement: np.array([x, y]) in map frame
            R: Measurement noise covariance (2x2)
            
        Returns:
            bool: True if update accepted, False if gated
        """
        # Measurement model (H = I for direct position observation)
        H = np.eye(2)
        
        # Innovation covariance: S = H·P·H^T + R
        S = self.covariance + R
        
        # Innovation: y = z - H·x̂
        innovation = measurement - self.state
        
        # Mahalanobis distance for gating
        try:
            S_inv = np.linalg.inv(S)
            mahal_dist_sq = innovation.T @ S_inv @ innovation
            
            # Gate check
            if mahal_dist_sq > MappingConstants.MAHALANOBIS_THRESHOLD:
                return False  # Reject outlier
                
        except np.linalg.LinAlgError:
            # Singular covariance matrix
            return False
        
        # Kalman gain: K = P·H^T·S^{-1}
        K = self.covariance @ S_inv
        
        # State update: x̂_{k|k} = x̂_{k|k-1} + K·y
        self.state = self.state + K @ innovation
        
        # Covariance update: P_{k|k} = (I - K·H)·P_{k|k-1}
        I_KH = np.eye(2) - K @ H
        self.covariance = I_KH @ self.covariance
        
        # Increment observation count
        self.observation_count += 1
        self.frames_not_seen = 0
        
        return True
    
    def get_innovation_covariance(self, R):
        """
        Compute innovation covariance S = H·P·H^T + R for data association.
        
        Args:
            R: Measurement noise covariance (2x2)
            
        Returns:
            S: Innovation covariance (2x2)
        """
        return self.covariance + R
    
    def compute_mahalanobis_distance(self, measurement, R):
        """
        Compute Mahalanobis distance for data association.
        
        d_M = sqrt((z - x̂)^T · S^{-1} · (z - x̂))
        
        Args:
            measurement: np.array([x, y])
            R: Measurement noise covariance (2x2)
            
        Returns:
            float: Mahalanobis distance
        """
        innovation = measurement - self.state
        S = self.get_innovation_covariance(R)
        
        try:
            S_inv = np.linalg.inv(S)
            mahal_dist_sq = innovation.T @ S_inv @ innovation
            return np.sqrt(mahal_dist_sq)
        except np.linalg.LinAlgError:
            return np.inf
    
    def check_type_consistency(self, observed_type):
        """
        Check if observed type matches assigned type.
        
        Args:
            observed_type: int (ConeType)
            
        Returns:
            bool: True if consistent
        """
        if self.lifecycle_state == LandmarkState.TENTATIVE:
            # Allow type changes in tentative state
            return True
        
        if observed_type == self.assigned_type:
            return True
        else:
            self.type_mismatch_count += 1
            return False
    
    def update_lifecycle(self, current_time, Tpose=None):
        """
        Update lifecycle state based on observation history.
        
        Args:
            current_time: rclpy.time.Time
            Tpose: 4x4 numpy array (optional), vehicle pose for anchoring
        """
        if self.lifecycle_state == LandmarkState.TENTATIVE:
            # Tentative → Confirmed
            if (self.observation_count >= MappingConstants.OBSERVATIONS_FOR_CONFIRMATION and
                np.trace(self.covariance) < MappingConstants.COVARIANCE_THRESHOLD_CONFIRMATION):
                self.lifecycle_state = LandmarkState.CONFIRMED
                self.assigned_type = self.cone_type  # Lock type
                
                # [NEW] Phase 4: Graph-SLAM Anchoring Logic
                if Tpose is not None:
                    self.anchor_timestamp = current_time
                    self.anchor_pose = Tpose
                    # Convert Kalman filter's self.state [x, y] into a homogeneous point p_map = [x, y, 0.0, 1.0]
                    p_map = np.array([self.state[0], self.state[1], 0.0, 1.0])
                    try:
                        # Compute the relative position: p_relative = inverse(T_pose) * p_map
                        self.relative_state = np.linalg.inv(Tpose) @ p_map
                    except np.linalg.LinAlgError:
                        self.relative_state = None  # Failed to compute relative state
                
        elif self.lifecycle_state == LandmarkState.CONFIRMED:
            pass  # Map Persistence: Once a cone is confirmed, it stays in the global map forever!
            # Confirmed → Lost
            # if self.frames_not_seen >= MappingConstants.FRAMES_UNTIL_LOST:
            #     self.lifecycle_state = LandmarkState.LOST
                
        elif self.lifecycle_state == LandmarkState.LOST:
            pass
            # Lost → Confirmed (if re-observed, handled externally)
            # Lost → Deleted
            # if self.last_seen_time is not None and current_time is not None:
            #     time_diff = (current_time.nanoseconds - self.last_seen_time.nanoseconds) / 1e9
            #     if time_diff > MappingConstants.TIMEOUT_UNTIL_DELETED:
            #         self.lifecycle_state = LandmarkState.DELETED


# ============================================================================
# PHASE 1: COORDINATE TRANSFORMATION & GATING
# ============================================================================

class CoordinateTransformer:
    """
    Handles deterministic coordinate transformations and spatial gating.
    
    Transform chain: p_cone_map = T_map_base · T_base_camera · p_cone_camera
    """
    
    def __init__(self, tf_buffer, logger):
        """
        Args:
            tf_buffer: tf2_ros.Buffer
            logger: rclpy logger
        """
        self.tf_buffer = tf_buffer
        self.logger = logger
        self.T_base_camera = None  # Cached static transform
        
    def lookup_static_transform(self):
        """
        Look up static transform from zed_camera to base_link.
        This should be called once during initialization.
        """
        try:
            transform = self.tf_buffer.lookup_transform(
                'base_link',
                'zed_camera',
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=5.0)
            )
            self.T_base_camera = self._transform_to_matrix(transform.transform)
            self.logger.info("Static transform zed_camera -> base_link acquired")
            return True
        except Exception as e:
            self.logger.error(f"Failed to lookup static transform: {e}")
            return False
    
    def _transform_to_matrix(self, transform):
        """
        Convert geometry_msgs/Transform to 4x4 homogeneous transformation matrix.
        
        Args:
            transform: geometry_msgs.msg.Transform
            
        Returns:
            np.array: 4x4 transformation matrix
        """
        # Extract translation
        t = np.array([transform.translation.x,
                     transform.translation.y,
                     transform.translation.z])
        
        # Extract rotation (quaternion to rotation matrix)
        q = transform.rotation
        qx, qy, qz, qw = q.x, q.y, q.z, q.w
        
        # Quaternion to rotation matrix
        R = np.array([
            [1 - 2*(qy**2 + qz**2), 2*(qx*qy - qw*qz), 2*(qx*qz + qw*qy)],
            [2*(qx*qy + qw*qz), 1 - 2*(qx**2 + qz**2), 2*(qy*qz - qw*qx)],
            [2*(qx*qz - qw*qy), 2*(qy*qz + qw*qx), 1 - 2*(qx**2 + qy**2)]
        ])
        
        # Build 4x4 matrix
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = t
        
        return T
    
    def _pose_to_matrix(self, pose):
        """
        Convert geometry_msgs/Pose to 4x4 homogeneous transformation matrix.
        
        Args:
            pose: geometry_msgs.msg.Pose
            
        Returns:
            np.array: 4x4 transformation matrix
        """
        # Extract translation
        t = np.array([pose.position.x,
                     pose.position.y,
                     pose.position.z])
        
        # Extract rotation
        q = pose.orientation
        qx, qy, qz, qw = q.x, q.y, q.z, q.w
        
        # Quaternion to rotation matrix
        R = np.array([
            [1 - 2*(qy**2 + qz**2), 2*(qx*qy - qw*qz), 2*(qx*qz + qw*qy)],
            [2*(qx*qy + qw*qz), 1 - 2*(qx**2 + qz**2), 2*(qy*qz - qw*qx)],
            [2*(qx*qz - qw*qy), 2*(qy*qz + qw*qx), 1 - 2*(qx**2 + qy**2)]
        ])
        
        # Build 4x4 matrix
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = t
        
        return T
    
    def transform_and_gate(self, landmarks_camera, pose_map_base):
        """
        Transform cone detections from camera frame to map frame and apply gating.
        
        Args:
            landmarks_camera: List of Landmark objects in camera frame
            pose_map_base: geometry_msgs.msg.Pose (vehicle pose in map)
            
        Returns:
            List of dicts: [{'position': np.array([x,y]), 'type': int, 'distance': float, 'probability': float}, ...]
        """
        if self.T_base_camera is None:
            self.logger.warn("Static transform not available")
            return []
        
        # Get T_map_base
        T_map_base = self._pose_to_matrix(pose_map_base)
        
        # Complete transformation: T_map_camera = T_map_base · T_base_camera
        T_map_camera = T_map_base @ self.T_base_camera
        
        validated_detections = []
        
        for landmark in landmarks_camera:

            # Map any out-of-range types to UNKNOWN
            if landmark.type not in [ConeType.BLUE, ConeType.YELLOW, ConeType.ORANGE, ConeType.ORANGE_LARGE, ConeType.UNKNOWN]:
                landmark.type = ConeType.UNKNOWN

            # Position in camera frame (homogeneous coordinates)
            p_camera = np.array([landmark.position.x,
                               landmark.position.y,
                               landmark.position.z,
                               1.0])
            
            # Transform to vehicle base_link frame
            p_base_homo = self.T_base_camera @ p_camera
            p_base = p_base_homo[:3]
            
            # Transform to map frame
            p_map_homo = T_map_base @ p_base_homo
            p_map = p_map_homo[:3]  # [x, y, z] in map frame

            if not np.all(np.isfinite(p_map)):
                self.logger.warn(
                    f"Invalid transformed cone position, dropping detection: {p_map}"
                )
                continue
            
            # Apply gating filters
            
            # 1. Distance gating (relative to vehicle base_link)
            distance_2d = np.linalg.norm(p_base[:2])
            self.logger.info(f"DEBUG GATING: cone base_link={p_base[:2]}, distance_2d={distance_2d:.2f}m, MAX_LIMIT={MappingConstants.MAX_DETECTION_RANGE:.2f}m")
            if distance_2d > MappingConstants.MAX_DETECTION_RANGE:
                self.logger.info(f"Gating: Rejected cone at d={distance_2d:.2f}m (> {MappingConstants.MAX_DETECTION_RANGE:.2f}m)")
                continue
            
            # 2. Height gating (z-coordinate check)
            # Assuming ground plane is approximately z=0 in map frame
            if abs(p_map[2]) > MappingConstants.MAX_CONE_HEIGHT_DEVIATION:
                self.logger.info(
                    f"Gating: Rejected cone at z={p_map[2]:.3f}m "
                    f"(abs > {MappingConstants.MAX_CONE_HEIGHT_DEVIATION:.3f}m). "
                    f"Pos: ({p_map[0]:.2f}, {p_map[1]:.2f})"
                )
                continue
            
            # Detection passed gating
            validated_detections.append({
                'position': p_map[:2],  # Only x, y for 2D mapping
                'type': landmark.type,
                'distance': distance_2d,
                'probability': landmark.probability
            })
            
            # Log successful validations sparingly
            if len(validated_detections) <= 3:
                self.logger.info(
                    f"Gating: Accepted cone at ({p_map[0]:.2f}, {p_map[1]:.2f}, {p_map[2]:.2f}) "
                    f"type={type_to_color_string(landmark.type)}"
                )
        
        return validated_detections


# ============================================================================
# PHASE 2: PROBABILISTIC DATA ASSOCIATION
# ============================================================================

class DataAssociator:
    """
    Performs probabilistic data association using Mahalanobis distance
    and Hungarian algorithm for global assignment.
    """
    
    def __init__(self, logger):
        self.logger = logger
    
    def compute_measurement_noise(self, distance):
        """
        Compute distance-dependent measurement noise covariance.
        
        R(d) = [[σ²(d), 0],
                [0, σ²(d)]]
        
        where σ²(d) = σ₀² + k·d²
        
        Args:
            distance: float, detection distance in meters
            
        Returns:
            np.array: 2x2 measurement noise covariance matrix
        """
        variance = (MappingConstants.SIGMA_0_SQUARED + 
                   MappingConstants.NOISE_SCALE_FACTOR * distance**2)
        return np.eye(2) * variance
    
    def associate(self, detections, landmarks):
        """
        Perform data association between detections and existing landmarks.
        
        Uses Hungarian algorithm for globally optimal one-to-one matching.
        
        Args:
            detections: List of dicts [{'position': np.array, 'color': str, 'distance': float}, ...]
            landmarks: List of KalmanLandmark objects
            
        Returns:
            matches: List of tuples [(detection_idx, landmark_idx), ...]
            unmatched_detections: List of detection indices
            unmatched_landmarks: List of landmark indices
        """
        if len(detections) == 0:
            return [], [], list(range(len(landmarks)))
        
        if len(landmarks) == 0:
            return [], list(range(len(detections))), []
        
        # Build spatial index for efficient candidate search
        active_landmarks = [lm for lm in landmarks 
                          if lm.lifecycle_state in [LandmarkState.TENTATIVE, 
                                                   LandmarkState.CONFIRMED,
                                                   LandmarkState.LOST]]
        
        if len(active_landmarks) == 0:
            return [], list(range(len(detections))), []

        # Remove any landmarks with invalid state values before building the KD-Tree
        finite_landmarks = []
        for lm in active_landmarks:
            if np.all(np.isfinite(lm.state)):
                finite_landmarks.append(lm)
            else:
                self.logger.warn(f"Removing invalid landmark state from association: {lm.state}")

        if len(finite_landmarks) == 0:
            return [], list(range(len(detections))), list(range(len(landmarks)))

        # Extract positions for KD-Tree
        landmark_positions = np.array([lm.state for lm in finite_landmarks])
        tree = cKDTree(landmark_positions)
        
        # Build cost matrix
        num_detections = len(detections)
        num_landmarks = len(active_landmarks)
        # linear_sum_assignment doesn't support np.inf, use large discrete value
        LARGE_COST = 1e9
        cost_matrix = np.full((num_detections, num_landmarks), LARGE_COST)
        
        for det_idx, detection in enumerate(detections):
            det_pos = detection['position']
            det_dist = detection['distance']

            if not np.all(np.isfinite(det_pos)):
                self.logger.warn(f"Skipping invalid detection position: {det_pos}")
                continue
            
            # Find candidates within gate radius
            candidates = tree.query_ball_point(det_pos, 
                                              MappingConstants.ASSOCIATION_GATE_RADIUS)
            
            # Compute measurement noise for this detection
            R = self.compute_measurement_noise(det_dist)
            
            for lm_idx in candidates:
                landmark = active_landmarks[lm_idx]
                
                # Compute Mahalanobis distance
                mahal_dist = landmark.compute_mahalanobis_distance(det_pos, R)
                
                # Only consider if within threshold
                if mahal_dist < np.sqrt(MappingConstants.MAHALANOBIS_THRESHOLD):
                    cost_matrix[det_idx, lm_idx] = mahal_dist
        
        # Solve assignment problem with Hungarian algorithm
        row_indices, col_indices = linear_sum_assignment(cost_matrix)
        
        # Filter out invalid assignments (cost = LARGE_COST)
        matches = []
        for r, c in zip(row_indices, col_indices):
            if cost_matrix[r, c] < LARGE_COST:
                # Map back to original landmark index
                original_lm_idx = landmarks.index(active_landmarks[c])
                matches.append((r, original_lm_idx))
        
        # Identify unmatched detections and landmarks
        matched_det_indices = set([m[0] for m in matches])
        matched_lm_indices = set([m[1] for m in matches])
        
        unmatched_detections = [i for i in range(num_detections) 
                               if i not in matched_det_indices]
        unmatched_landmarks = [i for i in range(len(landmarks)) 
                              if i not in matched_lm_indices]
        
        return matches, unmatched_detections, unmatched_landmarks


# ============================================================================
# PHASE 3: MAP MAINTENANCE
# ============================================================================

class MapMaintenance:
    """
    Handles landmark merging, pruning, and map optimization.
    """
    
    def __init__(self, logger):
        self.logger = logger
    
    def merge_nearby_landmarks(self, landmarks):
        """
        Merge landmarks that are too close using covariance-weighted averaging.
        
        Merging criterion: ||x_i - x_j|| < d_merge
        
        Merged estimate:
            P_merged^{-1} = P_i^{-1} + P_j^{-1}
            x_merged = P_merged · (P_i^{-1}·x_i + P_j^{-1}·x_j)
        
        Args:
            landmarks: List of KalmanLandmark objects
            
        Returns:
            List of KalmanLandmark objects after merging
        """
        if len(landmarks) < 2:
            return landmarks
        
        # Only merge confirmed landmarks
        confirmed = [lm for lm in landmarks if lm.lifecycle_state == LandmarkState.CONFIRMED]
        other = [lm for lm in landmarks if lm.lifecycle_state != LandmarkState.CONFIRMED]
        
        if len(confirmed) < 2:
            return landmarks
        
        merged_flags = [False] * len(confirmed)
        result = []
        
        for i in range(len(confirmed)):
            if merged_flags[i]:
                continue
                
            current = confirmed[i]
            
            # Find all landmarks within merge distance
            merge_candidates = [i]
            
            for j in range(i+1, len(confirmed)):
                if merged_flags[j]:
                    continue
                    
                dist = np.linalg.norm(current.state - confirmed[j].state)
                # Ensure they are the exact same color before merging
                if dist < MappingConstants.MERGE_DISTANCE_THRESHOLD and current.cone_type == confirmed[j].cone_type:
                    merge_candidates.append(j)
            
            # If only one landmark, keep as is
            if len(merge_candidates) == 1:
                result.append(current)
                continue
            
            # Merge multiple landmarks
            P_inv_sum = np.zeros((2, 2))
            P_inv_x_sum = np.zeros(2)
            merged_type = current.cone_type
            total_observations = 0
            
            for idx in merge_candidates:
                lm = confirmed[idx]
                try:
                    P_inv = np.linalg.inv(lm.covariance)
                    P_inv_sum += P_inv
                    P_inv_x_sum += P_inv @ lm.state
                    total_observations += lm.observation_count
                    merged_flags[idx] = True
                except np.linalg.LinAlgError:
                    # Skip singular covariance
                    continue
            
            try:
                P_merged = np.linalg.inv(P_inv_sum)
                x_merged = P_merged @ P_inv_x_sum
                
                # Create merged landmark
                merged_lm = KalmanLandmark(x_merged, merged_type, 0.0)
                merged_lm.covariance = P_merged
                merged_lm.lifecycle_state = LandmarkState.CONFIRMED
                merged_lm.observation_count = total_observations
                merged_lm.assigned_type = merged_type
                
                result.append(merged_lm)
                
                self.logger.debug(f"Merged {len(merge_candidates)} landmarks")
                
            except np.linalg.LinAlgError:
                # Keep original if merge fails
                result.append(current)
        
        # Add back non-confirmed landmarks
        return result + other
    
    def prune_deleted_landmarks(self, landmarks):
        """
        Remove landmarks marked as DELETED.
        
        Args:
            landmarks: List of KalmanLandmark objects
            
        Returns:
            List of KalmanLandmark objects (pruned)
        """
        before_count = len(landmarks)
        pruned = [lm for lm in landmarks if lm.lifecycle_state != LandmarkState.DELETED]
        after_count = len(pruned)
        
        if before_count != after_count:
            self.logger.debug(f"Pruned {before_count - after_count} deleted landmarks")
        
        return pruned


# ============================================================================
# MAIN CONE MAPPING NODE
# ============================================================================

class ConeMappingNode(Node):
    """
    Main ROS2 node for cone mapping and localization.
    
    Subscribes to:
        - /perception_landmarks (LandmarkArray)
        - /zed2i/zed_node/pose (PoseStamped)
    
    Publishes:
        - /map/global_cones (LandmarkArray)
    """
    
    def __init__(self):
        super().__init__('cone_mapping_node')
        self.status = StatusPublisher("/status/cone_mapping", self)
        self.status.starting()
        self.status_timer = self.create_timer(0.1, self.status.running)
        self.status.ready()
        
        # Declare and load parameters from YAML
        self.declare_parameter('max_detection_range', 1.0)
        self.declare_parameter('max_cone_height_deviation', 1.0)
        self.declare_parameter('association_gate_radius', 2.0)
        self.declare_parameter('mahalanobis_threshold', 5.991)
        self.declare_parameter('sigma_0_squared', 0.01)
        self.declare_parameter('noise_scale_factor', 0.02)
        self.declare_parameter('process_noise_q', 0.001)
        self.declare_parameter('observations_for_confirmation', 3)
        self.declare_parameter('covariance_threshold_confirmation', 0.5)
        self.declare_parameter('frames_until_lost', 10)
        self.declare_parameter('timeout_until_deleted', 5.0)
        
        # Override MappingConstants with loaded parameters
        MappingConstants.MAX_DETECTION_RANGE = self.get_parameter('max_detection_range').value
        MappingConstants.MAX_CONE_HEIGHT_DEVIATION = self.get_parameter('max_cone_height_deviation').value
        MappingConstants.ASSOCIATION_GATE_RADIUS = self.get_parameter('association_gate_radius').value
        MappingConstants.MAHALANOBIS_THRESHOLD = self.get_parameter('mahalanobis_threshold').value
        MappingConstants.SIGMA_0_SQUARED = self.get_parameter('sigma_0_squared').value
        MappingConstants.NOISE_SCALE_FACTOR = self.get_parameter('noise_scale_factor').value
        MappingConstants.PROCESS_NOISE_Q = self.get_parameter('process_noise_q').value
        MappingConstants.OBSERVATIONS_FOR_CONFIRMATION = self.get_parameter('observations_for_confirmation').value
        MappingConstants.COVARIANCE_THRESHOLD_CONFIRMATION = self.get_parameter('covariance_threshold_confirmation').value
        MappingConstants.FRAMES_UNTIL_LOST = self.get_parameter('frames_until_lost').value
        MappingConstants.TIMEOUT_UNTIL_DELETED = self.get_parameter('timeout_until_deleted').value
        
        self.get_logger().info(f"Loaded parameters: height_dev={MappingConstants.MAX_CONE_HEIGHT_DEVIATION}m, "
                              f"range={MappingConstants.MAX_DETECTION_RANGE}m")
        
        # Initialize TF2
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # Initialize subsystems
        self.transformer = CoordinateTransformer(self.tf_buffer, self.get_logger())
        self.associator = DataAssociator(self.get_logger())
        self.maintenance = MapMaintenance(self.get_logger())
        
        # Global landmark map (stored in 'map' frame)
        self.landmarks = []
        self.map_lock = threading.Lock()
        
        # Process noise matrix (static model)
        self.Q = np.eye(2) * MappingConstants.PROCESS_NOISE_Q
        
        # Debug counters
        self.landmark_msg_count = 0
        self.pose_msg_count = 0
        self.sync_callback_count = 0
        self.latest_input_stamp = None
        
        # Subscribers with message filters for synchronization
        # Prefer subscribing to asurt_msgs if available (matches publisher), otherwise use cone_mapping
        if AsurtLandmarkArray is not None:
            perception_msg_type = AsurtLandmarkArray
            self.get_logger().info("Subscribing to /perception_landmarks using asurt_msgs LandmarkArray")
        else:
            perception_msg_type = LandmarkArray

        self.landmark_sub = message_filters.Subscriber(
            self,
            perception_msg_type,
            '/perception_landmarks'
        )
        
        self.pose_sub = message_filters.Subscriber(
            self,
            PoseStamped,
            '/zed/zed_node/pose'
        )
        
        # Time synchronizer
        self.sync = message_filters.ApproximateTimeSynchronizer(
            [self.landmark_sub, self.pose_sub],
            queue_size=10,
            slop=0.1  # 100ms tolerance
        )
        self.sync.registerCallback(self.synchronized_callback)
        
        self.get_logger().info("Message synchronizer configured (slop=0.1s)")
        
        self.map_pub = self.create_publisher(
            LandmarkArray,
            '/map/global_cones',
            10
        )
        
        self.time_publisher = self.create_publisher(
            Float64,
            '/diagnostics/comp_time/slam',
            10
        )
        
        # Publisher for RViz visualization
        self.marker_pub = self.create_publisher(
            MarkerArray,
            '/map/global_cones_markers',
            10
        )
        
        # Track IDs of markers currently rendered in RViz
        self.published_marker_ids = set()
        
        # Map publication timer
        self.create_timer(1.0, self.maintenance_callback)  # 1 Hz map maintenance
        self.create_timer(0.1, self.publish_map)  # 10 Hz map publishing
        
        # [NEW] Phase 6: Subscriber for SLAM corrected trajectory
        self.trajectory_sub = self.create_subscription(
            Path,
            '/zed/zed_node/path_map',
            self.trajectory_update_callback,
            10
        )
        
        # Subscriber for ZED Positional Tracking Status to detect loop closures
        self.spatial_memory_status = 0 # Default state
        if PosTrackStatus is not None:
            self.status_sub = self.create_subscription(
                PosTrackStatus,
                '/zed/zed_node/pose/status',
                self.pose_status_callback,
                10
            )
        else:
            self.get_logger().warn("PosTrackStatus not available. Cannot subscribe to spatial memory status.")

        # Wait for static transform
        self.get_logger().info("Waiting for static transform zed_camera -> base_link...")
        self.create_timer(0.5, self.init_static_transform)

        # No direct debug subscriptions in production
        
        self.get_logger().info("Cone Mapping Node initialized")
        

            
    
    def init_static_transform(self):
        """Initialize static transform (called periodically until successful)"""
        if self.transformer.T_base_camera is None:
            self.transformer.lookup_static_transform()
            
    def pose_status_callback(self, msg):
        """
        Callback to track the ZED positional tracking status.
        Specifically looking for spatial_memory_status (e.g. LOOP_CLOSED)
        """
        if self.spatial_memory_status != msg.spatial_memory_status:
            self.spatial_memory_status = msg.spatial_memory_status
            if self.spatial_memory_status == 1: # 1 == LOOP_CLOSED
                self.get_logger().info("LOOP_CLOSED: Loop closure detected and drift corrected (from ZED SDK status)!")
            elif self.spatial_memory_status == 2: # 2 == SEARCHING
                self.get_logger().info("SEARCHING: ZED SDK spatial memory is searching for relocation...")
    
    def synchronized_callback(self, landmarks_msg, pose_msg):
        """
        Main processing callback for synchronized perception and pose data.
        
        Args:
            landmarks_msg: LandmarkArray in zed_camera frame
            pose_msg: PoseStamped (vehicle pose in map frame)
        """
        start_time = time.perf_counter()
        try:
            self.latest_input_stamp = landmarks_msg.header.stamp
            self.sync_callback_count += 1
            
            if self.sync_callback_count == 1:
                self.get_logger().info("✓ Synchronized callback triggered! Processing started.")
            
            if self.sync_callback_count % 10 == 0:
                self.get_logger().info(f"Processed {self.sync_callback_count} synchronized message pairs")
            
            if self.transformer.T_base_camera is None:
                self.get_logger().warn("Static transform not ready, skipping frame")
                return  # Static transform not ready
            
            # PHASE 1: Transform and gate detections
            detections = self.transformer.transform_and_gate(
                landmarks_msg.landmarks,
                pose_msg.pose
            )
            
            if self.sync_callback_count <= 5 or self.sync_callback_count % 100 == 0:
                self.get_logger().info(
                    f"Phase 1: {len(landmarks_msg.landmarks)} raw detections -> "
                    f"{len(detections)} after transform & gating"
                )
            
            if len(detections) == 0:
                # No valid detections, update lifecycle
                with self.map_lock:
                    # [NEW] Calculate T_map_base for lifecycle updates
                    T_map_base = self.transformer._pose_to_matrix(pose_msg.pose)
                    for lm in self.landmarks:
                        lm.predict(self.Q)  # Predict state uncertainty forward even when no detections
                        lm.frames_not_seen += 1
                        lm.update_lifecycle(self.get_clock().now(), T_map_base)
                return
            
            # PHASE 2: Data association
            with self.map_lock:
                # Predict step - inflate uncertainty by process noise BEFORE association matching
                for lm in self.landmarks:
                    lm.predict(self.Q)
                    
                matches, unmatched_dets, unmatched_lms = self.associator.associate(
                    detections,
                    self.landmarks
                )
                
                if self.sync_callback_count <= 5 or self.sync_callback_count % 100 == 0:
                    self.get_logger().info(
                        f"Phase 2: {len(matches)} matches, "
                        f"{len(unmatched_dets)} new detections, "
                        f"{len(unmatched_lms)} unmatched landmarks"
                    )
                
                # PHASE 3: Update matched landmarks (Kalman filter)
                for det_idx, lm_idx in matches:
                    detection = detections[det_idx]
                    landmark = self.landmarks[lm_idx]
                    
                    # Compute measurement noise
                    R = self.associator.compute_measurement_noise(detection['distance'])
                    
                    # Check type consistency
                    type_ok = landmark.check_type_consistency(detection['type'])
                    
                    # Update landmark
                    accepted = landmark.update(detection['position'], R)
                    
                    if accepted:
                        landmark.last_seen_time = self.get_clock().now()
                        landmark.cone_type = detection['type']
                        
                        # If was lost, recover
                        if landmark.lifecycle_state == LandmarkState.LOST:
                            landmark.lifecycle_state = LandmarkState.CONFIRMED
                
                # PHASE 4: Initialize new landmarks from unmatched detections
                for det_idx in unmatched_dets:
                    detection = detections[det_idx]
                    
                    new_landmark = KalmanLandmark(
                        detection['position'],
                        detection['type'],
                        MappingConstants.INITIAL_COVARIANCE
                    )
                    new_landmark.last_seen_time = self.get_clock().now()
                    
                    self.landmarks.append(new_landmark)
                    
                    self.get_logger().debug(
                        f"Initialized new {type_to_color_string(detection['type'])} landmark at "
                        f"({detection['position'][0]:.2f}, {detection['position'][1]:.2f})"
                    )
                
                # Update unmatched landmarks (not seen this frame)
                for lm_idx in unmatched_lms:
                    self.landmarks[lm_idx].frames_not_seen += 1
                
                # Update all lifecycle states
                current_time = self.get_clock().now()
                # [NEW] Calculate T_map_base for anchoring logic
                T_map_base = self.transformer._pose_to_matrix(pose_msg.pose)
                for lm in self.landmarks:
                    lm.update_lifecycle(current_time, T_map_base)
        finally:
            execution_time = (time.perf_counter() - start_time) * 1000.0
            time_msg = Float64()
            time_msg.data = execution_time
            self.time_publisher.publish(time_msg)
    
    def maintenance_callback(self):
        """
        Periodic map maintenance: merging and pruning.
        Called at 1 Hz.
        """
        with self.map_lock:
            # Merge nearby landmarks
            self.landmarks = self.maintenance.merge_nearby_landmarks(self.landmarks)
            
            # Prune deleted landmarks
            self.landmarks = self.maintenance.prune_deleted_landmarks(self.landmarks)
            
            # Log statistics
            stats = {state: 0 for state in LandmarkState}
            for lm in self.landmarks:
                stats[lm.lifecycle_state] += 1
            
            self.get_logger().info(
                f"Map: {len(self.landmarks)} total | "
                f"Confirmed: {stats[LandmarkState.CONFIRMED]} | "
                f"Tentative: {stats[LandmarkState.TENTATIVE]} | "
                f"Lost: {stats[LandmarkState.LOST]} | "
                f"Callbacks: {self.sync_callback_count}"
            )
            
    def trajectory_update_callback(self, path_msg):
        """
        [NEW] Phase 6: Global Warp / Loop Closure Correction
        Adjust anchored landmarks when the historical trajectory shifts.
        """
        # Time tolerance for matching poses (0.1 seconds = 1e8 nanoseconds)
        MAX_DT_NS = 1e8 
        # Minimum shift distance to trigger an update (meters)
        MIN_SHIFT_DIST = 0.05
        count = 0
        loop_closure_triggered = False
        updated_landmarks_count = 0
        
        poses = path_msg.poses
        if not poses:
            return

        # Pre-extract timestamps once for all landmarks to avoid O(N * K) conversions
        timestamps = [Time.from_msg(p.header.stamp).nanoseconds for p in poses]
        import bisect

        with self.map_lock:
            for lm in self.landmarks:
                count += 1
                
                if (lm.lifecycle_state == LandmarkState.CONFIRMED and 
                    lm.anchor_timestamp is not None and 
                    lm.relative_state is not None):
                    
                    target_time = lm.anchor_timestamp.nanoseconds
                    
                    # Use binary search to find the closest pose in time
                    idx = bisect.bisect_left(timestamps, target_time)
                    best_pose = None
                    min_dt = float('inf')
                    
                    # Check closest indices around the insertion point
                    for i in (idx - 1, idx, idx + 1):
                        if 0 <= i < len(poses):
                            dt = abs(timestamps[i] - target_time)
                            if dt < min_dt:
                                min_dt = dt
                                best_pose = poses[i]
                            
                    # 1. TIME THRESHOLD: Check if the matched pose is close enough in time
                    if best_pose is not None and min_dt < MAX_DT_NS:
                        # Extract the new, corrected pose and convert it to a 4x4 matrix (Tpose_new)
                        Tpose_new = self.transformer._pose_to_matrix(best_pose.pose)
                        
                        # 2. JITTER PREVENTION: Only warp if the trajectory actually shifted significantly
                        old_pos = lm.anchor_pose[:3, 3]
                        new_pos = Tpose_new[:3, 3]
                        shift_dist = float(np.linalg.norm(new_pos - old_pos))
                        
                        if shift_dist >= MIN_SHIFT_DIST:
                            loop_closure_triggered = True
                            updated_landmarks_count += 1
                            self.get_logger().info(f"[Phase 6] Loop closure trigger detected on landmark {lm.id}! Shift: {shift_dist:.3f}m")
                            
                            # Recalculate global position from relative state: p_map_new = T_pose_new * p_relative
                            p_map_new = Tpose_new @ lm.relative_state
                            
                            # Overwrite the mapped state and save new anchor
                            lm.state = np.array([p_map_new[0], p_map_new[1]])
                            lm.anchor_pose = Tpose_new
                            
                            # 3. KALMAN FILTER BLENDING: Inflate covariance due to sudden map jump
                            lm.covariance += np.eye(2) * (shift_dist * 0.1)
            
            if loop_closure_triggered:
                self.get_logger().info(f"[Phase 6] Spatial Memory Status Update: Loop closure applied. {updated_landmarks_count} landmarks updated out of {len(self.landmarks)} total landmarks in spatial memory.")
    
    def publish_map(self):
        """
        Publish confirmed landmarks to the planner.
        Called at 10 Hz.
        """
        msg = LandmarkArray()
        if hasattr(self, 'latest_input_stamp') and self.latest_input_stamp is not None:
            msg.header.stamp = self.latest_input_stamp
        else:
            msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        
        marker_array_msg = MarkerArray()
        active_marker_ids = set()
        
        with self.map_lock:
            for i, lm in enumerate(self.landmarks):
                # Only publish confirmed landmarks
                if lm.lifecycle_state != LandmarkState.CONFIRMED:
                    continue
                
                # --- Custom Landmark Message ---
                landmark_msg = Landmark()
                landmark_msg.position.x = float(lm.state[0])
                landmark_msg.position.y = float(lm.state[1])
                landmark_msg.position.z = 0.0
                landmark_msg.type = lm.assigned_type
                landmark_msg.probability = 1.0 / (1.0 + np.trace(lm.covariance))
                landmark_msg.identifier = lm.id
                
                msg.landmarks.append(landmark_msg)
                
                # --- RViz Marker Message ---
                marker = Marker()
                marker.header = msg.header
                marker.ns = "global_cones"
                marker.id = lm.id  # Use global landmark ID to keep it consistent
                
                # Use a cylinder instead of an actual triangle mesh
                marker.type = Marker.CYLINDER
                
                # Action ADD means "add or modify". RViz will keep it as long as the ID is the same
                marker.action = Marker.ADD
                
                # Position coordinates
                marker.pose.position.x = float(lm.state[0])
                marker.pose.position.y = float(lm.state[1])
                marker.pose.position.z = 0.15  # Half of height so base is at z=0
                
                # Upright rotation
                marker.pose.orientation.x = 0.0
                marker.pose.orientation.y = 0.0
                marker.pose.orientation.z = 0.0
                  # Size (approximate FS cone: 30cm height, 20cm width base for small; 50.5cm height, 28.5cm width base for large)
                if lm.assigned_type == ConeType.ORANGE_LARGE:
                    marker.scale.x = 0.285
                    marker.scale.y = 0.285
                    marker.scale.z = 0.505
                    marker.pose.position.z = 0.2525  # Half of height so base is at z=0
                else:
                    marker.scale.x = 0.20
                    marker.scale.y = 0.20
                    marker.scale.z = 0.30
                    marker.pose.position.z = 0.15  # Half of height so base is at z=0
                
                # Color based on cone type
                if lm.assigned_type == ConeType.BLUE:
                    marker.color.r = 0.0
                    marker.color.g = 0.0
                    marker.color.b = 1.0
                    marker.color.a = 1.0
                elif lm.assigned_type == ConeType.YELLOW:
                    marker.color.r = 1.0
                    marker.color.g = 1.0
                    marker.color.b = 0.0
                    marker.color.a = 1.0
                elif lm.assigned_type == ConeType.ORANGE:
                    marker.color.r = 1.0
                    marker.color.g = 0.5
                    marker.color.b = 0.0
                    marker.color.a = 1.0
                elif lm.assigned_type == ConeType.ORANGE_LARGE:
                    # Orange-Red/Darker Orange color for large cones
                    marker.color.r = 1.0
                    marker.color.g = 0.25
                    marker.color.b = 0.0
                    marker.color.a = 1.0
                else:
                    marker.color.r = 0.5
                    marker.color.g = 0.5
                    marker.color.b = 0.5
                    marker.color.a = 1.0
                
                # Lifetime 0 means the marker will persist forever until deleted
                marker.lifetime = rclpy.duration.Duration(seconds=0).to_msg()
                
                marker_array_msg.markers.append(marker)
                active_marker_ids.add(lm.id)
                
            # Add markers for DELETED/LOST landmarks that we want to formally remove from RViz
            deleted_ids = self.published_marker_ids - active_marker_ids
            for del_id in deleted_ids:
                del_marker = Marker()
                del_marker.header = msg.header
                del_marker.ns = "global_cones"
                del_marker.id = del_id
                del_marker.action = Marker.DELETE
                marker_array_msg.markers.append(del_marker)
                
            # Update the tracked published IDs
            self.published_marker_ids = active_marker_ids
        
        self.map_pub.publish(msg)
        self.marker_pub.publish(marker_array_msg)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main(args=None):
    rclpy.init(args=args)
    
    node = ConeMappingNode()

    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
