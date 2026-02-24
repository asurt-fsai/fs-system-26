"""Bicycle model for MPC prediction

Separate from ROS node - pure dynamics calculations
"""

import numpy as np
from typing import Tuple
from .config import MPCConfig


class BicycleModel:
    """Kinematic bicycle model for trajectory prediction
    
    State: [x, y, theta, delta]
    Input: [v, delta_dot]
    """
    
    def __init__(self, config: MPCConfig):
        """Initialize bicycle model
        
        Args:
            config: MPC configuration object
        """
        self.config = config
    
    def dynamics(
        self, 
        state: np.ndarray, 
        control: np.ndarray
    ) -> np.ndarray:
        """Calculate state derivative using kinematic bicycle model
        
        Args:
            state: [x, y, theta, delta] (4,)
            control: [v, delta_dot] (2,)
            
        Returns:
            state_dot: State derivatives (4,)
        """
        x, y, theta, delta = state
        v, delta_dot = control
        
        # Kinematic constraints
        x_dot = v * np.cos(theta)
        y_dot = v * np.sin(theta)
        theta_dot = (v / self.config.wheelbase) * np.tan(delta)
        delta_dot = delta_dot
        
        return np.array([x_dot, y_dot, theta_dot, delta_dot])
    
    def step(
        self, 
        state: np.ndarray, 
        control: np.ndarray, 
        dt: float = None
    ) -> np.ndarray:
        """Euler integration step
        
        Args:
            state: Current state [x, y, theta, delta]
            control: Control input [v, delta_dot]
            dt: Time step (uses config.dt if None)
            
        Returns:
            next_state: State at t + dt
        """
        if dt is None:
            dt = self.config.dt
        
        state_dot = self.dynamics(state, control)
        next_state = state + state_dot * dt
        
        return next_state
    
    def predict_trajectory(
        self,
        x0: np.ndarray,
        controls: np.ndarray
    ) -> np.ndarray:
        """Predict trajectory over horizon with given control sequence
        
        Args:
            x0: Initial state [x, y, theta, delta]
            controls: Control sequence shape (horizon, 2)
                     Each row: [v, delta_dot]
        
        Returns:
            trajectory: Shape (horizon+1, 4)
                       Includes initial state
        """
        trajectory = np.zeros((len(controls) + 1, 4))
        trajectory[0] = x0
        
        for i, control in enumerate(controls):
            trajectory[i + 1] = self.step(trajectory[i], control)
        
        return trajectory
    
    def linearize(
        self,
        state: np.ndarray,
        control: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Get Jacobians for linearization around nominal trajectory
        
        Uses finite differences for robustness
        
        Args:
            state: Nominal state
            control: Nominal control
        
        Returns:
            A: State Jacobian (4x4)
            B: Input Jacobian (4x2)
        """
        eps = 1e-6
        
        # Nominal state derivative
        x_dot_nom = self.dynamics(state, control)
        
        # A matrix: ∂x_dot/∂state
        A = np.zeros((4, 4))
        for i in range(4):
            state_pert = state.copy()
            state_pert[i] += eps
            x_dot_pert = self.dynamics(state_pert, control)
            A[:, i] = (x_dot_pert - x_dot_nom) / eps
        
        # B matrix: ∂x_dot/∂control
        B = np.zeros((4, 2))
        for i in range(2):
            control_pert = control.copy()
            control_pert[i] += eps
            x_dot_pert = self.dynamics(state, control_pert)
            B[:, i] = (x_dot_pert - x_dot_nom) / eps
        
        # Discrete time Jacobians
        A_discrete = np.eye(4) + A * self.config.dt
        B_discrete = B * self.config.dt
        
        return A_discrete, B_discrete
