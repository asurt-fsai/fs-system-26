import matplotlib.pyplot as plt
import numpy as np
from modules.planner import PathPlanner

# ==========================================
# 1. CONFIGURATION
# ==========================================
# Select what you want to run: 'full_sim', 'test_1_cone', or 'test_2_cones'
RUN_MODE = 'full_sim'

# Simulation Settings
START_VISIBLE = 2
REVEAL_RATE = 4
SHAPE_MODE = 'straight'  # Options: 'straight', 'hairpin', 's_curve'

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
    
    # 2. Setup Planner
    planner = PathPlanner(robot_radius=0.7, safety_margin=0.4, max_edge_len=8.0)
    car_data = [(0.0, 0.0, 0.0)]

    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 8))

    # 3. The Loop (Updated for Dynamic Movement & Yaw)
    # 3. The Loop (Updated with Virtual Cone Visualization)
    current_x, current_y, current_yaw = 0.0, 0.0, 0.0

    for n in range(START_VISIBLE, len(full_track_cones) + 1, REVEAL_RATE):
        visible_cones = full_track_cones[:n]
        car_data = [(current_x, current_y, current_yaw)]
        
        # --- DEBUG STEP: Get the balanced list to visualize hallucinations ---
        # Assuming your planner stores the balanced list or you can call it:
        balanced_cones = planner._balance_uneven_cones(visible_cones, current_yaw)
        
        # Execute the planning cycle
        path_points = planner.execute_cycle(visible_cones, car_data)
        
        if path_points and len(path_points) > 1:
            next_p = path_points[1]
            dx, dy = next_p[0] - current_x, next_p[1] - current_y
            current_yaw = np.arctan2(dy, dx)
            current_x, current_y = next_p[0], next_p[1]

        # --- Visualization ---
        ax.clear()
        
        # 1. Plot VIRTUAL Cones (Faded colors)
        # We identify them by checking which cones in 'balanced' aren't in 'visible'
        visible_coords = set((c[0], c[1]) for c in visible_cones)
        for bc in balanced_cones:
            if (bc[0], bc[1]) not in visible_coords:
                v_col = 'cyan' if bc[2] == 'b' else 'orange'
                ax.scatter(bc[0], bc[1], c=v_col, s=150, alpha=0.3, edgecolors='none', label="Virtual" if 'Virtual' not in ax.get_legend_handles_labels()[1] else "")

        # 2. Plot REAL Cones (Solid colors)
        xs = [c[0] for c in visible_cones]
        ys = [c[1] for c in visible_cones]
        cols = ['gold' if c[2] == 'y' else 'blue' for c in visible_cones]
        ax.scatter(xs, ys, c=cols, s=100, edgecolors='k', zorder=5, label="Real Cones")
        
        # 3. Plot Car
        ax.plot(current_x, current_y, color='red', marker=(3, 0, np.degrees(current_yaw)-90), markersize=15)
        
        # 4. Plot Path
        if path_points:
            px, py = zip(*path_points)
            ax.plot(px, py, '-g', linewidth=3, label='Planned Path')
        else:
            ax.text(current_x, current_y, "NO PATH FOUND", fontsize=15, color='red', weight='bold')
            
        # Camera & Layout
        ax.set_aspect('equal')
        ax.set_xlim(current_x - 15, current_x + 25)
        ax.set_ylim(current_y - 15, current_y + 15)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(loc='upper right', fontsize='small')
        
        plt.pause(0.1)
    
    plt.ioff()
    plt.show()

# ==========================================
# 4. NEW TEST FUNCTIONS (1 & 2 Cones)
# ==========================================
def run_static_test(cones, title):
    """Helper function to run a single static test frame"""
    planner = PathPlanner(robot_radius=0.75, safety_margin=0.5, max_edge_len=8.0)
    
    # Car at (0,0) facing East (0 radians)
    car_data = [(0.0, 0.0, 0.0)]
    
    print(f"--- TESTING: {title} ---")
    path_points = planner.execute_cycle(cones, car_data)
    
    # Visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot Cones
    if cones:
        xs = [c[0] for c in cones]
        ys = [c[1] for c in cones]
        cols = ['gold' if c[2] == 'y' else 'blue' for c in cones]
        ax.scatter(xs, ys, c=cols, s=150, edgecolors='k', zorder=5)
    
    # Plot Car
    ax.plot(0, 0, 'r^', markersize=15, label="Car", zorder=10)
    
    # Plot Path
    if path_points:
        px = [p[0] for p in path_points]
        py = [p[1] for p in path_points]
        ax.plot(px, py, '-g', linewidth=3, label='Resulting Path')
        ax.scatter(px, py, c='lime', s=30)
    else:
        ax.text(1, 0, "NO PATH FOUND", fontsize=15, color='red')

    ax.set_title(title)
    ax.set_xlim(-2, 15)
    ax.set_ylim(-5, 5)
    ax.grid(True)
    ax.legend()
    plt.show()



def test_uneven_balance():
    """
    Scenario: 
    1. Blue Wall: Only blue cones for the first 10 meters.
    2. Yellow Wall: Only yellow cones from 10m to 20m.
    3. Normal: Both colors from 20m to 30m.
    """
    print("--- TESTING: Uneven Balance Logic ---")
    
    # Generate Synthetic Data
    test_cones = []
    
    # Segment 1: Blue Wall Only (Dense)
    for x in range(2, 12, 2):
        test_cones.append((float(x), 3.0, 'b'))
        
    # Segment 2: Yellow Wall Only (Dense)
    for x in range(14, 20, 2):
        test_cones.append((float(x), -3.0, 'y'))
        
    # Segment 3: Normal Straight
    for x in range(22, 36, 2):
        test_cones.append((float(x), 1.5, 'b'))
        test_cones.append((float(x), -1.5, 'y'))

    # Run the test
    planner = PathPlanner(robot_radius=0.75, safety_margin=0.5, max_edge_len=8.0)
    car_data = [(0.0, 0.0, 0.0)] # Car starting at origin
    
    # We manually trigger balance here to see it, 
    # but planner.execute_cycle should call it internally
    balanced = planner._balance_uneven_cones(test_cones, car_yaw=0.0, virtual_width=3.0)
    path_points = planner.execute_cycle(test_cones, car_data)

    # Visualization
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 1. Plot Original Cones (Solid colors)
    xs = [c[0] for c in test_cones]
    ys = [c[1] for c in test_cones]
    cols = ['gold' if c[2] == 'y' else 'blue' for c in test_cones]
    ax.scatter(xs, ys, c=cols, s=100, edgecolors='k', label="Real Cones", zorder=5)

    # 2. Plot Balanced Cones (Faded/smaller to see the "hallucinated" ones)
    b_xs = [c[0] for c in balanced]
    b_ys = [c[1] for c in balanced]
    b_cols = ['orange' if c[2] == 'y' else 'cyan' for c in balanced]
    ax.scatter(b_xs, b_ys, c=b_cols, s=30, alpha=0.5, label="Balanced (Virtual)")

    # 3. Plot Path
    if path_points:
        px = [p[0] for p in path_points]
        py = [p[1] for p in path_points]
        ax.plot(px, py, '-g', linewidth=2, label='Path')

    ax.set_title("Uneven Balance Test: Blue Wall -> Yellow Wall -> Normal")
    ax.set_xlim(-2, 40)
    ax.set_ylim(-8, 8)
    ax.grid(True)
    ax.legend()
    plt.show()


# ==========================================
# 5. MAIN EXECUTION (Select Mode Here)
# ==========================================
if __name__ == "__main__":
    
    
    if RUN_MODE == 'full_sim':
        run_full_simulation()
    elif RUN_MODE == 'test_uneven_balance':
        test_uneven_balance()
        
    else:
        print("Invalid Run Mode selected.")