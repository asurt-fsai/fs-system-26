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

TrackConstraint ConstraintSet::getTrackConstraints(const mpc_controller::ArcSpline& track,
                                                   double s, double r_in, double r_out) const {
    // Given arc length s and the track -> compute linearized track constraints
    
    // X-Y point of the center line
    const Eigen::Vector2d pos_center = track.getPoint(s);
    const Eigen::Vector2d d_center = track.getDerivative(s);
    
    // Tangent of center line at s (perpendicular to derivative)
    const Eigen::Vector2d tan_center = Eigen::Vector2d(-d_center(1), d_center(0));
    
    // Inner and outer track boundary given left and right width of track
    // TODO: make r_out and r_in dependent on s
    const Eigen::Vector2d pos_outer = pos_center + r_out * tan_center;
    const Eigen::Vector2d pos_inner = pos_center - r_in * tan_center;
    
    // Define track Jacobian as perpendicular vector
    TrackConstraint track_constraint;
    track_constraint.C(0, 0) = tan_center(0);
    track_constraint.C(0, 1) = tan_center(1);
    
    // Compute bounds
    track_constraint.lower = tan_center(0) * pos_inner(0) + tan_center(1) * pos_inner(1);
    track_constraint.upper = tan_center(0) * pos_outer(0) + tan_center(1) * pos_outer(1);
    
    return track_constraint;
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
