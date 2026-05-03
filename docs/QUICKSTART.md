# MPC Controller — Quick Start

## 1. Build the Solver (first time only)

```bash
cd src/mpc_controller/src

# BLASFEO
cd blasfeo
mkdir -p build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../../install -DTARGET=X64_AUTOMATIC
make -j$(nproc) && make install
cd ../..

# HPIPM
cd hpipm
mkdir -p build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../../install -DBLASFEO_PATH=../../install
make -j$(nproc) && make install
cd ../../..
```

## 2. Build the ROS 2 Package

```bash
cd /home/ibrahim-el-dawy/FSAI_2026/MPC_Controller/Control_Project/fs-system-26
colcon build --packages-select mpc_controller
```

After every build, fix the package.dsv:

```bash
cp build/mpc_controller/ament_cmake_environment_hooks/package.dsv \
   install/mpc_controller/share/mpc_controller/package.dsv
```

## 3. Source + Set Library Path

```bash
source install/setup.bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)/src/mpc_controller/src/install/lib
```

## 4. Launch the Simulator Test

```bash
ros2 launch mpc_controller rviz_test.launch.py
```

This starts the bicycle simulator, MPC controller, track publisher, and RViz.

## 5. Launch for Real Car (IPG/CarMaker)

```bash
ros2 launch mpc_controller mpc.launch.py
```

---

## One-liner (build + run)

```bash
colcon build --packages-select mpc_controller && \
cp build/mpc_controller/ament_cmake_environment_hooks/package.dsv \
   install/mpc_controller/share/mpc_controller/package.dsv && \
source install/setup.bash && \
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)/src/mpc_controller/src/install/lib && \
ros2 launch mpc_controller rviz_test.launch.py
```

## Key Parameters

| File | What to tune |
|------|-------------|
| `src/mpc_controller/src/Params/cost.json` | `ref_velocity`, `q_c` (position tracking), `q_mu` (heading) |
| `src/mpc_controller/src/Params/model.json` | `wheelbase`, `dt` (timestep), `horizon` (N) |
| `src/mpc_controller/src/Params/bounds.json` | `v_max`, `delta_max`, `a_max` |
| `src/mpc_controller/src/config.h` | `N` (horizon length, must match model.json) |
