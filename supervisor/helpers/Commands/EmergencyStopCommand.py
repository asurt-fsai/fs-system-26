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
        Logic  : 
                 Shutdown all modules via moduleManager.shutdownAll().
                 Stop mission via MissionManager.stopMission()
        """
        pass