#include "solver_interface.h"

namespace mpcc {

/// Convert State struct to Eigen vector [x, y, vx, vy, theta, delta, v]
Eigen::Matrix<double, NX, 1> stateToVector(const State &state) {
    Eigen::Matrix<double, NX, 1> vec;
    vec(0) = state.x;
    vec(1) = state.y;
    vec(2) = state.vx;
    vec(3) = state.vy;
    vec(4) = state.theta;
    vec(5) = state.delta;
    vec(6) = state.v;
    return vec;
}

/// Convert Eigen vector to State struct
State vectorToState(const Eigen::Matrix<double, NX, 1> &vec) {
    State state{};
    state.x = vec(0);
    state.y = vec(1);
    state.vx = vec(2);
    state.vy = vec(3);
    state.theta = vec(4);
    state.delta = vec(5);
    state.v = vec(6);
    return state;
}

/// Convert Control vector to control struct
mpc_controller::control vectorToControl(const Eigen::Matrix<double, NU, 1> &vec) {
    mpc_controller::control ctrl{};
    // NU=2: [acceleration, steering angle rate]
    // control struct has: D_dot, delta_dot, dV_ghost
    ctrl.D_dot = vec(0);           // acceleration
    ctrl.delta_dot = vec(1);       // steering angle rate
    ctrl.dV_ghost = 0.0;           // not controlled
    return ctrl;
}

}  // namespace mpcc
