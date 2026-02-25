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