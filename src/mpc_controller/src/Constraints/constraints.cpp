#include "constraints.h"
#include <cmath>

ConstraintSet::ConstraintSet(const MPCConfig& config) : config_(config) {}

std::pair<Eigen::MatrixXd, Eigen::MatrixXd> ConstraintSet::getInputBounds() const {
    int horizon = config_.horizon;
    
    Eigen::MatrixXd lower = Eigen::MatrixXd::Zero(horizon, 2);
    Eigen::MatrixXd upper = Eigen::MatrixXd::Zero(horizon, 2);
    
    // Static bounds (same for all steps)
    for (int i = 0; i < horizon; ++i) {
        lower(i, 0) = config_.v_min;        // Velocity min
        upper(i, 0) = config_.v_max;        // Velocity max
        
        lower(i, 1) = -config_.delta_dot_max;
        upper(i, 1) = config_.delta_dot_max;
    }
    
    return {lower, upper};
}

std::pair<Eigen::MatrixXd, Eigen::MatrixXd> ConstraintSet::getStateBounds() const {
    int horizon = config_.getPredictionSize();
    
    Eigen::MatrixXd lower = Eigen::MatrixXd::Constant(horizon, 4, -1e9);
    Eigen::MatrixXd upper = Eigen::MatrixXd::Constant(horizon, 4, 1e9);
    
    // Steering angle constraint: -delta_max <= delta <= delta_max
    lower.col(3).setConstant(-config_.delta_max);
    upper.col(3).setConstant(config_.delta_max);
    
    return {lower, upper};
}



bool ConstraintSet::checkFeasibility(const Eigen::Vector4d& state,
                                     const Eigen::Vector2d& control) const {
    // Steering angle constraint
    if (state(3) < -config_.delta_max || state(3) > config_.delta_max) {
        return false;
    }
    
    // Velocity constraint
    if (control(0) < config_.v_min || control(0) > config_.v_max) {
        return false;
    }
    
    // Steering rate constraint
    if (control(1) < -config_.delta_dot_max || control(1) > config_.delta_dot_max) {
        return false;
    }
    
    return true;
}
