"""Utility functions for MPC controller"""

import numpy as np
from typing import Tuple


def wrap_angle(angle: float) -> float:
    """Wrap angle to [-pi, pi]
    
    Args:
        angle: Angle in radians
        
    Returns:
        Wrapped angle
    """
    while angle > np.pi:
        angle -= 2 * np.pi
    while angle < -np.pi:
        angle += 2 * np.pi
    return angle


def get_reference_error(
    state: np.ndarray,
    reference: np.ndarray
) -> np.ndarray:
    """Compute state tracking error with angle wrapping
    
    Args:
        state: Current state [x, y, theta, delta]
        reference: Reference state [x_ref, y_ref, theta_ref, delta_ref]
    
    Returns:
        error: State error with wrapped angle
    """
    error = state - reference
    error[2] = wrap_angle(error[2])  # Wrap heading error
    error[3] = wrap_angle(error[3])  # Wrap steering error
    return error


def create_cost_function(
    reference_trajectory: np.ndarray,
    Q: np.ndarray,
    R: np.ndarray,
    Q_terminal: np.ndarray = None
) -> callable:
    """Create cost function for MPC
    
    J = sum_i ||x_i - x_ref_i||_Q^2 + ||u_i||_R^2 + ||x_N - x_ref_N||_Q_terminal^2
    
    Args:
        reference_trajectory: Reference trajectory shape (N, 4)
        Q: Stage state cost matrix (4x4)
        R: Control cost matrix (2x2)
        Q_terminal: Terminal cost matrix (4x4), uses Q if None
    
    Returns:
        cost_fn: Function that takes predicted trajectory and controls
    """
    if Q_terminal is None:
        Q_terminal = Q
    
    def cost_function(
        trajectory: np.ndarray,
        controls: np.ndarray
    ) -> float:
        """Calculate total cost
        
        Args:
            trajectory: Predicted trajectory (N+1, 4)
            controls: Control sequence (N, 2)
        
        Returns:
            cost: Total cost value
        """
        cost = 0.0
        N = len(controls)
        
        # Stage costs
        for i in range(N):
            error = trajectory[i] - reference_trajectory[i]
            control_norm = controls[i]
            
            cost += error @ Q @ error + control_norm @ R @ control_norm
        
        # Terminal cost
        terminal_error = trajectory[-1] - reference_trajectory[-1]
        cost += terminal_error @ Q_terminal @ terminal_error
        
        return cost
    
    return cost_function


def saturate(value: float, min_val: float, max_val: float) -> float:
    """Saturate value to bounds
    
    Args:
        value: Value to saturate
        min_val: Minimum bound
        max_val: Maximum bound
    
    Returns:
        Saturated value
    """
    return np.clip(value, min_val, max_val)


def rate_limit(
    current: float,
    desired: float,
    rate_limit: float,
    dt: float
) -> float:
    """Apply rate limit to control change
    
    Args:
        current: Current value
        desired: Desired value
        rate_limit: Maximum change per second
        dt: Time step
    
    Returns:
        Rate-limited value
    """
    max_change = rate_limit * dt
    change = np.clip(desired - current, -max_change, max_change)
    return current + change
