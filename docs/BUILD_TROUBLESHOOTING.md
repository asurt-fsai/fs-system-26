# Build & Deployment Troubleshooting

## Pre-Build Checklist

```bash
# 1. Verify ROS 2 is sourced
echo $ROS_DISTRO
# Should output: humble (or your version)

# 2. Verify colcon is installed
which colcon
# Should return: /usr/bin/colcon

# 3. Check compiler
g++ --version
# Should show: g++ (Ubuntu 11.x.x)

# 4. Verify Eigen3
dpkg -l | grep eigen
# Should show: libeigen3-dev
```

## Build Steps

```bash
cd ~/Control_Project

# Clean (optional but recommended)
rm -rf build install log

# Build just the MPC package
colcon build --packages-select mpc_controller

# Or build with verbose output
colcon build --packages-select mpc_controller --cmake-args -DCMAKE_BUILD_TYPE=Release

# Source the workspace
source install/setup.bash
```

## Common Build Errors

### Error: "Eigen not found"
```
CMake Error: Cannot find package "Eigen3"
```

**Fix:**
```bash
sudo apt-get install libeigen3-dev
colcon build --packages-select mpc_controller --cmake-force-configure
```

### Error: "rclcpp not found"
```
CMake Error: Unknown CMake command "find_package(rclcpp REQUIRED)"
```

**Fix:**
```bash
source /opt/ros/humble/setup.bash  # Or your ROS distro
colcon build --packages-select mpc_controller
```

### Error: "tf2 not found"
```
CMake Error: Cannot find package "tf2"
```

**Fix:**
```bash
sudo apt-get install ros-humble-tf2-ros ros-humble-tf2-geometry-msgs
colcon build --packages-select mpc_controller
```

### Error: Compilation hangs or uses too much memory
```
c++ fatal error: Killed signal terminated program cc1plus
```

**Fix:**
```bash
# Reduce parallel jobs
colcon build --packages-select mpc_controller -j 2

# Or use all but one core
colcon build --packages-select mpc_controller -j $(( $(nproc) - 1 ))
```

## Runtime Errors

### Error: "mpc_controller_node: command not found"
```
/bin/bash: ros2: command not found
```

**Fix:**
```bash
source ~/Control_Project/install/setup.bash
ros2 run mpc_controller mpc_controller_node
```

### Error: "Cannot open shared library"
```
error while loading shared libraries: libmpc_controller.so
```

**Fix:**
```bash
source ~/Control_Project/install/setup.bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:~/Control_Project/install/mpc_controller/lib
ros2 run mpc_controller mpc_controller_node
```

### Error: Node starts but receives no messages
```
[mpc_controller] INFO: MPC Controller Node initialized
[mpc_controller] INFO: Waiting for odometry...
```

**Check:**
```bash
# Terminal 2: Check if odometry is being published
ros2 topic echo /odom

# If empty, your Python bicycle model isn't running
# Terminal 1: Start your bicycle model
ros2 run kinematic_bicycle bicycle_node
```

### Error: NaN in computed controls
```
[mpc_controller] WARN: NaN detected in control
```

**Causes and fixes:**
```cpp
// 1. Check config weights are initialized
config_.initializeDefaults();

// 2. Verify reference trajectory is finite
for (size_t i = 0; i < reference_traj.rows(); ++i) {
    if (!std::isfinite(reference_traj(i, 0))) {
        RCLCPP_ERROR(this->get_logger(), "NaN in reference trajectory");
        return;
    }
}

// 3. Check steering angle isn't exceeding limits
if (std::abs(state(3)) > config_.delta_max) {
    RCLCPP_WARN(this->get_logger(), "Steering angle out of bounds");
}
```

## Performance Issues

### Issue: Controller updates slowly (< 10 Hz)
```
[diagnostic_aggregator] Warning: MPC controller running at 5 Hz, expected 10 Hz
```

**Diagnosis:**
```bash
# Check CPU usage
top -p $(pgrep -f mpc_controller_node)
# If > 80% CPU, optimization is too slow

# Check optimization time
ros2 topic echo /mpc/debug
# Check first value (cost) and second (iterations)
```

**Solutions:**
1. **Reduce horizon:** `config_.horizon = 5;` (but less accurate)
2. **Increase dt:** `config_.dt = 0.2;` (but less responsive)
3. **Install NLOPT:** (See NLOPT_INTEGRATION.md)
4. **Profile code:** Use `gprof` or `perf`

### Issue: Controls are jerky or oscillating
```
Vehicle moves forward, then backward repeatedly
```

**Causes and fixes:**

```cpp
// 1. Weights are unbalanced
config_.Q = diag([1, 1, 50, 0.1]);  // Too much heading penalty
// Fix: Reduce slightly
config_.Q = diag([1, 1, 10, 0.1]);

// 2. Horizon is too short
config_.horizon = 3;  // Can't see far enough ahead
// Fix: Increase to 10-15

// 3. Control rate is too slow relative to horizon
config_.dt = 0.5;  // 2 Hz update with 10-step horizon = 5 sec prediction
// Fix: Increase update rate to 10+ Hz
```

## Deployment Checklist

```bash
# 1. Clean rebuild
rm -rf build install log
colcon build --packages-select mpc_controller

# 2. Verify executable exists
ls -l install/mpc_controller/lib/mpc_controller/mpc_controller_node

# 3. Test in simulator
ros2 run kinematic_bicycle bicycle_node &
ros2 run mpc_controller mpc_controller_node &
ros2 topic pub /reference_path nav_msgs/Path '{...}'

# 4. Record data
ros2 bag record /odom /cmd_vel /mpc/predicted_path -o test_run

# 5. Analyze performance
# - Check message delays: ros2 topic hz /cmd_vel
# - Check CPU: top
# - Check memory: free -h
```

## Debugging with GDB

```bash
# Build with debug symbols
colcon build --packages-select mpc_controller \
  --cmake-args -DCMAKE_BUILD_TYPE=Debug

# Run with debugger
gdb ros2
> run run mpc_controller mpc_controller_node
> break src/mpc_controller_node.cpp:100
> continue
> print state_
> quit
```

## Optimization for Production

```bash
# Build with optimizations
colcon build --packages-select mpc_controller \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \
                -DCMAKE_CXX_FLAGS="-O3 -march=native"

# This will:
# - 2-5x faster execution
# - Use CPU-specific optimizations
# - Only slightly longer compilation
```

## Memory Profiling

```bash
# Install memory profiler
sudo apt-get install google-perftools

# Run with profiling
CPUPROFILE=/tmp/mpc.prof ros2 run mpc_controller mpc_controller_node
# Wait a bit, then Ctrl+C

# Analyze results
google-pprof --svg /opt/ros/humble/lib/mpc_controller/mpc_controller_node /tmp/mpc.prof
# Opens visualization in browser
```

## Continuous Integration

For automated testing:

```yaml
# .github/workflows/build.yml
name: Build MPC Controller
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v2
      - name: Build
        run: |
          colcon build --packages-select mpc_controller
      - name: Test
        run: |
          colcon test --packages-select mpc_controller
```

## Final Verification

```bash
# 1. Can build?
colcon build --packages-select mpc_controller && echo "✅ Build OK"

# 2. Can run?
timeout 2 ros2 run mpc_controller mpc_controller_node && echo "✅ Run OK"

# 3. Published topics?
ros2 topic list | grep mpc && echo "✅ Topics OK"

# 4. No memory leaks? (Optional)
valgrind --leak-check=full ros2 run mpc_controller mpc_controller_node
```

## Support Resources

- **ROS 2 Build Issues:** https://docs.ros.org/en/humble/
- **CMake Help:** https://cmake.org/documentation/
- **Eigen Documentation:** https://eigen.tuxfamily.org/
- **GDB Debugging:** https://www.gnu.org/software/gdb/documentation/

---

Most issues can be fixed by:
1. `source /opt/ros/humble/setup.bash`
2. `colcon build --cmake-force-configure`
3. `source install/setup.bash`
