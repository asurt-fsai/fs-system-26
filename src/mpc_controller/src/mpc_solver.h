#pragma once

#include <Eigen/Dense>
#include "config.h"
#include "bicycle_model.h"

/**
 * @brief MPC Solver - Model Predictive Controller
 * 
 * Solves the optimal control problem:
 *   min J = sum(||x_i - x_ref||_Q^2 + ||u_i||_R^2)
 *   s.t. x_{i+1} = f(x_i, u_i)
 *        constraints on x, u
 */
class MPCSolver {
public:
    struct SolveInfo {
        bool success = false;
        int iterations = 0;
        double cost = 0.0;
        std::string message;
    };
    
    explicit MPCSolver(const MPCConfig& config);
    
    /**
     * @brief Solve MPC optimization problem
     * 
     * @param x0 Initial state
     * @param reference_trajectory Reference trajectory (horizon+1, 4)
     * @param x0_control Initial control guess (horizon, 2), uses last if empty
     * @param optimal_controls [out] Optimal control sequence
     * @param predicted_trajectory [out] Predicted trajectory
     * @return Solver information
     */
    SolveInfo solve(const Eigen::Vector4d& x0,
                    const Eigen::MatrixXd& reference_trajectory,
                    Eigen::MatrixXd& optimal_controls,
                    Eigen::MatrixXd& predicted_trajectory,
                    const Eigen::MatrixXd& x0_control = Eigen::MatrixXd());
    
    /**
     * @brief Get first control of optimal sequence (receding horizon)
     * 
     * @param x0 Current state
     * @param reference_trajectory Reference trajectory
     * @return First control [v, delta_dot]
     */
    Eigen::Vector2d getControl(const Eigen::Vector4d& x0,
                               const Eigen::MatrixXd& reference_trajectory);
    
    /**
     * @brief Update cost weights (for online tuning)
     * 
     * @param Q State cost matrix
     * @param R Control cost matrix
     * @param Q_terminal Terminal cost matrix (optional)
     */
    void setWeights(const Eigen::Matrix4d& Q,
                    const Eigen::Matrix2d& R,
                    const Eigen::Matrix4d& Q_terminal = Eigen::Matrix4d());
    
    /**
     * @brief Reset warm-start storage
     * 
     * Useful after large state jumps
     */
    void resetWarmStart();
    
    /**
     * @brief Get last solve information
     */
    const SolveInfo& getLastSolveInfo() const { return last_solve_info_; }

private:
    MPCConfig config_;
    BicycleModel model_;
    
    // Warm-start storage
    Eigen::MatrixXd last_control_sequence_;
    Eigen::MatrixXd last_trajectory_;
    SolveInfo last_solve_info_;
    
    /**
     * @brief Compute total cost
     */
    double computeCost(const Eigen::MatrixXd& trajectory,
                       const Eigen::MatrixXd& controls,
                       const Eigen::MatrixXd& reference_trajectory) const;
    
    /**
     * @brief Build parameter bounds for optimizer
     */
    std::vector<std::pair<double, double>> buildBounds() const;
};
