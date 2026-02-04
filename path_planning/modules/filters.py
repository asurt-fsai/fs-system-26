"""
Filter module for building safe graph from Voronoi diagram.
Applies color matching, distance pruning, and collision detection.
"""

import numpy as np
import networkx as nx
from .collision import is_collision, build_obstacle_tree


def remove_ghost_cones(
    cone_data,
    same_color_max_dist=5.0,
    diff_color_min_dist=3.0
):
    """
    Remove ghost cones using very simple distance consistency rules.

    Rules we know for sure :
    - Same-color cones should NOT be farther than 5 meters apart
    - Different-color cones should NOT be closer than 3 meters

    Method:
    - Each cone gets a violation counter
    - The cone(s) with the highest violations are considered ghosts
    """

    # If there are fewer than 3 cones, we cannot make a reliable decision
    if len(cone_data) < 3:
        return cone_data

    num_cones = len(cone_data)

    # One violation counter per cone
    violation_counts = [0] * num_cones

    # Compare every cone with every other cone
    for i in range(num_cones):
        xi, yi, color_i = cone_data[i]

        for j in range(num_cones):
            # Skip comparing the cone with itself
            if i == j:
                continue

            xj, yj, color_j = cone_data[j]

            # Compute distance between the two cones
            dx = xi - xj
            dy = yi - yj
            distance = np.sqrt(dx * dx + dy * dy)

            # Rule 1: Same color cones: d>5m is suspicious
            if color_i == color_j:
                if distance > same_color_max_dist:
                    violation_counts[i] += 1

            # Rule 2: Different color cones: d<3m is suspicious
            else:
                if distance < diff_color_min_dist:
                    violation_counts[i] += 1

    # Find the maximum number of violations
    max_violations = max(violation_counts)

    # If no cone violated any rule, keep everything
    if max_violations == 0:
        return cone_data

    # Remove the cone(s) with the highest violation count
    filtered = [cone_data[i] for i in range(num_cones) if violation_counts[i] < max_violations]

    return filtered
def build_safe_graph(vor, colors, cone_data, robot_radius, max_edge_len, safety_margin):
    """
    A function that accepts a voronoi structure vor and a list of cone colors.
    Filters Voronoi ridges based on:
    1. Color Mismatch (blue-yellow pairs only)
    2. Distance pruning
    3. Collision detection with cones
    
    Returns a NetworkX graph of safe paths.
    
    :param vor: Voronoi diagram object
    :param colors: List of cone colors corresponding to Voronoi input points
    :param cone_data: Original cone data [(x, y, color), ...]
    :param robot_radius: Effective radius of vehicle
    :param max_edge_len: Maximum allowable edge length
    :param safety_margin: Additional safety buffer around robot
    :return: NetworkX graph with safe edges
    """
    G = nx.Graph()  # Create an empty graph to hold safe edges and vertices

    # Build KDTree for efficient collision detection
    obstacle_tree = build_obstacle_tree(cone_data)
    
    # Effective robot radius with safety margin
    effective_radius = robot_radius + safety_margin

    # Iterate through all potential paths (ridges)
    for (p1_idx, p2_idx), (v1_idx, v2_idx) in vor.ridge_dict.items():

        # 1. Color Check: Skip if both cones are the same color
        if colors[p1_idx] == colors[p2_idx]:
            continue

        # Check for infinite ridges (open ends)
        if v1_idx == -1 or v2_idx == -1:
            continue

        # Get the actual physical 2D points of the voronoi vertices
        p_start = vor.vertices[v1_idx]
        p_end = vor.vertices[v2_idx]

        # 2. Distance Check: Prune edges that are too long
        dist = np.linalg.norm(p_start - p_end)
        if dist > max_edge_len:
            continue

<<<<<<< HEAD
        # 3. Collision Check: Ensure edge doesn't collide with cones
        #collision_detected = is_collision(
         #   p_start[0], p_start[1],    
           # p_end[0], p_end[1],
           # effective_radius,
           # obstacle_tree,
           # max_edge_len
         #)
        
        #if collision_detected:
          #  continue  # Skip this edge if collision detected
=======
        """"   # 3. Collision Check: Ensure edge doesn't collide with cones
        collision_detected = is_collision(
            p_start[0], p_start[1],
            p_end[0], p_end[1],
            effective_radius,
            obstacle_tree,
            max_edge_len
        )
       
        if collision_detected:
            continue  # Skip this edge if collision detected
        """


>>>>>>> 3b00664610b751b680f44a8d3c76f0a7e9d7d9e5

        # Add to Graph (only if all checks passed)
        G.add_node(v1_idx, pos=p_start)
        G.add_node(v2_idx, pos=p_end)
        G.add_edge(v1_idx, v2_idx, weight=dist)

    return G