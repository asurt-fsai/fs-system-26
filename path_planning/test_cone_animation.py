import matplotlib.pyplot as plt
import numpy as np
from modules.planner import PathPlanner

# ==========================================
# 1. CONFIGURATION
# ==========================================
# Select what you want to run: 'full_sim'
RUN_MODE = 'full_sim'

# Simulation Settings
START_VISIBLE = 2
REVEAL_RATE = 4
SHAPE_MODE = 'hairpin'

# ==========================================
# 2. HELPER FUNCTIONS (Track Generation)
# ==========================================
def generate_cones_from_path(center_line_points, track_width=4.0, step=3):
    cones = []
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
    for x in np.linspace(0, 20, 20): points.append((x, 0))
    for t in np.linspace(-1.57, 1.57, 20):
        points.append((20 + 8*np.cos(t), 8 + 8*np.sin(t)))
    for x in np.linspace(20, 0, 20): points.append((x, 16))
    return points

def get_s_curve_path():
    return [(x, 5 * np.sin(x * 0.2)) for x in np.linspace(0, 50, 60)]

# ==========================================
# 3. THE ORIGINAL SIMULATION LOGIC
# ==========================================
def run_full_simulation():
    print("--- RUNNING FULL TRACK SIMULATION ---")
    
    # 1. Generate Track
    if SHAPE_MODE == 'hairpin':
        center = get_hairpin_path()
    elif SHAPE_MODE == 's_curve':
        center = get_s_curve_path()
    else:
        center = [(x, 0) for x in np.linspace(0, 50, 50)]
        
    full_track_cones = generate_cones_from_path(center)
    # ==========================================
    # ADD GHOST CONE TO HAIRPIN HERE
    # ==========================================
    if SHAPE_MODE == 'hairpin':
        # Placed at (22, 8), which is right in the middle of the hairpin turn
        # This sits between the blue and yellow boundaries.
        full_track_cones.append((28.0, 8.0, 'b'))
        # ==========================================
    
    # 2. Setup Planner
    planner = PathPlanner(robot_radius=0.6, safety_margin=0.5, max_edge_len=6.0)
    car_data = [(0.0, 0.0, 0.0)]

    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 8))

    # 3. The Loop
    for n in range(START_VISIBLE, len(full_track_cones) + 1, REVEAL_RATE):
        visible_cones = full_track_cones[:n]
        path_points = planner.execute_cycle(visible_cones, car_data)
        
        ax.clear()
        xs = [c[0] for c in visible_cones]
        ys = [c[1] for c in visible_cones]
        cols = ['gold' if c[2] == 'y' else 'blue' for c in visible_cones]
        ax.scatter(xs, ys, c=cols, s=100, edgecolors='k')
        
        if path_points:
            px = [p[0] for p in path_points]
            py = [p[1] for p in path_points]
            ax.plot(px, py, '-g', linewidth=3, label='Planned Path')
            ax.scatter(px, py, c='lime', s=20)
        else:
            ax.text(0, 0, "NO PATH FOUND", fontsize=15, color='red')
            
        ax.set_xlim(-5, 35)
        ax.set_ylim(-10, 25)
        ax.set_title(f"Full Sim: {n} Cones")
        ax.grid(True)
        plt.pause(0.1)
    
    plt.ioff()
    plt.show()

# ==========================================
# 4. MAIN EXECUTION
# ==========================================

if __name__ == "__main__":
    
    if RUN_MODE == 'full_sim':
        run_full_simulation()
    else:
        print(f"Unknown RUN_MODE: {RUN_MODE}")