# Deep Code Review Prompt — FSAI MPC Controller (C++/ROS 2)

> **Context for Opus:** You are acting as a senior control-systems software engineer with deep expertise in Model Predictive Control, real-time C++, convex optimization (QP / HPIPM), and ROS 2. You are performing a comprehensive, adversarial audit of a Formula Student Autonomous (FSAI) MPC controller that runs on a real race car. Bugs here have safety implications. Be thorough, precise, and unforgiving.

---

## Project Overview

A C++/ROS 2 MPC controller for autonomous racing (Formula Student AI 2026). The optimizer is **Sequential Quadratic Programming (SQP)** over a **kinematic bicycle model** with a **horizon N=20** and **sampling time Ts**. The QP solver backend is **HPIPM** (high-performance interior-point method) via the `hpipm-cpp` wrapper. The track reference is an **arc-length-parameterized cubic spline** (`ArcSpline`). Cost combines **contouring error**, **heading error**, **input regularization**, and **soft track-boundary constraints**.

---

## File / Module Map

```
src/mpc_controller/src/
  config.h                        — compile-time constants (NX=5, NU=2, N=20, NPC=3, NS=1)
  types.h                         — state/control structs, Eigen typedefs, PathToJson
  types.cpp                       — (inspect)
  config.cpp                      — (inspect)
  main.cpp                        — standalone test entrypoint (NOT the ROS node)

  MPC/
    mpc.h / mpc.cpp               — PRIMARY: SQP loop, warm-start, stage construction
    mpc_solver.h / mpc_solver.cpp — SECONDARY: alternative solver class (check if used)

  Bicycle Model/
    bicycle_model.h / .cpp        — dynamics, step (RK4/Euler), numerical linearization

  Integrator/
    integration_methods.h / .cpp  — eulerForward<>, rungeKutta4<>, predictTrajectory()

  Cost/
    Cost.h / cost.cpp             — contouring + heading + input + soft-constraint cost

  Constraints/
    constraints.h / .cpp          — box bounds (state 4D, control 2D)
    trackConstraints.h / .cpp     — polytopic track-boundary constraint (1 row used of NPC=3)

  Interfaces/
    solver_interface.h            — abstract SolverInterface + Stage/OptVariables/CostMatrix (mpcc ns)
    hpipm_interface.h / .cpp      — HPIPM QP solve implementation

  Spline/
    Arc_Spline.h / .cpp           — arc-length spline, projectOntoSpline(), getPosition/Derivative
    Cubic_Spline.h / .cpp         — underlying cubic spline

  Params/
    params.h / .cpp               — JSON parameter loader, all physical / cost / bound constants
    *.json                        — config files

  IPG Node/
    mpc_controller_node.h / .cpp  — ROS 2 node (odometry → MPC → cmd_vel)
    simulator_model.h / .cpp      — (inspect)

  Solver/                         — EMPTY directory (investigate)
```

---

## Known Architecture Facts (gathered from reading the code)

### State & Control
- **State** (`mpc_controller::state`, 5D active): `[x, y, theta, delta, v]`  
  The struct also carries **dead fields**: `vx, vy, r, Throttle, s` — explicitly labeled "NOT used in MPC dynamics" in the comments.
- **Control** (`mpc_controller::control`, 2D active): `[D_dot (=acceleration a), delta_dot]`  
  The struct also carries **dead field**: `dV_ghost` — explicitly zero-set at every call site.

### Two Solver Classes
- `mpc_controller::MPC` (mpc.h) — the live SQP solver used by the ROS node  
- `mpcc::MPCSolver` (mpc_solver.h) — separate class using **4D state** (`Eigen::Vector4d`), `Matrix4d Q`, `Matrix2d R`, no HPIPM integration, no link to the rest of the pipeline

### Dual Namespaces
- `mpc_controller` — owns `state`, `control`, `Params`, `BicycleModel`, `Cost`, `MPC`, `ArcSpline`
- `mpcc` — owns `Stage`, `CostMatrix`, `SolverInterface`, `OptVariables`, `HpipmInterface`
- `config.h` defines many Eigen `typedef`s in `mpc_controller`; `solver_interface.h` redefines similar ones in `mpcc`

### Linearization
- `BicycleModel::linearize()` uses **numerical finite differences** (perturbation = `params_.linearize_eps`)
- Discretization is **first-order Euler hold**: `A_d = I + A_c * dt`, `B_d = B_c * dt`
- But the integrator in `step()` uses **RK4**

### Warm-Start Shift (updateInitialGuess)
```cpp
for (int i = 1; i < N; i++) {       // loop stops at N-1
    initial_guess_[i-1] = initial_guess_[i];
}
initial_guess_[0].xk = x0;
initial_guess_[N-1].xk = initial_guess_[N-2].xk;  // duplicate, not old [N]
```

### Stage Construction (setMPCProblem / setStage)
- Stage 0: `ng=0, ns=0` — **no polytopic or soft constraints at the initial stage**
- Stages 1..N: `ng=NPC=3, ns=NS=1` — but only **row 0 of D is populated** (track normal); rows 1 and 2 left at zero with `l_g = -INF, u_g = +INF`
- Track constraint uses **position at linearization point** `xk_nz.s`, not next predicted `s`
- State box bounds: `ConstraintSet` returns 4D, `v` bounds appended manually in `setStage` — inconsistency with the 4D vs 5D split

### Cost
- Two separate `CostMatrix` structs exist: `mpc_controller::CostMatrix` (Cost.h) and `mpcc::CostMatrix` (solver_interface.h) — converted manually in `setStage`, field-by-field

### Params
- `params_.horizon` is referenced in `generateNewInitialGuess()` but `Params` struct needs to be checked whether this field actually exists
- `params_.linearize_eps` is described as coming from `motor_model.json` which is conceptually wrong (eps is a numerical method parameter, not a motor property)

### StateInputIndexes (config.h)
- `r = 2` (yaw rate → mapped to theta index)
- `vs = 4` (virtual speed → mapped to v index)  
- `phi = 2` (heading alias → also mapped to theta index)
- `dD = 0`, `dDelta = 1` (MPCC-style names mapped to acceleration/delta_dot)

---

## Requested Analysis Tasks

### 1. Logic Bugs & Correctness Issues

For each of the following, confirm whether it is a bug, explain the exact impact, and provide the correct fix:

**A. Warm-start shift in `updateInitialGuess`**  
The loop runs `for i = 1 to N-1`, copying `[i-1] ← [i]`. This means `initial_guess_[N-1]` is never updated to `initial_guess_[N]` (old last stage). Instead it is manually set to `initial_guess_[N-2]` (creating a duplicate). Is this an off-by-one bug? What is the correct receding-horizon warm-start procedure? Should the loop run to `N` inclusive?

**B. Linearization vs. integration consistency**  
`linearize()` uses a first-order Euler hold (`A_d = I + A_c*dt`), but `step()` uses RK4. For SQP to converge, the linearized model used to build the QP should be consistent with the integration used to propagate the nominal trajectory. Is this mismatch a correctness issue? Does it cause SQP to diverge or simply slow convergence? What is the recommended fix (analytical Jacobians + ZOH / exact discretization)?

**C. Track constraint at wrong arc-length**  
In `setStage(xk, uk, xk1, k)`, the track constraint calls `getTrackConstraints(track_, xk_nz.s)`. The arc-length `s` is the **current** state at stage k, but the constraint bounds the **next** state `xk1`. Should the constraint be evaluated at the predicted next arc-length instead? What is the practical impact (constraint violation, conservative/aggressive boundary)?

**D. Stage 0 has no polytopic or soft constraints (`ng=0, ns=0`)**  
The initial stage fixes `x0` as an equality constraint — is it therefore correct to have no polytopic constraints here? Or should the track boundary also be enforced at k=0? What does HPIPM do if `ng=0` at stage 0?

**E. `params_.horizon` field**  
`generateNewInitialGuess` accesses `params_.horizon`. Scan `params.h` and the JSON files to determine if this field is defined and loaded. If it is missing, what compilation or runtime error occurs? If it exists, is `if (params_.horizon > 0)` the right guard (should it compare against `N` instead)?

**F. Numerical linearization of analytical model**  
The kinematic bicycle model has closed-form Jacobians:
```
∂f/∂x: ∂(ẋ)/∂theta = -v*sin(theta), ∂(ẋ)/∂v = cos(theta), etc.
```
Using numerical finite-differences at every stage of every SQP iteration multiplies computation. Is the perturbation `linearize_eps` correctly sized to avoid cancellation error for typical state magnitudes in FSAI? Provide the analytical Jacobians and estimate the computational saving.

---

### 2. Redundant / Orphaned Code

**A. `mpc_solver.h` / `mpc_solver.cpp` — `MPCSolver` class**  
This class uses a 4D state (`Eigen::Vector4d`), its own `Params` reference, a different warm-start (`Eigen::MatrixXd`), and has no connection to HPIPM or `Stage`. Verify:
- Is `MPCSolver` instantiated or called anywhere in the project?
- Does it share any logic with `mpc_controller::MPC`?
- Is it safe to delete? What would break?

**B. `Solver/` directory**  
The directory exists but is empty. Is it referenced in `CMakeLists.txt`? Should it be removed?

**C. Dead fields in `state` struct**  
`vx, vy, r, Throttle` are labeled "NOT used in MPC". They are allocated on the stack in every `state` instance (N+1 stages × sizeof(state)). Are these used anywhere in the ROS node, simulator model, or spline projection? If truly unused, propose the clean removal path without breaking other consumers.

**D. Dead field `dV_ghost` in `control` struct**  
Always set to 0.0. Used anywhere? Propose removal.

**E. Dual `CostMatrix` structs (`mpc_controller::CostMatrix` in Cost.h vs `mpcc::CostMatrix` in solver_interface.h)**  
These are nearly identical. In `setStage`, cost matrices are copied field-by-field from one to the other. Is there a reason for two separate structs, or is this an artifact of porting from a prior codebase? Can they be unified?

**F. `StateInputIndexes` aliases in `config.h`**  
`r=2`, `vs=4`, `phi=2`, `dD=0`, `dDelta=1` are MPCC-specific aliases that map to physical state indices. Are these used in Cost or Constraints and could they introduce index errors if the state ordering changes? Are they actually referenced in the cost/constraint code?

---

### 3. Performance Issues

**A. Per-stage `std::make_unique` / heap allocations in hot path**  
`MPC::MPC()` allocates `constraints_`, `model_`, `cost_`, `solver_` via `std::make_unique`. This happens at construction time (not per-solve), so it is fine. But check: are any heap allocations in `setStage`, `getCost`, `getTrackConstraints`, or `solveMPC` called within the 10 ms real-time budget?

**B. `std::function` in integration templates**  
`eulerForward<>` and `rungeKutta4<>` accept `std::function<...>` which involves heap allocation and virtual dispatch overhead. In `BicycleModel::step()` and `predictTrajectory()`, these are called inside the SQP loop (N stages × n_sqp iterations). Estimate the overhead vs passing a template functor. Recommend replacing with a template lambda or Curiously Recurring Template Pattern (CRTP).

**C. Numerical finite-difference Jacobians**  
In `linearize()`, `dynamics()` is called `2*(NX+NU) = 14` times per stage to build `A` and `B`. Over N=20 stages and n_sqp SQP iterations, this is `20 × n_sqp × 14` dynamics evaluations per control step. Compare to analytical Jacobians (0 extra evaluations). Is this real-time feasible at 100 Hz?

**D. `ArcSpline::projectOntoSpline()` call in `runMPC()`**  
Called every control cycle. If the spline has N_Spline=5000 sample points, what is the complexity? Is it a linear scan, binary search, or Newton iteration? Confirm the implementation and flag if it is a bottleneck.

**E. `Eigen::MatrixXd` (dynamic) vs `Eigen::Matrix<double, NX, NX>` (fixed)**  
In `setStage`, `A_d(NX, NX)` and `B_d(NX, NU)` are declared as `Eigen::MatrixXd` (dynamic). Since NX=5/NU=2 are compile-time constants, fixed-size matrices would avoid heap allocation and enable full vectorization. Audit `setStage`, `BicycleModel::linearize()`, and `BicycleModel::dynamics()` for similar dynamic-size regressions.

**F. `std::array<mpcc::Stage, N+1>` copying in `setMPCProblem`**  
`stages_` is a member array rebuilt every SQP iteration. Are the Eigen matrices inside `Stage` (A, B, g, Q, R, S, D, C etc.) zero-initialized every call? Is there unnecessary initialization or copying?

---

### 4. Code Structure & Cross-File Linking

**A. `mpcc` vs `mpc_controller` namespace split**  
The project uses both namespaces with heavy cross-pollination. `solver_interface.h` is `#include`d inside `mpc.h` which is in `mpc_controller`. The `using` aliases `State = mpc_controller::state` inside `mpcc` create tight coupling. Assess:
- Is the namespace split intentional (separation of QP abstraction from control)?
- Does it cause any ambiguity (two `CostMatrix`, two `OptVariables`)?
- Recommend consolidation or clear boundary documentation.

**B. `#include` chain and cyclic risk**  
`config.h` defines `NX, NU, N` as `#define` macros and then includes `types.h`. `types.h` includes `config.h`. Check for cyclic includes. Note the comment in `params.h` warning that `nlohmann/json.hpp` conflicts with the `#define N 20` macro (`json`'s template uses `N`). Is this actually guarded? What happens if someone includes `<nlohmann/json.hpp>` before `config.h` in a translation unit?

**C. `hpipm_interface.h` includes `"config.h"` and `"types.h"` without path prefix**  
These are relative includes that will fail if the file is compiled from a different directory. Verify the include paths in `CMakeLists.txt` ensure these resolve correctly. Solver headers should use `<mpc_controller/...>` style or absolute paths via CMake `target_include_directories`.

**D. `CMakeLists.txt` source list**  
Audit `src/mpc_controller/CMakeLists.txt`:
- Is `mpc_solver.cpp` listed as a source? (If MPCSolver is orphaned, it should be removed)
- Is `Solver/` directory added (it's empty)?
- Are all `.cpp` files in `Bicycle Model/`, `IPG Node/`, `Spline/` etc. included with correct paths (spaces in directory names like `"Bicycle Model"` and `"IPG Node"` can cause CMake issues on some platforms)?

**E. `main.cpp` vs ROS node**  
`main.cpp` creates `Params`, `ConstraintSet`, `Cost`, `BicycleModel` but has a `// TODO: Implement main control loop`. It is not the ROS entry point. The ROS entry point is `IPG Node/mpc_controller_node.cpp`. Does `main.cpp` still compile as part of the package? Does it conflict with the ROS node's `main()`? This could cause a linker error (`multiple definition of main`).

---

### 5. MPC Formulation Correctness

**A. Cost function structure**  
The cost combines contouring error, heading error, input cost, and soft constraints. Verify in `cost.cpp`:
- Is the contouring error computed as the **signed orthogonal distance** to the spline? Is the sign convention consistent (positive = left of centerline)?
- Is the heading error `theta - theta_ref` properly wrapped to `(-π, π)`?
- Are the terminal cost multipliers (`q_c_N_mult`, `q_r_N_mult`) applied correctly only at k=N?
- Does the **cross-term S matrix** in the cost (state-control coupling) make physical sense for this formulation? If not used, is it zero?

**B. Soft constraint formulation**  
NS=1 soft slack for track boundary. In `setStage`:
```cpp
stg.l_bounds_s.setConstant(-mpcc::INF);
stg.u_bounds_s.setConstant( mpcc::INF);
```
Unbounded slack means the constraint is never hard-enforced. The softness is controlled only by the `Z_MPC` (quadratic) and `z_MPC` (linear) penalty weights. Confirm that `sc_quad_track` and `sc_lin_track` in the cost are non-zero and that HPIPM receives the `Zl/Zu/zl/zu` matrices correctly.

**C. Track constraint only has 1 active row out of NPC=3**  
`NPC=3` is set in `config.h` as "Number of Polytopic Constraints" but only 1 constraint (track normal) is used. HPIPM is told `ng=NPC=3` but rows 1/2 of D are zero with `l_g=-INF, u_g=+INF`. This wastes solver memory and adds 2 trivially-satisfied constraints at every non-initial stage. Should `NPC` be reduced to 1, or are rows 1/2 reserved for future use (e.g., tire friction ellipse)?

**D. SQP blending (sqp_mixing)**  
The `sqpSolutionUpdate` blends `sqp_mixing * current + (1-sqp_mixing) * last`. Standard SQP uses a **line search** or trust-region step. Fixed blending (mixing factor = constant) can cause oscillation or slow convergence. Assess:
- Is fixed blending appropriate for real-time SQP?
- If `sqp_mixing = 1.0` (default in the default constructor), is blending disabled entirely?
- Is there a stability guarantee for any particular mixing value?

**E. Affine offset `g = xk1 - A*xk - B*uk` correctness**  
This offset linearizes around the nominal trajectory. If `xk1` is from the initial guess (propagated by one step), and `A_d, B_d` are also computed at `xk`, then `g` should effectively be zero if the guess is consistent with the linearized model. Is `g` actually negligible, or does the RK4 vs Euler mismatch make `g` large? A large `g` biases the linear prediction away from the true nonlinear trajectory.

**F. Velocity lower bound and division-by-zero**  
`v_min` is likely 0 or a small positive value. The kinematic bicycle model dynamics divide by `v` (via `tan(delta)/L * v`):
```cpp
X_dot(2) = (v / params_.wheelbase) * std::tan(delta);
```
This is multiplied by v which is fine, but the **linearization** computes `∂(X_dot(2))/∂delta = v/L * sec²(delta)`. At `v ≈ 0` this is fine (approaches 0). However check if there is a `tan(delta)` overflow guard — at `delta → ±π/2` (beyond physical limits), `tan` blows up. Is `delta_max = 0.6109 rad` sufficient to prevent this? Verify the box constraint is enforced **before** the linearization point enters `linearize()`.

---

### 6. Output Format

For each issue found, structure your response as:

```
SEVERITY: [CRITICAL | HIGH | MEDIUM | LOW | INFO]
FILE: <filename:line>
CATEGORY: [Bug | Redundant | Performance | Structure | Formulation]
ISSUE: <one-line description>
DETAIL: <explanation with relevant code snippet>
FIX: <concrete corrective action with corrected code where applicable>
```

At the end, provide:
1. A **priority-ordered action list** (fix critical bugs first, then performance, then cleanup)
2. A **dependency graph** showing which files include which (to identify unsafe coupling)
3. A **"safe to delete" list** of files/classes/fields that are confirmed dead code

Do not summarize — be exhaustive. Every issue matters on a race car.
