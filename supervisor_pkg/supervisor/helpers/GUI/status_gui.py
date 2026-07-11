import os
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext

import rclpy
from rclpy.node import Node
from asurt_msgs.msg import NodeStatus

# ===== RACING THEME COLORS (matching main GUI) =====
BG = "#0a0a0a"  # Main background
CARD = "#1a1a1a"  # Card background
PANEL = "#1a1a1a"  # Panel background (consistent with CARD)
CARD_DARK = "#121212"  # Darker card background
HEADER = "#e63946"  # Red primary for headers
HEADER_DARK = "#b71c1c"  # Dark red for headers
TXT = "#ffffff"  # Primary text
TXT_DIM = "#888888"  # Dimmed text
TXT_HINT = "#555555"  # Hint text

# Status colors
RUNNING = "#00d68f"  # Green for running
STARTING = "#f39c12"  # Yellow/orange for starting
ERROR = "#e63946"  # Red for error
INACTIVE = "#555555"  # Gray for inactive
UNRESPONSIVE = "#8b0000"  # Dark red for unresponsive
READY = "#3498db"  # Blue for ready

# Constants
INACTIVE_THRESHOLD = 5


def map_state_to_str(state_int: int) -> str:
    return {
        NodeStatus.STARTING: "STARTING",
        NodeStatus.READY: "READY",
        NodeStatus.RUNNING: "RUNNING",
        NodeStatus.ERROR: "ERROR",
        NodeStatus.SHUTDOWN: "SHUTDOWN",
        NodeStatus.UNRESPONSIVE: "UNRESPONSIVE",
    }.get(state_int, "UNKNOWN")


class ModernTreeview(ttk.Treeview):
    """Custom Treeview with modern styling"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configure custom styles
        style = ttk.Style()
        style.theme_use("clam")
        
        # Treeview style
        style.configure(
            "Modern.Treeview",
            background=CARD,
            foreground=TXT,
            fieldbackground=CARD,
            borderwidth=0,
            font=("Segoe UI", 11),
            rowheight=35
        )
        
        style.map(
            "Modern.Treeview",
            background=[('selected', HEADER_DARK)],
            foreground=[('selected', TXT)]
        )
        
        # Heading style
        style.configure(
            "Modern.Treeview.Heading",
            background=CARD_DARK,
            foreground=RED_PRIMARY if 'RED_PRIMARY' in globals() else HEADER,
            font=("Arial", 12, "bold"),
            borderwidth=0
        )
        
        style.map(
            "Modern.Treeview.Heading",
            background=[('active', CARD_DARK)]
        )


class NodeStatusGUI(Node):
    def __init__(self):
        super().__init__("node_status_gui")

        self.root = tk.Tk()
        self.root.title("Racing Supervisor - Node Status Monitor")
        self.root.geometry("900x550")
        self.root.configure(bg=BG)
        self.root.minsize(800, 500)
        
        # Set window icon if available
        try:
            self.root.iconbitmap(default='icon.ico')
        except:
            pass

        self._setup_ui()
        
        # key=node/module name, value=(state_int, status_str, heartbeat_str, last_rx_time)
        self.node_data = {}
        self.lock = threading.Lock()

        # Heartbeat monitor topic used by supervisor and restart logic
        self.create_subscription(NodeStatus, "/module_heartbeat", self.status_callback, 10)

        self.update_gui()

    def _setup_ui(self):
        # Main container with padding
        main_container = tk.Frame(self.root, bg=BG)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header section
        header_frame = tk.Frame(main_container, bg=CARD)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Title with icon
        title_label = tk.Label(
            header_frame,
            text="● NODE STATUS MONITOR",
            bg=CARD,
            fg=RED_PRIMARY if 'RED_PRIMARY' in globals() else HEADER,
            font=("Arial", 16, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=15, pady=12)
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Real-time module health monitoring",
            bg=CARD,
            fg=TXT_DIM,
            font=("Arial", 10)
        )
        subtitle_label.pack(side=tk.RIGHT, padx=15, pady=12)
        
        # Separator
        separator = tk.Frame(main_container, bg=RED_PRIMARY if 'RED_PRIMARY' in globals() else HEADER, height=2)
        separator.pack(fill=tk.X, pady=(0, 15))
        
        # Create custom treeview
        self._create_treeview(main_container)
        
        # Status bar at bottom
        self._create_status_bar(main_container)

    def _create_treeview(self, parent):
        # Create frame for treeview
        tree_frame = tk.Frame(parent, bg=CARD)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        # Create treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("Node", "Status", "Last Heartbeat"),
            show="headings",
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            height=15
        )
        
        # Configure scrollbars
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
        
        # Configure columns
        self.tree.heading("Node", text="Node / Module Name")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Last Heartbeat", text="Last Heartbeat")
        
        self.tree.column("Node", width=380, minwidth=200)
        self.tree.column("Status", width=140, minwidth=100)
        self.tree.column("Last Heartbeat", width=220, minwidth=150)
        
        # Configure tags for status colors
        self.tree.tag_configure("running", background=RUNNING, foreground="#0a0a0a", font=("Segoe UI", 11, "bold"))
        self.tree.tag_configure("ready", background=READY, foreground="#ffffff", font=("Segoe UI", 11, "bold"))
        self.tree.tag_configure("starting", background=STARTING, foreground="#0a0a0a", font=("Segoe UI", 11, "bold"))
        self.tree.tag_configure("error", background=ERROR, foreground="#ffffff", font=("Segoe UI", 11, "bold"))
        self.tree.tag_configure("unresponsive", background=UNRESPONSIVE, foreground="#ffffff", font=("Segoe UI", 11, "bold"))
        self.tree.tag_configure("inactive", background=INACTIVE, foreground=TXT_DIM, font=("Segoe UI", 11))
        self.tree.tag_configure("shutdown", background=INACTIVE, foreground=TXT_DIM, font=("Segoe UI", 11))
        
        # Layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click event for details
        self.tree.bind("<Double-1>", self._on_node_double_click)

    def _create_status_bar(self, parent):
        status_bar = tk.Frame(parent, bg=CARD_DARK, height=40)
        status_bar.pack(fill=tk.X, pady=(15, 0))
        status_bar.pack_propagate(False)
        
        # Status indicators
        indicators_frame = tk.Frame(status_bar, bg=CARD_DARK)
        indicators_frame.pack(side=tk.LEFT, padx=15, pady=8)
        
        # Running indicator
        running_indicator = tk.Frame(indicators_frame, bg=RUNNING, width=12, height=12)
        running_indicator.pack(side=tk.LEFT, padx=(0, 5))
        running_indicator.pack_propagate(False)
        tk.Label(indicators_frame, text="RUNNING", bg=CARD_DARK, fg=RUNNING, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 15))
        
        # Ready indicator
        ready_indicator = tk.Frame(indicators_frame, bg=READY, width=12, height=12)
        ready_indicator.pack(side=tk.LEFT, padx=(0, 5))
        ready_indicator.pack_propagate(False)
        tk.Label(indicators_frame, text="READY", bg=CARD_DARK, fg=READY, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 15))
        
        # Starting indicator
        starting_indicator = tk.Frame(indicators_frame, bg=STARTING, width=12, height=12)
        starting_indicator.pack(side=tk.LEFT, padx=(0, 5))
        starting_indicator.pack_propagate(False)
        tk.Label(indicators_frame, text="STARTING", bg=CARD_DARK, fg=STARTING, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 15))
        
        # Error indicator
        error_indicator = tk.Frame(indicators_frame, bg=ERROR, width=12, height=12)
        error_indicator.pack(side=tk.LEFT, padx=(0, 5))
        error_indicator.pack_propagate(False)
        tk.Label(indicators_frame, text="ERROR", bg=CARD_DARK, fg=ERROR, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 15))
        
        # Inactive indicator
        inactive_indicator = tk.Frame(indicators_frame, bg=INACTIVE, width=12, height=12)
        inactive_indicator.pack(side=tk.LEFT, padx=(0, 5))
        inactive_indicator.pack_propagate(False)
        tk.Label(indicators_frame, text="INACTIVE", bg=CARD_DARK, fg=INACTIVE, font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        # Stats label on right
        self.stats_label = tk.Label(
            status_bar,
            text="0 nodes monitored",
            bg=CARD_DARK,
            fg=TXT_DIM,
            font=("Arial", 9)
        )
        self.stats_label.pack(side=tk.RIGHT, padx=15)

    def _read_module_log(self, node_name, tail=40):
        log_path = os.path.join(
            os.path.expanduser("~/.ros/logs/supervisor_modules"),
            f"{node_name}.log"
        )
        if not os.path.exists(log_path):
            return None, log_path
        try:
            with open(log_path, "r") as f:
                lines = f.readlines()
            return "".join(lines[-tail:]), log_path
        except Exception as e:
            return f"[Error reading log: {e}]", log_path

    def _on_node_double_click(self, event):
        """Show detailed info and last log lines when double-clicking a node."""
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        node_name = item['values'][0]
        status = item['values'][1]
        heartbeat = item['values'][2]

        accent = RED_PRIMARY if 'RED_PRIMARY' in globals() else HEADER

        popup = tk.Toplevel(self.root)
        popup.title(f"Node Details — {node_name}")
        popup.geometry("640x480")
        popup.configure(bg=CARD)
        popup.resizable(True, True)
        popup.transient(self.root)
        popup.grab_set()

        details_frame = tk.Frame(popup, bg=CARD, padx=15, pady=10)
        details_frame.pack(fill=tk.X)

        tk.Label(details_frame, text="NODE INFORMATION", bg=CARD, fg=accent,
                 font=("Arial", 13, "bold")).pack(anchor="w", pady=(0, 6))

        tk.Label(details_frame, text=f"Name: {node_name}", bg=CARD, fg=TXT,
                 font=("Arial", 10)).pack(anchor="w")
        tk.Label(details_frame, text=f"Status: {status}", bg=CARD,
                 fg=self._get_status_color(status),
                 font=("Arial", 10, "bold")).pack(anchor="w")
        tk.Label(details_frame, text=f"Last Heartbeat: {heartbeat}", bg=CARD, fg=TXT,
                 font=("Arial", 10)).pack(anchor="w")

        # Log section
        sep = tk.Frame(popup, bg=accent, height=1)
        sep.pack(fill=tk.X, padx=15, pady=6)

        log_content, log_path = self._read_module_log(node_name)

        log_label = tk.Label(popup,
                             text=f"LOG  ({log_path})",
                             bg=CARD, fg=TXT_DIM, font=("Courier", 8))
        log_label.pack(anchor="w", padx=15)

        log_box = scrolledtext.ScrolledText(
            popup, bg="#0d0d0d", fg="#cccccc",
            font=("Courier", 9), wrap=tk.WORD,
            state=tk.DISABLED, height=18
        )
        log_box.pack(fill=tk.BOTH, expand=True, padx=15, pady=(4, 0))

        def _load_log(text_widget, content):
            text_widget.config(state=tk.NORMAL)
            text_widget.delete("1.0", tk.END)
            if content is None:
                text_widget.insert(tk.END, "[No log file found — module not yet launched or log dir missing]")
            else:
                text_widget.insert(tk.END, content)
            text_widget.see(tk.END)
            text_widget.config(state=tk.DISABLED)

        _load_log(log_box, log_content)

        btn_frame = tk.Frame(popup, bg=CARD)
        btn_frame.pack(fill=tk.X, padx=15, pady=8)

        tk.Button(
            btn_frame, text="Refresh",
            command=lambda: _load_log(log_box, self._read_module_log(node_name)[0]),
            bg="#333333", fg=TXT, font=("Arial", 9, "bold"), cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            btn_frame, text="Close",
            command=popup.destroy,
            bg=accent, fg=TXT, font=("Arial", 9, "bold"), cursor="hand2"
        ).pack(side=tk.LEFT)

    def _get_status_color(self, status):
        """Return color for status text"""
        status_colors = {
            "RUNNING": RUNNING,
            "READY": READY,
            "STARTING": STARTING,
            "ERROR": ERROR,
            "UNRESPONSIVE": UNRESPONSIVE,
            "SHUTDOWN": INACTIVE
        }
        return status_colors.get(status, TXT)

    def status_callback(self, msg: NodeStatus):
        node_name = msg.message if msg.message else "unknown"
        status_str = map_state_to_str(msg.status)
        heartbeat_str = time.strftime("%H:%M:%S", time.localtime(msg.header.stamp.sec or time.time()))
        with self.lock:
            self.node_data[node_name] = (msg.status, status_str, heartbeat_str, time.time())

    def _tag_for_row(self, state_int: int, last_rx_time: float) -> str:
        if time.time() - last_rx_time > INACTIVE_THRESHOLD:
            return "inactive"
        if state_int == NodeStatus.RUNNING:
            return "running"
        if state_int == NodeStatus.READY:
            return "ready"
        if state_int == NodeStatus.STARTING:
            return "starting"
        if state_int == NodeStatus.ERROR:
            return "error"
        if state_int == NodeStatus.UNRESPONSIVE:
            return "unresponsive"
        if state_int == NodeStatus.SHUTDOWN:
            return "shutdown"
        return "inactive"

    def update_gui(self):
        with self.lock:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Insert updated data
            for node_name, (state_int, status_str, heartbeat_str, last_rx_time) in sorted(self.node_data.items()):
                self.tree.insert(
                    "",
                    "end",
                    values=(node_name, status_str, heartbeat_str),
                    tags=(self._tag_for_row(state_int, last_rx_time),),
                )
            
            # Update stats label
            node_count = len(self.node_data)
            active_count = sum(1 for state_int, _, _, _ in self.node_data.values() 
                             if state_int in [NodeStatus.RUNNING, NodeStatus.READY, NodeStatus.STARTING])
            
            self.stats_label.config(text=f"{active_count}/{node_count} nodes active")
        
        # Schedule next update
        self.root.after(500, self.update_gui)

    def run(self):
        ros_thread = threading.Thread(target=rclpy.spin, args=(self,), daemon=True)
        ros_thread.start()
        self.root.mainloop()

    def shutdown(self):
        rclpy.shutdown()
        self.root.quit()
        self.root.destroy()


def main():
    rclpy.init()
    gui = NodeStatusGUI()
    try:
        gui.run()
    except KeyboardInterrupt:
        pass
    finally:
        gui.shutdown()


if __name__ == "__main__":
    main()