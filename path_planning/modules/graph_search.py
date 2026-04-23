import networkx as nx   
import numpy as np

# def find_optimal_path(graph, car_pos, car_orientation):
#     print(f"[SEARCH DEBUG] Graph initialized with {len(graph.nodes)} nodes and {len(graph.edges)} edges.")
#     if len(graph.nodes) == 0:
#         print("[SEARCH FAIL] Graph is empty. No nodes survive filtering.")
#         return []


#     # 1. Find the Start Node
#     start_node = None
#     min_dist = float('inf')
#     for node_id in graph.nodes:
#         pos = graph.nodes[node_id]['pos']
#         dist = np.linalg.norm(pos - car_pos)
#         if dist < min_dist:
#             min_dist = dist
#             start_node = node_id

#     print(f"[SEARCH DEBUG] Car is {min_dist:.2f}m away from the nearest graph node.")

#     if min_dist > 15.0: # Increased threshold for sparse slaloms
#         print(f"[SEARCH FAIL] Car too far from track ({min_dist:.2f}m > 15m).")
#         return []

#     try:
#         # 2. Check for Reachability
#         path_lengths = nx.single_source_dijkstra_path_length(graph, start_node)

#         print(f"[SEARCH DEBUG] Reachable nodes from car: {len(path_lengths)} / Total nodes: {len(graph.nodes)}")
        
#         if len(path_lengths) <= 1:
#             print(f"[SEARCH FAIL] Start node {start_node} has NO neighbors. Check max_edge_len.")
#             return []

#         # Find the furthest reachable node
#         end_node = max(path_lengths, key=path_lengths.get)
#         path_indices = nx.shortest_path(graph, start_node, end_node, weight='weight')
        
#         print(f"[SEARCH SUCCESS] Path Found! Length: {len(path_indices)} nodes.")
        
#         # Return path starting from car position
#         final_path = [tuple(car_pos)] + [tuple(graph.nodes[i]['pos']) for i in path_indices]
        
#         return final_path

#     except nx.NetworkXNoPath:
#         print("[SEARCH FAIL] No connection between start and furthest node.")
#         return []

#FORWORD CLOSEST POINT NO DEGREE LIMIT (HANA)
# def find_optimal_path(graph, car_pos, car_orientation, forward_bias_angle=90):
#     print(f"[SEARCH DEBUG] Graph initialized with {len(graph.nodes)} nodes and {len(graph.edges)} edges.")
#     if len(graph.nodes) == 0:
#         print("[SEARCH FAIL] Graph is empty.")
#         return []

#     car_forward = np.array([np.cos(car_orientation), np.sin(car_orientation)])
    
#     # ── NEW: Build a forward-only subgraph ──────────────────────────────────
#     # Discard any node that lies behind the car before we even search.
#     # "Behind" = angle to node > forward_bias_angle degrees from heading.
#     cos_thresh = np.cos(np.radians(forward_bias_angle))  # e.g. cos(90°) = 0.0

#     forward_nodes = []
#     for node_id in graph.nodes:
#         pos = np.array(graph.nodes[node_id]['pos'])
#         to_node = pos - car_pos
#         dist = np.linalg.norm(to_node)

#         if dist < 0.01:          # car is sitting on the node — keep it
#             forward_nodes.append(node_id)
#             continue

#         cos_angle = np.dot(to_node / dist, car_forward)
#         if cos_angle >= cos_thresh:   # node is within the forward cone
#             forward_nodes.append(node_id)

#     if not forward_nodes:
#         print("[SEARCH FAIL] No nodes found in forward cone.")
#         return []

#     # Work on the subgraph — Dijkstra stays inside the forward cone
#     sub = graph.subgraph(forward_nodes)
#     print(f"[SEARCH DEBUG] Forward-cone nodes: {len(forward_nodes)} / {len(graph.nodes)}")
#     # ── END NEW ─────────────────────────────────────────────────────────────

#     # 1. Find the closest forward node as the start
#     start_node = None
#     min_dist = float('inf')

#     for node_id in sub.nodes:
#         pos = np.array(sub.nodes[node_id]['pos'])
#         dist = np.linalg.norm(pos - car_pos)
#         if dist < min_dist:
#             min_dist = dist
#             start_node = node_id

#     if start_node is None:
#         print("[SEARCH FAIL] No start node found.")
#         return []

#     print(f"[SEARCH DEBUG] Nearest forward node is {min_dist:.2f}m away.")

#     if min_dist > 15.0:
#         print(f"[SEARCH FAIL] Car too far from track ({min_dist:.2f}m > 15m).")
#         return []

#     try:
#         path_lengths = nx.single_source_dijkstra_path_length(sub, start_node)
#         print(f"[SEARCH DEBUG] Reachable nodes: {len(path_lengths)} / {len(sub.nodes)}")

#         if len(path_lengths) <= 1:
#             print(f"[SEARCH FAIL] Start node {start_node} has no neighbours in forward cone.")
#             return []

#         end_node = max(path_lengths, key=path_lengths.get)
#         path_indices = nx.shortest_path(sub, start_node, end_node, weight='weight')

#         print(f"[SEARCH SUCCESS] Path found — {len(path_indices)} nodes.")

#         return [tuple(car_pos)] + [tuple(sub.nodes[i]['pos']) for i in path_indices]

#     except nx.NetworkXNoPath:
#         print("[SEARCH FAIL] No connection between start and end node.")
#         return []


# FORWORD PATH FORWORD CLOSED POINT (90 DEGREE)(RUBA)
# def find_optimal_path(graph, car_pos, car_orientation):
#     print(f"[SEARCH DEBUG] Graph initialized with {len(graph.nodes)} nodes and {len(graph.edges)} edges.")
#     if len(graph.nodes) == 0:
#         print("[SEARCH FAIL] Graph is empty. No nodes survive filtering.")
#         return []

#     # 1. Find the Start Node (filtering cones behind the car)
#     start_node = None
#     min_dist = float('inf')

#     # Car's forward direction vector
#     car_forward = np.array([np.cos(car_orientation), np.sin(car_orientation)])

#     for node_id in graph.nodes:
#         pos = np.array(graph.nodes[node_id]['pos'])
#         to_node = pos - car_pos
#         dist = np.linalg.norm(to_node)

#         # Check if the node is ahead of the car (dot product > 0 means same direction)
#         is_ahead = np.dot(to_node, car_forward) > 0

#         if is_ahead and dist < min_dist:
#             min_dist = dist
#             start_node = node_id

#     if start_node is None:
#         print("[SEARCH FAIL] No nodes found ahead of the car. All cones are behind.")
#         return []

#     print(f"[SEARCH DEBUG] Car is {min_dist:.2f}m away from the nearest graph node.")

#     if min_dist > 15.0:
#         print(f"[SEARCH FAIL] Car too far from track ({min_dist:.2f}m > 15m).")
#         return []

#     try:
#         # 2. Check for Reachability
#         path_lengths = nx.single_source_dijkstra_path_length(graph, start_node)

#         print(f"[SEARCH DEBUG] Reachable nodes from car: {len(path_lengths)} / Total nodes: {len(graph.nodes)}")

#         if len(path_lengths) <= 1:
#             print(f"[SEARCH FAIL] Start node {start_node} has NO neighbors. Check max_edge_len.")
#             return []

#         # Find the furthest reachable node
#         end_node = max(path_lengths, key=path_lengths.get)
#         path_indices = nx.shortest_path(graph, start_node, end_node, weight='weight')

#         print(f"[SEARCH SUCCESS] Path Found! Length: {len(path_indices)} nodes.")

#         # Return path starting from car position
#         final_path = [tuple(car_pos)] + [tuple(graph.nodes[i]['pos']) for i in path_indices]

#         return final_path

#     except nx.NetworkXNoPath:
#         print("[SEARCH FAIL] No connection between start and furthest node.")
#         return []

 

 #filtering also max distance and angle to end node (RUBA)
import numpy as np
import networkx as nx

def find_optimal_path(graph, car_pos, car_orientation, max_path_dist=20.0, max_end_angle=110.0):
    """
    Finds a path from the car to the furthest logical point on the track.
    
    :param graph: NetworkX graph representing the track midpoints/nodes
    :param car_pos: (x, y) coordinates of the car
    :param car_orientation: Yaw in radians
    :param max_path_dist: Maximum track-distance to look ahead (prevents targeting noise)
    :param max_end_angle: Maximum angle (degrees) from heading for the end node
    """
    if len(graph.nodes) == 0:
        print("[SEARCH FAIL] Graph is empty.")
        return []

    # 1. Create Heading Vector
    car_forward = np.array([np.cos(car_orientation), np.sin(car_orientation)])
    car_pos = np.array(car_pos)

    # 2. Find the Start Node (Closest node physically in front of the car)
    start_node = None
    min_dist = float('inf')

    for node_id in graph.nodes:
        pos = np.array(graph.nodes[node_id]['pos'])
        to_node = pos - car_pos
        dist = np.linalg.norm(to_node)

        # Dot product > 0 means the node is in the forward 180-degree hemisphere
        is_ahead = np.dot(to_node, car_forward) > 0

        if is_ahead and dist < min_dist:
            min_dist = dist
            start_node = node_id

    if start_node is None:
        print("[SEARCH FAIL] No nodes found ahead of the car.")
        return []

    if min_dist > 15.0:
        print(f"[SEARCH FAIL] Nearest node too far ({min_dist:.2f}m).")
        return []

    try:
        # 3. Calculate all reachable paths from start_node using Dijkstra
        path_lengths = nx.single_source_dijkstra_path_length(graph, start_node, weight='weight')

        # 4. Filter for a "Trusted" End Node
        # We want a node that is:
        # a) Reachable via the graph
        # b) Within a reasonable track distance (max_path_dist)
        # c) Within a reasonable field of view (max_end_angle)
        
        cos_thresh = np.cos(np.radians(max_end_angle))
        trusted_nodes = {}

        for node_id, track_dist in path_lengths.items():
            node_pos = np.array(graph.nodes[node_id]['pos'])
            vec_to_node = node_pos - car_pos
            direct_dist = np.linalg.norm(vec_to_node)
            
            # Avoid division by zero for nodes sitting on the car
            if direct_dist < 0.1:
                cos_angle = 1.0 
            else:
                cos_angle = np.dot(vec_to_node / direct_dist, car_forward)

            if track_dist <= max_path_dist and cos_angle >= cos_thresh:
                trusted_nodes[node_id] = track_dist

        if not trusted_nodes:
            print("[SEARCH FAIL] No nodes satisfied the trusted look-ahead criteria.")
            return []

        # 5. Select the furthest node within the trusted set
        end_node = max(trusted_nodes, key=trusted_nodes.get)
        
        # 6. Generate the actual path of coordinates
        path_indices = nx.shortest_path(graph, start_node, end_node, weight='weight')
        
        # Convert indices back to (x, y) coordinates
        path_coords = [tuple(car_pos)] # Start with current car position
        for i in path_indices:
            path_coords.append(tuple(graph.nodes[i]['pos']))

        print(f"[SEARCH SUCCESS] Path found with {len(path_coords)} points.")
        return path_coords

    except nx.NetworkXNoPath:
        print("[SEARCH FAIL] No connection found in the graph.")
        return []
    except Exception as e:
        print(f"[SEARCH ERROR] {e}")
        return []