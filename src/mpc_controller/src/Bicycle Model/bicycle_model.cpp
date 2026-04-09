#include "bicycle_model.h"
#include <iostream>

/****************************************************
 * Kinematic Bicycle Model Implementation
 * ─────────────────────────────────────────────────
 * dx/dt = v*cos(theta)      →  state_dot(0) = v * cos(theta)
 * dy/dt = v*sin(theta)      →  state_dot(1) = v * sin(theta)
 * dtheta/dt = v*tan(δ)/L    →  state_dot(2) = (v/L) * tan(delta)
 * ddelta/dt = delta_dot     →  state_dot(3) = delta_dot
 * (acceleration implicit)   →  state_dot(4) = a
 */
namespace mpc_controller {

BicycleModel::BicycleModel(const Params& config)
    : params_(config)
{
}

Eigen::VectorXd BicycleModel::dynamics(const state& X,
                                       const control& U) const {
    double x = X.x;
    double y = X.y;
    double theta = X.theta;
    double delta = X.delta;
    double v = X.v;
    
    double a = U.D_dot;
    double delta_dot = U.delta_dot;
    
    Eigen::VectorXd X_dot = Eigen::VectorXd::Zero(5);
    X_dot(0) = v * std::cos(theta);
    X_dot(1) = v * std::sin(theta);
    X_dot(2) = (v / params_.wheelbase) * std::tan(delta);
    X_dot(3) = delta_dot;
    X_dot(4) = a;
    
    return X_dot;
}

Eigen::VectorXd BicycleModel::step(const state& X,
                                   const control& U,
                                   double dt) const {
    if (dt < 0) {
        dt = params_.dt;
    }

    // Convert state/control structs to plain Eigen vectors for the integrator
    Eigen::VectorXd x_vec(5);
    x_vec << X.x, X.y, X.theta, X.delta, X.v;
    Eigen::VectorXd u_vec(2);
    u_vec << U.D_dot, U.delta_dot;

    // Lambda adapts Eigen vectors back to state/control structs required by dynamics()
    auto dynamics_fn = [this](const Eigen::VectorXd& xv, const Eigen::VectorXd& uv) {
        state Xs;  Xs.x = xv(0); Xs.y = xv(1); Xs.theta = xv(2); Xs.delta = xv(3); Xs.v = xv(4);
        control Us; Us.D_dot = uv(0); Us.delta_dot = uv(1); Us.dV_ghost = 0.0;
        return this->dynamics(Xs, Us);
    };

    return integration::rungeKutta4<5, 2>(x_vec, u_vec, dynamics_fn, dt);
}

Eigen::VectorXd BicycleModel::stepEulerForward(const state& X,
                                               const control& U,
                                               double dt) const {
    if (dt < 0) {
        dt = params_.dt;
    }

    // Convert state/control structs to plain Eigen vectors for the integrator
    Eigen::VectorXd x_vec(5);
    x_vec << X.x, X.y, X.theta, X.delta, X.v;
    Eigen::VectorXd u_vec(2);
    u_vec << U.D_dot, U.delta_dot;

    // Lambda adapts Eigen vectors back to state/control structs required by dynamics()
    auto dynamics_fn = [this](const Eigen::VectorXd& xv, const Eigen::VectorXd& uv) {
        state Xs;  Xs.x = xv(0); Xs.y = xv(1); Xs.theta = xv(2); Xs.delta = xv(3); Xs.v = xv(4);
        control Us; Us.D_dot = uv(0); Us.delta_dot = uv(1); Us.dV_ghost = 0.0;
        return this->dynamics(Xs, Us);
    };

    return integration::eulerForward<5, 2>(x_vec, u_vec, dynamics_fn, dt);
}

Eigen::MatrixXd BicycleModel::predictTrajectory(const state& X0,
                                                const Eigen::MatrixXd& controls) const {
    // Convert initial state struct to 5-element vector for the integrator
    Eigen::VectorXd x0_vec(5);
    x0_vec << X0.x, X0.y, X0.theta, X0.delta, X0.v;

    // Lambda adapts Eigen vectors back to state/control structs required by dynamics()
    auto dynamics_fn = [this](const Eigen::VectorXd& xv, const Eigen::VectorXd& uv) {
        state Xs;  Xs.x = xv(0); Xs.y = xv(1); Xs.theta = xv(2); Xs.delta = xv(3); Xs.v = xv(4);
        control Us; Us.D_dot = uv(0); Us.delta_dot = uv(1); Us.dV_ghost = 0.0;
        return this->dynamics(Xs, Us);
    };

    // Use RK4 integration (use_rk4=true) for better MPC prediction accuracy
    return integration::predictTrajectory(x0_vec, controls, dynamics_fn, params_.dt, true);
}

void BicycleModel::linearize(const state& X,
                            const control& U,
                            Eigen::MatrixXd& A,
                            Eigen::MatrixXd& B) const {
    // Pack state/control into plain vectors for numerical differentiation
    Eigen::VectorXd x_vec(5);
    x_vec << X.x, X.y, X.theta, X.delta, X.v;
    Eigen::VectorXd u_vec(2);
    u_vec << U.D_dot, U.delta_dot;

    // Helper: convert 5-element vector → state struct
    auto toState = [](const Eigen::VectorXd& xv) {
        state Xs; Xs.x = xv(0); Xs.y = xv(1); Xs.theta = xv(2); Xs.delta = xv(3); Xs.v = xv(4);
        return Xs;
    };
    // Helper: convert 2-element vector → control struct
    auto toControl = [](const Eigen::VectorXd& uv) {
        control Us; Us.D_dot = uv(0); Us.delta_dot = uv(1); Us.dV_ghost = 0.0;
        return Us;
    };

    Eigen::VectorXd x_dot_nom = dynamics(toState(x_vec), toControl(u_vec));

    // A matrix: ∂x_dot/∂state (5x5) - use perturbation from Params
    A = Eigen::MatrixXd::Zero(5, 5);
    for (int i = 0; i < 5; ++i) {
        Eigen::VectorXd x_pert = x_vec;
        x_pert(i) += params_.linearize_eps;     // From Params (motor_model.json)!
        Eigen::VectorXd x_dot_pert = dynamics(toState(x_pert), toControl(u_vec));
        A.col(i) = (x_dot_pert - x_dot_nom) / params_.linearize_eps;  // From Params!
    }

    // B matrix: ∂x_dot/∂control (5x2) - use perturbation from Params
    B = Eigen::MatrixXd::Zero(5, 2);
    for (int i = 0; i < 2; ++i) {
        Eigen::VectorXd u_pert = u_vec;
        u_pert(i) += params_.linearize_eps;     // From Params (motor_model.json)!
        Eigen::VectorXd x_dot_pert = dynamics(toState(x_vec), toControl(u_pert));
        B.col(i) = (x_dot_pert - x_dot_nom) / params_.linearize_eps;  // From Params!
    }

    // Discrete time Jacobians (zero-order hold)
    A = Eigen::MatrixXd::Identity(5, 5) + A * params_.dt;
    B = B * params_.dt;
}

double BicycleModel::throttleToAcceleration(double throttle, double current_velocity) const {
    // Motor dynamics model (formula from Params - ALL constants from JSON files)
    // a = throttle * (Bm1 + Bm2*v - Bm3*v²)
    // 
    // This maps throttle command to realistic acceleration using motor dynamics model
    // that captures speed-dependent effects.
    //
    // Key insight for Formula Student:
    // - At v=0: a = throttle * Bm1  (maximum acceleration)
    // - As v increases: linear term (Bm2*v) reduces effect, quadratic term kills acceleration
    // - Captures realistic throttle response at different speeds
    
    // Clamp throttle to valid range (from Params)
    double throttle_valid = validateThrottle(throttle);
    
    // Apply throttle-to-acceleration formula using ONLY Params constants
    double v = current_velocity;
    double acceleration = throttle_valid * (
        params_.Bm1 +                    // Base coefficient from Params (vehicle parameters)
        params_.Bm2 * v -                // Linear speed coefficient from Params (vehicle parameters)
        params_.Bm3 * v * v              // Quadratic speed coefficient from Params (vehicle parameters)
    );
    
    return acceleration;
}

double BicycleModel::validateSteeringAngle(double steering_angle_rad) const {
    // Validate against steering limit from Params
    // All constraint values come from JSON files (constraints.json)
    
    double clamped_angle = steering_angle_rad;
    
    if (std::abs(clamped_angle) > params_.delta_max) {    // From Params (constraints.json)!
        std::cerr << "WARNING: Steering angle " << clamped_angle * 180.0 / M_PI 
                  << "° exceeds ±" << params_.delta_max * 180.0 / M_PI 
                  << "°, clamping to limit" << std::endl;
        
        // Clamp to valid range (from Params)
        if (clamped_angle > params_.delta_max) {         // From Params (constraints.json)!
            clamped_angle = params_.delta_max;
        } else if (clamped_angle < -params_.delta_max) { // From Params (constraints.json)!
            clamped_angle = -params_.delta_max;
        }
    }
    
    return clamped_angle;
}

double BicycleModel::validateThrottle(double throttle) const {
    // Validate against throttle limit from Params
    // All constraint values come from JSON files (motor_model.json)
    
    double clamped_throttle = throttle;
    
    if (std::abs(clamped_throttle) > params_.throttle_max) {  // From Params (motor_model.json)!
        std::cerr << "WARNING: Throttle " << clamped_throttle 
                  << " exceeds ±" << params_.throttle_max   // From Params (motor_model.json)!
                  << ", clamping to limit" << std::endl;
        
        // Clamp to valid range (from Params)
        if (clamped_throttle > params_.throttle_max) {        // From Params (motor_model.json)!
            clamped_throttle = params_.throttle_max;
        } else if (clamped_throttle < -params_.throttle_max) {  // From Params (motor_model.json)!
            clamped_throttle = -params_.throttle_max;
        }
    }
    
    return clamped_throttle;
}

} // namespace mpc_controller