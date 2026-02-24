#pragma once

#include <Eigen/Dense>
#include "config.h"

/**
 * @file Cost.h
 * @brief Cost function evaluation for Model Predictive Control
 * 
 * Implements the standard quadratic cost function for MPC:
 * J = sum(||x_i - x_ref||_Q^2 + ||u_i||_R^2) + ||x_N - x_ref_N||_Q_terminal^2
 * 
 * Where:
 * - x_i: State at step i
 * - x_ref_i: Reference state at step i
 * - u_i: Control input at step i
 * - Q: State tracking cost weight matrix (4x4)
 * - R: Control effort cost weight matrix (2x2)
 * - Q_terminal: Terminal state cost weight matrix (4x4)
 * - N: Prediction horizon length
 */
class Cost {
public:
    /**
     * @brief Constructor
     * 
     * @param config MPC configuration containing cost matrices
     */
    explicit Cost(const MPCConfig& config);
    
    /**
     * @brief Compute total stage cost at a specific time step
     * 
     * Computes: L_i = (x_i - x_ref_i)^T * Q * (x_i - x_ref_i) + u_i^T * R * u_i
     * 
     * @param state Current state [x, y, theta, delta, v]
     * @param reference_state Reference state [x, y, theta, delta, v]
     * @param control Control input [v, delta_dot]
     * 
     * @return Stage cost value (scalar)
     */
    double stageCost(const Eigen::VectorXd& state,
                     const Eigen::VectorXd& reference_state,
                     const Eigen::Vector2d& control) const;
    
    /**
     * @brief Compute terminal cost
     * 
     * Computes: L_N = (x_N - x_ref_N)^T * Q_terminal * (x_N - x_ref_N)
     * 
     * @param final_state Final predicted state [x, y, theta, delta, v]
     * @param reference_state Final reference state [x, y, theta, delta, v]
     * 
     * @return Terminal cost value (scalar)
     */
    double terminalCost(const Eigen::VectorXd& final_state,
                        const Eigen::VectorXd& reference_state) const;
    
    /**
     * @brief Compute total cost over full trajectory
     * 
     * Computes sum of all stage costs and terminal cost:
     * J = sum_{i=0}^{N-1} L_i + L_N
     * 
     * @param trajectory Predicted trajectory (N+1, 5) - includes velocity
     * @param controls Control sequence (N, 2)
     * @param reference_trajectory Reference trajectory (N+1, 5)
     * 
     * @return Total cost value (scalar)
     */
    double trajectoryCost(const Eigen::MatrixXd& trajectory,
                         const Eigen::MatrixXd& controls,
                         const Eigen::MatrixXd& reference_trajectory) const;
    
    /**
     * @brief Compute state tracking cost only (no control cost)
     * 
     * Useful for analyzing tracking performance separately
     * 
     * @param trajectory Predicted trajectory (N+1, 5)
     * @param reference_trajectory Reference trajectory (N+1, 5)
     * 
     * @return State tracking cost value (scalar)
     */
    double trackingCost(const Eigen::MatrixXd& trajectory,
                       const Eigen::MatrixXd& reference_trajectory) const;
    
    /**
     * @brief Compute control effort cost only
     * 
     * Useful for analyzing control energy separately
     * 
     * @param controls Control sequence (N, 2)
     * 
     * @return Control effort cost value (scalar)
     */
    double controlCost(const Eigen::MatrixXd& controls) const;
    
    /**
     * @brief Compute state error with angle wrapping
     * 
     * Handles circular nature of angles by wrapping to [-π, π]
     * 
     * @param state Current state (5D or 4D, only theta component used)
     * @param reference_state Reference state (same size as state)
     * 
     * @return State error vector with wrapped angle
     */
    Eigen::VectorXd stateError(const Eigen::VectorXd& state,
                              const Eigen::VectorXd& reference_state) const;
    
    /**
     * @brief Update cost weight matrices
     * 
     * @param Q New state weight matrix (4x4)
     * @param R New control weight matrix (2x2)
     * @param Q_terminal New terminal cost weight matrix (4x4)
     */
    void setWeights(const Eigen::Matrix4d& Q,
                   const Eigen::Matrix2d& R,
                   const Eigen::Matrix4d& Q_terminal);
    
    /**
     * @brief Get current state weight matrix
     * 
     * @return Reference to Q matrix
     */
    const Eigen::Matrix4d& getQ() const { return Q_; }
    
    /**
     * @brief Get current control weight matrix
     * 
     * @return Reference to R matrix
     */
    const Eigen::Matrix2d& getR() const { return R_; }
    
    /**
     * @brief Get current terminal weight matrix
     * 
     * @return Reference to Q_terminal matrix
     */
    const Eigen::Matrix4d& getQTerminal() const { return Q_terminal_; }
    
    /**
     * @brief Get cost breakdown for diagnostics
     * 
     * Returns detailed cost components
     * 
     * @param trajectory Predicted trajectory (N+1, 5)
     * @param controls Control sequence (N, 2)
     * @param reference_trajectory Reference trajectory (N+1, 5)
     * @param[out] tracking_cost Cumulative state tracking cost
     * @param[out] control_cost Cumulative control effort cost
     * @param[out] terminal_cost Final state cost
     */
    void getCostBreakdown(const Eigen::MatrixXd& trajectory,
                         const Eigen::MatrixXd& controls,
                         const Eigen::MatrixXd& reference_trajectory,
                         double& tracking_cost,
                         double& control_cost,
                         double& terminal_cost) const;

private:
    /// State cost weight matrix (4x4) - penalizes tracking error
    Eigen::Matrix4d Q_;
    
    /// Control cost weight matrix (2x2) - penalizes control effort
    Eigen::Matrix2d R_;
    
    /// Terminal state cost weight matrix (4x4) - penalizes final error
    Eigen::Matrix4d Q_terminal_;
    
    /// Reference to MPC configuration
    const MPCConfig& config_;
    
    /// State dimension (4: x, y, theta, delta - not including velocity)
    static constexpr int STATE_DIM = 4;
    
    /// Control dimension (2: v, delta_dot)
    static constexpr int CONTROL_DIM = 2;
};
