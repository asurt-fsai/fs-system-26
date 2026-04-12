// Copyright 2019 Alexander Liniger
// Adapted for FSAI MPC Controller 2026
//
// Licensed under the Apache License, Version 2.0 (the "License");
// see http://www.apache.org/licenses/LICENSE-2.0

#include "mpc.h"
#include <cmath>
#include <iostream>

namespace mpc_controller {

// ─────────────────────────────────────────────────────────────────────────────
// Constructors
// ─────────────────────────────────────────────────────────────────────────────

MPC::MPC()
    : Ts_(1.0),
      n_sqp_(1), sqp_mixing_(1.0),
      n_non_solves_(0), n_no_solves_sqp_(0), n_reset_(5),
      valid_initial_guess_(false)
{
    std::cout << "MPC Default Constructor — params not loaded from JSON.\n";
    params_       = Params();
    constraints_  = std::make_unique<ConstraintSet>(params_);
    cost_         = std::make_unique<Cost>(params_);
    model_        = std::make_unique<BicycleModel>(params_);
    solver_       = std::make_unique<mpcc::HpipmInterface>();
}

MPC::MPC(int n_sqp, int n_reset, double sqp_mixing, double Ts,
         const PathToJson &path)
    : Ts_(Ts),
      n_sqp_(n_sqp), sqp_mixing_(sqp_mixing),
      n_non_solves_(0), n_no_solves_sqp_(0), n_reset_(n_reset),
      valid_initial_guess_(false)
{
    // Load all parameters from JSON
    params_.loadAll(path.model_path, path.costs_path,
                    path.bounds_path, path.normalization_path);

    constraints_  = std::make_unique<ConstraintSet>(params_);
    cost_         = std::make_unique<Cost>(params_);
    model_        = std::make_unique<BicycleModel>(params_);
    solver_       = std::make_unique<mpcc::HpipmInterface>();
}

// ─────────────────────────────────────────────────────────────────────────────
// setMPCProblem — build QP for all N+1 stages
// ─────────────────────────────────────────────────────────────────────────────

void MPC::setMPCProblem()
{
    for (int i = 0; i <= N; i++) {
        setStage(initial_guess_[i].xk,
                 initial_guess_[i].uk,
                 initial_guess_[i < N ? i+1 : i].xk,
                 i);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// setStage — populate one stage of the QP
// ─────────────────────────────────────────────────────────────────────────────

void MPC::setStage(const state &xk, const control &uk,
                   const state &xk1, const int time_step)
{
    auto &stg = stages_[time_step];

    // ── 1. Constraint counts ──────────────────────────────────────────────
    if (time_step == 0) {
        stg.ng = 0;
        stg.ns = 0;
    } else {
        stg.ng = NPC;
        stg.ns = NS;
    }

    // ── 2. Guard against near-zero velocity (numerical stability) ─────────
    state xk_nz  = xk;
    if (std::abs(xk_nz.v) < 1e-3) xk_nz.v = 1e-3;

    // ── 3. Linearise dynamics: x_{k+1} = A*x_k + B*u_k + g ──────────────
    // BicycleModel::linearize already returns discrete-time (A_d, B_d)
    Eigen::MatrixXd A_d(NX, NX), B_d(NX, NU);
    model_->linearize(xk_nz, uk, A_d, B_d);

    stg.lin_model.A = A_d;
    stg.lin_model.B = B_d;

    // Affine offset: g = x_{k+1} - A*x_k - B*u_k
    StateVector xk_vec  = StateToVector(xk_nz);
    StateVector xk1_vec = StateToVector(xk1);
    ControlVector uk_vec = ControlToVector(uk);
    stg.lin_model.g = xk1_vec - A_d * xk_vec - B_d * uk_vec;

    // ── 4. Cost matrices ──────────────────────────────────────────────────
    // Cost::getCost(track, x_as_VectorXd, stage_index)
    Eigen::VectorXd x_vec(NX);
    x_vec << xk_nz.x, xk_nz.y, xk_nz.theta, xk_nz.delta, xk_nz.v;
    mpc_controller::CostMatrix cm = cost_->getCost(track_, x_vec, time_step);

    stg.cost_mat.Q = cm.Q;
    stg.cost_mat.R = cm.R;
    stg.cost_mat.S = cm.S;
    stg.cost_mat.q = cm.q;
    stg.cost_mat.r = cm.r;
    stg.cost_mat.Z = cm.Z;
    stg.cost_mat.z = cm.z;

    // ── 5. State box bounds [x, y, theta, delta, v] ───────────────────────
    // ConstraintSet returns 4-D [x, y, theta, delta]; append v separately.
    Eigen::Vector4d slb = constraints_->getStateLowerBounds();
    Eigen::Vector4d sub = constraints_->getStateUpperBounds();

    stg.l_bounds_x << slb(0), slb(1), slb(2), slb(3), params_.v_min;
    stg.u_bounds_x << sub(0), sub(1), sub(2), sub(3), params_.v_max;

    // ── 6. Input box bounds [acceleration, delta_dot] ─────────────────────
    stg.l_bounds_u << params_.a_min, params_.delta_dot_min;
    stg.u_bounds_u << params_.a_max, params_.delta_dot_max;

    // ── 7. Polytopic constraints (track boundaries, non-first stages) ──────
    if (time_step != 0) {
        // hpipm-cpp convention: l_g <= C*x + D*u <= u_g  (C=state, D=input)
        // mpcc::Stage stores D (NPC×NX state) and C (NPC×NU input) with same
        // semantics when we swap before passing to hpipm (done in hpipm_interface).
        stg.D.setZero();   // (NPC×NX) — state constraint rows
        stg.C.setZero();   // (NPC×NU) — input constraint rows
        stg.l_g.setConstant(-mpcc::INF);
        stg.u_g.setConstant( mpcc::INF);

        // Row 0: track boundary (normal direction ⊥ centerline)
        TrackConstraint tc = track_constraints_.getTrackConstraints(
                                 track_, xk_nz.s);
        stg.D(0, 0) = tc.C(0, 0);   // normal_x
        stg.D(0, 1) = tc.C(0, 1);   // normal_y
        stg.l_g(0)  = tc.lower;
        stg.u_g(0)  = tc.upper;

        // Soft-constraint slack bounds (allow small violations)
        stg.l_bounds_s.setConstant(-mpcc::INF);
        stg.u_bounds_s.setConstant( mpcc::INF);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Initial guess management
// ─────────────────────────────────────────────────────────────────────────────

void MPC::updateInitialGuess(const state &x0)
{
    for (int i = 1; i < N; i++) {
        initial_guess_[i-1] = initial_guess_[i];
    }
    initial_guess_[0].xk = x0;
    initial_guess_[0].uk.setZero();

    initial_guess_[N-1].xk = initial_guess_[N-2].xk;
    initial_guess_[N-1].uk.setZero();

    Eigen::VectorXd x_next_vec = model_->step(
        initial_guess_[N-1].xk, initial_guess_[N-1].uk, Ts_);
    initial_guess_[N].xk = VectorToState(x_next_vec.head<NX>());
    initial_guess_[N].uk.setZero();

    unwrapInitialGuess();
}

void MPC::generateNewInitialGuess(const state &x0)
{
    initial_guess_[0].xk = x0;
    initial_guess_[0].uk.setZero();

    for (int i = 1; i <= N; i++) {
        initial_guess_[i].xk.setZero();
        initial_guess_[i].uk.setZero();

        // Simple constant-velocity forward projection along arc-length
        initial_guess_[i].xk.s = initial_guess_[i-1].xk.s
                                  + Ts_ * params_.ref_velocity;
        initial_guess_[i].xk.v = params_.ref_velocity;

        // Project onto 2-D track when spline is initialised
        if (params_.horizon > 0) {
            double s_i = initial_guess_[i].xk.s;
            Eigen::Vector2d pos  = track_.getPosition(s_i);
            Eigen::Vector2d dpos = track_.getDerivative(s_i);
            initial_guess_[i].xk.x     = pos(0);
            initial_guess_[i].xk.y     = pos(1);
            initial_guess_[i].xk.theta = std::atan2(dpos(1), dpos(0));
        }
    }
    unwrapInitialGuess();
    valid_initial_guess_ = true;
}

void MPC::unwrapInitialGuess()
{
    const double L = track_.getTotalLength();
    for (int i = 1; i <= N; i++) {
        double dtheta = initial_guess_[i].xk.theta
                      - initial_guess_[i-1].xk.theta;
        if (dtheta < -M_PI) initial_guess_[i].xk.theta += 2.0 * M_PI;
        if (dtheta >  M_PI) initial_guess_[i].xk.theta -= 2.0 * M_PI;

        if (L > 0.0) {
            double ds = initial_guess_[i].xk.s - initial_guess_[i-1].xk.s;
            if (ds >  L * 0.5) initial_guess_[i].xk.s -= L;
            if (ds < -L * 0.5) initial_guess_[i].xk.s += L;
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// SQP blending
// ─────────────────────────────────────────────────────────────────────────────

std::array<OptVariables, N+1> MPC::sqpSolutionUpdate(
    const std::array<OptVariables, N+1> &last_solution,
    const std::array<OptVariables, N+1> &current_solution)
{
    std::array<OptVariables, N+1> out;
    for (int i = 0; i <= N; i++) {
        StateVector   cx = StateToVector(current_solution[i].xk);
        StateVector   lx = StateToVector(last_solution[i].xk);
        ControlVector cu = ControlToVector(current_solution[i].uk);
        ControlVector lu = ControlToVector(last_solution[i].uk);

        out[i].xk = VectorToState  (sqp_mixing_ * cx + (1.0 - sqp_mixing_) * lx);
        out[i].uk = VectorToControl(sqp_mixing_ * cu + (1.0 - sqp_mixing_) * lu);
    }
    return out;
}

// ─────────────────────────────────────────────────────────────────────────────
// extractOptVar — helper: mpcc::OptVariables → mpc_controller::OptVariables
// ─────────────────────────────────────────────────────────────────────────────

OptVariables MPC::extractOptVar(const mpcc::OptVariables &o)
{
    OptVariables v;
    v.xk = o.xk;
    v.uk = o.uk;
    return v;
}

// ─────────────────────────────────────────────────────────────────────────────
// runMPC — main entry point
// ─────────────────────────────────────────────────────────────────────────────

MPCReturn MPC::runMPC(state &x0)
{
    auto t1 = std::chrono::high_resolution_clock::now();
    int solver_status = -1;

    // ── Project state onto track spline ──────────────────────────────────
    Eigen::Vector2d x0_pos(x0.x, x0.y);
    x0.s = track_.projectOntoSpline(x0_pos);
    x0.unwrapTheta();

    // ── Warm-start or fresh initial guess ─────────────────────────────────
    if (valid_initial_guess_) {
        updateInitialGuess(x0);
    } else {
        generateNewInitialGuess(x0);
    }

    // ── SQP iterations ────────────────────────────────────────────────────
    n_no_solves_sqp_ = 0;
    std::array<OptVariables, N+1> last_guess = initial_guess_;

    for (int iter = 0; iter < n_sqp_; iter++) {
        setMPCProblem();

        // Build the initial-state vector for the solver
        StateVector x0_vec = StateToVector(x0);

        // Call solver
        std::array<mpcc::OptVariables, N+1> raw_sol =
            solver_->solveMPC(stages_, x0, &solver_status);

        if (solver_status != 0) {
            n_no_solves_sqp_++;
        } else {
            // Unpack solver output into optimal_solution_
            optimal_solution_ = raw_sol;

            // Convert to initial_guess_ format for next SQP iteration
            std::array<OptVariables, N+1> current_guess;
            for (int i = 0; i <= N; i++) {
                current_guess[i] = extractOptVar(optimal_solution_[i]);
            }

            // SQP step: blend with previous iterate (skip blend on first pass)
            if (iter > 0) {
                initial_guess_ = sqpSolutionUpdate(last_guess, current_guess);
            } else {
                initial_guess_ = current_guess;
            }
            last_guess = initial_guess_;
        }
    }

    // ── Failure tracking ──────────────────────────────────────────────────
    const int max_fails = std::max(n_sqp_ - 1, 1);
    if (n_no_solves_sqp_ >= max_fails) {
        n_non_solves_++;
    } else {
        n_non_solves_ = 0;
    }
    if (n_non_solves_ >= n_reset_) {
        valid_initial_guess_ = false;
    }

    // ── Timing ────────────────────────────────────────────────────────────
    auto t2 = std::chrono::high_resolution_clock::now();
    double time_mpc = std::chrono::duration<double>(t2 - t1).count();

    return { initial_guess_[0].uk, initial_guess_, time_mpc };
}

// ─────────────────────────────────────────────────────────────────────────────
// setTrack
// ─────────────────────────────────────────────────────────────────────────────

void MPC::setTrack(const Eigen::VectorXd &X, const Eigen::VectorXd &Y)
{
    track_.generateSpline(X, Y);
}

} // namespace mpc_controller
