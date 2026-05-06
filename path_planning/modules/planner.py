from math import dist
import numpy as np
from . import voronoi_gen
from . import filters
from . import graph_search
from .filters import remove_ghost_cones
from .smoothing import smooth_path_bspline
from .virtual_cones import VirtualCones 

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
        
        
        # --- NEW: Instantiate the VirtualCones module ---
        self.virtual_cone_generator = VirtualCones(
            virtual_width=4.0, 
            pairing_threshold=15.0, 
            collision_threshold=2.5
        )

    def execute_cycle(self, cone_data, car_data):
        """
        Main pipeline function.
        """
        # 1. Extract Car Data FIRST
        car_pos = np.array([car_data[0][0], car_data[0][1]])
        car_yaw = car_data[0][2]

        # 2. Check for Low Cones (Startup / Fallback Mode)
        print ("iam seeing now " + str(len(cone_data)) + " cones")
        if len(cone_data) < 3:
            self.last_balanced_cones = cone_data
            self.last_virtual_cones = []
            return self._handle_low_cones(cone_data, car_pos, car_yaw)

        # 3. Ghost cones logic (currently commented out in your original)
        # cone_data = remove_ghost_cones(cone_data)

        # 4. Virtual cones logic - DELEGATED TO THE NEW CLASS
        balanced_cone_data, midpoint_nodes = self.virtual_cone_generator.generate_balanced_cones(
             cone_data, car_pos, car_yaw
         )

        # 5. Module 1: Generate Voronoi
        points, colors, vor = voronoi_gen.generate_voronoi(balanced_cone_data)

        if vor is None:
            print("Voronoi generation failed. Switching to fallback.")
            return self._handle_low_cones(cone_data, car_pos, car_yaw)
        
        # 6. Module 2: Build Safe Graph
        safe_graph = filters.build_safe_graph(
            vor,
            colors,
            midpoint_nodes ,
            cone_data = balanced_cone_data,  # Use the balanced cone data for safety checks
            max_edge_len=self.max_edge_len
        )

        # 7. Module 3: Search Graph
        path = graph_search.find_optimal_path(safe_graph, car_pos, car_yaw)

        if not path:
            print("No path found.")
            return []

        # 8. Module 4: Smoothing
        # rx = [p[0] for p in path]
        # ry = [p[1] for p in path]

        # try:
        #     smoothed_x, smoothed_y = smooth_path_bspline(rx, ry)
        #     return list(zip(smoothed_x, smoothed_y))
        # except Exception as e:
        #     print(f"Smoothing failed ({e}), returning raw path")
        #     return path
            
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
            color1, color2 = cone_data[0][2], cone_data[1][2]
            
            if color1 != color2:
                # Different colors - use midpoint logic
                target_point = (c1 + c2) / 2.0
            else:
                # Same color - use same logic as 1 cone
                cone_pos = (c1 + c2) / 2.0  # Use midpoint as reference
                right_vec = np.array([np.sin(car_yaw), -np.cos(car_yaw)])
                
                if color1 == 'b':  # Blue -> Path is to the Right
                    target_point = cone_pos + (right_vec * (ASSUMED_WIDTH / 2.0))
                elif color1 == 'y':  # Yellow -> Path is to the Left
                    target_point = cone_pos - (right_vec * (ASSUMED_WIDTH / 2.0))

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
            if length > 0.5:  # Require at least 0.5m distance
                direction = direction / length
                extension = target_point + direction * 3.0
                return [tuple(car_pos), tuple(target_point), tuple(extension)]
            else:
                # Car is AT the target, use car's heading to go forward
                forward_vec = np.array([np.cos(car_yaw), np.sin(car_yaw)])
                p1 = car_pos + forward_vec * 3.0
                p2 = car_pos + forward_vec * 8.0
                return [tuple(car_pos), tuple(p1), tuple(p2)]

        return []