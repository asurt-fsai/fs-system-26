import json
import os
import logging
from enum import Enum
from typing import Optional
logger = logging.getLogger(__name__)

from supervisor.helpers.Missions.AutoDemoMission import AutoDemoMission
from supervisor.helpers.Missions.StaticAMission import StaticAMission
from supervisor.helpers.Missions.StaticBMission import StaticBMission
from supervisor.helpers.Module.ModuleState import ModuleState
from supervisor.helpers.Module.Module import Module
from supervisor.helpers.Module.ModuleManager import ModuleManager
from supervisor.helpers.CommunicationLayer import CommunicationLayer
from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.Missions.AccelerationMission import AccelerationMission
from supervisor.helpers.Missions.SkidpadMission import SkidpadMission
from supervisor.helpers.Missions.AutocrossMission import AutocrossMission
from supervisor.helpers.Missions.TrackdriveMission import TrackdriveMission
from supervisor.helpers.Missions.MissionStatus import MissionStatus


# ======================================================
# Mission Type Enum
# ======================================================

class MissionType(Enum):
    """
    Defines possible mission types.
    Derived from Supervisor's amiState (CAN signal).
    Used by MissionManager to create the correct MissionFinishing
    subclass and load the correct module list from JSON.
    """
    ACCELERATION = 1
    SKIDPAD      = 2
    AUTOCROSS    = 3
    TRACKDRIVE   = 4
    STATIC_A     = 5
    STATIC_B     = 6
    AUTODEMO     = 7


# ======================================================
# MissionManager
# ======================================================

class MissionManager:
    """
    Singleton orchestrator responsible for mission lifecycle
    and module dispatch.

    Responsibilities
    ----------------
    - Create the correct MissionFinishing subclass from MissionType
    - Load required modules from JSON config per mission type
    - Dispatch modules to ModuleManager before launch
    - Track active mission status

    Flow
    ----
    Supervisor issues StartMissionCommand
        --> createMission(missionType)
                --> instantiates MissionFinishing subclass
                --> registers mission with CommunicationLayer
        --> startMission()
                --> resolveModules(missionType)     [reads JSON]
                --> dispatchModulesToManager(modules)
                --> moduleManager.launchAll()
                --> sets mission status RUNNING

    Supervisor issues StopMissionCommand
        --> stopMission()
                --> moduleManager.shutdownAll()
                --> sets mission status FINISHED
                --> deregisters mission from CommunicationLayer

    JSON path
    ---------
    Modules are loaded from:
        <package_root>/json/{missionType}.json
    Resolved relative to this file so it works on any machine.
    """

    _instance  = None
    _initialised = False

    # Path resolved relative to this file — works on any machine
    JSON_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "json")

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._initialised = False
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def getInstance() -> "MissionManager":
        """
        Input  : None
        Output : MissionManager — the singleton instance
        Logic  : Create instance if not exists, return existing otherwise.
        """
        if MissionManager._instance is None:
            MissionManager._instance = MissionManager()
        return MissionManager._instance

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------

    def __init__(self):
        """
        Input  : None
        Output : None
        Logic  : Initialise state. ModuleManager injected via setModuleManager().
        """
        if MissionManager._initialised:
            return
        MissionManager._initialised = True

        self.activeMission: Optional[MissionFinishing] = None
        self.moduleManager: Optional[ModuleManager]    = None
        self.supervisor = None

        self._missionFactory = {
            MissionType.ACCELERATION : AccelerationMission,
            MissionType.SKIDPAD      : SkidpadMission,
            MissionType.AUTOCROSS    : AutocrossMission,
            MissionType.TRACKDRIVE   : TrackdriveMission,
            MissionType.STATIC_A     : StaticAMission,
            MissionType.STATIC_B     : StaticBMission,
            MissionType.AUTODEMO     : AutoDemoMission, 
        }

        logger.info("[MissionManager] Initialised")

    # ------------------------------------------------------------------
    # Dependency Injection
    # ------------------------------------------------------------------

    def setModuleManager(self, moduleManager: ModuleManager) -> None:
        """
        Input  : moduleManager (ModuleManager)
        Output : None
        Logic  : Inject ModuleManager after construction.
        """
        self.moduleManager = moduleManager
        logger.info("[MissionManager] ModuleManager injected")

    def setSupervisor(self, supervisor) -> None:
        """Inject Supervisor reference."""
        self.supervisor = supervisor
        logger.info("[MissionManager] Supervisor injected")
        
    # ------------------------------------------------------------------
    # Create Mission
    # ------------------------------------------------------------------

    def createMission(self, missionType: MissionType) -> MissionFinishing:
        """
        Input  : missionType (MissionType) — derived from Supervisor.amiState
        Output : MissionFinishing — the created mission instance
        Logic  :
            - Instantiate correct MissionFinishing subclass via factory
            - Set status IDLE
            - Store as activeMission
            - Register with CommunicationLayer so callbacks route correctly
        """
        missionClass = self._missionFactory.get(missionType)

        if missionClass is None:
            logger.error(
                f"[MissionManager] Unknown missionType={missionType} — "
                f"valid: {list(self._missionFactory.keys())}"
            )
            raise ValueError(f"[MissionManager] Unknown missionType: {missionType}")
        communication = CommunicationLayer.getInstance()
        self.activeMission = missionClass(communication ,self.supervisor)
        self.activeMission.missionStatus = MissionStatus.IDLE


        communication.registerMission(self.activeMission)

        logger.info(
            f"[MissionManager] Mission created — "
            f"class={missionClass.__name__} type={missionType.name}"
            f"with state = {self.activeMission.missionStatus.name}"
        )


        return self.activeMission

    # ------------------------------------------------------------------
    # Start Mission
    # ------------------------------------------------------------------

    def startMission(self) -> None:
        """
        Input  : None — uses self.activeMission set by createMission()
        Output : None
        Logic  :
            - Guard: ModuleManager must be injected
            - Guard: activeMission must exist
            - Guard: prevent double start if already RUNNING
            - Resolve modules from JSON for this mission type
            - Dispatch modules to ModuleManager
            - Launch all modules
            - Set mission status RUNNING
        """
        if self.moduleManager is None:
            logger.error("[MissionManager] ModuleManager not set — call setModuleManager() first")
            raise Exception("[MissionManager] ModuleManager not set")

        if self.activeMission is None:
            logger.error("[MissionManager] No active mission — call createMission() first")
            raise Exception("[MissionManager] No active mission")

        if self.activeMission.missionStatus == MissionStatus.RUNNING:
            logger.warning(
                f"[MissionManager] Mission already RUNNING — ignoring startMission()"
            )
            return

        missionType = self.activeMission.missionType

        logger.info(f"[MissionManager] Starting mission — type={missionType}")

        # Resolve modules from JSON
        modules = self.resolveModules(missionType)

        # Dispatch to ModuleManager
        self.dispatchModulesToManager(modules)

        # Launch
        failed = self.moduleManager.launchAll()

        # Set status based on launch result
        if failed:
            failed_names = [m.pkg for m in failed]
            self.activeMission.missionStatus = MissionStatus.FAILED
            logger.error(
                f"[MissionManager] Mission FAILED — "
                f"{len(failed)} module(s) failed to launch: {failed_names}"
            )
            return

        self.activeMission.missionStatus = MissionStatus.RUNNING
        logger.info(
            f"[MissionManager] Mission RUNNING — "
            f"type={missionType} modules={len(modules)}"
        )

    # ------------------------------------------------------------------
    # Stop Mission
    # ------------------------------------------------------------------

    #def stopMission(self) -> None:
    #    """
    #    Input  : None
    #    Output : None
    #    Logic  :
    #        - Guard: no active mission
    #        - Shutdown all modules via ModuleManager
    #        - Log any modules that failed to shut down
    #        - Set mission status FINISHED
    #        - Deregister mission from CommunicationLayer
    #        - Clear activeMission reference
    #    """
    #       
    #     if self.activeMission is None:
    #         logger.warning("[MissionManager] stopMission called but no active mission — ignoring")
    #         return
    #
    #     mission_name = type(self.activeMission).__name__
    #
    #     logger.info(f"[MissionManager] Stopping mission={mission_name}")
    #
    #     failed = self.moduleManager.shutdownAll()
    #
    #     if failed:
    #         failed_names = [m.pkg for m in failed]
    #         logger.warning(
    #             f"[MissionManager] {len(failed)} module(s) failed to shut down: {failed_names}"
    #         )
    #     else:
    #         logger.info("[MissionManager] All modules shut down cleanly")
    #
    #     self.activeMission.missionStatus = MissionStatus.FINISHED
    #
    #     CommunicationLayer.getInstance().registerMission(None)
    #
    #     self.activeMission = None
    #
    #     logger.info(f"[MissionManager] Mission={mission_name} stopped")
    # ------------------------------------------------------------------
    # JSON Loader
    # ------------------------------------------------------------------

    def loadModulesFromJSON(self, missionType) -> list:
        """
        Input  : missionType (MissionType or str)
        Output : list[Module]
        Logic  :
            - Resolve JSON path relative to package root
            - Open and parse JSON file
            - Construct Module object for each entry
            - Return module list
        """
        # Accept both MissionType enum and plain string
        type_str = missionType.name.lower() if isinstance(missionType, MissionType) else missionType

        filePath = os.path.join(self.JSON_DIR, f"{type_str}.json")

        logger.debug(f"[MissionManager] Loading modules from path={filePath}")

        if not os.path.exists(filePath):
            logger.error(f"[MissionManager] Config not found — path={filePath}")
            raise FileNotFoundError(f"[MissionManager] Missing config: {filePath}")

        with open(filePath, "r") as file:
            config = json.load(file)

        modules = []

        for entry in config.get("modules", []):
            module = Module(
                entry["pkg"],
                entry["launch_file"],
                entry["heartbeats_topic"],
                bool(entry["is_node_msg"])
            )
            modules.append(module)
            logger.debug(
                f"[MissionManager] Module loaded — "
                f"pkg={entry['pkg']} "
                f"heartbeats_topic={entry['heartbeats_topic']} "
                f"is_node_msg={entry['is_node_msg']}"
            )

        logger.info(
            f"[MissionManager] Loaded {len(modules)} modules for missionType={type_str}"
        )

        return modules

    # ------------------------------------------------------------------
    # Resolve Modules
    # ------------------------------------------------------------------

    def resolveModules(self, missionType) -> list:
        """
        Input  : missionType (MissionType or str)
        Output : list[Module]
        Logic  : Load modules from JSON for the given mission type.
        """
        logger.debug(f"[MissionManager] resolveModules — missionType={missionType}")
        return self.loadModulesFromJSON(missionType)

    # ------------------------------------------------------------------
    # Dispatch Modules to ModuleManager
    # ------------------------------------------------------------------

    def dispatchModulesToManager(self, modules: list) -> None:
        """
        Input  : modules (list[Module])
        Output : None
        Logic  :
            - Call moduleManager.registerModules(modules)
            - ModuleManager shuts down previous modules before loading new ones
        """
        logger.info(
            f"[MissionManager] Dispatching {len(modules)} modules to ModuleManager — "
            f"pkgs={[m.pkg for m in modules]}"
        )
        self.moduleManager.registerModules(modules)
        
    #=================================
    # checking that mission is ready 
    #=================================
    def isReady(self) -> bool:
        """
        Returns True if mission is ready to run.

        Logic:
        - Active mission must exist
        - Mission must be in RUNNING state (modules launched)
        - All modules must be in RUNNING state (heartbeat received)
        """

        if self.activeMission is None:
            return False

        if self.activeMission.missionStatus != MissionStatus.RUNNING:
            return False

        if self.moduleManager is None:
            return False

        modules = self.moduleManager.getModules()

        if not modules:
            return False

        for module in modules.values():
            if module.state != ModuleState.RUNNING:
                return False

        return True    

    # ------------------------------------------------------------------
    # Getter
    # ------------------------------------------------------------------

    def getActiveMission(self) -> Optional[MissionFinishing]:
        """
        Input  : None
        Output : MissionFinishing or None — the currently active mission
        """
        return self.activeMission
