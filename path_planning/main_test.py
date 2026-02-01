# main_test.py
import matplotlib.pyplot as plt
import numpy as np
from modules.planner import PathPlanner

# Test 0: One-side only cones (all Yellow)
print("\n" + "="*60)
print("TEST 0: ONE-SIDE ONLY CONES (All Yellow)")
print("="*60)

cone_data_one_side = [
    # Right Side (Yellow) - 6 cones
    (0, 0, 'y'), (2, 0, 'y'), (4, 0, 'y'), (6, 0, 'y'), (8, 0, 'y'), (10, 0, 'y')
]

car_data_one_side = [(0.0, 1.5, 0.0)]

planner_one_side = PathPlanner(robot_radius=0.5, safety_margin=0.2, max_edge_len=5.0)
print(f"Planner config: robot_radius={planner_one_side.robot_radius}, safety_margin={planner_one_side.safety_margin}, max_edge_len={planner_one_side.max_edge_len}")
path_points_one_side = planner_one_side.execute_cycle(cone_data_one_side, car_data_one_side)

print(f"Path Generated with {len(path_points_one_side)} points.")

xs_one = [c[0] for c in cone_data_one_side]
ys_one = [c[1] for c in cone_data_one_side]
colors_one = ['gold' if c[2] == 'y' else 'blue' for c in cone_data_one_side]

plt.figure(figsize=(10, 6))
plt.scatter(xs_one, ys_one, c=colors_one, s=100, label='Cones', edgecolors='black', linewidth=2)
plt.plot(car_data_one_side[0][0], car_data_one_side[0][1], 'r^', markersize=15, label='Car Start')

if path_points_one_side:
    px_one = [p[0] for p in path_points_one_side]
    py_one = [p[1] for p in path_points_one_side]
    plt.plot(px_one, py_one, '-g', linewidth=2, label='Calculated Path')
    plt.scatter(px_one, py_one, c='green', s=20, alpha=0.5)

plt.title('Test 0: One-Side Only Cones (All Yellow)')
plt.legend()
plt.axis('equal')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Test 1: Balanced cones (original)
print("\n" + "="*60)
print("TEST 1: BALANCED CONES (6 Yellow, 6 Blue)")
print("="*60)

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
planner = PathPlanner(robot_radius=0.5, safety_margin=0.2, max_edge_len=5.0)
print(f"Planner config: robot_radius={planner.robot_radius}, safety_margin={planner.safety_margin}, max_edge_len={planner.max_edge_len}")
path_points = planner.execute_cycle(cone_data, car_data)

# --- 3. Visualization ---
print(f"Path Generated with {len(path_points)} points.")

# Unpack data for plotting
xs = [c[0] for c in cone_data]
ys = [c[1] for c in cone_data]
colors = ['gold' if c[2] == 'y' else 'blue' for c in cone_data]

plt.figure(figsize=(10, 6))
plt.scatter(xs, ys, c=colors, s=100, label='Cones', edgecolors='black', linewidth=2)
plt.plot(car_data[0][0], car_data[0][1], 'r^', markersize=15, label='Car Start')

if path_points:
    px = [p[0] for p in path_points]
    py = [p[1] for p in path_points]
    plt.plot(px, py, '-g', linewidth=2, label='Calculated Path')
    plt.scatter(px, py, c='green', s=20, alpha=0.5)

plt.title('Test 1: Balanced Cones (6 Yellow, 6 Blue)')
plt.legend()
plt.axis('equal')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Test 2: Uneven cones (4 Yellow, 1 Blue)
print("\n" + "="*60)
print("TEST 2: SIMPLE UNEVEN CONES (4 Yellow, 1 Blue)")
print("="*60)

cone_data_simple = [
    # Right Side (Yellow) - 4 cones
    (0, 0, 'y'), (4, 0, 'y'), (8, 0, 'y'), (12, 0, 'y'),
    # Left Side (Blue) - 1 cone
    (6, 3, 'b')
]

car_data_simple = [(0.0, 1.5, 0.0)]

planner_simple = PathPlanner(robot_radius=0.5, safety_margin=0.2, max_edge_len=5.0)
print(f"Planner config: robot_radius={planner_simple.robot_radius}, safety_margin={planner_simple.safety_margin}, max_edge_len={planner_simple.max_edge_len}")
path_points_simple = planner_simple.execute_cycle(cone_data_simple, car_data_simple)

# --- 3. Visualization ---
print(f"Path Generated with {len(path_points_simple)} points.")

# Unpack data for plotting
xs_simple = [c[0] for c in cone_data_simple]
ys_simple = [c[1] for c in cone_data_simple]
colors_simple = ['gold' if c[2] == 'y' else 'blue' for c in cone_data_simple]

plt.figure(figsize=(10, 6))
plt.scatter(xs_simple, ys_simple, c=colors_simple, s=100, label='Original Cones', edgecolors='black', linewidth=2)
plt.plot(car_data_simple[0][0], car_data_simple[0][1], 'r^', markersize=15, label='Car Start')

if path_points_simple:
    px_simple = [p[0] for p in path_points_simple]
    py_simple = [p[1] for p in path_points_simple]
    plt.plot(px_simple, py_simple, '-g', linewidth=2, label='Calculated Path')
    plt.scatter(px_simple, py_simple, c='green', s=20, alpha=0.5)

plt.title('Test 2: Simple Uneven Cones - Virtual Cones Added (4 Yellow, 1 Blue)')
plt.legend()
plt.axis('equal')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()