"""MPC Configuration - Centralized parameter definitions"""

from dataclasses import dataclass
from typing import Tuple
import numpy as np


@dataclass
class MPCConfig:
    """MPC controller parameters
    
    Attributes:
        horizon: Prediction horizon (number of steps)
        dt: Time step (seconds)
        wheelbase: Vehicle wheelbase length (meters)
        
    Optimization weights:
        Q: State tracking weight matrix (4x4)
        R: Input effort weight matrix (2x2)
        
    Constraints:
        v_max: Maximum velocity (m/s)
        v_min: Minimum velocity (m/s)
        delta_max: Maximum steering angle (rad)
        delta_dot_max: Maximum steering rate (rad/s)
    """
    
    # Horizon & sampling
    horizon: int = 10
    dt: float = 0.1
    
    # Vehicle
    wheelbase: float = 2.5
    
    # State weights [x, y, theta, delta]
    Q: np.ndarray = None
    
    # Input weights [v, delta_dot]
    R: np.ndarray = None
    
    # Terminal state weight (penalize deviation at end of horizon)
    Q_terminal: np.ndarray = None
    
    # Constraints
    v_max: float = 2.0
    v_min: float = -1.0
    delta_max: float = np.pi / 4  # 45 degrees
    delta_dot_max: float = np.pi / 3  # 60 deg/s
    
    def __post_init__(self):
        """Initialize default weight matrices"""
        if self.Q is None:
            # Heavy penalty on heading error, light on position
            self.Q = np.diag([1.0, 1.0, 10.0, 0.1])
        
        if self.R is None:
            # Penalize velocity and steering changes
            self.R = np.diag([0.1, 0.5])
        
        if self.Q_terminal is None:
            # Terminal cost (typically larger than stage cost)
            self.Q_terminal = self.Q * 2
    
    @property
    def state_size(self) -> int:
        """Size of state vector: [x, y, theta, delta]"""
        return 4
    
    @property
    def input_size(self) -> int:
        """Size of input vector: [v, delta_dot]"""
        return 2
    
    @property
    def prediction_size(self) -> int:
        """Total prediction horizon states"""
        return self.horizon + 1  # Include initial state


# Create a default config instance
DEFAULT_CONFIG = MPCConfig()
