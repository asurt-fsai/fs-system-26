# CasADi Integration for MPC Cost Function Minimization

## Overview
The MPC solver has been enhanced to use **CasADi** library for efficient nonlinear optimization of the cost function using IPOPT (Interior Point Optimizer).

## Changes Made

### 1. **CMakeLists.txt Updates**
- Added `find_package(casadi REQUIRED)` to locate CasADi library
- Linked CasADi library to mpc_lib target: `target_link_libraries(mpc_lib Eigen3::Eigen casadi)`
- Added casadi to exported dependencies for proper package configuration

### 2. **mpc_solver.cpp Implementation**

#### Added CasADi Header
```cpp
#include <casadi/casadi.hpp>
```

#### Enhanced solve() Function
The optimization now:
- **Converts state representation**: Expands 4D input state to 5D (adds velocity dimension)
- **Builds symbolic cost function** using CasADi MX (symbolic matrix expressions)
- **Implements RK4 integration**: Uses Runge-Kutta 4th-order for accurate state propagation
- **Defines bicycle model dynamics** symbolically within CasADi
- **Computes stage costs**: State tracking error + control effort penalties
- **Computes terminal cost**: Final state tracking penalty for stability
- **Enforces input bounds**: Velocity and steering rate constraints
- **Solves with IPOPT**: Interior point optimization algorithm
- **Handles failures gracefully**: Falls back to warm-start on solver errors

## Key Features

### Cost Function Formulation
$$J = \sum_{i=0}^{N-1} \left( \|x_i - x_{\text{ref},i}\|_Q^2 + \|u_i\|_R^2 \right) + \|x_N - x_{\text{ref},N}\|_{Q_{\text{terminal}}}^2$$

Where:
- $x_i$ = predicted state at step i
- $u_i$ = control input [acceleration, steering rate]
- $Q$ = state cost weight matrix
- $R$ = control cost weight matrix
- $Q_{\text{terminal}}$ = terminal state cost weight

### Dynamics Integration
Uses symbolic RK4 integration:
```
k1 = f(x, u)
k2 = f(x + 0.5*dt*k1, u)
k3 = f(x + 0.5*dt*k2, u)
k4 = f(x + dt*k3, u)
x_next = x + (dt/6)*(k1 + 2*k2 + 2*k3 + k4)
```

### Optimization Options
- **Algorithm**: IPOPT (Interior Point Method)
- **Max Iterations**: 100
- **Print Level**: 0 (silent)
- **Warm Starting**: Uses previous control solution as initial guess

## State & Control Variables

### State (5D)
- `x`: Global X position (m)
- `y`: Global Y position (m)
- `θ`: Vehicle heading (rad)
- `δ`: Steering angle (rad)
- `v`: Longitudinal velocity (m/s)

### Control (2D)
- `a`: Acceleration (m/s²)
- `δ̇`: Steering rate (rad/s)

## Error Handling
The implementation includes try-catch blocks for robust failure handling:
- Catches CasADi solver exceptions
- Falls back to warm-start solution if optimization fails
- Preserves functionality even when IPOPT convergence fails
- Returns diagnostic messages in SolveInfo structure

## Performance Considerations
1. **Computational Cost**: O(N³) for IPOPT, where N = horizon length
2. **Accuracy**: RK4 integration provides O(dt⁵) accuracy
3. **Warm Starting**: Significantly improves convergence for sequential solves
4. **Memory**: Minimal overhead beyond Eigen matrices

## Testing Recommendations
1. Verify IPOPT convergence on reference trajectories
2. Test with various horizon lengths (10, 20, 50 steps)
3. Validate cost function values match manual computations
4. Check solver timing and iteration counts
5. Test constraint enforcement (velocity, steering rate bounds)

## Dependencies
- CasADi (must be installed: `apt install casadi` or build from source)
- IPOPT (typically included with CasADi)
- Eigen3 (existing dependency)
- ROS 2 (for node integration)

## Configuration
Cost weights can be tuned via:
```cpp
solver.setWeights(Q, R, Q_terminal);
```

Where Q is 4×4, R is 2×2, and Q_terminal is 4×4 matrices.
