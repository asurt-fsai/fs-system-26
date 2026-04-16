import time
import numpy as np

from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.MissionManager import MissionType
from ackermann_msgs.msg import AckermannDriveStamped
import math



class StaticBMission(MissionFinishing):

    missionType = MissionType.STATIC_B

    def __init__(self, communication, supervisor):
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

        # RAMP UP
        elif self.step == 1:
            elapsed = now - self.t0
            speed = (elapsed / self.ramp_time) * self.target_velocity

            self.publishDrive(speed, 0.0)

            if elapsed >= self.ramp_time:
                self.t0 = now
                self.step = 2

        # HOLD
        elif self.step == 2:
            self.publishDrive(self.target_velocity, 0.0)

            if now - self.t0 >= self.hold_time:
                self.step = 3

        # FINISH + EBS
        elif self.step == 3:
            self.publishDrive(0.0, 0.0)

            self.communication.publishMissionFlag(True)

            # NEW WAY (NO SERVICE HERE)
            self.communication.triggerEBS()

            self.notifyMissionFinished()
