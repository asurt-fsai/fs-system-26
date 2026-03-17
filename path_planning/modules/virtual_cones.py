import numpy as np


class VirtualCones:
    def __init__(self, virtual_width=4.0, pairing_threshold=15.0, collision_threshold=2.5):
        """
        Initialize the Virtual Cone generator with configuration parameters.
        """
        self.virtual_width = virtual_width
        self.pairing_threshold = pairing_threshold
        self.collision_threshold = collision_threshold


    # ============================================================
    # MAIN PUBLIC METHOD
    # ============================================================

    def generate_balanced_cones(self, cone_data, car_pos, car_yaw):
        """
        Main function that balances the track by generating missing virtual cones.
        """

        # Convert yaw to heading vector
        car_heading = np.array([np.cos(car_yaw), np.sin(car_yaw)])

        # Separate cones by color and order them along the wall
        yellows = self._order_cones_along_wall(
            [c for c in cone_data if c[2] == 'y'], car_pos, car_heading
        )

        blues = self._order_cones_along_wall(
            [c for c in cone_data if c[2] == 'b'], car_pos, car_heading
        )

        # Copy original cones
        balanced = [(float(c[0]), float(c[1]), c[2], False) for c in cone_data]

        midpoint_nodes = []

        # Mirror both walls
        self._mirror_wall(blues, yellows, 'y', -1, yellows, blues, balanced, midpoint_nodes, cone_data)
        self._mirror_wall(yellows, blues, 'b', 1, yellows, blues, balanced, midpoint_nodes, cone_data)

        print(f"[MIDPOINT TRACE] Total midpoints added: {len(midpoint_nodes)}")

        return balanced, midpoint_nodes


    # ============================================================
    # WALL MIRRORING LOGIC
    # ============================================================

    def _mirror_wall(self, source_cones, target_cones, t_color, direction,
                     yellows, blues, balanced, midpoint_nodes, cone_data):
        """
        For every cone in one wall, try to find a partner in the opposite wall.
        If no partner exists, generate a virtual cone.
        """

        if len(source_cones) < 2:
            return

        for i in range(len(source_cones)):

            p_curr = np.array([source_cones[i][0], source_cones[i][1]])

            is_start_or_end = (i == 0 or i == len(source_cones) - 1)

            if is_start_or_end:
                print(f"\n[DECISION DEBUG] Checking {source_cones[i][2]} cone {i} at {p_curr}")

            # ----------------------------------------------------
            # Step 1: Compute track normal vector
            # ----------------------------------------------------

            normal_line = self._get_normal_vector(i, source_cones, direction)

            if normal_line is None:
                continue

            # ----------------------------------------------------
            # Step 2: Search for natural partner
            # ----------------------------------------------------

            has_partner = False

            for target in target_cones:

                t_pos = np.array([target[0], target[1]])
                partner_vec = t_pos - p_curr
                d = np.linalg.norm(partner_vec)

                if  d < self.pairing_threshold:

                    unit_partner_vec = partner_vec / d
                    dot_with_normal = np.dot(normal_line, unit_partner_vec)

                    angle_deg = np.degrees(
                        np.arccos(np.clip(dot_with_normal, -1.0, 1.0))
                    )

                    if is_start_or_end:
                        print(
                            f"  -> Comparing with {target[2]} at {t_pos}: "
                            f"dist={d:.2f}, angle={angle_deg:.1f}°"
                        )

                    if angle_deg <= 20.0:

                        if is_start_or_end:
                            print("  [SUCCESS] Found natural partner!")

                        has_partner = True
                        break

            # ----------------------------------------------------
            # Step 3: If no partner -> generate virtual cone
            # ----------------------------------------------------

            if not has_partner:

                if is_start_or_end:
                    print("  [FAILURE] No partner found. Decision: GENERATE VIRTUAL CONE.")

                v_cone, midpoint = self._calculate_virtual_cone(
                    p_curr, normal_line, t_color, yellows, blues, cone_data
                )

                if v_cone:

                    balanced.append(v_cone)
                    midpoint_nodes.append(midpoint)

                    print(
                        f"[MIDPOINT TRACE] Added midpoint at {midpoint} "
                        f"between cone at {tuple(p_curr)} "
                        f"and virtual cone at {(v_cone[0], v_cone[1])} "
                        f"(color: {t_color})"
                    )


    # ============================================================
    # NORMAL VECTOR CALCULATION
    # ============================================================

    def _get_normal_vector(self, index, cones, direction):
        """
        Computes the normal vector across the track at the current cone.
        """

        p_curr = np.array([cones[index][0], cones[index][1]])

        if index == 0:

            vec = np.array([cones[index+1][0], cones[index+1][1]]) - p_curr

        elif index == len(cones) - 1:

            vec = p_curr - np.array([cones[index-1][0], cones[index-1][1]])

        else:

            p_prev = np.array([cones[index-1][0], cones[index-1][1]])
            p_next = np.array([cones[index+1][0], cones[index+1][1]])

            vec = p_next - p_prev

        mag = np.linalg.norm(vec)

        if mag == 0:
            return None

        unit_vec = vec / mag

        return np.array([-unit_vec[1], unit_vec[0]]) * direction


    # ============================================================
    # VIRTUAL CONE CREATION
    # ============================================================

    def _calculate_virtual_cone(self, p_curr, normal_line, t_color, yellows, blues, cone_data):
        """
        Calculate position of a virtual cone using adaptive track width.
        """

        local_width = self.virtual_width
        min_dist_to_gate = float('inf')

        # ----------------------------------------------------
        # Adaptive width based on nearby gates
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Compute virtual cone position
        # ----------------------------------------------------

        v_pos = p_curr + (normal_line * local_width)

        # ----------------------------------------------------
        # Collision check
        # ----------------------------------------------------

        is_colliding = any(
            np.linalg.norm(v_pos - np.array([c[0], c[1]])) < self.collision_threshold
            for c in cone_data
        )

        if not is_colliding:

            virtual_cone = (float(v_pos[0]), float(v_pos[1]), t_color, True)

            midpoint = tuple((p_curr + v_pos) / 2.0)

            return virtual_cone, midpoint

        return None, None


    # ============================================================
    # CONE ORDERING ALGORITHM
    # ============================================================

    def _order_cones_along_wall(self, cones, car_pos, car_heading):
        """Orders a list of cones by finding the start of the wall and connecting nearest neighbors."""
        if len(cones) <= 2:
            return list(cones)

        car_pos = np.array([car_pos[0], car_pos[1]])
        heading = car_heading / (np.linalg.norm(car_heading) + 1e-6)

        # 1. Find the starting cone. 
        # By projecting the cones onto the car's heading, the minimum value 
        # will always be the cone furthest back (the start of the visible track).
        start_idx = min(range(len(cones)), key=lambda i: np.dot(np.array([cones[i][0], cones[i][1]]) - car_pos, heading))
        
        remaining = list(cones)
        ordered = [remaining.pop(start_idx)]

        # 2. Build the wall by simply jumping to the nearest unvisited cone.
        # Since cones on the same wall are close together, this works perfectly.
        while remaining:
            last = np.array([ordered[-1][0], ordered[-1][1]])
            
            # Find the index of the closest remaining cone
            next_idx = min(range(len(remaining)), key=lambda i: np.linalg.norm(np.array([remaining[i][0], remaining[i][1]]) - last))
            
            ordered.append(remaining.pop(next_idx))

        return ordered