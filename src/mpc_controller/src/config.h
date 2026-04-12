#ifndef MPC_CONFIG_H
#define MPC_CONFIG_H

#include <Eigen/Dense>
#include <vector>
#include <iostream>
#include <fstream>
#include <math.h>

// Define NX and NU BEFORE including types.h (they're needed by types.h)
#define NX 5  // Number of states: [x, y, theta, delta, v] - Kinematic bicycle model
#define NU 2  // Number of control inputs: [acceleration, steering_rate]
#define N  20 // Prediction horizon length (compile-time constant for fixed-size arrays)

#include "types.h"

namespace mpc_controller{

    #define NB 10 // Max Number of Bounds
    #define NPC 3 // Number of Polytopic Constraints
    #define NS 3 // Number of Soft Constraints

    // static constexp is used so these values are compile-time constants and can be used in array sizes and other compile-time contexts
    static constexpr double N_Spline = 5000; // Number of points to resample the track spline to for accurate projection and reference generation
    static constexpr double LINEARIZE_EPS = 1e-5; // Perturbation size for numerical differentiation when linearizing dynamics
    static constexpr double N_MAX = 20; // Maximum number of MPC iterations

    struct StateInputIndexes{
        // 5D Kinematic State Indices
        int x = 0;           // Global X position [m]
        int y = 1;           // Global Y position [m]
        int theta = 2;       // Heading angle [rad]
        int delta = 3;       // Steering angle [rad]
        int v = 4;           // Forward velocity [m/s]

        // 2D Control Input Indices
        int a = 0;           // Acceleration [m/s²]
        int delta_dot = 1;   // Steering angle rate [rad/s]
    };

    static const StateInputIndexes state_input_indexes; // Global instance for easy access to state/input indexes
}



#endif // MPC_CONFIG_H