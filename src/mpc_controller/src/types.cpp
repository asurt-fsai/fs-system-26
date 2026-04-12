#include "types.h"

namespace mpc_controller {

    StateVector StateToVector(const state& X) {
        StateVector vec;
        vec(0) = X.x;
        vec(1) = X.y;
        vec(2) = X.theta;
        vec(3) = X.delta;
        vec(4) = X.v;
        return vec;
    }

    state VectorToState(const StateVector& X_vec) {
        state s{};
        s.x     = X_vec(0);
        s.y     = X_vec(1);
        s.theta = X_vec(2);
        s.delta = X_vec(3);
        s.v     = X_vec(4);
        return s;
    }

    ControlVector ControlToVector(const control& U) {
        ControlVector vec;
        vec(0) = U.D_dot;      // acceleration [m/s^2]
        vec(1) = U.delta_dot;  // steering rate [rad/s]
        return vec;
    }

    control VectorToControl(const ControlVector& U_vec) {
        control c{};
        c.D_dot     = U_vec(0);
        c.delta_dot = U_vec(1);
        c.dV_ghost  = 0.0;
        return c;
    }

} // namespace mpc_controller