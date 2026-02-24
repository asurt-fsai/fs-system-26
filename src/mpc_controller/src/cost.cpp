#include "Cost.h"
#include "utils.h"
#include <cmath>
#include <stdexcept>

Cost::Cost(const MPCConfig& config) : config_(config) {
    // Initialize with default weight matrices from config
    Q_ = config_.Q;
    R_ = config_.R;
    Q_terminal_ = config_.Q_terminal;
}

double Cost::stageCost(const Eigen::VectorXd& state,
                       const Eigen::VectorXd& reference_state,
                       const Eigen::Vector2d& control) const {
    
    if (state.size() < STATE_DIM || reference_state.size() < STATE_DIM) {
        throw std::invalid_argument("State vector must have at least 4 elements");
    }
    
    // Compute state error with angle wrapping
    Eigen::VectorXd error = stateError(state, reference_state);
    
    // State tracking cost: (x - x_ref)^T * Q * (x - x_ref)
    double state_cost = error.head(STATE_DIM).transpose() * Q_ * error.head(STATE_DIM);
    
    // Control effort cost: u^T * R * u
    double control_cost = control.transpose() * R_ * control;
    
    return state_cost + control_cost;
}

double Cost::terminalCost(const Eigen::VectorXd& final_state,
                          const Eigen::VectorXd& reference_state) const {
    
    if (final_state.size() < STATE_DIM || reference_state.size() < STATE_DIM) {
        throw std::invalid_argument("State vector must have at least 4 elements");
    }
    
    // Compute state error with angle wrapping
    Eigen::VectorXd error = stateError(final_state, reference_state);
    
    // Terminal cost: (x_N - x_ref_N)^T * Q_terminal * (x_N - x_ref_N)
    double terminal_cost = error.head(STATE_DIM).transpose() * Q_terminal_ * error.head(STATE_DIM);
    
    return terminal_cost;
}

double Cost::trajectoryCost(const Eigen::MatrixXd& trajectory,
                            const Eigen::MatrixXd& controls,
                            const Eigen::MatrixXd& reference_trajectory) const {
    
    if (trajectory.rows() != reference_trajectory.rows()) {
        throw std::invalid_argument("Trajectory and reference must have same number of rows");
    }
    
    if (controls.rows() != trajectory.rows() - 1) {
        throw std::invalid_argument("Controls must have horizon length rows");
    }
    
    double total_cost = 0.0;
    int horizon = controls.rows();
    
    // Sum stage costs
    for (int i = 0; i < horizon; ++i) {
        Eigen::VectorXd state = trajectory.row(i).transpose();
        Eigen::VectorXd reference = reference_trajectory.row(i).transpose();
        Eigen::Vector2d control = controls.row(i).transpose();
        
        total_cost += stageCost(state, reference, control);
    }
    
    // Add terminal cost
    Eigen::VectorXd final_state = trajectory.row(horizon).transpose();
    Eigen::VectorXd final_reference = reference_trajectory.row(horizon).transpose();
    total_cost += terminalCost(final_state, final_reference);
    
    return total_cost;
}

double Cost::trackingCost(const Eigen::MatrixXd& trajectory,
                         const Eigen::MatrixXd& reference_trajectory) const {
    
    if (trajectory.rows() != reference_trajectory.rows()) {
        throw std::invalid_argument("Trajectory and reference must have same number of rows");
    }
    
    double total_cost = 0.0;
    int horizon = trajectory.rows() - 1;
    
    // Sum stage tracking costs (excluding control cost)
    for (int i = 0; i < horizon; ++i) {
        Eigen::VectorXd state = trajectory.row(i).transpose();
        Eigen::VectorXd reference = reference_trajectory.row(i).transpose();
        
        Eigen::VectorXd error = stateError(state, reference);
        total_cost += error.head(STATE_DIM).transpose() * Q_ * error.head(STATE_DIM);
    }
    
    // Add terminal tracking cost
    Eigen::VectorXd final_state = trajectory.row(horizon).transpose();
    Eigen::VectorXd final_reference = reference_trajectory.row(horizon).transpose();
    Eigen::VectorXd final_error = stateError(final_state, final_reference);
    total_cost += final_error.head(STATE_DIM).transpose() * Q_terminal_ * final_error.head(STATE_DIM);
    
    return total_cost;
}

double Cost::controlCost(const Eigen::MatrixXd& controls) const {
    
    double total_cost = 0.0;
    
    for (int i = 0; i < controls.rows(); ++i) {
        Eigen::Vector2d control = controls.row(i).transpose();
        total_cost += control.transpose() * R_ * control;
    }
    
    return total_cost;
}

Eigen::VectorXd Cost::stateError(const Eigen::VectorXd& state,
                                const Eigen::VectorXd& reference_state) const {
    
    if (state.size() < STATE_DIM || reference_state.size() < STATE_DIM) {
        throw std::invalid_argument("State vectors must have at least 4 elements");
    }
    
    Eigen::VectorXd error = state.head(STATE_DIM) - reference_state.head(STATE_DIM);
    
    // Wrap angle error to [-π, π] (theta is at index 2)
    // error(2) = theta_error
    error(2) = mpc_utils::wrapAngle(error(2));
    
    return error;
}

void Cost::setWeights(const Eigen::Matrix4d& Q,
                     const Eigen::Matrix2d& R,
                     const Eigen::Matrix4d& Q_terminal) {
    
    Q_ = Q;
    R_ = R;
    Q_terminal_ = Q_terminal;
}

void Cost::getCostBreakdown(const Eigen::MatrixXd& trajectory,
                           const Eigen::MatrixXd& controls,
                           const Eigen::MatrixXd& reference_trajectory,
                           double& tracking_cost,
                           double& control_cost,
                           double& terminal_cost) const {
    
    if (trajectory.rows() != reference_trajectory.rows()) {
        throw std::invalid_argument("Trajectory and reference must have same number of rows");
    }
    
    if (controls.rows() != trajectory.rows() - 1) {
        throw std::invalid_argument("Controls must have horizon length rows");
    }
    
    tracking_cost = 0.0;
    control_cost = 0.0;
    terminal_cost = 0.0;
    
    int horizon = controls.rows();
    
    // Accumulate stage costs
    for (int i = 0; i < horizon; ++i) {
        Eigen::VectorXd state = trajectory.row(i).transpose();
        Eigen::VectorXd reference = reference_trajectory.row(i).transpose();
        Eigen::Vector2d ctrl = controls.row(i).transpose();
        
        // Tracking component
        Eigen::VectorXd error = stateError(state, reference);
        tracking_cost += error.head(STATE_DIM).transpose() * Q_ * error.head(STATE_DIM);
        
        // Control component
        control_cost += ctrl.transpose() * R_ * ctrl;
    }
    
    // Terminal cost
    Eigen::VectorXd final_state = trajectory.row(horizon).transpose();
    Eigen::VectorXd final_reference = reference_trajectory.row(horizon).transpose();
    Eigen::VectorXd final_error = stateError(final_state, final_reference);
    terminal_cost = final_error.head(STATE_DIM).transpose() * Q_terminal_ * final_error.head(STATE_DIM);
}
