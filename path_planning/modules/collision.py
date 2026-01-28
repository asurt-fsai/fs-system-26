"""
Collision detection module for Formula AI path planning.
Checks if a path segment between two points collides with any cones.
"""

import math
import numpy as np
from scipy.spatial import cKDTree


def is_collision(sx, sy, gx, gy, robot_radius, obstacle_tree, max_edge_len=30.0):
    """
    Checks for collisions between two waypoints (sx, sy) and (gx, gy).
    
    :param sx, sy: Start point coordinates
    :param gx, gy: Goal point coordinates
    :param robot_radius: Effective radius of the vehicle (with safety margin)
    :param obstacle_tree: KDTree structure containing obstacle (cone) positions
    :param max_edge_len: Maximum allowable edge length
    :return: True if collision detected, False otherwise
    """
    x = sx
    y = sy
    dx = gx - sx
    dy = gy - sy
    yaw = math.atan2(dy, dx)
    d = math.hypot(dx, dy)

    # If edge is too long, consider it invalid
    if d >= max_edge_len:
        return True

    # Step size for collision checking
    D = robot_radius
    n_steps = max(int(d / D), 1)

    # Check collision at intermediate points along the edge
    for _ in range(n_steps):
        dist, _ = obstacle_tree.query([x, y])
        if dist <= robot_radius:
            return True  # Collision detected
        x += D * math.cos(yaw)
        y += D * math.sin(yaw)

    # Final check at the goal point
    dist, _ = obstacle_tree.query([gx, gy])
    if dist <= robot_radius:
        return True  # Collision at goal

    return False  # No collision


def build_obstacle_tree(cone_data):
    """
    Builds a KDTree from cone data for efficient collision queries.
    
    :param cone_data: List of tuples [(x, y, color), ...]
    :return: cKDTree object
    """
    points = np.array([[cone[0], cone[1]] for cone in cone_data])
    return cKDTree(points)