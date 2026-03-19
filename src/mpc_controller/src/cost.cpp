#include "Cost.h"

namespace mpc_controller{
Cost::Cost()
{
    std::cout << "Cost object created with default configuration." << std::endl;
}

//Cost::Cost

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
    Eigen::Matrix<double,1,2> contouring_error;
    contouring_error(0) = -std::sin(ref_point.theta_ref) * error(0) + std::cos(ref_point.theta_ref) * error(1);
    // lag error
    contouring_error(1) = std::cos(ref_point.theta_ref) * error(0) + std::sin(ref_point.theta_ref) * error(1);
    // compute the Jacobian of the error with respect to the state variables
    const double dContouringError = - ref_point.dtheta_ref * std::cos(ref_point.theta_ref) * error(0)
                                    - ref_point.dtheta_ref * std::sin(ref_point.theta_ref) * error(1)
                                    - ref_point.dx_ref * std::sin(ref_point.theta_ref)
                                    + ref_point.dy_ref * std::cos(ref_point.theta_ref);
    
    const double dLagError        = - ref_point.dtheta_ref * std::sin(ref_point.theta_ref) * error(0)
                                    + ref_point.dtheta_ref * std::cos(ref_point.theta_ref) * error(1)
                                    + ref_point.dx_ref * std::cos(ref_point.theta_ref)
                                    + ref_point.dy_ref * std::sin(ref_point.theta_ref);

    Eigen::Matrix<double,2,Nx> d_error = Eigen::Matrix<double,2,NX>::Zero();
}
} // namespace mpc_controller
