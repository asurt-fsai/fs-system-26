// Copyright 2019 Alexander Liniger
// Adapted for FSAI MPC Controller 2026

// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at

//     http://www.apache.org/licenses/LICENSE-2.0

// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
///////////////////////////////////////////////////////////////////////////
// MPC Controller - Model Predictive Control for Autonomous Racing
// Features: Sequential Quadratic Programming (SQP), Horizon-based trajectory
//           optimization, Soft constraints, Real-time performance tracking
///////////////////////////////////////////////////////////////////////////

#ifndef MPC_CONTROLLER_MPC_H
#define MPC_CONTROLLER_MPC_H

#include "../config/config.h"
#include "../types/types.h"
#include "../Params/params.h"
#include "../Spline/Arc_Spline.h"
#include "../Bicycle Model/bicycle_model.h"
#include "../Integrator/integration_methods.h"
#include "../Cost/Cost.h"
#include "../Constraints/constraints.h"
#include "../Constraints/trackConstraints.h"
#include "../Interfaces/solver_interface.h"
#include "../Interfaces/hpipm_interface.h"

#include <array>
#include <memory>
#include <ctime>
#include <ratio>
#include <chrono>

namespace mpc_controller {

// ─── OptVariables ─────────────────────────────────────────────────────────────
// State and control at a single horizon step (external interface)
struct OptVariables {
    state   xk;   // Current state [x, y, theta, delta, v]
    control uk;   // Current control input [acceleration, delta_dot]
};

// ─── MPCReturn ────────────────────────────────────────────────────────────────
struct MPCReturn {
    const control                      u0;           // First control to apply
    const std::array<OptVariables, N+1> mpc_horizon; // Full predicted horizon
    const double                        time_total;  // Computation time [s]
    const double                        lateral_error; // Perpendicular distance to track [m]
};

// ─── MPC class ────────────────────────────────────────────────────────────────
class MPC {
public:
    MPC();

    /**
     * @brief Full constructor.
     * @param n_sqp     Number of SQP iterations per solve
     * @param n_reset   Failed-solve threshold before resetting guess
     * @param sqp_mixing  SQP blending factor (0–1)
     * @param Ts        Sampling time [s]
     * @param path      JSON config paths
     */
    MPC(int n_sqp, int n_reset, double sqp_mixing, double Ts,
        const PathToJson &path);

    /**
     * @brief Main MPC solver — call at each time step.
     * @param x0  Current vehicle state (updated with track projection)
     * @return MPCReturn containing u0, full horizon, and timing
     */
    MPCReturn runMPC(state &x0);

    /**
     * @brief Set reference track from 2-D waypoints.
     */
    void setTrack(const Eigen::VectorXd &X, const Eigen::VectorXd &Y);

private:
    // ── Core components ────────────────────────────────────────────────────
    int    n_sqp_;
    double sqp_mixing_;
    int    n_non_solves_;
    int    n_no_solves_sqp_;
    int    n_reset_;
    const double Ts_;

    Params                      params_;
    std::unique_ptr<ConstraintSet>  constraints_;
    std::unique_ptr<BicycleModel>   model_;
    std::unique_ptr<Cost>           cost_;
    std::unique_ptr<mpcc::SolverInterface> solver_;

    TrackConstraints             track_constraints_;
    ArcSpline                    track_;

    // ── Solution storage ───────────────────────────────────────────────────
    bool                             valid_initial_guess_;
    std::array<mpcc::Stage, N+1>     stages_;
    std::array<OptVariables, N+1>    initial_guess_;
    std::array<mpcc::OptVariables, N+1> optimal_solution_;

    // ── Private methods ────────────────────────────────────────────────────
    void setMPCProblem();
    void setStage(const state &xk, const control &uk,
                  const state &xk1, int time_step);

    void updateInitialGuess(const state &x0);
    void generateNewInitialGuess(const state &x0);
    void unwrapInitialGuess();

    /** Blend last and current SQP iterates by sqp_mixing_. */
    std::array<OptVariables, N+1> sqpSolutionUpdate(
        const std::array<OptVariables, N+1> &last_solution,
        const std::array<OptVariables, N+1> &current_solution);

    /** Extract OptVariables from mpcc::OptVariables. */
    static OptVariables extractOptVar(const mpcc::OptVariables &o);
};

} // namespace mpc_controller

#endif // MPC_CONTROLLER_MPC_H
