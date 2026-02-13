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
    car_data = [(-10, 0.0, 0.0)] # x, y, yaw
    
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
      # ("7. Sparse Straight", [(2, 2, 'b'), (2, -2, 'y'), (25, 2, 'b'), (25, -2, 'y')]),
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
    case_hairpin = [(-2,1,'y'),(-5,1,'y'),(-8,1,'y')
   ,(1,1,'y'),(4,1,'y'),(7,2,'y'),(9,4,'y'),(10,7,'y'),(7,9,'y'),(4,10,'y')]


    test_cases.append(("14. Hairpin 180-Degree Turn", case_hairpin))

    for name, cones in test_cases:
        run_test_visual(name, cones, planner)