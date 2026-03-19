#include "mpc_controller/simulator_model.h"
#include <cmath>
#include <iostream>

SimulatorModel::SimulatorModel(const MPCConfig& config) 
    : config_(config) {
    // Initialize state vector [x, y, theta, delta, v]
    latest_state_ = Eigen::VectorXd::Zero(5);
}

void SimulatorModel::setLatestState(const Eigen::VectorXd& state) {
    if (state.size() != 5) {
        std::cerr << "ERROR: SimulatorModel expects state size 5 [x, y, theta, delta, v], "
                  << "got " << state.size() << std::endl;
        return;
    }
    latest_state_ = state;
}

Eigen::VectorXd SimulatorModel::getLatestState() const {
    return latest_state_;
}

Eigen::MatrixXd SimulatorModel::predictTrajectory(const Eigen::VectorXd& x0,
                                                   const Eigen::MatrixXd& controls) const {
    // In simulator mode, we don't predict - we use ground-truth from simulator
    // Return single state for compatibility with MPC interface
    int horizon = controls.rows();
    Eigen::MatrixXd trajectory(horizon + 1, 5);
    
    // Fill trajectory with latest simulator state
    // In practice, you would fill this with buffered simulator predictions
    for (int i = 0; i <= horizon; ++i) {
        trajectory.row(i) = latest_state_.transpose();
    }
    
    return trajectory;
}

void SimulatorModel::linearize(const Eigen::VectorXd& state,
                               const Eigen::VectorXd& control,
                               Eigen::MatrixXd& A,
                               Eigen::MatrixXd& B) const {
    // Extract state components
    // state = [x, y, theta, delta, v]
    double theta = state(2);
    double delta = state(3);
    double v = state(4);
    
    // Extract control components
    // control = [a, delta_dot] (acceleration and steering rate)
    double a = control(0);
    double delta_dot = control(1);
    
    // ============================================================================
    // LINEARIZED DYNAMICS (Extended model with velocity as state)
    // ============================================================================
    // 
    // State: [x, y, theta, delta, v]
    // Control: [a, delta_dot]
    //
    // Continuous dynamics:
    // dx/dt = v * cos(theta)
    // dy/dt = v * sin(theta)
    // dtheta/dt = (v / wheelbase) * tan(delta)
    // ddelta/dt = delta_dot
    // dv/dt = a
    //
    // Jacobian A = ∂f/∂x (5×5):
    A = Eigen::MatrixXd::Zero(5, 5);
    A(0, 2) = -v * std::sin(theta);      // ∂(dx/dt)/∂theta
    A(0, 4) = std::cos(theta);           // ∂(dx/dt)/∂v
    
    A(1, 2) = v * std::cos(theta);       // ∂(dy/dt)/∂theta
    A(1, 4) = std::sin(theta);           // ∂(dy/dt)/∂v
    
    double tan_delta = std::tan(delta);
    double sec_sq_delta = 1.0 / (std::cos(delta) * std::cos(delta));
    A(2, 3) = (v / config_.wheelbase) * sec_sq_delta;  // ∂(dtheta/dt)/∂delta
    A(2, 4) = tan_delta / config_.wheelbase;           // ∂(dtheta/dt)/∂v
    
    // delta and v don't depend on any state
    // (ddelta/dt = delta_dot, dv/dt = a)
    
    // Convert to discrete time Jacobian
    A = Eigen::MatrixXd::Identity(5, 5) + A * config_.dt;
    
    // ============================================================================
    // JACOBIAN B = ∂f/∂u (5×2):
    // ============================================================================
    //
    // ∂(dx/dt)/∂a = 0,           ∂(dx/dt)/∂delta_dot = 0
    // ∂(dy/dt)/∂a = 0,           ∂(dy/dt)/∂delta_dot = 0
    // ∂(dtheta/dt)/∂a = 0,       ∂(dtheta/dt)/∂delta_dot = 0
    // ∂(ddelta/dt)/∂a = 0,       ∂(ddelta/dt)/∂delta_dot = 1
    // ∂(dv/dt)/∂a = 1,           ∂(dv/dt)/∂delta_dot = 0
    //
    B = Eigen::MatrixXd::Zero(5, 2);
    B(3, 1) = 1.0;  // ddelta/dt = delta_dot
    B(4, 0) = 1.0;  // dv/dt = a
    
    // Convert to discrete time Jacobian
    B = B * config_.dt;
}
