import networkx as nx
import numpy as np


def find_optimal_path(graph, car_pos, car_orientation):
    print(f"[SEARCH DEBUG] Graph initialized with {len(graph.nodes)} nodes and {len(graph.edges)} edges.")
    if len(graph.nodes) == 0:
        print("[SEARCH FAIL] Graph is empty. No nodes survive filtering.")
        return []

    # 1. Find the Start Node (filtering cones behind the car)
    start_node = None
    min_dist = float('inf')

    # Car's forward direction vector
    car_forward = np.array([np.cos(car_orientation), np.sin(car_orientation)])

    for node_id in graph.nodes:
        pos = np.array(graph.nodes[node_id]['pos'])
        to_node = pos - car_pos
        dist = np.linalg.norm(to_node)

        # Check if the node is ahead of the car (dot product > 0 means same direction)
        is_ahead = np.dot(to_node, car_forward) > 0

        if is_ahead and dist < min_dist:
            min_dist = dist
            start_node = node_id

    if start_node is None:
        print("[SEARCH FAIL] No nodes found ahead of the car. All cones are behind.")
        return []

    print(f"[SEARCH DEBUG] Car is {min_dist:.2f}m away from the nearest graph node.")

    if min_dist > 15.0:
        print(f"[SEARCH FAIL] Car too far from track ({min_dist:.2f}m > 15m).")
        return []

    try:
        # 2. Check for Reachability
        path_lengths = nx.single_source_dijkstra_path_length(graph, start_node)

        print(f"[SEARCH DEBUG] Reachable nodes from car: {len(path_lengths)} / Total nodes: {len(graph.nodes)}")

        if len(path_lengths) <= 1:
            print(f"[SEARCH FAIL] Start node {start_node} has NO neighbors. Check max_edge_len.")
            return []

        # Find the furthest reachable node
        end_node = max(path_lengths, key=path_lengths.get)
        path_indices = nx.shortest_path(graph, start_node, end_node, weight='weight')

        print(f"[SEARCH SUCCESS] Path Found! Length: {len(path_indices)} nodes.")

        # Return path starting from car position
        final_path = [tuple(car_pos)] + [tuple(graph.nodes[i]['pos']) for i in path_indices]

        return final_path

    except nx.NetworkXNoPath:
        print("[SEARCH FAIL] No connection between start and furthest node.")
        return []