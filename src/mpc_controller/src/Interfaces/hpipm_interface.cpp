// HPIPM Solver Interface Implementation
// Uses hpipm-cpp C++ wrapper when HPIPM library is available,
// otherwise falls back to printing a warning and returning zero solution.

#include <cstring>
#include "hpipm_interface.h"

#ifdef HPIPM_CPP_AVAILABLE
// Full C++ wrapper for HPIPM — compiled only when real HPIPM is installed
// hpipm-cpp uses 'N' as a parameter name in its API, which conflicts with the
// MPC prediction horizon macro #define N 20 from config.h.
// We temporarily undefine N around the include, then restore it.
#pragma push_macro("N")
#undef N
#include "hpipm-cpp/hpipm-cpp.hpp"
#pragma pop_macro("N")
#endif

namespace mpcc {

// ─── Internal helpers ────────────────────────────────────────────────────────

// Convert mpcc::Stage array to the hpipm::OcpQp vector expected by the C++ wrapper.
// hpipm-cpp convention: lg <= C*x + D*u <= ug  (C is state, D is input)
// mpcc::Stage convention: l_g <= D*x + C*u <= u_g (D is state NPC×NX, C is input NPC×NU)
// We therefore swap names when populating hpipm::OcpQp.
#ifdef HPIPM_CPP_AVAILABLE
static std::vector<hpipm::OcpQp> buildOcpQp(
        const std::array<mpcc::Stage, N+1>& stages,
        const Eigen::Matrix<double, NX, 1>& /*x0_not_used_here*/)
{
    std::vector<hpipm::OcpQp> qp(N + 1);

    for (int i = 0; i <= N; ++i) {
        const auto& s = stages[i];

        // ── Dynamics (not needed at final stage; solver ignores A,B at N) ──
        if (i < N) {
            qp[i].A = s.lin_model.A;
            qp[i].B = s.lin_model.B;
            qp[i].b = s.lin_model.g;
        }

        // ── Cost ─────────────────────────────────────────────────────────────
        qp[i].Q = s.cost_mat.Q;
        qp[i].R = s.cost_mat.R;
        qp[i].S = s.cost_mat.S.transpose();  // mpcc stores NX×NU; hpipm-cpp needs NU×NX
        qp[i].q = s.cost_mat.q;
        qp[i].r = s.cost_mat.r;

        // ── State box bounds ─────────────────────────────────────────────────
        qp[i].idxbx.clear();
        Eigen::VectorXd lbx_active, ubx_active;
        int nbx_count = 0;
        for (int j = 0; j < NX; ++j) {
            if (s.l_bounds_x(j) > -INF || s.u_bounds_x(j) < INF) {
                qp[i].idxbx.push_back(j);
                nbx_count++;
            }
        }
        lbx_active.resize(nbx_count);
        ubx_active.resize(nbx_count);
        int idx = 0;
        for (int j = 0; j < NX; ++j) {
            if (s.l_bounds_x(j) > -INF || s.u_bounds_x(j) < INF) {
                lbx_active(idx) = s.l_bounds_x(j);
                ubx_active(idx) = s.u_bounds_x(j);
                idx++;
            }
        }
        qp[i].lbx = lbx_active;
        qp[i].ubx = ubx_active;

        // ── Input box bounds ─────────────────────────────────────────────────
        if (i < N) {
            qp[i].idxbu.clear();
            Eigen::VectorXd lbu_active, ubu_active;
            int nbu_count = 0;
            for (int j = 0; j < NU; ++j) {
                if (s.l_bounds_u(j) > -INF || s.u_bounds_u(j) < INF) {
                    qp[i].idxbu.push_back(j);
                    nbu_count++;
                }
            }
            lbu_active.resize(nbu_count);
            ubu_active.resize(nbu_count);
            int uidx = 0;
            for (int j = 0; j < NU; ++j) {
                if (s.l_bounds_u(j) > -INF || s.u_bounds_u(j) < INF) {
                    lbu_active(uidx) = s.l_bounds_u(j);
                    ubu_active(uidx) = s.u_bounds_u(j);
                    uidx++;
                }
            }
            qp[i].lbu = lbu_active;
            qp[i].ubu = ubu_active;
        }

        // ── Polytopic constraints: hpipm C = state (ng×nx), D = input (ng×nu)
        //    mpcc::Stage.D is (NPC×NX) state matrix → maps to hpipm::OcpQp.C
        //    mpcc::Stage.C is (NPC×NU) input matrix → maps to hpipm::OcpQp.D
        if (s.ng > 0) {
            qp[i].C  = s.D.cast<double>();  // state constraint NPC×NX
            qp[i].D  = s.C.cast<double>();  // input constraint NPC×NU
            qp[i].lg = s.l_g;
            qp[i].ug = s.u_g;
        }

        // ── Soft constraint cost (slack penalty) ─────────────────────────────
        // NOTE: hpipm-cpp wrapper only supports nsbx (soft state box constraints)
        // via idxs, not nsg (soft polytopic). Setting Zl/Zu here would cause a
        // dimension mismatch (nsg is always 0 in the wrapper). Track constraints
        // remain as hard constraints; ensure track boundary is wide enough.
        // Soft constraints on polytopic are handled by the raw-C path only.
    }
    return qp;
}
#endif // HPIPM_CPP_AVAILABLE

// ─── solveMPC ──────────────────────────────────────────────────────────────

void HpipmInterface::setDynamics(std::array<Stage, N+1> &stages, const State &x0) {
    b0_ = (stages[0].lin_model.A * mpcc::stateToVector(x0) + stages[0].lin_model.g);

    for (int i = 0; i < N; ++i) {
        if (i == 0) {
            hA_[i] = nullptr;
            hB_[i] = stages[i].lin_model.B.data();
            hb_[i] = b0_.data();
            nx_[i] = 0;
            nu_[i] = NU;
        } else {
            hA_[i] = stages[i].lin_model.A.data();
            hB_[i] = stages[i].lin_model.B.data();
            hb_[i] = stages[i].lin_model.g.data();
            nx_[i] = NX;
            nu_[i] = NU;
        }
    }
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

void HpipmInterface::setBounds(std::array<Stage, N+1> &stages, const State &/*x0*/) {
    nbu_[0] = 0;
    hpipm_bounds_[0].idx_u.clear();
    hpipm_bounds_[0].lower_bounds_u.clear();
    hpipm_bounds_[0].upper_bounds_u.clear();

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
    hlbx_[0]   = nullptr;
    hubx_[0]   = nullptr;
    hlbu_[0]   = hpipm_bounds_[0].lower_bounds_u.data();
    hubu_[0]   = hpipm_bounds_[0].upper_bounds_u.data();

    for (int i = 1; i <= N; ++i) {
        hpipm_bounds_[i].idx_u.clear();
        hpipm_bounds_[i].lower_bounds_u.clear();
        hpipm_bounds_[i].upper_bounds_u.clear();
        nbu_[i] = 0;

        if (i < N) {
            for (int j = 0; j < NU; ++j) {
                if (stages[i].l_bounds_u(j) > -INF && stages[i].u_bounds_u(j) < INF) {
                    nbu_[i]++;
                    hpipm_bounds_[i].idx_u.push_back(j);
                    hpipm_bounds_[i].lower_bounds_u.push_back(stages[i].l_bounds_u(j));
                    hpipm_bounds_[i].upper_bounds_u.push_back(stages[i].u_bounds_u(j));
                }
            }
        }

        hpipm_bounds_[i].idx_x.clear();
        hpipm_bounds_[i].lower_bounds_x.clear();
        hpipm_bounds_[i].upper_bounds_x.clear();
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
        hlbx_[i]   = hpipm_bounds_[i].lower_bounds_x.data();
        hubx_[i]   = hpipm_bounds_[i].upper_bounds_x.data();
        hlbu_[i]   = hpipm_bounds_[i].lower_bounds_u.data();
        hubu_[i]   = hpipm_bounds_[i].upper_bounds_u.data();
    }
    nbu_[N]   = 0;
    hidxbu_[N] = nullptr;
    hlbu_[N]   = nullptr;
    hubu_[N]   = nullptr;
}

void HpipmInterface::setPolytopicConstraints(std::array<Stage, N+1> &stages) {
    for (int i = 0; i <= N; ++i) {
        ng_[i] = stages[i].ng;
        if (stages[i].ng > 0) {
            // HPIPM raw-C convention: C*x + D*u
            //   hC_[i] → state constraint matrix  (ng×nx) ← mpcc::Stage.D (NPC×NX)
            //   hD_[i] → input constraint matrix  (ng×nu) ← mpcc::Stage.C (NPC×NU)
            hC_[i]  = stages[i].D.data();  // state constraint rows
            hD_[i]  = stages[i].C.data();  // input constraint rows
            hlg_[i] = stages[i].l_g.data();
            hug_[i] = stages[i].u_g.data();
        } else {
            hC_[i]  = nullptr;
            hD_[i]  = nullptr;
            hlg_[i] = nullptr;
            hug_[i] = nullptr;
        }
    }
}

void HpipmInterface::setSoftConstraints(std::array<Stage, N+1> &stages) {
    for (int i = 0; i <= N; ++i) {
        hpipm_bounds_[i].idx_s.clear();

        if (stages[i].ns != 0) {
            nsbx_[i] = 0;
            nsbu_[i] = 0;
            nsg_[i]  = stages[i].ns;

            for (int j = 0; j < stages[i].ns; ++j) {
                hpipm_bounds_[i].idx_s.push_back(j + nbx_[i] + nbu_[i]);
            }

            hidxs_[i] = hpipm_bounds_[i].idx_s.data();
            hlls_[i]  = stages[i].l_bounds_s.data();
            hlus_[i]  = stages[i].u_bounds_s.data();
        } else {
            nsbx_[i] = 0;
            nsbu_[i] = 0;
            nsg_[i]  = 0;
            hidxs_[i] = nullptr;
            hlls_[i]  = nullptr;
            hlus_[i]  = nullptr;
        }
    }
}

// ─── Primary entry point ──────────────────────────────────────────────────────
std::array<OptVariables, N+1> HpipmInterface::solveMPC(
        std::array<Stage, N+1> &stages,
        const State &x0,
        int *status)
{
#ifdef HPIPM_CPP_AVAILABLE
    // ── Use hpipm-cpp C++ wrapper ─────────────────────────────────────────
    Eigen::Matrix<double, NX, 1> x0_vec = mpcc::stateToVector(x0);

    std::vector<hpipm::OcpQp> ocp_qp = buildOcpQp(stages, x0_vec);

    hpipm::OcpQpIpmSolverSettings settings;
    settings.mode     = hpipm::HpipmMode::Speed;
    settings.iter_max = 50;
    settings.tol_stat = 1e-6;
    settings.tol_eq   = 1e-6;
    settings.tol_ineq = 1e-6;
    settings.tol_comp = 1e-6;

    hpipm::OcpQpIpmSolver solver(settings);
    solver.resize(ocp_qp);

    std::vector<hpipm::OcpQpSolution> sol(N + 1);
    hpipm::HpipmStatus hs = solver.solve(x0_vec, ocp_qp, sol);
    // Accept Success and MinStep/MaxIter as usable (suboptimal) solutions
    bool usable = (hs == hpipm::HpipmStatus::Success
                || hs == hpipm::HpipmStatus::MinStepLengthReached
                || hs == hpipm::HpipmStatus::MaxIterReached);
    *status = usable ? 0 : 1;

    static int hpipm_log = 0;
    static hpipm::HpipmStatus last_status = hpipm::HpipmStatus::NaNDetected;
    if (hpipm_log++ % 100 == 0 || hs != last_status) {
        last_status = hs;
        const char* status_str = "Unknown";
        switch (hs) {
            case hpipm::HpipmStatus::Success: status_str = "Success"; break;
            case hpipm::HpipmStatus::MaxIterReached: status_str = "MaxIter"; break;
            case hpipm::HpipmStatus::MinStepLengthReached: status_str = "MinStep"; break;
            case hpipm::HpipmStatus::NaNDetected: status_str = "NaN"; break;
            default: break;
        }
        printf("[HPIPM] status=%s  x0=(%.2f,%.2f) v=%.2f δ=%.3f\n",
               status_str, x0.x, x0.y, x0.v, x0.delta);
        if (sol[0].u.size() == NU) {
            printf("[HPIPM] u0: a=%.4f δ̇=%.4f\n", sol[0].u(0), sol[0].u(1));
        }
    }

    std::array<OptVariables, N+1> result;
    // Stage 0: initial state is embedded — x size is 0 from solver
    result[0].xk = x0;
    result[0].x.setZero();
    if (sol[0].u.size() == NU) {
        result[0].u  = sol[0].u.head<NU>();
        result[0].uk = vectorToControl(sol[0].u.head<NU>());
    } else {
        result[0].u.setZero();
        result[0].uk = mpc_controller::control{};
    }
    // Stages 1..N
    for (int i = 1; i <= N; ++i) {
        if (sol[i].x.size() == NX) {
            result[i].x  = sol[i].x.head<NX>();
            result[i].xk = vectorToState(sol[i].x.head<NX>());
        } else {
            result[i].x.setZero();
            result[i].xk = x0;
        }
        if (i < N && sol[i].u.size() == NU) {
            result[i].u  = sol[i].u.head<NU>();
            result[i].uk = vectorToControl(sol[i].u.head<NU>());
        } else {
            result[i].u.setZero();
            result[i].uk = mpc_controller::control{};
        }
    }
    return result;

#else
    // ── Fallback: prepare internal arrays and return zeros ────────────────
    // (Solver cannot run without HPIPM library; build with HPIPM to enable)
    setDynamics(stages, x0);
    setCost(stages);
    setBounds(stages, x0);
    setPolytopicConstraints(stages);
    setSoftConstraints(stages);

    std::array<OptVariables, N+1> solution;
    solution[0].xk = x0;
    for (int i = 0; i <= N; ++i) {
        solution[i].x.setZero();
        solution[i].u.setZero();
    }
    *status = 1;  // Non-zero = solver not available
    return solution;
#endif
}

std::array<OptVariables, N+1> HpipmInterface::Solve(int *status) {
    // Legacy stub kept for compatibility; the real path goes through solveMPC().
    std::array<OptVariables, N+1> solution;
    for (int i = 0; i <= N; ++i) {
        solution[i].x.setZero();
        solution[i].u.setZero();
    }
    *status = 1;
    return solution;
}

void HpipmInterface::print_data() {
    printf("\n=== MPC QP Data ===\n");
    printf("Horizon: N = %d\n", N);
    printf("State dimension: NX = %d\n", NX);
    printf("Control dimension: NU = %d\n", NU);
#ifdef HPIPM_CPP_AVAILABLE
    printf("Solver backend: hpipm-cpp (real HPIPM)\n");
#else
    printf("Solver backend: STUB (link against HPIPM to enable)\n");
#endif
}

}  // namespace mpcc
