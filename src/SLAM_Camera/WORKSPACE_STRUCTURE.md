# Complete Workspace Structure

## Directory Layout

```
~/formula_student_ws/
└── src/
    └── cone_mapping/
        ├── CMakeLists.txt
        ├── package.xml (use package_corrected.xml)
        ├── setup.py
        ├── resource/
        │   └── cone_mapping
        ├── msg/
        │   ├── Landmark.msg
        │   └── LandmarkArray.msg
        ├── cone_mapping/
        │   ├── __init__.py
        │   ├── cone_mapping_node.py
        │   ├── perception_simulator_base.py
        │   ├── test_case_1_ideal.py
        │   ├── test_case_2_noisy.py
        │   ├── test_case_3_loop_closure.py
        │   ├── test_case_4_edge_cases.py
        │   └── test_case_5_multilap.py
        ├── launch/
        │   ├── cone_mapping_launch.py
        │   └── test_launch.py
        ├── config/
        │   └── cone_mapping_params.yaml
        ├── test/
        │   └── test_cone_mapping.py
        └── docs/
            ├── README.md
            ├── QUICKSTART.md
            ├── TESTING_GUIDE.md
            └── VALIDATION_CHECKLIST.md
```

## Setup Instructions

### Step 1: Create Workspace Structure

```bash
# Create workspace
mkdir -p ~/formula_student_ws/src
cd ~/formula_student_ws/src

# Create package structure
mkdir -p cone_mapping/{msg,cone_mapping,launch,config,test,docs,resource}

# Create __init__.py
touch cone_mapping/cone_mapping/__init__.py

# Create resource file (empty)
touch cone_mapping/resource/cone_mapping
```

### Step 2: Copy Files

Copy all provided files to their respective locations:

**Root files:**
- `CMakeLists.txt` → `cone_mapping/CMakeLists.txt`
- `package_corrected.xml` → `cone_mapping/package.xml` (rename!)
- `setup.py` → `cone_mapping/setup.py`

**Message files:**
- `Landmark.msg` → `cone_mapping/msg/Landmark.msg`
- `LandmarkArray.msg` → `cone_mapping/msg/LandmarkArray.msg`

**Python modules:**
- `cone_mapping_node.py` → `cone_mapping/cone_mapping/cone_mapping_node.py`
- `perception_simulator_base.py` → `cone_mapping/cone_mapping/perception_simulator_base.py`
- `test_case_1_ideal.py` → `cone_mapping/cone_mapping/test_case_1_ideal.py`
- `test_case_2_noisy.py` → `cone_mapping/cone_mapping/test_case_2_noisy.py`
- `test_case_3_loop_closure.py` → `cone_mapping/cone_mapping/test_case_3_loop_closure.py`
- `test_case_4_edge_cases.py` → `cone_mapping/cone_mapping/test_case_4_edge_cases.py`
- `test_case_5_multilap.py` → `cone_mapping/cone_mapping/test_case_5_multilap.py`

**Launch files:**
- `cone_mapping_launch.py` → `cone_mapping/launch/cone_mapping_launch.py`
- `test_launch.py` → `cone_mapping/launch/test_launch.py`

**Config files:**
- `cone_mapping_params.yaml` → `cone_mapping/config/cone_mapping_params.yaml`

**Test files:**
- `test_cone_mapping.py` → `cone_mapping/test/test_cone_mapping.py`

**Documentation:**
- `README.md` → `cone_mapping/docs/README.md`
- `QUICKSTART.md` → `cone_mapping/docs/QUICKSTART.md`
- `TESTING_GUIDE.md` → `cone_mapping/docs/TESTING_GUIDE.md`
- `VALIDATION_CHECKLIST.md` → `cone_mapping/docs/VALIDATION_CHECKLIST.md`

### Step 3: Make Python Files Executable

```bash
cd ~/formula_student_ws/src/cone_mapping
chmod +x cone_mapping/*.py
```

### Step 4: Build Package

```bash
cd ~/formula_student_ws
colcon build --packages-select cone_mapping
source install/setup.bash
```

### Step 5: Verify Installation

```bash
# Check messages
ros2 interface list | grep cone_mapping
# Should show:
#   cone_mapping/msg/Landmark
#   cone_mapping/msg/LandmarkArray

# Check nodes
ros2 pkg executables cone_mapping
# Should show:
#   cone_mapping cone_mapping_node
#   cone_mapping test_case_1_ideal
#   cone_mapping test_case_2_noisy
#   cone_mapping test_case_3_loop_closure
#   cone_mapping test_case_4_edge_cases
#   cone_mapping test_case_5_multilap
```

### Step 6: Run Tests

```bash
# Test Case 1: Ideal conditions
ros2 launch cone_mapping test_launch.py test_case:=ideal

# Test Case 2: Noisy detections
ros2 launch cone_mapping test_launch.py test_case:=noisy

# Test Case 3: Loop closure
ros2 launch cone_mapping test_launch.py test_case:=loop_closure

# Test Case 4: Edge cases
ros2 launch cone_mapping test_launch.py test_case:=edge_cases

# Test Case 5: Multi-lap
ros2 launch cone_mapping test_launch.py test_case:=multilap
```

## Message Format Details

### Landmark.msg
```
# Position in camera frame
geometry_msgs/Point position
  float64 x  # Forward
  float64 y  # Lateral
  float64 z  # Height

# Cone type/color
int32 type
  # 0 = Blue
  # 1 = Yellow
  # 2 = Orange
  # 3 = Unknown

# Tracking ID (unstable, ignored by mapper)
int32 identifier

# Detection confidence
float32 probability  # Range: [0.0, 1.0]
```

### LandmarkArray.msg
```
# Header with timestamp and frame
std_msgs/Header header
  builtin_interfaces/Time stamp
  string frame_id  # "zed_camera"

# Array of detected landmarks
Landmark[] landmarks
```

## Topic Interface

### Published by Simulators

| Topic | Type | Rate | Frame | Description |
|-------|------|------|-------|-------------|
| `/perception/landmarks` | `LandmarkArray` | 10 Hz | `zed_camera` | Cone detections |
| `/zed2i/zed_node/pose` | `PoseStamped` | 10 Hz | `map` | Vehicle pose |

### Published by Cone Mapping Node

| Topic | Type | Rate | Frame | Description |
|-------|------|------|-------|-------------|
| `/map/global_cones` | `LandmarkArray` | 10 Hz | `map` | Confirmed landmarks |

### TF Frames

```
map (SLAM global frame)
 └── base_link (vehicle body)
      └── zed_camera (sensor)
```

Static TF: `base_link` → `zed_camera`
- Translation: (0.3, 0.0, 0.5) meters
- Rotation: (0, 0, 0, 1) quaternion (aligned)

## Troubleshooting Build Issues

### Message generation fails

```bash
# Ensure rosidl is installed
sudo apt install ros-humble-rosidl-default-generators

# Clean and rebuild
cd ~/formula_student_ws
rm -rf build install log
colcon build --packages-select cone_mapping
```

### Python module not found

```bash
# Verify PYTHONPATH
echo $PYTHONPATH

# Re-source
source ~/formula_student_ws/install/setup.bash

# Check installation
python3 -c "from cone_mapping.msg import Landmark"
```

### Executable not found

```bash
# Check if installed
ls ~/formula_student_ws/install/cone_mapping/lib/cone_mapping/

# If missing, verify setup.py entry_points
# Rebuild
colcon build --packages-select cone_mapping --symlink-install
```

### TF not available

```bash
# Manually publish static TF
ros2 run tf2_ros static_transform_publisher \
  0.3 0.0 0.5 0 0 0 1 base_link zed_camera

# Or use launch file (preferred)
ros2 launch cone_mapping test_launch.py test_case:=ideal
```

## Next Steps

1. **Validate installation:** Run all 5 test cases
2. **Review documentation:** Read TESTING_GUIDE.md
3. **Tune parameters:** Adjust cone_mapping_params.yaml
4. **Integrate real sensors:** Replace simulators with ZED camera
5. **Competition ready:** Test on actual track

## File Checklist

Before building, verify you have all files:

**Required (17 files):**
- [ ] CMakeLists.txt
- [ ] package.xml
- [ ] setup.py
- [ ] msg/Landmark.msg
- [ ] msg/LandmarkArray.msg
- [ ] cone_mapping/__init__.py
- [ ] cone_mapping/cone_mapping_node.py
- [ ] cone_mapping/perception_simulator_base.py
- [ ] cone_mapping/test_case_1_ideal.py
- [ ] cone_mapping/test_case_2_noisy.py
- [ ] cone_mapping/test_case_3_loop_closure.py
- [ ] cone_mapping/test_case_4_edge_cases.py
- [ ] cone_mapping/test_case_5_multilap.py
- [ ] launch/cone_mapping_launch.py
- [ ] launch/test_launch.py
- [ ] config/cone_mapping_params.yaml
- [ ] resource/cone_mapping (empty file)

**Optional (5 files):**
- [ ] test/test_cone_mapping.py
- [ ] docs/README.md
- [ ] docs/QUICKSTART.md
- [ ] docs/TESTING_GUIDE.md
- [ ] docs/VALIDATION_CHECKLIST.md

All set! Ready to build and test! 🚀
