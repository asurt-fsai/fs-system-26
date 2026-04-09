#include "constraints.h"
#include <cmath>

namespace mpc_controller {

///////////////////////////////////////////////////////////////////////////////
// Constructor
///////////////////////////////////////////////////////////////////////////////
ConstraintSet::ConstraintSet(const Params& params) : params_(params) {}

///////////////////////////////////////////////////////////////////////////////
// STATE BOUNDS [x, y, theta, delta] - Explicit & Clean
///////////////////////////////////////////////////////////////////////////////
Eigen::Vector4d ConstraintSet::getStateLowerBounds() const {
    // Return lower bounds for states: [x, y, theta, delta]
    return Eigen::Vector4d(
        params_.x_min,           // 0: x position lower bound
        params_.y_min,           // 1: y position lower bound
        params_.theta_min,       // 2: heading angle lower bound
        params_.delta_min        // 3: steering angle lower bound
    );
}

Eigen::Vector4d ConstraintSet::getStateUpperBounds() const {
    // Return upper bounds for states: [x, y, theta, delta]
    return Eigen::Vector4d(
        params_.x_max,           // 0: x position upper bound
        params_.y_max,           // 1: y position upper bound
        params_.theta_max,       // 2: heading angle upper bound
        params_.delta_max        // 3: steering angle upper bound
    );
}

///////////////////////////////////////////////////////////////////////////////
// INPUT BOUNDS [v, delta_dot] - Explicit & Clean
///////////////////////////////////////////////////////////////////////////////
Eigen::Vector2d ConstraintSet::getInputLowerBounds() const {
    // Return lower bounds for inputs: [v, delta_dot]
    return Eigen::Vector2d(
        params_.v_min,           // 0: velocity lower bound
        -params_.delta_dot_max   // 1: steering rate lower bound (symmetric)
    );
}

Eigen::Vector2d ConstraintSet::getInputUpperBounds() const {
    // Return upper bounds for inputs: [v, delta_dot]
    return Eigen::Vector2d(
        params_.v_max,           // 0: velocity upper bound
        params_.delta_dot_max    // 1: steering rate upper bound (symmetric)
    );
}

///////////////////////////////////////////////////////////////////////////////
// MATRIX VERSIONS FOR MPC HORIZON (Convenience methods)
///////////////////////////////////////////////////////////////////////////////
std::pair<Eigen::MatrixXd, Eigen::MatrixXd> ConstraintSet::getInputBounds() const {
    int horizon = params_.horizon;
    
    Eigen::MatrixXd lower = Eigen::MatrixXd::Zero(horizon, 2);
    Eigen::MatrixXd upper = Eigen::MatrixXd::Zero(horizon, 2);
    
    // Apply same bounds for all steps using explicit vector method
    Eigen::Vector2d input_lower = getInputLowerBounds();
    Eigen::Vector2d input_upper = getInputUpperBounds();
    
    for (int i = 0; i < horizon; ++i) {
        lower.row(i) = input_lower.transpose();
        upper.row(i) = input_upper.transpose();
    }
    
    return {lower, upper};
}

std::pair<Eigen::MatrixXd, Eigen::MatrixXd> ConstraintSet::getStateBounds() const {
    int horizon = params_.getPredictionSize();
    
    Eigen::MatrixXd lower = Eigen::MatrixXd::Zero(horizon, 4);
    Eigen::MatrixXd upper = Eigen::MatrixXd::Zero(horizon, 4);
    
    // Apply same bounds for all steps using explicit vector method
    Eigen::Vector4d state_lower = getStateLowerBounds();
    Eigen::Vector4d state_upper = getStateUpperBounds();
    
    for (int i = 0; i < horizon; ++i) {
        lower.row(i) = state_lower.transpose();
        upper.row(i) = state_upper.transpose();
    }
    
    return {lower, upper};
}

///////////////////////////////////////////////////////////////////////////////
// FEASIBILITY CHECK
///////////////////////////////////////////////////////////////////////////////
bool ConstraintSet::checkFeasibility(const Eigen::Vector4d& state,
                                     const Eigen::Vector2d& control) const {
    // Get explicit bounds
    Eigen::Vector4d state_lower = getStateLowerBounds();
    Eigen::Vector4d state_upper = getStateUpperBounds();
    Eigen::Vector2d input_lower = getInputLowerBounds();
    Eigen::Vector2d input_upper = getInputUpperBounds();
    
    // Check state constraints [x, y, theta, delta]
    if (state(0) < state_lower(0) || state(0) > state_upper(0)) return false;  // x
    if (state(1) < state_lower(1) || state(1) > state_upper(1)) return false;  // y
    if (state(2) < state_lower(2) || state(2) > state_upper(2)) return false;  // theta
    if (state(3) < state_lower(3) || state(3) > state_upper(3)) return false;  // delta
    
    // Check input constraints [v, delta_dot]
    if (control(0) < input_lower(0) || control(0) > input_upper(0)) return false;  // v
    if (control(1) < input_lower(1) || control(1) > input_upper(1)) return false;  // delta_dot
    
    return true;
}

}  // namespace mpc_controller