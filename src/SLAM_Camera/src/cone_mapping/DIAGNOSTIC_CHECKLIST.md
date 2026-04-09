# Cone Mapping System - Deep Diagnostic Checklist

## Overview
This checklist provides a comprehensive evaluation framework for the cone mapping system, covering all aspects from ROS communication to algorithm performance.

## How to Use
Run the automated diagnostic script:
```bash
cd /home/hazem/Desktop/FSAI/SLAM_Camera
python3 src/cone_mapping/diagnostics.py
```

Or manually verify each item below.

---

## 1. ROS 2 COMMUNICATION

### 1.1 Topic Existence
- [ ] `/perception/landmarks` exists
- [ ] `/zed2i/zed_node/pose` exists
- [ ] `/map/global_cones` exists
- [ ] `/tf` exists
- [ ] `/tf_static` exists

**Command**: `ros2 topic list`

### 1.2 Topic Types
- [ ] `/perception/landmarks` → `cone_mapping/msg/LandmarkArray`
- [ ] `/zed2i/zed_node/pose` → `geometry_msgs/msg/PoseStamped`
- [ ] `/map/global_cones` → `cone_mapping/msg/LandmarkArray`

**Command**: `ros2 topic type <topic_name>`

### 1.3 Publisher/Subscriber Connections
- [ ] `/perception/landmarks`: ≥1 publisher, ≥1 subscriber
- [ ] `/zed2i/zed_node/pose`: ≥1 publisher, ≥1 subscriber
- [ ] `/map/global_cones`: ≥1 publisher, ≥1 subscriber

**Command**: `ros2 topic info <topic_name>`

### 1.4 Message Frequencies
- [ ] `/perception/landmarks`: 9-11 Hz (target: 10 Hz)
- [ ] `/zed2i/zed_node/pose`: 9-11 Hz (target: 10 Hz)
- [ ] `/map/global_cones`: 9-11 Hz (target: 10 Hz)

**Command**: `ros2 topic hz <topic_name>`

---

## 2. MESSAGE CONTENT VALIDATION

### 2.1 Perception Landmarks
- [ ] Message contains `header` with valid timestamp
- [ ] Message contains `landmarks` array
- [ ] Landmarks have valid `position` (x, y, z)
- [ ] Landmarks have valid `type` (0-3)
- [ ] Landmarks have `probability` (0.0-1.0)
- [ ] At least some landmarks detected (not always empty)

**Command**: `ros2 topic echo /perception/landmarks --once`

### 2.2 Vehicle Pose
- [ ] Message contains `header` with valid timestamp
- [ ] Message contains `pose.position` (x, y, z)
- [ ] Message contains `pose.orientation` (quaternion)
- [ ] Position values are reasonable (not NaN/Inf)
- [ ] Orientation is normalized quaternion

**Command**: `ros2 topic echo /zed2i/zed_node/pose --once`

### 2.3 Global Map
- [ ] Message contains `header` with `frame_id: "map"`
- [ ] Message contains `landmarks` array
- [ ] Confirmed landmarks appear after ~30 seconds
- [ ] Landmark positions are in map frame
- [ ] No duplicate landmarks at same position

**Command**: `ros2 topic echo /map/global_cones --once`

---

## 3. TF TRANSFORMS

### 3.1 Static Transform
- [ ] `base_link` → `zed_camera` transform exists
- [ ] Translation: (0.3, 0.0, 0.5) meters
- [ ] Rotation: identity quaternion (0, 0, 0, 1)

**Command**: `ros2 run tf2_ros tf2_echo base_link zed_camera`

### 3.2 Dynamic Transforms
- [ ] `map` → `base_link` transform available (from pose)
- [ ] Transform chain: `map` → `base_link` → `zed_camera` complete

**Command**: `ros2 run tf2_tools view_frames.py`

---

## 4. PARAMETER LOADING

### 4.1 Critical Parameters
- [ ] `max_cone_height_deviation` loaded correctly
- [ ] Value is ≥ 0.5m (preferably 2.0m for simulator)
- [ ] `max_detection_range` = 15.0m
- [ ] All parameters logged at startup

**Check**: Node startup logs should show "Loaded parameters: height_dev=2.0m, range=15.0m"

### 4.2 Parameter File
- [ ] `config/cone_mapping_params.yaml` exists
- [ ] All required parameters present
- [ ] Values are within valid ranges

**File**: `src/cone_mapping/config/cone_mapping_params.yaml`

---

## 5. PROCESSING PIPELINE - PHASE BY PHASE

### 5.1 Phase 1: Transform & Gating
**Input**: Raw detections in camera frame  
**Output**: Validated detections in map frame

- [ ] Receives raw detections from perception
- [ ] Transforms from `zed_camera` frame to `map` frame
- [ ] Applies distance gating (≤15m)
- [ ] Applies height gating (|z| ≤ 2.0m)
- [ ] Some detections pass through (not all filtered)
- [ ] Logs show: "Phase 1: X raw detections → Y after transform & gating"

**Expected**: Y > 0 when cones are in range

**Debug**: If Y=0 always, check:
- Height deviation parameter (should be 2.0m)
- TF transforms are valid
- Detection range is reasonable

### 5.2 Phase 2: Data Association
**Input**: Validated detections + existing landmarks  
**Output**: Matched pairs, new detections, unmatched landmarks

- [ ] Builds cost matrix using Mahalanobis distance
- [ ] Applies Hungarian algorithm for optimal matching
- [ ] Identifies new detections (unmatched)
- [ ] Identifies lost landmarks (unmatched)
- [ ] Logs show: "Phase 2: X matches, Y new detections, Z unmatched landmarks"

**Expected**: Matches increase as landmarks are tracked

### 5.3 Phase 3: Kalman Filter Update
**Input**: Matched detection-landmark pairs  
**Output**: Updated landmark states and covariances

- [ ] Prediction step executed for all landmarks
- [ ] Update step executed for matched landmarks
- [ ] Innovation gating applied (Mahalanobis threshold)
- [ ] Covariance matrices remain positive definite
- [ ] Landmark positions converge over time

**Metrics**:
- Covariance trace should decrease with observations
- Position estimates should stabilize

### 5.4 Phase 4: Lifecycle Management
**Input**: Landmark observation history  
**Output**: Updated lifecycle states

States and transitions:
- [ ] **TENTATIVE**: New landmarks start here
- [ ] **TENTATIVE → CONFIRMED**: After 3+ observations with low covariance
- [ ] **CONFIRMED → LOST**: After 10+ frames without observation
- [ ] **LOST → DELETED**: After 5 seconds without re-observation
- [ ] **LOST → CONFIRMED**: If re-observed

**Check**: Map statistics show progression through states

### 5.5 Phase 5: Map Maintenance
**Input**: All landmarks  
**Output**: Cleaned and merged map

- [ ] Runs at 1 Hz (every second)
- [ ] Merges nearby confirmed landmarks (within 0.5m)
- [ ] Uses covariance-weighted averaging for merging
- [ ] Prunes deleted landmarks from map
- [ ] Logs show map statistics every second

**Expected**: Map size stabilizes, no unbounded growth

---

## 6. SYNCHRONIZED CALLBACKS

### 6.1 Message Synchronization
- [ ] `ApproximateTimeSynchronizer` configured
- [ ] Slop tolerance = 0.1 seconds (100ms)
- [ ] Queue size = 10
- [ ] Callbacks are triggered (counter increases)
- [ ] Logs show: "Processed X synchronized message pairs"

**Expected**: Callback count increases at ~10 Hz

### 6.2 Callback Execution
- [ ] No crashes or exceptions in callback
- [ ] Processing completes within 100ms
- [ ] All phases execute in sequence
- [ ] Map lock prevents race conditions

---

## 7. PERFORMANCE METRICS

### 7.1 Latency
- [ ] End-to-end latency < 100ms (perception → map)
- [ ] No significant processing delays
- [ ] Callback execution time reasonable

### 7.2 Throughput
- [ ] Processes 10 messages/second
- [ ] No message drops or queue overflow
- [ ] CPU usage < 50% on target hardware

### 7.3 Memory
- [ ] Map size bounded (no memory leaks)
- [ ] Landmark count stabilizes
- [ ] No unbounded array growth

---

## 8. ALGORITHM CORRECTNESS

### 8.1 Landmark Confirmation
- [ ] Landmarks confirm after 3+ observations
- [ ] Confirmation requires low covariance
- [ ] Only confirmed landmarks published
- [ ] Tentative landmarks not in output

**Test**: Run for 30+ seconds, check confirmed count > 0

### 8.2 Loop Closure
- [ ] Revisiting areas doesn't create duplicates
- [ ] Data association recognizes existing landmarks
- [ ] Map consistency maintained

**Test**: Use `test_case_3_loop_closure.py`

### 8.3 Noise Rejection
- [ ] Outliers rejected by innovation gating
- [ ] Kalman filter smooths noisy measurements
- [ ] False positives don't confirm

**Test**: Use `test_case_2_noisy.py`

---

## 9. ERROR HANDLING

### 9.1 Graceful Degradation
- [ ] Handles empty detection arrays
- [ ] Handles missing TF transforms
- [ ] Handles invalid measurements
- [ ] No crashes on edge cases

### 9.2 Logging
- [ ] Errors logged with context
- [ ] Warnings for unusual conditions
- [ ] Info logs for major events
- [ ] Debug logs available if needed

---

## 10. INTEGRATION TESTS

### 10.1 End-to-End Test
```bash
# Run for 60 seconds
# Expected results:
- [ ] System runs without crashes
- [ ] Confirmed landmarks: 5-15
- [ ] Tentative landmarks: 2-8
- [ ] Lost landmarks: 0-3
- [ ] Map frame_id = "map"
- [ ] All cone types present (blue, yellow)
```

### 10.2 Multi-Lap Test
```bash
# Use test_case_5_multilap.py
# Expected results:
- [ ] Map doesn't grow unbounded
- [ ] Duplicates are merged
- [ ] Consistent landmark count across laps
```

---

## DIAGNOSTIC SCRIPT OUTPUT

The `diagnostics.py` script automatically checks:
- ✓ All ROS communication tests (topics, types, frequencies)
- ✓ Message content validation
- ✓ TF transforms
- ✓ Parameter loading
- ✓ Phase-by-phase pipeline analysis
- ✓ Lifecycle state transitions
- ✓ Overall system health

**Generates**:
- Console output with color-coded results
- `/tmp/cone_mapping_diagnostics.log` - Full node logs
- `/tmp/cone_mapping_diagnostic_report.json` - Machine-readable results

---

## SUCCESS CRITERIA

### Minimum Requirements
- [ ] All ROS communication tests pass
- [ ] At least 1 landmark confirmed within 30 seconds
- [ ] No crashes or exceptions
- [ ] Message frequencies within ±10% of target

### Optimal Performance
- [ ] 5+ landmarks confirmed within 30 seconds
- [ ] <5% of detections filtered by gating
- [ ] >80% data association match rate
- [ ] <50ms average callback execution time

---

## TROUBLESHOOTING QUICK REFERENCE

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| No callbacks | Message sync issue | Check both topics publishing |
| All detections filtered | Height gating too strict | Set `max_cone_height_deviation: 2.0` |
| No confirmations | Insufficient observations | Run longer (30+ seconds) |
| Node crashes | AttributeError | Fixed: use `self.cone_type` |
| Empty map output | Lifecycle threshold | Lower `observations_for_confirmation` |
| Duplicate landmarks | Merge distance too large | Adjust `merge_distance_threshold` |

---

## KNOWN ISSUES AND RECENT FIXES

### ✅ Fixed Issues (February 2026)

#### 1. Launch File `IfCondition` Syntax Error
**Problem**: Launch file used string literals in `IfCondition` (e.g., `"test_case == 'ideal'"`)  
**Solution**: Use `PythonExpression` for string comparisons  
**Status**: ✅ Fixed in `test_launch.py`

#### 2. Parameter Type Mismatch
**Problem**: YAML had `max_cone_height_deviation: 2` (INTEGER) but node expected DOUBLE  
**Solution**: Use float notation `2.0` instead of `2` in YAML files  
**Status**: ✅ Fixed in `cone_mapping_params.yaml`

#### 3. Parameters Not Loading from YAML
**Problem**: Launch file didn't specify path to parameter file  
**Solution**: Use `PathJoinSubstitution` with `FindPackageShare` to locate config file  
**Status**: ✅ Fixed in `test_launch.py`

#### 4. All Detections Filtered in Phase 1
**Problem**: Height gating too strict (0.3m deviation)  
**Solution**: Increased `max_cone_height_deviation` to 2.0m for simulator  
**Status**: ✅ Fixed - system now detects landmarks successfully

### Current Configuration (Tested Feb 10, 2026)
- `observations_for_confirmation: 1` (tuned for fast testing, default: 3)
- `max_cone_height_deviation: 2.0` (meters)
- `max_detection_range: 15.0` (meters)
- **Test Results**: 6 landmarks detected, 100% peak confirmation rate

---

## ADDITIONAL RESOURCES

- **Test Results**: See `test_results/` directory for logs and visualizations
- **Recent Test Run**: `test_run_20260210_195532` (30 seconds, ideal conditions)
- **Walkthrough**: See project artifacts for detailed test walkthrough

