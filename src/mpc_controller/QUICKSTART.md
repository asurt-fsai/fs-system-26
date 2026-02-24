# Quick Start: C++ MPC Controller

## 1. Build the Package

```bash
cd ~/Control_Project
colcon build --packages-select mpc_controller
source install/setup.bash
```

## 2. Verify Build

```bash
ros2 pkg list | grep mpc_controller
```

## 3. Run the Controller

```bash
ros2 run mpc_controller mpc_controller_node
```

## 4. Publish a Reference Path

In another terminal:
```bash
# Python script to publish reference path
python3 -c "
import rclpy
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped, Quaternion
import tf_transformations as tf

rclpy.init()
node = rclpy.create_node('path_publisher')
pub = node.create_publisher(Path, '/reference_path', 10)

path = Path()
path.header.frame_id = 'map'

# Straight line from (0,0) to (10,0)
for x in range(11):
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.pose.position.x = float(x)
    pose.pose.position.y = 0.0
    
    quat = tf.quaternion_from_euler(0, 0, 0)
    pose.pose.orientation = Quaternion(x=quat[0], y=quat[1], z=quat[2], w=quat[3])
    
    path.poses.append(pose)

pub.publish(path)
print('Published reference path')
rclpy.spin_once(node, timeout_sec=1)
"
```

## 5. Monitor Output

```bash
# In a new terminal, watch the control commands
ros2 topic echo /cmd_vel
```

## Code Organization

```cpp
// config.h - Where to change MPC parameters
config_.horizon = 10;           // More = better tracking, slower
config_.dt = 0.1;               // Control loop period

// Tune these weights:
config_.Q = diag([1, 1, 10, 0.1])   // [x, y, θ, δ]
config_.R = diag([0.1, 0.5])        // [v, δ_dot]
```

## Common Tasks

### Change Control Rate
Edit in `mpc_controller_node.cpp`:
```cpp
control_timer_ = this->create_wall_timer(
    std::chrono::milliseconds(100),  // Change this (milliseconds)
    std::bind(&MPCControllerNode::controlLoop, this)
);
```

### Tune Weight Matrices
Edit in `config.cpp`:
```cpp
void MPCConfig::initializeDefaults() {
    Q(0, 0) = 1.0;    // x weight
    Q(1, 1) = 1.0;    // y weight
    Q(2, 2) = 20.0;   // theta weight (INCREASE for better heading control)
    Q(3, 3) = 0.1;    // delta weight
    
    R(0, 0) = 0.2;    // velocity smoothness (INCREASE to penalize speed changes)
    R(1, 1) = 1.0;    // steering smoothness (INCREASE to penalize steering)
}
```

### Access Predicted Trajectory (for visualization)
```cpp
auto [info] = mpc_solver_->solve(...);
// Predicted trajectory published to /mpc/predicted_path
// View in RViz by adding Path display
```

## Troubleshooting

**Issue: Compilation fails**
```bash
# Make sure dependencies are installed
sudo apt-get install libeigen3-dev ros-humble-tf2* ros-humble-geometry-msgs
colcon build --packages-select mpc_controller --cmake-force-configure
```

**Issue: Node doesn't receive odometry**
```bash
ros2 topic list  # Check if /odom topic exists
ros2 topic echo /odom  # See if data is being published
```

**Issue: Controller outputs NaN**
```cpp
// Add bounds checking in mpc_controller_node.cpp
if (std::isnan(control(0)) || std::isnan(control(1))) {
    RCLCPP_WARN(this->get_logger(), "NaN detected in control");
    return;
}
```

## Next Steps

1. **Integrate with your bicycle model** - modify to accept `/cmd_vel` commands
2. **Upgrade optimization** - install NLOPT for faster solving
3. **Add parameter server** - tune weights without recompiling
4. **Profile performance** - measure CPU usage and latency

See `README.md` for detailed documentation.
