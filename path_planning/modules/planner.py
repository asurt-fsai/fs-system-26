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
        # 1. Extract Car Data FIRST
        car_pos = np.array([car_data[0][0], car_data[0][1]])
        car_yaw = car_data[0][2]

        # 2. Check for Low Cones (Startup / Fallback Mode)
        if len(cone_data) < 3:
            return self._handle_low_cones(cone_data, car_pos, car_yaw)

        # 3. Balance Uneven Cones
        # Updated to use your new local tangent parameters
        balanced_cone_data = self._balance_uneven_cones(
            cone_data,
            car_x=car_pos[0],
            car_y=car_pos[1],
            car_yaw=car_yaw,
            virtual_width=3.5,
            pairing_radius=5.5
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

    def _handle_low_cones(self, cone_data, car_pos, car_yaw):
        """
        Handles 1 or 2 cones by inferring the missing data.
        """
        print(f"Low cones detected ({len(cone_data)}). Using fallback logic.")
        
        ASSUMED_WIDTH = 3
        target_point = None
        
        if len(cone_data) == 2:
            c1 = np.array([cone_data[0][0], cone_data[0][1]])
            c2 = np.array([cone_data[1][0], cone_data[1][1]])
            target_point = (c1 + c2) / 2.0
            
        elif len(cone_data) == 1:
            cone_x, cone_y, color = cone_data[0]
            cone_pos = np.array([cone_x, cone_y])
            right_vec = np.array([np.sin(car_yaw), -np.cos(car_yaw)])
            
            if color == 'b': 
                target_point = cone_pos + (right_vec * (ASSUMED_WIDTH / 2.0))
            elif color == 'y': 
                target_point = cone_pos - (right_vec * (ASSUMED_WIDTH / 2.0))
        
        if target_point is not None:
            direction = target_point - car_pos
            length = np.linalg.norm(direction)
            if length > 0:
                direction = direction / length
                extension = target_point + direction * 3.0
                return [tuple(car_pos), tuple(target_point), tuple(extension)]
        
        return []

    def _balance_uneven_cones(self, cone_data, car_x, car_y, car_yaw, virtual_width=3.5, pairing_radius=5.5):
        """
        New Local Tangent Logic: Projects virtual partners perpendicular to the wall slope.
        """
        forward_vec = np.array([np.cos(car_yaw), np.sin(car_yaw)])
        yellows = [c for c in cone_data if c[2] == 'y']
        blues = [c for c in cone_data if c[2] == 'b']
        balanced = list(cone_data)

        # Mapping: if yellow, opposites are blue and we project left (sign -1)
        # if blue, opposites are yellow and we project right (sign 1)
        for color, opposites, sign in [('y', blues, -1), ('b', yellows, 1)]:
            current_wall = [c for c in cone_data if c[2] == color]
        
            for i, cone in enumerate(current_wall):
                cone_pos = np.array([cone[0], cone[1]])
            
                # 1. Forward Filter: Only process cones in front of the car
                if np.dot(cone_pos - np.array([car_x, car_y]), forward_vec) < 0:
                    continue
                
                # 2. Radius Check: Only add partner if one doesn't exist within range
                has_partner = any(np.linalg.norm(cone_pos - np.array([p[0], p[1]])) <= pairing_radius for p in opposites)
            
                if not has_partner:
                    # 3. LOCAL TANGENT CALCULATION
                    if len(current_wall) > 1:
                        # Use neighbor to find wall slope
                        neighbor_idx = (i + 1) if i < len(current_wall)-1 else (i - 1)
                        neighbor_pos = np.array([current_wall[neighbor_idx][0], current_wall[neighbor_idx][1]])
                    
                        # Wall Vector (Tangent)
                        tangent = (neighbor_pos - cone_pos).astype(float)
                        
                        # Normal Vector: Rotate tangent 90 degrees
                        # This creates a vector perpendicular to the wall
                        local_normal = np.array([-tangent[1], tangent[0]])
                        
                        # Normalize the vector
                        norm = np.linalg.norm(local_normal)
                        if norm > 0:
                            local_normal /= norm
                    else:
                        # Fallback to car's right vector if it's the only cone seen
                        local_normal = np.array([np.sin(car_yaw), -np.cos(car_yaw)])

                    # 4. Project using Local Normal
                    v_pos = cone_pos + (sign * local_normal * virtual_width)
                    balanced.append((float(v_pos[0]), float(v_pos[1]), 'b' if color == 'y' else 'y', True))
                
        return balanced