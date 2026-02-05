import networkx as nx
import numpy as np

def is_edge_safe(p1, p2, cone_data, safe_dist=1.5):
    """
    Checks if a line segment between p1 and p2 passes too close to any cone.
    """
    p1 = np.array(p1)
    p2 = np.array(p2)
    for cone in cone_data:
        c_pos = np.array([cone[0], cone[1]])
        
        # Vector from p1 to p2
        line_vec = p2 - p1
        line_len_sq = np.sum(line_vec**2)
        if line_len_sq == 0: continue
        
        # Projection of cone onto the line
        t = max(0, min(1, np.dot(c_pos - p1, line_vec) / line_len_sq))
        projection = p1 + t * line_vec
        
        # Distance from cone to the closest point on the segment
        dist_to_cone = np.linalg.norm(c_pos - projection)
        if dist_to_cone < safe_dist:
            return False
    return True

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

def build_safe_graph(vor, colors, midpoint_nodes, cone_data, max_edge_len):
    """
    Builds a graph using Voronoi ridges and manual gate centers,
    filtering out edges that pass through cones.
    """
    G = nx.Graph()
    
    # --- PART A: Voronoi Ridges ---
    for (p1_idx, p2_idx), (v1_idx, v2_idx) in vor.ridge_dict.items():
        if colors[p1_idx] == colors[p2_idx]: continue
        
        # Infinite Ridge Handling
        if v1_idx == -1 or v2_idx == -1:
            c1, c2 = np.array(vor.points[p1_idx]), np.array(vor.points[p2_idx])
            gate_mid = (c1 + c2) / 2.0
            v_fin = v2_idx if v1_idx == -1 else v1_idx
            if v_fin != -1:
                p_fin = vor.vertices[v_fin]
                if np.linalg.norm(gate_mid - p_fin) <= max_edge_len:
                    if is_edge_safe(gate_mid, p_fin, cone_data):
                        node_id = f"inf_{p1_idx}_{p2_idx}"
                        G.add_node(node_id, pos=gate_mid)
                        G.add_node(v_fin, pos=p_fin)
                        G.add_edge(node_id, v_fin, weight=np.linalg.norm(gate_mid - p_fin))
            continue

        # Standard Finite Ridges
        p1, p2 = vor.vertices[v1_idx], vor.vertices[v2_idx]
        dist = np.linalg.norm(p1 - p2)
        if dist <= max_edge_len and is_edge_safe(p1, p2, cone_data):
            G.add_node(v1_idx, pos=p1)
            G.add_node(v2_idx, pos=p2)
            G.add_edge(v1_idx, v2_idx, weight=dist)

    # --- PART B: Manual Midpoints (Gate Centers) ---
    for i, mp in enumerate(midpoint_nodes):
        node_id = f"mid_{i}"
        mp_pos = np.array(mp)
        G.add_node(node_id, pos=mp_pos)
        
        for v_idx in G.nodes:
            if isinstance(v_idx, str) and "mid" in v_idx: continue
            v_pos = G.nodes[v_idx]['pos']
            dist = np.linalg.norm(mp_pos - v_pos)
            # Only connect if the edge doesn't cross a cone
            if dist < max_edge_len and is_edge_safe(mp_pos, v_pos, cone_data):
                G.add_edge(node_id, v_idx, weight=dist)
                
    return G