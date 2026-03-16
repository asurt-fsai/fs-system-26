class RestartModuleCommand:

    def __init__(self, moduleManager, targetModule):
        """
        Input  : moduleManager (ModuleManager) — manager that owns the module
                 targetModule (Module) — the module to restart
        Output : None
        Logic  : Store references.
        """
        pass

    def execute(self):
        """
        Input  : None
        Output : None
        Logic  : Look up targetModule by pkg name in moduleManager.
                 Call module.restart().
        """
        pass