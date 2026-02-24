# MPC Controller - Complete Documentation Guide
## Formula Student AI 2026

---

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [File Structure & Purpose](#file-structure--purpose)
3. [Core Concepts](#core-concepts)
4. [Configuration Guide](#configuration-guide)
5. [Vehicle Dynamics](#vehicle-dynamics)
6. [Constraint System](#constraint-system)
7. [MPC Solver](#mpc-solver)
8. [Utility Functions](#utility-functions)
9. [ROS 2 Integration](#ros-2-integration)
10. [FSAI 2026 Tuning Guide](#fsai-2026-tuning-guide)

---

## Project Overview

This is a **Model Predictive Controller (MPC)** for autonomous Formula Student racing vehicles. The controller uses optimal control theory to command steering and acceleration inputs that minimize tracking error while respecting vehicle constraints.

### Key Features
- **Receding Horizon Control**: Plans 1 second ahead (50 steps), executes first control
- **Kinematic Bicycle Model**: Captures essential steering dynamics without tire slip complexity
- **Runge-Kutta 4th Order Integration**: Accurate trajectory prediction
- **ROS 2 Integration**: Subscribes to vehicle state, publishes control commands
- **Online Tuning**: Adjust cost weights during testing without rebuilding
- **Warm-Start**: Reuses previous solution for faster convergence

---

## File Structure & Purpose

### Header Files (include/mpc_controller/)

#### 1. **config.h** - Configuration Management
**Purpose**: Centralized storage for all tunable MPC parameters

**Key Components**:
```cpp
class MPCConfig {
    // Prediction parameters
    int horizon = 50;           // Prediction steps (1 second at 50 Hz)
    double dt = 0.02;          // Time step between predictions
    
    // Vehicle model
    double wheelbase = 2.5;     // Distance from front to rear axle
    
    // Cost function weights (TUNE THESE!)
    Eigen::Matrix4d Q;          // State tracking penalty
    Eigen::Matrix2d R;          // Control effort penalty
    Eigen::Matrix4d Q_terminal; // Terminal state penalty
    
    // Constraint limits
    double v_max, v_min;        // Velocity limits
    double delta_max;           // Steering angle limit (±30°)
    double delta_dot_max;       // Steering rate limit (±60°/s)
};
```

**FSAI 2026 Tuning**:
- `Q(2,2)` = 10: High weight on heading error (most critical for track following)
- `R(1,1)` = 0.5: Steering smoothness (5x vehicle acceleration smoothness)
- Adjust these based on track test results

---

#### 2. **bicycle_model.h** - Vehicle Dynamics Model
**Purpose**: Represents vehicle motion using kinematic bicycle model

**Continuous Dynamics**:
```
dx/dt = v * cos(theta)
dy/dt = v * sin(theta)
dtheta/dt = (v / wheelbase) * tan(delta)
ddelta/dt = delta_dot
```

**Key Functions**:
- `dynamics()`: Compute state derivatives at current point
- `step()`: Integrate forward one time step using RK4
- `predictTrajectory()`: Generate full predicted path for cost calculation
- `linearize()`: Compute Jacobian matrices (advanced feature)

**Why Kinematic Model?**
- Suitable for FS speeds (< 12 m/s)
- Ignores tire slip, inertia effects
- Computationally efficient
- Accurate enough for mid-speed racing

**Runge-Kutta 4 Integration**:
```cpp
k1 = f(x, u)
k2 = f(x + 0.5*dt*k1, u)
k3 = f(x + 0.5*dt*k2, u)
k4 = f(x + dt*k3, u)
x_next = x + (dt/6) * (k1 + 2*k2 + 2*k3 + k4)
```
- **Error**: O(dt⁵) vs O(dt²) for Euler
- **Benefit**: ~10,000x better accuracy!

---

#### 3. **constraints.h** - Safety Limits
**Purpose**: Define and enforce vehicle operating constraints

**Functions**:
- `getInputBounds()`: Returns velocity and steering rate limits
- `getStateBounds()`: Returns position and angle limits
- `checkFeasibility()`: Verifies if state/control pair is safe

**Constraint Types**:
```cpp
// Control constraints (what we command)
0 ≤ v ≤ v_max              // Velocity [m/s]
-delta_dot_max ≤ δ_dot ≤ delta_dot_max  // Steering rate [rad/s]

// State constraints (what we allow)
-delta_max ≤ δ ≤ delta_max  // Steering angle [rad]
```

**FSAI 2026 Example**:
- v_max = 8 m/s (adjust for your car)
- delta_max = π/6 rad (30°, adjust for your steering linkage)
- delta_dot_max = π/3 rad/s (60°/s, adjust for servo speed)

---

#### 4. **mpc_solver.h** - Core Optimization
**Purpose**: Solves the MPC optimization problem each control cycle

**Optimization Problem**:
```
minimize: Cost = Σ ||x_i - x_ref_i||²_Q + ||u_i||²_R + ||x_final||²_Q_terminal
subject to:
  x_{i+1} = f(x_i, u_i)  [bicycle model]
  constraints on x, u
```

**Key Functions**:
- `solve()`: Solves full optimization, returns optimal controls & trajectory
- `getControl()`: Executes only first control (receding horizon)
- `setWeights()`: Updates Q, R online without rebuilding
- `resetWarmStart()`: Clears previous solution cache

**Receding Horizon Strategy**:
1. Plans 50 steps ahead
2. Executes only first control
3. Next cycle: New plan with updated state
4. Continuous replanning enables feedback control

**Warm-Starting**:
```cpp
last_control_sequence_;  // Previous optimal sequence
// Reused as initial guess in next solve
// → ~50% faster convergence
```

---

#### 5. **utils.h** - Helper Functions
**Purpose**: Common mathematical utilities for control logic

**Functions**:

1. **`wrapAngle(angle)`**: Wraps angle to [-π, π]
   - Prevents angle from becoming ±1000° instead of 0°
   - Critical for angle-based cost calculations
   ```cpp
   wrapAngle(370°) → 10°  // 360° + 10° = 370° → 10°
   wrapAngle(-190°) → 170° // -180° - 10° → 170°
   ```

2. **`saturate(value, min, max)`**: Clamps value to bounds
   - Enforces physical limits (motor won't exceed max RPM)
   ```cpp
   saturate(15, 0, 10) → 10  // Cap at maximum
   saturate(-5, 0, 10) → 0   // Cap at minimum
   ```

3. **`rateLimit(current, desired, rate, dt)`**: Smooths control changes
   - Prevents jerky commands that damage hardware
   ```cpp
   // Max change = rate * dt = 60°/s * 0.02s = 1.2°/cycle
   rateLimit(0, 30, 60, 0.02) → 1.2  // Limit upward change
   ```

4. **`getReferenceError(state, ref)`**: Computes tracking error
   - Subtracts reference with angle wrapping
   - Used in cost function computation

---

#### 6. **mpc_controller_node.h** - ROS 2 Interface
**Purpose**: Connects MPC solver to actual vehicle via ROS 2 middleware

**Subscribers** (INPUT from vehicle):
- `/odometry/filtered`: Current state [x, y, θ, δ]

**Subscribers** (INPUT from planner):
- `/reference_path`: Desired trajectory (nav_msgs::Path)

**Publishers** (OUTPUT to vehicle):
- `/cmd_vel`: Control commands (geometry_msgs::Twist)
- `/mpc/predicted_path`: Predicted trajectory (for RVIZ visualization)
- `/mpc/debug`: Solver statistics (for monitoring)

**Control Loop** (50 Hz):
```
1. Receive latest odometry
2. Receive reference path
3. Extract 50-step prediction window
4. Solve MPC optimization
5. Send first control to vehicle
6. Publish predictions for debugging
7. Repeat every 20ms
```

---

## Core Concepts

### 1. State Vector: x = [x, y, θ, δ]
- **x, y**: Position in global frame (meters)
- **θ**: Vehicle heading (radians, [-π, π])
- **δ**: Steering angle (radians, typically [-π/6, π/6])

### 2. Control Input: u = [v, δ_dot]
- **v**: Longitudinal velocity (m/s)
- **δ_dot**: Steering rate (rad/s)

### 3. Prediction Horizon: 50 steps
- At 50 Hz control rate: 50 × 0.02s = 1 second lookahead
- Longer horizon: More predictive but slower
- Shorter horizon: Faster but less predictive

### 4. Cost Function Components
```
Total Cost = Position Error + Heading Error + Control Effort + Terminal Penalty
           = ||x-x_ref||²_Q + ||u||²_R + ||x_final||²_Q_terminal
```

---

## Configuration Guide

### Default Values (FSAI 2026)
```cpp
// Timing
horizon = 50              // 1 second at 50 Hz
dt = 0.02                 // 20 milliseconds per step

// Vehicle
wheelbase = 2.5           // Typical FS car (measure yours!)

// Velocity limits
v_max = 2.0               // Start conservative, increase after testing
v_min = 0.0               // Can stop

// Steering limits
delta_max = π/6 (0.524)   // 30 degrees
delta_dot_max = π/3 (1.047) // 60 degrees/second

// Cost weights
Q = diag(1, 1, 10, 0.1)   // Heavy penalty on heading
R = diag(0.1, 0.5)        // Steering 5x smoother than acceleration
Q_terminal = Q * 2.0      // Extra penalty at horizon end
```

### How to Tune for Your Track

1. **Initial Testing** (use defaults):
   - Run vehicle on track
   - Record: oscillation, overshoot, tracking error

2. **If car oscillates left-right**:
   - Increase R(1,1): Smoother steering
   - Decrease Q(2,2): Less aggressive heading control

3. **If car drifts off track**:
   - Increase Q(0,0), Q(1,1): Better position tracking
   - Increase Q(2,2): Better heading accuracy

4. **If car is slow to accelerate**:
   - Decrease R(0,0): More aggressive throttle changes
   - But monitor for wheel spin

5. **Store best tuning**:
   - Create profiles for: acceleration zone, braking zone, high-speed turn, etc.
   - Use ROS 2 parameter server for dynamic switching

---

## Vehicle Dynamics

### Kinematic Bicycle Model

The model assumes the vehicle can be represented as two "bikes" (front and rear axles) connected by rigid wheelbase.

**Continuous Equations**:
```
dx/dt = v * cos(θ)
dy/dt = v * sin(θ)
dθ/dt = (v/L) * tan(δ)      where L = wheelbase
dδ/dt = δ_dot
```

**Turning Radius**:
```
R = L / tan(δ)
```

**FSAI 2026 Example** (wheelbase = 2.5m):
- δ = 0°  → R = ∞ (straight)
- δ = 10° → R ≈ 14m (gentle)
- δ = 30° → R ≈ 4.3m (sharp)

### Why NOT Dynamic Model?

Dynamic model would include:
- Tire slip angles
- Vehicle inertia and mass
- Suspension compliance
- Wind resistance

**Trade-off**:
- Dynamic model: More accurate, much slower computation
- Kinematic model: Less accurate but fast enough for FS speeds

At FS typical speeds (4-8 m/s), kinematic model is sufficient.

---

## Constraint System

Constraints ensure physical feasibility:

**Control Constraints** (what MPC can command):
```cpp
// Velocity
0 m/s ≤ v ≤ v_max

// Steering rate
-delta_dot_max ≤ δ_dot ≤ delta_dot_max
```

**State Constraints** (what we allow vehicle to reach):
```cpp
// Steering angle
-delta_max ≤ δ ≤ delta_max

// Position (typically very loose)
-large ≤ x,y ≤ large
```

**Enforcement**:
1. MPC solver respects constraints during optimization
2. Control output is saturated: `u_safe = saturate(u_mpc, u_min, u_max)`
3. Commands sent to vehicle are always feasible

---

## MPC Solver

### Optimization Algorithm

Standard gradient-based optimization:

```
1. Initialize: u_0 = previous optimal sequence (warm-start)
2. Compute cost: J = Σ||x_i(u) - x_ref_i||²_Q + ||u_i||²_R
3. Compute gradient: ∇J = [∂J/∂u_0, ∂J/∂u_1, ..., ∂J/∂u_49]
4. Update: u_{k+1} = u_k - α*∇J  (gradient descent)
5. Repeat until ||∇J|| < tolerance or max iterations
```

### Typical Performance
- **Iterations**: 5-15 per solve
- **Solve time**: 5-10 ms (well within 20 ms budget)
- **Convergence**: Warm-start enables fast convergence

### Receding Horizon

**Key Insight**: We only use first control, not entire sequence!

```
Horizon: [u0  u1  u2  ...  u49]
         [↑ USE]  [← Re-optimized next cycle]

Cycle 1: Compute full horizon, use only u0, discard u1-u49
Cycle 2: New state, re-plan full horizon, use only new u0
Cycle 3: ...
```

**Advantage**: Feedback control that adapts to disturbances

---

## Utility Functions

### `wrapAngle()`
Prevents angle wraparound issues:
```
Input:  -190°
Output: 170°

Input:  750°
Output: 30°
```

Critical for cost functions because:
- Angle error should be ≤ 180°
- Prevents treating 190° as "better" than 10°

### `saturate()`
Enforces hard physical limits:
```
Motor: Can't go faster than max RPM
Servo: Can't turn faster than servo speed
Battery: Can't exceed BMS current limit
```

### `rateLimit()`
Smooths control changes:
```
Raw command:   0° → 30° (instant)
Rate-limited:  0° → 1.2° → 2.4° → ... (smooth ramp)
               (limited by servo mechanical speed)
```

Benefits:
- Prevents servo damage
- Maintains tire grip (smooth steering)
- Keeps sensors stable
- Improves energy efficiency

---

## ROS 2 Integration

### Node Architecture

```
┌─────────────────────────────────┐
│  Path Planner Node              │
│  Publishes reference trajectory │
└──────────────┬──────────────────┘
               │ /reference_path
               ▼
┌─────────────────────────────────┐
│  MPC Controller Node (50 Hz)    │
│  - Receives reference path      │
│  - Solves MPC optimization      │
│  - Publishes control commands   │
└──────────────┬──────────────────┘
               │ /cmd_vel
               ▼
┌─────────────────────────────────┐
│  Vehicle Controller             │
│  Executes steering & throttle   │
└──────────────┬──────────────────┘
               │ /odometry/filtered
               ▼
┌─────────────────────────────────┐
│  Odometry/State Estimation      │
│  Publishes current vehicle state│
└──────────────┬──────────────────┘
               │
               └─→ Back to MPC Node (feedback loop)
```

### Publishers

1. **`/cmd_vel` (geometry_msgs::Twist)**
   ```cpp
   twist.linear.x = velocity;    // m/s
   twist.angular.z = steering;   // rad/s
   ```

2. **`/mpc/predicted_path` (nav_msgs::Path)**
   - MPC's predicted trajectory
   - Visualize in RVIZ for debugging

3. **`/mpc/debug` (std_msgs::Float32MultiArray)**
   - Solver cost, iterations, convergence status
   - Monitor solver health

### Subscribers

1. **`/odometry/filtered` (nav_msgs::Odometry)**
   - Current vehicle state
   - Extract: x, y, θ, δ

2. **`/reference_path` (nav_msgs::Path)**
   - Desired trajectory from planner
   - Extract 50-step window aligned with current state

---

## FSAI 2026 Tuning Guide

### Competition Day Preparation

#### 1. Pre-Race Calibration
```cpp
// Measure your vehicle
wheelbase = (YOUR VEHICLE WHEELBASE);
v_max = (YOUR VEHICLE MAX SPEED);
delta_max = (YOUR STEERING LIMIT);
delta_dot_max = (YOUR SERVO SPEED);
```

#### 2. Initial Tuning (Use Defaults)
- Start with provided default weights
- Run practice lap
- Record performance

#### 3. Iterative Improvement
```
Performance Issue          → Tuning Action
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Car weaves left-right    → Increase R(1,1) (smoother steering)
Car undershoots turns    → Decrease Q(2,2) (less aggressive heading)
Car overshoots turns     → Increase Q(2,2) (more aggressive heading)
Car drifts outside lane  → Increase Q(0,0), Q(1,1) (better position)
Oscillation at high speed → Increase R (smoother overall)
Oscillation at low speed → Decrease R (allow faster response)
```

#### 4. Track-Specific Profiles
```cpp
// Create profiles for different scenarios
struct TuningProfile {
    std::string name;           // e.g., "tight_turns"
    Eigen::Matrix4d Q;
    Eigen::Matrix2d R;
    Eigen::Matrix4d Q_terminal;
};

// Profiles to test
TuningProfile slow_speed;      // Low speed, high maneuverability
TuningProfile high_speed;      // High speed, stability priority
TuningProfile acceleration;    // Straight zones, aggressive acceleration
TuningProfile braking;         // Slower steering rate, smooth deceleration
```

#### 5. Online Parameter Adjustment
```bash
# During competition, adjust parameters without stopping
ros2 param set /mpc_controller q_heading 15.0
ros2 param set /mpc_controller r_steering 0.7

# Vehicle immediately responds to new weights!
```

### Testing Protocol

1. **Baseline**: Record lap times with default tuning
2. **Vary Q(2,2)**: Test 5.0, 7.5, 10.0, 15.0, 20.0
3. **Record Results**: Time, smoothness, tracking error
4. **Vary R(1,1)**: Test 0.3, 0.5, 0.7, 1.0
5. **Combine Best**: Use best Q(2,2) + best R(1,1)
6. **Fine-Tune**: Adjust remaining weights

### Safety Considerations

- **Conservative Start**: Begin with 50% of max velocity
- **Gradual Increase**: Increase speed 1 m/s per test lap
- **Constraint Checking**: Verify no commands exceed limits
- **Sensor Monitoring**: Watch IMU/lidar stability (oscillation = bad tuning)
- **Conservative Limits**: Always allow safety margin below physical limits

---

## Compilation & Deployment

### Build
```bash
cd /path/to/workspace
source /opt/ros/jazzy/setup.bash
colcon build --packages-select mpc_controller
```

### Source Setup
```bash
source install/setup.bash
```

### Launch MPC Node
```bash
ros2 run mpc_controller mpc_controller_node
```

### Monitor Performance
```bash
# Terminal 1: View predictions in RVIZ
ros2 run rviz2 rviz2 -d config.rviz

# Terminal 2: Monitor MPC statistics
ros2 topic echo /mpc/debug

# Terminal 3: View actual vs reference trajectory
# (create custom visualization)
```

---

## Troubleshooting

### Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| MPC solve time > 20ms | Horizon too large, solver not converging | Decrease horizon to 40, check warm-start |
| Vehicle oscillates | R matrix too small | Increase R(0,0) and R(1,1) |
| Vehicle drifts off track | Q matrix too small | Increase Q(0,0), Q(1,1), Q(2,2) |
| Steering is jerky | delta_dot_max too high | Decrease delta_dot_max, increase R(1,1) |
| Can't turn tight enough | delta_max too low | Increase delta_max, verify servo range |
| Predict trajectory diverges | Euler integration (use RK4!) | Already fixed - using RK4 now |
| MPC not responding to path changes | Warm-start too aggressive | Call resetWarmStart() after large state jumps |

---

## Advanced Topics (Optional)

### 1. Adaptive Tuning
Automatically adjust Q, R based on track conditions:
```cpp
if (speed > 6.0) {
    Q(2,2) = 8.0;   // Less aggressive at high speed
} else {
    Q(2,2) = 15.0;  // More aggressive at low speed
}
```

### 2. Multi-Segment Tuning
Different tuning for different track sections:
```cpp
if (curvature > 0.1) {
    // Tight turn: aggressive steering
    R(1,1) = 0.3;
} else {
    // Straight: smooth control
    R(1,1) = 1.0;
}
```

### 3. Constraint Tightening
Dynamically reduce limits for safety:
```cpp
if (tire_temperature > 80_C) {
    delta_dot_max *= 0.8;  // Reduce steering rate
    v_max *= 0.9;          // Reduce speed
}
```

### 4. Uncertainty Propagation
Use Jacobians to quantify prediction uncertainty:
- Compute state covariance evolution
- Tighten constraints under high uncertainty
- Adjust cost weights based on confidence

---

## References & Further Reading

### Control Theory
- Model Predictive Control (MPC) fundamentals
- Receding horizon control
- Optimization algorithms

### Vehicle Dynamics
- Kinematic bicycle model theory
- Tire slip characteristics
- High-speed vs low-speed dynamics tradeoffs

### FSAI Resources
- FSG/FSN/FSA technical regulations
- Vehicle design guidelines
- Control system benchmarks

---

## Questions & Support

For implementation details, see:
- `config.h` (detailed comments on each parameter)
- `bicycle_model.h` (detailed comments on RK4, dynamics)
- `mpc_solver.h` (detailed comments on optimization)
- `utils.h` (detailed comments on helper functions)
- `mpc_controller_node.h` (detailed comments on ROS 2 integration)

Good luck in FSAI 2026! 🏎️

