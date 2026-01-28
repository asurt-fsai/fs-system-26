# path_planning/modules/planner.py
import numpy as np

# Importing our custom modules
from . import voronoi_gen
from . import filters
from . import graph_search


class PathPlanner:
    def execute_cycle(self, cone_data, car_data):
        """
        Main pipeline function.
        Args:
            cone_data: [(x, y, color), ...]
            car_data: [(x, y, orientation)]
        """
        # 1.  Car Data
        car_pos = np.array([car_data[0][0], car_data[0][1]])
        car_yaw = car_data[0][2]

        # 2. Module 1: Generate Voronoi
        points, colors, vor = voronoi_gen.generate_voronoi(cone_data)

        if vor is None:
            print("Not enough cones to plan.")
            return []

        # 3. Module 2: Build Safe Graph (Filter & Prune)
        safe_graph = filters.build_safe_graph(vor, colors)

        # 4. Module 3: Search Graph
        path = graph_search.find_optimal_path(safe_graph, car_pos, car_yaw)

        return path