import time
import math
import numpy as np

from ackermann_msgs.msg import AckermannDriveStamped

from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Missions.mission_types import MissionType
from supervisor.helpers.CommunicationLayer import CommunicationLayer


class AutoDemoMission(MissionFinishing):

    missionType = MissionType.AUTODEMO
    def __init__(self, communication: CommunicationLayer, supervisor):
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
            self.publishMissionState("AutoDemo STEP 1: steer left")
            self.logger.info("[AutoDemo] STEP 0->1: INIT complete, now steering LEFT")

        elif self.step == 1:
            self.publishDrive(0.0, -self.maxSteer)
            elapsed = now - self.t0
            self.logger.info(f"[AutoDemo] STEP 1: steering LEFT (elapsed={elapsed:.1f}s, vel=0.0, steer={-self.maxSteer:.3f})")
            
            if now - self.t0 >= 3:
                self.t0 = now
                self.step = 2
                self.publishMissionState("AutoDemo STEP 2: steer right")
                self.logger.info("[AutoDemo] STEP 1->2: Completed LEFT steering, now steering RIGHT")

        elif self.step == 2:
            self.publishDrive(0.0, self.maxSteer)
            elapsed = now - self.t0
            self.logger.info(f"[AutoDemo] STEP 2: steering RIGHT (elapsed={elapsed:.1f}s, vel=0.0, steer={self.maxSteer:.3f})")
            
            if now - self.t0 >= 3:
                self.t0 = now
                self.step = 3
                self.publishMissionState("AutoDemo STEP 3: center")
                self.logger.info("[AutoDemo] STEP 2->3: Completed RIGHT steering, now CENTER")

        elif self.step == 3:
            self.publishDrive(0.0, 0.0)
            elapsed = now - self.t0
            self.logger.info(f"[AutoDemo] STEP 3: CENTER (elapsed={elapsed:.1f}s, vel=0.0, steer=0.0)")
            
            if now - self.t0 >= 3:
                self.t0 = now
                self.step = 4
                self.publishMissionState("AutoDemo STEP 4: accelerate")
                self.logger.info("[AutoDemo] STEP 3->4: Completed CENTER, now ACCELERATING")

        elif self.step == 4:

            elapsed = now - self.t0

            self.velocity = self.initial_velocity + self.acceleration * elapsed

            self.distance = (
                self.initial_velocity * elapsed +
                0.5 * self.acceleration * (elapsed ** 2)
            )

            self.publishDrive(self.velocity, 0.0)
            self.logger.info(f"[AutoDemo] STEP 4: ACCELERATE (elapsed={elapsed:.1f}s, vel={self.velocity:.3f}, distance={self.distance:.3f}, steer=0.0)")

            if self.distance >= 2.0:
                self.t0 = now
                self.initial_velocity = self.velocity
                self.step = 5
                self.publishMissionState("AutoDemo STEP 5: decelerate")
                self.logger.info(f"[AutoDemo] STEP 4->5: Reached 2.0m distance, now DECELERATING")

        elif self.step == 5:

            elapsed = now - self.t0

            self.velocity = self.initial_velocity + self.deceleration * elapsed

            self.distance = (
                2 +
                self.initial_velocity * elapsed +
                0.5 * abs(self.deceleration) * (elapsed ** 2)
            )

            self.publishDrive(self.velocity, 0.0)
            self.logger.info(f"[AutoDemo] STEP 5: DECELERATE (elapsed={elapsed:.1f}s, vel={self.velocity:.3f}, distance={self.distance:.3f}, steer=0.0)")

            if self.distance >= 4.0 or self.velocity <= 0:
                self.t0 = now
                self.step = 6
                self.publishMissionState("AutoDemo STEP 6: accelerate")
                self.logger.info(f"[AutoDemo] STEP 5->6: Reached 4.0m distance or velocity zero, now ACCELERATING again")
        
        elif self.step == 6:

            elapsed = now - self.t0

            self.velocity = self.acceleration * elapsed

            self.distance = (4 +0.5 * self.acceleration * (elapsed ** 2))

            self.publishDrive(self.velocity, 0.0)
            self.logger.info(f"[AutoDemo] STEP 6: ACCELERATE (elapsed={elapsed:.1f}s, vel={self.velocity:.3f}, distance={self.distance:.3f}, steer=0.0)")

            if self.distance >= 8.0:
                self.step = 7
                self.publishMissionState("AutoDemo STEP 7: stop + EBS")
                self.logger.info("[AutoDemo] STEP 6->7: Reached 8.0m distance, now STOPPING + EBS")
        
        elif self.step == 7:

            self.publishDrive(0.0, 0.0)
            self.logger.info("[AutoDemo] STEP 7: STOP + EBS (vel=0.0, steer=0.0)")

            self.communication.triggerEBS()
            self.logger.info("[AutoDemo] Triggering EBS - Mission complete!")

            self.notifyMissionFinished()



            