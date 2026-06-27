import time
import numpy as np
import logging
from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.mission_types import MissionType
from supervisor.helpers.Supervisor import Supervisor
from ackermann_msgs.msg import AckermannDriveStamped
import math
from supervisor.helpers.CommunicationLayer import CommunicationLayer



class StaticAMission(MissionFinishing):

    missionType = MissionType.STATIC_A

    def __init__(self, communication: CommunicationLayer, supervisor: Supervisor):
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
            self.publishMissionState("StaticA STEP 1: steer left")
            self.logger.info("[StaticA] STEP 0->1: INIT complete, now steering LEFT")

        # -------------------------------------------------
        # STEP 1: steer LEFT (5 sec)
        # -------------------------------------------------
        elif self.step == 1:
            self.publishDrive(0.0, -self.maxSteer)
            elapsed = now - self.phase_start_time
            self.logger.info(f"[StaticA] STEP 1: steering LEFT (elapsed={elapsed:.1f}s, vel=0.0, steer={-self.maxSteer:.3f})")

            if now - self.phase_start_time >= 5.0:
                self.phase_start_time = now
                self.step = 2
                self.publishMissionState("StaticA STEP 2: steer right")
                self.logger.info("[StaticA] STEP 1->2: Completed LEFT steering, now steering RIGHT")

        # -------------------------------------------------
        # STEP 2: steer RIGHT (5 sec)
        # -------------------------------------------------
        elif self.step == 2:
            self.publishDrive(0.0, self.maxSteer)
            elapsed = now - self.phase_start_time
            self.logger.info(f"[StaticA] STEP 2: steering RIGHT (elapsed={elapsed:.1f}s, vel=0.0, steer={self.maxSteer:.3f})")

            if now - self.phase_start_time >= 5.0:
                self.phase_start_time = now
                self.step = 3
                self.publishMissionState("StaticA STEP 3: center")
                self.logger.info("[StaticA] STEP 2->3: Completed RIGHT steering, now CENTER")

        # -------------------------------------------------
        # STEP 3: center (5 sec)
        # -------------------------------------------------
        elif self.step == 3:
            self.publishDrive(0.0, 0.0)
            elapsed = now - self.phase_start_time
            self.logger.info(f"[StaticA] STEP 3: CENTER (elapsed={elapsed:.1f}s, vel=0.0, steer=0.0)")

            if now - self.phase_start_time >= 5.0:
                self.phase_start_time = now
                self.step = 4
                self.publishMissionState("StaticA STEP 4: accelerate")
                self.logger.info("[StaticA] STEP 3->4: Completed CENTER, now ACCELERATING")

        # -------------------------------------------------
        # STEP 4: acceleration (EXACT old logic)
        # -------------------------------------------------
        elif self.step == 4:
            elapsed = now - self.phase_start_time

            speed = (2 * np.pi * 200 * 0.253 / 60* 0.1 * elapsed)

            self.publishDrive(speed, 0.0)
            self.logger.info(f"[StaticA] STEP 4: ACCELERATE (elapsed={elapsed:.1f}s, vel={speed:.3f}, steer=0.0)")

            if elapsed >= self.ramp_duration:
                self.phase_start_time = now
                self.step = 5
                self.publishMissionState("StaticA STEP 5: decelerate")
                self.logger.info("[StaticA] STEP 4->5: Completed ACCELERATION, now DECELERATING")

        # -------------------------------------------------
        # STEP 5: deceleration (EXACT old logic)
        # -------------------------------------------------
        elif self.step == 5:
            elapsed = now - self.phase_start_time

            remaining = max(0.0, self.brake_duration - elapsed)

            speed = (2 * np.pi * 200 * 0.253 / 60* 0.1 * (2 * remaining))

            self.publishDrive(speed, 0.0)
            self.logger.info(f"[StaticA] STEP 5: DECELERATE (elapsed={elapsed:.1f}s, vel={speed:.3f}, steer=0.0)")

            if elapsed >= self.brake_duration:
                self.step = 6
                self.publishMissionState("StaticA STEP 6: stop")
                self.logger.info("[StaticA] STEP 5->6: Completed DECELERATION, now STOPPING")

        # -------------------------------------------------
        # STEP 6: STOP + FINISH
        # -------------------------------------------------
        elif self.step == 6:
            self.publishDrive(0.0, 0.0)
            self.logger.info("[StaticA] STEP 6: STOP + FINISH (vel=0.0, steer=0.0) - Mission complete!")
            self.notifyMissionFinished()
