"""
Main path planner module that orchestrates the planning pipeline.
"""

import numpy as np
from . import voronoi_gen
from . import filters
from . import graph_search
from .smoothing import smooth_path_bspline


class PathPlanner:
    def __init__(self, robot_radius=1.5, safety_margin=0.5, max_edge_len=3.0):
        """
        Initialize the path planner with configuration parameters.
        
        :param robot_radius: Effective radius of the vehicle
        :param safety_margin: Additional safety buffer
        :param max_edge_len: Maximum edge length for graph connections
        """
        self.robot_radius = robot_radius
        self.safety_margin = safety_margin
        self.max_edge_len = max_edge_len

    def execute_cycle(self, cone_data, car_data):
        """
        Main pipeline function.
        
        Args:
            cone_data: [(x, y, color), ...]
            car_data: [(x, y, orientation)]
            
        Returns:
            List of (x, y) tuples representing the smoothed path
        """
        # 1. Extract Car Data
        car_pos = np.array([car_data[0][0], car_data[0][1]])
        car_yaw = car_data[0][2]

        # 2. Module 1: Generate Voronoi
        points, colors, vor = voronoi_gen.generate_voronoi(cone_data)

        if vor is None:
            print("Not enough cones to plan.")
            return []

        # 3. Module 2: Build Safe Graph (Filter, Prune, and Collision Check)
        safe_graph = filters.build_safe_graph(
            vor, 
            colors, 
            cone_data,
            robot_radius=self.robot_radius,
            max_edge_len=self.max_edge_len,
            safety_margin=self.safety_margin
        )
        
        print(f"Graph has {len(safe_graph.nodes)} nodes and {len(safe_graph.edges)} edges")

        # 4. Module 3: Search Graph
        path = graph_search.find_optimal_path(safe_graph, car_pos, car_yaw)

        # If no path was found, return an empty path immediately
        if not path:
            print("No path found.")
            return []

        # 5. Module 4: Smoothing
        rx = [p[0] for p in path]
        ry = [p[1] for p in path]
        smoothed_x, smoothed_y = smooth_path_bspline(rx, ry)

        # Return list of smoothed points as tuples
        smoothed_path = list(zip(smoothed_x, smoothed_y))
       
        return smoothed_path