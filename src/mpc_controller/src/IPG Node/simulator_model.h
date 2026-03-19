#pragma once

#include <Eigen/Dense>
#include "config.h"

/**
 * @file simulator_model.h
 * @brief Simulator State Provider for Direct State Input
 * 
 * Provides a lightweight interface for using simulator-published car states directly
 * without computing dynamics via the bicycle model. This is useful when:
 * 
 * - Using an external simulator (e.g., CARLA, LGSVL, Gazebo) that publishes states
 * - The simulator already handles vehicle dynamics internally
 * - You want MPC to work with ground-truth simulator states
 * - Testing control algorithms without kinematic approximations
 * 
 * ============================================================================
 * USAGE
 * ============================================================================
 * 
 * Instead of BicycleModel that computes dynamics:
 *   BicycleModel model(config);
 *   state = model.step(state, control, dt);
 * 
 * Use SimulatorModel to pass through published states:
 *   SimulatorModel sim_model(config);
 *   state = sim_model.getLatestState();  // From simulator subscription
 * 
 * ============================================================================
 * STATE VECTOR
 * ============================================================================
 * 
 * Same as BicycleModel for compatibility:
 * x = [x, y, theta, delta, v]
 * 
 * - x: Global frame X position (meters)
 * - y: Global frame Y position (meters)
 * - theta: Vehicle heading/yaw angle (radians)
 * - delta: Steering angle (radians)
 * - v: Longitudinal velocity (m/s)
 * 
 * These are received directly from the simulator, not computed.
 */
class SimulatorModel {
public:
    /**
     * @brief Constructor - Initialize simulator model
     * 
     * @param config Vehicle configuration (mainly for compatibility)
     */
    explicit SimulatorModel(const MPCConfig& config);
    
    /**
     * @brief Set the latest state from simulator subscription
     * 
     * Called by ROS subscriber when simulator publishes new state.
     * Stores the state for use by MPC.
     * 
     * @param state: Eigen::VectorXd containing [x, y, theta, delta, v]
     *   - state(0): X position (m)
     *   - state(1): Y position (m)
     *   - state(2): Heading angle (radians)
     *   - state(3): Steering angle (radians)
     *   - state(4): Velocity (m/s)
     */
    void setLatestState(const Eigen::VectorXd& state);
    
    /**
     * @brief Get the latest state published by simulator
     * 
     * @return: Eigen::VectorXd [x, y, theta, delta, v]
     *   - Direct pass-through of simulator state, no dynamics computation
     */
    Eigen::VectorXd getLatestState() const;
    
    /**
     * @brief Predict trajectory using pre-recorded simulator states
     * 
     * In simulator mode, you typically have access to ground-truth trajectory
     * from the simulator instead of predicting it. This is a placeholder that
     * returns the current state for MPC prediction (actual trajectory should
     * come from simulator buffering).
     * 
     * @param x0: Initial state (unused - uses internal simulator state)
     * @param controls: Control inputs (unused in pure pass-through mode)
     * @return: MatrixXd with single row = current state
     */
    Eigen::MatrixXd predictTrajectory(const Eigen::VectorXd& x0,
                                      const Eigen::MatrixXd& controls) const;
    
    /**
     * @brief Linearize dynamics around operating point
     * 
     * For compatibility with MPC solvers that need Jacobians.
     * Since we're using simulator states directly, linearization uses
     * the bicycle model dynamics as an approximation for the Jacobian.
     * 
     * @param state: State around which to linearize
     * @param control: Control input
     * @param A: Output state Jacobian (5×5)
     * @param B: Output input Jacobian (5×2)
     */
    void linearize(const Eigen::VectorXd& state,
                   const Eigen::VectorXd& control,
                   Eigen::MatrixXd& A,
                   Eigen::MatrixXd& B) const;
    
private:
    MPCConfig config_;
    Eigen::VectorXd latest_state_;  // Stores [x, y, theta, delta, v] from simulator
    
    static constexpr double LINEARIZE_EPS = 1e-6;  // For numerical differentiation
};
