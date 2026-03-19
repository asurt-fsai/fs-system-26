#ifndef MPC_CONFIG_H
#define MPC_CONFIG_H

#include <Eigen/Dense>
#include <vector>
#include <iostream>
#include <fstream>
#include <math.h>
#include "types.h"

namespace mpc_controller{

    #define NX 7 // Number of states: [x, y, vx, vy, theta, delta, v]
    #define NU 2 // Number of control inputs: [acceleration, steering rate]

    #define NB 10 // Max Number of Bounds
    #define NPC 3 // Number of Polytopic Constraints
    #define NS 3 // Number of Soft Constraints

    // static constexp is used so these values are compile-time constants and can be used in array sizes and other compile-time contexts
    static constexpr double N_Spline = 5000; // Number of points to resample the track spline to for accurate projection and reference generation
    static constexpr double LINEARIZE_EPS = 1e-5; // Perturbation size for numerical differentiation when linearizing dynamics
    static constexpr double N_MAX = 20; // Maximum number of MPC iterations

    struct StateInputIndexes{
        int x = 0;
        int y = 1;
        int vx = 2;
        int vy = 3;
        int theta = 4;
        int delta = 5;
        int v = 6;
        int s = 7;

        int a = 0; // control input: acceleration
        int delta_dot = 1; // control input: steering angle rate

    };

    static const StateInputIndexes state_input_indexes; // Global instance for easy access to state/input indexes
}



#endif // MPC_CONFIG_H