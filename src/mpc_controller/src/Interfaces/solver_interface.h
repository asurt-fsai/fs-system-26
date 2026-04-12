// Copyright 2019 Alexander Liniger
// Licensed under the Apache License, Version 2.0

#ifndef MPCC_SOLVER_INTERFACE_H
#define MPCC_SOLVER_INTERFACE_H

#include <Eigen/Dense>
#include <array>

#include "config.h"
#include "types.h"

namespace mpcc {

// Constant for unbounded values
constexpr double INF = 1e20;

// Type alias for easier usage
using State = mpc_controller::state;
using Control = mpc_controller::control;

/// Linear dynamics model: x_k+1 = A_k*x_k + B_k*u_k + g_k
struct LinearModel {
    Eigen::Matrix<double, NX, NX> A;    // State transition matrix
    Eigen::Matrix<double, NX, NU> B;    // Input matrix
    Eigen::Matrix<double, NX, 1> g;     // Affine term (linearization offset)
};

/// Cost matrices for quadratic cost function
struct CostMatrix {
    Eigen::Matrix<double, NX, NX> Q;    // State cost
    Eigen::Matrix<double, NU, NU> R;    // Input cost
    Eigen::Matrix<double, NX, NU> S;    // Cross term
    Eigen::Matrix<double, NX, 1> q;     // Linear state cost
    Eigen::Matrix<double, NU, 1> r;     // Linear input cost
    Eigen::Matrix<double, NS, NS> Z;    // Soft constraint cost
    Eigen::Matrix<double, NS, 1> z;     // Soft constraint linear term
};

/// Single stage of the MPC problem
struct Stage {
    LinearModel lin_model;              // Linearized dynamics
    CostMatrix cost_mat;                // Cost matrices
    int ng = 0;                         // Number of polytopic constraints
    int ns = 0;                         // Number of soft constraints
    
    Eigen::Matrix<double, NPC, NX> D;   // Polytopic constraint: D*x + C*u <= bounds
    Eigen::Matrix<double, NPC, NU> C;   // Polytopic constraint matrix
    Eigen::Matrix<double, NPC, 1> l_g;  // Lower bound on polytopic constraint
    Eigen::Matrix<double, NPC, 1> u_g;  // Upper bound on polytopic constraint
    
    Eigen::Matrix<double, NX, 1> l_bounds_x;    // Lower bounds on states
    Eigen::Matrix<double, NX, 1> u_bounds_x;    // Upper bounds on states
    Eigen::Matrix<double, NU, 1> l_bounds_u;    // Lower bounds on inputs
    Eigen::Matrix<double, NU, 1> u_bounds_u;    // Upper bounds on inputs
    
    Eigen::Matrix<double, NS, 1> l_bounds_s;    // Lower bounds on soft constraints
    Eigen::Matrix<double, NS, 1> u_bounds_s;    // Upper bounds on soft constraints
};

/// Optimal solution from MPC solver
struct OptVariables {
    Eigen::Matrix<double, NX, 1> x;     // State vector solution
    Eigen::Matrix<double, NU, 1> u;     // Control vector solution
    State xk;                            // State as struct
    mpc_controller::control uk;          // Control as struct
    
    OptVariables() : xk{}, uk{} {}
};

/// Abstract solver interface
class SolverInterface {
public:
    virtual ~SolverInterface() = default;
    
    /// Solve the MPC problem
    virtual std::array<OptVariables, N+1> solveMPC(
        std::array<Stage, N+1> &stages,
        const State &x0,
        int *status) = 0;
};

// Converter functions between Eigen vectors and state/control structs
Eigen::Matrix<double, NX, 1> stateToVector(const State &state);
State vectorToState(const Eigen::Matrix<double, NX, 1> &vec);
Control vectorToControl(const Eigen::Matrix<double, NU, 1> &vec);

}  // namespace mpcc

#endif  // MPCC_SOLVER_INTERFACE_H
