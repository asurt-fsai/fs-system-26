# Cone Mapping Node - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### 1. Prerequisites Check

```bash
# Verify ROS2 Humble installation
ros2 --version

# Should output: ros2 doctor version 0.10.x

# Install Python dependencies
pip3 install numpy scipy
```

### 2. Build the Package

```bash
# Navigate to your workspace
cd ~/formula_student_ws/src

# Clone or copy the cone_mapping package
# (Assuming files are in cone_mapping directory)

# Build
cd ~/formula_student_ws
colcon build --packages-select cone_mapping

# Source the workspace
source install/setup.bash
```

### 3. Verify Static Transform

The node requires a static transform from `base_link` to `zed_camera`. 

**Option A: Use the launch file** (includes example transform)
```bash
ros2 launch cone_mapping cone_mapping_launch.py
```

**Option B: Publish manually**
```bash
ros2 run tf2_ros static_transform_publisher \
  0.3 0.0 0.5 0 0 0 1 base_link zed_camera
```

Replace `0.3 0.0 0.5` with your actual camera offset from vehicle center.

### 4. Connect Your Sensors

Ensure these topics are publishing:

```bash
# Check ZED pose
ros2 topic hz /zed2i/zed_node/pose

# Check perception detections
ros2 topic hz /perception/landmarks
```

### 5. Launch the Node

```bash
ros2 launch cone_mapping cone_mapping_launch.py log_level:=info
```

### 6. Verify Operation

```bash
# Check the global map is publishing
ros2 topic echo /map/global_cones

# Monitor node logs
ros2 topic echo /rosout | grep cone_mapping

# Expected output every 1 second:
# [cone_mapping_node]: Map: 47 total | Confirmed: 42 | Tentative: 3 | Lost: 2
```

---

## 🔧 Common Issues and Solutions

### Issue: "Static transform not available"

**Solution:** The TF from `base_link` to `zed_camera` is not being published.

```bash
# Check current transforms
ros2 run tf2_tools view_frames

# Manually publish if missing
ros2 run tf2_ros static_transform_publisher \
  X Y Z qx qy qz qw base_link zed_camera
```

### Issue: "No landmarks appearing in map"

**Checklist:**
1. ✅ Perception is publishing detections: `ros2 topic echo /perception/landmarks`
2. ✅ ZED pose is publishing: `ros2 topic echo /zed2i/zed_node/pose`
3. ✅ Detections are within 15m range
4. ✅ Static TF is configured correctly

**Debug:**
```bash
# Enable debug logging
ros2 launch cone_mapping cone_mapping_launch.py log_level:=debug
```

### Issue: "Landmarks flickering or disappearing"

**Tuning required:**

Edit `config/cone_mapping_params.yaml`:

```yaml
# Make confirmation easier (lower threshold)
observations_for_confirmation: 2  # Was: 3

# Keep landmarks longer before marking lost
frames_until_lost: 15  # Was: 10

# Increase timeout before deletion
timeout_until_deleted: 10.0  # Was: 5.0
```

Then restart:
```bash
ros2 launch cone_mapping cone_mapping_launch.py
```

### Issue: "Association errors / wrong matches"

**Likely causes:**
- SLAM drift too large between loop closures
- Detection noise higher than expected

**Tuning:**
```yaml
# Increase association gate (be more permissive)
association_gate_radius: 2.5  # Was: 2.0

# Increase measurement noise model
sigma_0_squared: 0.05  # Was: 0.01
noise_scale_factor: 0.05  # Was: 0.02
```

---

## 📊 Monitoring Performance

### Real-time Statistics

```bash
# Watch map updates
watch -n 1 "ros2 topic echo /map/global_cones --once | grep -c 'position'"

# Check processing rate
ros2 topic hz /map/global_cones
# Expected: ~10 Hz
```

### CPU and Memory

```bash
# Monitor resource usage
top -p $(pgrep -f cone_mapping_node)
```

**Expected on Jetson Xavier:**
- CPU: 10-20% of one core
- Memory: 30-60 MB

### Latency Check

```bash
# Measure end-to-end latency
ros2 topic delay /map/global_cones
```

**Target:** < 50ms total latency

---

## 🎯 Calibration Workflow

### Step 1: Measure Camera Position

Physically measure the camera's position relative to vehicle center:
- **X**: Forward distance (positive = ahead of center)
- **Y**: Lateral distance (positive = left of center)
- **Z**: Vertical distance (positive = above center)

Example: Camera mounted 30cm forward, 0cm left, 50cm above center:
```
X = 0.3
Y = 0.0
Z = 0.5
```

### Step 2: Measure Camera Orientation

If camera is not aligned with vehicle:
- Measure pitch, roll, yaw in degrees
- Convert to quaternion using: [https://quaternions.online](https://quaternions.online)

Example: Camera aligned with vehicle (no rotation):
```
qx = 0.0
qy = 0.0
qz = 0.0
qw = 1.0
```

### Step 3: Update Launch File

Edit `launch/cone_mapping_launch.py`:

```python
static_tf_publisher = Node(
    package='tf2_ros',
    executable='static_transform_publisher',
    name='base_to_camera_broadcaster',
    arguments=[
        '0.3', '0.0', '0.5',        # <-- Your X, Y, Z
        '0.0', '0.0', '0.0', '1.0',  # <-- Your quaternion
        'base_link',
        'zed_camera'
    ]
)
```

### Step 4: Validate

```bash
# Verify transform
ros2 run tf2_ros tf2_echo base_link zed_camera

# Check the translation and rotation match your measurements
```

---

## 🏁 First Track Test

### Pre-Test Checklist

- [ ] Static transform calibrated correctly
- [ ] ZED SLAM initialized and tracking
- [ ] Perception detections visible: `ros2 topic echo /perception/landmarks`
- [ ] Map publishing: `ros2 topic echo /map/global_cones`
- [ ] Parameters tuned for your track

### During Test

1. **Start slowly** - Let the system initialize landmarks
2. **Complete one full lap** - Build initial map
3. **Second lap** - Observe map refinement
4. **Check consistency** - Landmarks should be stable

### Post-Test Analysis

```bash
# Save rosbag for analysis
ros2 bag record -a -o test_run_1

# Replay and analyze
ros2 bag play test_run_1.db3
```

---

## 📋 Parameter Tuning Cheat Sheet

| Goal | Parameters to Adjust |
|------|---------------------|
| **More landmarks detected** | ↓ `observations_for_confirmation` to 2<br>↑ `max_detection_range` to 20.0 |
| **Fewer false positives** | ↑ `observations_for_confirmation` to 5<br>↓ `association_gate_radius` to 1.5 |
| **Faster recovery after occlusion** | ↓ `frames_until_lost` to 5<br>↑ `timeout_until_deleted` to 10.0 |
| **Better handling of noisy detections** | ↑ `sigma_0_squared` to 0.05<br>↑ `noise_scale_factor` to 0.05 |
| **Prevent duplicate landmarks** | ↓ `merge_distance_threshold` to 0.3 |

---

## 🐛 Debug Mode

Enable full debug output:

```bash
ros2 launch cone_mapping cone_mapping_launch.py \
  log_level:=debug \
  params_file:=$(pwd)/config/cone_mapping_params.yaml
```

This will log:
- Every detection transformation
- Association decisions
- Kalman filter updates
- Lifecycle state transitions

---

## 📞 Need Help?

**Check the full README:** See `README.md` for comprehensive documentation

**Run unit tests:**
```bash
python3 test_cone_mapping.py
```

**Common problems:** See "Troubleshooting" section in README.md

**Contact:** slam@asu-racing.com

---

## ✅ Success Criteria

Your system is working correctly when:

1. ✅ Map publishes at 10 Hz consistently
2. ✅ Confirmed landmark count stabilizes after 1 lap
3. ✅ Landmarks don't flicker or jump positions
4. ✅ New cones are detected on first pass
5. ✅ Map survives loop closure without corruption
6. ✅ Processing latency < 50ms
7. ✅ No error messages in logs

**Ready to race!** 🏎️💨
