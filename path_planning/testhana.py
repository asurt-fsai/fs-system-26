import numpy as np
import matplotlib.pyplot as plt

class HandshakePlanner:
    def __init__(self, virtual_width=3.0, pairing_threshold=6.0):
        self.virtual_width = virtual_width
        self.pairing_threshold = pairing_threshold

    def balance_uneven_cones(self, cone_data, car_yaw):
        """
        Implementation of the Handshake logic.
        """
        yellow_cones = [c for c in cone_data if c[2] == 'y']
        blue_cones = [c for c in cone_data if c[2] == 'b']
        balanced_cones = list(cone_data)
        
        # Vector pointing right relative to car heading
        right_vec = np.array([np.sin(car_yaw), -np.cos(car_yaw)])

        # Check for lonely Yellow cones
        for y in yellow_cones:
            y_pos = np.array([y[0], y[1]])
            has_partner = any(
                np.linalg.norm(y_pos - np.array([b[0], b[1]])) <= self.pairing_threshold 
                for b in blue_cones
            )
            if not has_partner:
                virtual_blue = y_pos - right_vec * self.virtual_width
                balanced_cones.append((virtual_blue[0], virtual_blue[1], 'b', True))

        # Check for lonely Blue cones
        for b in blue_cones:
            b_pos = np.array([b[0], b[1]])
            has_partner = any(
                np.linalg.norm(b_pos - np.array([y[0], y[1]])) <= self.pairing_threshold 
                for y in yellow_cones
            )
            if not has_partner:
                virtual_yellow = b_pos + right_vec * self.virtual_width
                balanced_cones.append((virtual_yellow[0], virtual_yellow[1], 'y', True))

        return balanced_cones

def run_comprehensive_tests():
    planner = HandshakePlanner()
    
    # 10 Diverse Test Scenarios
    scenarios = [
        {"name": "1. Balanced Straight", "yaw": np.pi/2, "cones": [(0,0,'y'), (3,0,'b'), (0,4,'y'), (3,4,'b')]},
        {"name": "2. One-Sided Yellow", "yaw": np.pi/2, "cones": [(0,0,'y'), (0,4,'y'), (0,8,'y')]},
        {"name": "3. One-Sided Blue", "yaw": np.pi/2, "cones": [(3,0,'b'), (3,4,'b'), (3,8,'b')]},
        {"name": "4. Lonely Middle", "yaw": np.pi/2, "cones": [(0,0,'y'), (3,0,'b'), (0,4,'y'), (0,8,'y'), (3,8,'b')]},
        {"name": "5. Diagonal Yaw (45°)", "yaw": np.pi/4, "cones": [(0,0,'y'), (2,2,'y')]},
        {"name": "6. Sharp Zigzag", "yaw": np.pi/2, "cones": [(0,0,'y'), (2,3,'y'), (0,6,'y')]},
        {"name": "7. Horizontal Track", "yaw": 0.0, "cones": [(0,0,'y'), (4,0,'y')]},
        {"name": "8. Sparse Curve", "yaw": np.pi/2, "cones": [(0,0,'y'), (1,3,'y'), (3,5,'y')]},
        {"name": "9. Partner Just Outside", "yaw": np.pi/2, "cones": [(0,0,'y'), (6.1,0,'b')]}, # Threshold is 6.0
        {"name": "10. Mixed Density", "yaw": np.pi/2, "cones": [(0,0,'y'), (3,0,'b'), (0,2,'y'), (0,4,'y')]}
    ]

    fig, axes = plt.subplots(2, 5, figsize=(25, 10))
    axes = axes.flatten()

    for ax, test in zip(axes, scenarios):
        result = planner.balance_uneven_cones(test["cones"], test["yaw"])
        
        for c in result:
            color = 'gold' if c[2] == 'y' else 'blue'
            marker = 'X' if len(c) > 3 else 'o'
            ax.scatter(c[0], c[1], c=color, marker=marker, s=100, edgecolors='k')
        
        # Draw car heading arrow
        ax.arrow(0, 0, np.cos(test["yaw"]), np.sin(test["yaw"]), head_width=0.3, color='red')
        ax.set_title(test["name"], fontsize=10)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_comprehensive_tests()