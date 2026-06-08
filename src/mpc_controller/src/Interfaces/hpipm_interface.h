// HPIPM Solver Interface Implementation
// Provides a solver using HPIPM (Interior Point Method) with BLASFEO matrix algebra

#ifndef MPCC_HPIPM_INTERFACE_H
#define MPCC_HPIPM_INTERFACE_H

#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <sys/time.h>
#include <array>
#include <vector>

#include "../config/config.h"
#include "../types/types.h"
#include "solver_interface.h"

namespace mpcc {

// Type alias for easier usage
using State = mpc_controller::state;
using Control = mpc_controller::control;

/// Wrapper struct for HPIPM-managed bounds
struct HpipmBound {
    std::vector<int> idx_u;               // Indices of bounded inputs
    std::vector<int> idx_x;               // Indices of bounded states
    std::vector<int> idx_s;               // Indices of soft constraints
    std::vector<double> lower_bounds_u;   // Lower bounds on inputs
    std::vector<double> upper_bounds_u;   // Upper bounds on inputs
    std::vector<double> lower_bounds_x;   // Lower bounds on states
    std::vector<double> upper_bounds_x;   // Upper bounds on states
};

/// HPIPM-based MPC solver
class HpipmInterface : public SolverInterface {
public:
    /// Solve the MPC problem using HPIPM
    std::array<OptVariables, N+1> solveMPC(
        std::array<Stage, N+1> &stages,
        const State &x0,
        int *status) override;

    ~HpipmInterface() {
        // Cleanup will be done in Solve() method
    }

private:
    // State dimensions
    int nx_[N+1];    // State dimensions at each stage
    int nu_[N+1];    // Input dimensions at each stage
    
    // Bound dimensions
    int nbx_[N+1];   // Number of state bounds
    int nbu_[N+1];   // Number of input bounds
    int ng_[N+1];    // Number of polytopic constraints
    int nsbx_[N+1];  // Number of soft state bounds
    int nsbu_[N+1];  // Number of soft input bounds
    int nsg_[N+1];   // Number of soft polytopic constraints
    
    // Dynamics matrices: x_k+1 = A_k*x_k + B_k*u_k + b_k
    double *hA_[N];    // State transition matrices
    double *hB_[N];    // Input matrices
    double *hb_[N];    // Affine terms
    
    // Cost matrices
    double *hQ_[N+1];  // State cost matrices
    double *hS_[N+1];  // Cross-term cost matrices
    double *hR_[N+1];  // Input cost matrices
    double *hq_[N+1];  // Linear state cost terms
    double *hr_[N+1];  // Linear input cost terms
    
    // Polytopic constraints
    double *hlg_[N+1]; // Lower bounds on polytopic constraints
    double *hug_[N+1]; // Upper bounds on polytopic constraints
    double *hC_[N+1];  // Input constraint matrices
    double *hD_[N+1];  // State constraint matrices
    
    // State bounds
    int *hidxbx_[N+1];     // Indices of bounded states
    double *hlbx_[N+1];    // Lower bounds on states
    double *hubx_[N+1];    // Upper bounds on states
    
    // Input bounds
    int *hidxbu_[N+1];     // Indices of bounded inputs
    double *hlbu_[N+1];    // Lower bounds on inputs
    double *hubu_[N+1];    // Upper bounds on inputs
    
    // Soft constraints
    double *hZl_[N+1];     // Soft constraint lower cost matrices
    double *hZu_[N+1];     // Soft constraint upper cost matrices
    double *hzl_[N+1];     // Soft constraint lower cost terms
    double *hzu_[N+1];     // Soft constraint upper cost terms
    int *hidxs_[N+1];      // Indices of soft constraints
    double *hlls_[N+1];    // Lower bounds on soft constraints
    double *hlus_[N+1];    // Upper bounds on soft constraints
    
    // Storage for bounds that differ from stage bounds
    std::array<HpipmBound, N+1> hpipm_bounds_;
    Eigen::Matrix<double, NX, 1> b0_;  // Affine term for first stage
    
    /// Set up dynamics for all stages
    void setDynamics(std::array<Stage, N+1> &stages, const State &x0);
    
    /// Set up cost matrices for all stages
    void setCost(std::array<Stage, N+1> &stages);
    
    /// Set up bound constraints for all stages
    void setBounds(std::array<Stage, N+1> &stages, const State &x0);
    
    /// Set up polytopic constraints for all stages
    void setPolytopicConstraints(std::array<Stage, N+1> &stages);
    
    /// Set up soft constraints for all stages
    void setSoftConstraints(std::array<Stage, N+1> &stages);
    
    /// Solve the QP problem using HPIPM IPM
    std::array<OptVariables, N+1> Solve(int *status);
    
    /// Print QP data to stdout (debug)
    void print_data();
};

}  // namespace mpcc

#endif  // MPCC_HPIPM_INTERFACE_H
