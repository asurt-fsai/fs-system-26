# MPC Controller — Complete Reference Guide

---

## What changed and why (session summary)

### Problems that were fixed

| # | Problem | Root Cause | Fix |
|---|---------|------------|-----|
| 1 | `colcon build` failed | `bicycle_simulator` not in CMakeLists.txt | Added as executable target |
| 2 | MPC received no odometry | Topic mismatch `/odom` vs `/carmaker/Odometry` | Added remappings in launch files |
| 3 | MPC received no steering feedback | No `/joint_states` from bicycle sim | Added `use_odom_steering` param; sim encodes `delta` in `odom.twist.linear.y` |
| 4 | No predicted path in RViz | Not published | Added `publishPredictedPath()` in controller |
| 5 | No CSV data | Not implemented | Added `initCsvLogger()` + `writeCsvRow()` |
| 6 | RViz crashed on launch | VS Code snap injects wrong `libpthread` via `GTK_PATH` | Set `GTK_PATH=''` before launching RViz |
| 7 | Track boundary wrong in RViz | Visualizer used symmetric `track_width` instead of `r_inner`/`r_outer` | Reads both from `model.json` |
| 8 | HPIPM libs not found at runtime | No RPATH embedded | Added `INSTALL_RPATH` to CMakeLists.txt |
| 9 | Messy source layout | All nodes in one folder `"IPG Node/"` | Reorganized into `controller/`, `bicycle_sim/`, `visualizer/` |

---

## New file/folder structure

```
src/mpc_controller/
├── config/
│   ├── nodes.json          ← Edit to rename nodes/topics WITHOUT recompiling
│   ├── mpc_test.rviz       ← RViz display config
│   └── (model.json, cost.json, bounds.json, normalization.json — installed here)
├── launch/
│   ├── bicycle_sim.launch.py    ← Bicycle simulator ONLY
│   ├── mpc_controller.launch.py ← MPC controller ONLY (real car / IPG)
│   ├── visualizer.launch.py     ← Visualizer + RViz ONLY
│   └── rviz_test.launch.py      ← All 4 together (sim + MPC + viz + RViz)
└── src/
    ├── controller/          ← mpc_controller_node.cpp/.h
    ├── bicycle_sim/         ← bicycle_simulator.cpp/.h
    ├── visualizer/          ← mpc_visualizer.cpp/.h
    ├── MPC/                 ← MPC solver core
    ├── Cost/                ← Cost function
    ├── Constraints/         ← Track constraints
    ├── Spline/              ← Arc/Cubic spline
    ├── Integrator/          ← RK4
    ├── Params/              ← JSON loader (model/cost/bounds/normalization)
    └── Interfaces/          ← HPIPM C++ wrapper

lap_tests/                   ← Auto-generated CSV files per run
    trial1.csv
    trial2.csv
    ...
```

---

## How to rename nodes and topics (without recompiling)

Edit `src/mpc_controller/config/nodes.json` **then rebuild** (`colcon build`):

```json
{
  "node_names": {
    "mpc_controller":    "mpc_controller",    // ← change node name here
    "bicycle_simulator": "bicycle_simulator",
    "mpc_visualizer":    "mpc_visualizer"
  },
  "topics": {
    "odometry":       "/carmaker/Odometry",   // ← odom input to MPC
    "ackermann_cmd":  "/ackr",               // ← command output from MPC
    "reference_path": "/path",               // ← track centerline input
    "predicted_path": "/mpc/predicted_path"  // ← MPC horizon output
  }
}
```

> After editing, run `colcon build --packages-select mpc_controller` (only the install step runs, ~0.2 s).

---

## How to launch each component

### Full test (simulator + MPC + visualizer + RViz)
```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch mpc_controller rviz_test.launch.py
# With custom track:
ros2 launch mpc_controller rviz_test.launch.py track_csv:=/path/to/track.csv
# Without CSV logging:
ros2 launch mpc_controller rviz_test.launch.py csv_enabled:=false
```

### Bicycle simulator only
```bash
ros2 launch mpc_controller bicycle_sim.launch.py
ros2 launch mpc_controller bicycle_sim.launch.py track_csv:=/path/to/track.csv
```

### MPC controller only (for real car / IPG)
```bash
ros2 launch mpc_controller mpc_controller.launch.py
ros2 launch mpc_controller mpc_controller.launch.py csv_enabled:=false
```

### Visualizer + RViz only
```bash
ros2 launch mpc_controller visualizer.launch.py
```

### Direct shell script (if ros2 launch environment is broken)
```bash
./launch_mpc_direct.sh --use-rviz        # full system
./launch_mpc_direct.sh                   # no RViz
./launch_mpc_direct.sh --no-sim          # MPC + viz only (real car mode)
```

---

## How the bicycle simulator works

**Source:** `src/mpc_controller/src/bicycle_sim/bicycle_simulator.cpp`

The simulator implements a **kinematic bicycle model** integrated with **4th-order Runge-Kutta (RK4)**:

| State | Symbol | Unit | Description |
|-------|--------|------|-------------|
| `x` | $x$ | m | Global X position |
| `y` | $y$ | m | Global Y position |
| `theta` | $\theta$ | rad | Yaw heading |
| `delta` | $\delta$ | rad | Front wheel steering angle |
| `v` | $v$ | m/s | Forward velocity |

**Dynamics:**
$$\dot{x} = v\cos\theta, \quad \dot{y} = v\sin\theta, \quad \dot{\theta} = \frac{v}{L}\tan\delta$$

**Inputs from MPC** (`/ackr` → AckermannDriveStamped):
- `drive.steering_angle` — target steering angle (servo-controlled, not rate)
- `drive.acceleration` — acceleration command

**How the car continues after finishing a lap:**

The track is loaded as a closed loop of 2713 waypoints. The MPC spline uses periodic boundary conditions (Arc Spline with wrap-around). When the car reaches the end of the track, the arc-length parameter `s` wraps back to 0. The simulator continues integrating the bicycle model indefinitely — there is no "stop at end" logic. The track publisher republishes the path every 2 seconds so any new subscriber gets it automatically.

**Steering feedback to MPC:** Because the simulator doesn't publish `/joint_states`, the current steering angle `delta` is encoded in `odom.twist.linear.y` (an unused field in standard odometry). The parameter `use_odom_steering: true` makes the MPC read delta from there.

---

## Cost function explained

**File:** `src/mpc_controller/src/Params/cost.json`

```json
{
  "ref_velocity": 8.0,      // Target speed [m/s] — raise to go faster
  "q_c": 10.0,              // Contouring error weight
  "q_c_N_mult": 5.0,        // Terminal contouring weight = q_c × q_c_N_mult
  "q_l": 40.0,              // Lag/progress error weight (tracks speed along path)
  "q_r": 0.0,               // Yaw rate tracking weight (usually 0)
  "q_vs": 10.0,             // Velocity tracking weight (tracks ref_velocity)
  "q_mu": 10.0,             // Heading alignment weight
  "a_lat_max": 3.0,         // Maximum lateral acceleration [m/s²]
  "r_delta": 0.1,           // Steering angle regularization (smooths steering)
  "r_dD": 0.01,             // Acceleration rate penalty (smooth acceleration)
  "r_dDelta": 0.6,          // Steering rate penalty (smooth steering changes)
  "sc_quad_track": 1e4,     // Quadratic slack penalty for track constraint violation
  "sc_lin_track": 1e3,      // Linear slack penalty for track constraint violation
  "weight_slack": 1e9       // Hard constraint violation weight (do not lower this)
}
```

### What each weight does

**`q_c` — contouring error:** Penalizes lateral deviation from the centerline. Higher = car hugs the center more tightly but may slow down on corners.

**`q_l` — lag error / progress:** Penalizes falling behind the reference speed profile. Higher = car accelerates harder to maintain `ref_velocity`.

**`q_vs` — velocity tracking:** Penalizes difference between actual speed and `ref_velocity`. Works with `q_l` — usually one is enough.

**`q_mu` — heading error:** Penalizes yaw misalignment relative to the track tangent. Higher = car aligns its heading more precisely (useful for preventing oscillation on straights).

**`r_dDelta` — steering rate penalty:** Penalizes rapid steering changes. This is the **most important smoothing weight**. Too low = oscillating steering. Too high = sluggish corner entry.

**`r_dD` — acceleration rate penalty:** Penalizes jerky acceleration/braking.

**`r_delta` — steering angle penalty:** Small bias toward straight-ahead steering.

**`sc_quad_track` / `sc_lin_track`:** Track boundary slack penalties. Higher = MPC fights harder to stay within `r_inner`/`r_outer`. Do not lower below 1e3 or the car will exit the track.

---

## Tuning the controller — step by step

### Step 1: Get it stable at low speed
Start with `ref_velocity: 3.0` in `cost.json`. Verify the car follows the track.

### Step 2: Fix oscillation
If steering oscillates:
- Increase `r_dDelta` (try 1.0 → 2.0)
- Increase `r_delta` (try 0.2 → 0.5)

### Step 3: Increase speed
Raise `ref_velocity` in 1 m/s steps. Watch `lateral_error_m` in CSV.

### Step 4: Tighten path following
If the car is cutting corners too aggressively:
- Increase `q_c` (try 15 → 30)
- Increase `q_c_N_mult` (try 5 → 10)

### Step 5: Improve lap time
- Lower `r_dDelta` slightly (allows faster corner entry)
- Raise `q_l` (car accelerates out of corners faster)
- Lower `a_lat_max` to restrict high-speed cornering only if needed

### Step 6: Track constraints
Edit `model.json`:
```json
"r_inner": 1.5,   // Left boundary offset from centerline [m]
"r_outer": 1.5    // Right boundary offset from centerline [m]
```
These come from the cone positions of the Formula Student track.

### Quick reference — parameter effects

| Want more of this | Change this |
|-------------------|-------------|
| Tighter path following | ↑ `q_c`, ↑ `q_c_N_mult` |
| Faster lap time | ↑ `ref_velocity`, ↑ `q_l` |
| Smoother steering | ↑ `r_dDelta` |
| Stronger acceleration | ↑ bounds `a_max` in `bounds.json` |
| Stay closer to track edges | ↑ `sc_quad_track` |

---

## Normalization weights — what they do and when to change them

**File:** `src/mpc_controller/src/Params/normalization.json`

Normalization scales variables so the QP solver sees numbers close to 1.0. This improves numerical conditioning and solver speed.

```json
{
  "state_normalization": {
    "X": 1.0,      // Scale for x position — set to expected max x deviation [m]
    "Y": 1.0,      // Scale for y position
    "theta": 1.0,  // Scale for heading [rad] — usually keep at 1.0 (max = π)
    "delta": 1.0,  // Scale for steering — set to delta_max (0.6109 rad)
    "v": 1.0       // Scale for velocity — set to v_max (10 m/s)
  },
  "control_normalization": {
    "a": 1.0,         // Scale for acceleration — set to a_max (5 m/s²)
    "delta_dot": 1.0  // Scale for steering rate — set to delta_dot_max (0.5 rad/s)
  }
}
```

**Example with proper scaling** (recommended for a 10 m/s, 951 m track):
```json
{
  "state_normalization": {
    "X": 250.0,    // max x range on your track
    "Y": 100.0,    // max y range
    "theta": 3.14,
    "delta": 0.61,
    "v": 10.0
  },
  "control_normalization": {
    "a": 5.0,
    "delta_dot": 0.5
  }
}
```

If the solver gives warnings about poor conditioning or solve times jump above 20 ms, try setting normalization to the maximum expected values of each variable.

---

## Exact steps to run on this PC

```bash
# 1. Open a native terminal (not VS Code terminal — snap causes RViz issues)
cd ~/FSAI_2026/MPC_Controller/Control_Project/fs-system-26

# 2. Build (only needed after code changes)
source /opt/ros/jazzy/setup.bash
colcon build --packages-select mpc_controller

# 3. Launch full test
source install/setup.bash
ros2 launch mpc_controller rviz_test.launch.py

# 4. Check CSV output
ls lap_tests/            # → trial1.csv, trial2.csv, ...
head lap_tests/trial1.csv
```

---

## Running on another PC with ROS 2 Humble (Ubuntu 22.04)

### Package and CMake changes required

**1. `package.xml` — no changes needed** (all packages exist in Humble)

**2. `CMakeLists.txt` — one change:**
```cmake
# Change minimum CMake version (optional but cleaner for Humble):
cmake_minimum_required(VERSION 3.8)   # stays the same, works on both
```

**3. Source changes — none.** All APIs used are identical between Jazzy (ROS 2 Iron/Jazzy) and Humble.

### Install commands for Humble

```bash
# Install ROS 2 Humble base
sudo apt install ros-humble-desktop

# Install required packages
sudo apt install \
  ros-humble-ackermann-msgs \
  ros-humble-nav-msgs \
  ros-humble-sensor-msgs \
  ros-humble-visualization-msgs \
  ros-humble-tf2 \
  ros-humble-tf2-ros \
  ros-humble-tf2-geometry-msgs \
  ros-humble-rosgraph-msgs \
  ros-humble-rviz2 \
  libeigen3-dev

# Source Humble (not jazzy)
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
```

### Build on Humble

```bash
cd ~/path/to/fs-system-26
source /opt/ros/humble/setup.bash
colcon build --packages-select mpc_controller
source install/setup.bash
ros2 launch mpc_controller rviz_test.launch.py
```

### Notes for Humble

- The HPIPM/BLASFEO solver libs are pre-compiled for x86-64 Linux and work on both Ubuntu 22.04 and 24.04.
- If you copy the workspace to the new PC, the RPATH is already embedded (`install/lib/...`), so no `LD_LIBRARY_PATH` changes needed.
- The `GTK_PATH=''` fix in the launch files also applies on Humble if running from a snap terminal.

---

## CSV columns explained

| Column | Unit | Description |
|--------|------|-------------|
| `time_s` | s | ROS wall time |
| `x` | m | Global X position |
| `y` | m | Global Y position |
| `theta_rad` | rad | Yaw heading |
| `v_ms` | m/s | Forward velocity |
| `delta_rad` | rad | Current steering angle |
| `acc_ms2` | m/s² | MPC acceleration command |
| `steering_cmd_rad` | rad/s | MPC steering rate command |
| `s_m` | m | Distance along track centerline |
| `lateral_error_m` | m | Perpendicular distance from centerline |
| `solve_time_ms` | ms | QP solver time (target: <10 ms) |
