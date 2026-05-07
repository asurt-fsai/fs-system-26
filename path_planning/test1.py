import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from modules.planner import PathPlanner

# ============================================================
# CONFIG
# ============================================================

ACTIVE_SCENARIO = 7

TRACK_LENGTH = 140
TRACK_WIDTH = 3
CONE_SPACING = 5

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
def scenario_7_heavy_noise():
    """
    Simulates high-jitter cone positions and frequent sensor dropouts.
    Useful for testing the robustness of Theta* and virtual cone generation.
    """
    cones = []
    rng = np.random.default_rng(99) # New seed for variety

    for x in np.arange(0, TRACK_LENGTH, CONE_SPACING):
        # 30% chance of missing a cone (High Dropout)
        # Jitter of 0.45m (Very Noisy)
        
        if rng.random() > 0.30:
            cones.append((
                x + rng.normal(0, 0.45),
                TRACK_WIDTH / 2 + rng.normal(0, 0.45),
                'b'
            ))

        if rng.random() > 0.30:
            cones.append((
                x + rng.normal(0, 0.45),
                -TRACK_WIDTH / 2 + rng.normal(0, 0.45),
                'y'
            ))

    return cones


SCENARIOS = {
    1: scenario_1_perfect_straight,
    2: scenario_2_missing_blue,
    3: scenario_3_missing_yellow,
    4: scenario_4_random_dropouts,
    5: scenario_5_noisy_realistic,
    6: scenario_6_block_gaps_clean,
    7: scenario_7_heavy_noise
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
    path = planner.execute_cycle(visible, [(car_x, car_y, car_yaw)])

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