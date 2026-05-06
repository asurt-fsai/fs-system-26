"""
FULL DYNAMIC FORMULA STUDENT TRACK SIMULATOR
============================================

FEATURES
--------
✔ 5 dynamic straight-track scenarios
✔ Real-time GLOBAL coordinate simulation
✔ Dynamic cone appearance
✔ Simulated sensor window
✔ Real-time yaw updates
✔ Uses your execute_cycle()
✔ Shows:
    - Real cones
    - Virtual cones
    - Planned path
    - Car position
    - Car heading
✔ Different marker for virtual cones
✔ Easy scenario switching

# ============================================================
# HOW TO CHOOSE SCENARIO
# ============================================================

# CHANGE THIS LINE:

#     ACTIVE_SCENARIO = 1

# OPTIONS:
# --------
# 1 = Perfect straight
# 2 = Missing blue cones
# 3 = Missing yellow cones
# 4 = Random dropouts
# 5 = Noisy realistic track

# ============================================================
# HOW TO RUN
# ============================================================

# pip install matplotlib numpy scipy

# python simulator.py
# """

# import numpy as np
# import matplotlib.pyplot as plt
# from matplotlib.animation import FuncAnimation

# from modules.planner import PathPlanner

# # ============================================================
# # CHOOSE SCENARIO HERE
# # ============================================================

# ACTIVE_SCENARIO = 2

# # ============================================================
# # CONFIGURATION
# # ============================================================

# TRACK_LENGTH = 140
# TRACK_WIDTH = 4.0
# CONE_SPACING = 4.0

# SENSOR_FORWARD_RANGE = 18.0
# SENSOR_BACKWARD_RANGE = 3.0

# CAR_SPEED = 1.5
# DT = 0.1

# # ============================================================
# # CREATE PLANNER
# # ============================================================

# planner = PathPlanner()

# # ============================================================
# # SCENARIO FUNCTIONS
# # ============================================================

# # ============================================================
# # SCENARIO FUNCTIONS
# # BLUE = LEFT
# # YELLOW = RIGHT
# # ============================================================

# def scenario_1_perfect_straight():

#     cones = []

#     for x in np.arange(0, TRACK_LENGTH, CONE_SPACING):

#         # BLUE LEFT
#         cones.append((x, TRACK_WIDTH / 2, 'b'))

#         # YELLOW RIGHT
#         cones.append((x, -TRACK_WIDTH / 2, 'y'))

#     return cones


# def scenario_2_missing_blue():

#     cones = []

#     for i, x in enumerate(np.arange(0, TRACK_LENGTH, CONE_SPACING)):

#         # BLUE LEFT
#         if i % 4 != 0:
#             cones.append((x, TRACK_WIDTH / 2, 'b'))

#         # YELLOW RIGHT
#         cones.append((x, -TRACK_WIDTH / 2, 'y'))

#     return cones


# def scenario_3_missing_yellow():

#     cones = []

#     for i, x in enumerate(np.arange(0, TRACK_LENGTH, CONE_SPACING)):

#         # BLUE LEFT
#         cones.append((x, TRACK_WIDTH / 2, 'b'))

#         # YELLOW RIGHT
#         if i % 5 != 0:
#             cones.append((x, -TRACK_WIDTH / 2, 'y'))

#     return cones


# def scenario_4_random_dropouts():

#     cones = []

#     rng = np.random.default_rng(42)

#     for x in np.arange(0, TRACK_LENGTH, CONE_SPACING):

#         # BLUE LEFT
#         if rng.random() > 0.25:
#             cones.append((x, TRACK_WIDTH / 2, 'b'))

#         # YELLOW RIGHT
#         if rng.random() > 0.25:
#             cones.append((x, -TRACK_WIDTH / 2, 'y'))

#     return cones


# def scenario_5_noisy_realistic():

#     cones = []

#     rng = np.random.default_rng(7)

#     for x in np.arange(0, TRACK_LENGTH, CONE_SPACING):

#         # BLUE LEFT
#         if rng.random() > 0.15:

#             cones.append((
#                 x + rng.normal(0, 0.15),
#                 TRACK_WIDTH / 2 + rng.normal(0, 0.15),
#                 'b'
#             ))

#         # YELLOW RIGHT
#         if rng.random() > 0.15:

#             cones.append((
#                 x + rng.normal(0, 0.15),
#                 -TRACK_WIDTH / 2 + rng.normal(0, 0.15),
#                 'y'
#             ))

#     return cones

# # ============================================================
# # LOAD ACTIVE SCENARIO
# # ============================================================

# SCENARIOS = {
#     1: scenario_1_perfect_straight,
#     2: scenario_2_missing_blue,
#     3: scenario_3_missing_yellow,
#     4: scenario_4_random_dropouts,
#     5: scenario_5_noisy_realistic
# }

# ALL_CONES = SCENARIOS[ACTIVE_SCENARIO]()

# # ============================================================
# # CAR STATE
# # ============================================================

# car_x = 0.0
# car_y = 0.0
# car_yaw = 0.0

# # ============================================================
# # SENSOR MODEL
# # ============================================================

# def get_visible_cones(cones, car_pos, yaw):

#     visible = []

#     heading = np.array([np.cos(yaw), np.sin(yaw)])

#     for cone in cones:

#         cone_pos = np.array([cone[0], cone[1]])

#         rel = cone_pos - car_pos

#         projection = np.dot(rel, heading)

#         if -SENSOR_BACKWARD_RANGE < projection < SENSOR_FORWARD_RANGE:

#             visible.append(cone)

#     return visible

# # ============================================================
# # PLOT SETUP
# # ============================================================

# fig, ax = plt.subplots(figsize=(15, 8))

# # Real cones
# yellow_real = ax.scatter([], [], s=80)
# blue_real = ax.scatter([], [], s=80)

# # Virtual cones
# yellow_virtual = ax.scatter([], [], s=180, marker='*')
# blue_virtual = ax.scatter([], [], s=180, marker='*')

# # Car
# car_plot, = ax.plot([], [], marker='o', markersize=10)

# # Yaw arrow
# yaw_line, = ax.plot([], [], linewidth=2)

# # Path
# path_line, = ax.plot([], [], linewidth=3)

# # ============================================================
# # COLORS
# # ============================================================

# yellow_real.set_color('gold')
# blue_real.set_color('blue')

# yellow_virtual.set_color('orange')
# blue_virtual.set_color('cyan')

# car_plot.set_color('red')

# yaw_line.set_color('red')

# path_line.set_color('green')

# # ============================================================
# # MAIN LOOP
# # ============================================================

# def update(frame):

#     global car_x
#     global car_y
#     global car_yaw

#     # ========================================================
#     # MOVE CAR
#     # ========================================================

#     car_x += CAR_SPEED * DT

#     # small yaw oscillation
#     car_yaw = 0.03 * np.sin(car_x * 0.05)

#     car_pos = np.array([car_x, car_y])

#     # ========================================================
#     # GET VISIBLE CONES
#     # ========================================================

#     visible_cones = get_visible_cones(
#         ALL_CONES,
#         car_pos,
#         car_yaw
#     )

#     # ========================================================
#     # SEND TO PLANNER
#     # ========================================================

#     car_data = [
#         (car_x, car_y, car_yaw)
#     ]

#     path, graph = planner.execute_cycle(
#         visible_cones,
#         car_data
#     )

#     # ========================================================
#     # GET VIRTUAL CONES
#     # ========================================================

#     balanced, midpoint_nodes = (
#         planner.virtual_cone_generator.generate_balanced_cones(
#             visible_cones,
#             car_pos,
#             car_yaw
#         )
#     )

#     # ========================================================
#     # SPLIT REAL / VIRTUAL
#     # ========================================================

#     yrx = []
#     yry = []

#     brx = []
#     bry = []

#     yvx = []
#     yvy = []

#     bvx = []
#     bvy = []

#     for c in balanced:

#         x, y, color, is_virtual = c

#         if not is_virtual:

#             if color == 'y':
#                 yrx.append(x)
#                 yry.append(y)
#             else:
#                 brx.append(x)
#                 bry.append(y)

#         else:

#             if color == 'y':
#                 yvx.append(x)
#                 yvy.append(y)
#             else:
#                 bvx.append(x)
#                 bvy.append(y)

#     # ========================================================
#     # UPDATE REAL CONES
#     # ========================================================

#     yellow_real.set_offsets(np.c_[yrx, yry])

#     blue_real.set_offsets(np.c_[brx, bry])

#     # ========================================================
#     # UPDATE VIRTUAL CONES
#     # ========================================================

#     if len(yvx) > 0:
#         yellow_virtual.set_offsets(np.c_[yvx, yvy])
#     else:
#         yellow_virtual.set_offsets(np.empty((0, 2)))

#     if len(bvx) > 0:
#         blue_virtual.set_offsets(np.c_[bvx, bvy])
#     else:
#         blue_virtual.set_offsets(np.empty((0, 2)))

#     # ========================================================
#     # UPDATE CAR
#     # ========================================================

#     car_plot.set_data([car_x], [car_y])

#     yaw_len = 2.5

#     dx = np.cos(car_yaw) * yaw_len
#     dy = np.sin(car_yaw) * yaw_len

#     yaw_line.set_data(
#         [car_x, car_x + dx],
#         [car_y, car_y + dy]
#     )

#     # ========================================================
#     # UPDATE PATH
#     # ========================================================

#     if path and len(path) > 1:

#         px = [p[0] for p in path]
#         py = [p[1] for p in path]

#         path_line.set_data(px, py)

#     else:

#         path_line.set_data([], [])

#     # ========================================================
#     # CAMERA FOLLOW
#     # ========================================================

#     ax.set_xlim(car_x - 10, car_x + 25)

#     ax.set_ylim(-10, 10)

#     # ========================================================
#     # TITLE
#     # ========================================================

#     ax.set_title(
#         f"Scenario {ACTIVE_SCENARIO} | "
#         f"Car X={car_x:.2f} | "
#         f"Yaw={np.degrees(car_yaw):.2f}° | "
#         f"Visible={len(visible_cones)}"
#     )

#     return (
#         yellow_real,
#         blue_real,
#         yellow_virtual,
#         blue_virtual,
#         car_plot,
#         yaw_line,
#         path_line
#     )

# # ============================================================
# # FINAL PLOT SETTINGS
# # ============================================================

# ax.grid(True)

# ax.set_aspect('equal')

# # ============================================================
# # LEGEND
# # ============================================================

# from matplotlib.lines import Line2D

# legend_elements = [

#     Line2D(
#         [0],
#         [0],
#         marker='o',
#         color='w',
#         label='Real Yellow',
#         markerfacecolor='gold',
#         markersize=10
#     ),

#     Line2D(
#         [0],
#         [0],
#         marker='o',
#         color='w',
#         label='Real Blue',
#         markerfacecolor='blue',
#         markersize=10
#     ),

#     Line2D(
#         [0],
#         [0],
#         marker='*',
#         color='w',
#         label='Virtual Yellow',
#         markerfacecolor='orange',
#         markersize=16
#     ),

#     Line2D(
#         [0],
#         [0],
#         marker='*',
#         color='w',
#         label='Virtual Blue',
#         markerfacecolor='cyan',
#         markersize=16
#     ),

#     Line2D(
#         [0],
#         [0],
#         color='green',
#         lw=3,
#         label='Planned Path'
#     )
# ]

# ax.legend(handles=legend_elements)

# # ============================================================
# # START ANIMATION
# # ============================================================

# ani = FuncAnimation(
#     fig,
#     update,
#     interval=100
# )

# plt.show()

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from modules.planner import PathPlanner

# ============================================================
# CONFIG
# ============================================================

ACTIVE_SCENARIO = 8

TRACK_LENGTH = 140
TRACK_WIDTH = 4.0
CONE_SPACING = 4.0

SENSOR_FORWARD_RANGE = 18.0
SENSOR_BACKWARD_RANGE = 3.0

CAR_SPEED = 1.5
DT = 0.1

planner = PathPlanner()

# ============================================================
# SCENARIOS
# ============================================================

# ============================================================
# SCENARIOS (LIGHTWEIGHT CLEAN)
# BLUE = LEFT
# YELLOW = RIGHT
# ============================================================

def scenario_1_perfect_straight():
    cones = []

    for x in np.arange(0, TRACK_LENGTH, CONE_SPACING):
        cones.append((x, TRACK_WIDTH / 2, 'b'))   # BLUE LEFT
        cones.append((x, -TRACK_WIDTH / 2, 'y'))  # YELLOW RIGHT

    return cones


def scenario_2_missing_blue():
    cones = []

    for i, x in enumerate(np.arange(0, TRACK_LENGTH, CONE_SPACING)):
        if i % 4 != 0:
            cones.append((x, TRACK_WIDTH / 2, 'b'))  # BLUE
        cones.append((x, -TRACK_WIDTH / 2, 'y'))     # YELLOW

    return cones


def scenario_3_missing_yellow():
    cones = []

    for i, x in enumerate(np.arange(0, TRACK_LENGTH, CONE_SPACING)):
        cones.append((x, TRACK_WIDTH / 2, 'b'))      # BLUE
        if i % 5 != 0:
            cones.append((x, -TRACK_WIDTH / 2, 'y')) # YELLOW

    return cones


def scenario_4_random_dropouts():
    cones = []
    rng = np.random.default_rng(42)

    for x in np.arange(0, TRACK_LENGTH, CONE_SPACING):

        if rng.random() > 0.25:
            cones.append((x, TRACK_WIDTH / 2, 'b'))

        if rng.random() > 0.25:
            cones.append((x, -TRACK_WIDTH / 2, 'y'))

    return cones


def scenario_5_noisy_realistic():
    cones = []
    rng = np.random.default_rng(7)

    for x in np.arange(0, TRACK_LENGTH, CONE_SPACING):

        if rng.random() > 0.15:
            cones.append((
                x + rng.normal(0, 0.15),
                TRACK_WIDTH / 2 + rng.normal(0, 0.15),
                'b'
            ))

        if rng.random() > 0.15:
            cones.append((
                x + rng.normal(0, 0.15),
                -TRACK_WIDTH / 2 + rng.normal(0, 0.15),
                'y'
            ))

    return cones

def scenario_6_block_gaps_clean():

    cones = []

    BLOCK_SIZE = 5
    GAP = 8.5  # bigger than normal spacing (12m gap)

    x = 0.0

    while x < TRACK_LENGTH:

        # ===== BLOCK OF 5 =====
        for i in range(BLOCK_SIZE):
            cones.append((x, TRACK_WIDTH / 2, 'b'))   # BLUE LEFT
            cones.append((x, -TRACK_WIDTH / 2, 'y'))  # YELLOW RIGHT
            x += CONE_SPACING

        # ===== BIG GAP =====
        x += GAP

    return cones


SCENARIOS = {
    1: scenario_1_perfect_straight,
    2: scenario_2_missing_blue,
    3: scenario_3_missing_yellow,
    4: scenario_4_random_dropouts,
    5: scenario_5_noisy_realistic,
    6: scenario_6_block_gaps_clean
}

ALL_CONES = SCENARIOS[ACTIVE_SCENARIO]()

# ============================================================
# CAR STATE
# ============================================================

car_x, car_y, car_yaw = 0.0, 0.0, 0.0

# ============================================================
# SENSOR
# ============================================================

def get_visible_cones(cones, car_pos, yaw):
    visible = []
    heading = np.array([np.cos(yaw), np.sin(yaw)])

    for cone in cones:
        rel = np.array([cone[0], cone[1]]) - car_pos
        proj = np.dot(rel, heading)

        if -SENSOR_BACKWARD_RANGE < proj < SENSOR_FORWARD_RANGE:
            visible.append(cone)

    return visible

# ============================================================
# PLOT (MINIMAL OBJECTS)
# ============================================================

fig, ax = plt.subplots(figsize=(12, 6))

real_scatter = ax.scatter([], [], s=60)
virtual_scatter = ax.scatter([], [], s=120, marker='*')

car_dot, = ax.plot([], [], 'ro')
yaw_line, = ax.plot([], [], 'r-', lw=2)
path_line, = ax.plot([], [], 'g-', lw=2)

ax.set_aspect('equal')
ax.grid(True)

# ============================================================
# UPDATE
# ============================================================

def update(frame):
    global car_x, car_y, car_yaw

    # Move car
    car_x += CAR_SPEED * DT
    car_yaw = 0.03 * np.sin(car_x * 0.05)

    car_pos = np.array([car_x, car_y])

    # Visible cones
    visible = get_visible_cones(ALL_CONES, car_pos, car_yaw)

    # Planner
    path, _ = planner.execute_cycle(visible, [(car_x, car_y, car_yaw)])

    balanced, _ = planner.virtual_cone_generator.generate_balanced_cones(
        visible, car_pos, car_yaw
    )

    # ========================================================
    # SPLIT DATA (FAST)
    # ========================================================

    real_pts = []
    real_colors = []

    virt_pts = []
    virt_colors = []

    for x, y, color, is_virtual in balanced:
        if is_virtual:
            virt_pts.append([x, y])
            virt_colors.append('orange' if color == 'y' else 'cyan')
        else:
            real_pts.append([x, y])
            real_colors.append('gold' if color == 'y' else 'blue')

    # ========================================================
    # UPDATE PLOTS
    # ========================================================

    if real_pts:
        real_scatter.set_offsets(np.array(real_pts))
        real_scatter.set_color(real_colors)
    else:
        real_scatter.set_offsets(np.empty((0, 2)))

    if virt_pts:
        virtual_scatter.set_offsets(np.array(virt_pts))
        virtual_scatter.set_color(virt_colors)
    else:
        virtual_scatter.set_offsets(np.empty((0, 2)))

    # Car
    car_dot.set_data([car_x], [car_y])

    dx = np.cos(car_yaw) * 2
    dy = np.sin(car_yaw) * 2

    yaw_line.set_data([car_x, car_x + dx], [car_y, car_y + dy])

    # Path
    if path and len(path) > 1:
        px = [p[0] for p in path]
        py = [p[1] for p in path]
        path_line.set_data(px, py)
    else:
        path_line.set_data([], [])

    # Camera
    ax.set_xlim(car_x - 10, car_x + 25)
    ax.set_ylim(-10, 10)

    ax.set_title(f"Lightweight Mode | X={car_x:.2f}")

    return real_scatter, virtual_scatter, car_dot, yaw_line, path_line

# ============================================================
# RUN
# ============================================================

ani = FuncAnimation(fig, update, interval=100)
plt.show()