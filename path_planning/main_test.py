# main_test.py
import matplotlib.pyplot as plt
import numpy as np
from modules.planner import PathPlanner

# --- 1. New Input Format ---
# List of tuples: [(x, y, color), ...]
cone_data = [
    # Right Side (Yellow)
    (0, 0, 'y'), (2, 0, 'y'), (4, 1, 'y'), (6, 1, 'y'), (8, 0, 'y'), (10, 0, 'y'),
    # Left Side (Blue)
    (0, 3, 'b'), (2, 3, 'b'), (4, 4, 'b'), (6, 4, 'b'), (8, 3, 'b'), (10, 3, 'b')
]
# Recommended Car Start: (0.0, 1.5, 0.0)


# Car input: [(x, y, orientation_in_radians)]
# Orientation 0.0 points East (Right)
car_data = [(0.0, 1.5, 0.0)]

# --- 2. Execution ---
planner = PathPlanner()
path_points = planner.execute_cycle(cone_data, car_data)

# --- 3. Visualization ---
print(f"Path Generated with {len(path_points)} points.")

# Unpack data for plotting
xs = [c[0] for c in cone_data]
ys = [c[1] for c in cone_data]
colors = ['gold' if c[2] == 'y' else 'blue' for c in cone_data]

plt.figure(figsize=(8, 6))
plt.scatter(xs, ys, c=colors, s=100, label='Cones')
plt.plot(car_data[0][0], car_data[0][1], 'r^', markersize=15, label='Car')

if path_points:
    px = [p[0] for p in path_points]
    py = [p[1] for p in path_points]
    plt.plot(px, py, '-g', linewidth=2, label='Calculated Path')
    plt.scatter(px, py, c='green', s=20)

plt.legend()
plt.axis('equal')
plt.grid(True)
plt.show()