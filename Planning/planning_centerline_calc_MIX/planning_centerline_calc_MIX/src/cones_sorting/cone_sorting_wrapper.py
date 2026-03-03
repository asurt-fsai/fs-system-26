"""
Cone sorting wrapper class
Description: Entry point for Pathing/ConeSorting
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

import numpy as np

from src.cones_sorting.core_cone_sorter import ConeSorter
from src.types_file.types import FloatArray
from src.utils.cone_types import ConeTypes


class ConeSorting:
    """Class that takes all Pathing/ConeSorting responsibilities"""

    def __init__( ### These are the parameters needed for cone sorting ###
        self,
        maxNNeighbors: int,
        maxDist: float,
        maxDistToFirst: float,
        maxLength: int,
        thresholdDirectionalAngle: float,
        thresholdAbsoluteAngle: float,
        useUnknownCones: bool = True
    ):
        """
        Init method.

        Args:
            maxNNeighbors, maxDist, maxDistToFirst: Arguments for ConeSorter.
            maxLength: Arguments for ConeSorter. The maximum length of the valid trace
                in a sorting algorithm.
            thresholdDirectionalAngle: The threshold for the directional angle that is
                the minimum angle for consecutive cones to be connected in the direction
                of the trace (clockwise for left cones, counter-clockwise for right cones).
            thresholdAbsoluteAngle: The threshold for the absolute angle that is the
                minimum angle for consecutive cones to be connected regardless of the
                cone type.
            useUnknownCones: Whether to use unknown ( as is no color info is known) cones
                in the sorting algorithm.
        """
        
        """ func is located in this file """
        self.newInput = ConeSortingInput()  ### define an input variable to store incoming data (inputs) ###

        """ func is located in this file """
        self.const = ConeSortingConstants( 
            ### define constants and store them in a dataclass,
            # to make them easier to access ###
            maxNNeighbors=maxNNeighbors,
            maxDist=maxDist,
            maxDistToFirst=maxDistToFirst,
            maxLength=maxLength,
            thresholdDirectionalAngle=thresholdDirectionalAngle,
            thresholdAbsoluteAngle=thresholdAbsoluteAngle,
            useUnknownCones=useUnknownCones
        )
        self.state = ConeSortingState()

    def setNewInput(self, newInput: ConeSortingInput) -> None:
        """Save inputs from other nodes in a varible."""
        self.newInput = newInput

    def transitionInputToState(self) -> None:
        """Parse and save the inputs in the state varible."""
        self.state.positionGlobal, self.state.directionGlobal = (
            self.newInput.slamPosition,
            self.newInput.slamDirection,
        )

        self.state.conesByTypeArray = self.newInput.perceptionCones.copy()
        if not self.const.useUnknownCones:
            self.state.conesByTypeArray[ConeTypes.UNKNOWN] = np.zeros((0, 2))

    def runConeSorting(
        self,
    ) -> Tuple[FloatArray, FloatArray]:
        """
        Calculate the sorted cones.

        Returns:
            The sorted cones. The first array contains the sorted blue (left) cones and
            the second array contains the sorted yellow (right) cones.
        """
        # makes the transition from set inputs to usable state varibles
        self.transitionInputToState()

        # calculate the sorted cones
        coneSorter = ConeSorter(
            self.const.maxNNeighbors,
            self.const.maxDist,
            self.const.maxDistToFirst,
            self.const.maxLength,
            self.const.thresholdDirectionalAngle,
            self.const.thresholdAbsoluteAngle,
        )

        leftCones, rightCones = coneSorter.sortLeftRight(
            self.state.conesByTypeArray,
            self.state.positionGlobal,
            self.state.directionGlobal,
        )
        # print(f"Sorted Cones after running sortLeftRight method are:\n---------------\n leftCones = {leftCones}\n rightCones = {rightCones}")
        return leftCones, rightCones


@dataclass
class ConeSortingInput:
    """Dataclass holding inputs."""

    perceptionCones: list[FloatArray] = field(
        default_factory=lambda: [np.zeros((0, 2)) for _ in ConeTypes]
    )
    slamPosition: FloatArray = field(default_factory=lambda: np.zeros(2))
    slamDirection: np.float_ = np.float_(0.0)


@dataclass
class ConeSortingConstants:
    """Dataclass holding calculation parameters"""
### The ConeSortingConstants dataclass serves as a configuration container
#  that stores all the tunable parameters used by the cone sorting algorithm.
# It decouples the algorithm parameters from the logic, allowing them to be 
# configured once during initialization and accessed consistently throughout
#  execution without passing them as individual arguments to multiple methods.
#  This makes the code cleaner and easier to tune performance.  ###
    thresholdDirectionalAngle: float
    thresholdAbsoluteAngle: float
    maxNNeighbors: int
    maxDist: float
    maxDistToFirst: float
    maxLength: int
    useUnknownCones: bool


@dataclass
class ConeSortingState:
    """Dataclass holding calculation variables."""

    positionGlobal: FloatArray = field(default_factory=lambda: np.zeros(2))
    directionGlobal: np.float_ = np.float_(0.0)
    conesByTypeArray: list[FloatArray] = field(
        default_factory=lambda: [np.zeros((0, 3)) for _ in ConeTypes]
    )
