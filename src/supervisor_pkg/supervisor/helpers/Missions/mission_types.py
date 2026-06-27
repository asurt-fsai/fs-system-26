from enum import Enum


class MissionType(Enum):
    """
    Defines possible mission types.
    Derived from Supervisor's amiState (CAN signal).
    Used by MissionManager to create the correct MissionFinishing
    subclass and load the correct module list from JSON.
    """
    ACCELERATION = 1
    SKIDPAD      = 2
    AUTOCROSS    = 3
    TRACKDRIVE   = 4
    STATIC_A     = 5
    STATIC_B     = 6
    AUTODEMO     = 7