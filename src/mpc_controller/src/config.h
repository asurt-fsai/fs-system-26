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
    #define NS 1 // Number of Soft Constraints (kinematic model: track boundary only)

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
        int r = 2;           // Yaw rate (maps to theta index in kinematic model)
        int vs = 4;          // Virtual speed / progress rate (maps to v index)
        int phi = 2;         // Heading angle alias used by heading cost (maps to theta index)

        // 2D Control Input Indices
        int a = 0;           // Acceleration [m/s²]
        int delta_dot = 1;   // Steering angle rate [rad/s]
        // Control input aliases used by input cost (map to our 2D control)
        int dD = 0;          // Rate of change of throttle → maps to acceleration a
        int dDelta = 1;      // Rate of change of steering → maps to delta_dot
        // Soft Constraint Indices (NS=1, kinematic model: track boundary only)
        int con_track = 0;   // Track boundary soft constraint
    };

    static const StateInputIndexes state_input_indexes; // Global instance for easy access to state/input indexes

    // ===== MPC Cost Matrix Type Definitions =====
    typedef Eigen::Matrix<double, NX, NX> Q_MPC;       // State cost matrix (NX x NX)
    typedef Eigen::Matrix<double, NX, 1> q_MPC;        // State cost vector (NX x 1)
    typedef Eigen::Matrix<double, NU, NU> R_MPC;       // Control cost matrix (NU x NU)
    typedef Eigen::Matrix<double, NU, 1> r_MPC;        // Control cost vector (NU x 1)
    typedef Eigen::Matrix<double, NX, NU> S_MPC;       // Cross term cost matrix (NX x NU)
    typedef Eigen::Matrix<double, NS, NS> Z_MPC;       // Soft constraint cost matrix (NS x NS)
    typedef Eigen::Matrix<double, NS, 1> z_MPC;        // Soft constraint cost vector (NS x 1)
}



#endif // MPC_CONFIG_H