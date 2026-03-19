#pragma once

#include <Eigen/Dense>
#include "Params/config.h"
#include "integration_methods.h"

/**
 * @file bicycle_model.h
 * @brief Kinematic Bicycle Model for Vehicle Dynamics
 * 
 * STATE: x = [x, y, theta, delta, v]
 *   - x, y: Position (m)
 *   - theta: Heading (rad)
 *   - delta: Steering angle (rad)
 *   - v: Velocity (m/s)
 * 
 * CONTROL: u = [a, delta_dot]
 *   - a: Acceleration (m/s²)
 *   - delta_dot: Steering rate (rad/s)
 * 
 * EQUATIONS:
 *   dx/dt = v * cos(theta)
 *   dy/dt = v * sin(theta)
 *   dtheta/dt = (v / wheelbase) * tan(delta)
 *   ddelta/dt = delta_dot
 */
class BicycleModel {
public:
    explicit BicycleModel(const MPCConfig& config);
    
    Eigen::VectorXd dynamics(const Eigen::VectorXd& state, 
                             const Eigen::Vector2d& control) const;
    
    Eigen::VectorXd step(const Eigen::VectorXd& state,
                        const Eigen::Vector2d& control,
                        double dt = -1.0) const;
    
    Eigen::VectorXd stepEulerForward(const Eigen::VectorXd& state,
                                     const Eigen::Vector2d& control,
                                     double dt = -1.0) const;
    
    Eigen::MatrixXd predictTrajectory(const Eigen::VectorXd& x0,
                                      const Eigen::MatrixXd& controls) const;
    
    void linearize(const Eigen::VectorXd& state,
                   const Eigen::Vector2d& control,
                   Eigen::MatrixXd& A,
                   Eigen::MatrixXd& B) const;
    
    /// Convert throttle to acceleration: a = throttle * (1.25 + 0.2*v - 0.01*v²)
    double throttleToAcceleration(double throttle, double current_velocity) const;
    
    /// Validate steering angle (clamp to ±35°)
    double validateSteeringAngle(double steering_angle_rad) const;
    
    /// Validate throttle command (clamp to ±1.0)
    double validateThrottle(double throttle) const;

private:
    const MPCConfig& config_;
    
    static constexpr double LINEARIZE_EPS = 1e-6;
    
    // Control constraints from FSAI 2026
    static constexpr double MAX_STEERING_ANGLE_RAD = 0.6109;  // ±35 degrees
    static constexpr double MAX_THROTTLE = 1.0;
    
    // Throttle dynamics coefficients: a = throttle * (1.25 + 0.2*v - 0.01*v²)
    static constexpr double THROTTLE_BASE_COEFF = 1.25;
    static constexpr double THROTTLE_LINEAR_SPEED_COEFF = 0.2;
    static constexpr double THROTTLE_QUAD_SPEED_COEFF = 0.01;
};
