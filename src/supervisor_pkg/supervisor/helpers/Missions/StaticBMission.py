import time
import numpy as np
import logging
from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.mission_types import MissionType
from supervisor.helpers.Supervisor import Supervisor
from supervisor.helpers.CommunicationLayer import CommunicationLayer
from ackermann_msgs.msg import AckermannDriveStamped
import math



class StaticBMission(MissionFinishing):

    missionType = MissionType.STATIC_B

    def __init__(self, communication: CommunicationLayer, supervisor: Supervisor):
        super().__init__(communication, supervisor)

        self.target_velocity = 1.32
        self.ramp_time = 10.0
        self.hold_time = 10.0

        self.step = 0
        self.t0 = None
    

    def tick(self):

        if self.missionStatus != MissionStatus.RUNNING:
            return

        now = time.time()

        # INIT
        if self.step == 0:
            self.t0 = now
            self.step = 1
            self.publishMissionState("StaticB STEP 1: ramp up")
            self.logger.info("[StaticB] STEP 0->1: INIT complete, now RAMPING UP velocity")

        # RAMP UP
        elif self.step == 1:
            elapsed = now - self.t0
            speed = (elapsed / self.ramp_time) * self.target_velocity

            self.publishDrive(speed, 0.0)
            self.logger.info(f"[StaticB] STEP 1: RAMP UP (elapsed={elapsed:.1f}s, vel={speed:.3f}, steer=0.0)")

            if elapsed >= self.ramp_time:
                self.t0 = now
                self.step = 2
                self.publishMissionState("StaticB STEP 2: hold")
                self.logger.info(f"[StaticB] STEP 1->2: Completed RAMP UP to {self.target_velocity:.3f}, now HOLDING")

        # HOLD
        elif self.step == 2:
            self.publishDrive(self.target_velocity, 0.0)
            elapsed = now - self.t0
            self.logger.info(f"[StaticB] STEP 2: HOLD (elapsed={elapsed:.1f}s, vel={self.target_velocity:.3f}, steer=0.0)")

            if now - self.t0 >= self.hold_time:
                self.step = 3
                self.publishMissionState("StaticB STEP 3: finish + EBS")
                self.logger.info("[StaticB] STEP 2->3: Completed HOLD, now STOPPING + EBS")

        # FINISH + EBS
        elif self.step == 3:
            self.publishDrive(0.0, 0.0)
            self.logger.info("[StaticB] STEP 3: STOP + EBS (vel=0.0, steer=0.0)")

            # NEW WAY (NO SERVICE HERE)
            self.communication.triggerEBS()
            self.logger.info("[StaticB] Triggering EBS - Mission complete!")
            self.publishMissionState("[StaticB] FINISHED")
            self.notifyMissionFinished()
            


