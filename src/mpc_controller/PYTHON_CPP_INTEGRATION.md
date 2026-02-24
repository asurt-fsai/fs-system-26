# Python ↔ C++ Integration Guide

## Architecture Diagram

```
┌─────────────────────────────────────┐
│  ROS 2 System Network               │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────────┐               │
│  │   Your Python    │               │
│  │ Bicycle Model    │               │
│  │   Node (.py)     │               │
│  └────────┬─────────┘               │
│           │                         │
│    ┌──────▼────────────┐            │
│    │ /odom (Odometry)  │            │
│    │ [x, y, θ, δ]      │            │
│    └──────┬────────────┘            │
│           │                         │
│  ┌────────▼──────────────────────┐  │
│  │   C++ MPC Controller Node      │  │
│  │  (mpc_controller_node)         │  │
│  │  - Solves optimization         │  │
│  │  - Computes controls           │  │
│  └────────┬──────────────────────┘  │
│           │                         │
│    ┌──────▼──────────────┐          │
│    │ /cmd_vel (Twist)    │          │
│    │ [v, δ_dot]          │          │
│    └──────┬──────────────┘          │
│           │                         │
│  ┌────────▼─────────────┐           │
│  │   Your Python Node   │           │
│  │  (reads /cmd_vel)    │           │
│  │  (updates bicycle)   │           │
│  └──────────────────────┘           │
│                                     │
└─────────────────────────────────────┘
```

## Message Flow

```
Time t=0:
  bicycle_model.py: state → /odom topic
  
Time t=0.05:
  mpc_controller (C++): reads /odom
  mpc_controller (C++): computes optimal control
  mpc_controller (C++): publishes to /cmd_vel
  
Time t=0.1:
  bicycle_model.py: reads /cmd_vel
  bicycle_model.py: updates dynamics
  bicycle_model.py: publishes new /odom
  
[Repeats with dt = 0.1s]
```

## Key Differences: Python vs C++

| Aspect | Python (your existing) | C++ (new MPC) |
|--------|------------------------|---------------|
| Performance | Slower, suitable for modeling | Fast, real-time capable |
| Dependencies | numpy, rclpy, scipy | rclcpp, Eigen, NLOPT |
| Update Rate | ~50 Hz typical | ~100-200 Hz typical |
| Memory | Higher | Lower |
| Development | Faster iteration | More optimizations needed |
| Debugging | Easier (print statements) | Harder (gdb) |

## Running Both Together

### Terminal 1: Build
```bash
cd ~/Control_Project
colcon build
```

### Terminal 2: Launch ROS 2 Daemon
```bash
ros2 daemon start
```

### Terminal 3: Run your Python bicycle model
```bash
ros2 run kinematic_bicycle bicycle_node
```
(or whatever your Python node is called)

### Terminal 4: Run C++ MPC controller
```bash
ros2 run mpc_controller mpc_controller_node
```

### Terminal 5: Monitor topics
```bash
ros2 topic list -t  # See all topics with types
ros2 topic echo /odom  # Watch odometry
ros2 topic echo /cmd_vel  # Watch commands
ros2 topic echo /mpc/predicted_path  # Watch predictions
```

## Cross-Language Communication

ROS 2 handles everything automatically:

```
Python publishes nav_msgs::Odometry → C++ MPC reads it (same message type)
C++ publishes geometry_msgs::Twist → Python reads it (same message type)
```

**No serialization/deserialization code needed!** ROS 2 DDS middleware handles it.

## Debugging Multi-Language System

1. **Check message rates**:
   ```bash
   ros2 topic hz /odom
   ros2 topic hz /cmd_vel
   ```

2. **Inspect messages**:
   ```bash
   ros2 topic echo /odom --once
   ```

3. **Record data for analysis**:
   ```bash
   ros2 bag record /odom /cmd_vel /mpc/predicted_path
   ```

4. **Check node status**:
   ```bash
   ros2 node list
   ros2 node info /mpc_controller
   ```

## Next: Optimize the C++ MPC

The basic C++ controller uses simple gradient descent. To make it production-ready:

```bash
# Install NLOPT for advanced optimization
sudo apt-get install libnlopt-dev libnlopt-cxx-dev
```

Then update `CMakeLists.txt`:
```cmake
find_package(nlopt REQUIRED)
target_link_libraries(mpc_lib nlopt::nlopt)
```

And replace the solver in `mpc_solver.cpp` with NLOPT:
```cpp
nlopt::opt opt(nlopt::LD_SLSQP, num_variables);
opt.minimize_objective_function(objective_func, ...);
```

This will give you **10-100x faster convergence!**
