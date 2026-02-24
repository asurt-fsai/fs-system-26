#include "bicycle_model.h"
#include "integration_methods.h"
#include <cmath>

/**
 * ============================================================================
 * BICYCLE MODEL C++ IMPLEMENTATION
 * ============================================================================
 * 
 * This C++ implementation is BASED ON the Python reference model:
 * kinematic_bicycle/bicycle_model.py
 * 
 * KEY DIFFERENCES:
 * - Python version: 4-state model [x, y, theta, delta]
 *                  Velocity is implicitly managed through throttle mapping
 * - C++ version:    5-state model [x, y, theta, delta, v]
 *                  Velocity is explicit state for MPC optimization
 * 
 * SHARED FEATURES:
 * ✓ Same kinematic bicycle model equations
 * ✓ Control constraints: Steering ±35°, Throttle ±1.0
 * ✓ Throttle dynamics: a = throttle * (1.25 + 0.2*v - 0.01*v²)
 * ✓ RK4 integration (C++) vs Euler integration (Python)
 * 
 * REFERENCE MAPPING:
 * Python dynamics.py        →  C++ bicycle_model.cpp
 * ─────────────────────────────────────────────────
 * dx/dt = v*cos(theta)      →  state_dot(0) = v * cos(theta)
 * dy/dt = v*sin(theta)      →  state_dot(1) = v * sin(theta)
 * dtheta/dt = v*tan(δ)/L    →  state_dot(2) = (v/L) * tan(delta)
 * ddelta/dt = delta_dot     →  state_dot(3) = delta_dot
 * (acceleration implicit)   →  state_dot(4) = a [NEW: velocity as state]
 * 
 * ============================================================================
 */

BicycleModel::BicycleModel(const MPCConfig& config) : config_(config) {}

Eigen::VectorXd BicycleModel::dynamics(const Eigen::VectorXd& state,
                                       const Eigen::Vector2d& control) const {
    // REFERENCE: kinematic_bicycle/bicycle_model.py - updateXDot() method
    // 
    // This implements the standard kinematic bicycle model equations:
    //
    // STATE INDICES:
    // state(0) = x       : Global X position (meters)
    // state(1) = y       : Global Y position (meters)
    // state(2) = theta   : Heading/yaw angle (radians)
    // state(3) = delta   : Steering angle of front wheel (radians)
    // state(4) = v       : Longitudinal velocity (m/s)
    //
    // CONTROL INDICES:
    // control(0) = a        : Longitudinal acceleration (m/s²)
    // control(1) = delta_dot: Steering angle rate (rad/s)
    //
    // KINEMATIC EQUATIONS (corresponding to Python implementation):
    // ───────────────────────────────────────────────────────────
    // x_dot = v * cos(theta)
    //         ↳ Horizontal motion based on heading and speed
    //
    // y_dot = v * sin(theta)
    //         ↳ Vertical motion based on heading and speed
    //
    // theta_dot = (v / wheelbase) * tan(delta)
    //             ↳ Yaw rate from bicycle steering geometry
    //             ↳ Larger steering angle → faster turning
    //             ↳ Larger wheelbase → slower turning (more stable)
    //
    // delta_dot = delta_dot_command
    //             ↳ Steering angle changes at commanded rate
    //
    // v_dot = a
    //         ↳ Velocity changes based on acceleration
    //         ↳ NOTE: In Python, 'a' comes from throttle mapping
    //                 a = throttle * (1.25 + 0.2*v - 0.01*v²)
    
    double x = state(0);
    double y = state(1);
    double theta = state(2);
    double delta = state(3);
    double v = state(4);
    
    double a = control(0);
    double delta_dot = control(1);
    
    Eigen::VectorXd state_dot = Eigen::VectorXd::Zero(5);
    state_dot(0) = v * std::cos(theta);
    state_dot(1) = v * std::sin(theta);
    state_dot(2) = (v / config_.wheelbase) * std::tan(delta);
    state_dot(3) = delta_dot;
    state_dot(4) = a;
    
    return state_dot;
}

Eigen::VectorXd BicycleModel::step(const Eigen::VectorXd& state,
                                   const Eigen::Vector2d& control,
                                   double dt) const {
    if (dt < 0) {
        dt = config_.dt;
    }
    
    // Use RK4 integration from integration_methods.h
    // Bind the dynamics function to this->dynamics for the integration solver
    auto dynamics_fn = [this](const Eigen::VectorXd& s, const Eigen::VectorXd& u) {
        return this->dynamics(s, Eigen::Vector2d(u(0), u(1)));
    };
    
    return integration::rungeKutta4<5, 2>(state, control, dynamics_fn, dt);
}

Eigen::VectorXd BicycleModel::stepEulerForward(const Eigen::VectorXd& state,
                                               const Eigen::Vector2d& control,
                                               double dt) const {
    if (dt < 0) {
        dt = config_.dt;
    }
    
    // Use Euler Forward integration from integration_methods.h
    // This is the integration method used in the Python bicycle_model.py
    auto dynamics_fn = [this](const Eigen::VectorXd& s, const Eigen::VectorXd& u) {
        return this->dynamics(s, Eigen::Vector2d(u(0), u(1)));
    };
    
    return integration::eulerForward<5, 2>(state, control, dynamics_fn, dt);
}

Eigen::MatrixXd BicycleModel::predictTrajectory(const Eigen::VectorXd& x0,
                                                const Eigen::MatrixXd& controls) const {
    // Use the integration methods framework for trajectory prediction
    // Bind the dynamics function for the integration solver
    auto dynamics_fn = [this](const Eigen::VectorXd& s, const Eigen::VectorXd& u) {
        return this->dynamics(s, Eigen::Vector2d(u(0), u(1)));
    };
    
    // Use RK4 integration (use_rk4=true) for better MPC prediction accuracy
    return integration::predictTrajectory(x0, controls, dynamics_fn, config_.dt, true);
}

void BicycleModel::linearize(const Eigen::VectorXd& state,
                            const Eigen::Vector2d& control,
                            Eigen::MatrixXd& A,
                            Eigen::MatrixXd& B) const {
    Eigen::VectorXd x_dot_nom = dynamics(state, control);
    
    // A matrix: ∂x_dot/∂state (5x5)
    A = Eigen::MatrixXd::Zero(5, 5);
    for (int i = 0; i < 5; ++i) {
        Eigen::VectorXd state_pert = state;
        state_pert(i) += LINEARIZE_EPS;
        Eigen::VectorXd x_dot_pert = dynamics(state_pert, control);
        A.col(i) = (x_dot_pert - x_dot_nom) / LINEARIZE_EPS;
    }
    
    // B matrix: ∂x_dot/∂control (5x2)
    B = Eigen::MatrixXd::Zero(5, 2);
    for (int i = 0; i < 2; ++i) {
        Eigen::Vector2d control_pert = control;
        control_pert(i) += LINEARIZE_EPS;
        Eigen::VectorXd x_dot_pert = dynamics(state, control_pert);
        B.col(i) = (x_dot_pert - x_dot_nom) / LINEARIZE_EPS;
    }
    
    // Discrete time Jacobians
    A = Eigen::MatrixXd::Identity(5, 5) + A * config_.dt;
    B = B * config_.dt;
}

double BicycleModel::throttleToAcceleration(double throttle, double current_velocity) const {
    // REFERENCE: From kinematic_bicycle/bicycle_model.py Python implementation
    // Line: a = msg.data*(1.25 + 0.2*self.u[0] - 0.01*(self.u[0]**2))
    // 
    // This maps throttle command to realistic acceleration using motor dynamics model
    // that captures speed-dependent effects.
    
    // Clamp throttle to valid range
    double throttle_valid = validateThrottle(throttle);
    
    // Apply throttle dynamics formula:
    // a = throttle * (1.25 + 0.2*v - 0.01*v²)
    double v = current_velocity;
    double acceleration = throttle_valid * (
        THROTTLE_BASE_COEFF + 
        THROTTLE_LINEAR_SPEED_COEFF * v - 
        THROTTLE_QUAD_SPEED_COEFF * v * v
    );
    
    return acceleration;
}

double BicycleModel::validateSteeringAngle(double steering_angle_rad) const {
    // REFERENCE: From kinematic_bicycle/bicycle_model.py
    // Lines: if (abs(msg.data) > 35): ... self.destroy_node()
    // 
    // FSAI 2026 control constraint: Steering limited to ±35 degrees
    
    double clamped_angle = steering_angle_rad;
    
    if (std::abs(clamped_angle) > MAX_STEERING_ANGLE_RAD) {
        // Log warning (in actual ROS context, would use node logger)
        // logger.warning(f"Steering angle {clamped_angle*180/pi}° exceeds ±35°, clamping")
        
        // Clamp to valid range
        if (clamped_angle > MAX_STEERING_ANGLE_RAD) {
            clamped_angle = MAX_STEERING_ANGLE_RAD;
        } else if (clamped_angle < -MAX_STEERING_ANGLE_RAD) {
            clamped_angle = -MAX_STEERING_ANGLE_RAD;
        }
    }
    
    return clamped_angle;
}

double BicycleModel::validateThrottle(double throttle) const {
    // REFERENCE: From kinematic_bicycle/bicycle_model.py
    // Lines: if (abs(msg.data) > 1.0): ... self.destroy_node()
    // 
    // FSAI 2026 control constraint: Throttle limited to [-1.0, 1.0]
    
    double clamped_throttle = throttle;
    
    if (std::abs(clamped_throttle) > MAX_THROTTLE) {
        // Log warning (in actual ROS context, would use node logger)
        // logger.warning(f"Throttle {clamped_throttle} exceeds ±1.0, clamping")
        
        // Clamp to valid range
        if (clamped_throttle > MAX_THROTTLE) {
            clamped_throttle = MAX_THROTTLE;
        } else if (clamped_throttle < -MAX_THROTTLE) {
            clamped_throttle = -MAX_THROTTLE;
        }
    }
    
    return clamped_throttle;
}

