"""
Main path planner module that orchestrates the planning pipeline.
"""

import numpy as np
from . import voronoi_gen
from . import filters
from . import graph_search
from .smoothing import smooth_path_bspline


def balance_uneven_cones(cone_data, virtual_width=3.0):
    """
    Add virtual cones opposite to uneven cone distributions.
    If there are more yellow cones, add virtual blue cones opposite.
    If there are more blue cones, add virtual yellow cones opposite.
    
    Args:
        cone_data: List of (x, y, color) tuples
        virtual_width: Distance in meters to place virtual cones opposite to extra cones
    
    Returns:
        cone_data with virtual cones added
    """
    # Separate yellow and blue cones
    yellow_cones = [c for c in cone_data if c[2] == 'y']
    blue_cones = [c for c in cone_data if c[2] == 'b']
    
    balanced_cones = list(cone_data)
    
    # If more yellow cones, add virtual blue cones
    if len(yellow_cones) > len(blue_cones):
        extra_count = len(yellow_cones) - len(blue_cones)
        
        # Get average y position of existing blue cones to know which side they're on
        if blue_cones:
            blue_avg_y = np.mean([c[1] for c in blue_cones])
        else:
            blue_avg_y = 0
        
        # Add virtual blue cones opposite to extra yellow cones
        for i in range(extra_count):
            # Use positions of first few yellow cones as reference
            ref_yellow = yellow_cones[i % len(yellow_cones)]
            # Place virtual cone at same Y level as existing blue cones, aligned with yellow X
            virtual_cone = (ref_yellow[0], blue_avg_y, 'b')
            balanced_cones.append(virtual_cone)
    
    # If more blue cones, add virtual yellow cones
    elif len(blue_cones) > len(yellow_cones):
        extra_count = len(blue_cones) - len(yellow_cones)
        
        # Get average y position of existing yellow cones to know which side they're on
        if yellow_cones:
            yellow_avg_y = np.mean([c[1] for c in yellow_cones])
        else:
            yellow_avg_y = 0
        
        # Add virtual yellow cones opposite to extra blue cones
        for i in range(extra_count):
            # Use positions of first few blue cones as reference
            ref_blue = blue_cones[i % len(blue_cones)]
            # Place virtual cone at same Y level as existing yellow cones, aligned with blue X
            virtual_cone = (ref_blue[0], yellow_avg_y, 'y')
            balanced_cones.append(virtual_cone)
    
    return balanced_cones


class PathPlanner:
    def __init__(self, robot_radius=0.75, safety_margin=0.5, max_edge_len=8.0):
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
        # 0. Balance uneven cones by adding virtual cones
        balanced_cone_data = balance_uneven_cones(cone_data, virtual_width=3.0)
        
        # 1. Extract Car Data
        car_pos = np.array([car_data[0][0], car_data[0][1]])
        car_yaw = car_data[0][2]

        # 2. Module 1: Generate Voronoi
        points, colors, vor = voronoi_gen.generate_voronoi(balanced_cone_data)

        if vor is None:
            print("Not enough cones to plan.")
            return []

        # 3. Module 2: Build Safe Graph (Filter, Prune, and Collision Check)
        safe_graph = filters.build_safe_graph(
            vor, 
            colors, 
            balanced_cone_data,
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