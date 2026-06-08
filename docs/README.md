# MPC Controller — Formula Student AI

Model Predictive Controller for a kinematic bicycle model, built on **ROS 2 Jazzy** with C++17, Eigen 5, and the HPIPM/BLASFEO QP solver.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Clone & First-Time Setup on a New PC](#clone--first-time-setup-on-a-new-pc)
5. [Building the Solver (BLASFEO + HPIPM)](#building-the-solver-blasfeo--hpipm)
6. [Building the ROS 2 Package](#building-the-ros-2-package)
7. [Running the Standalone RViz Test](#running-the-standalone-rviz-test)
8. [Running on the Real Car (IPG / CarMaker)](#running-on-the-real-car-ipg--carmaker)
9. [Configuration & Tuning](#configuration--tuning)
10. [ROS 2 Topics Reference](#ros-2-topics-reference)
11. [Project Structure](#project-structure)
12. [Troubleshooting](#troubleshooting)

---

## Overview

| Item | Detail |
|---|---|
| **Model** | Kinematic bicycle (5 states, 2 controls) |
| **States** | `[x, y, θ, δ, v]` — position, heading, steering angle, velocity |
| **Controls** | `[a, δ̇]` — acceleration, steering rate |
| **Solver** | HPIPM (with BLASFEO BLAS backend), SQP outer loop |
| **Cost** | MPCC — contouring error + lag error + heading + input regularization |
| **Horizon** | N = 20 steps, dt = 0.05 s (1 s look-ahead) |
| **ROS 2 distro** | Jazzy Jalisco (Ubuntu 24.04) |

The package provides **three executables**:

| Executable | Purpose |
|---|---|
| `mpc_controller_node` | Core MPC solver node — subscribes to odometry & track, publishes controls |
| `mpc_visualizer` | RViz visualization node — track, heading, constraints, predicted path |
| `bicycle_simulator` | Standalone kinematic simulator for offline testing (replaces IPG) |

---

## Architecture

```
┌──────────────────┐        /odom         ┌──────────────────────┐
│  IPG CarMaker    │ ──────────────────►  │  mpc_controller_node │
│  (or bicycle_    │  /reference_path     │                      │
│   simulator)     │ ◄────────────────    │  - SQP solve loop    │
│                  │        /cmd_vel      │  - publishes /cmd_vel│
└──────────────────┘ ◄────────────────    │  - publishes         │
                                          │    /mpc/predicted_path│
                                          └──────────────────────┘
                                                    │
                               /mpc/predicted_path  │  /odom
                                                    ▼
                                          ┌──────────────────────┐
                                          │   mpc_visualizer     │
                                          │                      │
                                          │  - track markers     │
                                          │  - heading arrow     │
                                          │  - vehicle footprint │
                                          │  - constraint normals│
                                          │  - TF broadcast      │
                                          └──────────────────────┘
                                                    │
                                                    ▼
                                                  RViz2
```

---

## Prerequisites

### System Requirements

- **OS:** Ubuntu 24.04 (Noble Numbat) — required for ROS 2 Jazzy
- **ROS 2:** Jazzy Jalisco (desktop install recommended for RViz)
- **Compiler:** GCC 13+ (ships with Ubuntu 24.04)
- **CMake:** 3.28+
- **Build tools:** `colcon`, `make`

### Install ROS 2 Jazzy (if not already installed)

Follow the official guide: <https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html>

Quick summary:

```bash
# 1. Set up sources
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 2. Install ROS 2 desktop (includes RViz)
sudo apt update
sudo apt install ros-jazzy-desktop

# 3. Install build tools
sudo apt install python3-colcon-common-extensions python3-rosdep
```

### Install Required ROS 2 Packages

```bash
sudo apt install \
  ros-jazzy-tf2 \
  ros-jazzy-tf2-ros \
  ros-jazzy-tf2-geometry-msgs \
  ros-jazzy-visualization-msgs \
  ros-jazzy-rviz2 \
  ros-jazzy-nav-msgs \
  ros-jazzy-geometry-msgs \
  ros-jazzy-std-msgs
```

> Most of these come with `ros-jazzy-desktop`. Run the above only if you did a
> minimal install.

### Install Eigen (if not pulled from the vendored copy)

The project vendors Eigen 5.0.0, but you may also install system Eigen:

```bash
sudo apt install libeigen3-dev
```

---

## Clone & First-Time Setup on a New PC

```bash
# 1. Source ROS 2
source /opt/ros/jazzy/setup.bash

# 2. Clone the repository
git clone <YOUR_REPO_URL> fs-system-26
cd fs-system-26

# 3. (Optional) Install any missing ROS dependencies via rosdep
sudo rosdep init        # only needed once per system
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# 4. Build the solver (see next section)

# 5. Build the ROS package (see section after)
```

---

## Building the Solver (BLASFEO + HPIPM)

The MPC uses the [HPIPM](https://github.com/giaf/hpipm) QP solver backed by [BLASFEO](https://github.com/giaf/blasfeo). A build script is provided that auto-detects your CPU and picks the fastest BLASFEO target.

> **If you skip this step**, the package will still compile — it falls back to
> **stub implementations** that satisfy the linker but do NOT actually solve
> QPs. You need the real solver for the controller to work at runtime.

```bash
cd src/mpc_controller/src

# Make the script executable (first time only)
chmod +x build_solver.sh

# Build in release mode (auto-detects AVX2 / AVX-512 / generic)
./build_solver.sh --release

# Optionally install the libs into src/install/
./build_solver.sh --install
```

### Script options

| Flag | Effect |
|---|---|
| `--release` | Optimized build (default) |
| `--debug` | Debug symbols, no optimization |
| `--clean` | Delete previous build artifacts first |
| `--install` | Copy built libs to `src/install/` |
| `--jobs N` | Parallel make jobs (default: nproc) |

### Verify solver build

```bash
# Check that the libraries exist
ls -la src/mpc_controller/src/build_solver/blasfeo/lib/libblasfeo.*
ls -la src/mpc_controller/src/build_solver/hpipm/lib/libhpipm.*
```

If both `.so` (or `.a`) files exist, the solver is ready.

---

## Building the ROS 2 Package

From the **workspace root** (`fs-system-26/`):

```bash
# 1. Source ROS 2
source /opt/ros/jazzy/setup.bash

# 2. Build
colcon build --packages-select mpc_controller --cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

# 3. Source the workspace overlay
source install/setup.bash
```

### Build output

After a successful build you should see three executables:

```bash
ls install/mpc_controller/lib/mpc_controller/
# → bicycle_simulator  mpc_controller_node  mpc_visualizer
```

And the launch/config files:

```bash
ls install/mpc_controller/share/mpc_controller/launch/
# → ipg_mpc.launch.py  rviz_test.launch.py

ls install/mpc_controller/share/mpc_controller/config/
# → mpc_test.rviz  bounds.json  config.json  cost.json  model.json  normalization.json
```

### Quick rebuild after code changes

```bash
source /opt/ros/jazzy/setup.bash
colcon build --packages-select mpc_controller
source install/setup.bash
```

---

## Running the Standalone RViz Test

This mode launches a self-contained simulation: a bicycle simulator generates
odometry and a reference track, the MPC controller tracks it, and everything
is visualized in RViz. **No IPG / CarMaker / real car needed.**

```bash
# 1. Source everything
source /opt/ros/jazzy/setup.bash
source install/setup.bash

# 2. Launch
ros2 launch mpc_controller rviz_test.launch.py
```

### What happens

1. **`bicycle_simulator`** starts immediately:
   - Publishes an **oval reference track** on `/reference_path`
   - Publishes vehicle odometry on `/odom` at 100 Hz
   - Listens for control commands on `/cmd_vel`
2. **`mpc_controller_node`** starts after a 1-second delay:
   - Ingests the track and odometry
   - Solves the MPC at 20 Hz (dt = 0.05 s)
   - Publishes acceleration + steering rate on `/cmd_vel`
   - Publishes the predicted horizon on `/mpc/predicted_path`
3. **`mpc_visualizer`** starts simultaneously:
   - Draws the track centerline (green), left boundary (red), right boundary (blue)
   - Shows a heading arrow (yellow) on the vehicle
   - Shows the vehicle footprint bounding box (cyan)
   - Shows MPC constraint normals (magenta arrows)
   - Shows the predicted path (green spheres)
   - Broadcasts TF `map → base_link`
4. **RViz2** opens with the pre-configured display layout

### Launch arguments

You can customize the test:

```bash
ros2 launch mpc_controller rviz_test.launch.py \
    track_a:=50.0 \       # oval semi-major axis [m] (default 40.0)
    track_b:=25.0 \       # oval semi-minor axis [m] (default 20.0)
    control_dt:=0.05       # MPC timestep [s] (default 0.05)
```

### What you should see in RViz

- A green oval track with red/blue boundaries
- A cyan box (the car) driving around the track
- A yellow heading arrow
- Magenta constraint arrows at each MPC prediction stage
- A green dotted predicted path ahead of the car

---

## Running on the Real Car (IPG / CarMaker)

For deployment with IPG CarMaker, the **IPG bridge** must be running separately
and publishing `/odom` and `/reference_path`.

```bash
# 1. Source
source /opt/ros/jazzy/setup.bash
source install/setup.bash

# 2. Launch the MPC + visualizer (no simulator)
ros2 launch mpc_controller ipg_mpc.launch.py
```

### Launch arguments

```bash
ros2 launch mpc_controller ipg_mpc.launch.py \
    control_dt:=0.05 \
    model_path:=/absolute/path/to/model.json \
    costs_path:=/absolute/path/to/cost.json \
    bounds_path:=/absolute/path/to/bounds.json \
    norm_path:=/absolute/path/to/normalization.json
```

> If you omit the path arguments, the node will look for the JSON files at the
> default paths specified in the installed config.

### IPG bridge requirements

Your IPG bridge node must publish:

| Topic | Message type | Content |
|---|---|---|
| `/odom` | `nav_msgs/Odometry` | Vehicle pose + twist in the `map` frame |
| `/reference_path` | `nav_msgs/Path` | Ordered list of track waypoints (x, y) |

The MPC publishes:

| Topic | Message type | Content |
|---|---|---|
| `/cmd_vel` | `geometry_msgs/Twist` | `linear.x` = acceleration [m/s²], `angular.z` = steering rate [rad/s] |

---

## Configuration & Tuning

All configuration lives in JSON files under `src/mpc_controller/src/Params/`.
After editing, **rebuild** the package so the updated files are copied to the
install space.

### `model.json` — Vehicle & MPC timing

| Parameter | Default | Description |
|---|---|---|
| `wheelbase` | 1.575 | Wheelbase [m] |
| `Lf` / `Lr` | 1.5 / 1.5 | Front/rear axle to CG [m] |
| `dt` | 0.05 | MPC sampling time [s] |
| `horizon` | 20 | Prediction horizon (N steps) |
| `r_inner` / `r_outer` | 10.0 / 15.0 | Inner/outer track constraint radii [m] |

### `cost.json` — Cost function weights

| Parameter | Default | Description |
|---|---|---|
| `q_c` | 1.0 | Contouring error weight |
| `q_l` | 0.5 | Lag error weight |
| `q_r` | 0.1 | Heading alignment weight |
| `q_vs` | 5.0 | Velocity tracking weight |
| `r_dD` | 0.01 | Acceleration input penalty |
| `r_dDelta` | 0.01 | Steering rate input penalty |
| `sc_quad_track` | 1e4 | Quadratic slack penalty (track constraints) |
| `sc_lin_track` | 1e3 | Linear slack penalty (track constraints) |
| `q_c_N_mult` | 10.0 | Terminal contouring multiplier |
| `q_r_N_mult` | 10.0 | Terminal heading multiplier |

**Tuning tips:**
- Increase `q_c` to reduce distance from track centerline
- Increase `q_l` to prevent the car from slowing down / falling behind the progress reference
- Increase `r_dDelta` if steering is too aggressive
- `sc_quad_track` / `sc_lin_track` are soft-constraint penalties — keep them high (1e3–1e5) to enforce track limits

### `bounds.json` — State & control limits

| Parameter | Default | Unit |
|---|---|---|
| `v_min` / `v_max` | 0 / 15 | m/s |
| `delta_min` / `delta_max` | -0.6109 / 0.6109 | rad (~±35°) |
| `a_min` / `a_max` | -5 / 5 | m/s² |
| `delta_dot_min/max` | -0.5 / 0.5 | rad/s |
| `theta_min/max` | -1e20 / 1e20 | rad (unbounded, allows heading unwrapping) |

### `normalization.json` — Numerical conditioning

Scaling factors for each variable. Set to 1.0 by default (no scaling). If the QP solver has conditioning issues, set each factor to the expected max value of that variable.

---

## ROS 2 Topics Reference

### Published by `mpc_controller_node`

| Topic | Type | Rate | Description |
|---|---|---|---|
| `/cmd_vel` | `geometry_msgs/Twist` | 20 Hz | `linear.x` = accel, `angular.z` = steering rate |
| `/mpc/predicted_path` | `nav_msgs/Path` | 20 Hz | N+1 predicted states |

### Published by `mpc_visualizer`

| Topic | Type | Rate | Description |
|---|---|---|---|
| `/mpc/track_markers` | `MarkerArray` | 20 Hz | Centerline + left/right boundaries |
| `/mpc/heading_arrow` | `Marker` | 20 Hz | Yellow arrow showing heading |
| `/mpc/vehicle_footprint` | `Marker` | 20 Hz | Cyan bounding box (base_link frame) |
| `/mpc/constraint_markers` | `MarkerArray` | 20 Hz | Magenta track constraint normals |
| TF: `map → base_link` | `tf2` | 20 Hz | Vehicle transform |

### Published by `bicycle_simulator`

| Topic | Type | Rate | Description |
|---|---|---|---|
| `/odom` | `nav_msgs/Odometry` | 100 Hz | Simulated vehicle state |
| `/reference_path` | `nav_msgs/Path` | Once (transient local) | Oval track waypoints |

### Subscribed by all nodes

| Topic | Node(s) |
|---|---|
| `/odom` | `mpc_controller_node`, `mpc_visualizer` |
| `/reference_path` | `mpc_controller_node`, `mpc_visualizer` |
| `/cmd_vel` | `bicycle_simulator` |
| `/mpc/predicted_path` | `mpc_visualizer` |

---

## Project Structure

```
fs-system-26/                        # Workspace root
├── src/
│   └── mpc_controller/              # ROS 2 package
│       ├── CMakeLists.txt
│       ├── package.xml
│       ├── README.md                # ← You are here
│       ├── config/
│       │   └── mpc_test.rviz        # RViz display config
│       ├── launch/
│       │   ├── ipg_mpc.launch.py    # Real car (IPG) launch
│       │   └── rviz_test.launch.py  # Standalone RViz test launch
│       ├── include/                  # Public headers (empty for now)
│       ├── docs/                     # Additional documentation
│       └── src/
│           ├── config.h / .cpp       # Compile-time constants (NX, NU, N, etc.)
│           ├── types.h / .cpp        # Common type aliases
│           ├── Bicycle Model/        # Kinematic bicycle model + analytical Jacobians
│           ├── Constraints/          # Box constraints + track constraints
│           ├── Cost/                 # MPCC cost function
│           ├── Integrator/           # Euler / RK4 integration templates
│           ├── Interfaces/           # HPIPM solver interface
│           ├── MPC/                  # Core MPC SQP solver
│           ├── Spline/              # Arc-length + cubic spline fitting
│           ├── Params/              # JSON configuration files
│           │   ├── config.json       # Master config (file paths)
│           │   ├── model.json        # Vehicle + timing params
│           │   ├── cost.json         # Cost weights
│           │   ├── bounds.json       # State/control limits
│           │   └── normalization.json
│           ├── IPG Node/            # ROS 2 nodes
│           │   ├── mpc_controller_node.h / .cpp
│           │   ├── mpc_visualizer.h / .cpp
│           │   └── mpc_visualizer_main.cpp
│           ├── rviz test/           # Standalone simulator
│           │   ├── bicycle_simulator.h
│           │   └── bicycle_simulator.cpp
│           ├── blasfeo/             # BLASFEO source (submodule / vendored)
│           ├── hpipm/               # HPIPM source
│           ├── hpipm-cpp-main/      # C++ wrapper for HPIPM
│           ├── hpipm_stubs/         # Fallback stubs when solver not built
│           ├── eigen-5.0.0/         # Vendored Eigen 5.0.0
│           ├── build_solver.sh      # Solver build script
│           └── setup_solver_env.sh  # Solver LD_LIBRARY_PATH helper
├── build/                           # colcon build output (gitignored)
├── install/                         # colcon install output (gitignored)
└── log/                             # colcon build logs (gitignored)
```

---

## Troubleshooting

### Build fails: "cannot find -lhpipm" or "cannot find -lblasfeo"

The solver libraries aren't built yet. Run:

```bash
cd src/mpc_controller/src
./build_solver.sh --release --install
cd ../../..
colcon build --packages-select mpc_controller
```

If BLASFEO/HPIPM sources aren't present, the build will use **stubs** — it compiles, but the solver doesn't actually work at runtime.

### Build fails: Eigen not found

```bash
sudo apt install libeigen3-dev
```

Or ensure the vendored copy at `src/mpc_controller/src/eigen-5.0.0/` is present and CMakeLists.txt points to it.

### RViz shows nothing / no track

- Check that `/reference_path` is being published:
  ```bash
  ros2 topic echo /reference_path --once
  ```
- The reference path uses **transient local** QoS. If you subscribed before the
  publisher started, re-launch.
- Check that the `mpc_test.rviz` config is loaded (it should auto-load with the launch file).

### Car doesn't move in RViz test

- Check `/cmd_vel` is being published:
  ```bash
  ros2 topic hz /cmd_vel
  ```
- If hz = 0, the MPC likely hasn't received the track yet. Wait a few seconds, or check:
  ```bash
  ros2 topic echo /reference_path --once
  ```
- Check the MPC node logs for solver errors:
  ```bash
  ros2 topic echo /rosout --filter "mpc"
  ```

### IntelliSense errors in VS Code (red squiggles)

These are usually not real compilation errors. Fix:

1. Make sure `.vscode/c_cpp_properties.json` includes `/opt/ros/jazzy/include/**`
2. Build with compile commands:
   ```bash
   colcon build --packages-select mpc_controller --cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
   ```
3. Set `"compileCommands"` in `c_cpp_properties.json` to:
   ```
   "${workspaceFolder}/build/mpc_controller/compile_commands.json"
   ```
4. Reload VS Code window (Ctrl+Shift+P → "Reload Window")

### LD_LIBRARY_PATH errors at runtime

If nodes crash with "cannot open shared object file" for BLASFEO/HPIPM:

```bash
source src/mpc_controller/src/setup_solver_env.sh
# or manually:
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)/src/mpc_controller/src/install/lib
```

### Rebuilding everything from scratch

```bash
# Clean all build artifacts
rm -rf build/ install/ log/

# Rebuild solver
cd src/mpc_controller/src
./build_solver.sh --clean --release --install
cd ../../..

# Rebuild package
source /opt/ros/jazzy/setup.bash
colcon build --packages-select mpc_controller
source install/setup.bash
```

---

## Quick-Start Cheat Sheet

```bash
# === On a fresh PC ===
# 1. Install ROS 2 Jazzy desktop (see Prerequisites)
# 2. Clone repo
git clone <REPO_URL> fs-system-26 && cd fs-system-26

# 3. Build solver
cd src/mpc_controller/src
chmod +x build_solver.sh
./build_solver.sh --release --install
cd ../../..

# 4. Build package
source /opt/ros/jazzy/setup.bash
colcon build --packages-select mpc_controller
source install/setup.bash

# 5. Run RViz test
ros2 launch mpc_controller rviz_test.launch.py

# === For IPG / real car ===
ros2 launch mpc_controller ipg_mpc.launch.py
```
