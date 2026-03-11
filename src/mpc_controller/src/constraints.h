#pragma once

#include <Eigen/Dense>
#include "config.h"
#include "Arc_Spline.h"

/**
 * @brief Track constraint data structure
 * 
 * Represents a linear track boundary constraint of the form:
 * lower <= C * [x, y] <= upper
 */
struct TrackConstraint {
    Eigen::Matrix<double, 1, 2> C;  // Constraint Jacobian (1x2: [c_x, c_y])
    double lower;                    // Lower bound
    double upper;                    // Upper bound
};

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
     * @brief Get state bounds
     * 
     * @return Pair of (lower_bounds, upper_bounds), each shape (horizon+1, 4)
     */
    std::pair<Eigen::MatrixXd, Eigen::MatrixXd> getStateBounds() const;
    
    /**
     * @brief Get track boundary constraints at a given position
     * 
     * Computes linearized track constraints based on arc length position.
     * The constraint ensures the vehicle stays within track boundaries:
     * - Inner boundary: pos_inner = pos_center - r_in * tangent
     * - Outer boundary: pos_outer = pos_center + r_out * tangent
     * 
     * @param track Arc length parametrized track spline
     * @param s Arc length position on track
     * @param r_in Inner track width (distance from center to inner boundary)
     * @param r_out Outer track width (distance from center to outer boundary)
     * @return Track constraint structure with Jacobian and bounds
     */
    TrackConstraint getTrackConstraints(const mpc_controller::ArcSpline& track,
                                       double s, double r_in, double r_out) const;
    
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
