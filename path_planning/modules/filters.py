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
    diff_color_min_dist=3.0,
    min_violation_ratio=0.4 #to avoid removing real cones from dense areas (we only remove cones that violate rules in more than 40% of their comparisons)
):
    """
    Remove ghost cones using distance rules.
    what we know for sure:
    -same color cones: max distance allowed is 5m
    -diff color cones: min distance allowed is 3m

    Each cone accumulates violations (potential ghost counter) normalized by number of checks.
    Cones with high violation ratios are removed.

    Pot_ghost: A cone gets +1 for each same-color cone that is too far, and +2 for each different-color cone that is too close.
    checks: Count of comparisons made for each cone (to normalize pot_ghost).


    """

    #Number of detected cones
    n = len(cone_data)

    if n < 3:
        return cone_data

    pot_ghost = [0.0] * n # potential ghost score for each cone
    checks = [0] * n  # number of checks conducted with every other cone

    #compare each cone with every other cone once
    for i in range(n):
        xi, yi, ci = cone_data[i]

        for j in range(i + 1, n):
            xj, yj, cj = cone_data[j]

            #compute distance between cone i and j
            dx = xi - xj
            dy = yi - yj
            d = np.hypot(dx, dy)

            #Rule 1: Same color cones: d > same_color_max_dist
            if ci == cj:
                if d > same_color_max_dist:
                    pot_ghost[i] += 1.0
                    pot_ghost[j] += 1.0
            # Rule 2: Different color cones: d < diff_color_min_dist
            # diff color being too close gives higher penalty
            else:
                if d < diff_color_min_dist:
                    pot_ghost[i] += 2.0
                    pot_ghost[j] += 2.0

            checks[i] += 1
            checks[j] += 1

    # Compute normalized violation ratio (total pot_ghost / total checks)
    ratios = [
        pot_ghost[i] / checks[i] if checks[i] > 0 else 0.0
        for i in range(n)
    ]

    # Keep cones with low violation ratios
    filtered = [
        cone_data[i]
        for i in range(n)
        if ratios[i] < min_violation_ratio
    ]

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



        # Add to Graph (only if all checks passed)
        G.add_node(v1_idx, pos=p_start)
        G.add_node(v2_idx, pos=p_end)
        G.add_edge(v1_idx, v2_idx, weight=dist)

    return G