import numpy as np
from scipy.interpolate import splprep, splev

def smooth_path_bspline(rx, ry, smoothing=0.5, num_points=100):
    """
    Smooth path using B-spline .

    Args:
        rx, ry: raw path x/y lists
        smoothing: spline smoothing factor (higher = smoother)
        num_points: number of output points

    Returns:
        smoothed_x, smoothed_y
    """
    rx = np.array(rx)
    ry = np.array(ry)

    if len(rx) < 4:
        # Not enough points for a cubic B-spline
        return rx, ry

    # Arc-length parameterization
    ds = np.sqrt(np.diff(rx)**2 + np.diff(ry)**2)
    s = np.insert(np.cumsum(ds), 0, 0.0)
    s /= s[-1]  # normalize to [0,1]

    # Build B-spline
    tck, _ = splprep(
        [rx, ry],
        u=s,
        s=smoothing,     # smoothing strength
        k=3              # cubic B-spline
    )

    u_fine = np.linspace(0, 1, num_points)
    smoothed_x, smoothed_y = splev(u_fine, tck)

    return smoothed_x, smoothed_y


def smooth_path_line(rx, ry, num_points=50):
    """
    Straighten a sparse/zigzag path by fitting a line (PCA) and
    resampling points along that line.

    Args:
        rx, ry: raw path x/y lists
        num_points: number of output points

    Returns:
        straight_x, straight_y
    """
    rx = np.array(rx)
    ry = np.array(ry)

    if len(rx) < 2:
        return rx, ry

    pts = np.column_stack((rx, ry))
    mean = pts.mean(axis=0)
    centered = pts - mean

    # Principal direction (largest eigenvector of covariance)
    cov = np.cov(centered.T)
    eigvals, eigvecs = np.linalg.eig(cov)
    direction = eigvecs[:, np.argmax(eigvals)]
    direction = direction / np.linalg.norm(direction)

    # Project points onto the line to get ordering
    t = centered @ direction
    t_min, t_max = t.min(), t.max()
    if t_max == t_min:
        return rx, ry

    t_samples = np.linspace(t_min, t_max, num_points)
    line_pts = mean + np.outer(t_samples, direction)

    straight_x = line_pts[:, 0]
    straight_y = line_pts[:, 1]

    return straight_x, straight_y
