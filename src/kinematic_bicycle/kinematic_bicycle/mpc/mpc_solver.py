"""MPC Solver - Optimization and control computation

This is the core control logic, separated from ROS
"""

import numpy as np
from typing import Tuple, Optional
from scipy.optimize import minimize

from .config import MPCConfig
from .model import BicycleModel
from .constraints import ConstraintSet
from .utils import get_reference_error, wrap_angle


class MPCSolver:
    """Model Predictive Controller Solver
    
    Solves the optimal control problem:
        min J = sum(||x_i - x_ref||_Q^2 + ||u_i||_R^2)
        s.t. x_{i+1} = f(x_i, u_i)
             x, u constraints
    """
    
    def __init__(self, config: MPCConfig):
        """Initialize MPC solver
        
        Args:
            config: MPC configuration
        """
        self.config = config
        self.model = BicycleModel(config)
        self.constraints = ConstraintSet(config)
        
        # Store last solution for warm-starting
        self.last_control_sequence = np.zeros((config.horizon, 2))
        self.last_trajectory = None
        
        # For debugging
        self.last_solve_info = {}
    
    def solve(
        self,
        x0: np.ndarray,
        reference_trajectory: np.ndarray,
        x0_control: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray, dict]:
        """Solve MPC optimization problem
        
        Args:
            x0: Initial state [x, y, theta, delta]
            reference_trajectory: Reference trajectory (horizon+1, 4)
            x0_control: Initial control guess (horizon, 2), uses last if None
        
        Returns:
            optimal_controls: Control sequence (horizon, 2)
            predicted_trajectory: Predicted trajectory (horizon+1, 4)
            info: Dictionary with solver info (success, iterations, etc.)
        """
        # Use warm start or provided initial guess
        if x0_control is None:
            u0 = self.last_control_sequence.flatten()
        else:
            u0 = x0_control.flatten()
        
        # Build optimization problem
        bounds = self._build_bounds()
        
        # Objective function
        def objective(u_flat):
            trajectory = self.model.predict_trajectory(x0, u_flat.reshape(-1, 2))
            cost = self._compute_cost(trajectory, u_flat.reshape(-1, 2), reference_trajectory)
            return cost
        
        # Solve
        result = minimize(
            objective,
            u0,
            method='SLSQP',
            bounds=bounds,
            options={'maxiter': 100, 'ftol': 1e-6}
        )
        
        # Extract solution
        optimal_controls = result.x.reshape(-1, 2)
        predicted_trajectory = self.model.predict_trajectory(x0, optimal_controls)
        
        # Store for warm-starting next solve
        self.last_control_sequence = optimal_controls
        self.last_trajectory = predicted_trajectory
        
        # Info dict
        info = {
            'success': result.success,
            'iterations': result.nit,
            'function_value': result.fun,
            'message': result.message
        }
        self.last_solve_info = info
        
        return optimal_controls, predicted_trajectory, info
    
    def get_control(
        self,
        x0: np.ndarray,
        reference_trajectory: np.ndarray
    ) -> np.ndarray:
        """Get first control input of optimal sequence (receding horizon)
        
        Args:
            x0: Current state
            reference_trajectory: Reference trajectory (horizon+1, 4)
        
        Returns:
            control: First control [v, delta_dot]
        """
        controls, _, _ = self.solve(x0, reference_trajectory)
        return controls[0]
    
    def _build_bounds(self) -> list:
        """Build parameter bounds for optimizer
        
        Returns:
            bounds: List of (min, max) tuples for each control variable
        """
        u_lower, u_upper = self.constraints.get_input_bounds()
        
        bounds = []
        for i in range(self.config.horizon):
            bounds.append((u_lower[i, 0], u_upper[i, 0]))  # velocity
            bounds.append((u_lower[i, 1], u_upper[i, 1]))  # steering rate
        
        return bounds
    
    def _compute_cost(
        self,
        trajectory: np.ndarray,
        controls: np.ndarray,
        reference_trajectory: np.ndarray
    ) -> float:
        """Compute total cost
        
        Args:
            trajectory: Predicted trajectory (N+1, 4)
            controls: Control sequence (N, 2)
            reference_trajectory: Reference trajectory (N+1, 4)
        
        Returns:
            cost: Total cost value
        """
        cost = 0.0
        N = len(controls)
        
        # Stage costs
        for i in range(N):
            # State tracking error
            error = trajectory[i] - reference_trajectory[i]
            error[2] = wrap_angle(error[2])  # Wrap angle error
            
            state_cost = error @ self.config.Q @ error
            
            # Control effort
            control_cost = controls[i] @ self.config.R @ controls[i]
            
            cost += state_cost + control_cost
        
        # Terminal cost
        terminal_error = trajectory[-1] - reference_trajectory[-1]
        terminal_error[2] = wrap_angle(terminal_error[2])
        terminal_cost = terminal_error @ self.config.Q_terminal @ terminal_error
        cost += terminal_cost
        
        return cost
    
    def set_weights(self, Q: np.ndarray, R: np.ndarray, Q_terminal: np.ndarray = None):
        """Update cost weights
        
        Useful for tuning controller online
        
        Args:
            Q: State cost matrix
            R: Control cost matrix
            Q_terminal: Terminal cost matrix
        """
        self.config.Q = Q
        self.config.R = R
        if Q_terminal is not None:
            self.config.Q_terminal = Q_terminal
        else:
            self.config.Q_terminal = Q * 2
    
    def reset_warm_start(self):
        """Reset warm-start storage (useful after large state jumps)"""
        self.last_control_sequence = np.zeros((self.config.horizon, 2))
        self.last_trajectory = None
