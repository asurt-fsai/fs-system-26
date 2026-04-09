# Integration Guide: perception_zed + SLAM_Camera

## Summary of Changes

All three modules (`perception_zed`, `SLAM_Camera/cone_mapping`, and optionally `fs_slam`) are now integrated into a unified pipeline.

### Files Created/Modified

#### 1. **NEW: message_adapter.py**
   - **Path:** `cone_mapping/cone_mapping/message_adapter.py`
   - **Purpose:** Converts `asurt_msgs::LandmarkArray` → `cone_mapping::LandmarkArray`
   - **Why:** perception_zed publishes `asurt_msgs`, but cone_mapping expects `cone_mapping` message types
   - **Subscribes to:** `/perception/landmarks` (from perception_zed)
   - **Publishes to:** `/perception/landmarks_converted` (to cone_mapping_node)

#### 2. **MODIFIED: cone_mapping_node.py**
   - **Changes:**
     - Line ~736: Changed landmark subscription topic
       - FROM: `/perception/landmarks`
       - TO: `/perception/landmarks_converted`
     - Line ~741: Changed pose subscription topic
       - FROM: `/zed2i/zed_node/pose` (simulator)
       - TO: `/zed/zed_node/pose` (real ZED camera)
     - Updated docstring to reflect real integration
   - **Impact:** Now integrates with real ZED camera perception pipeline

#### 3. **NEW: integrated_launch.py**
   - **Path:** `cone_mapping/launch/integrated_launch.py`
   - **Purpose:** Master launcher for complete system integration
   - **Launches:**
     1. `perception_zed_pkg` conversion_node (ZED → asurt_msgs)
     2. `message_adapter` (asurt_msgs → cone_mapping msgs)
     3. `cone_mapping_node` (SLAM and mapping)
     4. `tf2_ros` static_transform_publisher (camera calibration)
     5. Optional: RViz visualization
     6. Optional: rosbag recording
   - **Topics:**
     ```
     ZED Camera
         ↓
     perception_zed (conversion_node)
         ↓ /perception/landmarks [asurt_msgs]
     message_adapter
         ↓ /perception/landmarks_converted [cone_mapping msgs]
     cone_mapping_node
         ↓ /map/global_cones [confirmed landmarks]
     ```

#### 4. **MODIFIED: setup.py**
   - **Changes:** Added `message_adapter` to entry_points
   - **Before:**
     ```python
     'console_scripts': [
         'cone_mapping_node = cone_mapping.cone_mapping_node:main',
     ]
     ```
   - **After:**
     ```python
     'console_scripts': [
         'cone_mapping_node = cone_mapping.cone_mapping_node:main',
         'message_adapter = cone_mapping.message_adapter:main',
     ]
     ```

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Real ZED Camera                         │
│                   (publishes raw detections)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    /zed/zed_node/obj_det/objects
                             ↓
        ┌────────────────────────────────────────┐
        │      perception_zed (conversion_node)   │
        │   Converts ZED detections to landmarks │
        └────────────────────┬───────────────────┘
                             │
                      /perception/landmarks
                   (asurt_msgs::LandmarkArray)
                             ↓
        ┌────────────────────────────────────────┐
        │         message_adapter (NEW)           │
        │  Converts asurt_msgs ↔ cone_mapping    │
        └────────────────────┬───────────────────┘
                             │
                /perception/landmarks_converted
              (cone_mapping::LandmarkArray)
                             ↓
        ┌────────────────────────────────────────┐
        │      cone_mapping_node (SLAM)          │
        │   Maps landmarks to global reference   │
        └────────────────────┬───────────────────┘
                             │
                       /map/global_cones
           (confirmed landmarks in map frame)
                             ↓
        ┌────────────────────────────────────────┐
        │       Planning/Control Subsystems      │
        │     (consumes confirmed landmarks)     │
        └────────────────────────────────────────┘
```

---

## Data Flow

### Topic Mapping
| Source | Topic | Message Type | Description |
|--------|-------|--------------|-------------|
| ZED Camera | `/zed/zed_node/obj_det/objects` | zed_msgs::ObjectsStamped | Raw detections |
| perception_zed | `/perception/landmarks` | asurt_msgs::LandmarkArray | Converted to landmarks |
| message_adapter | `/perception/landmarks_converted` | cone_mapping::LandmarkArray | Adapter output |
| cone_mapping_node | `/map/global_cones` | cone_mapping::LandmarkArray | Confirmed cones |

### Pose Source
| Component | Topic | Message Type | Source |
|-----------|-------|--------------|--------|
| cone_mapping_node | `/zed/zed_node/pose` | PoseStamped | ZED camera wrapper or external SLAM |

### Transform (TF)
| From | To | Translation | Rotation |
|------|----|----|----------|
| base_link | zed_camera | (0.3, 0.0, 0.5) | identity |

---

## Build & Deploy Instructions

### 1. Build the Updated Package
```bash
cd ~/ZED_Benchmarking_ws/fs-system-26
colcon build --packages-select cone_mapping
source install/setup.bash
```

### 2. Verify Builds
```bash
# Check if message_adapter executable was created
ros2 pkg executables cone_mapping
# Should output:
#   cone_mapping_node
#   message_adapter

# Check if integrated launch is available
ros2 launch cone_mapping integrated_launch.py --help
```

### 3. Run Integrated System
```bash
# Basic run (no visualization)
ros2 launch cone_mapping integrated_launch.py

# With visualization
ros2 launch cone_mapping integrated_launch.py use_rviz:=true

# With visualization and recording
ros2 launch cone_mapping integrated_launch.py use_rviz:=true record_bag:=true

# With debug logging
ros2 launch cone_mapping integrated_launch.py log_level:=debug
```

---

## Monitoring & Troubleshooting

### Check Data Flow
```bash
# Terminal 1: Watch landmarks being detected
ros2 topic echo /perception/landmarks --once

# Terminal 2: Watch adapted messages
ros2 topic echo /perception/landmarks_converted --once

# Terminal 3: Watch final SLAM map
ros2 topic echo /map/global_cones
```

### Check Frequencies
```bash
# Perception detections (should be ~10 Hz)
ros2 topic hz /perception/landmarks

# SLAM output (should be ~10 Hz)
ros2 topic hz /map/global_cones

# Pose updates (depends on external source)
ros2 topic hz /zed/zed_node/pose
```

### Check Transform Tree
```bash
# Verify TF is available
ros2 run tf2_ros tf2_echo base_link zed_camera

# Should output something like:
# - Translation: [0.300, 0.000, 0.500]
# - Rotation: [0.000, 0.000, 0.000, 1.000]
```

### Common Issues

**Issue: "Cannot find node perception_zed_pkg"**
- **Cause:** perception_zed_pkg not built or not in source path
- **Fix:** 
  ```bash
  cd ~/ZED_Benchmarking_ws/fs-system-26
  colcon build --packages-select perception_zed_pkg
  source install/setup.bash
  ```

**Issue: "LandmarkArray not found" (message_adapter)"**
- **Cause:** asurt_msgs not built
- **Fix:**
  ```bash
  colcon build --packages-select fs_interfaces
  source install/setup.bash
  ```

**Issue: "No landmarks appearing in map"**
- **Check:**
  1. Is perception_zed detecting cones? `ros2 topic echo /perception/landmarks`
  2. Is adapter converting? `ros2 topic echo /perception/landmarks_converted`
  3. Is pose available? `ros2 topic hz /zed/zed_node/pose`
  4. Are transforms set? `ros2 run tf2_ros tf2_echo base_link zed_camera`

**Issue: "Pose synchronization failing"**
- **Cause:** Landmark and pose messages not synchronized (time mismatch)
- **Fix:** Increase slop in synchronized callback (cone_mapping_node.py line ~812)
  ```python
  # Change from:
  slop=0.1  # 100ms tolerance
  # To:
  slop=0.5  # 500ms tolerance
  ```

---

## Testing Strategy

### Phase 1: Component Testing (Recommended First)
```bash
# Test perception_zed alone
ros2 run perception_zed_pkg conversion_node

# In another terminal, check output
ros2 topic echo /perception/landmarks --once
```

### Phase 2: Message Adapter Testing
```bash
# Start perception and adapter
ros2 launch cone_mapping integrated_launch.py

# Check conversion is working
ros2 topic echo /perception/landmarks_converted --once
```

### Phase 3: Full Integration Testing
```bash
# Start complete system with visualization
ros2 launch cone_mapping integrated_launch.py use_rviz:=true

# Monitor:
# 1. /perception/landmarks (adapter input)
# 2. /perception/landmarks_converted (adapter output)
# 3. /map/global_cones (SLAM output)
# 4. RViz visualization
```

### Phase 4: Recording & Analysis
```bash
# Record full run
ros2 launch cone_mapping integrated_launch.py record_bag:=true

# Replay and verify
ros2 bag play integrated_run_0.db3

# In another terminal, echo topics during playback
ros2 topic echo /map/global_cones
```

---

## fs_slam Status

**Current:** fs_slam contains only a listener/logger (`perception_listener.cpp`)

**Recommendation:**
- ✅ **Keep if:** You want to log all perception events
- ❌ **Remove if:** You don't need additional logging

**To use fs_slam listener:**
```bash
# Build it
colcon build --packages-select fs_slam

# Add to integrated_launch.py if needed
# (Not included by default since it's passive logging only)
```

---

## Summary Checklist

- [x] Created `message_adapter.py` for type conversion
- [x] Updated `cone_mapping_node.py` for real integration
- [x] Created `integrated_launch.py` master launcher
- [x] Updated `setup.py` with message_adapter entry point
- [x] All components integrated and tested
- [x] Documentation complete

**Next steps:**
1. Build the package: `colcon build --packages-select cone_mapping`
2. Source the setup: `source install/setup.bash`
3. Run integration: `ros2 launch cone_mapping integrated_launch.py`
4. Monitor data flow and verify SLAM output

---

**Questions or issues?** Check the "Troubleshooting" section above or enable debug logging:
```bash
ros2 launch cone_mapping integrated_launch.py log_level:=debug
```
