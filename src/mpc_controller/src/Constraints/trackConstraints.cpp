#include "trackConstraints.h"

namespace mpc_controller {

TrackConstraints::TrackConstraints()
{
    std::cout << "default constructor, not everything is initialized properly" << std::endl;
}

TrackConstraints::TrackConstraints(const PathToJson& path)
    : params_(Params())
{
}

TrackConstraints::TrackConstraints(const Params& params)
    : params_(params)
{
}

TrackConstraint TrackConstraints::getTrackConstraints(const ArcSpline& track, double s) const {
    // Get r_in and r_out from params_ member (loaded from JSON)
    double r_in = params_.r_inner;
    double r_out = params_.r_outer;
    
    // X-Y point of the center line
    const Eigen::Vector2d pos_center = track.getPosition(s);
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

} // namespace mpc_controller