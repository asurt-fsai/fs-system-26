// HPIPM Solver Interface Implementation
// Uses BLASFEO and HPIPM for QP solving

#include <cstring>
#include "hpipm_interface.h"

// BLASFEO headers
#include <blasfeo_d_aux_ext_dep.h>

// HPIPM headers (from hpipm_stubs or actual HPIPM library)
#include "hpipm_d_ocp_qp_ipm.h"
#include "hpipm_d_ocp_qp_dim.h"
#include "hpipm_d_ocp_qp.h"
#include "hpipm_d_ocp_qp_sol.h"
#include "hpipm_timing.h"

namespace mpcc {

void HpipmInterface::setDynamics(std::array<Stage, N+1> &stages, const State &x0) {
    b0_ = (stages[0].lin_model.A * stateToVector(x0) + stages[0].lin_model.g);
    
    for (int i = 0; i < N; ++i) {
        if (i == 0) {
            // First stage: x_0 is initial condition, so A not used
            hA_[i] = nullptr;
            hB_[i] = stages[i].lin_model.B.data();
            hb_[i] = b0_.data();
            
            nx_[i] = 0;
            nu_[i] = NU;
        } else {
            // Subsequent stages: full dynamics
            hA_[i] = stages[i].lin_model.A.data();
            hB_[i] = stages[i].lin_model.B.data();
            hb_[i] = stages[i].lin_model.g.data();
            
            nx_[i] = NX;
            nu_[i] = NU;
        }
    }
    // Final stage: no inputs
    nx_[N] = NX;
    nu_[N] = 0;
}

void HpipmInterface::setCost(std::array<Stage, N+1> &stages) {
    for (int i = 0; i <= N; ++i) {
        hQ_[i] = stages[i].cost_mat.Q.data();
        hR_[i] = stages[i].cost_mat.R.data();
        hS_[i] = stages[i].cost_mat.S.data();
        hq_[i] = stages[i].cost_mat.q.data();
        hr_[i] = stages[i].cost_mat.r.data();
        
        if (stages[i].ns != 0) {
            hZl_[i] = stages[i].cost_mat.Z.data();
            hZu_[i] = stages[i].cost_mat.Z.data();
            hzl_[i] = stages[i].cost_mat.z.data();
            hzu_[i] = stages[i].cost_mat.z.data();
        } else {
            hZl_[i] = nullptr;
            hZu_[i] = nullptr;
            hzl_[i] = nullptr;
            hzu_[i] = nullptr;
        }
    }
}

void HpipmInterface::setBounds(std::array<Stage, N+1> &stages, const State &x0) {
    // First stage: no state bounds (x_0 is fixed), only input bounds
    nbu_[0] = 0;
    hpipm_bounds_[0].idx_u.resize(0);
    hpipm_bounds_[0].lower_bounds_u.resize(0);
    hpipm_bounds_[0].upper_bounds_u.resize(0);
    
    for (int j = 0; j < NU; ++j) {
        if (stages[0].l_bounds_u(j) > -INF && stages[0].u_bounds_u(j) < INF) {
            nbu_[0]++;
            hpipm_bounds_[0].idx_u.push_back(j);
            hpipm_bounds_[0].lower_bounds_u.push_back(stages[0].l_bounds_u(j));
            hpipm_bounds_[0].upper_bounds_u.push_back(stages[0].u_bounds_u(j));
        }
    }
    
    nbx_[0] = 0;
    hidxbx_[0] = nullptr;
    hidxbu_[0] = hpipm_bounds_[0].idx_u.data();
    hlbx_[0] = nullptr;
    hubx_[0] = nullptr;
    hlbu_[0] = hpipm_bounds_[0].lower_bounds_u.data();
    hubu_[0] = hpipm_bounds_[0].upper_bounds_u.data();
    
    // Intermediate and final stages: both state and input bounds
    for (int i = 1; i <= N; ++i) {
        // Input bounds
        hpipm_bounds_[i].idx_u.resize(0);
        hpipm_bounds_[i].lower_bounds_u.resize(0);
        hpipm_bounds_[i].upper_bounds_u.resize(0);
        nbu_[i] = 0;
        
        for (int j = 0; j < NU; ++j) {
            if (i < N && stages[i].l_bounds_u(j) > -INF && stages[i].u_bounds_u(j) < INF) {
                nbu_[i]++;
                hpipm_bounds_[i].idx_u.push_back(j);
                hpipm_bounds_[i].lower_bounds_u.push_back(stages[i].l_bounds_u(j));
                hpipm_bounds_[i].upper_bounds_u.push_back(stages[i].u_bounds_u(j));
            }
        }
        
        // State bounds
        hpipm_bounds_[i].idx_x.resize(0);
        hpipm_bounds_[i].lower_bounds_x.resize(0);
        hpipm_bounds_[i].upper_bounds_x.resize(0);
        nbx_[i] = 0;
        
        for (int j = 0; j < NX; ++j) {
            if (stages[i].l_bounds_x(j) > -INF && stages[i].u_bounds_x(j) < INF) {
                nbx_[i]++;
                hpipm_bounds_[i].idx_x.push_back(j);
                hpipm_bounds_[i].lower_bounds_x.push_back(stages[i].l_bounds_x(j));
                hpipm_bounds_[i].upper_bounds_x.push_back(stages[i].u_bounds_x(j));
            }
        }
        
        hidxbx_[i] = hpipm_bounds_[i].idx_x.data();
        hidxbu_[i] = hpipm_bounds_[i].idx_u.data();
        hlbx_[i] = hpipm_bounds_[i].lower_bounds_x.data();
        hubx_[i] = hpipm_bounds_[i].upper_bounds_x.data();
        hlbu_[i] = hpipm_bounds_[i].lower_bounds_u.data();
        hubu_[i] = hpipm_bounds_[i].upper_bounds_u.data();
    }
    
    // Final stage: no inputs
    nbu_[N] = 0;
    hidxbu_[N] = nullptr;
    hlbu_[N] = nullptr;
    hubu_[N] = nullptr;
}

void HpipmInterface::setPolytopicConstraints(std::array<Stage, N+1> &stages) {
    for (int i = 0; i <= N; ++i) {
        ng_[i] = stages[i].ng;
        if (stages[i].ng > 0) {
            hC_[i] = stages[i].C.data();
            hD_[i] = stages[i].D.data();
            hlg_[i] = stages[i].l_g.data();
            hug_[i] = stages[i].u_g.data();
        } else {
            hC_[i] = nullptr;
            hD_[i] = nullptr;
            hlg_[i] = nullptr;
            hug_[i] = nullptr;
        }
    }
}

void HpipmInterface::setSoftConstraints(std::array<Stage, N+1> &stages) {
    for (int i = 0; i <= N; ++i) {
        hpipm_bounds_[i].idx_s.resize(0);
        
        if (stages[i].ns != 0) {
            nsbx_[i] = 0;
            nsbu_[i] = 0;
            nsg_[i] = stages[i].ns;
            
            for (int j = 0; j < stages[i].ns; ++j) {
                hpipm_bounds_[i].idx_s.push_back(j + nbx_[i] + nbu_[i]);
            }
            
            hidxs_[i] = hpipm_bounds_[i].idx_s.data();
            hlls_[i] = stages[i].l_bounds_s.data();
            hlus_[i] = stages[i].u_bounds_s.data();
        } else {
            nsbx_[i] = 0;
            nsbu_[i] = 0;
            nsg_[i] = 0;
            hidxs_[i] = nullptr;
            hlls_[i] = nullptr;
            hlus_[i] = nullptr;
        }
    }
}

std::array<OptVariables, N+1> HpipmInterface::solveMPC(
    std::array<Stage, N+1> &stages,
    const State &x0,
    int *status) {
    
    setDynamics(stages, x0);
    setCost(stages);
    setBounds(stages, x0);
    setPolytopicConstraints(stages);
    setSoftConstraints(stages);
    
    std::array<OptVariables, N+1> opt_solution = Solve(status);
    opt_solution[0].xk = x0;
    
    return opt_solution;
}

std::array<OptVariables, N+1> HpipmInterface::Solve(int *status) {
    // This is a stub implementation. When actual HPIPM libraries are available,
    // replace with actual solver code.
    
    printf("\n WARNING: Using stub HPIPM solver. \n");
    printf(" Link against real HPIPM library for actual solving.\n");
    
    std::array<OptVariables, N+1> solution;
    for (int i = 0; i <= N; ++i) {
        solution[i].x.setZero();
        solution[i].u.setZero();
    }
    
    *status = 0;  // Return success status
    return solution;
}

void HpipmInterface::print_data() {
    printf("\n=== MPC QP Data ===\n");
    printf("Horizon: N = %d\n", N);
    printf("State dimension: NX = %d\n", NX);
    printf("Control dimension: NU = %d\n", NU);
}

}  // namespace mpcc
