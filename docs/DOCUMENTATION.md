# MPC Controller — Formula Student AI
## Complete Documentation

> **ROS 2 Jazzy · C++17 · HPIPM/BLASFEO QP Solver · Kinematic Bicycle Model**

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Repository Structure](#2-repository-structure)
3. [Paths That Must Be Changed on a New PC](#3-paths-that-must-be-changed-on-a-new-pc)
4. [Prerequisites](#4-prerequisites)
5. [First-Time Setup — Solver Build (BLASFEO + HPIPM)](#5-first-time-setup--solver-build-blasfeo--hpipm)
6. [Building the ROS 2 Package](#6-building-the-ros-2-package)
7. [Launching the System](#7-launching-the-system)
8. [Running on a Different PC](#8-running-on-a-different-pc)
9. [Configuration & Tuning](#9-configuration--tuning)
10. [ROS 2 Topics Reference](#10-ros-2-topics-reference)
11. [Cost Function Explained](#11-cost-function-explained)
12. [Renaming Nodes and Topics](#12-renaming-nodes-and-topics)
13. [CSV Lap Logger](#13-csv-lap-logger)
14. [Bicycle Simulator Internals](#14-bicycle-simulator-internals)
15. [Architecture Diagram](#15-architecture-diagram)
16. [Troubleshooting](#16-troubleshooting)

---

## 1. Project Overview

| Item | Value |
|---|---|
| **Model** | Kinematic bicycle — 5 states `[x, y, θ, δ, v]`, 2 controls `[a, δ̇]` |
| **Solver** | HPIPM with BLASFEO BLAS backend (SQP outer loop) |
| **Cost** | MPCC — contouring error + lag error + heading + input regularisation |
| **Horizon** | N = 40 steps, dt = 0.05 s → 2 s look-ahead |
| **Track** | 2713 waypoints, ~951 m closed loop (`track.csv`) |
| **ROS 2** | Jazzy Jalisco (Ubuntu 24.04) |
| **Language** | C++17 |

### Executables

| Executable | Purpose |
|---|---|
| `mpc_controller_node` | Core MPC solver — subscribes to odometry & track, publishes Ackermann commands |
| `bicycle_simulator` | Kinematic simulator for offline testing (no IPG/Isaac Sim needed) |
| `mpc_visualizer` | RViz2 visualization — track boundaries, predicted path, vehicle footprint |

---

## 2. Repository Structure

```
fs-system-26/                         ← workspace root
├── track.csv                         ← 2713-waypoint track file (installed by colcon)
├── lap_tests/                        ← auto-generated CSV per run (trial1.csv, trial2.csv …)
│
├── docs/                             ← all project documentation
│   └── DOCUMENTATION.md              ← this file
│
├── src/
│   └── mpc_controller/               ← ROS 2 package
│       ├── CMakeLists.txt
│       ├── package.xml
│       │
│       ├── config/                   ← runtime config (installed to share/)
│       │   ├── nodes.json            ← rename nodes/topics without recompiling
│       │   ├── mpc_test.rviz         ← RViz display config
│       │   └── (track.csv is installed here by colcon)
│       │
│       ├── launch/
│       │   ├── bicycle_sim.launch.py      ← simulator only
│       │   ├── mpc_controller.launch.py   ← MPC controller only (real car / IPG)
│       │   └── visualizer.launch.py       ← visualizer + RViz only
│       │
│       └── src/
│           ├── config/               ← config.h / config.cpp  (compile-time constants)
│           ├── types/                ← types.h / types.cpp     (shared struct definitions)
│           ├── controller/           ← mpc_controller_node.cpp/.h
│           ├── bicycle_sim/          ← bicycle_simulator.cpp
│           ├── visualizer/           ← mpc_visualizer.cpp/.h
│           ├── MPC/                  ← MPC solver wrapper (mpc.cpp/h)
│           ├── Cost/                 ← MPCC cost function
│           ├── Constraints/          ← track boundary constraints
│           ├── Spline/               ← arc-length & cubic spline
│           ├── Integrator/           ← RK4 integration
│           ├── Params/               ← JSON param loader + *.json files
│           │   ├── cost.json
│           │   ├── model.json
│           │   ├── bounds.json
│           │   └── normalization.json
│           └── Interfaces/           ← HPIPM C++ wrapper
│
├── build/                            ← colcon build artifacts (do not commit)
├── install/                          ← colcon install tree (do not commit)
└── log/                              ← colcon build logs
```

---

## 3. Paths That Must Be Changed on a New PC

> These are the **only** absolute paths in the project. Everything else is relative.

### 3.1 Hardcoded in CMakeLists.txt — **no change needed**

`CMakeLists.txt` uses `${CMAKE_CURRENT_SOURCE_DIR}` everywhere, so paths are computed at build time and work on any machine as long as the folder structure is preserved.

### 3.2 Solver library location (environment variable — optional)

By default CMakeLists.txt looks for the pre-built solver at:
```
<workspace>/src/mpc_controller/src/install/lib/libblasfeo.so
<workspace>/src/mpc_controller/src/install/lib/libhpipm.so
```

If you moved the workspace or want to use a different install path, set these **before** running `colcon build`:
```bash
export MPC_SOLVER_INSTALL=/absolute/path/to/src/mpc_controller/src/install
export MPC_SOLVER_BUILD=/absolute/path/to/src/mpc_controller/src/build_solver/blasfeo
colcon build --packages-select mpc_controller
```

### 3.3 RPATH is embedded — no LD_LIBRARY_PATH needed at runtime

The solver `.so` paths are embedded into the executables as RPATH during build. You do **not** need to set `LD_LIBRARY_PATH` at runtime — `ros2 launch` works directly after `source install/setup.bash`.

### 3.4 CSV lap output directory

CSV files are saved to `<workspace_root>/lap_tests/`. The workspace root is computed automatically in the launch file (4 directory levels up from the installed package share). If colcon is run from a different directory, override with:
```bash
ros2 launch mpc_controller mpc_controller.launch.py csv_lap_dir:=/your/path/lap_tests
```

### 3.5 nodes.json topic names

If the real car or simulator uses different topic names, edit:
```
src/mpc_controller/config/nodes.json
```
then rebuild (details in [Section 12](#12-renaming-nodes-and-topics)).

---

## 4. Prerequisites

### System requirements

| Requirement | Version |
|---|---|
| OS | Ubuntu 24.04 (Noble) |
| ROS 2 | Jazzy Jalisco |
| GCC | 13+ |
| CMake | 3.28+ |
| Eigen3 | Any recent (via apt) |
| colcon | via pip / apt |

### Install ROS 2 Jazzy (if not present)

```bash
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu noble main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt install ros-jazzy-desktop python3-colcon-common-extensions
```

### Install required ROS 2 packages

```bash
sudo apt install \
  ros-jazzy-tf2 ros-jazzy-tf2-ros ros-jazzy-tf2-geometry-msgs \
  ros-jazzy-visualization-msgs ros-jazzy-rviz2 \
  ros-jazzy-nav-msgs ros-jazzy-geometry-msgs \
  ros-jazzy-ackermann-msgs ros-jazzy-sensor-msgs \
  ros-jazzy-rosgraph-msgs libeigen3-dev
```

---

## 5. First-Time Setup — Solver Build (BLASFEO + HPIPM)

> **This step is required once per machine.** The pre-built `.so` files in
> `src/mpc_controller/src/install/` are already committed if you cloned the
> repo. Only run this section if they are missing or you need to rebuild for
> a different CPU.

```bash
cd src/mpc_controller/src

# ── BLASFEO ──────────────────────────────────────────────────────────────
cd blasfeo
mkdir -p build && cd build
cmake .. \
  -DCMAKE_INSTALL_PREFIX=../../install \
  -DTARGET=X64_AUTOMATIC        # auto-detects AVX2 / AVX-512
make -j$(nproc) && make install
cd ../..

# ── HPIPM ─────────────────────────────────────────────────────────────────
cd hpipm
mkdir -p build && cd build
cmake .. \
  -DCMAKE_INSTALL_PREFIX=../../install \
  -DBLASFEO_PATH=../../install
make -j$(nproc) && make install
cd ../../..
```

After building, verify:
```bash
ls src/mpc_controller/src/install/lib/
# Expected: libblasfeo.so  libhpipm.so
```

---

## 6. Building the ROS 2 Package

```bash
# 1. Source ROS 2
source /opt/ros/jazzy/setup.bash

# 2. Build (from workspace root)
cd /path/to/fs-system-26
colcon build --packages-select mpc_controller

# 3. Source the install tree
source install/setup.bash
```

**Typical build time:**
- First full build: ~20–25 s
- Incremental (no source changes): ~0.2 s

**Build with verbose output (for debugging):**
```bash
colcon build --packages-select mpc_controller --cmake-args -DCMAKE_BUILD_TYPE=Release --event-handlers console_direct+
```

**Force clean reconfigure:**
```bash
colcon build --packages-select mpc_controller --cmake-force-configure
```

---

## 7. Launching the System

> Always source both ROS 2 and the workspace before launching:
> ```bash
> source /opt/ros/jazzy/setup.bash && source install/setup.bash
> ```

### 7.1 Simulator test (bicycle sim + MPC + visualizer + RViz)

Launch each component in a **separate terminal**:

**Terminal 1 — Bicycle Simulator:**
```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch mpc_controller bicycle_sim.launch.py
```

**Terminal 2 — MPC Controller:**
```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch mpc_controller mpc_controller.launch.py
```

**Terminal 3 — Visualizer + RViz:**
```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch mpc_controller visualizer.launch.py
```

### 7.2 Real car / IPG CarMaker (MPC only)

```bash
ros2 launch mpc_controller mpc_controller.launch.py
# Disable CSV logging:
ros2 launch mpc_controller mpc_controller.launch.py csv_enabled:=false
```

### 7.3 Visualizer only (when another system runs the sim and MPC)

```bash
ros2 launch mpc_controller visualizer.launch.py
```

### 7.4 Custom track CSV

```bash
ros2 launch mpc_controller bicycle_sim.launch.py \
  track_csv:=/absolute/path/to/my_track.csv
```

### 7.5 RViz snap crash fix

If you launch from **VS Code** and RViz crashes with a `libpthread` error, this is caused by VS Code's snap setting `GTK_PATH` to a snap-internal GTK. The `visualizer.launch.py` already sets `additional_env={'GTK_PATH': ''}` to clear this. If you launch RViz manually:
```bash
GTK_PATH="" rviz2 -d install/mpc_controller/share/mpc_controller/config/mpc_test.rviz
```

---

## 8. Running on a Different PC

### 8.1 Clone and set up

```bash
git clone <repo_url> fs-system-26
cd fs-system-26
git checkout control        # the main working branch
```

### 8.2 Install system dependencies (Section 4)

```bash
sudo apt install ros-jazzy-desktop python3-colcon-common-extensions \
  ros-jazzy-tf2 ros-jazzy-tf2-ros ros-jazzy-tf2-geometry-msgs \
  ros-jazzy-visualization-msgs ros-jazzy-rviz2 ros-jazzy-nav-msgs \
  ros-jazzy-geometry-msgs ros-jazzy-ackermann-msgs ros-jazzy-sensor-msgs \
  ros-jazzy-rosgraph-msgs libeigen3-dev
```

### 8.3 Check if solver libraries are present

```bash
ls src/mpc_controller/src/install/lib/libblasfeo.so
ls src/mpc_controller/src/install/lib/libhpipm.so
```

- **If both exist:** go straight to step 8.4.
- **If missing:** follow [Section 5](#5-first-time-setup--solver-build-blasfeo--hpipm) to rebuild them.

> **Note on CPU architecture:** The BLASFEO library is optimised for the CPU it was built on (`-DTARGET=X64_AUTOMATIC`). If you move from Intel to AMD (or vice versa) you should rebuild BLASFEO to get the best performance, but the existing `.so` will still run correctly on any x86-64 machine.

### 8.4 Build and run

```bash
source /opt/ros/jazzy/setup.bash
colcon build --packages-select mpc_controller
source install/setup.bash

# Terminal 1
ros2 launch mpc_controller bicycle_sim.launch.py

# Terminal 2
ros2 launch mpc_controller mpc_controller.launch.py

# Terminal 3
ros2 launch mpc_controller visualizer.launch.py
```

### 8.5 Nothing to change

All paths inside launch files, CMakeLists.txt, and the node source code are computed relative to the workspace or the installed package share. **No edits are required to run on a new machine** as long as the folder structure is the same.

The only thing that may differ is the `lap_tests/` directory, which is created automatically on first run.

---

## 9. Configuration & Tuning

All tunable parameters live in **JSON files** inside `src/mpc_controller/src/Params/`. They are installed to `install/mpc_controller/share/mpc_controller/config/` by `colcon build`.

### 9.1 `Params/model.json` — Vehicle geometry & MPC settings

| Key | Current Value | Description |
|---|---|---|
| `wheelbase` | `1.575` m | Distance between axles |
| `Lf` / `Lr` | `1.5` m | Front/rear axle to CoM |
| `r_inner` | `1.5` m | Track boundary margin — inner |
| `r_outer` | `1.5` m | Track boundary margin — outer |
| `dt` | `0.05` s | MPC time step |
| `horizon` | `40` | Prediction horizon N (must match `config.h`) |

> **Important:** If you change `horizon` here, also change `static constexpr int N = 40;` in `src/config/config.h` and rebuild.

### 9.2 `Params/bounds.json` — Control & state limits

| Key | Current Value | Description |
|---|---|---|
| `v_max` | `10.0` m/s | Maximum speed |
| `v_min` | `0.0` m/s | Minimum speed (no reverse) |
| `delta_max` | `0.6109` rad | Max steering angle (~35°) |
| `a_max` | `5.0` m/s² | Max acceleration |
| `a_min` | `-5.0` m/s² | Max braking |
| `delta_dot_max` | `0.5` rad/s | Max steering rate |
| `delta_dot_min` | `-0.5` rad/s | Min steering rate |

### 9.3 `Params/cost.json` — Cost weights

| Key | Current Value | Description |
|---|---|---|
| `ref_velocity` | `8.0` m/s | Target speed on straights |
| `q_c` | `10.0` | Contouring (lateral) error weight |
| `q_l` | `40.0` | Lag (longitudinal) error weight |
| `q_vs` | `10.0` | Velocity tracking weight |
| `q_mu` | `10.0` | Heading alignment weight |
| `r_dDelta` | `0.6` | Steering rate penalty |
| `r_dD` | `0.01` | Acceleration rate penalty |
| `sc_quad_track` | `1e4` | Quadratic soft-constraint penalty (track boundary) |
| `q_c_N_mult` | `5.0` | Terminal position weight multiplier |
| `a_lat_max` | `3.0` m/s² | Lateral accel limit for curvature-aware velocity reference |

**Quick tuning guide:**

| Goal | Change |
|---|---|
| Car cuts corners | Increase `q_c` |
| Car oscillates / steers jerkily | Increase `r_dDelta` |
| Car too slow in corners | Increase `a_lat_max` |
| Car ignores speed reference | Increase `q_vs` |
| Car doesn't align with track | Increase `q_mu` |
| Car violates track boundary | Increase `sc_quad_track` |

### 9.4 `src/config/config.h` — Compile-time constants

```cpp
static constexpr int NX  = 5;   // States: [x, y, theta, delta, v]
static constexpr int NU  = 2;   // Inputs: [acceleration, steering_rate]
static constexpr int N   = 40;  // Horizon (must match model.json)
static constexpr int NPC = 1;   // Polytopic constraints (track boundary)
static constexpr int NS  = 1;   // Soft constraints
```

> Changing `N` here requires a full `colcon build`.

---

## 10. ROS 2 Topics Reference

Topic names can be changed in `config/nodes.json` (see [Section 12](#12-renaming-nodes-and-topics)).

### Default topics

| Topic | Direction | Type | Publisher | Subscriber |
|---|---|---|---|---|
| `/carmaker/Odometry` | → MPC | `nav_msgs/Odometry` | bicycle_simulator | mpc_controller_node |
| `/path` | → MPC + Viz | `nav_msgs/Path` | bicycle_simulator | mpc_controller_node, mpc_visualizer |
| `/ackr` | MPC → | `ackermann_msgs/AckermannDriveStamped` | mpc_controller_node | bicycle_simulator |
| `/mpc/predicted_path` | → Viz | `nav_msgs/Path` | mpc_controller_node | mpc_visualizer |
| `/joint_states` | → MPC | `sensor_msgs/JointState` | (real car only) | mpc_controller_node |

**Steering feedback (simulator vs real car):**
- **Simulator:** steering angle `δ` is encoded in `odom.twist.linear.y` (unused field). MPC reads it with `use_odom_steering: true`.
- **Real car / IPG:** MPC reads `/joint_states` with `use_odom_steering: false`.

---

## 11. Cost Function Explained

The MPC minimises over the N=40 horizon:

$$J = \sum_{k=0}^{N-1} \ell(x_k, u_k) + \ell_N(x_N)$$

### Stage cost terms

| Term | Equation | Weight |
|---|---|---|
| Contouring error | $q_c \cdot e_c^2$ where $e_c$ = lateral deviation from track centre | `q_c = 10` |
| Lag error | $q_l \cdot e_l^2$ where $e_l$ = longitudinal deviation | `q_l = 40` |
| Heading alignment | $q_\mu \cdot (\theta - \theta_{ref})^2$ | `q_\mu = 10` |
| Velocity tracking | $q_{vs} \cdot (v - v_{ref})^2$ | `q_vs = 10` |
| Steering rate | $r_{\dot\delta} \cdot \dot\delta^2$ | `r_dDelta = 0.6` |
| Acceleration | $r_a \cdot a^2$ | `r_dD = 0.01` |
| Track boundary (soft) | $\sigma_{quad} \cdot s^2 + \sigma_{lin} \cdot s$ where $s$ = slack | `sc_quad_track = 1e4` |

### Curvature-aware velocity reference

The target speed adapts to track curvature automatically:

$$v_{ref} = \min\left(v_{max},\ \sqrt{\frac{a_{lat,max}}{|\kappa| + \epsilon}}\right)$$

- On a straight ($\kappa \approx 0$): $v_{ref} = v_{max} = 10$ m/s
- In a tight corner ($|\kappa|$ large): $v_{ref}$ is reduced automatically

---

## 12. Renaming Nodes and Topics

Edit `src/mpc_controller/config/nodes.json`:

```json
{
  "node_names": {
    "mpc_controller":    "mpc_controller",
    "bicycle_simulator": "bicycle_simulator",
    "mpc_visualizer":    "mpc_visualizer"
  },
  "topics": {
    "odometry":       "/carmaker/Odometry",
    "ackermann_cmd":  "/ackr",
    "reference_path": "/path",
    "predicted_path": "/mpc/predicted_path",
    "joint_states":   "/joint_states"
  }
}
```

After editing, run a rebuild (only the install step runs, ~0.2 s):
```bash
colcon build --packages-select mpc_controller
source install/setup.bash
```

No C++ recompilation is needed — the launch files read `nodes.json` at launch time.

---

## 13. CSV Lap Logger

The MPC controller node automatically saves a CSV file per run to `lap_tests/`.

### Auto-increment naming

The node finds the next free filename at startup:
```
lap_tests/trial1.csv
lap_tests/trial2.csv
lap_tests/trial3.csv
...
```
Files are never overwritten.

### CSV columns

```
time_s, x, y, theta_rad, v_ms, delta_rad, acc_ms2, steering_cmd_rad, s_m, lateral_error_m, solve_time_ms
```

### Control logging via launch argument

```bash
# Disable CSV logging
ros2 launch mpc_controller mpc_controller.launch.py csv_enabled:=false

# Custom output directory
ros2 launch mpc_controller mpc_controller.launch.py csv_lap_dir:=/tmp/my_logs
```

---

## 14. Bicycle Simulator Internals

**Source:** `src/mpc_controller/src/bicycle_sim/bicycle_simulator.cpp`

### Kinematic bicycle model (RK4 integration, dt = 0.05 s)

| State | Symbol | Unit |
|---|---|---|
| `x` | $x$ | m — global X |
| `y` | $y$ | m — global Y |
| `theta` | $\theta$ | rad — yaw |
| `delta` | $\delta$ | rad — front steering angle |
| `v` | $v$ | m/s — forward speed |

**Dynamics:**
$$\dot{x} = v\cos\theta, \quad \dot{y} = v\sin\theta, \quad \dot\theta = \frac{v}{L}\tan\delta, \quad \dot\delta = \dot\delta_{cmd}, \quad \dot{v} = a_{cmd}$$

### Lap continuation

The track is a closed loop of 2713 waypoints. The arc-length parameter `s` wraps around at the end of the lap — there is no stop condition. The simulator runs indefinitely and the track publisher re-publishes the path every 2 s for any late subscribers.

### Initial speed

```bash
ros2 launch mpc_controller bicycle_sim.launch.py initial_v:=3.0
```

---

## 15. Architecture Diagram

```
┌──────────────────────┐   /carmaker/Odometry    ┌─────────────────────────┐
│  bicycle_simulator   │ ──────────────────────► │  mpc_controller_node    │
│  (or real car / IPG) │                          │                         │
│                      │ ◄────────────────────── │  SQP solve (HPIPM)      │
└──────────────────────┘        /ackr             │  → publishes /ackr      │
         │                                        │  → publishes            │
         │ /path (transient_local)                │    /mpc/predicted_path  │
         └──────────────────────────────────────► └─────────────────────────┘
                                                             │
                                    /mpc/predicted_path      │
                                    /carmaker/Odometry        │
                                    /path                     ▼
                                                  ┌─────────────────────────┐
                                                  │  mpc_visualizer         │
                                                  │                         │
                                                  │  track boundaries       │
                                                  │  heading arrow          │
                                                  │  vehicle footprint      │
                                                  │  predicted path         │
                                                  └─────────────────────────┘
                                                             │
                                                             ▼
                                                           RViz2
```

---

## 16. Troubleshooting

### `libhpipm.so: cannot open shared object file`

RPATH is embedded in the executables during build. This error means the solver was not found at the RPATH location — the `.so` has moved or was never built.

**Fix:** Rebuild the solver (Section 5), then rebuild the package:
```bash
colcon build --packages-select mpc_controller --cmake-force-configure
source install/setup.bash
```

Or set the path manually:
```bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:<workspace>/src/mpc_controller/src/install/lib
```

---

### `Package 'mpc_controller' not found`

You have not sourced the workspace install.

**Fix:**
```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch mpc_controller bicycle_sim.launch.py
```

---

### RViz crashes with `undefined symbol: __libc_pthread_init`

Caused by VS Code's snap injecting `GTK_PATH=/snap/code/.../gtk-3.0`, which loads an incompatible Ubuntu 20.04 `libpthread` from the snap.

**Fix:** The `visualizer.launch.py` already sets `GTK_PATH=""`. If launching RViz manually:
```bash
GTK_PATH="" rviz2
```

---

### `Eigen3 not found`

```bash
sudo apt install libeigen3-dev
colcon build --packages-select mpc_controller --cmake-force-configure
```

---

### `rclcpp not found` / `tf2 not found`

ROS 2 is not sourced.
```bash
source /opt/ros/jazzy/setup.bash
```

---

### MPC solver produces no output / car doesn't move

1. Check that both `/carmaker/Odometry` and `/path` are being published:
   ```bash
   ros2 topic echo /carmaker/Odometry --once
   ros2 topic echo /path --once
   ```
2. Confirm the bicycle simulator is running and `bicycle_sim.launch.py` was launched first.
3. Check `use_odom_steering` — for the simulator it must be `true`, for real car `false`.

---

### Build uses too much memory / is killed

```bash
colcon build --packages-select mpc_controller --parallel-workers 1 -- -j2
```

---

### `horizon` in model.json doesn't match `N` in config.h

The compile-time constant `N` in `src/config/config.h` and the runtime value `horizon` in `Params/model.json` **must be equal**. If they differ, the HPIPM problem dimensions will be wrong.

Current values: both set to **40**.

To change: update both files and run `colcon build`.

---

*Last updated: May 2026. Branch: `control`.*
