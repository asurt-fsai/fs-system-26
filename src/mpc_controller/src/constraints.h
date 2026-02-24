#pragma once

#include <Eigen/Dense>
#include "config.h"

/**
 * @brief Constraint definitions for MPC
 */
class ConstraintSet {
public:
    explicit ConstraintSet(const MPCConfig& config);
    
    /**
     * @brief Get input bounds (static - constant for all steps)
     * 
     * @return Pair of (lower_bounds, upper_bounds), each shape (horizon, 2)
     */
    std::pair<Eigen::MatrixXd, Eigen::MatrixXd> getInputBounds() const;
    
    /**
     * @brief Get dynamic input bounds based on curve radius
     * 
     * Limits velocity based on turning radius to prevent excessive lateral acceleration:
     * R = wheelbase / tan(delta)
     * v_max = sqrt(a_max_lateral * R)
     * 
     * This prevents the car from going too fast while turning.
     * Physically realistic: tighter curves → lower speed limits.
     * 
     * @param trajectory Predicted trajectory with steering angles in column 3
     * @return Pair of (lower_bounds, upper_bounds), each shape (horizon, 2)
     */
    std::pair<Eigen::MatrixXd, Eigen::MatrixXd> getDynamicInputBounds(
        const Eigen::MatrixXd& trajectory) const;
    
    /**
     * @brief Get state bounds
     * 
     * @return Pair of (lower_bounds, upper_bounds), each shape (horizon+1, 4)
     */
    std::pair<Eigen::MatrixXd, Eigen::MatrixXd> getStateBounds() const;
    
    /**
     * @brief Check if state-control pair satisfies constraints
     * 
     * @param state Current state
     * @param control Control input
     * @return true if feasible
     */
    bool checkFeasibility(const Eigen::Vector4d& state,
                         const Eigen::Vector2d& control) const;

private:
    const MPCConfig& config_;
};
