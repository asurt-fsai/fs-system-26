import time
import math
import numpy as np

from ackermann_msgs.msg import AckermannDriveStamped

from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.MissionManager import MissionType


class AutoDemoMission(MissionFinishing):

    missionType = MissionType.AUTODEMO

    def __init__(self, communication, supervisor):
        super().__init__(communication, supervisor)

        self.step = 0
        self.t0 = None

        # physics state (replacing old simulation)
        self.distance = 0.0
        self.velocity = 0.0

        self.acceleration = 1.0
        self.deceleration = -1.0

        self.initial_velocity = 0.0
         # MUST be real max steering (IMPORTANT for rules)
        self.maxSteer = 27.2 # wa5daha mn el code el adeem 
        self.maxSteer_rad = math.radians(self.maxSteer)  # ≈ 0.475 rad


    def tick(self):

        if self.missionStatus != MissionStatus.RUNNING:
            return

        now = time.time()

        # -------------------------
        # STEP 0 INIT
        # -------------------------
        if self.step == 0:
            self.t0 = now
            self.step = 1

        elif self.step == 1:
            self.publishDrive(0.0, -self.maxSteer_rad)
            if now - self.t0 >= 3:
                self.t0 = now
                self.step = 2

        elif self.step == 2:
            self.publishDrive(0.0, self.maxSteer_rad)
            if now - self.t0 >= 3:
                self.t0 = now
                self.step = 3

        elif self.step == 3:
            self.publishDrive(0.0, 0.0)
            if now - self.t0 >= 3:
                self.t0 = now
                self.step = 4

        elif self.step == 4:

            elapsed = now - self.t0

            self.velocity = self.initial_velocity + self.acceleration * elapsed

            self.distance = (
                self.initial_velocity * elapsed +
                0.5 * self.acceleration * (elapsed ** 2)
            )

            self.publishDrive(self.velocity, 0.0)

            if self.distance >= 2.0:
                self.t0 = now
                self.initial_velocity = self.velocity
                self.step = 5

        elif self.step == 5:

            elapsed = now - self.t0

            self.velocity = self.initial_velocity + self.deceleration * elapsed

            self.distance = (
                2 +
                self.initial_velocity * elapsed +
                0.5 * abs(self.deceleration) * (elapsed ** 2)
            )

            self.publishDrive(self.velocity, 0.0)

            if self.distance >= 4.0 or self.velocity <= 0:
                self.t0 = now
                self.step = 6
        
        elif self.step == 6:

            elapsed = now - self.t0

            self.velocity = self.acceleration * elapsed

            self.distance = (4 +0.5 * self.acceleration * (elapsed ** 2))

            self.publishDrive(self.velocity, 0.0)

            if self.distance >= 8.0:
                self.step = 7
        
        elif self.step == 7:

            self.publishDrive(0.0, 0.0)

            self.communication.publishMissionFlag(True)

            self.communication.triggerEBS()

            self.notifyMissionFinished()

            
