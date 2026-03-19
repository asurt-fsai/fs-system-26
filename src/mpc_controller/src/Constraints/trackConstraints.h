#include "../types.h"
#include "../Spline/Arc_Spline.h"
#include "constraints.h"
#include "../Params/params.h"

namespace mpc_controller {
    struct TrackConstraint {
        Eigen::Matrix<double, 1, 2> C;  // Constraint Jacobian (1x2: [c_x, c_y])
        double lower;                    // Lower bound
        double upper;                    // Upper bound
    };

    class TrackConstraints {
    public:
        TrackConstraints();
        TrackConstraints(const PathToJson& path);
        
        TrackConstraint getTrackConstraints(const ArcSpline& track, double s) const;
    
    private:
        Params params_;
    };
}