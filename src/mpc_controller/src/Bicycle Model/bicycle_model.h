#pragma once

#include <Eigen/Dense>
#include <cmath>
#include "../config.h"
#include "../Integrator/integration_methods.h"
#include "../Params/params.h"
#include "../types.h"

namespace mpc_controller {
/**
 * @file bicycle_model.h
 * @brief Kinematic Bicycle Model for Vehicle Dynamics
 * 
 * STATE: x = [x, y, theta, delta, v]
 *   - x, y: Position in global frame [m]
 *   - theta: Heading angle [rad]
 *   - delta: Steering angle of front wheels [rad]
 *   - v: Forward velocity [m/s]
 * 
 * CONTROL: u = [a, delta_dot]
 *   - a: Acceleration command [m/s²] - NOT velocity, NOT throttle
 *   - delta_dot: Steering angle rate [rad/s]
 * 
 * CONTROL SEMANTICS (ACCELERATION-BASED):
 *   - MPC directly commands acceleration (not velocity or throttle)
 *   - Constraints: -5 m/s² ≤ a ≤ 5 m/s²
 *   - Dynamics: v(t+dt) = v(t) + a(t) × dt
 * 
 * DYNAMICS EQUATIONS:
 *   dx/dt = v * cos(theta)
 *   dy/dt = v * sin(theta)
 *   dtheta/dt = (v / wheelbase) * tan(delta)
 *   ddelta/dt = delta_dot
 *   dv/dt = a  (velocity changes by acceleration)
 */
class BicycleModel {
public:
    BicycleModel(const Params& config);

    Eigen::VectorXd dynamics(const state& X,const control& U) const;
    Eigen::VectorXd step(const state& X, const control& U, double dt = -1.0) const;
    Eigen::VectorXd stepEulerForward(const state& X, const control& U, double dt = -1.0) const;
    Eigen::MatrixXd predictTrajectory(const state& X0, const Eigen::MatrixXd& controls) const;
    
    void linearize(const state& X,const control& U, Eigen::MatrixXd& A, Eigen::MatrixXd& B) const;
    
    /// Convert throttle to acceleration using motor model from Params
    /// Formula: a = throttle * (c0 + c1*v - c2*v²)
    /// All coefficients loaded from motor_model.json at startup:
    ///   - c0 = params_.throttle_coeff_0 (typically 1.25)
    ///   - c1 = params_.throttle_coeff_1 (typically 0.2)
    ///   - c2 = params_.throttle_coeff_2 (typically 0.01)
    double throttleToAcceleration(double throttle, double current_velocity) const;
    
    /// Validate steering angle against delta_max from Params
    /// Loaded from constraints.json at startup (typically 0.6109 rad = 35°)
    double validateSteeringAngle(double steering_angle_rad) const;
    
    /// Validate throttle command against throttle_max from Params
    /// Loaded from motor_model.json at startup (typically 1.0)
    double validateThrottle(double throttle) const;

private:
    // ============================================================================
    // NO HARDCODED CONSTANTS - All values come from JSON files loaded into Params!
    // ============================================================================
    // See params.cpp and JSON files for:
    //   - params_.linearize_eps (motor_model.json, ~1e-6 for numerical differentiation)
    //   - params_.wheelbase (vehicle.json, from bicycle model geometry)
    //   - params_.throttle_coeff_0/1/2 (motor_model.json, motor model coefficients)
    //   - params_.delta_max (constraints.json, maximum steering angle)
    //   - params_.throttle_max (motor_model.json, maximum throttle command)
    //
    // Single load pattern: All constants loaded ONE TIME via Params::loadAll()
    // in main.cpp at startup - see main.cpp for initialization example
    // ============================================================================

    Params params_;
};
} // namespace mpc_controller