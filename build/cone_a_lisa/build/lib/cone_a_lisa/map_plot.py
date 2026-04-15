import rclpy
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

# === CONFIGURATION ===
bag_path = '/home/ubuntu/ObservedLandmarks/asurt_msgs'  # Change this to your actual full path
topic_name = '/Landmarks/Observed'

# === TYPE MAP FOR CONES ===
type_map = {
    0: 'BLUE_CONE',
    1: 'YELLOW_CONE',
    2: 'ORANGE_CONE',
    3: 'LARGE_CONE',
    4: 'UNKNOWN'
}

# === OPEN ROS 2 BAG DATABASE ===
db_path = os.path.join(bag_path, 'rosbag2_0.db3')
print(f"Reading bag database: {db_path}")
db = sqlite3.connect(db_path)
cursor = db.cursor()

# === GET MESSAGE TYPE ===
cursor.execute("SELECT type FROM topics WHERE name = ?", (topic_name,))
msg_type_str = cursor.fetchone()
if not msg_type_str:
    raise RuntimeError(f"Topic {topic_name} not found in the bag.")
msg_type = get_message(msg_type_str[0])

# === EXTRACT MESSAGES ===
cursor.execute("""
SELECT timestamp, data FROM messages 
WHERE topic_id = (SELECT id FROM topics WHERE name = ?)
""", (topic_name,))
rows = cursor.fetchall()

# === PARSE CONE POSITIONS ===
data = []
for timestamp, raw in rows:
    msg = deserialize_message(raw, msg_type)
    for lm in msg.landmarks:
        x = lm.position.x
        y = lm.position.y
        cone_type = type_map.get(lm.type, "UNKNOWN")
        data.append((x, y, cone_type))

# === CONVERT TO DATAFRAME ===
df = pd.DataFrame(data, columns=["x", "y", "type"])

# === PLOT CONE POSITIONS ===
plt.figure(figsize=(10, 8))
for cone_type in df["type"].unique():
    subset = df[df["type"] == cone_type]
    plt.scatter(subset["x"], subset["y"], s=20, label=cone_type)

plt.xlabel("X position (m)")
plt.ylabel("Y position (m)")
plt.title("Cone Positions from ROS 2 Bag")
plt.grid(True)
plt.axis("equal")
plt.legend()
plt.tight_layout()
plt.show()
