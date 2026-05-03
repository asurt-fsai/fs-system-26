# MPC Cost Function: Detailed Cost Weights & Equations

## Cost Equation (Full Form)

The MPC optimization solves:

$$\min_{x_{0:N}, u_{0:N-1}} J = \sum_{k=0}^{N-1} \ell(x_k, u_k) + \ell_N(x_N)$$

Where:
- $x_k \in \mathbb{R}^5$ = State [x, y, θ, δ, v]
- $u_k \in \mathbb{R}^2$ = Control [a, δ̇]
- $\ell(x_k, u_k)$ = Stage cost
- $\ell_N(x_N)$ = Terminal cost (with higher weight multiplier)

---

## Stage Cost Breakdown (for k = 0 to N-1)

### 1. **Position Tracking Cost** (Lateral & Longitudinal Centering)

**Equation:**
$$\ell_{pos} = q_c \cdot \left[(x_k - x_{ref,k})^2 + (y_k - y_{ref,k})^2\right]$$

**QP Form (what solver sees):**
$$0.5 \cdot x^T Q_{pos} x + q_{pos}^T x$$

Where:
```cpp
Q_pos[0,0] = 2.0 * q_c    // Position weight on x
Q_pos[1,1] = 2.0 * q_c    // Position weight on y
q_pos[0]   = -2.0 * q_c * x_ref
q_pos[1]   = -2.0 * q_c * y_ref
```

**Source:** `params/cost.json`
```json
{
  "q_c": <position_weight>,  // Typically 50-100
}
```

**Tuning Note:** 
- ↑ Higher q_c → Tighter position tracking, aggressive corrective maneuvers
- ↓ Lower q_c → Smoother, more relaxed trajectory (may drift off track)

---

### 2. **Velocity Tracking Cost** (Speed Reference)

**Equation:**
$$\ell_{vel} = q_{vs} \cdot (v_k - v_{ref,k})^2$$

Where $v_{ref,k}$ is **curvature-aware**:

$$v_{ref} = \min\left(v_{max}, \sqrt{\frac{a_{lat,max}}{|\kappa|+\epsilon}}\right)$$

- $v_{max}$ = Maximum reference speed (e.g., 15 m/s on straights)
- $\kappa$ = Track curvature at position s
- $a_{lat,max}$ = Maximum lateral acceleration (e.g., 12 m/s²)

**Physical Meaning:** 
- On straights (κ≈0): v_ref = v_max
- In tight corner (κ large): v_ref = √(a_lat_max/κ) ← naturally reduces speed!

**QP Form:**
```cpp
Q_vel[4,4] = 2.0 * q_vs    // Velocity weight
q_vel[4]   = -2.0 * q_vs * v_ref
```

**Source:** `params/cost.json` & `params/model.json`
```json
{
  "q_vs": <velocity_weight>,      // Typically 10-50
  "ref_velocity": 15.0,           // m/s
  "a_lat_max": 12.0               // m/s²
}
```

---

### 3. **Heading Alignment Cost** (Orientation to Track)

**Equation:**
$$\ell_{head} = q_\mu \cdot (\theta_k - \theta_{ref,k})^2$$

Where:
- $\theta_{ref}$ = Track tangent angle: $\theta_{ref} = \text{atan2}(dy_{ref}, dx_{ref})$
- Unwrapped to closest angle (avoids ±π discontinuity)

**Physical Meaning:** 
- Aligns car heading with track direction
- Prevents "approaching at wrong angle" during lane changes

**QP Form:**
```cpp
Q_head[2,2] = 2.0 * q_mu   // Heading weight  (θ is index 2)
q_head[2]   = -2.0 * q_mu * theta_ref_unwrapped
```

**Source:** `params/cost.json`
```json
{
  "q_mu": <heading_weight>,  // Typically 5-30
}
```

---

### 4. **Acceleration Magnitude Cost** (Smoothness)

**Equation:**
$$\ell_{accel} = q_a \cdot a_k^2$$

**Physical Meaning:**
- Penalizes large acceleration commands
- Creates smooth, comfortable trajectories
- Reduces jerk and passenger discomfort

**QP Form:**
```cpp
R_accel[0,0] = 2.0 * q_a   // Input weight (a is index 0)
r_accel[0]   = 0.0         // No linear term (cost is on deviation from 0)
```

**Source:** `params/cost.json`
```json
{
  "q_a": <accel_weight>,  // Typically 1-10
}
```

---

### 5. **Steering Rate Cost** (Smooth Steering)

**Equation:**
$$\ell_{steer} = q_\delta \cdot \dot{\delta}_k^2$$

**Physical Meaning:**
- Penalizes rapid steering angle changes
- Creates smooth cornering (no jerky maneuvers)
- Important for control smoothness and safety

**QP Form:**
```cpp
R_steer[1,1] = 2.0 * q_delta  // Input weight (δ̇ is index 1)
r_steer[1]   = 0.0            // No linear term
```

**Source:** `params/cost.json`
```json
{
  "q_delta": <steering_rate_weight>,  // Typically 1-50
}
```

---

## Terminal Cost (Stage k = N)

For the **last stage** (8 steps ahead), costs are increased by a multiplier:

$$\ell_N = q_{c,N} \cdot \left[(x_N - x_{ref,N})^2 + (y_N - y_{ref,N})^2\right]$$

Where: $q_{c,N} = q_{c,N,mult} \times q_c$ (applied at stage k=40)

**Rationale:** 
- Ensures terminal trajectory converges to track reference
- Prevents "giving up" near end of prediction horizon

**Source:** `params/cost.json`
```json
{
  "q_c_N_mult": 1.5  // Terminal position weight multiplier
}
```

---

## Complete Cost Matrix Assembly (cost.cpp:68-145)

```
For each stage k:
  Q = Q_pos + Q_head + Q_vel            (5×5 state cost matrix)
  R = R_accel + R_steer                 (2×2 input cost matrix)
  S = 0                                 (5×2 cross term)
  q = q_pos + q_head + q_vel            (5×1 state cost vector)
  r = r_accel + r_steer                 (2×1 input cost vector)
```

**Result:** Each stage has **full quadratic penalty structure** ready for QP solver.

---

## Summary Table: Cost Weights

| Cost Term | Variable | Units | Range | Effect |
|-----------|----------|-------|-------|--------|
| Position | `q_c` | dimensionless | 50-100 | Lateral/longitudinal centering |
| Velocity | `q_vs` | dimensionless | 10-50 | Speed profile tracking |
| Heading | `q_mu` | dimensionless | 5-30 | Orientation alignment |
| Acceleration | `q_a` | dimensionless | 1-10 | Smoothness of a |
| Steering Rate | `q_delta` | dimensionless | 1-50 | Smoothness of δ̇ |
| Terminal Mult | `q_c_N_mult` | factor | 1.0-2.0 | Terminal position emphasis |
| Max Lateral Acc | `a_lat_max` | m/s² | 8-15 | Curvature-dependent speed |
| Max Speed | `ref_velocity` | m/s | 10-20 | Straight-line max speed |

---

## Example Cost Minimization (Real Numbers)

**Current State:**
- Position: (445.23, 812.45)
- Heading: θ = -0.52 rad
- Velocity: v = 12.34 m/s
- Steering: δ = 0.025 rad

**Reference (from track):**
- Position_ref: (445.10, 812.80) — 0.35 m ahead on track
- Heading_ref: θ_ref = -0.50 rad
- Velocity_ref: v_ref = 14.5 m/s (curvature-aware)

**Cost Contributions:**

| Term | Computation | Weight | Value |
|------|-------------|--------|-------|
| Position | (0.13)² + (0.35)² | q_c=75 | 75 × 0.1394 = **10.46** |
| Heading | (-0.02)² | q_μ=20 | 20 × 0.0004 = **0.01** |
| Velocity | (-2.16)² | q_vs=30 | 30 × 4.6656 = **140.0** |
| Accel (if a=-0.34) | (-0.34)² | q_a=2 | 2 × 0.1156 = **0.23** |
| Steer Rate (if δ̇=-0.15) | (-0.15)² | q_δ=5 | 5 × 0.0225 = **0.11** |
| **Total (stage cost)** | | | **≈150.8** |

**Solver Objectives:** Minimize position error (especially velocity lag) while keeping control smooth.

---

## Tuning Guide

### Emphasize Position Tracking:
```json
"q_c": 150,      // Higher
"q_vs": 10,      // Lower
"q_mu": 5,
"q_a": 1,
"q_delta": 1
```
→ More aggressive lateral corrections, may overshoot

### Emphasize Smooth Control:
```json
"q_c": 50,       // Lower
"q_vs": 50,      // Higher
"q_mu": 30,
"q_a": 10,       // Higher
"q_delta": 20    // Higher
```
→ Smooth trajectories, may take wider corners

### Balanced (Default FSAI):
```json
"q_c": 75,
"q_vs": 30,
"q_mu": 20,
"q_a": 2,
"q_delta": 5
```
→ Good tracking + reasonable smoothness

---

## Files with Cost Parameters

1. **[params/cost.json](../params/cost.json)** - All q_* weights
2. **[params/model.json](../params/model.json)** - a_lat_max, ref_velocity
3. **[cost.cpp](../src/Cost/cost.cpp)** - Cost matrix assembly logic
4. **[mpc.cpp](../src/MPC/mpc.cpp)** - Cost integration into stages

