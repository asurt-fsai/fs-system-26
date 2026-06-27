import argparse
import logging
import signal
import threading
import tkinter as tk
import math

import rclpy

from supervisor.helpers.GUI.ros_node import ROSNode
from supervisor.helpers.GUI.widgets import Dashboard

# ===== RED/BLACK RACING THEME =====
BG = "#000000"
CARD = "#0a0a0a"
CARD_LIGHT = "#111111"
RED = "#ff0000"
RED_DARK = "#8b0000"
RED_GLOW = "#cc0000"
TXT = "#ffffff"
TXT_DIM = "#888888"


class SteeringWheel:
    """Custom steering wheel visualization with left/right/center markings"""
    def __init__(self, parent, x, y, size=180):
        self.parent = parent
        self.x = x
        self.y = y
        self.size = size
        self.angle = 0
        
        # Create canvas for steering wheel
        self.canvas = tk.Canvas(
            parent, 
            width=size, 
            height=size, 
            bg=BG, 
            highlightthickness=0
        )
        self.canvas.place(x=x-size//2, y=y-size//2)
        
        self.draw_wheel()
    
    def draw_wheel(self):
        """Draw the steering wheel with direction markings"""
        self.canvas.delete("all")
        
        center = self.size // 2
        radius = self.size // 2 - 10
        
        # Outer ring
        self.canvas.create_oval(
            center-radius, center-radius, 
            center+radius, center+radius,
            outline=RED, width=4, fill=""
        )
        
        # Inner ring
        self.canvas.create_oval(
            center-radius+15, center-radius+15,
            center+radius-15, center+radius-15,
            outline=RED_DARK, width=2, fill=""
        )
        
        # Center hub
        self.canvas.create_oval(
            center-25, center-25, center+25, center+25,
            fill=RED_DARK, outline=RED, width=2
        )
        
        # Center bolt
        self.canvas.create_oval(
            center-10, center-10, center+10, center+10,
            fill=RED, outline=""
        )
        
        # LEFT marking
        left_x = center - radius + 25
        left_y = center
        self.canvas.create_text(
            left_x, left_y,
            text="L",
            fill=RED,
            font=("Arial", 14, "bold")
        )
        self.canvas.create_line(
            left_x - 10, left_y,
            left_x - 25, left_y,
            fill=RED, width=2
        )
        
        # RIGHT marking
        right_x = center + radius - 25
        right_y = center
        self.canvas.create_text(
            right_x, right_y,
            text="R",
            fill=RED,
            font=("Arial", 14, "bold")
        )
        self.canvas.create_line(
            right_x + 10, right_y,
            right_x + 25, right_y,
            fill=RED, width=2
        )
        
        # CENTER marking (top)
        center_y = center - radius + 25
        self.canvas.create_text(
            center, center_y,
            text="▲",
            fill=RED,
            font=("Arial", 16, "bold")
        )
        
        # Spokes (rotated)
        spoke_length = radius - 25
        for i in range(3):
            angle_rad = math.radians(self.angle + i * 120)
            x1 = center + math.cos(angle_rad) * 20
            y1 = center + math.sin(angle_rad) * 20
            x2 = center + math.cos(angle_rad) * spoke_length
            y2 = center + math.sin(angle_rad) * spoke_length
            self.canvas.create_line(x1, y1, x2, y2, fill=RED, width=3)
        
        # Grip markers
        for i in range(4):
            angle_rad = math.radians(self.angle + i * 90)
            x = center + math.cos(angle_rad) * (radius - 8)
            y = center + math.sin(angle_rad) * (radius - 8)
            self.canvas.create_oval(x-4, y-4, x+4, y+4, fill=RED, outline="")
        
        # Center logo text
        self.canvas.create_text(
            center, center, 
            text="F1", 
            fill=TXT, 
            font=("Arial", 14, "bold")
        )
    
    def update_steering(self, steering_angle):
        """Update steering wheel angle"""
        self.angle = steering_angle * 45
        self.draw_wheel()


class Speedometer:
    """Speedometer visualization"""
    def __init__(self, parent, x, y, size=180):
        self.parent = parent
        self.x = x
        self.y = y
        self.size = size
        self.speed = 0
        
        self.canvas = tk.Canvas(
            parent,
            width=size,
            height=size,
            bg=BG,
            highlightthickness=0
        )
        self.canvas.place(x=x-size//2, y=y-size//2)
        
        self.draw_speedometer()
    
    def draw_speedometer(self):
        """Draw the speedometer"""
        self.canvas.delete("all")
        
        center = self.size // 2
        radius = self.size // 2 - 10
        
        # Outer circle
        self.canvas.create_oval(
            center-radius, center-radius,
            center+radius, center+radius,
            outline=RED, width=3, fill=CARD
        )
        
        # Inner circle
        self.canvas.create_oval(
            center-radius+10, center-radius+10,
            center+radius-10, center+radius-10,
            outline=RED_DARK, width=1, fill=""
        )
        
        # Speed markings (0 to 30 m/s)
        for i in range(0, 31, 5):
            angle = -150 + (i / 30) * 300
            angle_rad = math.radians(angle)
            
            x1 = center + math.cos(angle_rad) * (radius - 15)
            y1 = center + math.sin(angle_rad) * (radius - 15)
            x2 = center + math.cos(angle_rad) * (radius - 5)
            y2 = center + math.sin(angle_rad) * (radius - 5)
            
            self.canvas.create_line(x1, y1, x2, y2, fill=TXT_DIM, width=2)
            
            # Add numbers
            if i % 10 == 0:
                x_text = center + math.cos(angle_rad) * (radius - 25)
                y_text = center + math.sin(angle_rad) * (radius - 25)
                self.canvas.create_text(
                    x_text, y_text, 
                    text=str(i), 
                    fill=TXT_DIM, 
                    font=("Arial", 9, "bold")
                )
        
        # Speed needle
        self.needle = self.canvas.create_line(
            center, center, center, center-radius+20,
            fill=RED, width=3, arrow="last"
        )
        
        # Center cap
        self.canvas.create_oval(
            center-12, center-12, center+12, center+12,
            fill=RED_DARK, outline=RED, width=2
        )
        
        # Digital speed display
        self.digital_speed = self.canvas.create_text(
            center, center+45,
            text="0.00",
            fill=RED,
            font=("Arial", 16, "bold")
        )
        
        self.canvas.create_text(
            center, center+60,
            text="M/S",
            fill=TXT_DIM,
            font=("Arial", 9)
        )
    
    def update_speed(self, speed):
        """Update speedometer needle"""
        self.speed = speed
        center = self.size // 2
        radius = self.size // 2 - 10
        
        max_speed = 30.0
        percentage = min(1.0, speed / max_speed)
        angle = -150 + percentage * 300
        
        angle_rad = math.radians(angle)
        x = center + math.cos(angle_rad) * (radius - 20)
        y = center + math.sin(angle_rad) * (radius - 20)
        
        self.canvas.coords(self.needle, center, center, x, y)
        self.canvas.itemconfig(self.digital_speed, text=f"{speed:.2f}")
        
        # Change color at high speeds
        if speed > 25:
            self.canvas.itemconfig(self.digital_speed, fill="#ff4444")
            self.canvas.itemconfig(self.needle, fill="#ff4444")
        elif speed > 15:
            self.canvas.itemconfig(self.digital_speed, fill=RED)
            self.canvas.itemconfig(self.needle, fill=RED)
        else:
            self.canvas.itemconfig(self.digital_speed, fill=RED_DARK)
            self.canvas.itemconfig(self.needle, fill=RED_DARK)


class FinishCelebration:
    """Finish line celebration effect"""
    def __init__(self, parent):
        self.parent = parent
        self.active = False
        self.flag_canvas = None
        self.message_frame = None
        self.confetti_particles = []
        
    def start_celebration(self):
        """Start finish celebration"""
        if self.active:
            return
            
        self.active = True
        self.create_checkered_flag()
        self.create_confetti()
        self.show_finish_message()
        
    def create_checkered_flag(self):
        """Create waving checkered flag"""
        self.flag_canvas = tk.Canvas(
            self.parent,
            width=400,
            height=250,
            bg=BG,
            highlightthickness=0
        )
        self.flag_canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Create checkered pattern
        for i in range(0, 400, 40):
            for j in range(0, 250, 25):
                if (i//40 + j//25) % 2 == 0:
                    self.flag_canvas.create_rectangle(i, j, i+40, j+25, fill=RED, outline="")
                else:
                    self.flag_canvas.create_rectangle(i, j, i+40, j+25, fill=TXT, outline="")
        
    def create_confetti(self):
        """Create confetti effect"""
        import random
        self.confetti_particles = []
        for _ in range(80):
            x = random.randint(50, self.parent.winfo_width() - 50)
            y = random.randint(0, 50)
            color = random.choice([RED, "#ff3333", "#ff5555", "#ff7777"])
            particle = tk.Frame(self.parent, bg=color, width=5, height=5)
            particle.place(x=x, y=y)
            self.confetti_particles.append((particle, random.randint(2, 5), random.randint(3, 7)))
        
        self.animate_confetti()
    
    def animate_confetti(self):
        """Animate confetti falling"""
        if self.active:
            for particle, x_vel, y_vel in self.confetti_particles:
                try:
                    x = particle.winfo_x() + x_vel
                    y = particle.winfo_y() + y_vel
                    particle.place(x=x, y=y)
                    
                    if y > 700:
                        particle.place(x=particle.winfo_x(), y=0)
                except:
                    pass
            
            self.parent.after(50, self.animate_confetti)
    
    def show_finish_message(self):
        """Show finish message"""
        self.message_frame = tk.Frame(self.parent, bg=BG)
        self.message_frame.place(relx=0.5, rely=0.3, anchor=tk.CENTER)
        
        tk.Label(
            self.message_frame,
            text="🏁 FINISH LINE! 🏁",
            font=("Arial", 36, "bold"),
            bg=BG,
            fg=RED
        ).pack()
        
        tk.Label(
            self.message_frame,
            text="MISSION COMPLETE",
            font=("Arial", 18, "bold"),
            bg=BG,
            fg=TXT
        ).pack()
        
        # Auto hide after 3 seconds
        self.parent.after(3000, self.hide_celebration)
    
    def hide_celebration(self):
        """Hide celebration effects"""
        self.active = False
        if self.flag_canvas:
            self.flag_canvas.destroy()
            self.flag_canvas = None
        if self.message_frame:
            self.message_frame.destroy()
            self.message_frame = None
        for particle, _, _ in self.confetti_particles:
            try:
                particle.destroy()
            except:
                pass
        self.confetti_particles = []
    
    def stop(self):
        """Stop celebration effects"""
        self.hide_celebration()


class StaticMissionGUI:
    def __init__(self, mission_name: str):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.root = tk.Tk()
        self.root.title("F1 AI - RACING CONTROL")
        self.root.geometry("1400x650")
        self.root.configure(bg=BG)

        self.mission_name = mission_name
        self.mission_complete = False

        # ORIGINAL LABELS - EXACT POSITIONS
        labels = [
            ("Mission Type", 0.2, 0.40),
            ("Mission State", 0.4, 0.40),
            ("Velocity", 0.6, 0.40),
            ("Steering", 0.8, 0.40),
        ]

        for text, relx, rely in labels:
            label = tk.Label(
                self.root,
                text=text,
                font=("Arial", 12, "bold"),
                background=BG,
                fg=TXT,
            )
            label.place(relx=relx, rely=rely, anchor=tk.CENTER)

        # ORIGINAL MISSION LABEL
        self.mission_label = tk.Label(
            self.root,
            text=mission_name,
            font=("Arial", 11),
            background=BG,
            fg=TXT,
        )
        self.mission_label.place(relx=0.2, rely=0.6, anchor=tk.CENTER)

        # ORIGINAL DASHBOARD - ATTACHED TO ROOT EXACTLY AS BEFORE
        self.dashboard = Dashboard(self.root)

        self.node = ROSNode(self._handle_ros_update)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # ADD VISUAL ELEMENTS (without changing existing layout)
        # Add steering wheel at bottom left
        self.steering_wheel = SteeringWheel(self.root, 200, 550, 160)
        
        # Add speedometer at bottom right
        self.speedometer = Speedometer(self.root, 1200, 550, 160)
        
        # Add header with custom font (top of window, doesn't affect existing elements)
        self._add_header()
        
        # Add status text
        self.status_text = tk.Label(
            self.root,
            text="● SYSTEM READY",
            font=("Arial", 10, "bold"),
            background=BG,
            fg=RED_DARK,
        )
        self.status_text.place(relx=0.02, rely=0.02)
        
        # Add status dot
        self.status_dot = tk.Canvas(self.root, width=10, height=10, bg=BG, highlightthickness=0)
        self.status_dot.place(relx=0.95, rely=0.02)
        self._animate_red_dot()
        
        self.finish_celebration = FinishCelebration(self.root)

    def _add_header(self):
        """Add header with custom font at top"""
        header_frame = tk.Frame(self.root, bg=BG)
        header_frame.place(relx=0.5, rely=0.05, anchor=tk.CENTER)
        
        # Top red line
        top_line = tk.Frame(self.root, bg=RED, height=2)
        top_line.place(relx=0, rely=0, relwidth=1)
        
        # Title with Impact font
        title = tk.Label(
            header_frame,
            text="RACING CONTROL SYSTEM",
            font=("Impact", 28, "bold"),
            bg=BG,
            fg=RED
        )
        title.pack()
        
        # Red line under title
        line = tk.Frame(self.root, bg=RED_DARK, height=1)
        line.place(relx=0.2, rely=0.09, relwidth=0.6)

    def _animate_red_dot(self):
        """Animate pulsing red dot"""
        self.dot_state = not getattr(self, 'dot_state', False)
        
        self.status_dot.delete("all")
        if self.dot_state:
            self.status_dot.create_oval(2, 2, 8, 8, fill=RED, outline=RED_GLOW, width=1)
        else:
            self.status_dot.create_oval(2, 2, 8, 8, fill=RED, outline="")
        
        self.root.after(500, self._animate_red_dot)

    def _handle_ros_update(self, kind, *args):
        if kind == "cmd":
            vel, steer = args
            # Update visualizations
            self.root.after(0, self.speedometer.update_speed, vel)
            self.root.after(0, self.steering_wheel.update_steering, steer)
            # Update original dashboard
            self.root.after(0, self.dashboard.update_cmd, vel, steer)
            self.logger.info(f"[StaticGUI] cmd speed={vel} steer={steer}")
            
            # Check for mission completion
            if not self.mission_complete and vel < 0.1 and hasattr(self, 'mission_finished'):
                self.mission_complete = True
                self.root.after(0, self._on_mission_complete)
                
        elif kind == "state":
            (state,) = args
            self.root.after(0, self.dashboard.update_state, state)
            self._update_status_text(state)
            self.logger.info(f"[StaticGUI] as_state={state}")
            
            if state == 3:  # Finished
                self.mission_finished = True
                
        elif kind == "mission_state":
            (state,) = args
            self.root.after(0, self.dashboard.update_state, state)
            self.logger.info(f"[StaticGUI] mission_state={state}")
            
            if state == 3:  # Mission complete
                self.mission_finished = True

    def _update_status_text(self, state):
        """Update status text based on state"""
        if state == 2:  # Running
            self.status_text.configure(text="● MISSION ACTIVE", fg=RED)
        elif state == 3:  # Finished
            self.status_text.configure(text="● MISSION COMPLETE", fg="#00ff00")
        else:
            self.status_text.configure(text="● SYSTEM READY", fg=RED_DARK)

    def _on_mission_complete(self):
        """Handle mission completion"""
        self.finish_celebration.start_celebration()
        self.status_text.configure(text="● MISSION COMPLETE!", fg="#00ff00")

    def _on_close(self):
        try:
            self.finish_celebration.stop()
            self.node.destroy_node()
        finally:
            if rclpy.ok():
                rclpy.shutdown()
            self.root.destroy()

    def _handle_signal(self, _signum, _frame):
        self.root.after(0, self._on_close)

    def run(self):
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        def _spin():
            try:
                rclpy.spin(self.node)
            except Exception as exc:
                if not rclpy.ok():
                    return
                raise exc

        ros_thread = threading.Thread(target=_spin, daemon=True)
        ros_thread.start()
        self.root.mainloop()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mission", default="Static")
    args = parser.parse_args()

    rclpy.init(args=None)

    gui = StaticMissionGUI(args.mission)
    gui.run()


if __name__ == "__main__":
    main()