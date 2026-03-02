from math import dist
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

        # 4. Balance Cones and generate Midpoints and ghost cones
        #cone_data = remove_ghost_cones(cone_data)
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
        
        balanced_cone_data, midpoint_nodes = self._balance_by_full_mirror(
            cone_data, car_pos, car_yaw, virtual_width=4.0
        )
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

    import numpy as np

    def _order_cones_along_wall(self, cones, car_pos, car_heading):
        if len(cones) <= 2:
            return list(cones)

        remaining = list(cones)

        if car_pos is not None:
            car_pos = np.array([car_pos[0], car_pos[1]])
            heading = car_heading / (np.linalg.norm(car_heading) + 1e-6)

            def start_score(c):
                v = np.array([c[0], c[1]]) - car_pos
                d = np.linalg.norm(v)
                if d == 0:
                    return (0.0, 0.0)
                in_front = np.dot(v / d, heading)
                return (0.0 if in_front > -0.2 else 1.0, d)

            start_idx = min(range(len(remaining)), key=lambda i: start_score(remaining[i]))
        else:
            start_idx = 0

        ordered = [remaining.pop(start_idx)]
        prev_vec = None

        while remaining:
            last = np.array([ordered[-1][0], ordered[-1][1]])

            def score(i):
                cand = np.array([remaining[i][0], remaining[i][1]])
                vec = cand - last
                d = np.linalg.norm(vec)
                if d == 0:
                    return (0.0, 0.0)
                if prev_vec is None:
                    return (d, 0.0)
                prev_unit = prev_vec / (np.linalg.norm(prev_vec) + 1e-6)
                vec_unit = vec / d
                direction_penalty = 1.0 - np.dot(vec_unit, prev_unit)
                return (d * (1.0 + 0.8 * max(0.0, direction_penalty)), direction_penalty)

            next_idx = min(range(len(remaining)), key=score)
            next_cone = remaining.pop(next_idx)
            prev_vec = np.array([next_cone[0], next_cone[1]]) - last
            ordered.append(next_cone)

        return ordered

    def _balance_by_full_mirror(self, cone_data, car_pos, car_yaw, virtual_width=4.0, pairing_threshold=15.0, collision_threshold=2.5):
        # Convert the car's orientation into a reference vector to ensure "Forward" is always known.
        car_heading = np.array([np.cos(car_yaw), np.sin(car_yaw)])

        yellows = self._order_cones_along_wall([c for c in cone_data if c[2] == 'y'], car_pos, car_heading)
        blues = self._order_cones_along_wall([c for c in cone_data if c[2] == 'b'], car_pos, car_heading)

        balanced = [(float(c[0]), float(c[1]), c[2], False) for c in cone_data]
        midpoint_nodes = []

        def mirror_wall(source_cones, target_cones, t_color, direction, reference_heading):
            if len(source_cones) < 2: return

            for i in range(len(source_cones)):
                p_curr = np.array([source_cones[i][0], source_cones[i][1]])

                if i == 0:
                    p_next = np.array([source_cones[i+1][0], source_cones[i+1][1]])
                    vec = p_next - p_curr
                elif i == len(source_cones) - 1:
                    p_prev = np.array([source_cones[i-1][0], source_cones[i-1][1]])
                    vec = p_curr - p_prev
                else:
                    p_prev = np.array([source_cones[i-1][0], source_cones[i-1][1]])
                    p_next = np.array([source_cones[i+1][0], source_cones[i+1][1]])
                    vec = p_next - p_prev

                mag = np.linalg.norm(vec)
                if mag == 0:
                    continue
                unit_vec = vec / mag

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

