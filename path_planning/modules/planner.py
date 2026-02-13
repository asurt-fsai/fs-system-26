import numpy as np
from . import voronoi_gen
from . import filters
from . import graph_search
from .filters import remove_ghost_cones
from .smoothing import smooth_path_bspline, smooth_path_line


class PathPlanner:
    def __init__(
            self,
            robot_radius=0.7,
            safety_margin=0.4,
            max_edge_len=8.0,
    ):
        """
        Initialize the path planner with configuration parameters.
        """
        self.robot_radius = robot_radius
        self.safety_margin = safety_margin
        self.max_edge_len = max_edge_len

    def execute_cycle(self, cone_data, car_data):
        """
        Main pipeline function.
        """
        # 1. Extract Car Data FIRST (So we can use it for low-cone logic)
        car_pos = np.array([car_data[0][0], car_data[0][1]])
        car_yaw = car_data[0][2]

        # 2. Check for Low Cones (Startup / Fallback Mode)
        if len(cone_data) < 3:
            return self._handle_low_cones(cone_data, car_pos, car_yaw)

        # 3. Remove Ghost Cones
        # Count original colors
        orig_y = sum(1 for c in cone_data if c[2] == 'y')
        orig_b = sum(1 for c in cone_data if c[2] == 'b')
        original_cones = list(cone_data)

        # Run the filter
        cone_data = remove_ghost_cones(cone_data)

        # Count remaining colors
        new_y = sum(1 for c in cone_data if c[2] == 'y')
        new_b = sum(1 for c in cone_data if c[2] == 'b')

        # Identify which specific cones were removed
        removed = [c for c in original_cones if c not in cone_data]

        if removed:
            print("\n--- GHOST FILTER SUMMARY ---")
            print(f"Yellow Cones: {orig_y} -> {new_y} (Removed: {orig_y - new_y})")
            print(f"Blue Cones:   {orig_b} -> {new_b} (Removed: {orig_b - new_b})")
            print("Specific cones removed:")
            for r in removed:
                print(f" >> {r[2]} cone at ({r[0]:.2f}, {r[1]:.2f})")
            print("---------------------------\n")

        # 5. Module 1: Generate Voronoi
        points, colors, vor = voronoi_gen.generate_voronoi(cone_data)

        if vor is None:
            print("Voronoi generation failed. Switching to fallback.")
            return self._handle_low_cones(cone_data, car_pos, car_yaw)

        # 6. Module 2: Build Safe Graph
        midpoint_nodes = []  # IMPORTANT: empty for now

        safe_graph = filters.build_safe_graph(
            vor,
            colors,
            midpoint_nodes,
            cone_data,
            self.max_edge_len
        )

        # 7. Module 3: Search Graph
        path = graph_search.find_optimal_path(safe_graph, car_pos, car_yaw)

        if not path:
            print("No path found.")
            return []

        # 8. Module 4: Smoothing
        rx = [p[0] for p in path]
        ry = [p[1] for p in path]
        try:
            yellow_count = sum(1 for c in cone_data if c[2] == 'y')
            blue_count = sum(1 for c in cone_data if c[2] == 'b')
            if min(yellow_count, blue_count) < 2:
                straight_x, straight_y = smooth_path_line(rx, ry, num_points=max(len(rx), 10))
                return list(zip(straight_x, straight_y))
            else:
                smoothed_x, smoothed_y = smooth_path_bspline(rx, ry)
                return list(zip(smoothed_x, smoothed_y))
        except:
            return path

    # --- HELPER METHODS (Must be indented INSIDE the class) ---

    def _handle_low_cones(self, cone_data, car_pos, car_yaw):
        """
        Handles 1 or 2 cones by inferring the missing data.
        """
        print(f"Low cones detected ({len(cone_data)}). Using fallback logic.")

        ASSUMED_WIDTH = 3
        target_point = None

        # CASE 1: 2 Cones
        if len(cone_data) == 2:
            c1 = np.array([cone_data[0][0], cone_data[0][1]])
            c2 = np.array([cone_data[1][0], cone_data[1][1]])
            target_point = (c1 + c2) / 2.0

        # CASE 2: 1 Cone
        elif len(cone_data) == 1:
            cone_x, cone_y, color = cone_data[0]
            cone_pos = np.array([cone_x, cone_y])

            # Vector pointing right relative to car
            right_vec = np.array([np.sin(car_yaw), -np.cos(car_yaw)])

            if color == 'b':  # Blue -> Path is to the Right
                target_point = cone_pos + (right_vec * (ASSUMED_WIDTH / 2.0))
            elif color == 'y':  # Yellow -> Path is to the Left
                target_point = cone_pos - (right_vec * (ASSUMED_WIDTH / 2.0))

        if target_point is not None:
            direction = target_point - car_pos
            length = np.linalg.norm(direction)
            if length > 0:
                direction = direction / length
                extension = target_point + direction * 3.0
                return [tuple(car_pos), tuple(target_point), tuple(extension)]

        return []

