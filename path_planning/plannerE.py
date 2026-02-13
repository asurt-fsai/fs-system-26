from math import dist
import numpy as np
from . import voronoi_gen
from . import filters
from . import graph_search
from .smoothing import smooth_path_bspline, smooth_path_line
from .filters import remove_ghost_cones


class PathPlanner:
    def __init__(self, robot_radius=0.5, safety_margin=0.2, max_edge_len=8.0):
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

        if len(cone_data) < 3:
            return self._handle_low_cones(cone_data, car_pos, car_yaw)

        # 4. Balance Cones and generate Midpoints and ghost cones
        #cone_data = remove_ghost_cones(cone_data)
        
        balanced_cone_data, midpoint_nodes = self._balance_by_full_mirror(
            cone_data, car_yaw, virtual_width=4.0
        )

        # 5. Module 1: Generate Voronoi
        points, colors, vor = voronoi_gen.generate_voronoi(balanced_cone_data)

        if vor is None:
            print("[SMOOTHING DEBUG] Voronoi failed. Switching to fallback.")
            return self._handle_low_cones(cone_data, car_pos, car_yaw)

        # 6. Module 2: Build Safe Graph (Updated to include midpoints)
        safe_graph = filters.build_safe_graph(
            vor, 
            colors, 
            midpoint_nodes,
            cone_data=balanced_cone_data,
            max_edge_len=self.max_edge_len
        )

        # 7. Module 3: Search Graph
        path = graph_search.find_optimal_path(safe_graph, car_pos, car_yaw)

        if not path:
            print("[SMOOTHING DEBUG] No path found.")
            return []

        # 8. Module 4: Smoothing
        return path

    def _run_smoothing_logic(self, path, cone_data):
        rx = [p[0] for p in path]
        ry = [p[1] for p in path]
        try:
            yellow_count = sum(1 for c in cone_data if c[2] == 'y')
            blue_count = sum(1 for c in cone_data if c[2] == 'b')
            
            if min(yellow_count, blue_count) < 2:
                sx, sy = smooth_path_line(rx, ry, num_points=max(len(rx), 10))
                return list(zip(sx, sy))
            else:
                if len(rx) < 4: return path
                sx, sy = smooth_path_bspline(rx, ry)
                return list(zip(sx, sy))
        except Exception as e:
            print(f"Smoothing Error: {e}")
            return path

    import numpy as np

    def _balance_by_full_mirror(self, cone_data, car_yaw, virtual_width=4.0, pairing_threshold=15.0, collision_threshold=2.5):
        yellows = sorted([c for c in cone_data if c[2] == 'y'], key=lambda x: (x[0], x[1]))
        blues = sorted([c for c in cone_data if c[2] == 'b'], key=lambda x: (x[0], x[1]))

    # --- CONCEPT: CAR YAW ANCHOR ---
    # Convert the car's orientation into a reference vector to ensure "Forward" is always known.
        car_heading = np.array([np.cos(car_yaw), np.sin(car_yaw)])

        balanced = [(float(c[0]), float(c[1]), c[2], False) for c in cone_data]
        midpoint_nodes = []

        def mirror_wall(source_cones, target_cones, t_color, direction, reference_heading):
            if len(source_cones) < 2: return

        # --- CONCEPT: HEADING SANITY CHECK ---
        # Initialize the previous unit vector with the car's heading to anchor the first cone.
            prev_unit_vec = reference_heading

            for i in range(len(source_cones)):
                p_curr = np.array([source_cones[i][0], source_cones[i][1]])
            
            # 1. Track Direction
                if i < len(source_cones) - 1:
                    vec = np.array([source_cones[i+1][0], source_cones[i+1][1]]) - p_curr
                else:
                    vec = p_curr - np.array([source_cones[i-1][0], source_cones[i-1][1]])
            
                mag = np.linalg.norm(vec)
                if mag == 0: continue
                unit_vec = vec / mag

            # --- FLIPPING CHECK ---
            # If the calculated vector points >90 degrees away from the previous heading, flip it back.
                if np.dot(unit_vec, prev_unit_vec) < 0:
                    unit_vec = -unit_vec
            
            # Update the reference for the next cone in the sequence
                prev_unit_vec = unit_vec 
            # ----------------------

            # 2. Angle-from-Normal Partner Search
                has_natural_partner = False
                normal_line = np.array([-unit_vec[1], unit_vec[0]]) * direction
            
            # ... [Debug prints remain the same] ...

                for target in target_cones:
                    t_pos = np.array([target[0], target[1]])
                    partner_vec = t_pos - p_curr
                    d = np.linalg.norm(partner_vec)
                
                    if d < pairing_threshold:
                        unit_partner_vec = partner_vec / d
                        dot_with_normal = np.dot(normal_line, unit_partner_vec)
                        angle_deg = np.degrees(np.arccos(np.clip(dot_with_normal, -1.0, 1.0)))
                    
                        if angle_deg <= 30.0:
                            has_natural_partner = True
                            break

            # 3. Adaptive Mirroring
                if not has_natural_partner:
                    local_width = virtual_width
                    min_dist_to_gate = float('inf')
                    for y in yellows:
                        y_p = np.array([y[0], y[1]])
                        for b in blues:
                            b_p = np.array([b[0], b[1]])
                            gate_dist = np.linalg.norm(y_p - b_p)
                            if 2.5 < gate_dist < 7.0:
                                unit_gate_vec = (b_p - y_p) / gate_dist
                                alignment = abs(np.dot(unit_gate_vec, normal_line))
                                if alignment > 0.85:
                                    dist_to_lonely = np.linalg.norm(p_curr - (y_p + b_p)/2)
                                    if dist_to_lonely < min_dist_to_gate:
                                        min_dist_to_gate = dist_to_lonely
                                        local_width = gate_dist

                v_pos = p_curr + (normal_line * local_width)
                
                if not any(np.linalg.norm(v_pos - np.array([c[0], c[1]])) < collision_threshold for c in cone_data):
                    balanced.append((float(v_pos[0]), float(v_pos[1]), t_color, True))
                    midpoint_nodes.append(tuple((p_curr + v_pos) / 2.0))

    # Pass the car_heading as the reference for both walls
        mirror_wall(blues, yellows, 'y', -1, car_heading)
        mirror_wall(yellows, blues, 'b', 1, car_heading)
        return balanced, midpoint_nodes

    def _handle_low_cones(self, cone_data, car_pos, car_yaw):
        ASSUMED_WIDTH = 4.0
        target_point = None
        right_vec = np.array([np.sin(car_yaw), -np.cos(car_yaw)])
        if len(cone_data) == 1:
            c = cone_data[0]
            cp = np.array([c[0], c[1]])
            target_point = cp + (right_vec * (ASSUMED_WIDTH/2.0)) if c[2]=='b' else cp - (right_vec * (ASSUMED_WIDTH/2.0))
        elif len(cone_data) == 2:
            target_point = (np.array(cone_data[0][:2]) + np.array(cone_data[1][:2])) / 2.0
        
        if target_point is not None:
            direction = (target_point - car_pos) / (np.linalg.norm(target_point - car_pos) + 1e-6)
            extension = target_point + direction * 3.0
            return [tuple(car_pos), tuple(target_point), tuple(extension)]
        return []
