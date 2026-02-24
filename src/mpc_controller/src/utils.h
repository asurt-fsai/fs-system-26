#pragma once

#include <Eigen/Dense>
#include <cmath>

/**
 * @brief Utility functions for MPC
 */
namespace mpc_utils {

/**
 * @brief Wrap angle to [-pi, pi]
 */
double wrapAngle(double angle);

/**
 * @brief Compute state tracking error with angle wrapping
 * 
 * @param state Current state
 * @param reference Reference state
 * @return Error with wrapped angles
 */
Eigen::Vector4d getReferenceError(const Eigen::Vector4d& state,
                                  const Eigen::Vector4d& reference);

/**
 * @brief Saturate value to bounds
 */
double saturate(double value, double min_val, double max_val);

/**
 * @brief Apply rate limit to control change
 * 
 * @param current Current value
 * @param desired Desired value
 * @param rate_limit Maximum change per second
 * @param dt Time step
 * @return Rate-limited value
 */
double rateLimit(double current, double desired, double rate_limit, double dt);

}  // namespace mpc_utils
