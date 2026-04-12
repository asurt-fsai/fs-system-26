#include "Cost.h"

namespace mpc_controller{

Cost::Cost(const Params& config) : config_(config) {
    std::cout << "Cost object created with loaded parameters." << std::endl;
}

TrackPoint Cost::getRefPoint(const mpc_controller::ArcSpline &track, const mpc_controller::state &x) const
{
    // Get the reference point on the track corresponding to the current state x
    //double s = track.projectOntoSpline(x.head(2)); // project current position onto track to get arc length s
    const double s = x.s;
    Eigen::Vector2d pos_ref = track.getPosition(s);
    Eigen::Vector2d d_pos_ref = track.getDerivative(s);
    double theta_ref = std::atan2(d_pos_ref(1), d_pos_ref(0));
    Eigen::Vector2d d2_pos_ref = track.getSecondDerivative(s);
    double dtheta_ref_nominator = d_pos_ref(0) * d2_pos_ref(1) - d_pos_ref(1) * d2_pos_ref(0);
    double dtheta_ref_denominator = std::pow(d_pos_ref.squaredNorm(), 1.5);
    if (dtheta_ref_denominator < 1e-6) {
        dtheta_ref_denominator = 1e-6; // prevent division by zero, set a minimum value
    }
    if (std::abs(dtheta_ref_nominator) < 1e-6) {
        dtheta_ref_nominator = 0.0; // if the nominator is very small, set it to zero to avoid numerical issues
    }
    double dtheta_ref = dtheta_ref_nominator / dtheta_ref_denominator;
    return {pos_ref(0), pos_ref(1), d_pos_ref(0), d_pos_ref(1), theta_ref, dtheta_ref};
}

ErrorInfo Cost::getErrorInfo(const mpc_controller::ArcSpline &track, const mpc_controller::state &x) const
{
    // compute the error between the refrence and the x-y coridinates of the current state
    TrackPoint ref_point = getRefPoint(track, x);
    Eigen::Vector2d error(ref_point.x_ref - x.x, ref_point.y_ref - x.y);
    // contouring error
    // contouring error = -dx * sin(theta_ref) + dy * cos(theta_ref)
    // ghost error is the error between the car and the reference point in the Frenet frame, it is used to compute the contouring error and the lag error
    Eigen::Matrix<double,1,2> ghost_error;
    ghost_error(0) = -std::sin(ref_point.theta_ref) * error(0) + std::cos(ref_point.theta_ref) * error(1);
    // lag error
    // lag error = dx * cos(theta_ref) + dy * sin(theta_ref)
    ghost_error(1) = std::cos(ref_point.theta_ref) * error(0) + std::sin(ref_point.theta_ref) * error(1);
    // compute the Jacobian of the error with respect to the state variables
    // d_contouring_error/dx = -dtheta_ref * cos(theta_ref) * dx 
                            // - dtheta_ref * sin(theta_ref) * dy 
                            // - dx_ref * sin(theta_ref) 
                            // + dy_ref * cos(theta_ref)
    const double dContouringError = - ref_point.dtheta_ref * std::cos(ref_point.theta_ref) * error(0)
                                    - ref_point.dtheta_ref * std::sin(ref_point.theta_ref) * error(1)
                                    - ref_point.dx_ref * std::sin(ref_point.theta_ref)
                                    + ref_point.dy_ref * std::cos(ref_point.theta_ref);
    // d_lag_error/dx = -dtheta_ref * sin(theta_ref) * dx 
                    // + dtheta_ref * cos(theta_ref) * dy 
                    // + dx_ref * cos(theta_ref) 
                    // + dy_ref * sin(theta_ref)
    const double dLagError        = - ref_point.dtheta_ref * std::sin(ref_point.theta_ref) * error(0)
                                    + ref_point.dtheta_ref * std::cos(ref_point.theta_ref) * error(1)
                                    + ref_point.dx_ref * std::cos(ref_point.theta_ref)
                                    + ref_point.dy_ref * std::sin(ref_point.theta_ref);

    
    Eigen::Matrix<double,2,NX> d_error = Eigen::Matrix<double,2,NX>::Zero();
    // Populate the Jacobian of the error with respect to the state variables
    // Row 0: derivatives of contouring error w.r.t. [x, y, theta, delta, v]
    d_error(0, 0) = -std::sin(ref_point.theta_ref);
    d_error(0, 1) = std::cos(ref_point.theta_ref);
    d_error(0, 2) = dContouringError;
    d_error(0, 3) = 0.0;  // Contouring error doesn't depend on delta directly
    d_error(0, 4) = 0.0;  // Contouring error doesn't depend on velocity directly
    
    // Row 1: derivatives of lag error w.r.t. [x, y, theta, delta, v]
    d_error(1, 0) = std::cos(ref_point.theta_ref);
    d_error(1, 1) = std::sin(ref_point.theta_ref);
    d_error(1, 2) = dLagError;
    d_error(1, 3) = 0.0;  // Lag error doesn't depend on delta directly
    d_error(1, 4) = 0.0;  // Lag error doesn't depend on velocity directly
    
    return {error, d_error};
}

CostMatrix Cost::getContouringCost(const ArcSpline &track, const state &x, int /*k*/) const
{
    ErrorInfo ei = getErrorInfo(track, x);
    const Eigen::Vector2d& error = ei.error;
    const Eigen::MatrixXd& D = ei.d_error;  // 2×NX Jacobian

    double w_c = config_.weight_state;
    double w_l = config_.weight_state;
    Eigen::Matrix2d W = Eigen::Matrix2d::Zero();
    W(0, 0) = w_c;  // contouring error weight
    W(1, 1) = w_l;  // lag error weight

    CostMatrix cm;
    cm.Q = D.transpose() * W * D;        // NX×NX
    cm.q = D.transpose() * W * error;    // NX×1 linear term
    cm.R = Eigen::MatrixXd::Zero(NU, NU);
    cm.S = Eigen::MatrixXd::Zero(NX, NU);
    cm.r = Eigen::VectorXd::Zero(NU);
    cm.Z = Eigen::MatrixXd::Zero(NS, NS);
    cm.z = Eigen::VectorXd::Zero(NS);
    return cm;
}

CostMatrix Cost::getHeadingCost(const ArcSpline& /*track*/, const state& /*x*/, int /*k*/) const
{
    // Heading deviation is already captured through contouring cost Jacobian.
    CostMatrix cm;
    cm.Q = Eigen::MatrixXd::Zero(NX, NX);
    cm.R = Eigen::MatrixXd::Zero(NU, NU);
    cm.S = Eigen::MatrixXd::Zero(NX, NU);
    cm.q = Eigen::VectorXd::Zero(NX);
    cm.r = Eigen::VectorXd::Zero(NU);
    cm.Z = Eigen::MatrixXd::Zero(NS, NS);
    cm.z = Eigen::VectorXd::Zero(NS);
    return cm;
}

CostMatrix Cost::getInputCost() const
{
    CostMatrix cm;
    cm.Q = Eigen::MatrixXd::Zero(NX, NX);
    cm.R = Eigen::MatrixXd::Identity(NU, NU) * config_.weight_control;
    cm.S = Eigen::MatrixXd::Zero(NX, NU);
    cm.q = Eigen::VectorXd::Zero(NX);
    cm.r = Eigen::VectorXd::Zero(NU);
    cm.Z = Eigen::MatrixXd::Zero(NS, NS);
    cm.z = Eigen::VectorXd::Zero(NS);
    return cm;
}

CostMatrix Cost::getBetaCost(const state& /*x*/) const
{
    // Kinematic model — no sideslip dynamics to penalize.
    CostMatrix cm;
    cm.Q = Eigen::MatrixXd::Zero(NX, NX);
    cm.R = Eigen::MatrixXd::Zero(NU, NU);
    cm.S = Eigen::MatrixXd::Zero(NX, NU);
    cm.q = Eigen::VectorXd::Zero(NX);
    cm.r = Eigen::VectorXd::Zero(NU);
    cm.Z = Eigen::MatrixXd::Zero(NS, NS);
    cm.z = Eigen::VectorXd::Zero(NS);
    return cm;
}

CostMatrix Cost::getBetaKinCost(const state& /*x*/) const
{
    CostMatrix cm;
    cm.Q = Eigen::MatrixXd::Zero(NX, NX);
    cm.R = Eigen::MatrixXd::Zero(NU, NU);
    cm.S = Eigen::MatrixXd::Zero(NX, NU);
    cm.q = Eigen::VectorXd::Zero(NX);
    cm.r = Eigen::VectorXd::Zero(NU);
    cm.Z = Eigen::MatrixXd::Zero(NS, NS);
    cm.z = Eigen::VectorXd::Zero(NS);
    return cm;
}

CostMatrix Cost::getSoftConstraintCost() const
{
    CostMatrix cm;
    cm.Q = Eigen::MatrixXd::Zero(NX, NX);
    cm.R = Eigen::MatrixXd::Zero(NU, NU);
    cm.S = Eigen::MatrixXd::Zero(NX, NU);
    cm.q = Eigen::VectorXd::Zero(NX);
    cm.r = Eigen::VectorXd::Zero(NU);
    cm.Z = Eigen::MatrixXd::Identity(NS, NS) * config_.weight_slack;
    cm.z = Eigen::VectorXd::Zero(NS);
    return cm;
}

CostMatrix Cost::getCost(const ArcSpline &track, const Eigen::VectorXd &x_vec, int k) const
{
    // Reconstruct state struct from VectorXd [x, y, theta, delta, v]
    state x;
    x.setZero();
    if (x_vec.size() >= NX) {
        x.x     = x_vec(0);
        x.y     = x_vec(1);
        x.theta = x_vec(2);
        x.delta = x_vec(3);
        x.v     = x_vec(4);
    }

    // Accumulate partial costs
    CostMatrix cm = getContouringCost(track, x, k);
    CostMatrix ic = getInputCost();
    cm.R += ic.R;
    CostMatrix sc = getSoftConstraintCost();
    cm.Z += sc.Z;

    // Velocity tracking: penalise deviation from ref_velocity at state index 4
    double w_v = config_.weight_state * 0.5;
    double v_err = x.v - config_.ref_velocity;
    cm.Q(4, 4) += w_v;
    cm.q(4)    += w_v * v_err;

    return cm;
}

} // namespace mpc_controller
