# path_planning/graph_search.py
import networkx as nx
import numpy as np


def find_optimal_path(graph, car_pos, car_orientation):
    """
    Finds the path from the car to the furthest node.
    
    steps:
    - Finds the closest node on the graph.
    - Adds the actual car position to the path so the path starts from the car.
    - Uses Dijkstra's algorithm to find the shortest path to the furthest node.
    - Returns a list of (x, y) coordinates representing the path.
    """

    if len(graph.nodes) == 0:
        return []

    #  1. Find Start Node (Closest to Car)
    start_node = None
    min_dist = float('inf')  # initialize to infinity

    for node_id in graph.nodes:
        pos = graph.nodes[node_id]['pos']
        dist = np.linalg.norm(pos - car_pos)
        if dist < min_dist:
            min_dist = dist
            start_node = node_id

    if start_node is None:
        return []

    # 2. Find End Node
    # Dijkstra to find furthest node from start_node
    path_lengths = nx.single_source_dijkstra_path_length(graph, start_node)
    end_node = max(path_lengths, key=path_lengths.get)

    #  3. Retrieve Path
    try:
        # Get the list of Node IDs 
        path_indices = nx.shortest_path(graph, start_node, end_node)

        # Convert Node IDs to actual (x, y) coordinates
        graph_path_points = [graph.nodes[i]['pos'] for i in path_indices]

        # Prepend the actual car position to the path
        final_path = [car_pos] + graph_path_points

        return final_path

    except nx.NetworkXNoPath:
        return []