import json
import os
import logging

from supervisor.helpers.Module.Module import Module
from supervisor.helpers.Missions.AccelerationMission import AccelerationMission
from supervisor.helpers.Missions.SkidpadMission import SkidpadMission
from supervisor.helpers.Missions.AutocrossMission import AutocrossMission
from supervisor.helpers.Missions.TrackdriveMission import TrackdriveMission
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.CommunicationLayer import CommunicationLayer


class MissionManager:
    _instance = None

    logger = logging.getLogger(__name__)

    def __init__(self):
        self.activeMission = None
        self.moduleManager = None

        self.missionFactory = {
            "acceleration": AccelerationMission,
            "skidpad": SkidpadMission,
            "autocross": AutocrossMission,
            "trackdrive": TrackdriveMission
        }

    # ==================================================
    # Singleton
    # ==================================================
    @staticmethod
    def getInstance():
        if MissionManager._instance is None:
            MissionManager._instance = MissionManager()
        return MissionManager._instance

    # ==================================================
    # Dependency Injection
    # ==================================================
    def setModuleManager(self, moduleManager):
        self.moduleManager = moduleManager

    # ==================================================
    # Create Mission
    # ==================================================
    def createMission(self, missionType: str):
        """
        Creates mission and registers it in CommunicationLayer
        """

        if missionType not in self.missionFactory:
            raise ValueError(f"[MissionManager] Unknown mission: {missionType}")

        missionClass = self.missionFactory[missionType]
        self.activeMission = missionClass()

        # Set initial state
        self.activeMission.missionStatus = MissionStatus.IDLE

        # Register in CommunicationLayer
        CommunicationLayer.getInstance().registerMission(self.activeMission)

        MissionManager.logger.info(f"[MissionManager] Created mission: {missionType} (IDLE)")

    # ==================================================
    # Start Mission
    # ==================================================
    def startMission(self, missionType: str):
        """
        Full mission startup pipeline
        """

        if self.moduleManager is None:
            raise Exception("[MissionManager] ModuleManager not set")

        # 🔴 Prevent starting while another mission is running
        if self.activeMission and self.activeMission.missionStatus == MissionStatus.RUNNING:
            MissionManager.logger.warning("[MissionManager] Cannot start new mission: another mission is RUNNING")
            return

        # 1. Create mission
        self.createMission(missionType)

        # 2. Resolve modules
        modules = self.resolveModules(missionType)

        if not modules:
            raise Exception("[MissionManager] No modules found")

        # 3. Register modules (DISPATCH STEP)
        self.moduleManager.registerModules(modules)

        # 4. Launch modules
        failed = self.moduleManager.launchAll()

        # 5. Handle launch result
        if failed:
            self.activeMission.missionStatus = MissionStatus.FAILED
            MissionManager.logger.error("[MissionManager] Mission FAILED (module launch error)")
            return

        # 6. Mission is now running
        self.activeMission.missionStatus = MissionStatus.RUNNING
        MissionManager.logger.info("[MissionManager] Mission RUNNING")

    # ==================================================
    # Stop Mission
    # ==================================================
    def stopMission(self):
        """
        Stops mission and unregisters it from CommunicationLayer
        """

        if self.activeMission is None:
            MissionManager.logger.warning("[MissionManager] No active mission")
            return

        MissionManager.logger.info("[MissionManager] Stopping mission...")

        # Shutdown modules
        self.moduleManager.shutdownAll()

        # Update state
        self.activeMission.missionStatus = MissionStatus.FINISHED

        # Remove mission from CommunicationLayer
        CommunicationLayer.getInstance().registerMission(None)

        # Clear reference
        self.activeMission = None

        MissionManager.logger.info("[MissionManager] Mission stopped")

    # ==================================================
    # Resolve Modules
    # ==================================================
    def resolveModules(self, missionType: str):
        """
        Loads modules from JSON and converts them to Module objects
        """

        filePath = f"missions/{missionType}.json"

        if not os.path.exists(filePath):
            raise FileNotFoundError(f"[MissionManager] Missing config: {filePath}")

        with open(filePath, "r") as file:
            data = json.load(file)

        modules = []

        for m in data.get("modules", []):
            module = Module(
                pkg=m["pkg"],
                launchFile=m["launch_file"],
                heartbeatTopic=m["heartbeats_topic"],
                isNodeMsg=m["is_node_msg"]
            )
            modules.append(module)

        MissionManager.logger.info(f"[MissionManager] Loaded {len(modules)} modules for {missionType}")

        return modules

    # ==================================================
    # Getter
    # ==================================================
    def getActiveMission(self):
        return self.activeMission