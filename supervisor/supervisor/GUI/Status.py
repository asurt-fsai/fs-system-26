import tkinter as tk
from tkinter import ttk
import threading
import rclpy
from rclpy.node import Node
from asurt_msgs.msg import NodeStatus
import time


BACKGROUND_COLOR ="black"
TEXT_COLOR = "white"
TABLE_HEADER_COLOR = "#8b0000"
TABLE_ROW_COLOR = "#020f12"
INACTIVE_COLOR = "#a60000"
ACTIVE_COLOR = "#195e2f"
INACTIVE_THRESHOLD = 5  # Seconds before a node is considered "inactive"

def map_state_to_str(state_int: int) -> str:
    state_map = {
        0: "starting",
        1: "ready",
        2: "running",
        3: "error",
        4: "shutdown",
        5: "unresponsive"
    }
    return state_map.get(state_int, "unknown")  # Return -1 if the state string is not found

class NodeStatusGUI(Node):
    def __init__(self):
        super().__init__('node_status_gui')
        
        self.root = tk.Tk()
        self.root.title("Node Status Monitor")
        self.root.geometry("600x400")
        self.root.configure(bg=BACKGROUND_COLOR)
        
        style=ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",background=TABLE_ROW_COLOR,
                        foreground=TEXT_COLOR,
                        fieldbackground=BACKGROUND_COLOR,
                        font=("Arial", 12))
        style.configure("Treeview.Heading",
                        background=TABLE_HEADER_COLOR,
                        foreground=TEXT_COLOR,
                        font=("Arial", 14, "bold"))  # Header Color

        style.map("Treeview", background=[("selected", "#4CAF50")])
        
        
        self.tree = ttk.Treeview(self.root, columns=("Node Name", "Status", "Last Heartbeat"), show='headings')
        self.tree.heading("Node Name", text="Node Name")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Last Heartbeat", text="Last Heartbeat")
        
        self.tree.tag_configure("active", background=ACTIVE_COLOR, foreground="white")
        self.tree.tag_configure("inactive", background=INACTIVE_COLOR, foreground="white")

        self.tree.pack(fill=tk.BOTH, expand=True)
        
        self.node_data = {}

        # **List of all known nodes in your system**
        self.known_nodes = [
            "/status/acceleration",
            "/status/simple_pure_pursuit",
            "/status/supervisor",
            "/status/lidar_orient",
            "/status/lidar",
            "/status/smoreo",
            "/status/yolov8_node",
            "/status/smornn",
            "/velodyne_points",
            "/zed/zed_node/left/image_rect_color",
            "/status/autocross",
            "/status/autonomous_demo",
            "/status/skidpad",
            "/status/staticA",
            "/status/staticB",
            "/status/placeholder_test_node",
            "/status/trackDrive",
            "/status/legoloam",
            "/status/planning_node",
            "/status/conemap",
            "/status/skidpad",
            "/status/planning_dl_node",
            "/status/perception_camera_node",
            "/status/adaptive_pure_pursuit",
            "/status/cone_mapping"
        ]

        # **Pre-load all nodes as "inactive"**
        for topic in self.known_nodes:
            node_name = topic.split("/")[-1]
            self.node_data[node_name] = ("inactive", "No heartbeat", 0)
            """
            self.create_subscription(NodeStatus, "/status/acceleration", lambda msg: self.status_callback(msg, "/status/acceleration"), 10)
            self.create_subscription(NodeStatus, "/status/simple_pure_pursuit", lambda msg: self.status_callback(msg, "/status/simple_pure_pursuit"), 10)
            self.create_subscription(NodeStatus, "/status/supervisor", lambda msg: self.status_callback(msg, "/status/supervisor"), 10)
            self.create_subscription(NodeStatus, "/status/lidar_orient", lambda msg: self.status_callback(msg, "/status/lidar_orient"), 10)
            self.create_subscription(NodeStatus, "/status/lidar", lambda msg: self.status_callback(msg, "/status/lidar"), 10)
            self.create_subscription(NodeStatus, "/status/smoreo", lambda msg: self.status_callback(msg, "/status/smoreo"), 10)
            self.create_subscription(NodeStatus, "/status/smornn", lambda msg: self.status_callback(msg, "/status/smornn"), 10)
            self.create_subscription(NodeStatus, "/darknet_ros/detection_image", lambda msg: self.status_callback(msg, "/darknet_ros/detection_image"), 10)
            self.create_subscription(NodeStatus, "/planning/waypoints", lambda msg: self.status_callback(msg, "/planning/waypoints"), 10)
            self.create_subscription(NodeStatus, "/control/cmd", lambda msg: self.status_callback(msg, "/control/cmd"), 10)
            self.create_subscription(NodeStatus, "/darknet_ros/detection_image", lambda msg: self.status_callback(msg, "/darknet_ros/detection_image"), 10)
            self.create_subscription(NodeStatus, "/velodyne_points", lambda msg: self.status_callback(msg, "/velodyne_points"), 10)
            self.create_subscription(NodeStatus, "/zed/zed_node/left/image_rect_color", lambda msg: self.status_callback(msg, "/zed/zed_node/left/image_rect_color"), 10)
            self.create_subscription(NodeStatus, "/status/autonomous_demo", lambda msg: self.status_callback(msg, "/status/autonomous_demo"), 10)
            self.create_subscription(NodeStatus, "/status/autocross", lambda msg: self.status_callback(msg, "/status/autocross"), 10)
            self.create_subscription(NodeStatus, "/status/skidpad", lambda msg: self.status_callback(msg, "/status/skidpad"), 10)
            self.create_subscription(NodeStatus, "/status/staticA", lambda msg: self.status_callback(msg, "/status/staticA"), 10)
            self.create_subscription(NodeStatus, "/status/staticB", lambda msg: self.status_callback(msg, "/status/staticB"), 10)
            self.create_subscription(NodeStatus, "/status/placeholder_test_node", lambda msg: self.status_callback(msg, "/status/placeholder_test_node"), 10)
            self.create_subscription(NodeStatus, "/status/trackDrive", lambda msg: self.status_callback(msg, "/status/trackDrive"), 10)
            self.create_subscription(NodeStatus, "/status/planning_node", lambda msg: self.status_callback(msg, "/status/planning_node"), 10)
            self.create_subscription(NodeStatus, "/status/planning_dl_node", lambda msg: self.status_callback(msg, "/status/planning_dl_node"), 10)
            self.create_subscription(NodeStatus, "/status/perception_camera_node", lambda msg: self.status_callback(msg, "/status/perception_camera_node"), 10)
            self.create_subscription(NodeStatus, "/status/adaptive_pure_pursuit", lambda msg: self.status_callback(msg, "/status/adaptive_pure_pursuit"), 10)
            self.create_subscription(NodeStatus, "/status/cone_mapping", lambda msg: self.status_callback(msg, "/status/cone_mapping"), 10)
           
            """
        for topic in self.known_nodes:
            self.create_subscription(NodeStatus, topic, lambda msg, t=topic: self.status_callback(msg, t), 10)

            


        self.lock = threading.Lock()
        self.update_gui()
    

    def status_callback(self, msg, topic_name):
        # Extract node name from topic "/status/{node_name}"
        node_name = topic_name.split("/")[-1]  # Gets last part, e.g., "acceleration"
        status = map_state_to_str (msg.status) 
        last_heartbeat = time.strftime('%H:%M:%S', time.localtime(msg.header.stamp.sec))
        last_received_time = time.time()

        #self.get_logger().info(f"🔥 Received NodeStatus: {node_name}, Status: {status}")

        with self.lock:
            self.node_data[node_name] = (status, last_heartbeat,last_received_time)
            
    def update_gui(self):
        with self.lock:
            self.tree.delete(*self.tree.get_children())
            for node_name, (status, last_heartbeat, last_received_time) in self.node_data.items():
                # Check if the node is inactive
                #if time.time() - last_received_time > INACTIVE_THRESHOLD:
                 #   continue  # Skip inserting inactive nodes

                self.tree.insert("", "end", values=(node_name, status, last_heartbeat))

        self.root.after(1000, self.update_gui)  # Update every second

    def run(self):
        ros_thread = threading.Thread(target=rclpy.spin, args=(self,), daemon=True)
        ros_thread.start()
        self.root.mainloop()
        
    def shutdown(self):
        rclpy.shutdown()


def main():
    rclpy.init()
    gui_node = NodeStatusGUI()
    gui_node.run()
    gui_node.shutdown()


if __name__ == "__main__":
    main()
