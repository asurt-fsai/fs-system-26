import numpy as np
from . import voronoi_gen
from . import filters
from . import graph_search
from .smoothing import smooth_path_bspline, smooth_path_line


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
        cone_data = remove_ghost_cones(cone_data)
        balanced_cone_data, midpoint_nodes = self._balance_by_full_mirror(
            cone_data, virtual_width=4.0
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

    def _balance_by_full_mirror(self, cone_data, virtual_width=4.0, pairing_threshold=15.0, collision_threshold=2.5):
        """
        Smartly balances the track by only adding virtual cones when a real partner 
        cannot be found within an angular sweep, regardless of large gate widths.
        """
        yellows = sorted([c for c in cone_data if c[2] == 'y'], key=lambda x: (x[0], x[1]))
        blues = sorted([c for c in cone_data if c[2] == 'b'], key=lambda x: (x[0], x[1]))
    
        balanced = [(float(c[0]), float(c[1]), c[2], False) for c in cone_data]
        midpoint_nodes = []

        def mirror_wall(source_cones, target_cones, t_color, direction):
            if len(source_cones) < 2: return
    
            for i in range(len(source_cones)):
                p_curr = np.array([source_cones[i][0], source_cones[i][1]])
                side = "BLUE" if t_color == 'y' else "YELLOW"
            
            # 1. Calculate track direction
                if i < len(source_cones) - 1:
                    vec = np.array([source_cones[i+1][0], source_cones[i+1][1]]) - p_curr
                else:
                    vec = p_curr - np.array([source_cones[i-1][0], source_cones[i-1][1]])
        
                mag = np.linalg.norm(vec)
                if mag == 0: continue
                unit_vec = vec / mag
        
            # 2. Smart Partner Search
                has_natural_partner = False
                best_dot = 1.0 # For debugging
            
                for target in target_cones:
                    t_pos = np.array([target[0], target[1]])
                    dist = np.linalg.norm(p_curr - t_pos)
            
                    if dist < pairing_threshold:
                        partner_vec = (t_pos - p_curr) / dist
                        dot_val = abs(np.dot(unit_vec, partner_vec))
                    
                        if dot_val < best_dot:
                            best_dot = dot_val

                        if dot_val < 0.7:
                            has_natural_partner = True
                            break
            
            # 3. Mirroring logic (Only if no natural partner is found)
                if not has_natural_partner:
                    print(f"   No partner for {source_cones[i]} | Checking for virtual cone placement...")
                    print(f"               Closest partner dot product was {best_dot:.2f} (Target < 0.7)")
                    normal = np.array([-unit_vec[1], unit_vec[0]])
                    v_pos = p_curr + (normal * virtual_width * direction)
                
                # Check for collisions with real cones before adding virtual cone
                    is_blocked = any(np.linalg.norm(v_pos - np.array([c[0], c[1]])) < collision_threshold 
                                    for c in cone_data)
                
                    if not is_blocked:
                        balanced.append((float(v_pos[0]), float(v_pos[1]), t_color, True))
                    # Create midpoint to anchor the path
                        gate_center = (p_curr + v_pos) / 2.0
                        midpoint_nodes.append(tuple(gate_center))
                    else:
                        print(f"               Virtual cone blocked by collision at {v_pos}")

        mirror_wall(blues, yellows, 'y', -1)
        mirror_wall(yellows, blues, 'b', 1)
    
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
