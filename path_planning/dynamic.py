import matplotlib.pyplot as plt
import numpy as np
from modules.planner import PathPlanner

# --- 1. CONFIGURATION ---
START_VISIBLE = 10
REVEAL_RATE = 4

# --- SELECT YOUR SHAPE HERE ---
# Options: 'straight', 's_curve', 'hairpin'
SHAPE_MODE = 's_curve'

# --- HELPER FUNCTIONS (Paste the functions from above here) ---
# (I will include the 'get_hairpin_path' and 'generate_cones_from_path' 
# inline for this runnable example)

def generate_cones_from_path(center_line_points, track_width=4.0):
    cones = []
    for i in range(len(center_line_points) - 1):
        p_curr = np.array(center_line_points[i])
        p_next = np.array(center_line_points[i+1])
        tangent = p_next - p_curr
        length = np.linalg.norm(tangent)
        if length == 0: continue
        tangent = tangent / length
        normal = np.array([-tangent[1], tangent[0]])
        
        b_pos = p_curr + normal * (track_width / 2.0)
        y_pos = p_curr - normal * (track_width / 2.0)
        cones.append((b_pos[0], b_pos[1], 'b'))
        cones.append((y_pos[0], y_pos[1], 'y'))
    return cones

def get_hairpin_path():
    points = []
    # Go straight
    for x in np.linspace(0, 20, 20): points.append((x, 0))
    # Turn 180 deg
    for t in np.linspace(-1.57, 1.57, 20):
        points.append((20 + 8*np.cos(t), 8 + 8*np.sin(t)))
    # Come back
    for x in np.linspace(20, 0, 20): points.append((x, 16))
    return points

def get_s_curve_path():
    return [(x, 5 * np.sin(x * 0.2)) for x in np.linspace(0, 50, 60)]

# --- 2. GENERATE TRACK ---
if SHAPE_MODE == 'hairpin':
    center_points = get_hairpin_path()
elif SHAPE_MODE == 's_curve':
    center_points = get_s_curve_path()
else:
    center_points = [(x, 0) for x in np.linspace(0, 50, 50)]

full_track_cones = generate_cones_from_path(center_points)

# --- 3. SIMULATION ---
planner = PathPlanner()
car_data = [(0.0, 0.0, 0.0)] # Start at 0,0

plt.ion()
fig, ax = plt.subplots(figsize=(10, 8))

for n in range(START_VISIBLE, len(full_track_cones) + 1, REVEAL_RATE):
    
    visible_cones = full_track_cones[:n]
    path_points = planner.execute_cycle(visible_cones, car_data)
    
    ax.clear()
    
    # Plot Cones
    xs = [c[0] for c in visible_cones]
    ys = [c[1] for c in visible_cones]
    cols = ['gold' if c[2] == 'y' else 'blue' for c in visible_cones]
    ax.scatter(xs, ys, c=cols, s=100, edgecolors='k')
    
    # Plot Path
    if path_points:
        px = [p[0] for p in path_points]
        py = [p[1] for p in path_points]
        ax.plot(px, py, '-g', linewidth=2)
        
    ax.set_xlim(-5, 35)
    ax.set_ylim(-10, 25) # Expanded view for hairpin
    ax.grid(True)
    plt.pause(0.1)

plt.ioff()
plt.show()