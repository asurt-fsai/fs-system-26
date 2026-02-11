# Cone Mapping Test Suite

This directory contains test scenarios for the cone mapping system. Each test simulates different real-world conditions.

## Test Files

### 1. `test_case_1_ideal.py` - Ideal Conditions ✅ **USED IN VERIFICATION**
**Purpose**: Baseline test with perfect conditions
- **Track**: Straight 50m track, cones every 5m
- **Noise**: Very low (σ = 0.02m)
- **Detection rate**: 98%
- **ID stability**: 99% (very stable)
- **Use case**: Verify basic functionality and algorithm correctness

**How to run**:
```bash
# Recommended: Using launch file
ros2 launch cone_mapping test_launch.py test_case:=ideal

# Alternative: Manual 3-terminal setup (advanced)
# Terminal 1: Start simulator
ros2 run cone_mapping test_case_1_ideal.py

# Terminal 2: Start mapper
ros2 run cone_mapping cone_mapping_node.py

# Terminal 3: Monitor map
ros2 topic echo /map/global_cones
```

**Note:** Launch file automatically starts TF publisher and loads parameters from YAML.

### 2. `test_case_2_noisy.py` - Noisy Detections
**Purpose**: Test robustness to sensor noise
- **Track**: Straight track with realistic noise
- **Noise**: High (σ = 0.15m)
- **Detection rate**: 85%
- **ID stability**: 70% (unstable tracking)
- **Use case**: Validate Kalman filtering and noise rejection

### 3. `test_case_3_loop_closure.py` - Loop Closure
**Purpose**: Test loop closure and map consistency
- **Track**: Circular track (20m radius)
- **Challenge**: Vehicle returns to start, must recognize same cones
- **Use case**: Verify data association handles revisiting areas

### 4. `test_case_5_multilap.py` - Multi-Lap Consistency
**Purpose**: Test long-term map stability
- **Track**: Figure-8 pattern
- **Challenge**: Multiple laps, overlapping paths
- **Use case**: Validate map doesn't accumulate duplicates

## Base Simulator

### `perception_simulator_base.py`
Base class providing:
- Vehicle motion simulation
- Sensor noise modeling
- Detection probability simulation
- Landmark publishing to `/perception/landmarks`
- Pose publishing to `/zed2i/zed_node/pose`

## Running Tests

### Quick Test (12 seconds)
```bash
# Start all components
ros2 run tf2_ros static_transform_publisher 0.3 0.0 0.5 0.0 0.0 0.0 1.0 base_link zed_camera &
ros2 run cone_mapping test_case_1_ideal.py &
ros2 run cone_mapping cone_mapping_node.py --ros-args -p max_cone_height_deviation:=2.0
```

### Extended Test (30+ seconds for confirmation)
Landmarks need observations to confirm (default: 3, tuned to 1 for testing). Run for at least 30 seconds to see confirmed landmarks.

**Recent Test Results (Feb 10, 2026):**
- 6 landmarks detected
- 100% peak confirmation rate
- Configuration: `observations_for_confirmation: 1`
- See `test_results/` directory for detailed logs and visualizations

## Expected Results

After 30 seconds with `test_case_1_ideal.py`:
- **Total landmarks**: 6 (with `observations_for_confirmation: 1`)
- **Peak confirmed**: 6 (100% confirmation rate)
- **Map frame**: All positions in global `map` frame
- **Cone types**: 0=Blue, 1=Yellow
- **Dynamic behavior**: Landmarks transition CONFIRMED ↔ LOST as vehicle moves (normal)

## Troubleshooting

### No landmarks confirmed
- **Cause**: Height gating too strict
- **Fix**: Set `max_cone_height_deviation: 2.0` in config or via parameter

### No detections passing through
- **Check**: Phase 1 logging shows "X raw detections → 0 after gating"
- **Fix**: Increase height deviation or detection range parameters

### Launch file errors
- **`IfCondition` syntax error**: Fixed - use `PythonExpression` for string comparisons
- **`InvalidParameterTypeException`**: Use float values (2.0) not integers (2) in YAML
- **Parameters not loading**: Fixed - launch file now uses `PathJoinSubstitution`

### Crashes with AttributeError
- **Fixed**: Changed `self.color` to `self.cone_type` in lifecycle management
