/**
 * @file ISAAC_SIM_INTEGRATION_GUIDE.md
 * @brief MPC Controller Isaac Sim Integration Guide
 * 
 * This document explains how the MPC controller integrates with NVIDIA Isaac Sim.
 */

# MPC Controller — Isaac Sim Integration Guide

## Overview

The MPC controller has been modified to work directly with **NVIDIA Isaac Sim** using the ROS 2 bridge.
The controller implements a **closed-loop control system** with an integration layer that converts
MPC optimization outputs into valid Ackermann drive commands.

---

## Data Flow

```
ISAAC SIM (Simulator)
     |
     |-- publishes → /odom (Odometry: position, velocity, heading)
     |-- publishes → /joint_states (Joint angles: steering wheel positions)
     |
     v
┌─────────────────────────────────────────┐
│  ROS 2 MPC Controller                   │
│  ┌─────────────────────────────────────┐│
│  │ STATE MEASUREMENT (from Isaac Sim)  ││
│  │  • v_meas (velocity)                ││
│  │  • x_meas, y_meas (position)        ││
│  │  • theta_meas (heading/yaw)         ││
│  │  • delta_meas (steering angle)      ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ MPC SOLVER                          ││
│  │  Inputs: Current state + track      ││
│  │  Outputs: delta_dot, acceleration  ││
│  │  (steering rate, accel)            ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ INTEGRATION LAYER (CRITICAL)        ││
│  │  delta_ref = delta_meas + δ̇ * dt   ││
│  │  v_ref     = v_meas    + a * dt    ││
│  │  (Clamp to limits)                  ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ PUBLISHER                           ││
│  │  → /ackermann_cmd (AckermannCmd)   ││
│  │    • steering_angle = delta_ref    ││
│  │    • speed = v_ref                 ││
│  │    • acceleration = a              ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
     |
     |-- publishes → /ackermann_cmd (to Isaac Sim Ackermann Controller)
     |
     v
ISAAC SIM (Ackermann Controller)
```

---

## Subscriptions (State Feedback)

### 1. `/odom` (nav_msgs/Odometry)

**Description**: Vehicle odometry from Isaac Sim
- **Source**: Isaac Sim vehicle state
- **Frequency**: ~100 Hz (typical)

**Extracted Fields**:
```cpp
x_meas_      = msg->pose.pose.position.x         // X position [m]
y_meas_      = msg->pose.pose.position.y         // Y position [m]
theta_meas_  = tf2::Matrix3x3(q).getRPY()[2]     // Yaw/heading [rad]
v_meas_      = msg->twist.twist.linear.x         // Forward velocity [m/s]
```

### 2. `/joint_states` (sensor_msgs/JointState)

**Description**: Joint positions of the robot (wheels, steering, etc.)
- **Source**: Isaac Sim joint state publisher
- **Frequency**: ~100 Hz

**Extracted Fields**:
```cpp
// Find steering joint indices by name:
// Common patterns: "steering_left_joint", "steering_right_joint"
//                  "front_left_wheel", "front_right_wheel"
delta_left  = msg->position[delta_left_idx]      // Left steering [rad]
delta_right = msg->position[delta_right_idx]     // Right steering [rad]
delta_meas_ = (delta_left + delta_right) / 2.0   // Mean steering [rad]
```

**NOTE**: Adjust joint names to match your Isaac Sim configuration in `jointStatesCallback()`.

### 3. `/clock` (rosgraph_msgs/Clock) [Optional]

**Description**: Simulation clock for time synchronization
- **Source**: Isaac Sim clock publisher
- **Usage**: Optional; currently not enforced but available for future synchronization

---

## Publication (Control Output)

### `/ackermann_cmd` (ackermann_msgs/AckermannDriveStamped)

**Description**: Control commands sent to Isaac Sim Ackermann controller
- **Frequency**: 100 Hz (configurable)
- **Message Fields**:

```cpp
msg.header.stamp            // Current timestamp
msg.drive.steering_angle    = delta_ref_           // Reference steering angle [rad]
msg.drive.steering_angle_velocity = |delta_dot_|  // Steering rate [rad/s]
msg.drive.speed             = v_ref_               // Reference speed [m/s]
msg.drive.acceleration      = a_                   // Desired acceleration [m/s²]
```

---

## Control Loop (100 Hz)

Each control cycle follows this sequence:

### 1. **Read State** (from ROS subscribers)
```
Wait for /odom and /joint_states messages
v_meas, x_meas, y_meas, theta_meas, delta_meas
```

### 2. **Run MPC** (closed-loop optimization)
```cpp
mpc_controller::state x0 = {x_meas, y_meas, theta_meas, v_meas, delta_meas};
mpc_controller::MPCReturn result = mpc_->runMPC(x0);

delta_dot_ = result.u0.delta_dot    // Steering rate [rad/s]
a_         = result.u0.D_dot        // Acceleration [m/s²]
```

### 3. **Integration Layer** (critical for closed-loop)
```cpp
// Integrate rates into reference commands
delta_ref_ = delta_meas_ + delta_dot_ * dt
v_ref_     = v_meas_ + a_ * dt

// Apply limits
delta_ref_ = clamp(delta_ref_, -max_steering_angle, max_steering_angle)
v_ref_     = clamp(v_ref_, 0.0, max_velocity)
```

### 4. **Publish Command** (to Isaac Sim)
```cpp
Send /ackermann_cmd with delta_ref_ and v_ref_
Isaac Sim Ackermann Controller receives command
```

### 5. **Loop Back**
```
Isaac Sim simulates vehicle dynamics
Publishes updated /odom (position, velocity)
Controller reads new state → repeat
```

---

## Key Parameters

Configure these in the ROS 2 parameter server or via launch file:

| Parameter | Default | Unit | Description |
|-----------|---------|------|-------------|
| `control_frequency` | 100.0 | Hz | Main control loop frequency |
| `max_steering_angle` | 0.6109 | rad | Maximum steering angle limit (~35°) |
| `max_velocity` | 15.0 | m/s | Maximum velocity limit |
| `model_path` | `params/model.json` | path | MPC vehicle model config |
| `costs_path` | `params/cost.json` | path | Cost function weights |
| `bounds_path` | `params/bounds.json` | path | State/control bounds |
| `norm_path` | `params/normalization.json` | path | Normalization factors |

### Set Parameters via Launch File

```bash
ros2 launch mpc_controller mpc_controller.launch.py \
  control_frequency:=100 \
  max_velocity:=20.0 \
  max_steering_angle:=0.7
```

---

## Integration Layer (CRITICAL)

The **integration layer** is crucial for closed-loop operation. It converts:

**MPC Outputs** → **Isaac Sim Commands**

### Steering Integration
```
delta_ref = delta_meas + delta_dot * dt
```
- `delta_meas`: Current measured steering angle (from `/joint_states`)
- `delta_dot`: MPC-computed steering rate (rad/s)
- `dt`: Time step (e.g., 0.01 s for 100 Hz)
- `delta_ref`: Reference steering angle sent to Isaac Sim

**Example**:
```
If delta_meas = 0.1 rad, delta_dot = 0.5 rad/s, dt = 0.01 s:
delta_ref = 0.1 + 0.5 * 0.01 = 0.105 rad
```

### Velocity Integration
```
v_ref = v_meas + a * dt
```
- `v_meas`: Current measured velocity (from `/odom`)
- `a`: MPC-computed acceleration (m/s²)
- `dt`: Time step
- `v_ref`: Reference velocity sent to Isaac Sim

**Example**:
```
If v_meas = 5.0 m/s, a = 1.0 m/s², dt = 0.01 s:
v_ref = 5.0 + 1.0 * 0.01 = 5.01 m/s
```

### Clamping
Both commands are clamped to physical limits:
```cpp
delta_ref = clamp(delta_ref, -max_steering_angle, max_steering_angle)
v_ref = clamp(v_ref, 0.0, max_velocity)
```

---

## Isaac Sim Configuration

For this controller to work with Isaac Sim, configure:

### 1. ROS 2 Bridge
Enable in Isaac Sim:
```
- /odom publisher (from vehicle position/velocity)
- /joint_states publisher (from steering joints)
- /ackermann_cmd subscriber (Ackermann controller)
```

### 2. Ackermann Controller
In Isaac Sim:
```
Set Ackermann controller to subscribe to /ackermann_cmd
Configure wheelbase and max steering angle to match model.json
```

### 3. Joint Names
Update `jointStatesCallback()` to match your Isaac Sim joint names:
```cpp
// In jointStatesCallback():
if (joint_name.find("YOUR_LEFT_STEERING_JOINT_NAME") != std::string::npos) {
    delta_left_idx = i;
}
```

---

## Closed-Loop vs. Open-Loop

### ❌ WRONG: Open-Loop Integration
```cpp
// BAD: Integrating without measuring
v_ref = v_prev + a * dt      // ❌ Drifts if a changes
delta_ref = delta_prev + delta_dot * dt
```

### ✅ CORRECT: Closed-Loop Integration
```cpp
// GOOD: Always use latest measured state
v_ref = v_meas + a * dt      // ✅ Uses current measurement
delta_ref = delta_meas + delta_dot * dt
```

This controller uses **closed-loop** integration, which ensures:
- State measurements are always fresh (from latest `/odom`, `/joint_states`)
- MPC solver uses actual vehicle state, not integrated estimates
- Errors are corrected at every control cycle

---

## Example Launch Command

```bash
# Build
cd ~/FSAI_2026/MPC_Controller/Control_Project/fs-system-26
colcon build --packages-select mpc_controller

# Source
source install/setup.bash

# Launch controller
ros2 launch mpc_controller mpc_controller.launch.py

# In Isaac Sim, publish path:
ros2 topic pub /path nav_msgs/msg/Path \
  '{"poses": [{"pose": {"position": {"x": 0.0, "y": 0.0}}}, ...]}'
```

---

## Debugging

### Check Topics
```bash
# Verify odometry
ros2 topic echo /odom

# Verify joint states
ros2 topic echo /joint_states

# Verify command output
ros2 topic echo /ackermann_cmd

# Monitor controller logs
ros2 run mpc_controller mpc_controller_node --ros-args --log-level mpc_controller:=DEBUG
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| No `/odom` messages | Isaac Sim bridge not running | Start Isaac Sim ROS 2 bridge |
| Wrong steering angle | Joint names mismatch | Update `jointStatesCallback()` |
| Vehicle not moving | `/ackermann_cmd` not received | Check Isaac Sim Ackermann controller subscriptions |
| High lateral error | MPC parameters mistuned | Adjust weights in `cost.json` |

---

## Code Structure

**Header**: `src/IPG Node/mpc_controller_node.h`
- State variables: `v_meas_`, `delta_meas_`, `delta_ref_`, `v_ref_`
- Subscribers: `odom_sub_`, `joint_states_sub_`, `reference_path_sub_`, `clock_sub_`
- Publisher: `ackermann_cmd_pub_`
- Methods: `odomCallback()`, `jointStatesCallback()`, `pathCallback()`, `controlLoop()`, `integrationLayer()`, `publishAckermannCommand()`

**Implementation**: `src/IPG Node/mpc_controller_node.cpp`
- Constructor: Sets up ROS 2 interfaces, MPC solver, control timer
- `odomCallback()`: Extracts state from Odometry message
- `jointStatesCallback()`: Extracts steering angle from JointState message
- `controlLoop()`: Main 100 Hz control loop
- `integrationLayer()`: Converts MPC rates to reference commands with limits
- `publishAckermannCommand()`: Sends Ackermann command to Isaac Sim

---

## Summary

✅ **Fully Integrated with Isaac Sim**
✅ **Closed-Loop Control** (uses measured state at every cycle)
✅ **Integration Layer** (converts rates to absolute commands)
✅ **Parameterizable** (100 Hz, adjustable steering/velocity limits)
✅ **Production-Ready** (clean code, modular structure)
✅ **MPC Logic Unchanged** (only I/O and integration modified)

---

**Last Updated**: 2026-05-02
