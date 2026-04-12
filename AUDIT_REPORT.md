# FSAI MPC Controller — Full Code Audit Report

> **Auditor role**: Senior control-systems software engineer.  
> **Date**: 2026-04-12  
> **Scope**: Every `.h`, `.cpp`, `.json` under `src/mpc_controller/`, plus `CMakeLists.txt` and `main.cpp`.

---

## 1. LOGIC BUGS & CORRECTNESS ISSUES

---

### 1A — `computeArcLength()` off-by-one: `s(1)` is never set, last segment is skipped

```
SEVERITY : CRITICAL
FILE     : Spline/Arc_Spline.cpp:50-57
CATEGORY : Bug
```

**ISSUE**: The arc-length vector `s` is uninitialized at index 1, and the last segment (n−2 → n−1) is never accumulated.

**DETAIL**:
```cpp
s(0) = 0.0;
for(int i = 1; i < n - 1; ++i)       // i goes from 1 to n-2
{
    dx = splineData.x(i + 1) - splineData.x(i);   // computes distance from i to i+1
    dy = splineData.y(i + 1) - splineData.y(i);
    distance = std::sqrt(dx * dx + dy * dy);
    s(i + 1) = s(i) + distance;                    // writes s[2..n-1] using s[1..n-2]
}
```

Problems:
1. `s(1)` is never explicitly assigned. It relies on `s(0)` in the first iteration (`i=1`), but the distance computed is from point 1→2, **not** 0→1. So **s(1) is garbage** (Eigen does not zero-init `Eigen::VectorXd(n)`).
2. The loop skips the first segment (0→1) entirely.
3. The resulting arc-length is wrong for every downstream consumer (spline fitting, projection, track constraints).

**FIX**:
```cpp
s(0) = 0.0;
for (int i = 0; i < n - 1; ++i) {
    dx = splineData.x(i + 1) - splineData.x(i);
    dy = splineData.y(i + 1) - splineData.y(i);
    distance = std::sqrt(dx * dx + dy * dy);
    s(i + 1) = s(i) + distance;
}
```

---

### 1B — Warm-start shift in `updateInitialGuess`: off-by-one loses the last stage

```
SEVERITY : HIGH
FILE     : MPC/mpc.cpp:152-168
CATEGORY : Bug
```

**ISSUE**: The classic receding-horizon warm-start should shift all N+1 entries left by one. The current code only shifts entries 1..N-1 into slots 0..N-2, then manually fabricates slots N-1 and N. Slot `N-1` is set to `N-2` (duplicate), losing the original `initial_guess_[N]`.

**DETAIL**:
```cpp
for (int i = 1; i < N; i++) {               // i = 1..N-1 only
    initial_guess_[i-1] = initial_guess_[i]; // writes slots 0..N-2
}
initial_guess_[0].xk = x0;                  // overwrite slot 0
initial_guess_[0].uk.setZero();

initial_guess_[N-1].xk = initial_guess_[N-2].xk;  // duplicate, not old [N]
```

After this, `initial_guess_[0]` gets the current state x0 (correct), but:
- Old `initial_guess_[N]` (which was the far end of the previous horizon) is discarded.
- `initial_guess_[N-1]` ends up as a copy of `initial_guess_[N-2]` — the horizon "flattens" at the end.

**FIX** — Standard receding-horizon shift:
```cpp
void MPC::updateInitialGuess(const state &x0) {
    // Shift entire horizon left by one step
    for (int i = 0; i < N; i++) {
        initial_guess_[i] = initial_guess_[i + 1];
    }
    // Fix slot 0 to current measured state
    initial_guess_[0].xk = x0;
    initial_guess_[0].uk.setZero();

    // Extend horizon by one step at the tail
    initial_guess_[N].uk.setZero();
    Eigen::VectorXd x_next_vec = model_->step(
        initial_guess_[N-1].xk, initial_guess_[N-1].uk, Ts_);
    initial_guess_[N].xk = VectorToState(x_next_vec.head<NX>());

    unwrapInitialGuess();
}
```

---

### 1C — Linearization (Euler) vs integration (RK4) mismatch

```
SEVERITY : HIGH
FILE     : Bicycle Model/bicycle_model.cpp:126-148
CATEGORY : Bug / Formulation
```

**ISSUE**: `linearize()` uses first-order Euler discretization (`A_d = I + A_c*dt`), but `step()` uses RK4. This means the affine offset `g = x_{k+1} − A_d*x_k − B_d*u_k` computed in `setStage()` is **not** close to zero — it absorbs the entire difference between RK4-propagated states and Euler-linearized predictions.

**IMPACT**: The SQP QP solves a problem with a large, non-negligible `g` that biases every stage. The result is:
- Slower or inconsistent SQP convergence.
- The linearized QP model poorly predicts the actual trajectory.
- With `n_sqp = 1` (as used in the ROS node), the single QP solutions is directly used — so the bias directly corrupts the control output.

**FIX** (recommended — use analytical Jacobians + match discretization):
```cpp
void BicycleModel::linearize(const state& X, const control& U,
                             Eigen::MatrixXd& A, Eigen::MatrixXd& B) const {
    double theta = X.theta, delta = X.delta, v = X.v;
    double L = params_.wheelbase;
    double a = U.D_dot, dd = U.delta_dot;

    // Continuous-time Jacobian A_c (analytical)
    Eigen::MatrixXd Ac = Eigen::MatrixXd::Zero(5, 5);
    Ac(0, 2) = -v * std::sin(theta);
    Ac(0, 4) = std::cos(theta);
    Ac(1, 2) =  v * std::cos(theta);
    Ac(1, 4) = std::sin(theta);
    double sec2 = 1.0 / (std::cos(delta) * std::cos(delta));
    Ac(2, 3) = (v / L) * sec2;
    Ac(2, 4) = std::tan(delta) / L;

    // Continuous-time Jacobian B_c (analytical)
    Eigen::MatrixXd Bc = Eigen::MatrixXd::Zero(5, 2);
    Bc(3, 1) = 1.0;
    Bc(4, 0) = 1.0;

    // Euler ZOH discretization (consistent with single-step forward model)
    A = Eigen::MatrixXd::Identity(5, 5) + Ac * params_.dt;
    B = Bc * params_.dt;
}
```
This also eliminates 14 dynamics evaluations per stage (see Performance §3C).

---

### 1D — Track constraint evaluated at wrong arc-length

```
SEVERITY : MEDIUM
FILE     : MPC/mpc.cpp:138-142
CATEGORY : Bug
```

**ISSUE**: `setStage(xk, uk, xk1, k)` calls `getTrackConstraints(track_, xk_nz.s)` using the current state's arc-length `s`. But the polytopic constraint at stage `k` is meant to bound the **predicted state at stage k** (which was propagated from k−1). For k ≥ 1, the constraint normal direction and bounds should use the arc-length of `xk` (the state at this stage), which is correct — **but** the `s` field of `xk` may not be set because`xk` comes from `initial_guess_[k].xk`, and the `s` field is only set during `generateNewInitialGuess()`. During `updateInitialGuess()`, the shifted states retain their old `s` values, which become stale after one shift.

**FIX**: Re-project s for every state in the initial guess before building the QP:
```cpp
void MPC::setMPCProblem() {
    for (int i = 0; i <= N; i++) {
        // Re-project onto track to get correct s for constraints/cost
        Eigen::Vector2d pos(initial_guess_[i].xk.x, initial_guess_[i].xk.y);
        initial_guess_[i].xk.s = track_.projectOntoSpline(pos);
        setStage(initial_guess_[i].xk, initial_guess_[i].uk,
                 initial_guess_[i < N ? i+1 : i].xk, i);
    }
}
```
**Caveat**: This adds N+1 projection calls per SQP iteration, each running Newton's method (up to 20 iterations). May impact real-time performance — cache or amortize.

---

### 1E — `getCost` receives state without `s` being set

```
SEVERITY : MEDIUM
FILE     : MPC/mpc.cpp:100-103, Cost/cost.cpp:12
CATEGORY : Bug
```

**ISSUE**: In `setStage`, the state `xk_nz` is passed to `cost_->getCost()` as an Eigen vector without `s`:
```cpp
Eigen::VectorXd x_vec(NX);
x_vec << xk_nz.x, xk_nz.y, xk_nz.theta, xk_nz.delta, xk_nz.v;
```
Inside `getCost`, this is unpacked back to a `state` struct, but `x.s` is **zero-initialized** (the `s` field is lost). Then `getRefPoint()` uses `x.s` to look up the track reference. If `s == 0`, the entire cost is computed relative to arc-length 0 (the start of the track), not the actual position along the track.

**FIX**: Either pass the full `state` struct directly to `getCost`, or add `s` to the Eigen vector:
```cpp
// Option A: Pass state struct directly
CostMatrix cm = cost_->getCost(track_, xk_nz, time_step);
```

---

### 1F — `#undef N` in cost.cpp breaks all downstream uses

```
SEVERITY : HIGH
FILE     : Cost/cost.cpp:78
CATEGORY : Bug
```

**ISSUE**: `cost.cpp` contains:
```cpp
#undef N  // Undefine the macro N from config.h to use local variable
const int N = params_.horizon;
```
The `#undef N` is executed at file scope within `getContouringCost()`. Since this is inside a function body, it affects the rest of the translation unit. If any code after this line in the same `.cpp` file uses the macro `N` (e.g., `std::array<..., N+1>`), it will use the now-undefined `N`, causing a compile error. Currently this works by luck because `N` is not referenced later in cost.cpp, but it is extremely fragile.

**FIX**: Use `params_.horizon` directly instead of `#undef`:
```cpp
const int horizon = params_.horizon;
// Replace all uses of N in this function with `horizon`
```

---

### 1G — `theta_min`/`theta_max` box constraint prevents unwrapping

```
SEVERITY : MEDIUM
FILE     : Params/bounds.json, MPC/mpc.cpp:267
CATEGORY : Formulation Bug
```

**ISSUE**: `theta_min = -π, theta_max = +π` as box constraints. But the MPC's `unwrapInitialGuess()` allows theta to go beyond ±π (by adding/subtracting 2π to maintain continuity). If the solver then clips theta to [−π, π], it creates discontinuities. Either the unwrapping is useless (solver clips it), or the box constraint fights the unwrapping.

**FIX**: Set `theta_min = -1e20, theta_max = 1e20` (effectively unbounded). Heading continuity is handled by the unwrapping logic.

---

## 2. REDUNDANT / ORPHANED CODE

---

### 2A — `MPCSolver` class (mpc_solver.h / mpc_solver.cpp) — DEAD CODE

```
SEVERITY : HIGH
FILE     : MPC/mpc_solver.h, MPC/mpc_solver.cpp
CATEGORY : Redundant
```

**ISSUE**: `MPCSolver` is a completely separate MPC implementation using:
- **CasADi + IPOPT** backend (not HPIPM)
- **4D state** (`Eigen::Vector4d`) — missing velocity as a state
- `config_.Q` as `Matrix4d`, `config_.R` as `Matrix2d` — fields that **do not exist** in the `Params` class
- `config_.Q_terminal` — **does not exist** in `Params`
- `mpc_utils::wrapAngle()` — a function that is **never defined** in the codebase
- **Not listed in CMakeLists.txt** source files → not compiled

This class is never instantiated, never called, and cannot compile. It also drags in `#include <casadi/casadi.hpp>` which the CMakeLists explicitly removed.

**VERDICT**: Safe to delete entirely. Nothing references it.

---

### 2B — `Solver/` directory — EMPTY

```
SEVERITY : LOW
FILE     : src/mpc_controller/src/Solver/
CATEGORY : Redundant
```

Not referenced in CMakeLists. Safe to delete.

---

### 2C — `SimulatorModel` class — BROKEN, UNUSED

```
SEVERITY : MEDIUM
FILE     : IPG Node/simulator_model.h, IPG Node/simulator_model.cpp
CATEGORY : Redundant
```

**ISSUE**: 
- References `MPCConfig` type which **does not exist** anywhere in the codebase (should be `Params`).
- Uses `config_.wheelbase`, `config_.dt` — fields that would only work with `Params`, not the non-existent `MPCConfig`.
- **Not listed in CMakeLists.txt** source files → not compiled.
- Never instantiated by the ROS node (`mpc_controller_node.cpp` does not include it).

**VERDICT**: Safe to delete. If needed later, must be rewritten with `Params` instead of `MPCConfig`.

---

### 2D — Dead fields in `state` struct

```
SEVERITY : LOW
FILE     : types.h:27-30
CATEGORY : Redundant
```

Fields `vx`, `vy`, `r`, `Throttle` are labeled "NOT used in MPC". Scanned all usage:
- `vx`, `vy`: Never read or written outside `setZero()`.
- `r`: Never read outside `setZero()`.
- `Throttle`: Never read outside `setZero()`.
- They do increase `sizeof(state)` by 32 bytes (4 doubles), multiplied by every `state` instance.

**VERDICT**: Safe to remove. No consumer reads them.

---

### 2E — Dead field `dV_ghost` in `control` struct

```
SEVERITY : LOW
FILE     : types.h:71
CATEGORY : Redundant
```

Always set to `0.0` at every call site (`vectorToControl`, lambda adaptors). Never read. Safe to remove.

---

### 2F — Duplicate `CostMatrix` structs

```
SEVERITY : MEDIUM
FILE     : Cost/Cost.h (mpc_controller::CostMatrix) vs Interfaces/solver_interface.h (mpcc::CostMatrix)
CATEGORY : Redundant
```

**ISSUE**: Two nearly identical structs with identical field names. In `setStage()`, the output of `cost_->getCost()` (`mpc_controller::CostMatrix`) is copied field-by-field into `stg.cost_mat` (`mpcc::CostMatrix`). The only difference: `mpc_controller::CostMatrix` uses `Eigen::MatrixXd` (dynamic) while `mpcc::CostMatrix` uses fixed-size `Eigen::Matrix<double, NX, NX>`.

**FIX**: Unify into a single struct using fixed-size matrices. Use it everywhere.

---

### 2G — Duplicate state/control converter functions

```
SEVERITY : LOW
FILE     : types.h/types.cpp vs Interfaces/solver_interface.h/solver_interface.cpp
CATEGORY : Redundant
```

- `mpc_controller::StateToVector` / `mpc_controller::stateToVector` (two functions with different capitalization doing the same thing!) in types.h/types.cpp
- `mpcc::stateToVector` in solver_interface.cpp
- Similarly for `VectorToState`, `VectorToControl`, `ControlToVector`

All three sets do the exact same conversion. **Three implementations of the same trivial function.**

**FIX**: Keep one set (in types.h), delete the rest. Add `using mpc_controller::StateToVector;` in mpcc namespace if needed.

---

### 2H — `config.cpp` is empty

```
SEVERITY : INFO
FILE     : config.cpp
CATEGORY : Redundant
```

Contains only a namespace and a comment. No code. Can be removed from CMakeLists.txt source list.

---

### 2I — `main.cpp` has no control loop, conflicts with ROS node

```
SEVERITY : HIGH
FILE     : main.cpp
CATEGORY : Redundant / Structural
```

`main.cpp` defines `int main()` and is in the source tree but NOT listed in CMakeLists.txt (which only builds `mpc_controller_node` from `IPG Node/mpc_controller_node.cpp`). If someone accidentally adds it, it will cause a **linker error** (multiple `main` definitions).

**FIX**: Move to a `test/` or `standalone/` directory, or delete it.

---

## 3. PERFORMANCE ISSUES

---

### 3A — `std::function` in integration templates (heap allocation in hot path)

```
SEVERITY : HIGH
FILE     : Integrator/integration_methods.h:31, :60
CATEGORY : Performance
```

**ISSUE**: `eulerForward<>` and `rungeKutta4<>` accept `std::function<Eigen::VectorXd(...)>`. Despite being templates, using `std::function` involves:
- Heap allocation for the lambda capture (closure exceeds SBO threshold)
- Virtual dispatch on every call

In `BicycleModel::step()`, a lambda is created and wrapped in `std::function` **every call**. With N=20 stages × n_sqp iterations, this is 20+ heap alloc/free cycles per MPC solve.

**FIX**: Make the dynamics function a template parameter instead of `std::function`:
```cpp
template <int STATE_DIM, int CONTROL_DIM, typename DynamicsFn>
Eigen::VectorXd rungeKutta4(
    const Eigen::VectorXd& state,
    const Eigen::VectorXd& control,
    DynamicsFn state_derivative_fn,   // deduced, zero-cost
    double dt);
```

---

### 3B — Numerical Jacobians: 14 dynamics evaluations per stage

```
SEVERITY : HIGH
FILE     : Bicycle Model/bicycle_model.cpp:120-148
CATEGORY : Performance
```

**ISSUE**: `linearize()` perturbs each of 5 states and 2 controls → 7 perturbations. Each requires one `dynamics()` call, plus the nominal → **8 calls per stage** (not 14 — corrected from prompt; 1 nominal + 7 perturbed). Over N=20 stages with 1 SQP iteration: 160 dynamics evaluations per MPC solve.

The kinematic bicycle model has trivial analytical Jacobians (see fix in §1C). With analytical Jacobians: **0 extra dynamics calls**.

**Savings**: Eliminates ~160 dynamics calls per solve. At 100 Hz, that's 16,000 evaluations/second saved.

---

### 3C — `Eigen::MatrixXd` (dynamic) where fixed-size suffices

```
SEVERITY : MEDIUM
FILE     : Bicycle Model/bicycle_model.cpp, MPC/mpc.cpp:86-87, Cost/Cost.h
CATEGORY : Performance
```

**ISSUE**: Throughout the codebase, `Eigen::MatrixXd` and `Eigen::VectorXd` are used where dimensions are compile-time constants:
- `bicycle_model.cpp`: `Eigen::VectorXd X_dot = Eigen::VectorXd::Zero(5)` → should be `Eigen::Matrix<double,5,1>`
- `mpc.cpp`: `Eigen::MatrixXd A_d(NX, NX)` → should be `Eigen::Matrix<double,NX,NX>`
- `Cost.h`: `CostMatrix` uses `Eigen::MatrixXd` for Q, R, S, q, r, Z, z

Dynamic-size matrices use heap allocation. Fixed-size matrices (≤4×4 or with known dimensions like 5×5) are stack-allocated and benefit from SIMD vectorization.

**FIX**: Replace all dynamic Eigen types with fixed-size equivalents where NX=5, NU=2, NPC=3, NS=1 are known at compile time.

---

### 3D — `ArcSpline::projectOntoSpline()` — linear scan fallback

```
SEVERITY : MEDIUM
FILE     : Spline/Arc_Spline.cpp:200-220
CATEGORY : Performance
```

**ISSUE**: When the initial guess is far (>5m) from the spline, the code does a linear scan over all 5000 spline points:
```cpp
Eigen::ArrayXd diff_x_all = splineData.x.array() - point(0);
Eigen::ArrayXd diff_y_all = splineData.y.array() - point(1);
Eigen::ArrayXd dist_square = diff_x_all.square() + diff_y_all.square();
```
This is O(N_SPLINE) = O(5000) per call. Called once per MPC cycle is acceptable, but if used per-stage (see §1D fix), it becomes 20×5000 = 100,000 distance computations.

**FIX**: Use a k-d tree or spatial hash for the initial guess, followed by Newton refinement. Alternatively, maintain a monotonically-advancing `s` estimate from the previous solve.

---

### 3E — Stage.D/C zero-filled then overwritten for only row 0

```
SEVERITY : LOW
FILE     : MPC/mpc.cpp:131-143
CATEGORY : Performance
```

For every non-initial stage, `D` (3×5) and `C` (3×2) are fully zeroed, then only row 0 is populated. HPIPM processes all 3 rows, wasting work on 2 empty rows. See §6C for the formulation fix.

---

## 4. CODE STRUCTURE & CROSS-FILE LINKING

---

### 4A — `#define N 20` macro conflicts with `nlohmann/json.hpp`

```
SEVERITY : CRITICAL
FILE     : config.h:13, Params/params.cpp:22-24
CATEGORY : Structure
```

**ISSUE**: `config.h` defines `#define N 20`. The `nlohmann/json.hpp` library uses `template<unsigned N>` internally. If `json.hpp` is included after `config.h`, every `N` in the json templates becomes `20`, causing obscure compile errors.

The workaround in `params.cpp` works (include json.hpp first), but it is fragile. Any `.cpp` file that includes both `config.h` and `json.hpp` in the wrong order will break.

**FIX**: Replace the `#define N 20` macro with a `constexpr`:
```cpp
static constexpr int N = 20;
```
This does not pollute the preprocessor namespace and avoids template conflicts.

Similarly for `NX`, `NU`, `NB`, `NPC`, `NS` — convert all to `constexpr`.

---

### 4B — `mpcc` vs `mpc_controller` namespace split creates confusion

```
SEVERITY : MEDIUM
FILE     : Multiple
CATEGORY : Structure
```

**ISSUE**: Two namespaces are used interchangeably:
- `mpc_controller`: `state`, `control`, `Params`, `BicycleModel`, `Cost`, `MPC`, `ArcSpline`, `StateToVector`, `VectorToState`
- `mpcc`: `SolverInterface`, `Stage`, `CostMatrix`, `OptVariables`, `HpipmInterface`, `stateToVector`, `vectorToState`

Inside `mpcc`, `using State = mpc_controller::state;` creates tight coupling. Both namespaces have `CostMatrix`, `OptVariables`, and `stateToVector`/`vectorToState` (different signatures).

**FIX**: Merge into a single namespace `mpc_controller`. The `mpcc` namespace is a leftover from the original MPCC (Model Predictive Contouring Control) reference code by Liniger.

---

### 4C — `hpipm_interface.h` uses relative includes without path prefix

```
SEVERITY : MEDIUM
FILE     : Interfaces/hpipm_interface.h:14-15
CATEGORY : Structure
```

```cpp
#include "config.h"
#include "types.h"
```

These resolve only because CMakeLists.txt has `include_directories(src)`. This is fragile. If the include is compiled from a different working directory, it will fail.

**FIX**: Use explicit relative paths:
```cpp
#include "../config.h"
#include "../types.h"
```

---

### 4D — Spaces in directory names

```
SEVERITY : LOW
FILE     : "Bicycle Model/", "IPG Node/"
CATEGORY : Structure
```

Spaces in directory names cause issues with some CMake generators and shell scripts. CMakeLists.txt correctly quotes them, so it currently works, but it's a maintenance hazard.

**FIX**: Rename to `BicycleModel/` and `IPGNode/` (or `bicycle_model/`, `ipg_node/`).

---

### 4E — Duplicate `typedef`s in `config.h` and `types.h`

```
SEVERITY : LOW
FILE     : config.h:53-59, types.h:93-99
CATEGORY : Structure
```

`Q_MPC`, `q_MPC`, `R_MPC`, `r_MPC`, `S_MPC` are defined identically in both files. Since `config.h` includes `types.h`, only one set is needed.

**FIX**: Keep them in `types.h` only (where the Eigen typedefs live), remove from `config.h`.

---

## 5. MPC FORMULATION CORRECTNESS

---

### 5A — Contouring error sign convention

```
SEVERITY : INFO (CORRECT)
FILE     : Cost/cost.cpp:38-41
CATEGORY : Formulation
```

The contouring error is computed as:
```cpp
Eigen::Vector2d error(ref_point.x_ref - x.x, ref_point.y_ref - x.y);
```

The Jacobian rows rotate this into (contouring, lag) coordinates:
- Row 0: `[-sin(θ_ref), cos(θ_ref)]` → signed orthogonal distance (contouring)
- Row 1: `[cos(θ_ref), sin(θ_ref)]` → along-track distance (lag)

**VERDICT**: Correct. Standard MPCC formulation.

---

### 5B — Heading error wrapping

```
SEVERITY : INFO (CORRECT)
FILE     : Cost/cost.cpp:123-124
CATEGORY : Formulation
```

```cpp
theta_ref += 2.0 * M_PI * std::round((x.theta - theta_ref) / (2.0 * M_PI));
```

This correctly unwraps `theta_ref` to be closest to `x.theta`, avoiding ±π discontinuity. **Correct.**

---

### 5C — NPC=3 but only 1 active constraint row

```
SEVERITY : MEDIUM
FILE     : config.h:20, MPC/mpc.cpp:131-143
CATEGORY : Formulation / Performance
```

**ISSUE**: `NPC=3` (3 polytopic constraint rows) but only row 0 is used (track normal). Rows 1 and 2 are zero with bounds [−∞, +∞]. HPIPM allocates memory for all 3 rows at every stage, and the IPM processes them (even though they're trivially satisfied).

**FIX**: Set `NPC=1` unless rows 1-2 are planned for future use (e.g., friction circle). If reserved for future, add a comment.

---

### 5D — Soft constraint slack is unbounded

```
SEVERITY : INFO (CORRECT BUT NOTEWORTHY)
FILE     : MPC/mpc.cpp:145-146
CATEGORY : Formulation
```

```cpp
stg.l_bounds_s.setConstant(-mpcc::INF);
stg.u_bounds_s.setConstant( mpcc::INF);
```

Slack variables are unbounded — softness is controlled entirely by the `Z` (quadratic) and `z` (linear) penalty weights. From `cost.json`: `sc_quad_track = 1e4`, `sc_lin_track = 1e3`. These are non-zero, so HPIPM will penalize violations. **Correct**, but very large violations are possible with only quadratic penalty.

**Recommendation**: Add a hard upper bound on slack (e.g., `u_bounds_s = track_width * 0.5`) to prevent the car from going completely off-track during solver failure.

---

### 5E — SQP blending with fixed mixing factor

```
SEVERITY : LOW
FILE     : MPC/mpc.cpp:218-232
CATEGORY : Formulation
```

**ISSUE**: `sqp_mixing = 1.0` (from both constructors and the ROS node). When `sqp_mixing = 1.0`:
```cpp
out[i].xk = VectorToState(1.0 * cx + 0.0 * lx);  // = cx, no blending
```

So blending is effectively **disabled**. This is fine with `n_sqp = 1` (only 1 iteration), but with multiple SQP iterations, setting `sqp_mixing < 1.0` would improve convergence on hard problems. Current setup is consistent.

---

### 5F — Affine offset `g` correctness

```
SEVERITY : HIGH (related to §1C)
FILE     : MPC/mpc.cpp:93-96
CATEGORY : Formulation
```

```cpp
stg.lin_model.g = xk1_vec - A_d * xk_vec - B_d * uk_vec;
```

If the initial guess `xk1` was propagated via RK4 but `A_d, B_d` are Euler-linearized, then `g` absorbs the difference:
- With Euler: `x_{k+1} ≈ x_k + f(x_k,u_k)*dt = (I + A_c*dt)*x_k + B_c*dt*u_k`
- With RK4: `x_{k+1} = RK4(x_k, u_k, dt)`
- So `g = RK4(xk, uk) - Euler(xk, uk)`, which can be ~O(dt³) ≈ 1.25e-4 per step.

This is not catastrophic for a single SQP iteration but degrades optimality. **Fix by making linearization consistent with the propagation method.**

---

### 5G — Progress maximization term `q_vs` in cost

```
SEVERITY : INFO (REVIEW)
FILE     : Cost/cost.cpp:97
CATEGORY : Formulation
```

```cpp
q_contouring_cost(si_index.vs) = -params_.q_vs;
```

`si_index.vs = 4` maps to the velocity state index. This adds a linear term `−q_vs * v` to the cost, encouraging higher velocity. With `q_vs = 5.0`, this strongly incentivizes speed. **This is correct** for lap time minimization but could cause aggressive behavior. Ensure `v_max = 15 m/s` constraint is tight enough for safety.

---

### 5H — `r_delta` and `r_vs` penalize state in input cost

```
SEVERITY : LOW
FILE     : Cost/cost.cpp:147-148
CATEGORY : Formulation / Naming
```

```cpp
Q_input_cost(si_index.delta, si_index.delta) = params_.r_delta;
Q_input_cost(si_index.vs, si_index.vs) = params_.r_vs;
```

Variables named `r_delta` and `r_vs` (with `r_` prefix suggesting input cost) are actually applied to the **state** cost matrix `Q`, not the input cost matrix `R`. This is confusing but not wrong — it regularizes the steering angle and velocity states. The naming is a legacy from the MPCC reference code.

---

## 6. DEPENDENCY GRAPH

```
config.h ──#include──▶ types.h
    ▲                    ▲
    │                    │
    ├── params.h ────────┘
    ├── bicycle_model.h ── integrator/integration_methods.h
    ├── Cost/Cost.h ────── Spline/Arc_Spline.h ── Cubic_Spline.h
    ├── constraints.h ──── Arc_Spline.h
    ├── trackConstraints.h ── Arc_Spline.h, constraints.h
    ├── solver_interface.h (mpcc ns, #include "config.h" NO PATH PREFIX)
    ├── hpipm_interface.h ── solver_interface.h
    │
    └── MPC/mpc.h ── ALL of the above
         │
         └── IPG Node/mpc_controller_node.h ── MPC/mpc.h

ORPHANED (not included anywhere):
  - MPC/mpc_solver.h
  - IPG Node/simulator_model.h
```

---

## 7. SAFE-TO-DELETE LIST

| File/Directory | Reason | Risk |
|---|---|---|
| `MPC/mpc_solver.h` | Dead code, CasADi-based, won't compile | Zero |
| `MPC/mpc_solver.cpp` | Dead code (not in CMakeLists) | Zero |
| `IPG Node/simulator_model.h` | References nonexistent `MPCConfig` | Zero |
| `IPG Node/simulator_model.cpp` | Not in CMakeLists, won't compile | Zero |
| `Solver/` (empty dir) | Empty | Zero |
| `main.cpp` | Stub with TODO, not compiled, possible linker conflict | Zero — move to `test/` if wanted |
| `config.cpp` | Empty module, no code | Zero |
| `state.vx, state.vy, state.r, state.Throttle` | Dead fields, never read | Low (confirm no external consumer) |
| `control.dV_ghost` | Always zero, never read | Low |

---

## 8. PRIORITY-ORDERED ACTION LIST

| Priority | Action | Files | Impact |
|---|---|---|---|
| **P0** | Fix `computeArcLength()` off-by-one (§1A) | Arc_Spline.cpp | **All track data is wrong** |
| **P0** | Fix `getCost` missing `s` field (§1E) | MPC/mpc.cpp, Cost/cost.cpp | **Cost computed at wrong location** |
| **P1** | Replace `#define N/NX/NU` with `constexpr` (§4A) | config.h | Prevents json.hpp conflicts |
| **P1** | Fix warm-start shift off-by-one (§1B) | MPC/mpc.cpp | Better SQP convergence |
| **P1** | Switch to analytical Jacobians (§1C, §3B) | bicycle_model.cpp | Correctness + 160 fewer dynamics calls |
| **P1** | Remove `#undef N` in cost.cpp (§1F) | cost.cpp | Fragile macro hygiene |
| **P2** | Remove theta box constraint or widen (§1G) | bounds.json | Allows proper unwrapping |
| **P2** | Re-project `s` for all stages (§1D) | MPC/mpc.cpp | Correct track constraints |
| **P2** | Set `NPC=1` (§5C) | config.h | Saves HPIPM memory+time |
| **P2** | Replace `std::function` with templates (§3A) | integration_methods.h | Eliminates heap alloc in hot path |
| **P2** | Use fixed-size Eigen types (§3C) | Multiple | Stack alloc + SIMD |
| **P3** | Delete dead code (§2A-2I) | Multiple | Cleaner codebase |
| **P3** | Merge duplicate CostMatrix/converters (§2F, 2G) | Multiple | Less confusion |
| **P3** | Merge namespaces (§4B) | Multiple | Cleaner architecture |
| **P3** | Fix relative includes (§4C) | hpipm_interface.h | Build robustness |
| **P3** | Remove duplicate typedefs (§4E) | config.h/types.h | Cleanliness |
| **P4** | Rename directories (remove spaces) (§4D) | Filesystem | Maintainability |
| **P4** | Add slack upper bound (§5D) | MPC/mpc.cpp | Safety margin |

---

*End of audit.*
