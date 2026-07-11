from enum import Enum

class MissionStatus(Enum):
    """
    Input  : None
    Output : None
    Logic  : Defines the possible states of a mission lifecycle.
             IDLE     — mission created but not started
             RUNNING  — mission is active
             FINISHED — mission completed successfully
             FAILED   — mission failed
    """
    IDLE     = 0
    RUNNING  = 1
    FINISHED = 2
    FAILED   = 3