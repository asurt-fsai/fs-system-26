import json
import os
import logging
from enum import Enum
from typing import Optional

try:
    from ament_index_python.packages import get_package_share_directory
except ImportError:
    get_package_share_directory = None

logger = logging.getLogger(__name__)

from supervisor.helpers.Module.ModuleState import ModuleState
from supervisor.helpers.Missions.mission_types import MissionType
from supervisor.helpers.CommunicationLayer import CommunicationLayer
from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.Missions.AccelerationMission import AccelerationMission
from supervisor.helpers.Missions.SkidpadMission import SkidpadMission
from supervisor.helpers.Missions.AutocrossMission import AutocrossMission
from supervisor.helpers.Missions.TrackdriveMission import TrackdriveMission
from supervisor.helpers.Missions.StaticAMission import StaticAMission
from supervisor.helpers.Missions.StaticBMission import StaticBMission
from supervisor.helpers.Missions.AutoDemoMission import AutoDemoMission
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from supervisor.helpers.Module.Module import Module
from supervisor.helpers.Module.ModuleManager import ModuleManager
from supervisor.helpers.Module.LocalLauncher import LocalLauncher


# ======================================================
# Mission Type Enum
# ======================================================




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
    Supervisor calls directly:
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

    # MissionType -> candidate JSON config basenames (without .json)
    # Keep both legacy and current naming styles for compatibility.
    _json_name_map = {
        MissionType.ACCELERATION: ["acceleration"],
        MissionType.SKIDPAD: ["skidpad"],
        MissionType.AUTOCROSS: ["autocross"],
        MissionType.TRACKDRIVE: ["trackdrive", "trackDrive"],
        MissionType.STATIC_A: ["static_a", "staticA"],
        MissionType.STATIC_B: ["static_b", "staticB"],
        MissionType.AUTODEMO: ["autonomousdemo", "autonomousDemo"],
    }

    @staticmethod
    def _candidate_json_dirs() -> list:
        """Return candidate JSON directories for both installed and source layouts."""
        dirs = []

        if get_package_share_directory is not None:
            try:
                share_dir = get_package_share_directory("supervisor_pkg")
                dirs.append(os.path.join(share_dir, "json"))
            except Exception:
                pass

        # Source-tree fallback (src/supervisor_pkg/json)
        dirs.append(os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "json")))
        return dirs

    # Path resolved relative to this file — works on any machine


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
        self.package_share = None
        self.JSON_DIR = None
        if get_package_share_directory is not None:
            try:
                self.package_share = get_package_share_directory('supervisor_pkg')
                self.JSON_DIR = os.path.join(self.package_share, "json")
            except Exception:
                pass

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
        if self.activeMission is not None:
            current_status = getattr(self.activeMission, "missionStatus", None)
            if current_status in (MissionStatus.IDLE, MissionStatus.RUNNING):
                raise RuntimeError(
                    f"[MissionManager] Mission already active ({self.activeMission.__class__.__name__}, "
                    f"status={current_status.name}). Shutdown or finish current mission first."
                )

        missionClass = self._missionFactory.get(missionType)

        if missionClass is None:
            logger.error(
                f"[MissionManager] Unknown missionType={missionType} — "
                f"valid: {list(self._missionFactory.keys())}"
            )
            raise ValueError(f"[MissionManager] Unknown missionType: {missionType}")
        communication = CommunicationLayer.getInstance()
        self.activeMission = missionClass(communication ,self.supervisor)
        # Some mission classes do not define missionType; set it uniformly here.
        self.activeMission.missionType = missionType
        self.activeMission.missionStatus = MissionStatus.IDLE


        communication.registerMission(self.activeMission)

        logger.info(
            f"[MissionManager] Mission created — "
            f"class={missionClass.__name__} type={missionType.name}"
            f"with state = {self.activeMission.missionStatus.name}"
        )


        return self.activeMission

    def clearActiveMission(self) -> None:
        """Clear active mission and deregister it from communication routing."""
        communication = CommunicationLayer.getInstance()
        communication.registerMission(None)
        self.activeMission = None
        logger.info("[MissionManager] Active mission cleared")

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

        # Register heartbeat subscriptions for mission modules
        communication = self.supervisor.communication if self.supervisor is not None else CommunicationLayer.getInstance()
        communication.registerModuleHeartbeats(modules)

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

        logger.info(
            f"[MissionManager] Mission modules launched — "
            f"type={missionType} modules={len(modules)} awaiting AS READY"
        )

    # ------------------------------------------------------------------
    # Stop Mission
    # ------------------------------------------------------------------

    def stopMission(self) -> None:
        """
        Input  : None
        Output : None
        Logic  :
            - Guard: no active mission
            - Shutdown all modules via ModuleManager
            - Log any modules that failed to shut down
            - Set mission status FINISHED
            - Deregister mission from CommunicationLayer
            - Clear activeMission reference
        """

        if self.activeMission is None:
            logger.warning("[MissionManager] stopMission called but no active mission — ignoring")
            return

        mission_name = type(self.activeMission).__name__

        logger.info(f"[MissionManager] Stopping mission={mission_name}")

        if self.moduleManager is None:
            logger.error("[MissionManager] ModuleManager not set — cannot shutdown modules")
        else:
            failed = self.moduleManager.shutdownAll()
            if failed:
                failed_names = [m.pkg for m in failed]
                logger.warning(
                    f"[MissionManager] {len(failed)} module(s) failed to shut down: {failed_names}"
                )
            else:
                logger.info("[MissionManager] All modules shut down cleanly")

        self.activeMission.missionStatus = MissionStatus.FINISHED

        communication = self.supervisor.communication if self.supervisor is not None else CommunicationLayer.getInstance()
        communication.registerModuleHeartbeats([])

        CommunicationLayer.getInstance().registerMission(None)

        self.activeMission = None

        logger.info(f"[MissionManager] Mission={mission_name} stopped")
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
        if isinstance(missionType, MissionType):
            type_candidates = self._json_name_map.get(missionType)
            if type_candidates is None:
                raise ValueError(f"[MissionManager] No JSON mapping for mission type: {missionType}")
        else:
            type_candidates = [str(missionType)]

        filePath = None
        for json_dir in self._candidate_json_dirs():
            for type_str in type_candidates:
                candidate = os.path.join(json_dir, f"{type_str}.json")
                logger.debug(f"[MissionManager] Probing config path={candidate}")
                if os.path.exists(candidate):
                    filePath = candidate
                    break
            if filePath is not None:
                break

        if filePath is None:
            logger.error(f"[MissionManager] Config not found for mission candidates {type_candidates}")
            raise FileNotFoundError(
                f"[MissionManager] Missing config for mission candidates: {type_candidates}"
            )

        logger.debug(f"[MissionManager] Loading modules from path={filePath}")

        with open(filePath, "r") as file:
            config = json.load(file)

        modules = []

        # Prefer Supervisor's communication instance when available
        # (Supervisor injects itself via setSupervisor()). Fall back to singleton.
        if self.supervisor is not None:
            communication = self.supervisor.communication
        else:
            communication = CommunicationLayer.getInstance()
        launcher = LocalLauncher()

        for entry in config.get("modules", []):
            # Basic JSON validation
            if not isinstance(entry, dict):
                logger.error(f"[MissionManager] Invalid module entry (not object): {entry}")
                continue
            if "pkg" not in entry or "launch_file" not in entry:
                logger.error(f"[MissionManager] Missing required module fields in entry: {entry}")
                continue

            pkg = entry["pkg"]
            launch_file = entry["launch_file"]
            heartbeat_topic = entry.get("heartbeats_topic") or entry.get("heartbeat_topic")

            if get_package_share_directory is not None:
                try:
                    share_dir = get_package_share_directory(pkg)
                    launch_path = os.path.join(share_dir, "launch", launch_file)
                    if not os.path.exists(launch_path):
                        logger.warning(
                            f"[MissionManager] Launch file not found for pkg={pkg}: {launch_file}"
                        )
                except Exception:
                    logger.warning(
                        f"[MissionManager] Unable to resolve share directory for pkg={pkg}"
                    )

            module = Module(
                pkg,
                launch_file,
                communication,
                launcher,
                entry.get("heartbeat_timeout", 5.0),
                entry.get("startup_timeout"),
                heartbeat_topic,
            )
            modules.append(module)
            logger.debug(
                f"[MissionManager] Module loaded — "
                f"pkg={entry['pkg']} "
                f"heartbeat_timeout={entry.get('heartbeat_timeout', 5.0)} "
                f"startup_timeout={entry.get('startup_timeout')}"
            )

        logger.info(
            f"[MissionManager] Loaded {len(modules)} modules for missionType={missionType}"
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

        if self.moduleManager is None:
            return False

        modules = self.moduleManager.getModules()

        if not modules:
            mission_type = getattr(self.activeMission, "missionType", None)
            if mission_type in (MissionType.STATIC_A, MissionType.STATIC_B, MissionType.AUTODEMO):
                return True
            return False

        for module in modules.values():
            if module.state != ModuleState.Running:
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
