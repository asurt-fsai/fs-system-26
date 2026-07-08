import time
import tkinter as tk
from threading import Timer

import rclpy
from std_msgs.msg import Bool, String
from src.dependencies.eufs_msgs.msg import CanState, VehicleCommandsStamped, WheelSpeedsStamped
from supervisor.helpers.Module.Module import Module


class Interface:
    def __init__(self, master):
        self.master = master
        master.title("IPG MODULE INTERFACE")
        master.geometry("1400x1000")

        self._closing = False
        self._mission_timer = None

        self.init_ros()
        self.create_widgets()
        self.initialize()
        self.selected_module = None

        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        self.publishMissionName()

        self.start_ros_spin()

    def publishMissionName(self):
        if self._closing or not rclpy.ok():
            return
        msg = String()
        msg.data = self.text.cget("text")
        if not msg.data:
            return
        try:
            self.missionName.publish(msg)
        except Exception:
            return

    def initialize(self):
        self.ASmaster = False
        self.TSmaster = False
        self.Flag = False
        self.GoSignal = False
        self.EBS = True
        self.EBSfail = True
        self.misson = 0
        self.mission_status = 0
        self.state = 0
        self.steerReq = 0
        self.torqueReq = 0
        self.steerFeedback = 0
        self.sdc = Bool()
        self.ebsTimerFlag = False
        self.readyTimerFlag = False
        self.ebsTimerRunning = False
        self.readyTimerRunning = False

        self.lf_speed = 0
        self.rf_speed = 0
        self.lb_speed = 0
        self.rb_speed = 0
        self.directionReq = 0
        self.wheel_speeds_seen = False

    def init_ros(self):
        rclpy.init()

        self.node = rclpy.create_node("interface")

        self.as_master_pub = self.node.create_publisher(Bool, "/state_machine/as_master_switch", 1)
        self.ts_master_pub = self.node.create_publisher(Bool, "/state_machine/ts_master_switch", 1)
        self.go_signal_pub = self.node.create_publisher(Bool, "/state_machine/go_signal", 1)
        self.ebs_pub = self.node.create_publisher(Bool, "/state_machine/ebs", 1)
        self.ebs_fail_pub = self.node.create_publisher(Bool, "/state_machine/ebs_fail", 1)
        self.flag_pub = self.node.create_publisher(Bool, "/state_machine/flag", 1)
        self.supervisor_driving_flag_pub = self.node.create_publisher(
            Bool, "/supervisor/driving_flag", 1
        )
        self.canStatePub = self.node.create_publisher(CanState, "/ros_can/state", 1)
        self.missionName = self.node.create_publisher(String, "/missionName", 10)

        self.node.create_subscription(String, "/state_machine/state_str", self.state_cb, 10)
        self.node.create_subscription(Bool, "shutDownCircuit", self.sdcCB, 10)
        self.node.create_subscription(
            Bool, "/state_machine/as_master_switch", self.as_master_cb, 10
        )
        self.node.create_subscription(
            Bool, "/state_machine/ts_master_switch", self.ts_master_cb, 10
        )
        self.node.create_subscription(
            Bool, "/state_machine/go_signal", self.go_signal_cb, 10
        )
        self.node.create_subscription(Bool, "/state_machine/ebs", self.ebs_cb, 10)
        self.node.create_subscription(
            Bool, "/state_machine/ebs_fail", self.ebs_fail_cb, 10
        )
        self.node.create_subscription(Bool, "/state_machine/flag", self.flag_cb, 10)
        self.node.create_subscription(VehicleCommandsStamped, "/ros_can/vehicle_commands", self.vehicleCommandsCB, 10)
        self.node.create_subscription(WheelSpeedsStamped, "/ros_can/wheel_speeds", self.wheelSpeedsCB, 10)

        self.CanStateMsg = CanState()
        self.vehicleCommandsMsg = VehicleCommandsStamped()
        self.wheelSpeedsMsg = WheelSpeedsStamped()

    def sdcCB(self, msg: Bool):
        self.sdc = msg
        self.update()

    def as_master_cb(self, msg: Bool):
        self.ASmaster = msg.data
        self.update()

    def ts_master_cb(self, msg: Bool):
        self.TSmaster = msg.data
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

    def vehicleCommandsCB(self, msg):
        self.steerReq = msg.commands.steering
        self.torqueReq = msg.commands.torque
        self.mission_status = msg.commands.mission_status
        self.directionReq = msg.commands.direction
        self.update()

    def wheelSpeedsCB(self, msg):
        self.lf_speed = msg.speeds.lf_speed
        self.rf_speed = msg.speeds.rf_speed
        self.lb_speed = msg.speeds.lb_speed
        self.rb_speed = msg.speeds.rb_speed
        self.steerFeedback = msg.speeds.steering
        self.wheel_speeds_seen = True
        self.update()

    def state_cb(self, msg: String):
        self.text.config(text=msg.data)

    def create_widgets(self):
        self.color1 = "#020f12"
        self.color2 = "#8b0000"
        self.color3 = "#a60000"
        self.color4 = "black"
        self.color5 = "#195e2f"

        self.text = tk.Label(
            self.master,
            text="",
            bg=self.color4,
            justify="center",
            foreground="white",
            font=("ubuntu", 18),
        )
        self.text.place(relx=0.5, rely=0.05, anchor="n")

        self.as_master_button = tk.Button(
            self.master,
            text="AS MASTER: OFF",
            width=24,
            height=3,
            font=("ubuntu", 12),
            bg=self.color2,
            borderwidth=0,
            highlightthickness=0,
        )
        self.as_master_button.configure(command=self.toggle_as_master)
        self.as_master_button.place(relx=0.15, rely=0.15)

        self.ts_master_button = tk.Button(
            self.master,
            text="TS MASTER: OFF",
            width=24,
            height=3,
            font=("ubuntu", 12),
            bg=self.color2,
            borderwidth=0,
            highlightthickness=0,
        )
        self.ts_master_button.configure(command=self.toggle_ts_master)
        self.ts_master_button.place(relx=0.55, rely=0.15)

        self.ebs_button = tk.Button(
            self.master,
            text="EBS: ARMED",
            width=12,
            height=3,
            font=("ubuntu", 10),
            bg=self.color5,
            borderwidth=0,
            highlightthickness=0,
        )
        self.ebs_button.configure(command=self.toggle_ebs)
        self.ebs_button.place(relx=0.55, rely=0.3)

        self.ebs_fail_button = tk.Button(
            self.master,
            text="EBS: AVAILABLE",
            font=("ubuntu", 10),
            width=14,
            height=3,
            bg=self.color5,
            borderwidth=0,
            highlightthickness=0,
        )
        self.ebs_fail_button.configure(command=self.toggle_ebs_fail)
        self.ebs_fail_button.place(relx=0.71, rely=0.3)

        self.flag_button = tk.Button(
            self.master,
            text="FLAG: OFF",
            width=24,
            height=3,
            font=("ubuntu", 12),
            bg=self.color2,
            borderwidth=0,
            highlightthickness=0,
        )
        self.flag_button.configure(command=self.toggle_flag)
        self.flag_button.place(relx=0.15, rely=0.3)

        self.go_signal_button = tk.Button(
            self.master,
            text="GO SIGNAL: OFF",
            width=24,
            height=3,
            font=("ubuntu", 12),
            bg=self.color2,
            borderwidth=0,
            highlightthickness=0,
        )
        self.go_signal_button.configure(command=self.toggle_go_signal)
        self.go_signal_button.place(relx=0.55, rely=0.45)

        buttons = [
            ("Not selected", 0.2, 0.7, self.notSelectedCommand),
            ("Static A", 0.4, 0.7, self.staticAcommand),
            ("Static B", 0.6, 0.7, self.staticBcommand),
            ("Autocross", 0.8, 0.7, self.autocrossCommand),
            ("autoDemo", 0.2, 0.85, self.autoDemoCommand),
            ("Skid Pad", 0.4, 0.85, self.skidpadCommand),
            ("Track Drive", 0.6, 0.85, self.trackDriveCommand),
            ("Acceleration", 0.8, 0.85, self.accelerationCommand),
        ]

        for text, relx, rely, command_func in buttons:
            button = tk.Button(
                self.master,
                text=text,
                font=("ubuntu", 12),
                background=self.color1,
                foreground=self.color2,
                activebackground=self.color3,
                activeforeground=self.color4,
                highlightbackground=self.color2,
                highlightthickness=2,
                highlightcolor="white",
                width=12,
                height=2,
                command=command_func,
            )
            button.place(relx=relx, rely=rely, anchor="center")

    def notSelectedCommand(self):
        self.text.configure(text="Not selected")
        self.CanStateMsg.as_state = 0
        self.CanStateMsg.ami_state = 10
        self.canStatePub.publish(self.CanStateMsg)
        self.misson = 10
        self.mission_status = 0
        self.state = 0

    def staticAcommand(self):
        self.text.configure(text="Static A")
        self.CanStateMsg.as_state = 0
        self.CanStateMsg.ami_state = 18
        self.canStatePub.publish(self.CanStateMsg)
        self.misson = 18
        self.mission_status = 1
        self.state = 0

    def staticBcommand(self):
        self.text.configure(text="Static B")
        self.CanStateMsg.as_state = 0
        self.CanStateMsg.ami_state = 19
        self.canStatePub.publish(self.CanStateMsg)
        self.misson = 19
        self.mission_status = 1
        self.state = 0

    def autocrossCommand(self):
        self.text.configure(text="Autocross")
        self.CanStateMsg.as_state = 0
        self.CanStateMsg.ami_state = 13
        self.canStatePub.publish(self.CanStateMsg)
        self.misson = 13
        self.mission_status = 1
        self.state = 0

    def autoDemoCommand(self):
        self.text.configure(text="Autonomus Demo")
        self.CanStateMsg.as_state = 0
        self.CanStateMsg.ami_state = 15
        self.canStatePub.publish(self.CanStateMsg)
        self.misson = 15
        self.mission_status = 1
        self.state = 0

    def skidpadCommand(self):
        self.text.configure(text="Skidpad")
        self.CanStateMsg.as_state = 0
        self.CanStateMsg.ami_state = 12
        self.canStatePub.publish(self.CanStateMsg)
        self.misson = 12
        self.mission_status = 1
        self.state = 0

    def trackDriveCommand(self):
        self.text.configure(text="Track Drive")
        self.CanStateMsg.as_state = 0
        self.CanStateMsg.ami_state = 14
        self.canStatePub.publish(self.CanStateMsg)
        self.misson = 14
        self.mission_status = 1
        self.state = 0

    def accelerationCommand(self):
        self.text.configure(text="Acceleration")
        self.CanStateMsg.as_state = 0
        self.CanStateMsg.ami_state = 11
        self.canStatePub.publish(self.CanStateMsg)
        self.misson = 11
        self.mission_status = 1
        self.state = 0

    def toggle_as_master(self):
        msg = Bool()
        msg.data = not self.as_master_button["text"].endswith("ON")
        self.as_master_pub.publish(msg)
        self.as_master_button.config(
            text="AS MASTER: ON" if msg.data else "AS MASTER: OFF",
            bg=self.color5 if msg.data else self.color2,
        )
        self.ASmaster = not self.ASmaster
        self.update()

    def toggle_ts_master(self):
        msg = Bool()
        msg.data = not self.ts_master_button["text"].endswith("ON")
        self.ts_master_pub.publish(msg)
        self.ts_master_button.config(
            text="TS MASTER: ON" if msg.data else "TS MASTER: OFF",
            bg=self.color5 if msg.data else self.color2,
        )
        self.TSmaster = not self.TSmaster
        self.update()

    def toggle_go_signal(self):
        msg = Bool()
        msg.data = not self.go_signal_button["text"].endswith("ON")
        self.go_signal_pub.publish(msg)
        self.go_signal_button.config(
            text="GO SIGNAL: ON" if msg.data else "GO SIGNAL: OFF",
            bg=self.color5 if msg.data else self.color2,
        )
        self.GoSignal = not self.GoSignal
        self.update()

    def toggle_ebs(self):
        msg = Bool()
        msg.data = not self.ebs_button["text"].endswith("TRIGGERED")
        self.ebs_pub.publish(msg)
        self.ebs_button.config(
            text="EBS: TRIGGERED" if msg.data else "EBS: ARMED",
            bg=self.color2 if msg.data else self.color5,
        )
        self.EBS = not self.EBS
        self.update()

    def toggle_ebs_fail(self):
        msg = Bool()
        msg.data = not self.ebs_fail_button["text"].endswith("UNAVAILABLE")
        self.ebs_fail_pub.publish(msg)
        self.ebs_fail_button.config(
            text="EBS: UNAVAILABLE" if msg.data else "EBS: AVAILABLE",
            bg=self.color2 if msg.data else self.color5,
        )
        self.EBSfail = not self.EBSfail
        self.update()

    def toggle_flag(self):
        msg = Bool()
        msg.data = not self.flag_button["text"].endswith("ON")
        self.flag_pub.publish(msg)
        self.flag_button.config(
            text="FLAG: ON" if msg.data else "FLAG: OFF",
            bg=self.color5 if msg.data else self.color2,
        )
        self.Flag = not self.Flag
        self.update()

    def initialize_module(self):
        if self.current_pkg and self.current_launch_file:
            self.module = Module(pkg=self.current_pkg, launchFile=self.current_launch_file)
            print(f"Module initialized with {self.current_pkg} and {self.current_launch_file}")
        else:
            print("Error: Current package or launch file is not set.")

    def select_mission(self, mission_name, pkg, launch_file, ami_state, mission_status):
        self.text.configure(text=mission_name)
        self.publishMissionName()

        self.selected_module = Module(pkg=pkg, launchFile=launch_file)

        self.CanStateMsg.ami_state = ami_state
        self.canStatePub.publish(self.CanStateMsg)
        self.misson = ami_state
        self.mission_status = mission_status
        self.steerReq = 0
        self.torqueReq = 0
        self.steerFeedback = 0
        self.directionReq = 0

    def update(self):
        if self.state == 0:
            self.ebsTimerFlag = False
            self.readyTimerFlag = False
            self.readyTimerRunning = False
            if self.ASmaster and self.TSmaster and self.EBS and self.mission_status:
                self.state = 1
                self.CanStateMsg.as_state = 1
                self.canStatePub.publish(self.CanStateMsg)

        if self.state == 1:
            if not self.ASmaster:
                self.state = 0
                self.last_state = 0
                self.CanStateMsg.as_state = 0
                self.canStatePub.publish(self.CanStateMsg)
            elif not self.EBS:
                self.state = 3
                self.CanStateMsg.as_state = 3
                self.canStatePub.publish(self.CanStateMsg)
            elif self.sdc.data is True:
                self.state = 3
                self.CanStateMsg.as_state = 3
                self.canStatePub.publish(self.CanStateMsg)
                self.update()
            elif (
                self.directionReq == 0
                and self.torqueReq == 0
                and self.steerReq == 0
                and abs(self.steerFeedback) < 5
            ):
                if not self.readyTimerRunning and not self.readyTimerFlag:
                    self.check_timer(5, False, True)
                if self.readyTimerFlag and self.GoSignal is True:
                    self.state = 2
                    self.CanStateMsg.as_state = 2
                    self.canStatePub.publish(self.CanStateMsg)

        elif self.state == 2:
            if not self.EBS:
                self.state = 3
                self.CanStateMsg.as_state = 3
                self.canStatePub.publish(self.CanStateMsg)
                self.update()
            elif (
                self.sdc.data is True
                or (not self.ASmaster)
                or (not self.GoSignal)
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
                self.CanStateMsg.as_state = 3
                self.canStatePub.publish(self.CanStateMsg)
                self.update()

            elif (
                self.mission_status == 2
                and (
                    not self.wheel_speeds_seen
                    or (
                        abs(self.lf_speed) < 10
                        and abs(self.rf_speed) < 10
                        and abs(self.lb_speed) < 10
                        and abs(self.rb_speed) < 10
                    )
                )
            ):
                self.state = 4
                self.CanStateMsg.as_state = 4
                self.canStatePub.publish(self.CanStateMsg)

        elif self.state == 3:
            if not self.ebsTimerFlag:
                self.check_timer(15, True, True)
            elif self.readyTimerFlag and not self.ASmaster:
                self.state = 0
                self.CanStateMsg.as_state = 0
                self.canStatePub.publish(self.CanStateMsg)
                self.initialize()

        elif self.state == 4:
            if not self.ASmaster:
                self.state = 0
                self.CanStateMsg.as_state = 0
                self.canStatePub.publish(self.CanStateMsg)
            if not self.EBS:
                self.state = 3
                self.CanStateMsg.as_state = 3
                self.canStatePub.publish(self.CanStateMsg)
            if self.sdc.data is True:
                self.state = 3
                self.CanStateMsg.as_state = 3
                self.canStatePub.publish(self.CanStateMsg)

        if self.state != self.last_state:
            if self.state == 2:
                msg = Bool()
                msg.data = True
                self.supervisor_driving_flag_pub.publish(msg)
            self.last_state = self.state

    def start_ros_spin(self):
        self.node.get_logger().info("Starting ROS spin")
        if not self._closing:
            self.master.after(100, self.ros_spin)

    def ros_spin(self):
        if self._closing or not rclpy.ok():
            return
        try:
            rclpy.spin_once(self.node, timeout_sec=0.1)
        except rclpy.executors.ExternalShutdownException:
            return
        self.master.after(100, self.ros_spin)

    def check_timer(self, timee, ebs, ready):
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

        Timer(timee, _timer_done).start()

    def on_close(self):
        if self._closing:
            return
        self._closing = True
        if self._mission_timer is not None:
            self._mission_timer.cancel()
        try:
            self.node.destroy_node()
        except Exception:
            pass
        if rclpy.ok():
            rclpy.shutdown()
        self.master.destroy()


def main():
    root = tk.Tk()
    root.configure(bg="black")
    interface = Interface(root)
    root.mainloop()


if __name__ == "__main__":
    main()
