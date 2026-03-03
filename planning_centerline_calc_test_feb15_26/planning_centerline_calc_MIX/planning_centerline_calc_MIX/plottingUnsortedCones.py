import matplotlib.pyplot as plt
import numpy as np

# All cones
all_cones = np.array([
    [239.65, -104.42, 1],
    [244.27, -106.33, 1],
    [251.16, -107.47, 1],
    [255.52, -100.15, 1],
    [250.20, -94.74, 1],
    [254.70, -104.62, 1],
    [246.82, -92.73, 1],
    [240.79, -101.65, 2],
    [245.41, -103.56, 2],
    [250.17, -104.64, 2],
    [252.57, -100.73, 2],
    [249.11, -97.53, 2],
    [244.85, -94.99, 2],
])

# Indices of cones NOT taken into consideration
unused_indices = [2, 3, 4, 5, 6, 10, 11, 12]

# Debug printout for cone info and unused cones
print("[DEBUG] Total cones inputted to sorting:", len(all_cones))
print("[planning_centerline_calc_node-1] [DEBUG] Cone positions and types:")
for i, cone in enumerate(all_cones):
    print(f"[planning_centerline_calc_node-1]   {i}: (x={cone[0]}, y={cone[1]}, type={int(cone[2])})")

print("[planning_centerline_calc_node-1] [DEBUG] Cones NOT taken into consideration by sorting:")
for i in unused_indices:
    cone = all_cones[i]
    print(f"[planning_centerline_calc_node-1]   {i}: (x={cone[0]}, y={cone[1]}, type={int(cone[2])})")

# Plot all cones
plt.figure(figsize=(8, 6))
for i, cone in enumerate(all_cones):
    color = 'y' if cone[2] == 1 else 'b'
    plt.scatter(cone[0], cone[1], c=color, s=60, label=f'Type {int(cone[2])}' if i == 0 else "")

# Highlight unused cones
for idx, i in enumerate(unused_indices):
    cone = all_cones[i]
    plt.scatter(cone[0], cone[1], c='r', s=120, marker='x', label='Unused' if idx == 0 else "")
    plt.text(cone[0], cone[1], str(i), color='r', fontsize=10)

plt.xlabel('X')
plt.ylabel('Y')
plt.title('Cones and Unused Cones (Red X)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
