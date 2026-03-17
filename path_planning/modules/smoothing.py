import numpy as np
from scipy.interpolate import splprep, splev

def smooth_path_bspline(rx, ry, smoothing=0.4, num_points=300):
    """
    Smooth path using B-spline.

    Args:
        rx, ry: raw path x/y lists
        smoothing: spline smoothing factor (higher = smoother)
        num_points: number of output points

    Returns:
        smoothed_x, smoothed_y
    """
    rx = np.array(rx, dtype=float)
    ry = np.array(ry, dtype=float)

    if len(rx) < 4:
        # Not enough points for a cubic B-spline
        return rx, ry

    # Remove duplicate consecutive points (splprep cannot handle zero-length segments)
    pts = np.vstack((rx, ry)).T
    unique_idx = np.concatenate(([True], np.any(np.diff(pts, axis=0) != 0, axis=1)))
    pts = pts[unique_idx]

    if pts.shape[0] < 4:
        return pts[:, 0], pts[:, 1]

    # Arc-length parameterization
    ds = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.insert(np.cumsum(ds), 0, 0.0)
    if s[-1] <= 0:
        return pts[:, 0], pts[:, 1]
    s /= s[-1]  # normalize to [0,1]

    # Try 3->2->1 spline degree as fallback for near-colinear or degenerate inputs
    for k in (3, 2, 1):
        try:
            tck, _ = splprep(
                [pts[:, 0], pts[:, 1]],
                u=s,
                s=smoothing,
                k=k
            )
            u_fine = np.linspace(0, 1, num_points)
            smoothed_x, smoothed_y = splev(u_fine, tck)
            return np.array(smoothed_x), np.array(smoothed_y)
        except Exception:
            continue

    # As a final fallback, return the input path without smoothing
    return pts[:, 0], pts[:, 1]


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