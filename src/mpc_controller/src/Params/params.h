#ifndef MPC_PARAMS_H
#define MPC_PARAMS_H


#include "../config.h"
#include "../types.h"
#include "nlohmann/json.hpp"
using json = nlohmann::json;
namespace mpc_controller{
    class Params {
    public:
        double Bm1; //motor model parameter 1
        double Bm2; //motor model parameter 2
        double Bm3; //motor model parameter 3

        //double m; //mass of the vehicle
        // mass is not used in the kinematic bicycle model, but we can include it for potential future use in dynamic models or for reference in throttle mapping

        double Lf; //distance from center of mass to front axle
        double Lr; //distance from center of mass to rear axle

        double wheelbase; //wheelbase of the vehicle
        double L; //length of the vehicle

        double r_inner; //inner radius of the track
        double r_outer; //outer radius of the track

        double g; //gravitational acceleration
        
        Params();
        Params(std::string file);
    };

    class CostParams {
    public:
        // put here the parameters related to the cost function, such as weights for different terms in the cost function, reference velocity, etc.
        CostParams();
        CostParams(std::string file);
    };

    class Bounds {
    public:
        struct LowerStateBounds     
        {
            /* data */
        };
        struct UpperStateBounds
        {
            /* data */
        };
        struct LowerControlBounds
        {
            /* data */
        };
        struct UpperControlBounds
        {
            /* data */
        };

        LowerStateBounds lower_state_bounds;
        UpperStateBounds upper_state_bounds;
        LowerControlBounds lower_control_bounds;
        UpperControlBounds upper_control_bounds;

        Bounds();
        Bounds(std::string file);
    };

    class MPCConfig {
    public:
        double dt; //time step duration (seconds)

    MPCConfig();
    MPCConfig(std::string file);
    };
        
}

#endif // MPC_PARAMS_H