# Perception Simulator & Testing Guide

## Overview

This testing framework provides **5 comprehensive test scenarios** to validate the cone mapping system under various conditions. Each test case simulates realistic perception data with different challenges.

## Test Scenarios

### Test Case 1: Ideal Conditions ✅
**File:** `test_case_1_ideal.py`

**Characteristics:**
- Clean straight track (50m long)
- Minimal noise (σ = 0.02m)
- High detection rate (98%)
- Stable tracking IDs
- Regular cone spacing (5m intervals)

**Purpose:** Baseline validation - system should achieve near-perfect map

**Expected Results:**
- All cones confirmed within 1-2 laps
- Position errors < 5cm
- No false positives
- Stable confirmed landmark count

**Run:**
```bash
ros2 launch cone_mapping test_launch.py test_case:=ideal
```

---

### Test Case 2: Noisy Detections 🌊
**File:** `test_case_2_noisy.py`

**Characteristics:**
- Chicane track with curves
- High position noise (σ = 0.15m)
- Intermittent detections (75% success)
- Frequent ID resets (30% per frame)
- 5% color misclassification rate

**Purpose:** Test robustness to real-world perception failures

**Expected Results:**
- System maintains stable map despite noise
- Kalman filter effectively smooths positions
- Color consistency checks catch most errors
- Some landmarks may cycle through Lost state

**Run:**
```bash
ros2 launch cone_mapping test_launch.py test_case:=noisy log_level:=debug
```

---

### Test Case 3: Loop Closure 🔄
**File:** `test_case_3_loop_closure.py`

**Characteristics:**
- Circular track (24 cones)
- Simulated SLAM drift accumulation
- Periodic loop closure events (every 40m)
- Drift corrected at closure
- Multiple laps for convergence

**Purpose:** Validate frame semantics and loop closure handling

**Expected Results:**
- Map remains consistent after loop closure
- No duplicate landmarks created
- Landmarks automatically corrected with pose
- Multi-lap refinement improves accuracy

**Run:**
```bash
ros2 launch cone_mapping test_launch.py test_case:=loop_closure
```

**Watch for:**
```
[perception_sim_loop_closure]: LOOP CLOSURE EVENT - Correcting drift of (X, Y)m
[cone_mapping_node]: Map: N total | Confirmed: M | ...
```

---

### Test Case 4: Extreme Edge Cases ⚠️
**File:** `test_case_4_edge_cases.py`

**Characteristics:**
- Complex slalom track
- **Sensor blindness** (1-3s periods of no detections)
- **False positive bursts** (2-8 spurious detections)
- Variable noise levels (σ = 0.05-0.25m)
- Complete ID resets between laps
- Low confidence detections

**Purpose:** Stress test - ensure system doesn't break

**Expected Results:**
- System recovers from temporary blindness
- False positives rejected or pruned quickly
- No crashes or deadlocks
- Map quality degrades gracefully under stress

**Run:**
```bash
ros2 launch cone_mapping test_launch.py test_case:=edge_cases log_level:=warn
```

**Watch for:**
```
[perception_sim_edge_cases]: SENSOR BLIND MODE for 2.3s
[perception_sim_edge_cases]: FALSE POSITIVE BURST for 1.5s
[cone_mapping_node]: Map: X total | Confirmed: Y | Tentative: Z | Lost: W
```

---

### Test Case 5: Multi-Lap Accumulation 🔁
**File:** `test_case_5_multilap.py`

**Characteristics:**
- Realistic autocross track
- Continuous lapping (no reset)
- **Progressive improvement**: noise ↓, detection rate ↑ each lap
- Tests map persistence and refinement
- Orange start/finish markers

**Purpose:** Validate multi-lap strategy and convergence

**Expected Results:**
- Landmark count stabilizes after lap 1
- Position uncertainty decreases each lap
- Observation counts increase for all landmarks
- No landmark duplication

**Run:**
```bash
ros2 launch cone_mapping test_launch.py test_case:=multilap
```

**Watch for:**
```
[perception_sim_multilap]: LAP 1 COMPLETE - Noise: 0.108, Detection: 0.85
[perception_sim_multilap]: LAP 2 COMPLETE - Noise: 0.097, Detection: 0.88
[cone_mapping_node]: Map: 85 total | Confirmed: 82 | Tentative: 3 | Lost: 0
```

---

## Quick Start

### 1. Build the Package

```bash
cd ~/formula_student_ws
colcon build --packages-select cone_mapping
source install/setup.bash
```

### 2. Run a Test

```bash
# Basic test (ideal conditions)
ros2 launch cone_mapping test_launch.py test_case:=ideal

# With visualization
ros2 launch cone_mapping test_launch.py test_case:=noisy use_rviz:=true

# With debug logging
ros2 launch cone_mapping test_launch.py test_case:=edge_cases log_level:=debug

# Record data for analysis
ros2 launch cone_mapping test_launch.py test_case:=multilap record_bag:=true
```

### 3. Monitor Performance

**Terminal 1:** Watch map statistics
```bash
watch -n 1 "ros2 topic echo /rosout --once | grep 'Map:'"
```

**Terminal 2:** Check update frequency
```bash
ros2 topic hz /map/global_cones
# Should maintain ~10 Hz
```

**Terminal 3:** View detections
```bash
ros2 topic echo /perception/landmarks
```

---

## Message Format

The simulators publish data in the exact format expected by cone_mapping_node:

### LandmarkArray.msg
```
std_msgs/Header header
  stamp: timestamp
  frame_id: "zed_camera"
Landmark[] landmarks
```

### Landmark.msg
```
geometry_msgs/Point position  # x, y, z in camera frame
  x: forward distance
  y: lateral distance
  z: height
int32 type                    # 0=Blue, 1=Yellow, 2=Orange
int32 identifier              # Tracking ID (unstable)
float32 probability           # Confidence [0.0-1.0]
```

### Vehicle Pose
```
geometry_msgs/PoseStamped
  header.frame_id: "map"
  pose.position: x, y, z (in map frame)
  pose.orientation: quaternion (yaw rotation)
```

---

## Validation Checklist

For each test case, verify:

### ✅ Basic Operation
- [ ] Node starts without errors
- [ ] Detections being published at ~10 Hz
- [ ] Pose being published at ~10 Hz
- [ ] Map being published at ~10 Hz
- [ ] TF tree is complete (map → base_link → zed_camera)

### ✅ Map Quality
- [ ] Landmark count stabilizes (not continuously growing)
- [ ] Confirmed landmarks have low covariance (< 0.5 m²)
- [ ] No duplicate landmarks in same location
- [ ] Colors are consistent (blue on one side, yellow on other)
- [ ] Tentative → Confirmed transitions occur within 3 frames

### ✅ Robustness
- [ ] System handles missing detections gracefully
- [ ] False positives are rejected or pruned
- [ ] Loop closure doesn't corrupt map
- [ ] Multi-lap convergence is monotonic
- [ ] No memory leaks (stable RAM usage)

### ✅ Performance
- [ ] Processing latency < 50ms
- [ ] CPU usage < 30% (Jetson Xavier)
- [ ] No dropped messages
- [ ] Real-time operation maintained

---

## Advanced Analysis

### Record and Replay

```bash
# Record test run
ros2 launch cone_mapping test_launch.py test_case:=multilap record_bag:=true

# Replay
ros2 bag play test_run_0.db3

# Analyze in another terminal
ros2 topic echo /map/global_cones
```

### Custom Visualization

Create RViz config:
1. Add `/map/global_cones` as MarkerArray
2. Color by cone type
3. Show TF frames
4. Fixed frame: "map"

### Extract Metrics

```bash
# Count confirmed landmarks over time
ros2 topic echo /rosout | grep "Confirmed:" | awk '{print $NF}' > confirmed_count.txt

# Plot convergence
python3 plot_convergence.py confirmed_count.txt
```

---

## Troubleshooting

### No landmarks appearing

**Check:**
1. Is perception simulator running? `ros2 node list | grep perception`
2. Are detections being published? `ros2 topic hz /perception/landmarks`
3. Is TF available? `ros2 run tf2_ros tf2_echo base_link zed_camera`

**Fix:**
```bash
# Restart with debug logging
ros2 launch cone_mapping test_launch.py test_case:=ideal log_level:=debug
```

### Landmarks flickering

**Cause:** Detection rate too low or noise too high

**Fix:** Adjust parameters in `cone_mapping_params.yaml`:
```yaml
observations_for_confirmation: 2  # Lower threshold
frames_until_lost: 15  # More tolerance
```

### Loop closure breaking map

**Check:** Are landmarks stored in `map` frame?

**Debug:**
```bash
# Verify frame IDs
ros2 topic echo /map/global_cones --once | grep frame_id
# Should output: frame_id: "map"
```

### Performance issues

**Check resource usage:**
```bash
top -p $(pgrep -f cone_mapping)
```

**Optimize:**
- Reduce `max_detection_range` if cones are always near
- Increase `association_gate_radius` to reduce search space
- Disable debug logging

---

## Comparing Test Results

### Ideal vs. Noisy

| Metric | Ideal | Noisy |
|--------|-------|-------|
| Confirmation time | ~0.3s | ~1.5s |
| Position error | < 0.05m | < 0.15m |
| False positives | 0 | < 5% |
| Landmark stability | 100% | > 90% |

### Loop Closure Impact

Before closure: Drift accumulates (~0.5m after 40m)
After closure: Map jumps to corrected position
Landmark consistency: Maintained (no corruption)

### Multi-Lap Convergence

Lap 1: ~85 cones, covariance ~0.8 m²
Lap 2: ~85 cones, covariance ~0.4 m²
Lap 3: ~85 cones, covariance ~0.2 m²

---

## Creating Custom Tests

Extend `PerceptionSimulatorBase` to create your own scenarios:

```python
from perception_simulator_base import PerceptionSimulatorBase, ConeType

class MyCustomTest(PerceptionSimulatorBase):
    def setup_track(self):
        # Define cone positions
        self.ground_truth_cones = [
            {'position': np.array([x, y]), 'type': ConeType.BLUE},
            # ... more cones
        ]
    
    def update_vehicle_pose(self, dt):
        # Define vehicle motion
        speed = 5.0
        self.vehicle_position[0] += speed * dt
```

---

## Expected Test Durations

- **Ideal:** Run 2-3 minutes for 2 complete laps
- **Noisy:** Run 5 minutes to see noise filtering
- **Loop Closure:** Run 3-4 minutes for 2-3 closures
- **Edge Cases:** Run 5-10 minutes to catch all edge cases
- **Multi-Lap:** Run 10+ minutes for 3+ laps

---

## Success Criteria Summary

| Test Case | Success Criteria |
|-----------|------------------|
| Ideal | 100% cones confirmed, no errors |
| Noisy | >85% cones confirmed, graceful degradation |
| Loop Closure | Map survives 3+ closures without duplication |
| Edge Cases | No crashes during sensor failures |
| Multi-Lap | Convergence improves each lap |

---

## Next Steps

After validating with simulators:

1. **✅ Integrate real ZED camera** - Replace simulator with actual perception
2. **✅ Test on real track** - Validate in competition environment
3. **✅ Tune parameters** - Optimize for your specific setup
4. **✅ Add safety checks** - Implement additional validation layers
5. **✅ Profile performance** - Ensure real-time on target hardware

Good luck with testing! 🏎️💨
