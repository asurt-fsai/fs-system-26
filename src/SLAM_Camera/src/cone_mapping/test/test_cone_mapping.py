#!/usr/bin/env python3
"""
Unit tests for Cone Mapping Node
Tests each phase of the pipeline independently
"""

import unittest
import numpy as np
from numpy.testing import assert_array_almost_equal, assert_array_equal
import sys
import os
from unittest.mock import MagicMock

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/cone_mapping")
# Note: MappingConstants.MAX_CONE_HEIGHT_DEVIATION is updated to 1.0m in the node

# Import modules to test
from cone_mapping_node import (
    KalmanLandmark,
    LandmarkState,
    MappingConstants,
    DataAssociator,
    MapMaintenance,
    ConeType
)


class TestKalmanLandmark(unittest.TestCase):
    """Test Kalman filter landmark state estimation"""
    
    def setUp(self):
        """Initialize test fixtures"""
        self.position = np.array([5.0, 3.0])
        self.cone_type = ConeType.BLUE
        self.initial_cov = 10.0
        
    def test_initialization(self):
        """Test landmark initialization"""
        landmark = KalmanLandmark(self.position, self.cone_type, self.initial_cov)
        
        assert_array_equal(landmark.state, self.position)
        self.assertEqual(landmark.cone_type, self.cone_type)
        self.assertEqual(landmark.lifecycle_state, LandmarkState.TENTATIVE)
        self.assertEqual(landmark.observation_count, 1)
        
        # Check covariance is diagonal with correct values
        expected_cov = np.eye(2) * self.initial_cov
        assert_array_equal(landmark.covariance, expected_cov)
    
    def test_predict_static_model(self):
        """Test Kalman prediction with static motion model"""
        landmark = KalmanLandmark(self.position, self.cone_type, self.initial_cov)
        initial_state = landmark.state.copy()
        initial_cov = landmark.covariance.copy()
        
        Q = np.eye(2) * 0.001
        landmark.predict(Q)
        
        # State should remain unchanged (F = I, static model)
        assert_array_equal(landmark.state, initial_state)
        
        # Covariance should increase by Q
        expected_cov = initial_cov + Q
        assert_array_almost_equal(landmark.covariance, expected_cov)
    
    def test_update_accept(self):
        """Test Kalman update with valid measurement"""
        landmark = KalmanLandmark(self.position, self.cone_type, 1.0)
        
        # Measurement close to state
        measurement = np.array([5.1, 3.1])
        R = np.eye(2) * 0.1
        
        initial_obs_count = landmark.observation_count
        accepted = landmark.update(measurement, R)
        
        self.assertTrue(accepted)
        self.assertEqual(landmark.observation_count, initial_obs_count + 1)
        self.assertEqual(landmark.frames_not_seen, 0)
        
        # State should move toward measurement
        self.assertLess(np.linalg.norm(landmark.state - measurement), 
                       np.linalg.norm(self.position - measurement))
    
    def test_update_reject_outlier(self):
        """Test Kalman update rejects outlier measurements"""
        landmark = KalmanLandmark(self.position, self.cone_type, 0.1)
        
        # Measurement very far from state (outlier)
        measurement = np.array([20.0, 20.0])
        R = np.eye(2) * 0.1
        
        initial_state = landmark.state.copy()
        initial_obs_count = landmark.observation_count
        
        accepted = landmark.update(measurement, R)
        
        self.assertFalse(accepted)
        self.assertEqual(landmark.observation_count, initial_obs_count)
        
        # State should remain unchanged
        assert_array_equal(landmark.state, initial_state)
    
    def test_mahalanobis_distance(self):
        """Test Mahalanobis distance computation"""
        landmark = KalmanLandmark(self.position, self.cone_type, 1.0)
        
        # Measurement at exact state position
        measurement_close = self.position.copy()
        R = np.eye(2) * 0.1
        
        dist_close = landmark.compute_mahalanobis_distance(measurement_close, R)
        self.assertAlmostEqual(dist_close, 0.0, places=5)
        
        # Measurement far from state
        measurement_far = np.array([15.0, 15.0])
        dist_far = landmark.compute_mahalanobis_distance(measurement_far, R)
        self.assertGreater(dist_far, dist_close)
    
    def test_lifecycle_tentative_to_confirmed(self):
        """Test lifecycle transition from Tentative to Confirmed"""
        landmark = KalmanLandmark(self.position, self.cone_type, 10.0)
        
        # Simulate multiple observations
        R = np.eye(2) * 0.1
        for _ in range(MappingConstants.OBSERVATIONS_FOR_CONFIRMATION):
            measurement = self.position + np.random.randn(2) * 0.1
            landmark.update(measurement, R)
        
        # Update lifecycle
        landmark.update_lifecycle(None)
        
        # Should transition to CONFIRMED (with low enough covariance)
        if np.trace(landmark.covariance) < MappingConstants.COVARIANCE_THRESHOLD_CONFIRMATION:
            self.assertEqual(landmark.lifecycle_state, LandmarkState.CONFIRMED)
    
    def test_lifecycle_confirmed_to_lost(self):
        """Test lifecycle transition from Confirmed to Lost"""
        landmark = KalmanLandmark(self.position, self.cone_type, 0.1)
        landmark.lifecycle_state = LandmarkState.CONFIRMED
        landmark.observation_count = 10
        
        # Simulate not seeing the landmark
        landmark.frames_not_seen = MappingConstants.FRAMES_UNTIL_LOST
        landmark.update_lifecycle(None)
        
        self.assertEqual(landmark.lifecycle_state, LandmarkState.LOST)
    
    def test_type_consistency(self):
        """Test type consistency checking"""
        landmark = KalmanLandmark(self.position, ConeType.BLUE, 0.1)
        landmark.lifecycle_state = LandmarkState.CONFIRMED
        landmark.assigned_type = ConeType.BLUE
        
        # Matching type
        self.assertTrue(landmark.check_type_consistency(ConeType.BLUE))
        self.assertEqual(landmark.type_mismatch_count, 0)
        
        # Mismatching type
        self.assertFalse(landmark.check_type_consistency(ConeType.YELLOW))
        self.assertEqual(landmark.type_mismatch_count, 1)


class TestDataAssociator(unittest.TestCase):
    """Test probabilistic data association"""
    
    def setUp(self):
        """Initialize test fixtures"""
        self.mock_logger = MagicMock()
        self.associator = DataAssociator(self.mock_logger)
    
    def test_measurement_noise_model(self):
        """Test distance-dependent measurement noise computation"""
        # At distance 0
        R_0 = self.associator.compute_measurement_noise(0.0)
        expected_var_0 = MappingConstants.SIGMA_0_SQUARED
        assert_array_almost_equal(R_0, np.eye(2) * expected_var_0)
        
        # At distance 10m
        d = 10.0
        R_10 = self.associator.compute_measurement_noise(d)
        expected_var_10 = (MappingConstants.SIGMA_0_SQUARED + 
                          MappingConstants.NOISE_SCALE_FACTOR * d**2)
        assert_array_almost_equal(R_10, np.eye(2) * expected_var_10)
        
        # Noise should increase with distance
        self.assertGreater(np.trace(R_10), np.trace(R_0))
    
    def test_associate_single_match(self):
        """Test association with single detection and single landmark"""
        # Create landmark
        landmark = KalmanLandmark(np.array([5.0, 3.0]), ConeType.BLUE, 0.5)
        landmarks = [landmark]
        
        # Create detection close to landmark
        detections = [{
            'position': np.array([5.1, 3.1]),
            'type': ConeType.BLUE,
            'distance': 5.0
        }]
        
        matches, unmatched_dets, unmatched_lms = self.associator.associate(
            detections, landmarks
        )
        
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0], (0, 0))  # Detection 0 matches landmark 0
        self.assertEqual(len(unmatched_dets), 0)
        self.assertEqual(len(unmatched_lms), 0)
    
    def test_associate_no_match(self):
        """Test association with detection too far from landmark"""
        # Create landmark
        landmark = KalmanLandmark(np.array([5.0, 3.0]), ConeType.BLUE, 0.1)
        landmarks = [landmark]
        
        # Create detection far from landmark
        detections = [{
            'position': np.array([15.0, 15.0]),
            'type': ConeType.BLUE,
            'distance': 20.0
        }]
        
        matches, unmatched_dets, unmatched_lms = self.associator.associate(
            detections, landmarks
        )
        
        self.assertEqual(len(matches), 0)
        self.assertEqual(unmatched_dets, [0])
        self.assertEqual(unmatched_lms, [0])
    
    def test_associate_multiple_hungarian(self):
        """Test Hungarian algorithm with multiple detections and landmarks"""
        # Create landmarks
        landmarks = [
            KalmanLandmark(np.array([5.0, 3.0]), ConeType.BLUE, 0.5),
            KalmanLandmark(np.array([10.0, 8.0]), ConeType.YELLOW, 0.5),
            KalmanLandmark(np.array([15.0, 2.0]), ConeType.BLUE, 0.5),
        ]
        
        # Create detections near landmarks
        detections = [
            {'position': np.array([5.1, 3.1]), 'type': ConeType.BLUE, 'distance': 5.0},
            {'position': np.array([10.1, 8.1]), 'type': ConeType.YELLOW, 'distance': 10.0},
            {'position': np.array([15.1, 2.1]), 'type': ConeType.BLUE, 'distance': 15.0},
        ]
        
        matches, unmatched_dets, unmatched_lms = self.associator.associate(
            detections, landmarks
        )
        
        # Should match all three
        self.assertEqual(len(matches), 3)
        self.assertEqual(len(unmatched_dets), 0)
        self.assertEqual(len(unmatched_lms), 0)
        
        # Check correct pairings
        match_dict = {det_idx: lm_idx for det_idx, lm_idx in matches}
        self.assertEqual(match_dict[0], 0)  # First detection to first landmark
        self.assertEqual(match_dict[1], 1)  # Second to second
        self.assertEqual(match_dict[2], 2)  # Third to third
    
    def test_associate_empty_inputs(self):
        """Test association with empty inputs"""
        # No detections
        matches, unmatched_dets, unmatched_lms = self.associator.associate([], [])
        self.assertEqual(len(matches), 0)
        self.assertEqual(len(unmatched_dets), 0)
        self.assertEqual(len(unmatched_lms), 0)
        
        # Only detections
        detections = [{'position': np.array([5.0, 3.0]), 'type': ConeType.BLUE, 'distance': 5.0}]
        matches, unmatched_dets, unmatched_lms = self.associator.associate(detections, [])
        self.assertEqual(len(matches), 0)
        self.assertEqual(unmatched_dets, [0])
        self.assertEqual(len(unmatched_lms), 0)


class TestMapMaintenance(unittest.TestCase):
    """Test map maintenance operations"""
    
    def setUp(self):
        """Initialize test fixtures"""
        self.mock_logger = MagicMock()
        self.maintenance = MapMaintenance(self.mock_logger)
    
    def test_merge_close_landmarks(self):
        """Test merging of nearby landmarks"""
        # Create two close landmarks
        lm1 = KalmanLandmark(np.array([5.0, 3.0]), ConeType.BLUE, 0.5)
        lm1.lifecycle_state = LandmarkState.CONFIRMED
        lm1.covariance = np.eye(2) * 0.5
        
        lm2 = KalmanLandmark(np.array([5.2, 3.1]), ConeType.BLUE, 0.3)
        lm2.lifecycle_state = LandmarkState.CONFIRMED
        lm2.covariance = np.eye(2) * 0.3
        
        landmarks = [lm1, lm2]
        
        merged = self.maintenance.merge_nearby_landmarks(landmarks)
        
        # Should merge into one landmark
        self.assertEqual(len(merged), 1)
        
        # Merged position should be between the two
        merged_pos = merged[0].state
        self.assertLess(merged_pos[0], max(lm1.state[0], lm2.state[0]))
        self.assertGreater(merged_pos[0], min(lm1.state[0], lm2.state[0]))
    
    def test_no_merge_far_landmarks(self):
        """Test that distant landmarks are not merged"""
        # Create two far landmarks
        lm1 = KalmanLandmark(np.array([5.0, 3.0]), ConeType.BLUE, 0.5)
        lm1.lifecycle_state = LandmarkState.CONFIRMED
        
        lm2 = KalmanLandmark(np.array([10.0, 8.0]), ConeType.BLUE, 0.5)
        lm2.lifecycle_state = LandmarkState.CONFIRMED
        
        landmarks = [lm1, lm2]
        
        merged = self.maintenance.merge_nearby_landmarks(landmarks)
        
        # Should not merge
        self.assertEqual(len(merged), 2)
    
    def test_prune_deleted_landmarks(self):
        """Test pruning of deleted landmarks"""
        # Create landmarks with different states
        lm1 = KalmanLandmark(np.array([5.0, 3.0]), ConeType.BLUE, 0.5)
        lm1.lifecycle_state = LandmarkState.CONFIRMED
        
        lm2 = KalmanLandmark(np.array([10.0, 8.0]), ConeType.YELLOW, 0.5)
        lm2.lifecycle_state = LandmarkState.DELETED
        
        lm3 = KalmanLandmark(np.array([15.0, 2.0]), ConeType.BLUE, 0.5)
        lm3.lifecycle_state = LandmarkState.TENTATIVE
        
        landmarks = [lm1, lm2, lm3]
        
        pruned = self.maintenance.prune_deleted_landmarks(landmarks)
        
        # Should remove only the deleted one
        self.assertEqual(len(pruned), 2)
        self.assertIn(lm1, pruned)
        self.assertNotIn(lm2, pruned)
        self.assertIn(lm3, pruned)
    
    def test_merge_covariance_weighting(self):
        """Test that merging properly weights by covariance"""
        # Landmark with low uncertainty
        lm1 = KalmanLandmark(np.array([5.0, 3.0]), ConeType.BLUE, 0.1)
        lm1.lifecycle_state = LandmarkState.CONFIRMED
        lm1.covariance = np.eye(2) * 0.1
        
        # Landmark with high uncertainty
        lm2 = KalmanLandmark(np.array([5.3, 3.2]), ConeType.BLUE, 2.0)
        lm2.lifecycle_state = LandmarkState.CONFIRMED
        lm2.covariance = np.eye(2) * 2.0
        
        landmarks = [lm1, lm2]
        
        merged = self.maintenance.merge_nearby_landmarks(landmarks)
        
        self.assertEqual(len(merged), 1)
        
        # Merged position should be closer to lm1 (lower uncertainty)
        merged_pos = merged[0].state
        dist_to_lm1 = np.linalg.norm(merged_pos - lm1.state)
        dist_to_lm2 = np.linalg.norm(merged_pos - lm2.state)
        
        self.assertLess(dist_to_lm1, dist_to_lm2)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete pipeline"""
    
    def test_full_pipeline_simulation(self):
        """Simulate full pipeline with multiple frames"""
        # Initialize system
        landmarks = []
        mock_logger = MagicMock()
        associator = DataAssociator(mock_logger)
        maintenance = MapMaintenance(mock_logger)
        
        # Frame 1: Initialize landmarks
        detections_frame1 = [
            {'position': np.array([5.0, 3.0]), 'type': ConeType.BLUE, 'distance': 5.0},
            {'position': np.array([10.0, 8.0]), 'type': ConeType.YELLOW, 'distance': 10.0},
        ]
        
        for det in detections_frame1:
            lm = KalmanLandmark(det['position'], det['type'], 1.0)
            landmarks.append(lm)
        
        self.assertEqual(len(landmarks), 2)
        
        # Frame 2: Re-observe with noise
        detections_frame2 = [
            {'position': np.array([5.1, 3.1]), 'type': ConeType.BLUE, 'distance': 5.0},
            {'position': np.array([10.1, 8.1]), 'type': ConeType.YELLOW, 'distance': 10.0},
        ]
        
        matches, unmatched_dets, _ = associator.associate(detections_frame2, landmarks)
        
        # Should match both
        self.assertEqual(len(matches), 2)
        
        # Update matched landmarks
        for det_idx, lm_idx in matches:
            det = detections_frame2[det_idx]
            R = associator.compute_measurement_noise(det['distance'])
            landmarks[lm_idx].update(det['position'], R)
        
        # Check observation counts increased
        self.assertEqual(landmarks[0].observation_count, 2)
        self.assertEqual(landmarks[1].observation_count, 2)
        
        # Frame 3: Add new detection
        detections_frame3 = [
            {'position': np.array([5.0, 3.0]), 'type': ConeType.BLUE, 'distance': 5.0},
            {'position': np.array([10.0, 8.0]), 'type': ConeType.YELLOW, 'distance': 10.0},
            {'position': np.array([15.0, 2.0]), 'type': ConeType.BLUE, 'distance': 15.0},
        ]
        
        matches, unmatched_dets, _ = associator.associate(detections_frame3, landmarks)
        
        # Should match 2 existing and have 1 new
        self.assertEqual(len(matches), 2)
        self.assertEqual(len(unmatched_dets), 1)
        
        # Initialize new landmark
        for det_idx in unmatched_dets:
            det = detections_frame3[det_idx]
            lm = KalmanLandmark(det['position'], det['type'], 1.0)
            landmarks.append(lm)
        
        self.assertEqual(len(landmarks), 3)


def run_tests():
    """Run all tests and report results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestKalmanLandmark))
    suite.addTests(loader.loadTestsFromTestCase(TestDataAssociator))
    suite.addTests(loader.loadTestsFromTestCase(TestMapMaintenance))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success/failure
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
