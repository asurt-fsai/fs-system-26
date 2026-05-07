import numpy as np
from scipy.interpolate import splprep, splev

""""
handwar 3ala no3 smoothing for straight paths only.
1- pca
2- line of sight, Converts zig-zag → straight segments

new_path = [start]
i = 0

while i < len(path)-1:
    j = len(path)-1
    while j > i+1:
        if line_of_sight(path[i], path[j]):
            break
        j -= 1
    new_path.append(path[j])
    i = j

3- we can also use theta* instead of Dijkstra to get a smoother path.
"""

# def smooth_path_bspline(rx, ry, smoothing=0.4, num_points=300):
#     """
#     Smooth path using B-spline.

#     Args:
#         rx, ry: raw path x/y lists
#         smoothing: spline smoothing factor (higher = smoother)
#         num_points: number of output points

#     Returns:
#         smoothed_x, smoothed_y
#     """
#     rx = np.array(rx, dtype=float)
#     ry = np.array(ry, dtype=float)

#     if len(rx) < 4:
#         # Not enough points for a cubic B-spline
#         return rx, ry

#     # Remove duplicate consecutive points (splprep cannot handle zero-length segments)
#     pts = np.vstack((rx, ry)).T
#     unique_idx = np.concatenate(([True], np.any(np.diff(pts, axis=0) != 0, axis=1)))
#     pts = pts[unique_idx]

#     if pts.shape[0] < 4:
#         return pts[:, 0], pts[:, 1]

#     # Arc-length parameterization
#     ds = np.linalg.norm(np.diff(pts, axis=0), axis=1)
#     s = np.insert(np.cumsum(ds), 0, 0.0)
#     if s[-1] <= 0:
#         return pts[:, 0], pts[:, 1]
#     s /= s[-1]  # normalize to [0,1]

#     # Try 3->2->1 spline degree as fallback for near-colinear or degenerate inputs
#     for k in (3, 2, 1):
#         try:
#             tck, _ = splprep(
#                 [pts[:, 0], pts[:, 1]],
#                 u=s,
#                 s=smoothing,
#                 k=k
#             )
#             u_fine = np.linspace(0, 1, num_points)
#             smoothed_x, smoothed_y = splev(u_fine, tck)
#             return np.array(smoothed_x), np.array(smoothed_y)
#         except Exception:
#             continue

#     # As a final fallback, return the input path without smoothing
#     return pts[:, 0], pts[:, 1]


# def smooth_path_line(rx, ry, num_points=50):
#     """
#     Straighten a sparse/zigzag path by fitting a line (PCA) and
#     resampling points along that line.

#     Args:
#         rx, ry: raw path x/y lists
#         num_points: number of output points

#     Returns:
#         straight_x, straight_y
#     """
#     rx = np.array(rx)
#     ry = np.array(ry)

#     if len(rx) < 2:
#         return rx, ry

#     pts = np.column_stack((rx, ry))
#     mean = pts.mean(axis=0)
#     centered = pts - mean

#     # Principal direction (largest eigenvector of covariance)
#     cov = np.cov(centered.T)
#     eigvals, eigvecs = np.linalg.eig(cov)
#     direction = eigvecs[:, np.argmax(eigvals)]
#     direction = direction / np.linalg.norm(direction)

#     # Project points onto the line to get ordering
#     t = centered @ direction
#     t_min, t_max = t.min(), t.max()
#     if t_max == t_min:
#         return rx, ry

#     t_samples = np.linspace(t_min, t_max, num_points)
#     line_pts = mean + np.outer(t_samples, direction)

#     straight_x = line_pts[:, 0]
#     straight_y = line_pts[:, 1]

#     return straight_x, straight_y

from sklearn.decomposition import PCA

def smooth_path_pca(path, n_components=1):
    """
    Project noisy path points onto their first principal component 
    to find the 'best fit' straight line.
    """
    if len(path) < 3:
        return path

    points = np.array(path)
    pca = PCA(n_components=1)
    
    # 1. Find the primary direction of the path
    pca.fit(points)
    
    # 2. Project the points onto that 1D line
    projected_points_1d = pca.transform(points)
    
    # 3. Reconstruct back to 2D
    smoothed_points = pca.inverse_transform(projected_points_1d)
    
    # Keep the original car position as the starting point exactly
    smoothed_points[0] = points[0] 
    
    return [tuple(p) for p in smoothed_points]

   
# def smooth_path_bspline(path, num_points=20, smoothing=0.5):
#     pts = np.array(path)
#     x, y = pts[:, 0], pts[:, 1]
    
#     # s=0 → interpolate exactly (stiff, follows points)
#     # s>0 → smooth/deviate from points (looser)
#     # k=1 → LINEAR spline (perfectly straight between points!)
#     # k=3 → cubic (curves)
#     tck, u = splprep([x, y], s=smoothing, k=1)  # k=1 = straight line segments
#     u_new = np.linspace(0, 1, num_points)
#     new_x, new_y = splev(u_new, tck)
#     return list(zip(new_x, new_y))

def smooth_path_bspline(rx, ry, point_spacing=0.5):
    rx = np.array(rx, dtype=float)
    ry = np.array(ry, dtype=float)

    if len(rx) < 2:
        return rx, ry

    pts = np.vstack((rx, ry)).T

    # Remove duplicate consecutive points
    unique_mask = np.concatenate(([True], np.any(np.diff(pts, axis=0) != 0, axis=1)))
    pts = pts[unique_mask]

    if len(pts) < 2:
        return rx, ry

    x, y = pts[:, 0], pts[:, 1]
    k = 1 if len(pts) < 4 else 1

    tck, _ = splprep([x, y], s=0.1, k=k)

    total_length = sum(np.linalg.norm(pts[i+1] - pts[i]) for i in range(len(pts)-1))
    num_points = max(2, int(total_length / point_spacing))

    u_new = np.linspace(0, 1, num_points)
    smoothed_x, smoothed_y = splev(u_new, tck)
    return np.array(smoothed_x), np.array(smoothed_y)