import numpy as np
from . import voronoi_gen
from . import filters
from . import graph_search
from .smoothing import smooth_path_bspline

class PathPlanner:
    def __init__(self, robot_radius=0.7, safety_margin=0.4, max_edge_len=8.0):
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

        # 3. Balance Uneven Cones (Add ghosts if one side is missing)
        # Note: We call the helper method defined below
        balanced_cone_data = self._balance_uneven_cones(
            cone_data,
            car_yaw=car_yaw,
            virtual_width=3.0
        )

        # 4. Module 1: Generate Voronoi
        points, colors, vor = voronoi_gen.generate_voronoi(balanced_cone_data)

        if vor is None:
            print("Voronoi generation failed. Switching to fallback.")
            return self._handle_low_cones(cone_data, car_pos, car_yaw)

        # 5. Module 2: Build Safe Graph
        safe_graph = filters.build_safe_graph(
            vor, 
            colors, 
            balanced_cone_data,
            robot_radius=self.robot_radius,
            max_edge_len=self.max_edge_len,
            safety_margin=self.safety_margin
        )
        
        # 6. Module 3: Search Graph
        path = graph_search.find_optimal_path(safe_graph, car_pos, car_yaw)

        if not path:
            print("No path found.")
            return []

        # 7. Module 4: Smoothing
        rx = [p[0] for p in path]
        ry = [p[1] for p in path]
        try:
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
            
            if color == 'b': # Blue -> Path is to the Right
                target_point = cone_pos + (right_vec * (ASSUMED_WIDTH / 2.0))
            elif color == 'y': # Yellow -> Path is to the Left
                target_point = cone_pos - (right_vec * (ASSUMED_WIDTH / 2.0))
        
        if target_point is not None:
            direction = target_point - car_pos
            length = np.linalg.norm(direction)
            if length > 0:
                direction = direction / length
                extension = target_point + direction * 3.0
                return [tuple(car_pos), tuple(target_point), tuple(extension)]
        
        return []

    def _balance_uneven_cones(self, cone_data, car_yaw, virtual_width=3.0, pairing_threshold=2.0):
        """
        Improved balance: Checks if each cone has a partner within 'pairing_threshold' 
        meters of longitudinal distance (X-axis).
        """
        yellow_cones = sorted([c for c in cone_data if c[2] == 'y'], key=lambda x: x[0])
        blue_cones = sorted([c for c in cone_data if c[2] == 'b'], key=lambda x: x[0])
    
        balanced_cones = list(cone_data)
        right_vec = np.array([np.sin(car_yaw), -np.cos(car_yaw)])

    # Check for lonely Yellow cones
        for y in yellow_cones:
        # Look for ANY blue cone that is roughly at the same X-distance
            has_partner = any(abs(y[0] - b[0]) <= pairing_threshold for b in blue_cones)
        
            if not has_partner:
            # Create a virtual blue cone opposite this lonely yellow one
                y_pos = np.array([y[0], y[1]])
                virtual_blue = y_pos - right_vec * virtual_width
                balanced_cones.append((virtual_blue[0], virtual_blue[1], 'b'))
                print(f"Adding virtual Blue partner for Yellow at x={y[0]}")

    # Check for lonely Blue cones
        for b in blue_cones:
        # Look for ANY yellow cone that is roughly at the same X-distance
            has_partner = any(abs(b[0] - y[0]) <= pairing_threshold for y in yellow_cones)
        
            if not has_partner:
            # Create a virtual yellow cone opposite this lonely blue one
                b_pos = np.array([b[0], b[1]])
                virtual_yellow = b_pos + right_vec * virtual_width
                balanced_cones.append((virtual_yellow[0], virtual_yellow[1], 'y'))
                print(f"Adding virtual Yellow partner for Blue at x={b[0]}")

        return balanced_cones