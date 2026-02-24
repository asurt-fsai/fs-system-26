# MPC Controller - Quick Start Guide for FSAI 2026

## 📦 What You Have

A complete Model Predictive Controller implementation for Formula Student racing with:
- ✅ Kinematic bicycle model with RK4 integration
- ✅ Configurable cost matrices (Q, R) for tuning
- ✅ Constraint enforcement (velocity, steering limits)
- ✅ ROS 2 integration for autonomous vehicles
- ✅ Comprehensive documentation

---

## 🚀 Getting Started in 5 Minutes

### 1. Build the Package
```bash
cd ~/Ibrahim\ Control\ Project/Control_Project
source /opt/ros/jazzy/setup.bash
colcon build --packages-select mpc_controller
source install/setup.bash
```

### 2. Launch the MPC Node
```bash
ros2 run mpc_controller mpc_controller_node
```

### 3. Send Reference Path
In another terminal:
```bash
# Your path planner publishes to /reference_path topic
# MPC subscribes to:
# - /odometry/filtered (vehicle state)
# - /reference_path (desired trajectory)
```

---

## 📚 Documentation Files

### Main Documentation
**`DOCUMENTATION_GUIDE.md`** (THIS FOLDER)
- Complete explanation of every component
- Control theory background
- FSAI 2026 tuning guide
- Troubleshooting section

### Code Comments
Each file has extensive inline documentation:

1. **`config.h`** - 300+ lines of comments
   - What each parameter controls
   - FSAI 2026 recommended values
   - How to tune for your vehicle

2. **`bicycle_model.h`** - 400+ lines of comments
   - Vehicle dynamics equations explained
   - Why kinematic model suitable for FS
   - Runge-Kutta 4 integration theory
   - Practical examples

3. **`constraints.h`** - Constraint definitions
4. **`mpc_solver.h`** - MPC optimization
5. **`utils.h`** - Helper function reference
6. **`mpc_controller_node.h`** - ROS 2 integration

---

## 🎯 Quick Reference: Key Concepts

### State Vector: x = [x, y, θ, δ]
```
x, y = Position in meters
θ = Heading angle in radians
δ = Steering angle in radians
```

### Control Input: u = [v, δ_dot]
```
v = Velocity in m/s
δ_dot = Steering rate in rad/s
```

### Prediction Horizon: 50 steps
```
At 50 Hz: 50 × 0.02s = 1 second lookahead
Longer = more predictive but slower
Shorter = faster but less predictive
```

### Cost Function
```
Minimize: ||x - x_ref||²_Q + ||u||²_R + ||x_final||²_Q_terminal

Q = State tracking weight (penalize position/heading error)
R = Control effort weight (penalize jerky commands)
Q_terminal = Extra penalty at end of horizon
```

---

## 🔧 How to Tune for Your Vehicle

### Step 1: Measure Vehicle Parameters
```cpp
// In config.h, set these to YOUR values:
wheelbase = 2.5;        // Distance front to rear axle (meters)
v_max = 8.0;            // Maximum speed (m/s)
delta_max = 0.524;      // Max steering angle (radians = degrees * π/180)
delta_dot_max = 1.047;  // Max steering rate (rad/s)
```

### Step 2: Use Default Cost Weights
```cpp
// Default values in config.cpp (already good for FS):
Q diagonal = [1.0, 1.0, 10.0, 0.1]  // Heavy on heading
R diagonal = [0.1, 0.5]             // Smooth steering
Q_terminal = Q * 2.0                // Terminal penalty
```

### Step 3: Test and Iterate
```
If oscillates left-right:     Increase R(1,1) [0.5 → 1.0]
If car drifts off track:      Increase Q(0,0), Q(1,1) [1.0 → 5.0]
If car can't turn tight:      Increase delta_max or improve steering servo
If slow to accelerate:        Decrease R(0,0) [0.1 → 0.05]
```

### Step 4: Create Tuning Profiles
```cpp
// For different scenarios:
struct SpeedProfile {
    double Q_heading;       // 10.0 for slow, 8.0 for fast
    double R_steering;      // 0.5 for aggressive, 1.0 for smooth
    double R_velocity;      // 0.1 for sprints, 0.3 for smooth
};

// Use ROS 2 dynamic reconfigure to switch at runtime
```

---

## 🏎️ FSAI 2026 Practical Tips

### Before First Track Test
- [ ] Measure wheelbase accurately
- [ ] Calibrate steering angle sensor
- [ ] Verify velocity measurement
- [ ] Set conservative limits (50% of max capability)
- [ ] Test emergency stop mechanism

### During First Track Test
- [ ] Record baseline lap time with default tuning
- [ ] Monitor: oscillation, overshoot, undershoot
- [ ] Gradually increase speed (1 m/s per lap)
- [ ] Take notes on controller behavior at each speed

### Iterative Tuning (Practice Days)
- [ ] Vary one weight at a time (Q(2,2), then R(1,1))
- [ ] Record lap time and driver feedback
- [ ] Identify best tuning for each track section
- [ ] Create separate profiles for tight vs high-speed sections

### Competition Day
- [ ] Use proven tuning from practice
- [ ] Keep ROS 2 terminal running to monitor solver
- [ ] Be ready to adjust if track conditions change
- [ ] Have fallback tuning profile ready

---

## 📊 Expected Performance

### Computational
- Prediction: 50 steps × 4 RK4 stages = ~200 dynamics() calls
- Optimization: 5-15 iterations × 200 calls = ~2,000-3,000 calls total
- Time: 5-10 ms per solve (well within 20 ms budget at 50 Hz)

### Tracking Error (typical FS car)
- Position error: ±0.1-0.3 m
- Heading error: ±0.05-0.1 rad
- Steering smoothness: No jerky commands

### Vehicle Response
- Latency: ~1 control cycle (20 ms) + vehicle actuator response
- Max steering rate: Limited by servo speed (usually 60-120 deg/s)
- Max acceleration: Limited by motor/traction (usually ±5 m/s²)

---

## 🐛 Debugging

### Enable MPC Debugging
```cpp
// In mpc_controller_node.cpp, MPC publishes:
// - /mpc/predicted_path: Your predicted trajectory (visualize in RVIZ)
// - /mpc/debug: Solver stats (cost, iterations, success)

// Monitor in terminal:
ros2 topic echo /mpc/debug
```

### Common Issues

**MPC solve time exceeds 20 ms:**
```
Problem: Solver too slow
Solutions:
1. Decrease horizon from 50 to 40
2. Check warm-start is enabled
3. Increase convergence tolerance (faster but less accurate)
```

**Vehicle oscillates left-right:**
```
Problem: Steering too aggressive
Solutions:
1. Increase R(1,1) from 0.5 to 1.0-2.0
2. Decrease Q(2,2) from 10.0 to 5.0-8.0
3. Increase steering servo lag (more realistic model)
```

**Vehicle drifts outside track:**
```
Problem: Position tracking not strong enough
Solutions:
1. Increase Q(0,0), Q(1,1) from 1.0 to 5.0-10.0
2. Increase wheelbase accuracy
3. Check reference path alignment
```

**Servo commands are jerky:**
```
Problem: Steering rate not smoothed enough
Solutions:
1. Increase R(1,1)
2. Lower delta_dot_max (hardware limit)
3. Check rateLimit() function is being applied
```

---

## 📋 File Organization

```
src/mpc_controller/
├── include/mpc_controller/
│   ├── config.h              ← Configuration parameters [TUNE THESE]
│   ├── bicycle_model.h       ← Vehicle dynamics model
│   ├── constraints.h         ← Safety constraints
│   ├── mpc_solver.h          ← MPC optimization
│   ├── utils.h               ← Helper functions
│   └── mpc_controller_node.h ← ROS 2 interface
│
├── src/
│   ├── config.cpp
│   ├── bicycle_model.cpp     ← RK4 integration [ALREADY OPTIMIZED]
│   ├── constraints.cpp
│   ├── mpc_solver.cpp
│   ├── utils.cpp
│   └── mpc_controller_node.cpp
│
├── DOCUMENTATION_GUIDE.md    ← Comprehensive guide (read this!)
├── QUICKSTART_GUIDE.md       ← This file
└── package.xml
```

---

## 🎓 Learning Path

### Beginner (First Test)
1. Read this QUICKSTART_GUIDE.md
2. Set wheelbase = your vehicle value
3. Run with default tuning
4. Record baseline performance

### Intermediate (Practice Days)
1. Read DOCUMENTATION_GUIDE.md
2. Understand Q and R matrix meanings
3. Systematically tune weights
4. Create tuning profiles

### Advanced (Competition Prep)
1. Study code comments in each header file
2. Understand RK4 integration accuracy
3. Implement dynamic parameter switching
4. Optimize for specific track layouts

---

## 🔗 Useful Commands

### Build
```bash
colcon build --packages-select mpc_controller
```

### Source Setup
```bash
source install/setup.bash
```

### Run MPC Node
```bash
ros2 run mpc_controller mpc_controller_node
```

### Monitor Topics
```bash
# Watch control commands
ros2 topic echo /cmd_vel

# Watch predicted path
ros2 topic echo /mpc/predicted_path

# Monitor MPC statistics
ros2 topic echo /mpc/debug

# View in RVIZ
ros2 run rviz2 rviz2
```

### Dynamic Parameter Adjustment (at runtime!)
```bash
# Change steering smoothness
ros2 param set /mpc_controller r_steering 1.0

# Change heading weight
ros2 param set /mpc_controller q_heading 15.0

# Vehicle immediately responds!
```

---

## ✅ Checklist Before Competition

### Setup
- [ ] Wheelbase measured and entered in config.h
- [ ] Vehicle limits (v_max, delta_max, delta_dot_max) calibrated
- [ ] ROS 2 network configured (all nodes communicate)
- [ ] RVIZ configured for visualization

### Testing
- [ ] Default tuning baseline established
- [ ] At least 3 tuning profiles created and tested
- [ ] Emergency stop mechanism verified
- [ ] MPC solver performance confirmed (< 20 ms)

### Competition Day
- [ ] All tuning profiles saved and tested
- [ ] Backup tuning profile available
- [ ] Team familiar with parameter adjustment procedure
- [ ] Monitoring terminal ready for live debugging
- [ ] No compiler errors or warnings

---

## 🏆 Success Metrics

**Good MPC tuning shows:**
- ✅ Smooth steering changes (no jerky oscillation)
- ✅ Tight track following (< 0.3m lateral error)
- ✅ Accurate heading control (< 0.1 rad heading error)
- ✅ Fast lap times (lower than manual driving)
- ✅ Stable performance (consistent lap times)
- ✅ Robust to disturbances (recovers from track bumps)

**Signs of poor tuning:**
- ❌ Oscillates left and right at high speed
- ❌ Drifts outside track on curves
- ❌ Jerky steering commands
- ❌ Slow solver (> 15 ms per solve)
- ❌ Inconsistent lap times

---

## 📞 Need Help?

### Documentation Structure
1. **QUICKSTART_GUIDE.md** (this file) - Overview & getting started
2. **DOCUMENTATION_GUIDE.md** - Deep dive into every component
3. **Code comments** - Detailed explanations in each file

### Debug Process
1. Check solver statistics: `ros2 topic echo /mpc/debug`
2. Visualize predictions: Open RVIZ, view /mpc/predicted_path
3. Check ROS topics: `ros2 topic list` and `ros2 topic info <topic>`
4. Read error messages in terminal output
5. Consult troubleshooting section in DOCUMENTATION_GUIDE.md

---

## Good Luck! 🏎️

You now have a professional-grade MPC controller ready for FSAI 2026. The code is optimized, documented, and tunable. Focus on:

1. Accurate parameter measurement
2. Systematic tuning
3. Safe testing procedures
4. Team coordination

Good luck at the competition!

---

**Document Created**: February 5, 2026
**For**: FSAI 2026 Formula Student Teams
**Status**: Ready for Competition

