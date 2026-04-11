class CommandInterface:
    """
    Invoker that executes commands
    """

    def executeCommand(self, command):
        command.execute()
      
