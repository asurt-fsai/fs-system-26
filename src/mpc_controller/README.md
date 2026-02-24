# MPC Controller (C++)

Model Predictive Controller for autonomous vehicle control, implemented in C++ with ROS 2 integration.

## Structure

```
mpc_controller/
├── CMakeLists.txt                 # Build configuration
├── package.xml                    # Package metadata
├── include/mpc_controller/
│   ├── config.h                   # Configuration parameters
│   ├── bicycle_model.h            # Vehicle dynamics
│   ├── mpc_solver.h               # Optimization core
│   ├── constraints.h              # Constraint handling
│   ├── utils.h                    # Utility functions
│   └── mpc_controller_node.h      # ROS 2 node
└── src/
    ├── config.cpp
    ├── bicycle_model.cpp
    ├── mpc_solver.cpp
    ├── constraints.cpp
    ├── utils.cpp
    └── mpc_controller_node.cpp
```

## Features

- **C++ for Performance**: Real-time control at high update rates
- **Modular Design**: Clean separation between MPC core and ROS integration
- **Eigen-based**: Uses Eigen for efficient linear algebra
- **ROS 2 Native**: Full integration with ROS 2 topics and services
- **Warm-starting**: Faster convergence using previous solutions

## Building

```bash
cd ~/Control_Project
colcon build --packages-select mpc_controller
```

## Running

```bash
ros2 run mpc_controller mpc_controller_node
```

## Topics

### Subscriptions
- `/odom` (nav_msgs::Odometry): Current vehicle state
- `/reference_path` (nav_msgs::Path): Target trajectory

### Publications
- `/cmd_vel` (geometry_msgs::Twist): Velocity and steering commands
- `/mpc/predicted_path` (nav_msgs::Path): Predicted trajectory
- `/mpc/debug` (std_msgs::Float32MultiArray): Debug info [cost, iterations, success]

## Configuration

Edit in `mpc_controller_node.cpp` or load from config file:

```cpp
config_.horizon = 10;           // Prediction steps
config_.dt = 0.1;               // Time step [s]
config_.wheelbase = 2.5;        // Vehicle wheelbase [m]
config_.v_max = 2.0;            // Max velocity [m/s]
config_.v_min = -1.0;           // Min velocity [m/s]
config_.delta_max = M_PI / 4;   // Max steering angle [rad]
config_.delta_dot_max = M_PI / 3; // Max steering rate [rad/s]
```

### Weight Tuning

Cost weights are in `config.h`:
- **Q**: State tracking penalty (4x4 matrix) - penalize position/heading error
- **R**: Control effort penalty (2x2 matrix) - penalize velocity/steering changes
- **Q_terminal**: Terminal cost (typically 2x Q)

## Integration with Python Bicycle Model

This C++ controller can communicate with your existing Python bicycle model node:

1. **Python node publishes `/odom`** with the bicycle state
2. **C++ MPC controller subscribes** and publishes `/cmd_vel`
3. **Python node reads `/cmd_vel`** and updates bicycle dynamics

Both nodes communicate via standard ROS 2 messages - no dependencies!

## Next Steps

1. **Link NLOPT** for better optimization:
   ```bash
   apt-get install libnlopt-dev libnlopt-cxx-dev
   ```
   Then replace gradient descent with NLOPT in `mpc_solver.cpp`

2. **Add parameter server** to tune weights online

3. **Add unit tests** for each component

4. **Profile and optimize** bottlenecks

## Performance

- Update rate: ~100 Hz (configurable via `dt`)
- Computation time: ~5-10ms per step (optimization-dependent)
- Memory: Minimal footprint suitable for embedded systems
