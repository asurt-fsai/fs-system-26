#include "solver_interface.h"

namespace mpcc {

/// Convert State struct to Eigen vector [x, y, theta, delta, v]  (NX=5)
Eigen::Matrix<double, NX, 1> stateToVector(const State &state) {
    Eigen::Matrix<double, NX, 1> vec;
    vec(0) = state.x;
    vec(1) = state.y;
    vec(2) = state.theta;
    vec(3) = state.delta;
    vec(4) = state.v;
    return vec;
}

/// Convert Eigen vector [x, y, theta, delta, v] to State struct
State vectorToState(const Eigen::Matrix<double, NX, 1> &vec) {
    State state{};
    state.x     = vec(0);
    state.y     = vec(1);
    state.theta = vec(2);
    state.delta = vec(3);
    state.v     = vec(4);
    return state;
}

/// Convert NU=2 control vector [acceleration, steering_rate] to control struct
mpc_controller::control vectorToControl(const Eigen::Matrix<double, NU, 1> &vec) {
    mpc_controller::control ctrl{};
    ctrl.D_dot     = vec(0);   // acceleration [m/s²]
    ctrl.delta_dot = vec(1);   // steering angle rate [rad/s]
    ctrl.dV_ghost  = 0.0;
    return ctrl;
}

}  // namespace mpcc
