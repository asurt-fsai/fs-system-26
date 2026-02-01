import matplotlib.pyplot as plt
import numpy as np
from modules.planner import PathPlanner

# ==========================================
# 1. CONFIGURATION
# ==========================================
START_VISIBLE = 10
REVEAL_RATE = 4

# Options: 'straight', 's_curve', 'hairpin'
# FIXED: Changed 'jj' to 'hairpin' so you see a real track
SHAPE_MODE = 's_curve'

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def generate_cones_from_path(center_line_points, track_width=4.0, step=3):
    cones = []
    # The 'step' parameter controls density. 
    for i in range(0, len(center_line_points) - 1, step):
        p_curr = np.array(center_line_points[i])
        
        next_idx = min(i + step, len(center_line_points) - 1)
        if next_idx == i: break 
        
        p_next = np.array(center_line_points[next_idx])
        
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

# ==========================================
# 3. GENERATE TRACK
# ==========================================
if SHAPE_MODE == 'hairpin':
    center_points = get_hairpin_path()
elif SHAPE_MODE == 's_curve':
    center_points = get_s_curve_path()
else:
    center_points = [(x, 0) for x in np.linspace(0, 50, 50)]

full_track_cones = generate_cones_from_path(center_points)

# ==========================================
# 4. SIMULATION (THE FIX IS HERE)
# ==========================================

# FIX: Initialize with FS Rules specific parameters
# robot_radius=0.75 -> Represents a ~1.5m wide car (Half width)
# safety_margin=0.5 -> Keeps 0.5m away from cones
# max_edge_len=8.0  -> Allows connection even if cones are sparse (step=3)
planner = PathPlanner(robot_radius=0.75, safety_margin=0.5, max_edge_len=8.0)

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
        ax.plot(px, py, '-g', linewidth=3, label='Planned Path')
        ax.scatter(px, py, c='lime', s=20)
    else:
        # Debugging: Show text if no path found
        ax.text(0, 0, "NO PATH FOUND", fontsize=15, color='red')
        
    ax.set_xlim(-5, 35)
    ax.set_ylim(-10, 25) # Expanded view for hairpin
    ax.set_title(f"Simulation Frame: {n} Cones Visible")
    ax.legend()
    ax.grid(True)
    plt.pause(0.1)

plt.ioff()
plt.show()