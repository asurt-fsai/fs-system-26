'''
Description: This module calculates the path if 2 or less cones are detected on both sides
'''

from typing import List
import math
import numpy as np
from numpy.typing import NDArray

from planning_acceleration.cone_types import ConeTypes

FloatArray = NDArray[np.float_]


class CalculatePath:
    """
    Class that is responsible for calculating the path
    when 2 or less cones are detected on both sides
    """
    def __init__(self,
        carPosition: FloatArray,
        carDirection: np.float_,
        cones: List[FloatArray]
    ) -> None:
        self.carPosition = carPosition
        self.carDirection = carDirection
        self.cones = cones
        self.initialPosition = carPosition
        self.updatedInitialPosition = carPosition

    def getPath(
        self,
    ) -> FloatArray:
        '''
        calculates the path
        '''
        if len(self.cones[ConeTypes.left]) >= 2 and len(self.cones[ConeTypes.right]) >= 2:
            sortedleft = sortCones(self.cones[ConeTypes.left], self.initialPosition)
            sortedright = sortCones(self.cones[ConeTypes.right], self.initialPosition)
            self.updatedInitialPosition = (sortedleft[0] + sortedright[0])/2
            self.destination = (sortedleft[-1] + sortedright[-1])/2
            direction_vec = self.destination - self.updatedInitialPosition
            #review angle alongside coordinate axis, whether it is correct
            direction_angle = float(angleFrom2dVector(direction_vec))
            

            #WTF????????
            # Extend path backwards by 20 meters so the car has points near it
            #dir_norm = direction_vec / np.linalg.norm(direction_vec) if np.linalg.norm(direction_vec) != 0 else np.array([math.cos(direction_angle), math.sin(direction_angle)])
            #start_pt = self.updatedInitialPosition - dir_norm * 20.0
            start_pt = self.updatedInitialPosition
            
            #find sutitable num of points(ex: 15)
            path = createStraightPath(start_pt, direction_angle, 150)
            startIndex = find_nearest_point_vectorized(path, self.carPosition)
            return path[startIndex:]
            
        if len(self.cones[ConeTypes.left]) >= 1 and len(self.cones[ConeTypes.right]) >= 1:
            self.destination = (self.cones[ConeTypes.left][-1] + self.cones[ConeTypes.right][-1])/2
            direction_vec = self.destination - self.initialPosition
            direction_angle = float(angleFrom2dVector(direction_vec))
            path = createStraightPath(self.carPosition, direction_angle, 100)
            startIndex = find_nearest_point_vectorized(path, self.carPosition)
            return path[startIndex:]
            
        # if len(self.cones[ConeTypes.left]) >= 2:
        #     sortedCones = sortCones(self.cones[ConeTypes.left], self.carPosition)
        #     return self.getPathFrom2PointsSameSide(sortedCones, ConeTypes.BLUE)
        
        if len(self.cones[ConeTypes.right]) >= 2:
            sortedCones = sortCones(self.cones[ConeTypes.right], self.carPosition)
            return self.getPathFrom2PointsSameSide(sortedCones, ConeTypes.YELLOW)
            
        if len(self.cones[ConeTypes.left]) == 1:
            return self.pathToAvoidCone(self.cones[ConeTypes.left], ConeTypes.BLUE)
            
        if len(self.cones[ConeTypes.right]) == 1:
            return self.pathToAvoidCone(self.cones[ConeTypes.right], ConeTypes.YELLOW)
            
        return createStraightPath(self.carPosition, self.carDirection, 100)

    def pathToAvoidCone(
        self,
        cone: FloatArray,
        color: ConeTypes
    ) -> FloatArray:
        '''
        Calculate path if one cone is found
        '''
        if color == ConeTypes.YELLOW:
            if self.isConeOnRightSide(cone):
                return createStraightPath(self.carPosition, self.carDirection, 10)
            newDirection = np.float_(angleFrom2dVector(cone - self.carPosition)) + 0.4
            return createStraightPath(self.carPosition, newDirection, 10)
            
        # if cone is BLUE
        if not self.isConeOnRightSide(cone):
            return createStraightPath(self.carPosition, self.carDirection, 10)
        newDirection = np.float_(angleFrom2dVector(cone - self.carPosition)) - 0.4
        return createStraightPath(self.carPosition, newDirection, 10)

    def isConeOnRightSide(
        self,
        conePosition: FloatArray
    ) -> bool:
        """
        Checks if a cone is on the car's right side based on positions and direction.
        """
        carDirectionVector = angleToVector(self.carDirection)
        carToCone = conePosition - self.carPosition
        crossProduct = np.cross(carDirectionVector, carToCone)

        if crossProduct < 0:
            return True
        return False

    def getPathFrom2PointsSameSide(
        self,
        cones: FloatArray,
        color: ConeTypes
    ) -> FloatArray:
        '''
        Calculates path with only 2 points given
        '''
        pointsDirection = cones[1] - cones[0]
        directionConeToPoint: FloatArray
        if color == ConeTypes.BLUE:
            directionConeToPoint = np.array([pointsDirection[1], -pointsDirection[0]])
        else:
            directionConeToPoint = np.array([-pointsDirection[1], pointsDirection[0]])
            
        if np.linalg.norm(directionConeToPoint) != 0:
            directionConeToPoint = directionConeToPoint / np.linalg.norm(directionConeToPoint)
            
        points: FloatArray = cones + directionConeToPoint * 1.5
        pointsDirectionAngle: np.float_ = np.float_(angleFrom2dVector(pointsDirection))
        path = createStraightPath(points[0], pointsDirectionAngle, 200)
        return path
    
    def updateInput(self, carPosition, carDirection, cones):
        self.carPosition = carPosition
        self.carDirection = carDirection
        self.cones = cones
        self.initialPosition = carPosition 


def sortCones(cones: FloatArray, carPosition: FloatArray) -> FloatArray:
    '''
    sorts the cones
    '''
    sortedCones = cones[
            np.argsort(
                (cones[:, 0] - carPosition[0]) ** 2
                + (cones[:, 1] - carPosition[1]) ** 2
            )
        ]
    return sortedCones

def createStraightPath(startPoint: FloatArray, direction: np.float_, numPoints: int) -> FloatArray:
    """
    Creates a list of points along a straight path with a given distance between points.
    """
    path: FloatArray = np.array([startPoint])
    x, y = startPoint
    # Calculate step vector components
    deltaX = math.cos(direction)
    deltaY = math.sin(direction)

    # Generate subsequent points
    for _ in range(1, numPoints):
        x += deltaX
        y += deltaY
        newPoint = [x,y]
        path = np.row_stack((path, newPoint))

    return path

def angleToVector(angle: np.float_) -> FloatArray:
    """
    Converts an angle in radians to a 2D unit vector.
    """
    x = math.cos(angle)
    y = math.sin(angle)

    # Normalize to create a unit vector
    magnitude = math.sqrt(x**2 + y**2)
    x /= magnitude
    y /= magnitude
    unitVector = np.array([x / magnitude, y / magnitude], dtype=np.float_)

    return unitVector

def angleFrom2dVector(vecs: np.ndarray) -> np.ndarray:
    """
    Calculates the angle of each vector in `vecs`.
    """
    assert vecs.shape[-1] == 2, "vecs must be a 2d vector"

    vecsFlat = vecs.reshape(-1, 2)
    angles = np.arctan2(vecsFlat[:, 1], vecsFlat[:, 0])
    returnValue = angles.reshape(vecs.shape[:-1])

    return returnValue

def find_nearest_point_vectorized(path: np.ndarray, car_pos: np.ndarray) -> np.ndarray:
        """
        FASTEST METHOD: Vectorized computation using NumPy.
        """
        if len(path) == 0:
            return 0, car_pos, 0.0
        
        # Vectorized distance calculation - VERY FAST
        distances_squared = np.sum((path - car_pos) ** 2, axis=1)
        nearest_index = np.argmin(distances_squared)
        
        return nearest_index
