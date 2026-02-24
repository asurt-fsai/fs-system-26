"""Constraint definitions for MPC

Keeps constraint logic organized and reusable
"""

import numpy as np
from .config import MPCConfig


class ConstraintSet:
    """Container for MPC constraints
    
    Handles box constraints and custom constraint logic
    """
    
    def __init__(self, config: MPCConfig):
        """Initialize constraints from config
        
        Args:
            config: MPC configuration
        """
        self.config = config
    
    def get_input_bounds(self) -> tuple:
        """Get control input bounds
        
        Returns:
            (lower_bound, upper_bound): Shape (horizon, 2)
        """
        horizon = self.config.horizon
        
        # Velocity bounds [v_min, v_max]
        v_bounds = np.array([self.config.v_min, self.config.v_max])
        
        # Steering rate bounds [-delta_dot_max, delta_dot_max]
        delta_dot_bounds = np.array([-self.config.delta_dot_max, self.config.delta_dot_max])
        
        lower = np.zeros((horizon, 2))
        upper = np.zeros((horizon, 2))
        
        lower[:, 0] = self.config.v_min
        upper[:, 0] = self.config.v_max
        
        lower[:, 1] = -self.config.delta_dot_max
        upper[:, 1] = self.config.delta_dot_max
        
        return lower, upper
    
    def get_state_bounds(self) -> tuple:
        """Get state bounds
        
        For now, mainly steering angle constraint
        
        Returns:
            (lower_bound, upper_bound): Shape (horizon+1, 4)
        """
        horizon = self.config.prediction_size
        
        lower = np.full((horizon, 4), -np.inf)
        upper = np.full((horizon, 4), np.inf)
        
        # Steering angle constraint: -delta_max <= delta <= delta_max
        lower[:, 3] = -self.config.delta_max
        upper[:, 3] = self.config.delta_max
        
        return lower, upper
    
    def check_feasibility(self, state: np.ndarray, control: np.ndarray) -> bool:
        """Check if state-control pair satisfies constraints
        
        Args:
            state: [x, y, theta, delta]
            control: [v, delta_dot]
        
        Returns:
            bool: True if feasible
        """
        # Steering angle constraint
        if not (-self.config.delta_max <= state[3] <= self.config.delta_max):
            return False
        
        # Velocity constraint
        if not (self.config.v_min <= control[0] <= self.config.v_max):
            return False
        
        # Steering rate constraint
        if not (-self.config.delta_dot_max <= control[1] <= self.config.delta_dot_max):
            return False
        
        return True
