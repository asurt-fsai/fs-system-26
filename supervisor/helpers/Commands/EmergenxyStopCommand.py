class EmergencyStopCommand:

    def __init__(self, missionManager, moduleManager):
        """
        Input  : missionManager (MissionManager)
                 moduleManager (ModuleManager)
        Output : None
        Logic  : Store references.
        """
        pass

    def execute(self):
        """
        Input  : None
        Output : None
        Logic  : Stop active mission immediately via missionManager.stopMission().
                 Shutdown all modules via moduleManager.shutdownAll().
        """
        pass