#ifndef MPC_Types_H
#define MPC_TYPES_H

namespace mpc_controller{
    struct state{
        double x;
        double y;
        double vx;
        double vy;
        double theta;
        double r;
        double delta;
        double v;
        double s; // arc length along the track
    };

    struct control{
        double a; // acceleration
        double delta_dot; // steering angle rate
    };
    
}
#endif //MPC_Types_H