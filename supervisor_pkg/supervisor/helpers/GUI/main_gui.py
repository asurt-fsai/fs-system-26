import tkinter as tk
import logging
import os
import signal
import threading

import rclpy
from ament_index_python.packages import get_package_share_directory
from eufs_msgs.msg import CanState, VehicleCommandsStamped, WheelSpeedsStamped
from std_msgs.msg import Bool, String

from supervisor.helpers.GUI.controller import GUIController

# ===== MODERN RACING COLORS =====
BG = "#0a0a0a"
CARD = "#1a1a1a"
CARD_DARK = "#121212"
CARD_LIGHT = "#222222"
RED_PRIMARY = "#e63946"
RED_DARK = "#b71c1c"
RED_HOVER = "#ff4757"
GREEN = "#00d68f"
GREEN_DARK = "#009975"
TXT = "#ffffff"
TXT_DIM = "#888888"
TXT_HINT = "#555555"
ACCENT_BLUE = "#3498db"
ACCENT_PURPLE = "#9b59b6"
WARNING = "#f39c12"
SUCCESS = "#2ecc71"


class ModernButton(tk.Canvas):
    def __init__(self, parent, text, command, **kwargs):
        self.command = command
        self.text = text
        self.is_hovered = False
        self.is_pressed = False
        
        super().__init__(parent, highlightthickness=0, bg=CARD, **kwargs)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Configure>", self.draw_button)
        
        self.draw_button()
    
    def draw_button(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        
        if w <= 1: w = 200
        if h <= 1: h = 60
            
        if self.is_pressed:
            current_color = RED_DARK
            shift = 2
        elif self.is_hovered:
            current_color = RED_HOVER
            shift = 0
        else:
            current_color = RED_PRIMARY
            shift = 0
        
        # Main button with gradient effect
        self.create_rounded_rect(shift, shift, w-2+shift, h-2+shift, radius=10,
                                fill=current_color, outline=RED_DARK, width=2)
        
        # Text
        self.create_text(w//2 + shift, h//2 + shift, text=self.text,
                        fill=TXT, font=("Arial", 12, "bold"), anchor="center")
    
    def create_rounded_rect(self, x1, y1, x2, y2, radius=10, **kwargs):
        points = []
        for x, y in [(x1+radius, y1), (x2-radius, y1), (x2, y1), (x2, y1+radius),
                     (x2, y2-radius), (x2, y2), (x2-radius, y2), (x1+radius, y2),
                     (x1, y2), (x1, y2-radius), (x1, y1+radius), (x1, y1)]:
            points.extend([x, y])
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def on_enter(self, event):
        self.is_hovered = True
        self.draw_button()
    
    def on_leave(self, event):
        self.is_hovered = False
        self.is_pressed = False
        self.draw_button()
    
    def on_press(self, event):
        self.is_pressed = True
        self.draw_button()
    
    def on_release(self, event):
        self.is_pressed = False
        self.draw_button()
        if self.command:
            self.command()


class ToggleButton(tk.Canvas):
    def __init__(self, parent, text, command, **kwargs):
        self.command = command
        self.text = text
        self.state = False
        self.is_hovered = False
        
        super().__init__(parent, highlightthickness=0, bg=CARD, **kwargs)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<Configure>", self.draw_button)
        
        self.draw_button()
    
    def draw_button(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        
        if w <= 1: w = 200
        if h <= 1: h = 50
        
        current_color = GREEN if self.state else CARD_LIGHT
        border_color = GREEN if self.state else TXT_DIM
        
        # Main button
        self.create_rounded_rect(2, 2, w-2, h-2, radius=8,
                                fill=current_color, outline=border_color, width=2)
        
        # Status indicator
        status_color = GREEN if self.state else TXT_DIM
        self.create_oval(w-25, h//2-6, w-13, h//2+6, fill=status_color, outline="")
        
        # Text
        text_color = TXT if self.state else TXT_DIM
        status_text = "ON" if self.state else "OFF"
        self.create_text(w//2 - 15, h//2, text=self.text,
                        fill=text_color, font=("Arial", 11, "bold"), anchor="center")
        self.create_text(w//2 + 60, h//2, text=status_text,
                        fill=status_color, font=("Arial", 10, "bold"), anchor="center")
    
    def create_rounded_rect(self, x1, y1, x2, y2, radius=8, **kwargs):
        points = []
        for x, y in [(x1+radius, y1), (x2-radius, y1), (x2, y1), (x2, y1+radius),
                     (x2, y2-radius), (x2, y2), (x2-radius, y2), (x1+radius, y2),
                     (x1, y2), (x1, y2-radius), (x1, y1+radius), (x1, y1)]:
            points.extend([x, y])
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def on_enter(self, event):
        self.is_hovered = True
        self.draw_button()
    
    def on_leave(self, event):
        self.is_hovered = False
        self.draw_button()
    
    def on_click(self, event):
        self.state = not self.state
        self.draw_button()
        if self.command:
            self.command()


class StateMachinePanel:
    def __init__(self, parent, logger, on_supervisor_driving_flag=None):
        self.logger = logger
        self.on_supervisor_driving_flag = on_supervisor_driving_flag
        self.selected_mission_name = None
        if not rclpy.ok():
            rclpy.init(args=None)

        self.node = rclpy.create_node("main_gui_state_machine")

        self.as_master_pub = self.node.create_publisher(Bool, "/state_machine/as_master_switch", 1)
        self.ts_master_pub = self.node.create_publisher(Bool, "/state_machine/ts_master_switch", 1)
        self.go_signal_pub = self.node.create_publisher(Bool, "/state_machine/go_signal", 1)
        self.sdc_pub = self.node.create_publisher(Bool, "/state_machine/sdc", 1)
        self.ebs_pub = self.node.create_publisher(Bool, "/state_machine/ebs", 1)
        self.ebs_fail_pub = self.node.create_publisher(Bool, "/state_machine/ebs_fail", 1)
        self.flag_pub = self.node.create_publisher(Bool, "/state_machine/flag", 1)

        self.can_state_pub = self.node.create_publisher(CanState, "/ros_can/state", 1)
        self.mission_name_pub = self.node.create_publisher(String, "/missionName", 10)

        self.node.create_subscription(String, "/state_machine/state_str", self.state_cb, 10)
        self.node.create_subscription(Bool, "shutDownCircuit", self.sdc_cb, 10)
        self.node.create_subscription(
            Bool, "/state_machine/as_master_switch", self.as_master_cb, 10
        )
        self.node.create_subscription(
            Bool, "/state_machine/ts_master_switch", self.ts_master_cb, 10
        )
        self.node.create_subscription(
            Bool, "/state_machine/go_signal", self.go_signal_cb, 10
        )
        self.node.create_subscription(Bool, "/state_machine/sdc", self.sdc_cb, 10)
        self.node.create_subscription(Bool, "/state_machine/ebs", self.ebs_cb, 10)
        self.node.create_subscription(
            Bool, "/state_machine/ebs_fail", self.ebs_fail_cb, 10
        )
        self.node.create_subscription(Bool, "/state_machine/flag", self.flag_cb, 10)

        self.node.create_subscription(Bool, "/ros_can/mission_completed", self.mission_flag_cb, 10)
        self.node.create_subscription(
            Bool, "/supervisor/driving_flag", self.supervisor_driving_flag_cb, 10
        )
        self.node.create_subscription(
            VehicleCommandsStamped, "/ros_can/vehicle_commands", self.vehicle_commands_cb, 10
        )
        self.node.create_subscription(
            WheelSpeedsStamped, "/ros_can/wheel_speeds", self.wheel_speeds_cb, 10
        )

        self.can_state_msg = CanState()
        self.vehicle_commands_msg = VehicleCommandsStamped()
        self.wheel_speeds_msg = WheelSpeedsStamped()

        self._build_ui(parent)
        self._initialize_state()

        self._spin_thread = threading.Thread(target=rclpy.spin, args=(self.node,), daemon=True)
        self._spin_thread.start()

    def _build_ui(self, parent):
        # Header section
        header = tk.Frame(parent, bg=CARD)
        header.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            header,
            text="VEHICLE CONTROL SYSTEM",
            bg=CARD,
            fg=RED_PRIMARY,
            font=("Arial", 13, "bold")
        ).pack(side=tk.LEFT)
        
        tk.Label(
            header,
            text="STATE MACHINE",
            bg=CARD,
            fg=TXT_DIM,
            font=("Arial", 10)
        ).pack(side=tk.RIGHT)
        
        # Status display
        status_frame = tk.Frame(parent, bg=CARD_DARK, padx=15, pady=15)
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            status_frame,
            text="CURRENT STATE",
            bg=CARD_DARK,
            fg=TXT_DIM,
            font=("Arial", 9, "bold")
        ).pack(anchor="w")
        
        self.state_text = tk.Label(
            status_frame,
            text="INITIALIZING...",
            bg=CARD_DARK,
            fg=GREEN,
            font=("Arial", 18, "bold"),
            wraplength=400
        )
        self.state_text.pack(anchor="w", pady=(5, 0))
        
        # Control grid - each row has 2 buttons
        controls_frame = tk.Frame(parent, bg=CARD)
        controls_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid for 2 columns
        for i in range(2):
            controls_frame.grid_columnconfigure(i, weight=1)
        
        # Row 1: AS Master, TS Master
        self.as_master_button = ToggleButton(
            controls_frame,
            text="AS MASTER",
            command=self.toggle_as_master,
            width=180,
            height=55
        )
        self.as_master_button.grid(row=0, column=0, padx=8, pady=6, sticky="ew")
        
        self.ts_master_button = ToggleButton(
            controls_frame,
            text="TS MASTER",
            command=self.toggle_ts_master,
            width=180,
            height=55
        )
        self.ts_master_button.grid(row=0, column=1, padx=8, pady=6, sticky="ew")
        
        # Row 2: Flag
        self.flag_button = ToggleButton(
            controls_frame,
            text="FLAG",
            command=self.toggle_flag,
            width=180,
            height=55
        )
        self.flag_button.grid(row=1, column=0, padx=8, pady=6, sticky="ew")
        
        # Row 3: Go Signal, EBS
        self.go_signal_button = ToggleButton(
            controls_frame,
            text="GO SIGNAL",
            command=self.toggle_go_signal,
            width=180,
            height=55
        )
        self.go_signal_button.grid(row=2, column=0, padx=8, pady=6, sticky="ew")
        
        self.sdc_button = ToggleButton(
            controls_frame,
            text="SDC",
            command=self.toggle_sdc,
            width=180,
            height=55
        )
        self.sdc_button.grid(row=2, column=1, padx=8, pady=6, sticky="ew")
        
        self.ebs_button = ModernButton(
            controls_frame,
            text="EBS ARMED",
            command=self.toggle_ebs,
            width=180,
            height=55
        )
        self.ebs_button.grid(row=3, column=0, padx=8, pady=6, sticky="ew")
        
        # Row 4: EBS Fail, (empty placeholder)
        self.ebs_fail_button = ModernButton(
            controls_frame,
            text="EBS AVAILABLE",
            command=self.toggle_ebs_fail,
            width=180,
            height=55
        )
        self.ebs_fail_button.grid(row=3, column=0, padx=8, pady=6, sticky="ew")

        tk.Frame(controls_frame, bg=CARD).grid(row=3, column=1, padx=8, pady=6, sticky="ew")

    def _initialize_state(self):
        self.ASmaster = False
        self.TSmaster = False
        self.Flag = False

        self.GoSignal = False
        self.EBS = True
        self.EBSfail = True
        self.misson = 0
        self.mission_status = 0
        self.MissionFinished = False
        self.state = 0
        self.last_state = 0
        self.steerReq = 0
        self.torqueReq = 0
        self.steerFeedback = 0
        self.sdc = Bool()
        self.ebsTimerFlag = False
        self.readyTimerFlag = False
        self.readyTimerRunning = False
        self.lf_speed = 0
        self.rf_speed = 0
        self.lb_speed = 0
        self.rb_speed = 0
        self.directionReq = 0
        self.logger.info(
            "[GUI] Initial state: state=%s AS_MASTER=%s TS_MASTER=%s "
            "GO=%s EBS=%s EBS_FAIL=%s mission_status=%s",
            self.state,
            self.ASmaster,
            self.TSmaster,
            self.GoSignal,
            self.EBS,
            self.EBSfail,
            self.mission_status,
        )

    def _schedule_mission_publish(self):
        msg = String()
        if not self.selected_mission_name:
            return
        msg.data = self._mission_label_from_key(self.selected_mission_name)
        self.mission_name_pub.publish(msg)
        self.logger.info(f"[GUI] missionName publish={msg.data}")

    def state_cb(self, msg: String):
        self.state_text.config(text=msg.data)
        self.logger.info(f"[GUI] State machine state_str: {msg.data}")

    def sdc_cb(self, msg: Bool):
        self.sdc = msg
        self.update()

    def as_master_cb(self, msg: Bool):
        old_value = self.ASmaster
        self.ASmaster = msg.data
        if old_value != self.ASmaster:
            self.logger.info(
                "[GUI] AS_MASTER transition: %s -> %s (topic=/state_machine/as_master_switch)",
                old_value,
                self.ASmaster,
            )
        self.update()

    def ts_master_cb(self, msg: Bool):
        old_value = self.TSmaster
        self.TSmaster = msg.data
        if old_value != self.TSmaster:
            self.logger.info(
                "[GUI] TS_MASTER transition: %s -> %s (topic=/state_machine/ts_master_switch)",
                old_value,
                self.TSmaster,
            )
        self.update()

    def go_signal_cb(self, msg: Bool):
        self.GoSignal = msg.data
        self.update()

    def ebs_cb(self, msg: Bool):
        self.EBS = msg.data
        self.update()

    def ebs_fail_cb(self, msg: Bool):
        self.EBSfail = msg.data
        self.update()

    def flag_cb(self, msg: Bool):
        self.Flag = msg.data
        self.update()

    def mission_flag_cb(self, msg: Bool):
        self.MissionFinished = msg.data
        self.update()

    def supervisor_driving_flag_cb(self, msg: Bool):
        self.logger.info("[GUI] Supervisor driving_flag=%s", msg.data)

    def vehicle_commands_cb(self, msg: VehicleCommandsStamped):
        self.steerReq = msg.commands.steering
        self.torqueReq = msg.commands.torque
        self.mission_status = msg.commands.mission_status
        self.directionReq = msg.commands.direction
        self.update()

    def wheel_speeds_cb(self, msg: WheelSpeedsStamped):
        self.lf_speed = msg.speeds.lf_speed
        self.rf_speed = msg.speeds.rf_speed
        self.lb_speed = msg.speeds.lb_speed
        self.rb_speed = msg.speeds.rb_speed
        self.steerFeedback = msg.speeds.steering
        self.update()

    def set_mission(self, label, ami_state, mission_status):
        self.logger.info(f"[FLOW] set_mission entered: label={label} ami_state={ami_state}")
        self.state_text.configure(text=label)
        self.can_state_msg.ami_state = ami_state
        self._publish_can_state()
        self.misson = ami_state
        self.mission_status = mission_status
        self.steerReq = 0
        self.torqueReq = 0
        self.steerFeedback = 0
        self.directionReq = 0
        self.selected_mission_name = self._mission_key_from_label(label)
        self._schedule_mission_publish()
        self.logger.info(
            f"[GUI] State machine mission set: label={label} ami_state={ami_state} mission_status={mission_status}"
        )

    def _mission_key_from_label(self, label):
        mapping = {
            "Static A": "StaticA",
            "Static B": "StaticB",
            "Autonomus Demo": "AutoDemo",
            "AutoDemo": "AutoDemo",
        }
        return mapping.get(label)

    def _mission_label_from_key(self, key):
        mapping = {
            "StaticA": "Static A",
            "StaticB": "Static B",
            "AutoDemo": "AutoDemo",
        }
        return mapping.get(key, "")

    def infer_static_mission(self):
        if self.selected_mission_name:
            return self.selected_mission_name
        label = self.state_text.cget("text")
        inferred = self._mission_key_from_label(label)
        if inferred:
            return inferred
        ami_map = {18: "StaticA", 19: "StaticB", 15: "AutoDemo"}
        return ami_map.get(self.misson)

    def toggle_as_master(self):
        msg = Bool()
        msg.data = not self.ASmaster
        self.as_master_pub.publish(msg)
        self.ASmaster = not self.ASmaster
        self.update()
        self.logger.info(f"[GUI] AS MASTER -> {self.ASmaster}")

    def toggle_ts_master(self):
        msg = Bool()
        msg.data = not self.TSmaster
        self.ts_master_pub.publish(msg)
        self.TSmaster = not self.TSmaster
        self.update()
        self.logger.info(f"[GUI] TS MASTER -> {self.TSmaster}")

    def toggle_go_signal(self):
        msg = Bool()
        msg.data = not self.GoSignal
        self.go_signal_pub.publish(msg)
        self.GoSignal = not self.GoSignal
        self.update()
        self.logger.info(f"[GUI] GO SIGNAL -> {self.GoSignal}")

    def toggle_sdc(self):
        msg = Bool()
        msg.data = not self.sdc.data
        self.sdc.data = msg.data
        self.sdc_pub.publish(msg)
        self.update()
        self.logger.info(f"[GUI] SDC -> {self.sdc.data}")

    def toggle_ebs(self):
        msg = Bool()
        msg.data = not self.EBS
        self.ebs_pub.publish(msg)
        self.EBS = not self.EBS
        button_text = "EBS TRIGGERED" if not self.EBS else "EBS ARMED"
        self.ebs_button.text = button_text
        self.ebs_button.draw_button()
        self.update()
        self.logger.info(f"[GUI] EBS -> {self.EBS}")

    def toggle_ebs_fail(self):
        msg = Bool()
        msg.data = not self.EBSfail
        self.ebs_fail_pub.publish(msg)
        self.EBSfail = not self.EBSfail
        button_text = "EBS UNAVAILABLE" if not self.EBSfail else "EBS AVAILABLE"
        self.ebs_fail_button.text = button_text
        self.ebs_fail_button.draw_button()
        self.update()
        self.logger.info(f"[GUI] EBS FAIL -> {self.EBSfail}")

    def toggle_flag(self):
        msg = Bool()
        msg.data = not self.Flag
        self.flag_pub.publish(msg)
        self.Flag = not self.Flag
        self.update()
        self.logger.info(f"[GUI] FLAG -> {self.Flag}")


    def update(self):
        if self.state == 0:
            self.ebsTimerFlag = False
            self.readyTimerFlag = False
            self.readyTimerRunning = False
            if self.ASmaster and self.TSmaster and self.EBS and self.mission_status:
                self.state = 1
                self.can_state_msg.as_state = 1
                self._publish_can_state()

        if self.state == 1:
            if not self.ASmaster:
                self.state = 0
                self.can_state_msg.as_state = 0
                self._publish_can_state()
            elif not self.EBS:
                self.state = 3
                self.can_state_msg.as_state = 3
                self._publish_can_state()
            elif self.sdc.data is True:
                self.state = 3
                self.can_state_msg.as_state = 3
                self._publish_can_state()
                self.update()
            elif (
                self.directionReq == 0
                and self.torqueReq == 0
                and self.steerReq == 0
                and abs(self.steerFeedback) < 5
            ):
                if not self.readyTimerRunning and not self.readyTimerFlag:
                    self._check_timer(5, False, True)
                if self.readyTimerFlag and self.GoSignal is True:
                    self.state = 2
                    self.can_state_msg.as_state = 2
                    self._publish_can_state()

        elif self.state == 2:
            if not self.EBS:
                self.state = 3
                self.can_state_msg.as_state = 3
                self._publish_can_state()
                self.update()
            elif (
                self.sdc.data is True
                or (not self.ASmaster)
                or (not self.GoSignal)
                or (
                    self.mission_status in (2, 4)
                    and (
                        self.lf_speed > 10
                        or self.rf_speed > 10
                        or self.lb_speed > 10
                        or self.rb_speed > 10
                    )
                )
                or (
                    self.directionReq == 0
                    and (
                        self.lf_speed > 10
                        or self.rf_speed > 10
                        or self.lb_speed > 10
                        or self.rb_speed > 10
                    )
                )
            ):
                self.state = 3
                self.can_state_msg.as_state = 3
                self._publish_can_state()
                self.update()

            elif (
                self.MissionFinished
                and self.lf_speed < 10
                and self.rf_speed < 10
                and self.lb_speed < 10
                and self.rb_speed < 10
            ):
                self.state = 4
                self.can_state_msg.as_state = 4
                self._publish_can_state()

        elif self.state == 3:
            if not self.ebsTimerFlag:
                self._check_timer(15, True, True)
            elif self.readyTimerFlag and not self.ASmaster:
                self.state = 0
                self.can_state_msg.as_state = 0
                self._publish_can_state()
                self._initialize_state()

        elif self.state == 4:
            if not self.ASmaster:
                self.state = 0
                self.can_state_msg.as_state = 0
                self._publish_can_state()
            if not self.EBS:
                self.state = 3
                self.can_state_msg.as_state = 3
                self._publish_can_state()
            if self.sdc.data is True:
                self.state = 3
                self.can_state_msg.as_state = 3
                self._publish_can_state()

        if self.state != self.last_state:
            previous_state = self.last_state
            self.last_state = self.state
            self.logger.info(
                "[GUI] GUI_STATE transition: %s -> %s | as_state=%s ami_state=%s "
                "AS_MASTER=%s TS_MASTER=%s GO=%s EBS=%s",
                previous_state,
                self.state,
                self.can_state_msg.as_state,
                self.can_state_msg.ami_state,
                self.ASmaster,
                self.TSmaster,
                self.GoSignal,
                self.EBS,
            )

    def _publish_can_state(self):
        self.can_state_pub.publish(self.can_state_msg)
        self.logger.info(
            "[GUI] Publish CAN state: as_state=%s ami_state=%s AS_MASTER=%s TS_MASTER=%s",
            self.can_state_msg.as_state,
            self.can_state_msg.ami_state,
            self.ASmaster,
            self.TSmaster,
        )

    def _check_timer(self, duration, ebs, ready):
        self.ebsTimerFlag = ebs
        if not ready:
            return
        if self.readyTimerRunning:
            return
        self.readyTimerFlag = False
        self.readyTimerRunning = True

        def _timer_done():
            self.readyTimerFlag = True
            self.readyTimerRunning = False
            self.update()

        timer = threading.Timer(duration, _timer_done)
        timer.daemon = True
        timer.start()

    def shutdown(self):
        try:
            self.node.destroy_node()
        finally:
            rclpy.shutdown()


class MainGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Racing Supervisor - Control Center")
        self.root.geometry("1400x800")
        self.root.configure(bg=BG)
        self.root.minsize(1200, 700)
        
        self.logger = logging.getLogger(__name__)
        self.controller = GUIController()
        self.selected_mission = None
        
        # ROS-safe asset path
        try:
            pkg_path = get_package_share_directory('supervisor_pkg')
            self.assets_path = os.path.join(pkg_path, "assests")
        except:
            self.assets_path = "."
            logging.warning("Package path not found, using current directory")
        
        self.setup_layout()
    
    def setup_layout(self):
        # ===== TOP SECTION WITH LOGO AND CAR =====
        top_section = tk.Frame(self.root, bg=BG, height=120)
        top_section.pack(fill=tk.X, pady=(10, 20))
        top_section.pack_propagate(False)
        
        # Top accent line
        accent = tk.Frame(top_section, bg=RED_PRIMARY, height=2)
        accent.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Content container
        top_content = tk.Frame(top_section, bg=BG)
        top_content.pack(fill=tk.BOTH, expand=True, padx=30)
        
        # Logo (left)
        left_logo = tk.Frame(top_content, bg=BG)
        left_logo.pack(side=tk.LEFT)
        
        try:
            self.logo_img = tk.PhotoImage(file=os.path.join(self.assets_path, "logo.png"))
            if self.logo_img.width() > 80:
                self.logo_img = self.logo_img.subsample(2, 2)
            logo_label = tk.Label(left_logo, image=self.logo_img, bg=BG)
            logo_label.pack()
        except Exception as e:
            print("Logo error:", e)
            logo_text = tk.Label(left_logo, text="RACING", font=("Arial", 24, "bold"), bg=BG, fg=RED_PRIMARY)
            logo_text.pack()
        
        # Title (center)
        title_frame = tk.Frame(top_content, bg=BG)
        title_frame.pack(side=tk.LEFT, expand=True)
        
        tk.Label(
            title_frame,
            text="RACING SUPERVISOR",
            bg=BG,
            fg=RED_PRIMARY,
            font=("Arial", 28, "bold")
        ).pack()
        
        tk.Label(
            title_frame,
            text="Control System",
            bg=BG,
            fg=TXT_DIM,
            font=("Arial", 10)
        ).pack()
        
        # Car image (right)
        right_car = tk.Frame(top_content, bg=BG)
        right_car.pack(side=tk.RIGHT)
        
        try:
            self.car_img = tk.PhotoImage(file=os.path.join(self.assets_path, "car.png"))
            if self.car_img.width() > 100:
                self.car_img = self.car_img.subsample(3, 3)
            car_label = tk.Label(right_car, image=self.car_img, bg=BG)
            car_label.pack()
        except Exception as e:
            print("Car image error:", e)
            car_text = tk.Label(right_car, text="VEHICLE", font=("Arial", 18, "bold"), bg=BG, fg=RED_PRIMARY)
            car_text.pack()
        
        # ===== MAIN CONTENT - TWO PANEL LAYOUT =====
        main_container = tk.Frame(self.root, bg=BG)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left Panel - Mission Selection
        left_panel = tk.Frame(main_container, bg=CARD, width=600)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        left_inner = tk.Frame(left_panel, bg=CARD, padx=20, pady=20)
        left_inner.pack(fill=tk.BOTH, expand=True)
        
        # Mission header
        mission_header = tk.Frame(left_inner, bg=CARD)
        mission_header.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            mission_header,
            text="MISSION SELECTION",
            bg=CARD,
            fg=RED_PRIMARY,
            font=("Arial", 18, "bold")
        ).pack(side=tk.LEFT)
        
        tk.Label(
            mission_header,
            text="Select competition mission",
            bg=CARD,
            fg=TXT_DIM,
            font=("Arial", 10)
        ).pack(side=tk.RIGHT)
        
        tk.Frame(left_inner, bg=RED_PRIMARY, height=2).pack(fill=tk.X, pady=(0, 20))
        
        # Missions grid - 2x4 layout (2 columns, 4 rows)
        missions = [
            "StaticA", "StaticB", "Autocross",
            "Trackdrive", "Skidpad", "Acceleration", "AutoDemo"
        ]
        
        grid_frame = tk.Frame(left_inner, bg=CARD)
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        for i in range(4):
            grid_frame.grid_rowconfigure(i, weight=1)
        for i in range(2):
            grid_frame.grid_columnconfigure(i, weight=1)
        
        for idx, mission in enumerate(missions):
            row = idx // 2
            col = idx % 2
            
            btn_frame = tk.Frame(grid_frame, bg=CARD, padx=8, pady=8)
            btn_frame.grid(row=row, column=col, sticky="nsew")
            
            btn = ModernButton(
                btn_frame,
                text=mission,
                command=lambda x=mission: self.handle_mission_start(x),
                width=250,
                height=80
            )
            btn.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons at bottom of left panel
        control_frame = tk.Frame(left_inner, bg=CARD)
        control_frame.pack(fill=tk.X, pady=(20, 0))
        
        tk.Frame(control_frame, bg=RED_PRIMARY, height=1).pack(fill=tk.X, pady=(0, 15))
        
        btn_container = tk.Frame(control_frame, bg=CARD)
        btn_container.pack(fill=tk.X)
        
        shutdown_btn = ModernButton(
            btn_container,
            text="SHUTDOWN",
            command=self.handle_shutdown,
            width=200,
            height=55
        )
        shutdown_btn.pack(side=tk.LEFT, padx=(0, 10), expand=True, fill=tk.X)
        
        restart_btn = ModernButton(
            btn_container,
            text="RESTART",
            command=self.handle_restart,
            width=200,
            height=55
        )
        restart_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Right Panel - State Machine
        right_panel = tk.Frame(main_container, bg=CARD_DARK, width=500)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_panel.pack_propagate(False)
        
        right_inner = tk.Frame(right_panel, bg=CARD_DARK, padx=20, pady=20)
        right_inner.pack(fill=tk.BOTH, expand=True)
        
        # Status header
        status_header = tk.Frame(right_inner, bg=CARD_DARK)
        status_header.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            status_header,
            text="VEHICLE STATUS",
            bg=CARD_DARK,
            fg=ACCENT_BLUE,
            font=("Arial", 14, "bold")
        ).pack(anchor="w")
        
        self.status_indicator = tk.Label(
            status_header,
            text="● SYSTEM READY",
            bg=CARD_DARK,
            fg=GREEN,
            font=("Arial", 10, "bold")
        )
        self.status_indicator.pack(anchor="w", pady=(5, 0))
        
        tk.Frame(right_inner, bg=ACCENT_BLUE, height=2).pack(fill=tk.X, pady=(0, 20))
        
        # State machine panel
        self.state_machine_panel = StateMachinePanel(
            right_inner, self.logger, self._on_supervisor_driving_flag
        )
    
    def handle_mission_start(self, mission):
        self.selected_mission = mission
        self._sync_state_machine_mission(mission)

        # Update status
        self.status_indicator.config(text=f"● RUNNING: {mission.upper()}")
        self.status_indicator.config(fg=WARNING)

        self.logger.info(f"[GUI] Mission button clicked: {mission}")

        # For static missions we must create/start the mission so it publishes steps/commands.
        is_static = mission in ("StaticA", "StaticB", "AutoDemo")
        self.controller.start_mission(mission, launch_only=not is_static)

        # Reset status after 2 seconds
        self.root.after(2000, lambda: self.status_indicator.config(text="● SYSTEM READY"))
        self.root.after(2000, lambda: self.status_indicator.config(fg=GREEN))
    
    def handle_shutdown(self):
        self.status_indicator.config(text="● SHUTTING DOWN...")
        self.status_indicator.config(fg=RED_PRIMARY)
        self.controller.shutdown()
    
    def handle_restart(self):
        self.status_indicator.config(text="● RESTARTING...")
        self.status_indicator.config(fg=WARNING)
        self.controller.restart()
    
    def _sync_state_machine_mission(self, mission):
        mapping = {
            "StaticA": ("Static A", 18, 1),
            "StaticB": ("Static B", 19, 1),
            "Autocross": ("Autocross", 13, 1),
            "Trackdrive": ("Track Drive", 14, 1),
            "Skidpad": ("Skidpad", 12, 1),
            "Acceleration": ("Acceleration", 11, 1),
            "AutoDemo": ("Autonomus Demo", 15, 1),
        }
        if mission not in mapping:
            return
        label, ami_state, mission_status = mapping[mission]
        self.state_machine_panel.set_mission(label, ami_state, mission_status)

    def _on_supervisor_driving_flag(self):
        mission = self.selected_mission
        if not mission:
            mission = self.state_machine_panel.infer_static_mission()
        if mission in ("StaticA", "StaticB", "AutoDemo"):
            self.logger.info(f"[GUI] supervisor driving_flag -> starting {mission}")
            self.handle_mission_start(mission)
        else:
            self.logger.warning("[GUI] supervisor driving_flag received but no static mission selected")
    
    def on_close(self):
        if getattr(self, "state_machine_panel", None):
            self.state_machine_panel.shutdown()
        self.root.destroy()

    def _heartbeat(self):
        # Recurring no-op tick so Tkinter's C event loop regularly returns
        # control to the Python interpreter, which is required for pending
        # OS signals (SIGINT/SIGTERM from `ros2 launch`) to be noticed
        # promptly. Without this, mainloop() can block long enough that
        # launch escalates to SIGTERM before we ever get to shut down.
        self.root.after(200, self._heartbeat)


def main():
    logging.basicConfig(level=logging.INFO)
    root = tk.Tk()
    app = MainGUI(root)

    def _handle_signal(_signum, _frame):
        root.after(0, app.on_close)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    root.protocol("WM_DELETE_WINDOW", app.on_close)
    app._heartbeat()
    root.mainloop()

if __name__ == "__main__":
    main()