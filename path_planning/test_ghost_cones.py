from __future__ import annotations
import sys
import numpy as np
import matplotlib.pyplot as plt

from typing import Dict, List, Tuple

from path_planning.modules.planner import PathPlanner
# 0-- y, 1-- b

SCENARIOS: Dict[str, Tuple[List[tuple], tuple]] = {
    "1": (
        [],
        (0.0, 0.0, 0.0),
    ),

    "2": (
        [(1.0, 3.0, 'b'), (1.0,1.0, 'y'),],
        (0.0, 0.0, 0.4),
    ),

    "3": (
        [
            (1.0, 3.0, 'b'),
            (3.0, 3.0, 'b'),
            (1.0, 0.0, 'y'),
            (3.0, 0.0, 'y'),
        ],
        (0.0, 1.5, 0.8),
    ),

    "4": (
        [(4.0, 2.0, 'y')],
        (0.0, 0.0, 1.2),
    ),

    #"5": (
    #    [(4.0, 2.0, 'y'), (3.0, 2.0, 'y')],
    #    (0.0, 0.0, 1.6),
    #),

    "6": (
        [
            (4.0, 4.0, 'b'),
            (4.0, 1.0, 'y'),
            (3.0, 1.0, 'y'),
        ],
        (0.0, 0.0, 2.0),
    ),

    "7": (
        [
            (2.0, 3.0, 'b'),
            (4.0, 3.0, 'b'),
            (2.0, 0.0, 'y'),
        ],
        (0.0, 0.0, 1.4),
    ),

    #"8": (
    #    [(3.0, 3.0, 'b'), (5.0, 3.0, 'b')],
    #    (0.0, 0.0, 1.8),
    #),

    "9": (
        [(3.0, 3.0, 'b')],
        (0.0, 0.0, 0.2),
    ),

    "10": (
        [(5.0, 3.0, 'b'), (5.0, 2.0, 'y')],
        (0.0, 0.0, 0.6),
    ),

    "11": (
        [
            (1.0, 3.0, 'b'),
            (4.0, 5.0, 'b'),
            (1.0, 2.0, 'y'),
            (4.0, 2.0, 'y'),
            (1.0, 5.0, 'b'),
        ],
        (0.0, 0.0, 1.0),
    ),

    "12": (
        [(5.0, 2.0, 'y')],
        (0.0, 0.0, 1.4),
    ),

    "13": (
        [(5.0, 3.0, 'y'), (5.0, 1.0, 'y')],
        (0.0, 0.0, 0.1),
    ),

    "14": (
        [
            (3.0, 5.0, 'b'),
            (3.0, 2.0, 'y'),
            (5.0, 2.0, 'y'),
        ],
        (0.0, 0.0, 5.2),
    ),

    "15": (
        [
            (2.0, 5.0, 'b'),
            (3.0, 4.0, 'b'),
            (3.0, 2.0, 'y'),
        ],
        (0.0, 0.0, 1.6),
    ),

    "16": (
        [(0.0, 3.0, 'b'), (2.0, 5.0, 'b')],
        (0.0, 0.0, 0.2),
    ),

    "17": (
        [(3.0, 5.0, 'b')],
        (0.0, 0.0, 0.6),
    ),

    "18": (
        [(2.0, 4.0, 'b'), (4.0, 3.0, 'y')],
        (0.0, 0.0, 1.0),
    ),

    "19": (
        [
            (2.0, 3.0, 'b'),
            (5.0, 3.0, 'b'),
            (2.0, 0.0, 'y'),
            (5.0, 2.0, 'y'),
        ],
        (0.0, 0.0, 1.4),
    ),

    "20": (
        [(0.0, 2.0, 'y')],
        (0.0, 0.0, 1.8),
    ),
    # 3 yellow s only
    "21":(
        [ (1.0, 1.0, 'y'),
          (2.0, 2.0, 'y'),
          (3.0, 3.0, 'y'),],
         (0.0, 0.0, 1.4),
    ),
    #3 s on each side
    "22":(
        [ (0.0, 1.0, 'b'),
          (1.0, 2.0, 'b'),
          (2.0, 3.0, 'b'),
          (1.0, 1.0, 'y'),
          (2.0, 2.0, 'y'),
          (3.0, 3.0, 'y'),
          ],
        (0.0, 0.0, 1.4),
    ),
    # 3 blue s only
    "23":(
        [ (1.0, 1.0, 'b'),
          (2.0, 2.0, 'b'),
          (3.0, 3.0, 'b'),
          ],
        (0.0, 0.0, 1.4),

    ),
    "24": ( # s curve
        [
            # First part (Straight-ish)
            (0, 0, 'y'), (3, 0.5, 'y'), (0, 3.5, 'b'), (3, 4, 'b'),
            # The S-Bend (Turning Left then Right)
            (6, 2, 'y'), (9, 5, 'y'),  # Inner Yellow
            (5, 6, 'b'), (8, 9, 'b'),  # Outer Blue
            # Recovery
            (12, 6, 'y'), (15, 6, 'y'),
            (11, 10, 'b'), (14, 10, 'b'),
        ],
        (-1.0, 1.75, 0.0),
    ),
"25": ( # s curve with a ghost cone
        [
            # First part (Straight-ish)
            (0, 0, 'y'), (3, 0.5, 'y'), (0, 3.5, 'b'), (3, 4, 'b'),
            # The S-Bend (Turning Left then Right)
            (6, 2, 'y'), (9, 5, 'y'),  # Inner Yellow
            (5, 6, 'b'), (8, 9, 'b'),  # Outer Blue
            # Recovery
            (12, 6, 'y'), (15, 6, 'y'),
            (11, 10, 'b'), (14, 10, 'b'),
            (7, 5, 'y'), # Ghost cone violating same color rule (too far from other yellows)
        ],
        (-1.0, 1.75, 0.0),
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


