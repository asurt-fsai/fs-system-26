#include "Cost.h"

namespace mpc_controller{

Cost::Cost(const Params& params) : params_(params) {
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
    double dtheta_ref_denominator = std::pow(d_pos_ref.norm(), 3.0);  // ||d_pos_ref||^3
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

    // Cache sin/cos of theta_ref — used multiple times below
    const double sin_theta = std::sin(ref_point.theta_ref);
    const double cos_theta = std::cos(ref_point.theta_ref);

    // Jacobian of contouring error w.r.t. heading angle theta:
    // d_contouring_error/dtheta = -dtheta_ref*cos(theta)*dx - dtheta_ref*sin(theta)*dy - dx_ref*sin(theta) + dy_ref*cos(theta)
    const double dContouringError = - ref_point.dtheta_ref * cos_theta * error(0)
                                    - ref_point.dtheta_ref * sin_theta * error(1)
                                    - ref_point.dx_ref * sin_theta
                                    + ref_point.dy_ref * cos_theta;

    // Jacobian of lag error w.r.t. heading angle theta:
    // d_lag_error/dtheta = -dtheta_ref*sin(theta)*dx + dtheta_ref*cos(theta)*dy + dx_ref*cos(theta) + dy_ref*sin(theta)
    const double dLagError        = - ref_point.dtheta_ref * sin_theta * error(0)
                                    + ref_point.dtheta_ref * cos_theta * error(1)
                                    + ref_point.dx_ref * cos_theta
                                    + ref_point.dy_ref * sin_theta;

    // Build 2×NX Jacobian matrix: rows = [contouring error, lag error], cols = [x, y, theta, delta, v]
    Eigen::Matrix<double,2,NX> d_error = Eigen::Matrix<double,2,NX>::Zero();
    // error = (x_ref − x, y_ref − y), so ∂error/∂(x,y) = −I₂
    // e_c = (−sinθ, cosθ)·error  →  ∂e_c/∂x = sinθ,  ∂e_c/∂y = −cosθ
    // e_l = ( cosθ, sinθ)·error  →  ∂e_l/∂x = −cosθ, ∂e_l/∂y = −sinθ
    // Row 0: derivatives of contouring error w.r.t. [x, y, theta, delta, v]
    d_error(0, 0) =  std::sin(ref_point.theta_ref);
    d_error(0, 1) = -std::cos(ref_point.theta_ref);
    d_error(0, 2) = 0.0;  // contouring error does not depend on car heading θ
    d_error(0, 3) = 0.0;  // Contouring error doesn't depend on delta directly
    d_error(0, 4) = 0.0;  // Contouring error doesn't depend on velocity directly
    
    // Row 1: derivatives of lag error w.r.t. [x, y, theta, delta, v]
    d_error(1, 0) = -std::cos(ref_point.theta_ref);
    d_error(1, 1) = -std::sin(ref_point.theta_ref);
    d_error(1, 2) = 0.0;  // lag error does not depend on car heading θ
    d_error(1, 3) = 0.0;  // Lag error doesn't depend on delta directly
    d_error(1, 4) = 0.0;  // Lag error doesn't depend on velocity directly
    
    return {error, d_error};
}

CostMatrix Cost::getContouringCost(const mpc_controller::ArcSpline &track, const mpc_controller::state &x, int k) const
{
    static const StateInputIndexes si_index;
    const int horizon = params_.horizon;

    // ── MPCC contouring/lag error cost ────────────────────────────────────
    // Decomposes the XY error into the track frame:
    //   e_c = lateral  deviation (perpendicular to track tangent) — penalised by q_c
    //   e_l = longitudinal deviation (along track tangent)        — penalised by q_l
    //
    // Setting q_c >> q_l means: strongly penalise going off track sideways,
    // but tolerate the car being slightly ahead/behind the reference point.
    // This is essential for time-optimal MPCC — a fixed reference point will
    // never perfectly align with the car's along-track position at every step.
    const ErrorInfo error_info = getErrorInfo(track, x);

    const double q_c = k < horizon ? params_.q_c : params_.q_c_N_mult * params_.q_c;
    const double q_l = params_.q_l;

    // Extract Jacobian rows for contouring and lag errors
    // d_error(0,:) = gradient of e_c w.r.t. state   [sinθ, -cosθ, 0, 0, 0]
    // d_error(1,:) = gradient of e_l w.r.t. state   [-cosθ, -sinθ, 0, 0, 0]
    const Eigen::Matrix<double,1,NX> d_contouring_error = error_info.d_error.row(0);
    const Eigen::Matrix<double,1,NX> d_lag_error        = error_info.d_error.row(1);

    // Zero-order terms: e_c(x0) - d_e_c * x0 (makes linearisation exact at current point)
    // For this 2D error (only x,y entries non-zero) these simplify to:
    //   c0 = -sin(θ_ref)*x_ref + cos(θ_ref)*y_ref
    //   l0 =  cos(θ_ref)*x_ref + sin(θ_ref)*y_ref
    const TrackPoint ref_point = getRefPoint(track, x);
    const double c0 = -std::sin(ref_point.theta_ref) * ref_point.x_ref
                     + std::cos(ref_point.theta_ref) * ref_point.y_ref;
    const double l0 =  std::cos(ref_point.theta_ref) * ref_point.x_ref
                     + std::sin(ref_point.theta_ref) * ref_point.y_ref;

    // Build Q and q: expanding (d*x + c0)^2 → x^T(d^T d)x + 2*c0*(d)x
    // Solver expects 0.5 x^T Q x + q^T x so Q is pre-scaled by 2
    Q_MPC Q_contouring_cost = Q_MPC::Zero();
    q_MPC q_contouring_cost = q_MPC::Zero();

    Q_contouring_cost = 2.0 * q_c * d_contouring_error.transpose() * d_contouring_error
                      + 2.0 * q_l * d_lag_error.transpose()        * d_lag_error;

    q_contouring_cost = 2.0 * q_c * c0 * d_contouring_error.transpose()
                      + 2.0 * q_l * l0 * d_lag_error.transpose();

    // ── Progress maximisation ─────────────────────────────────────────────
    // Pure linear incentive: the car goes as fast as the constraints allow.
    // No Q term — the constraints (speed/track limits) are the ceiling.
    q_contouring_cost(si_index.vs) = -params_.q_vs;

    // solver interface expects 0.5 x^T Q x + q^T x
    return {Q_contouring_cost, R_MPC::Zero(), S_MPC::Zero(), q_contouring_cost, r_MPC::Zero(), Z_MPC::Zero(), z_MPC::Zero()};
}

CostMatrix Cost::getHeadingCost(const mpc_controller::ArcSpline &track, const mpc_controller::state &x, int k) const
{
    static const StateInputIndexes si_index;

    // Get track tangent at the arc-length reference for this stage.
    // With arc-length-advancing references (set in MPC::setMPCProblem),
    // x.s already points to the correct future track section, so no
    // separate lateral correction is needed — the position cost handles
    // lateral approach and this cost just aligns heading with the track.
    const Eigen::Vector2d dpos_ref = track.getDerivative(x.s);
    double theta_ref = std::atan2(dpos_ref(1), dpos_ref(0));

    // Unwrap theta_ref to be closest to current heading — avoids discontinuity at ±π
    theta_ref += 2.0 * M_PI * std::round((x.theta - theta_ref) / (2.0 * M_PI));

    // Build heading cost: penalizes (theta - theta_ref)^2
    // Expanding: q_mu*(theta - theta_ref)^2 = q_mu*theta^2 - 2*q_mu*theta_ref*theta + const
    // In QP form (0.5*x^T*Q*x + q^T*x): Q[phi,phi] = 2*q_mu, q[phi] = -2*q_mu*theta_ref
    Q_MPC Q_heading_cost = Q_MPC::Zero();
    Q_heading_cost(si_index.phi, si_index.phi) = 2.0 * params_.q_mu;

    q_MPC q_heading_cost = q_MPC::Zero();
    q_heading_cost(si_index.phi) = -2.0 * params_.q_mu * theta_ref;

    return {Q_heading_cost, R_MPC::Zero(), S_MPC::Zero(), q_heading_cost, r_MPC::Zero(), Z_MPC::Zero(), z_MPC::Zero()};
}

CostMatrix Cost::getInputCost() const
{
    static const StateInputIndexes si_index;

    Q_MPC Q_input_cost = Q_MPC::Zero();
    R_MPC R_input_cost = R_MPC::Zero();

    // State penalties on steering angle
    // vs (velocity) is NOT penalised here — it is handled by the progress
    // maximisation linear term in getContouringCost (pure incentive, no target).
    Q_input_cost(si_index.delta, si_index.delta) = params_.r_delta;

    // Control input penalties on acceleration rate and steering rate
    // Note: reference also penalizes dVs (vs control) but our NU=2 has no vs control — skipped
    R_input_cost(si_index.dD,     si_index.dD)     = params_.r_dD;
    R_input_cost(si_index.dDelta, si_index.dDelta) = params_.r_dDelta;

    // Scale by 2 for solver format: 0.5 x^T Q x + q^T x
    Q_input_cost = 2.0 * Q_input_cost;
    R_input_cost = 2.0 * R_input_cost;

    return {Q_input_cost, R_input_cost, S_MPC::Zero(), q_MPC::Zero(), r_MPC::Zero(), Z_MPC::Zero(), z_MPC::Zero()};
}

CostMatrix Cost::getSoftConstraintCost() const
{
    static const StateInputIndexes si_index;

    Z_MPC Z_cost = Z_MPC::Identity();
    z_MPC z_cost = z_MPC::Ones();

    // Track boundary soft constraint only (kinematic model — no tire/slip angle constraints)
    Z_cost(si_index.con_track, si_index.con_track) = params_.sc_quad_track;
    z_cost(si_index.con_track) = params_.sc_lin_track;

    return {Q_MPC::Zero(), R_MPC::Zero(), S_MPC::Zero(), q_MPC::Zero(), r_MPC::Zero(), Z_cost, z_cost};
}

CostMatrix Cost::getCost(const mpc_controller::ArcSpline &track, const mpc_controller::state &x, int k) const
{
    // State struct passed directly — preserves the s field for track projection
    const CostMatrix contouring_cost   = getContouringCost(track, x, k);
    const CostMatrix heading_cost      = getHeadingCost(track, x, k);
    const CostMatrix input_cost        = getInputCost();
    const CostMatrix soft_con_cost     = getSoftConstraintCost();

    // Sum all Q contributions and symmetrize to avoid numerical asymmetry from floating point
    const Q_MPC Q_sum = contouring_cost.Q + heading_cost.Q + input_cost.Q;
    const Q_MPC Q     = 0.5 * (Q_sum + Q_sum.transpose());

    const R_MPC R = contouring_cost.R + heading_cost.R + input_cost.R;
    const q_MPC q = contouring_cost.q + heading_cost.q + input_cost.q;
    const r_MPC r = contouring_cost.r + heading_cost.r + input_cost.r;

    return {Q, R, S_MPC::Zero(), q, r, soft_con_cost.Z, soft_con_cost.z};
}


} // namespace mpc_controller
