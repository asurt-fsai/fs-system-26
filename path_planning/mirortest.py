import matplotlib.pyplot as plt
import numpy as np
from modules.planner import PathPlanner
from modules import voronoi_gen

import matplotlib.pyplot as plt
import numpy as np
from modules.planner import PathPlanner
from modules import voronoi_gen

def run_test_visual(name, cones, planner):
    print(f"\n--- RUNNING TEST: {name} ---")
    car_data = [(-2.5, -2.5, 0.0)] # x, y, yaw
    
    # 1. Execute Cycle
    path_points = planner.execute_cycle(cones, car_data)
    
    # 2. Get data for visualization
    balanced, midpoints = planner._balance_by_full_mirror(cones, car_data[0][2], virtual_width=4.0)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # --- LAYER 1: CONES ---
    for c in balanced:
        is_v = c[3] if len(c) > 3 else False
        cone_color = 'blue' if c[2] == 'b' else 'gold'
        ax.scatter(x=c[0], y=c[1], c=cone_color, 
                    alpha=0.3 if is_v else 1.0, 
                    edgecolors='none' if is_v else 'black', 
                    s=120, zorder=3, 
                    label=f"Virtual {c[2]}" if is_v else None)

    # --- LAYER 2: MIDPOINTS (Stars) ---
    for mp in midpoints:
        ax.scatter(x=mp[0], y=mp[1], c='lime', marker='*', s=150, 
                   edgecolors='black', zorder=5, label='Gate Midpoint')

    # --- LAYER 3: PATH ---
    if path_points:
        px, py = zip(*path_points)
        ax.plot(px, py, '-g', linewidth=3, label='Final Path', zorder=4)
        ax.scatter(px, py, c='lime', s=20, zorder=5)

    # --- DYNAMIC ZOOM FOR CASE 12 ---
    if "14" in name:
        ax.set_xlim(-10, 30)
        ax.set_ylim(-5, 22)
        # Add width labels for clarity
        ax.text(2, 0, "3m Width", color='black', fontsize=9, ha='center')
        ax.text(22, 12, "4m Width", color='black', fontsize=9, rotation=70)
    
    ax.set_title(f"Test Case: {name}")
    ax.set_aspect('equal')
    ax.grid(True, linestyle=':', alpha=0.6)
    
    # Legend deduplication
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper left', fontsize='small')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Initialize Planner (Using max_edge_len=15.0 for sparse cases)
    planner = PathPlanner(robot_radius=0.0, safety_margin=0.0, max_edge_len=15.0)

    # 10 Comprehensive Test Cases
    test_cases = [
      #("1. Baseline Corridor", [(2, 2.5, 'b'), (2, -2.5, 'y'), (8, 2.5, 'b'), (8, -2.5, 'y')]),
       # ("2. Standard Slalom", [(2, 2, 'b'), (2, -2, 'y'), (10, 4, 'b'), (18, -4, 'y')]),
       # ("3. Staggered Long Slalom", [(2, 2, 'b'), (2, -2, 'y'), (14, 4, 'b'), (26, -4, 'y')]),
        #("4. Tight Bottleneck", [(2, 3, 'b'), (2, -3, 'y'), (10, 1.2, 'b'), (10, -1.2, 'y'), (18, 3, 'b')]),
       # ("5. Narrowing Funnel", [(x, 5 - x*0.2, 'b') for x in range(2, 16, 4)] + [(x, -5 + x*0.2, 'y') for x in range(2, 16, 4)]),
       # ("6. 90-Deg Turn (Left)", [(2, 2, 'b'), (5, 2, 'b'), (8, 2, 'b'), (8, 5, 'b'), (8, 8, 'b')]),
      #("7. Sparse Straight", [(2, 2, 'b'), (2, -2, 'y'), (25, 2, 'b'), (25, -2, 'y')]),
       #("8. Missing Partners", [(5, 3, 'b'), (10, -3, 'y'), (15, 3, 'b')]),
        
       #("10. Noisy/Close Cones", [(5, 2, 'b'), (5.1, 2.1, 'b'), (5, -2, 'y'), (5, -1.9, 'y')])
    ]

    # CASE 12: Wide Vertical Sweep (No Virtual Cones Expected)
    # CASE 12: Wide Entrance (8m) to Tight Curve (4m)
# Goal: No virtual cones at start, smooth curve following.
    # CASE 12: Precision Wide Entrance to Tight Curve
# This test ensures the smart pairing logic handles transitions without 
# hallucinating virtual cones, following your exact sketch dimensions.
        # CASE 12: Precision Wide Entrance to Tight Curve
# Yellow Right (Inner), Blue Left (Outer), Distance 4m in curve
    case_precision_sweep = [
    # --- Parallel Entrance (Width = 3m) ---
    (1, 4, 'b'),   (1, 1, 'y'),  # Start Gate
    (4, 4, 'b'),   (4, 1, 'y'),
    (7, 4, 'b'),  (7, 1, 'y'),
    (10,4, 'b'), (10, 1, 'y'),  
    
    # --- Transition (Widening to 4m) ---
      (14, 1.5, 'y'),
    
    # --- The Curve (Constant 4m width) ---
    # Coordinates calculated to keep Yellow on the right and Blue on the left
    (13, 8, 'b'),   # Turn starts
     # Blue outside, Yellow inside
    (15, 14, 'b'),  # Maintaining 4m sweep
    (20, 18, 'b'), (27, 10, 'y') 
     
]

# Add to your test cases in mirortest.py
    case_13 =[(1,1,'y'),(4,1.2,'y'),(4,5.2,'b'),(8,2,'y'),(12,2.5,'y'),(12,6.5,'b'),(16,3,'y'),(16,7,'b')]


    
    #test_cases.append(("12. Precision Precision Sweep", case_precision_sweep))
    #test_cases.append(("13. Asymmetric Pairing Challenge", case_13))
    # --- CASE 14: The Hairpin Challenge ---
# A tight 180-degree turn to test local heading and adaptive width.
    
    perfect_hairpin = [(1,1,'y'),(4,1,'y'),(1,4,'b'),(4,4,'b'), (7,1.5,'y'),(7,4.5,'b'),(10,2,'y'),(9.5,5,'b'),(13,5,'y'),(10.5,8,'b')]
    test_cases.append(("21. Perfect Hairpin", perfect_hairpin))


    def generate_hairpin(start_x=5, start_y=0, inner_radius=4.0, width=4.0, num_cones=6):
        """
        Generates a 180-degree hairpin turn.
        Yellow = Outside (Larger radius)
        Blue = Inside (Smaller radius)
        """
        cones = []
    # Radii for both sides
        r_blue = inner_radius
        r_yellow = inner_radius + width
    
    # Generate angles from -90 to +90 degrees (a 180-deg U-turn)
        angles = np.linspace(-np.pi/2, np.pi/2, num_cones)
    
        for alpha in angles:
        # Blue Cones (Inside)
            bx = start_x + r_blue * np.cos(alpha)
            by = start_y + r_blue * np.sin(alpha) + r_blue
            cones.append((bx, by, 'b'))
        
        # Yellow Cones (Outside)
            yx = start_x + r_yellow * np.cos(alpha)
            yy = start_y + r_yellow * np.sin(alpha) + r_blue # Centered on same point
            cones.append((yx, yy, 'y'))
            cones.append((7,-4,'y'))
            cones.append((4,-4,'y'))
            cones.append((1,-4,'y'))
            cones.append((7,0,'b'))
            cones.append((4,0,'b'))
            cones.append((1,0,'b')) # Add some extra yellows to widen the entrance
            cones.append((7,10,'b'))
            cones.append((4,10,'b'))
            cones.append((1,10,'b')) 
            cones.append((7,14,'y'))
            cones.append((4,14,'y'))
            cones.append((1,14,'y')) # Add some extra yellows to widen the
        
        
        return cones
    
    if __name__ == "__main__":
        planner = PathPlanner(robot_radius=0.0, safety_margin=0.0, max_edge_len=15.0)
        test_cases = []

    # Generate the perfect hairpin
    # start_x=10 moves it forward so it doesn't overlap the origin
        hairpin_cones = generate_hairpin(start_x=10, start_y=0, inner_radius=5.0, width=4.0, num_cones=8)
    
        test_cases.append(("14. Mathematical Hairpin (Yellow Outside)", hairpin_cones))

        for name, cones in test_cases:
            run_test_visual(name, cones, planner)