import time
import numpy as np

from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.MissionManager import MissionType
from ackermann_msgs.msg import AckermannDriveStamped


class StaticAMission(MissionFinishing):

    missionType = MissionType.STATIC_A

    def __init__(self, communication, supervisor):
        super().__init__(communication, supervisor)

        # ----------------------------
        # Parameters (same as old node)
        # ----------------------------
        self.maxSteer = 0.5  # replace with param if needed

        # ----------------------------
        # State machine
        # ----------------------------
        self.step = 0
        self.start_time = None
        self.phase_start_time = None

        # ----------------------------
        # Constants (from old logic)
        # ----------------------------
        self.acceleration_time = 10.0
        self.brake_time = 5.0

    # =========================================================
    # MAIN EXECUTION (called by Supervisor loop)
    # =========================================================
    def tick(self):

        if self.missionStatus != MissionStatus.RUNNING:
            return

        now = time.time()

        # -------------------------------------------------
        # STEP 0: INIT
        # -------------------------------------------------
        if self.step == 0:
            self.start_time = now
            self.phase_start_time = now
            self.step = 1

        # -------------------------------------------------
        # STEP 1: steer LEFT (5 sec)
        # -------------------------------------------------
        elif self.step == 1:
            self.publishDrive(0.0, -self.maxSteer)

            if now - self.phase_start_time >= 5.0:
                self.phase_start_time = now
                self.step = 2

        # -------------------------------------------------
        # STEP 2: steer RIGHT (5 sec)
        # -------------------------------------------------
        elif self.step == 2:
            self.publishDrive(0.0, self.maxSteer)

            if now - self.phase_start_time >= 5.0:
                self.phase_start_time = now
                self.step = 3

        # -------------------------------------------------
        # STEP 3: center (5 sec)
        # -------------------------------------------------
        elif self.step == 3:
            self.publishDrive(0.0, 0.0)

            if now - self.phase_start_time >= 5.0:
                self.phase_start_time = now
                self.step = 4

        # -------------------------------------------------
        # STEP 4: acceleration phase (same formula as old)
        # -------------------------------------------------
        elif self.step == 4:
            elapsed = now - self.start_time

            speed = 2 * np.pi * 200 * 0.253 / 60 * 0.1 * elapsed
            self.publishDrive(speed, 0.0)

            if elapsed >= self.acceleration_time:
                self.phase_start_time = now
                self.step = 5
                self.last_speed = speed

        # -------------------------------------------------
        # STEP 5: deceleration phase (same logic as old)
        # -------------------------------------------------
        elif self.step == 5:
            t = now - self.phase_start_time

            speed = max(
                0.0,
                self.last_speed * (1 - t / self.brake_time)
            )

            self.publishDrive(speed, 0.0)

            if t >= self.brake_time:
                self.step = 6

        # -------------------------------------------------
        # STEP 6: STOP + FINISH
        # -------------------------------------------------
        elif self.step == 6:
            self.publishDrive(0.0, 0.0)
            self.notifyMissionFinished()

    # =========================================================
    # HELPERS (replace ROS publishers)
    # =========================================================
    def publishDrive(self, speed, steer):
        """
        Sends Ackermann command through CommunicationLayer
        """
        msg = AckermannDriveStamped()
        msg.drive.speed = speed
        msg.drive.steering_angle = steer

        self.communication.publishDriveCommand(msg)