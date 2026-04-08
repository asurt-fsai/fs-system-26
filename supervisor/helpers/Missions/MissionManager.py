import json
import os
import logging

# Module logger
logger = logging.getLogger(__name__)

from supervisor.helpers.Module.Module import Module
from supervisor.helpers.Missions.AccelerationMission import AccelerationMission
from supervisor.helpers.Missions.SkidpadMission import SkidpadMission
from supervisor.helpers.Missions.AutocrossMission import AutocrossMission
from supervisor.helpers.Missions.TrackdriveMission import TrackdriveMission
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.CommunicationLayer import CommunicationLayer


class MissionManager:
    _instance = None

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
    # Start Mission (MAIN ENTRY)
    # ==================================================
    def startMission(self, missionType: str):
        """
        Input  : missionType (str)
        Output : None
        Logic  :
            1. Create mission object
            2. Load modules from JSON
            3. Send modules to ModuleManager
            4. Launch modules
            5. Set mission RUNNING if success
        """

        if self.moduleManager is None:
            raise Exception("[MissionManager] ModuleManager not set")

        # Prevent double start
        if self.activeMission and self.activeMission.missionStatus == MissionStatus.RUNNING:
            logger.info("Mission already running")
            return
            return

        # 1. Create mission
        missionClass = self.missionFactory.get(missionType)
        if missionClass is None:
            raise ValueError(f"[MissionManager] Unknown mission: {missionType}")

        self.activeMission = missionClass()
        self.activeMission.missionStatus = MissionStatus.IDLE

        # Register mission in CommunicationLayer
        CommunicationLayer.getInstance().registerMission(self.activeMission)

        logger.info(f"Created mission {missionType}")

        # 2. Load modules from JSON (USING YOUR OLD LOGIC)
        modules = self.loadModulesFromJSON(missionType)

        # 3. Send to ModuleManager
        logger.debug("Registering modules with ModuleManager: %s", [(m.pkg, m.launchFile) for m in modules])
        self.moduleManager.registerModules(modules)
        logger.debug("Modules registered with ModuleManager")

        # 4. Launch modules
        failed = self.moduleManager.launchAll()

        # 5. Update mission state
        if failed:
            self.activeMission.missionStatus = MissionStatus.FAILED
            logger.info("Mission FAILED (launch error)")
            return

        self.activeMission.missionStatus = MissionStatus.RUNNING
        logger.info("Mission RUNNING")

    # ==================================================
    # JSON Loader (THIS IS YOUR OLD LOGIC CLEANED)
    # ==================================================
    def loadModulesFromJSON(self, missionType: str):
        """
        Input  : missionType (str)
        Output : List[Module]
        Logic  :
            - Open corresponding JSON file
            - Extract modules
            - Convert each entry into Module object
        """

        filePath = f"missions/{missionType}.json"

        if not os.path.exists(filePath):
            raise FileNotFoundError(f"[MissionManager] Missing config: {filePath}")

        with open(filePath, "r") as file:
            config = json.load(file)

        modules = []

        # 🔥 EXACT SAME LOGIC YOU USED (cleaned)
        for i in config["modules"]:
            modules.append(
                Module(
                    i["pkg"],
                    i["launch_file"],
                    i["heartbeats_topic"],
                    bool(i["is_node_msg"])
                )
            )

        logger.info(f"Loaded {len(modules)} modules for {missionType}")
        logger.debug("Loaded module entries: %s", config.get("modules", []))

        return modules

    def resolveModules(self, missionType: str):
        """Backward-compatible wrapper used by tests: returns same as loadModulesFromJSON."""
        return self.loadModulesFromJSON(missionType)

    # ==================================================
    # Stop Mission
    # ==================================================
    def stopMission(self):
        """
        Input  : None
        Output : None
        Logic  :
            - Shutdown all modules
            - Set mission FINISHED
            - Remove mission from CommunicationLayer
        """

        if self.activeMission is None:
            logger.info("No active mission")
            return

        logger.info("Stopping mission")
        self.moduleManager.shutdownAll()

        self.activeMission.missionStatus = MissionStatus.FINISHED
        CommunicationLayer.getInstance().registerMission(None)

        self.activeMission = None

        logger.info("Mission stopped")

    # ==================================================
    # Getter
    # ==================================================
    def getActiveMission(self):
        return self.activeMission