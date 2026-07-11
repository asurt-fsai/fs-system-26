from supervisor.helpers.Commands.Command import Command


class RestartModuleCommand(Command):
    """Restart a single module via its own restart() method."""

    def __init__(self, module):
        self.module = module

    def execute(self):
        self.module.restart()
