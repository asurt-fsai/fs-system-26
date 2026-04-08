from supervisor.helpers.Module.ModuleManager import ModuleManager
from supervisor.helpers.CommunicationLayer import CommunicationLayer
from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from supervisor.helpers.Missions.AccelerationMission import AccelerationMission
from supervisor.helpers.Missions.SkidpadMission import SkidpadMission
from supervisor.helpers.Missions.AutocrossMission import AutocrossMission
from supervisor.helpers.Missions.TrackdriveMission import TrackdriveMission
from supervisor.helpers.Missions.MissionStatus import MissionStatus
from enum import Enum


class MissionType(Enum):
    """
    Defines the possible mission types.

    These are derived from the amiState received by the Supervisor
    from the CAN bus.

    MissionManager uses this enum to:
        - create the correct MissionFinishing subclass
        - resolve the correct module dependencies
    """

    ACCELERATION = 1
    SKIDPAD = 2
    AUTOCROSS = 3
    TRACKDRIVE = 4


class MissionManager:
    """
    MissionManager

    Responsibilities:
        - Create mission objects
        - Resolve mission module dependencies
        - Send modules to ModuleManager
        - Request module launch
        - Set mission state to RUNNING


    """

    _instance = None

    # ======================================================
    # Singleton Access
    # ======================================================

    @classmethod
    def getInstance(cls, communication=None, moduleManager=None):
        """
        Input:
            communication (CommunicationLayer)
            moduleManager (ModuleManager)

        Output:
            MissionManager singleton instance

        Logic:
            If instance does not exist → create it.
            Otherwise return the existing instance.
        """

        if cls._instance is None:

            if communication is None or moduleManager is None:
                raise Exception(
                    "MissionManager requires CommunicationLayer and ModuleManager"
                )

            cls._instance = MissionManager(communication, moduleManager)

        return cls._instance

    # ======================================================
    # Constructor
    # ======================================================

    def __init__(self, communication, moduleManager):
        """
        Input:
            communication (CommunicationLayer)
            moduleManager (ModuleManager)

        Output:
            None

        Logic:
            Store references and initialize active mission.
        """

        self.communication = communication
        self.moduleManager = moduleManager

        # Currently active mission
        self.activeMission = None

        # Mapping mission type → module list
        # (can later be replaced by JSON loading)
        self.missionModuleMap = {
            MissionType.ACCELERATION: [],
            MissionType.SKIDPAD: [],
            MissionType.AUTOCROSS: [],
            MissionType.TRACKDRIVE: [],
        }

    # ======================================================
    # Create Mission
    # ======================================================

    def createMission(self, missionType):
        """
        Input:
            missionType (MissionType)

        Output:
            MissionFinishing instance

        Logic:
            Instantiate the correct MissionFinishing subclass,
            store it as activeMission, and register it with
            CommunicationLayer so it receives events.
        """

        if missionType == MissionType.ACCELERATION:
            mission = AccelerationMission()

        elif missionType == MissionType.SKIDPAD:
            mission = SkidpadMission()

        elif missionType == MissionType.AUTOCROSS:
            mission = AutocrossMission()

        elif missionType == MissionType.TRACKDRIVE:
            mission = TrackdriveMission()

        else:
            raise ValueError("Unknown mission type")

        # Store mission
        self.activeMission = mission

        # Initialize status
        self.activeMission.missionStatus = MissionStatus.IDLE

        # Register mission with communication layer
        self.communication.registerMission(self.activeMission)

        return mission

    # ======================================================
    # Start Mission
    # ======================================================

    def startMission(self):
        """
        Input:
            None (uses self.activeMission)

        Output:
            None

        Logic:
            Resolve required modules,
            send them to ModuleManager,
            request module launch,
            update mission status.
        """

        if self.activeMission is None:
            raise Exception("No mission created")

        missionType = self.activeMission.missionType

        # Resolve required modules
        modules = self.resolveModules(missionType)

        # Send modules to ModuleManager
        self.dispatchModulesToManager(modules)

        # Ask ModuleManager to launch modules
        self.moduleManager.launchAll()

        # Update mission state
        self.activeMission.missionStatus = MissionStatus.RUNNING

    # ======================================================
    # Resolve Modules
    # ======================================================

    def resolveModules(self, missionType) -> list:
        """
        Input:
            missionType (MissionType)

        Output:
            list[Module]

        Logic:
            Look up missionModuleMap and return
            modules required for that mission.
        """

        if missionType not in self.missionModuleMap:
            raise Exception("Mission type not defined in module map")

        return self.missionModuleMap[missionType]

    # ======================================================
    # Dispatch Modules
    # ======================================================

    def dispatchModulesToManager(self, modules: list):
        """
        Input:
            modules (list[Module])

        Output:
            None

        Logic:
            Forward module list to ModuleManager.
        """

        self.moduleManager.registerModules(modules)

    # ======================================================
    # Get Active Mission
    # ======================================================

    def getActiveMission(self):
        """
        Returns the currently active mission.
        """

        return self.activeMission

    # ======================================================
    # Get ModuleManager
    # ======================================================

    def getModuleManager(self):
        """
        Returns the module manager reference.
        """

        return self.moduleManager
