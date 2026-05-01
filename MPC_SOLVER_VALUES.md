# MPC Cost Function & Solver Output Values

## 📊 Complete Data Flow: What the Solver is Solving For

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      MPC OPTIMIZATION PROBLEM                            │
│                   (What the Solver is Solving For)                       │
└─────────────────────────────────────────────────────────────────────────┘

OPTIMIZATION VARIABLES (Decision Variables) — N+1 stages over horizon N=40 (2 seconds):
═════════════════════════════════════════════════════════════════════════

For each stage k = 0, 1, ..., 40 (41 total stages at 50ms intervals):

STATE VARIABLES [x_k, y_k, θ_k, δ_k, v_k]:
  • x_k        : Global X position [m]
  • y_k        : Global Y position [m] 
  • θ_k        : Heading angle [rad]
  • δ_k        : Steering angle [rad]
  • v_k        : Forward velocity [m/s]

CONTROL VARIABLES [a_k, δ̇_k]:
  • a_k        : Acceleration command [m/s²]  ← First output: a_0 sent to vehicle
  • δ̇_k       : Steering rate [rad/s]        ← First output: δ̇_0 sent to vehicle


COST FUNCTION (Objective Being Minimized):
═════════════════════════════════════════════════════════════════════════

J = Σ(k=0 to 39) [Stage Cost] + Terminal Cost  (N=40 stages over 2 seconds)

The solver is minimizing SUM OF:

1️⃣  POSITION TRACKING COST (Direct XY tracking):
    ────────────────────────────────────────────
    For k < N (intermediate stages):
      q_c * [(x_k - x_ref_k)² + (y_k - y_ref_k)²]
    
    For k = N (terminal):
      q_c_N_mult * q_c * [(x_N - x_ref_N)² + (y_N - y_ref_N)²]
    
    Parameters from params/cost.json:
      • q_c = position weight
      • q_c_N_mult = terminal position weight multiplier


2️⃣  VELOCITY TRACKING COST:
    ──────────────────────────
    q_vs * (v_k - v_ref_k)²
    
    Where v_ref is CURVATURE-AWARE:
      v_ref = min(ref_velocity, √(a_lat_max / |κ|))
      
    The vehicle automatically slows in tight corners!
    
    Parameters:
      • q_vs = velocity weight
      • ref_velocity = desired speed (e.g., 15 m/s)
      • a_lat_max = max lateral acceleration (e.g., 12 m/s²)
      • κ = curvature at that point on track


3️⃣  HEADING ALIGNMENT COST:
    ────────────────────────
    q_μ * (θ_k - θ_ref_k)²
    
    Aligns car heading with track tangent direction.
    
    Parameters:
      • q_μ = heading weight


4️⃣  ACCELERATION (INPUT) COST:
    ──────────────────────────
    Σ q_a * a_k²  (for k=0 to N-1)
    
    Penalizes aggressive acceleration changes.
    
    Parameters:
      • q_a = acceleration weight


5️⃣  STEERING RATE (INPUT) COST:
    ──────────────────────────────
    Σ q_δ * δ̇_k²  (for k=0 to N-1)
    
    Penalizes aggressive steering changes (smooth cornering).
    
    Parameters:
      • q_δ = steering rate weight


═════════════════════════════════════════════════════════════════════════════

CONSTRAINTS (What's Constrained):
═════════════════════════════════

State Bounds:
  • x_k, y_k ∈ ℝ (unbounded globally)
  • θ_k ∈ [-π, π] (unwrapped)
  • δ_k ∈ [-0.6109, 0.6109] rad (±35° steering limit for FSAI)
  • v_k ∈ [0, 25] m/s (velocity limits)

Control Bounds:
  • a_k ∈ [-5.0, 5.0] m/s² (acceleration limits)
  • δ̇_k ∈ [params.delta_dot_min, params.delta_dot_max] rad/s

Dynamics Constraints (equality):
  x_{k+1} = f(x_k, u_k)  [Bicycle model from mpc.cpp:122-126]
  
  Linearized: x_{k+1} = A_d·x_k + B_d·u_k + g

Track Boundary Constraint (polytopic):
  For k > 0: n_normal · [x_k, y_k] ∈ [bound_lower, bound_upper]
  
  Ensures car stays within track boundaries
  Parameters:
    • r_inner, r_outer = track width constraints


═════════════════════════════════════════════════════════════════════════════
```

---

## 🎯 Solver Outputs: What Gets Returned

```
┌─────────────────────────────────────────────────────────────────────────┐
│              HPIPM SOLVER OUTPUT (mpc.cpp:306-325)                       │
│         OptVariables array with solutions for all N+1 stages             │
└─────────────────────────────────────────────────────────────────────────┘

RAW SOLVER SOLUTION:
════════════════════

std::array<OptVariables, N+1> raw_sol = solver_->solveMPC(stages_, x0, ...)

This is an array of N+1=41 OptVariables structs, one per horizon stage:

┌─ Stage 0 (NOW) ─────────────────────────────────────────┐
│  OptVariables[0].xk = [x₀*, y₀*, θ₀*, δ₀*, v₀*]        │
│  OptVariables[0].uk = [a₀*, δ̇₀*]                       │
│                                                          │
│  ✓ a₀* = OPTIMAL ACCELERATION to send to vehicle NOW   │
│  ✓ δ̇₀* = OPTIMAL STEERING RATE to send to vehicle NOW │
└──────────────────────────────────────────────────────────┘

┌─ Stage 1 ────────────────────────────────────┐
│  OptVariables[1].xk = [x₁*, y₁*, θ₁*, δ₁*, v₁*]        │
│  OptVariables[1].uk = [a₁*, δ̇₁*]                       │
│  (Predicted state & control at t+1 step)               │
└──────────────────────────────────────────────┘

... (Stages 2-7) ...

┌─ Stage 40 (Terminal) ─────────────────────────┐
│  OptVariables[40].xk = [x₄₀*, y₄₀*, θ₄₀*, δ₄₀*, v₄₀*]   │
│  OptVariables[40].uk = [a₄₀*, δ̇₄₀*]                    │
│  (Predicted state & control at 2s horizon end)        │
└────────────────────────────────────────────────┘


EXTRACTED OPTIMAL SOLUTION:
═══════════════════════════

From raw_sol, the MPC returns optimal_solution_ containing ALL stages.

But what gets APPLIED (sent to vehicle) is ONLY the first stage:

    u₀ = initial_guess_[0].uk = [a₀*, δ̇₀*]
    
    Where:
    • a₀*  = acceleration to command (m/s²)
    • δ̇₀* = steering rate to command (rad/s)


═════════════════════════════════════════════════════════════════════════════
```

---

## 📤 What Gets Sent to the Vehicle

```
┌─────────────────────────────────────────────────────────────────────────┐
│              MPC NODE → IPG CarMaker (mpc_controller_node.cpp:117-120)  │
│                   ackermann_msgs::msg::AckermannDriveStamped            │
└─────────────────────────────────────────────────────────────────────────┘

Control Loop (20 Hz = 0.05 s):
════════════════════════════════════════════════════════════════════════

INPUT:
  • current_state: [x₀, y₀, θ₀, δ₀, v₀] from odometry
  • reference_path: waypoints for track spline

MPC SOLVE:
  • Runs optimization over 40-step horizon (2.0 seconds ahead)
  • Solves for optimal state trajectory X* and control trajectory U*
  • Returns: u₀ = [a₀*, δ̇₀*]

OUTPUT (Published to /ackr):
  ┌────────────────────────────────────────────────┐
  │ drive_msg.drive.acceleration = a₀*             │
  │                                                │
  │ drive_msg.drive.steering_angle = δ_target      │
  │   where:                                       │
  │   δ_target = clamp(δ₀ + δ̇₀* × dt, ±0.6109)   │
  │                                                │
  │   NOTE: STEERING ANGLE INCREMENTED by rate!    │
  │   This converts steering RATE to absolute angle│
  └────────────────────────────────────────────────┘

EXAMPLE LOG OUTPUT (every 50ms at 20 Hz):
═════════════════════════════════════════

  MPC: x0=(445.23, 812.45) θ=-0.52 δ=0.025 v=12.34 
       → a=-0.34 δ_cmd=0.031 err=0.15m t=2.3ms
       
  Breakdown:
    • x0, y0 = current position in global frame
    • θ = current heading angle
    • δ = current steering angle (from car state)
    • v = current velocity
    • a = optimal acceleration from solver (m/s²)
    • δ_cmd = computed steering angle to send = δ + δ̇ × 0.05
    • err = perpendicular distance to track reference (m)
    • t = MPC computation time (milliseconds)


RECEDING HORIZON PRINCIPLE:
═══════════════════════════

[t=0]  Apply u₀*         → Horizon shifts forward
[t=1]  Apply u₁*         → Resolve MPC with new horizon
[t=2]  Apply u₂*         → Continuous tracking...
  ⋮     ⋮
[t=N]  Apply u_N*        → Always looking 0.4s ahead

═════════════════════════════════════════════════════════════════════════════
```

---

## 📋 Summary: The Three Key Outputs

| Output | Source | Type | Value | Unit | Sent To |
|--------|--------|------|-------|------|---------|
| **a₀*** | Solver stage 0 | Acceleration | -5.0 to +5.0 | m/s² | IPG CarMaker |
| **δ̇₀*** | Solver stage 0 | Steering Rate | See bounds.json | rad/s | Applied incremental |
| **δ_target** | Computed | Steering Angle | -0.6109 to +0.6109 | rad | IPG CarMaker |

---

## 🔍 Where Each Value Comes From

### Cost Function Building (cost.cpp)

```cpp
CostMatrix cm = cost_->getCost(track_, xk_nz, time_step);
// Returns: Q, R, S, q, r (cost matrices for stage k)

// What each cost term penalizes:
Q_contouring_cost → Penalizes lateral position error (x_k - x_ref)²
Q_heading_cost    → Penalizes heading misalignment (θ_k - θ_ref)²
Q_velocity_cost   → Penalizes velocity error (v_k - v_ref)²
R_accel_cost      → Penalizes acceleration magnitude |a_k|²
R_steer_rate_cost → Penalizes steering rate magnitude |δ̇_k|²
```

### Solver Interface (hpipm_interface.cpp)

```cpp
solver_->solveMPC(stages_, x0, &solver_status)
// Returns array<OptVariables, 9> with optimal x* and u* for each stage
```

### MPC Node Output (mpc_controller_node.cpp:111-120)

```cpp
mpc_controller::MPCReturn result = mpc_->runMPC(x0);

// result contains:
// ├─ u0: [a₀*, δ̇₀*]          ← WHAT TO SEND
// ├─ mpc_horizon: ALL N+1 stages
// ├─ time_total: solver time
// └─ lateral_error: diagnostics

// Convert to Ackermann message:
drive_msg.drive.acceleration = result.u0.D_dot;              // a₀*
drive_msg.drive.steering_angle = clamp(δ₀ + δ̇₀*·dt, ±35°); // δ_target
```

---

## ⚡ Key Insights

1. **What's Solved For**: The solver optimizes **41 trajectory segments** (0-40 steps = 2 seconds) with:
   - 5 state variables per step (x, y, θ, δ, v)
   - 2 control variables per step (a, δ̇)
   - **Total: 41×5 + 40×2 = 285 decision variables**

2. **What's Sent**: Only the **first control** [a₀*, δ̇₀*] is applied; the rest are predictions

3. **Cost Being Minimized**:
   - Position error (keep on track centerline)
   - Velocity tracking (speed depends on curvature)
   - Heading alignment (face track direction)
   - Smooth inputs (avoid jerky acceleration/steering)

4. **Every 50ms (20 Hz)**: Fresh MPC solve → New optimal trajectory (2s ahead) → Apply u₀ → Receding horizon

---

## 📁 Code References

| File | Function | What It Does |
|------|----------|-------------|
| [cost.cpp](../src/Cost/cost.cpp) | `getCost()` | Builds Q, R, S, q, r cost matrices |
| [mpc.cpp](../src/MPC/mpc.cpp#L306) | `runMPC()` | Solves QP, returns u₀* |
| [mpc_controller_node.cpp](../src/IPG%20Node/mpc_controller_node.cpp#L117) | `controlLoop()` | Publishes drive_msg with [a, δ] |
| [solver_interface.cpp](../src/Interfaces/solver_interface.cpp) | `solveMPC()` | HPIPM solver interface |

