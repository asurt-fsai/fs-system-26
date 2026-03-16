from supervisor.helpers.Module.ModuleManager import ModuleManager
from supervisor.helpers.CommunicationLayer import CommunicationLayer
from supervisor.helpers.Missions.MissionFinishing import MissionFinishing
from enum import Enum


class MissionType(Enum):
    """
    Input  : None
    Output : None
    Logic  : Defines the possible mission types.
             Derived from amiState received from CAN bus via Supervisor.
             Used by MissionManager to create correct MissionFinishing subclass
             and resolve correct module list from missionModuleMap.
    """
    ACCELERATION = 1
    SKIDPAD      = 2
    AUTOCROSS    = 3
    TRACKDRIVE   = 4

class MissionManager:

    _instance = None

    @classmethod
    def getInstance(cls):
        """
        Input  : None
        Output : MissionManager — the singleton instance
        Logic  : Create instance if not exists.
                 Return existing instance otherwise.
        """
        pass

    def __init__(self, communication, moduleManager):
        """
        Input  : communication (CommunicationLayer) — event bus
                 moduleManager (ModuleManager) — manages module lifecycle
        Output : None
        Logic  : Store references.
                 Initialize activeMission = None.
                 Define hardcoded missionModuleMap per mission type.
        """
        pass

    def createMission(self, missionType):
        """
        Input  : missionType — derived from Supervisor.amiState (CAN signal)
        Output : MissionFinishing — the created mission object
        Logic  : Use missionType to instantiate the correct MissionFinishing subclass.
                AccelerationMission, SkidpadMission, AutocrossMission, or TrackdriveMission.
                Store as activeMission.
                Register mission with CommunicationLayer.
                Return the mission.
        """
        pass

    def startMission(self):
        """
        Input  : None — uses self.activeMission set by createMission()
        Output : None
        Logic  : Guard — if self.activeMission is None raise error or return.
                Call self.resolveModules(self.activeMission.missionType)
                to get the required module list.
                Call self.dispatchModulesToManager(modules).
                Call self.moduleManager.launchAll().
                Start self.activeMission.
        """
        pass

    def resolveModules(self, missionType) -> list:
        """
        Input  : missionType (MissionType) — mission type to resolve modules for
        Output : list[Module] — list of modules required for this mission
        Logic  : Look up missionModuleMap[missionType].
                 Return the hardcoded list of modules for that mission type.
        """
        pass

    def dispatchModulesToManager(self, modules: list):
        """
        Input  : modules (list[Module]) — modules to register with manager
        Output : None
        Logic  : Call moduleManager.registerModules(modules).
        """
        pass
