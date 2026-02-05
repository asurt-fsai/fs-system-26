# test_ghost_cones.py
from typing import Dict, List, Tuple
import sys
import matplotlib.pyplot as plt
import numpy as np

from path_planning.modules.planner import PathPlanner

# to run : python -m path_planning.test_ghost_cones 1

# scenario_id -> (cone_data, car_pose)
SCENARIOS: Dict[str, Tuple[List[tuple], tuple]] = {

    # 1) Straight corridor
    "1": (
        [
            (0, 0, 'y'), (2, 0, 'y'), (4, 0, 'y'),
            (0, 3, 'b'), (2, 3, 'b'), (4, 3, 'b'),
            (2.0, 6.0, 'b'),   # far away ghost cone
        ],
        (0.0, 1.5, 0.0),
    ),

    # 2) Same + ghost cone in the middle
    "2": (
        [
            (0, 0, 'y'), (2, 0, 'y'), (4, 0, 'y'),
            (0, 3, 'b'), (2, 3, 'b'), (4, 3, 'b'),
            (2.0, 2.0, 'b'),   #  ghost cone
        ],
        (0.0, 1.5, 0.0),
    ),

    # 4) Hairpin with ghost in track and straight entry
    "4": (
        [
            # --- Straight Entry ---
            (0, 0, 'y'), (2, 0, 'y'), (4, 0, 'y'),
            (0, -3, 'b'), (2, -3, 'b'), (4, -3, 'b'),

            # --- The Hairpin Curve ---
            (6, 1, 'y'), (7, 3, 'y'), (6, 5, 'y'), (4, 6, 'y'), (2, 6, 'y'),(0,6,'y'),
            (10, 0, 'b'), (10, 3, 'b'), (8, 6, 'b'), (6, 8, 'b'), (2, 9, 'b'),(7.5, -2, 'b'),

            #ghost cone
            (8, 1, 'b')
        ],
        (-2.5, -1.5, 0.0),
    ),

    # 5) straight + ghost cone in the middle
    "5": (
        [
            (0, 0, 'y'), (2, 0, 'y'), (4, 0, 'y'),
            (0, 3, 'b'), (2, 3, 'b'), (4, 3, 'b'),
            (2.0, 1.5, 'b'),  # ghost cone
        ],
        (0.0, 1.5, 0.0),
    ),

    # 6) straight +curve with ghost in curve
    "6": (
        [
            # Straight section
            (0, 1, 'y'), (2, 1, 'y'), (4, 1, 'y'), (6, 1, 'y'),
            (0, -2, 'b'), (2, -2, 'b'), (4, -2, 'b'), (6, -2, 'b'),(9,-1,'b'),

            # Curve section
            (8, 1, 'y'), (9, 3, 'y'), (8, 5, 'y'), (6, 6, 'y'),
            (10, 0, 'b'), (12, 3, 'b'), (10, 6, 'b'), (8, 8, 'b'),

            # Ghost cone in the curve
            (9.5, 4.0, 'b'),
        ],
        (0.0, -1, 0.0),
    ),

    # 7)multiple ghost cones
    "7": (
        [
            (0, 0, 'y'), (2, 0, 'y'), (4, 0, 'y'), (6, 0, 'y'),
            (0, 3, 'b'), (2, 3, 'b'), (4, 3, 'b'),
            (4.1, 3.1, 'b'),
            (1, 1.5, 'b'),
            (3,2,'y'),
            (6, 3, 'b'),
        ],
        (0.0, 1.5, 0.0),
    ),
    # 8
    "8": (
        [
            (0, 0, 'b'), (0, 4, 'b'), (4, 0, 'y'),
            (2, 0, 'y'), # Ghost cone in the middle
        ],
        (2, -1, 0.0),
    ),


}

def get_scenario_names():
    return sorted(SCENARIOS.keys(), key=int)

def make_scenario(name: str):
    if name not in SCENARIOS:
        valid = ", ".join(get_scenario_names())
        raise ValueError(f"Unknown scenario '{name}'. Valid options: {valid}")
    cones, car = SCENARIOS[name]
    return list(cones), tuple(car)

def run_scenario(scenario_id: str):
    cone_data, car_data = make_scenario(scenario_id)

    planner = PathPlanner(
        robot_radius=0.5,
        safety_margin=0.2,
        max_edge_len=8.0 # Increased for larger scenarios
    )

    path = planner.execute_cycle(cone_data, [car_data])
    visualize(cone_data, car_data, path, scenario_id)

def visualize(cones, car, path, scenario_id):
    xs = [c[0] for c in cones]
    ys = [c[1] for c in cones]
    colors = ['gold' if c[2] == 'y' else 'blue' for c in cones]

    plt.figure(figsize=(10, 7))
    plt.scatter(xs, ys, c=colors, s=100, edgecolors='black', zorder=5, label='Input Cones')
    plt.plot(car[0], car[1], 'r^', markersize=14, label='Car Pose', zorder=10)

    if path:
        px, py = zip(*path)
        plt.plot(px, py, '-g', linewidth=3, label='Planned Path', zorder=1)
        plt.scatter(px, py, c='green', s=30, zorder=2)

    plt.axis('equal')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.title(f"Scenario {scenario_id} Execution")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_ghost_cones.py <scenario_id>")
        print("Available scenarios:", ", ".join(get_scenario_names()))
        sys.exit(0)

    run_scenario(sys.argv[1])