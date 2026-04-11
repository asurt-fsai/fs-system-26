from abc import ABC, abstractmethod


class Command(ABC):
    """
    Command Interface
    All commands must implement execute()
    """

    @abstractmethod
    def execute(self):
        pass
