import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
import os
import sys
from collections import defaultdict
from datetime import datetime

# Set seaborn style for better-looking plots
sns.set_style("whitegrid")
sns.set_palette("husl")

# Set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)


file_path = sys.argv[1]
print("File path:", file_path)

def create_results_folder(log_file_path):
    """
    Create a results folder structure for the log file
    """
    # Extract log file name without extension
    log_file_name = os.path.basename(log_file_path)
    log_file_base = os.path.splitext(log_file_name)[0]
    
    # Create main results folder if it doesn't exist
    results_root = "./Results"
    os.makedirs(results_root, exist_ok=True)
    
    # Create folder for this specific log file
    log_results_folder = os.path.join(results_root, log_file_base)
    os.makedirs(log_results_folder, exist_ok=True)

    return log_file_base

## 1. Parsing the Camera Output YAML File
# Create results folder
test_log_name = create_results_folder(file_path)

# Use safe_load_all to load all YAML documents
with open(file_path, 'r') as file:
    camera_data_list = list(yaml.safe_load_all(file))

print(f"File loaded successfully")
print(f"Total documents loaded: {len(camera_data_list)}")


# Filter out empty/null documents
camera_data_list = [doc for doc in camera_data_list if doc is not None and 'header' in doc]
print(f"Valid documents after filtering: {len(camera_data_list)}")

i = 0
for data in camera_data_list:
    camera_data = data
    i += 1
    print(f"\n {i}. Document Frame ID: {camera_data['header']['frame_id']}")
    print(f"Document Timestamp: {camera_data['header']['stamp']['sec']}.{camera_data['header']['stamp']['nanosec']}")
    print(f"Total objects detected in this document: {len(camera_data['objects'])}")

## 2. Extraction of Blue and Yellow Labeled Objects

# Filter objects based on their label (blue or yellow)


i = 0
for data in camera_data_list:
    camera_data = data
    i += 1
    print(f"{i}. Camera Document")
    blue_objects = [obj for obj in camera_data['objects'] if obj.get('label') == 'blue']
    yellow_objects = [obj for obj in camera_data['objects'] if obj.get('label') == 'yellow']

    print(f"Blue objects found: {len(blue_objects)}")
    print(f"Yellow objects found: {len(yellow_objects)}")
    print(f"\nTotal colored objects: {len(blue_objects) + len(yellow_objects)}")

    all_labels = set(obj.get('label', 'NO_LABEL') for obj in camera_data['objects'])
    print(f"\nAll unique labels found: {all_labels}\n")
    print("=========================================================\n")




## 3. Displaying Detailed Info for Each Object (Blue or Yellow)

# Extract key information from each detected object

def extract_object_info(obj):
    """Extract relevant information from an object"""
    return {
        'Label': obj['label'],
        'Label_ID': obj['label_id'],
        'Sublabel': obj['sublabel'],
        'Confidence (%)': round(obj['confidence'], 2),
        'Position_X': round(obj['position'][0], 4),
        'Position_Y': round(obj['position'][1], 4),
        'Position_Z': round(obj['position'][2], 4),
        'Velocity_X': round(obj['velocity'][0], 4),
        'Velocity_Y': round(obj['velocity'][1], 4),
        'Velocity_Z': round(obj['velocity'][2], 4),
        'Width_3D': round(obj['dimensions_3d'][0], 4),
        'Height_3D': round(obj['dimensions_3d'][1], 4),
        'Depth_3D': round(obj['dimensions_3d'][2], 4),
        'Tracking_State': obj['tracking_state'],
        'Action_State': obj['action_state']
    }

all_colored_objects = blue_objects + yellow_objects
object_data = [extract_object_info(obj) for obj in all_colored_objects]
df = pd.DataFrame(object_data)

print("="*80)
print("DETECTED OBJECTS SUMMARY")
print("="*80)
print(df)

### Detailed Analysis by Color

print("="*80)
print("BLUE OBJECTS ANALYSIS")
print("="*80)

for i, obj in enumerate(blue_objects, 1):
    print(f"\n[Blue Object #{i}]")
    print(f"  Label ID: {obj['label_id']}")
    print(f"  Confidence: {obj['confidence']:.2f}%")
    print(f"  Position: X={obj['position'][0]:.4f}, Y={obj['position'][1]:.4f}, Z={obj['position'][2]:.4f}")
    print(f"  Velocity: X={obj['velocity'][0]:.4f}, Y={obj['velocity'][1]:.4f}, Z={obj['velocity'][2]:.4f}")
    print(f"  Dimensions (WxHxD): {obj['dimensions_3d'][0]:.4f} × {obj['dimensions_3d'][1]:.4f} × {obj['dimensions_3d'][2]:.4f}")
    print(f"  Tracking: {'Active' if obj['tracking_available'] else 'Inactive'}")


print("="*80)
print("YELLOW OBJECTS ANALYSIS")
print("="*80)

for i, obj in enumerate(yellow_objects, 1):
    print(f"\n[Yellow Object #{i}]")
    print(f"  Label ID: {obj['label_id']}")
    print(f"  Confidence: {obj['confidence']:.2f}%")
    print(f"  Position: X={obj['position'][0]:.4f}, Y={obj['position'][1]:.4f}, Z={obj['position'][2]:.4f}")
    print(f"  Velocity: X={obj['velocity'][0]:.4f}, Y={obj['velocity'][1]:.4f}, Z={obj['velocity'][2]:.4f}")
    print(f"  Dimensions (WxHxD): {obj['dimensions_3d'][0]:.4f} × {obj['dimensions_3d'][1]:.4f} × {obj['dimensions_3d'][2]:.4f}")
    print(f"  Tracking: {'Active' if obj['tracking_available'] else 'Inactive'}")

# ## 4. Visualized 2D Bounding Boxes

# Assume camera resolution (adjust based on your camera)
img_width, img_height = 1920, 1080

fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, img_width)
ax.set_ylim(img_height, 0)  # Invert Y axis for image coordinates
ax.set_aspect('equal')
ax.set_title('2D Bounding Boxes (Camera View)', fontsize=16, fontweight='bold')
ax.set_xlabel('X (pixels)', fontsize=12)
ax.set_ylabel('Y (pixels)', fontsize=12)

# Draw blue objects
for obj in blue_objects:
    corners = obj['bounding_box_2d']['corners']
    x_coords = [c['kp'][0] for c in corners] + [corners[0]['kp'][0]]
    y_coords = [c['kp'][1] for c in corners] + [corners[0]['kp'][1]]
    ax.plot(x_coords, y_coords, 'b-', linewidth=2, label='Blue' if obj == blue_objects[0] else '')
    # Add label
    center_x = np.mean([c['kp'][0] for c in corners])
    center_y = np.mean([c['kp'][1] for c in corners])
    ax.text(center_x, center_y, f"Blue\n{obj['confidence']:.1f}%", 
            ha='center', va='center', color='blue', fontweight='bold', fontsize=10)

# Draw yellow objects
for obj in yellow_objects:
    corners = obj['bounding_box_2d']['corners']
    x_coords = [c['kp'][0] for c in corners] + [corners[0]['kp'][0]]
    y_coords = [c['kp'][1] for c in corners] + [corners[0]['kp'][1]]
    ax.plot(x_coords, y_coords, color='gold', linewidth=2, label='Yellow' if obj == yellow_objects[0] else '')
    # Add label
    center_x = np.mean([c['kp'][0] for c in corners])
    center_y = np.mean([c['kp'][1] for c in corners])
    ax.text(center_x, center_y, f"Yellow\n{obj['confidence']:.1f}%", 
            ha='center', va='center', color='orange', fontweight='bold', fontsize=10)

ax.legend(fontsize=12)
ax.grid(True, alpha=0.3)
plt.tight_layout()


plt.savefig(os.path.join(f'./Results/{test_log_name}', f'2D_bounding_boxes_{test_log_name}.png'), 
                dpi=150, bbox_inches='tight')

plt.show()

# ## 5. Visualized 3D Positions

fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, projection='3d', proj_type='persp')

# Explicitly use Axes3D for 3D plotting
# Plot blue objects
for obj in blue_objects:
    pos = obj['position']
    dims = obj['dimensions_3d']
    ax.scatter(pos[0], pos[1], pos[2], c='blue', s=500, marker='o', alpha=0.6, edgecolors='darkblue', linewidth=2)
    ax.text(pos[0], pos[1], pos[2], f"  Blue\n  {obj['confidence']:.1f}%", color='blue', fontweight='bold')

# Plot yellow objects
for obj in yellow_objects:
    pos = obj['position']
    dims = obj['dimensions_3d']
    ax.scatter(pos[0], pos[1], pos[2], c='yellow', s=500, marker='o', alpha=0.6, edgecolors='orange', linewidth=2)
    ax.text(pos[0], pos[1], pos[2], f"  Yellow\n  {obj['confidence']:.1f}%", color='orange', fontweight='bold')

# Plot camera at origin
ax.scatter(0, 0, 0, c='red', s=200, marker='^', label='Camera')

ax.set_xlabel('X (meters)', fontsize=12, fontweight='bold')
ax.set_ylabel('Y (meters)', fontsize=12, fontweight='bold')
ax.set_zlabel('Z (meters)', fontsize=12, fontweight='bold')
ax.set_title('3D Object Positions Relative to Camera', fontsize=16, fontweight='bold', pad=20)
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig(os.path.join(f'./Results/{test_log_name}', f'3D_bounding_boxes_{test_log_name}.png'), 
                dpi=150, bbox_inches='tight')

plt.show()

# ## 6. Providing Statistical Comparisons

comparison = df.groupby('Label').agg({
    'Confidence (%)': ['mean', 'min', 'max'],
    'Position_X': 'mean',
    'Position_Y': 'mean',
    'Position_Z': 'mean',
    'Velocity_X': 'mean',
    'Velocity_Y': 'mean',
    'Velocity_Z': 'mean',
    'Width_3D': 'mean',
    'Height_3D': 'mean',
    'Depth_3D': 'mean'
}).round(4)

print("="*80)
print("COMPARATIVE STATISTICS: BLUE vs YELLOW")
print("="*80)
print(comparison)

# ## 7. Creating Comprehensive Comparisons Dashboard

# ### Dashboard Statistical Visualization with Seaborn

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Object Detection Dashboard - Basic Metrics', fontsize=18, fontweight='bold', y=0.995)

# Confidence scores
ax1 = axes[0, 0]
colors = ['blue' if label == 'blue' else 'gold' for label in df['Label']]
ax1.bar(range(len(df)), df['Confidence (%)'], color=colors, alpha=0.7, edgecolor='black')
ax1.set_xlabel('Object Index', fontweight='bold')
ax1.set_ylabel('Confidence (%)', fontweight='bold')
ax1.set_title('Detection Confidence by Object', fontweight='bold')
ax1.grid(True, alpha=0.3, axis='y')

# Position distribution
ax2 = axes[0, 1]
for label, color in [('blue', 'blue'), ('yellow', 'gold')]:
    subset = df[df['Label'] == label]
    ax2.scatter(subset['Position_X'], subset['Position_Y'], 
                s=300, c=color, alpha=0.6, edgecolors='black', linewidth=2, label=label.capitalize())
ax2.set_xlabel('X Position (m)', fontweight='bold')
ax2.set_ylabel('Y Position (m)', fontweight='bold')
ax2.set_title('Object Positions (Top View)', fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.axhline(y=0, color='red', linestyle='--', alpha=0.5, label='Camera')
ax2.axvline(x=0, color='red', linestyle='--', alpha=0.5)

# Velocity comparison
ax3 = axes[1, 0]
velocities = np.sqrt(df['Velocity_X']**2 + df['Velocity_Y']**2 + df['Velocity_Z']**2)
colors = ['blue' if label == 'blue' else 'gold' for label in df['Label']]
ax3.bar(range(len(df)), velocities, color=colors, alpha=0.7, edgecolor='black')
ax3.set_xlabel('Object Index', fontweight='bold')
ax3.set_ylabel('Speed (m/s)', fontweight='bold')
ax3.set_title('Object Speed (Magnitude)', fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')

# Size comparison
ax4 = axes[1, 1]
volumes = df['Width_3D'] * df['Height_3D'] * df['Depth_3D']
colors = ['blue' if label == 'blue' else 'gold' for label in df['Label']]
ax4.bar(range(len(df)), volumes, color=colors, alpha=0.7, edgecolor='black')
ax4.set_xlabel('Object Index', fontweight='bold')
ax4.set_ylabel('Volume (m³)', fontweight='bold')
ax4.set_title('Object Volume', fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()

plt.savefig(os.path.join(f'./Results/{test_log_name}', f'Object_Detection_Dashboard_{test_log_name}.png'), 
                dpi=150, bbox_inches='tight')

plt.show()


# ## 8. Exporting the Data to CSV Files

output_file = f'./Results/{test_log_name}/parsed_camera_objects_{test_log_name}.csv'
df.to_csv(output_file, index=False)
print(f"Data exported to: {output_file}")

df[df['Label'] == 'blue'].to_csv('./Results/blue_objects.csv', index=False)
df[df['Label'] == 'yellow'].to_csv('./Results/yellow_objects.csv', index=False)
print(f"Blue objects exported to: blue_objects.csv")
print(f"Yellow objects exported to: yellow_objects.csv")

# ## 9. Tracking Objects across frames


# Set seaborn style
sns.set_style("whitegrid")
sns.set_palette("husl")


with open(file_path, 'r') as file:
    camera_data_list = [doc for doc in yaml.safe_load_all(file) 
                       if doc is not None and 'header' in doc]

print(f"Total frames loaded: {len(camera_data_list)}")
print(f"First frame timestamp: {camera_data_list[0]['header']['stamp']['sec']}")
print(f"Last frame timestamp: {camera_data_list[-1]['header']['stamp']['sec']}")

# Using timestamps to find an estimate for this setup's inference time
# Calculate time differences between consecutive frames
time_diffs = []
timestamps_sec = []  # Full timestamps in seconds
timestamps_ns = []   # Just for reference

for i in range(1, len(camera_data_list)):
    # Get current frame timestamp in seconds (including nanoseconds)
    current_sec = camera_data_list[i]['header']['stamp']['sec']
    current_nsec = camera_data_list[i]['header']['stamp']['nanosec']
    current_time = current_sec + current_nsec / 1e9
    
    # Get previous frame timestamp
    prev_sec = camera_data_list[i-1]['header']['stamp']['sec']
    prev_nsec = camera_data_list[i-1]['header']['stamp']['nanosec']
    prev_time = prev_sec + prev_nsec / 1e9
    
    # Calculate difference in seconds
    time_diff = current_time - prev_time
    time_diffs.append(time_diff)
    
    # Store for reference
    timestamps_sec.append(current_time)
    timestamps_ns.append((current_sec, current_nsec))

# Also store the first timestamp for completeness
if camera_data_list:
    first_sec = camera_data_list[0]['header']['stamp']['sec']
    first_nsec = camera_data_list[0]['header']['stamp']['nanosec']
    timestamps_sec.insert(0, first_sec + first_nsec / 1e9)
    timestamps_ns.insert(0, (first_sec, first_nsec))

# Calculate statistics
if time_diffs:
    time_diffs_ms = np.array(time_diffs) * 1000  # Convert to milliseconds
    
    print("\n" + "="*80)
    print("INFERENCE TIME ANALYSIS")
    print("="*80)
    print(f"Total frames analyzed: {len(camera_data_list)}")
    print(f"Time intervals analyzed: {len(time_diffs)}")
    print(f"Total duration: {(timestamps_sec[-1] - timestamps_sec[0]):.4f} seconds")
    print(f"Average frame interval: {np.mean(time_diffs):.6f} seconds")
    print(f"Average frame interval: {np.mean(time_diffs_ms):.2f} ms")
    print(f"Standard deviation: {np.std(time_diffs_ms):.2f} ms")
    print(f"Minimum interval: {np.min(time_diffs_ms):.2f} ms")
    print(f"Maximum interval: {np.max(time_diffs_ms):.2f} ms")
    print(f"Median interval: {np.median(time_diffs_ms):.2f} ms")
    
    # Calculate FPS (Frames Per Second)
    avg_interval_seconds = np.mean(time_diffs)
    fps = 1.0 / avg_interval_seconds if avg_interval_seconds > 0 else 0
    print(f"Estimated FPS: {fps:.2f}")
    

# Track objects across frames
object_tracking = defaultdict(list)

for frame_idx, frame_data in enumerate(camera_data_list):
    timestamp = frame_data['header']['stamp']['sec'] + frame_data['header']['stamp']['nanosec'] / 1e9
    
    for obj in frame_data.get('objects', []):
        obj_id = obj.get('label_id')
        if obj_id is not None:
            object_tracking[obj_id].append({
                'frame_idx': frame_idx,
                'timestamp': timestamp,
                'label': obj.get('label', 'unknown'),
                'confidence': obj.get('confidence', 0),
                'position_x': obj.get('position', [0, 0, 0])[0],
                'position_y': obj.get('position', [0, 0, 0])[1],
                'position_z': obj.get('position', [0, 0, 0])[2],
                'distance': np.sqrt(sum([coord**2 for coord in obj.get('position', [0, 0, 0])])),
                'velocity_x': obj.get('velocity', [0, 0, 0])[0],
                'velocity_y': obj.get('velocity', [0, 0, 0])[1],
                'velocity_z': obj.get('velocity', [0, 0, 0])[2],
                'width': obj.get('dimensions_3d', [0, 0, 0])[0],
                'height': obj.get('dimensions_3d', [0, 0, 0])[1],
                'depth': obj.get('dimensions_3d', [0, 0, 0])[2],
                'tracking_state': obj.get('tracking_state', 0),
                'action_state': obj.get('action_state', ''),
                'frame_id': frame_data['header']['frame_id']
            })

print(f"\nTotal unique objects detected: {len(object_tracking)}")

# Create comprehensive analysis
analysis_results = []

for obj_id, detections in object_tracking.items():
    if len(detections) > 0:
        df_obj = pd.DataFrame(detections)
        
        # Basic statistics
        analysis_results.append({
            'object_id': obj_id,
            'label': detections[0]['label'],
            'total_detections': len(detections),
            'detection_frames': f"{detections[0]['frame_idx']} to {detections[-1]['frame_idx']}",
            'avg_confidence': df_obj['confidence'].mean(),
            'confidence_std': df_obj['confidence'].std(),
            'min_confidence': df_obj['confidence'].min(),
            'max_confidence': df_obj['confidence'].max(),
            'avg_distance': df_obj['distance'].mean(),
            'distance_std': df_obj['distance'].std(),
            'min_distance': df_obj['distance'].min(),
            'max_distance': df_obj['distance'].max(),
            'avg_width': df_obj['width'].mean(),
            'width_std': df_obj['width'].std(),
            'avg_height': df_obj['height'].mean(),
            'height_std': df_obj['height'].std(),
            'avg_depth': df_obj['depth'].mean(),
            'depth_std': df_obj['depth'].std(),
            'tracking_consistency': df_obj['tracking_state'].mean(),  # 1 = consistently tracked
            'detection_rate': len(detections) / len(camera_data_list),  # Percentage of frames detected
            'first_frame': detections[0]['frame_idx'],
            'last_frame': detections[-1]['frame_idx']
        })

# Create analysis DataFrame
analysis_df = pd.DataFrame(analysis_results)
analysis_df = analysis_df.sort_values('total_detections', ascending=False)

print("\n" + "="*80)
print("OBJECT TRACKING ANALYSIS SUMMARY")
print("="*80)
print(f"Total frames analyzed: {len(camera_data_list)}")
print(f"Total unique objects: {len(object_tracking)}")
print(f"Objects by label:")
print(analysis_df['label'].value_counts())

print("\nTop 10 most consistently detected objects:")
print(analysis_df[['object_id', 'label', 'total_detections', 'detection_rate', 
                  'avg_confidence', 'avg_distance']])

# 1. Object detection consistency over frames
plt.figure(figsize=(14, 8))

# Create a matrix of object presence across frames
object_ids = list(object_tracking.keys())
frame_range = range(len(camera_data_list))

# Create presence matrix
presence_matrix = np.zeros((len(object_ids), len(frame_range)))

for i, obj_id in enumerate(object_ids):
    frames_with_obj = [det['frame_idx'] for det in object_tracking[obj_id]]
    for frame in frames_with_obj:
        if frame < len(frame_range):
            presence_matrix[i, frame] = 1

# 1. Distance vs Confidence scatter
plt.subplot(2, 2, 3)
for obj_id, detections in list(object_tracking.items())[:50]:  # Limit to first 50 for clarity
    df_obj = pd.DataFrame(detections)
    if not df_obj.empty:
        label = detections[0]['label']
        color = 'blue' if label == 'blue' else 'gold' if label == 'yellow' else 'gray'
        plt.scatter(df_obj['distance'].mean(), df_obj['confidence'].mean(), 
                   c=color, alpha=0.6, s=100, edgecolors='black')
plt.xlabel('Average Distance (m)')
plt.ylabel('Average Confidence (%)')
plt.title('Object Distance vs Confidence')
plt.grid(True, alpha=0.3)

# 2. Temporal tracking of top objects
plt.subplot(2, 2, 4)
top_objects = analysis_df.head(5)['object_id'].tolist()
for obj_id in top_objects:
    detections = object_tracking[obj_id]
    df_obj = pd.DataFrame(detections)
    if not df_obj.empty:
        label = detections[0]['label']
        color = 'blue' if label == 'blue' else 'gold'
        plt.plot(df_obj['frame_idx'], df_obj['confidence'], 
                color=color, marker='o', linewidth=2, markersize=4, 
                label=f"ID {obj_id} ({label})")
plt.xlabel('Frame Index')
plt.ylabel('Confidence (%)')
plt.title('Confidence Over Time (Top 5 Objects)')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()


plt.savefig(os.path.join(f'./Results/{test_log_name}', f'Object_tracking_plots_{test_log_name}.png'), 
                dpi=150, bbox_inches='tight')

plt.show()

# Function to create detailed report for a specific object
def create_object_report(obj_id):
    if obj_id not in object_tracking:
        print(f"Object ID {obj_id} not found!")
        return
    
    detections = object_tracking[obj_id]
    df_obj = pd.DataFrame(detections)
    
    print(f"\n{'='*60}")
    print(f"DETAILED REPORT - Object ID: {obj_id}")
    print(f"{'='*60}")
    
    print(f"\nBasic Info:")
    print(f"  Label: {detections[0]['label']}")
    print(f"  Detected in: {len(detections)} frames")
    print(f"  First detection: Frame {detections[0]['frame_idx']}")
    print(f"  Last detection: Frame {detections[-1]['frame_idx']}")
    print(f"  Detection rate: {(len(detections)/len(camera_data_list))*100:.1f}% of frames")
    
    print(f"\nConfidence Analysis:")
    print(f"  Average: {df_obj['confidence'].mean():.2f}%")
    print(f"  Std Dev: {df_obj['confidence'].std():.2f}")
    print(f"  Range: {df_obj['confidence'].min():.2f}% - {df_obj['confidence'].max():.2f}%")
    
    print(f"\nDistance Analysis:")
    print(f"  Average distance: {df_obj['distance'].mean():.2f} m")
    print(f"  Std Dev: {df_obj['distance'].std():.2f} m")
    print(f"  Closest: {df_obj['distance'].min():.2f} m")
    print(f"  Farthest: {df_obj['distance'].max():.2f} m")
    
    print(f"\nPosition Stability (standard deviation):")
    print(f"  X: {df_obj['position_x'].std():.3f} m")
    print(f"  Y: {df_obj['position_y'].std():.3f} m")
    print(f"  Z: {df_obj['position_z'].std():.3f} m")
    
    print(f"\nDimensions (average):")
    print(f"  Width: {df_obj['width'].mean():.3f} m")
    print(f"  Height: {df_obj['height'].mean():.3f} m")
    print(f"  Depth: {df_obj['depth'].mean():.3f} m")
    

# Example: Create report for the most consistently detected object
if len(analysis_df) > 0:
    most_consistent_id = analysis_df.iloc[0]['object_id']
    create_object_report(most_consistent_id)

# Save comprehensive analysis to CSV
analysis_df.to_csv(f'./Results/{test_log_name}/object_tracking_analysis_{test_log_name}.csv', index=False)
print(f"\nAnalysis saved to 'object_tracking_analysis.csv'")

# Save raw tracking data for each object
# for obj_id, detections in object_tracking.items():
#     if len(detections) > 0:
#         df_obj = pd.DataFrame(detections)
#         filename = f"object_{obj_id}_tracking.csv"
#         df_obj.to_csv(filename, index=False)
# 
# print(f"Individual object tracking data saved to CSV files")

# Create summary report
with open( f'./Results/{test_log_name}/tracking_summary_{test_log_name}.txt', 'w') as f:
    f.write("="*60 + "\n")
    f.write("OBJECT DETECTION TRACKING SUMMARY\n")
    f.write("="*60 + "\n\n")
    f.write(f"Total frames analyzed: {len(camera_data_list)}\n")
    f.write(f"Total unique objects detected: {len(object_tracking)}\n")
    f.write(f"Analysis timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    f.write("Objects by label:\n")
    for label, count in analysis_df['label'].value_counts().items():
        f.write(f"  {label}: {count} objects\n")
    
    f.write("\nMost consistently detected objects:\n")
    for i, row in analysis_df.head(10).iterrows():
        f.write(f"{i+1:2d}. ID {row['object_id']} ({row['label']}): "
                f"{row['total_detections']} detections, "
                f"{row['detection_rate']*100:.1f}% detection rate, "
                f"Avg confidence: {row['avg_confidence']:.1f}%, "
                f"Avg distance: {row['avg_distance']:.1f}m\n")
    
    f.write("\nDetection statistics:\n")
    f.write(f"  Average detections per object: {analysis_df['total_detections'].mean():.1f}\n")
    f.write(f"  Median detections per object: {analysis_df['total_detections'].median():.1f}\n")
    f.write(f"  Max detections: {analysis_df['total_detections'].max()}\n")
    f.write(f"  Min detections: {analysis_df['total_detections'].min()}\n")

    f.write("\n" + "="*80)
    f.write("\nINFERENCE TIME ANALYSIS\n")
    f.write("="*80)
    f.write(f"\nTotal frames analyzed: {len(camera_data_list)}")
    f.write(f"\nTime intervals analyzed: {len(time_diffs)}")
    f.write(f"\nTotal duration: {(timestamps_sec[-1] - timestamps_sec[0]):.4f} seconds")
    f.write(f"\nAverage frame interval: {np.mean(time_diffs):.6f} seconds")
    f.write(f"\nAverage frame interval: {np.mean(time_diffs_ms):.2f} ms")
    f.write(f"\nStandard deviation: {np.std(time_diffs_ms):.2f} ms")
    f.write(f"\nMinimum interval: {np.min(time_diffs_ms):.2f} ms")
    f.write(f"\nMaximum interval: {np.max(time_diffs_ms):.2f} ms")
    f.write(f"\nMedian interval: {np.median(time_diffs_ms):.2f} ms")
    f.write(f"\nEstimated FPS: {fps:.2f}")
    
print(f"Summary report saved to 'tracking_summary.txt'")


