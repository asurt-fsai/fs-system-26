import time
import numpy as np

from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.MissionManager import MissionType
from ackermann_msgs.msg import AckermannDriveStamped
import math



class StaticAMission(MissionFinishing):

    missionType = MissionType.STATIC_A

    def __init__(self, communication, supervisor):
        super().__init__(communication, supervisor)

        # MUST be real max steering (IMPORTANT for rules)
        self.maxSteer = 27.2 # wa5daha mn el code el adeem 
        self.maxSteer_rad = math.radians(self.maxSteer)  # ≈ 0.475 rad

        # State machine
        self.step = 0
        self.phase_start_time = None

        # Constants (same as old)
        self.ramp_duration = 10.0
        self.brake_duration = 5.0

    # =========================================================
    # MAIN LOOP (called every supervisor cycle)
    # =========================================================
    def tick(self):

        if self.missionStatus != MissionStatus.RUNNING:
            return

        now = time.time()

        # -------------------------------------------------
        # STEP 0: INIT
        # -------------------------------------------------
        if self.step == 0:
            self.phase_start_time = now
            self.step = 1

        # -------------------------------------------------
        # STEP 1: steer LEFT (5 sec)
        # -------------------------------------------------
        elif self.step == 1:
            self.publishDrive(0.0, -self.maxSteer_rad)

            if now - self.phase_start_time >= 5.0:
                self.phase_start_time = now
                self.step = 2

        # -------------------------------------------------
        # STEP 2: steer RIGHT (5 sec)
        # -------------------------------------------------
        elif self.step == 2:
            self.publishDrive(0.0, self.maxSteer_rad)

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
        # STEP 4: acceleration (EXACT old logic)
        # -------------------------------------------------
        elif self.step == 4:
            elapsed = now - self.phase_start_time

            speed = (2 * np.pi * 200 * 0.253 / 60* 0.1 * elapsed)

            self.publishDrive(speed, 0.0)

            if elapsed >= self.ramp_duration:
                self.phase_start_time = now
                self.step = 5

        # -------------------------------------------------
        # STEP 5: deceleration (EXACT old logic)
        # -------------------------------------------------
        elif self.step == 5:
            elapsed = now - self.phase_start_time

            remaining = max(0.0, self.brake_duration - elapsed)

            speed = (2 * np.pi * 200 * 0.253 / 60* 0.1 * (2 * remaining))

            self.publishDrive(speed, 0.0)

            if elapsed >= self.brake_duration:
                self.step = 6

        # -------------------------------------------------
        # STEP 6: STOP + FINISH
        # -------------------------------------------------
        elif self.step == 6:
            self.publishDrive(0.0, 0.0)
            self.notifyMissionFinished()

