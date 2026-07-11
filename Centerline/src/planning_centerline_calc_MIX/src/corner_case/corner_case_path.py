'''
Description: This module calculates the path if 2 or less cones are detected on both sides
'''

from typing import List
import math
import numpy as np

from src.types_file.types import FloatArray
from numpy.typing import NDArray
from src.utils.math_utils import (
    angleFrom2dVector,
    angleToVector
)
from src.utils.cone_types import ConeTypes
from icecream import ic     ##why?## ##was it used for debugging?? ##

class CornerCasesPath:
    """
    Class that is responsible for calculating the path
    when 2 or less cones are detected on both sides
    """
    def __init__(self,
        carPosition: FloatArray,
        carDirection: np.float64,
        cones: List[FloatArray]
    ) -> None:
        self.carPosition = carPosition
        self.carDirection = carDirection
        self.cones = cones

    def getPath(
        self,
    ) -> FloatArray:
        '''
        calculates the path
        '''
        ## remove cones that are too close than 0.001 meters apart, to prevent path calc errors from duplicates ##
        ## cleans both left (blue) and right (yellow) cone arrays /// check the ##
        print(f"DEBUG_TRACE: Input cones - Left: {len(self.cones[ConeTypes.left])}, Right: {len(self.cones[ConeTypes.right])}")
        print(f"DEBUG_TRACE: Car Pos: {self.carPosition}, Dir: {self.carDirection}")
        
        self.cones[ConeTypes.left] = duplicateConeCleaner(self.cones[ConeTypes.left])
        self.cones[ConeTypes.right] = duplicateConeCleaner(self.cones[ConeTypes.right])
        
        print(f"DEBUG_TRACE: Cleaned cones - Left: {len(self.cones[ConeTypes.left])}, Right: {len(self.cones[ConeTypes.right])}")
        
        #if len(self.cones[ConeTypes.left]) > 1 and len(self.cones[ConeTypes.right]) > 1:
        #    return createStraightPath(self.carPosition, self.carDirection, 5)
            
        if len(self.cones[ConeTypes.left]) >= 1 and len(self.cones[ConeTypes.right]) >= 1:
            print(f"DEBUG_TRACE: 2DifferentPoints triggered. Left: {self.cones[ConeTypes.left]}, Right: {self.cones[ConeTypes.right]}")
            return self.getPathFrom2DifferentPoints()

        if len(self.cones[ConeTypes.left]) >= 2:
            """beyzabat el cones eli metla5bat mabeen heya either left or right"""
            sortedCones = sortCones(self.cones[ConeTypes.left], self.carPosition)
            print(f"DEBUG_TRACE: 2PointsSameSideBlue triggered. Cones: {sortedCones}")
            return self.getPathFrom2PointsSameSide(sortedCones, ConeTypes.BLUE)
        if len(self.cones[ConeTypes.right]) >= 2:
            sortedCones = sortCones(self.cones[ConeTypes.right], self.carPosition)
            print(f"DEBUG_TRACE: 2PointsSameSideYellow triggered. Cones: {sortedCones}")
            return self.getPathFrom2PointsSameSide(sortedCones, ConeTypes.YELLOW)
        """
        if len(self.cones[ConeTypes.left]) == 1 and len(self.cones[ConeTypes.right]) == 1:
            print(f"DEBUG_TRACE: 2DifferentPoints triggered. Left: {self.cones[ConeTypes.left]}, Right: {self.cones[ConeTypes.right]}")
            return self.getPathFrom2DifferentPoints()
        """
            ### 1 cone case ###
        if len(self.cones[ConeTypes.left]) == 1 and len(self.cones[ConeTypes.right]) == 0:
            print(f"DEBUG_TRACE: 1ConeLeft triggered")
            return self.pathToAvoidCone(self.cones[ConeTypes.left][0], ConeTypes.BLUE)
            
        if len(self.cones[ConeTypes.right]) == 1 and len(self.cones[ConeTypes.left]) == 0:
            print(f"DEBUG_TRACE: 1ConeRight triggered")
            return self.pathToAvoidCone(self.cones[ConeTypes.right][0], ConeTypes.YELLOW)

            ### Fallback for 0 cone case ###
        if len(self.cones[ConeTypes.left]) == 0 and len(self.cones[ConeTypes.right]) == 0:
             print(f"DEBUG_TRACE: ZeroConesCaseEntered")
             return createStraightPath(self.carPosition, self.carDirection, 5)

        else:
            print(f"DEBUG_TRACE: No valid corner case condition met. Returning None. Left Len: {len(self.cones[ConeTypes.left])}, Right Len: {len(self.cones[ConeTypes.right])}")
            return None

        """Fakkar fe 7ewar lel 1 cone case"""
        # if len(self.cones[ConeTypes.left]) == 1:
        #     #print("avoiding cones")
        #     return self.pathToAvoidCone(self.cones[ConeTypes.left], ConeTypes.BLUE)
        # if len(self.cones[ConeTypes.right]) == 1:
        #     #print("avoiding cones")
        #     return self.pathToAvoidCone(self.cones[ConeTypes.right], ConeTypes.YELLOW)
        # print(f"ZeroConesCase Entered")
        # return createStraightPath(self.carPosition, self.carDirection, 5)

    """Not used????"""
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
            newDirection = np.float64(angleFrom2dVector(cone - self.carPosition)) + 0.4
            return createStraightPath(self.carPosition, newDirection, 10)
        # if cone is BLUE
        if not self.isConeOnRightSide(cone):
            return createStraightPath(self.carPosition, self.carDirection, 10)
        newDirection = np.float64(angleFrom2dVector(cone - self.carPosition)) - 0.4
        return createStraightPath(self.carPosition, newDirection, 10)

    """Since it's only used within the pathToAcvoidCone function, which itself is not used, can we say it's also not used"""
    """We can still use it in the future, if needed, will  probably need it later"""
    def isConeOnRightSide(
        self,
        conePosition: FloatArray
    ) -> bool:
        """
        Checks if a cone is on the car's right side based on positions and direction.

        Args:
            car_position: A 2D vector (x, y) representing the car's position.
            car_direction: The car's direction in degrees (0: right, 90: up, 180: left, 270: down).
            cone_position: A 2D vector (x, y) representing the cone's position.

        Returns:
            True if the cone is on the car's right side, False otherwise.
        """
        carDirectionVector = angleToVector(self.carDirection)

        carToCone = conePosition - self.carPosition

        crossProduct = np.cross(carDirectionVector, carToCone)

        if crossProduct < 0:
            return True
        return False

    def getPathFrom2DifferentPoints(self) -> FloatArray:
        '''
        get path from car position passing between left and right cones.
        Uses all available cone pairs to create midpoints, and blends
        the path direction with the car's forward direction to prevent
        wild diagonal paths when only 1 pair exists.
        '''
        leftCones = self.cones[ConeTypes.left]
        rightCones = self.cones[ConeTypes.right]
        
        # Compute midpoints between all available left-right pairs
        midpoints = []
        numPairs = min(len(leftCones), len(rightCones))
        for i in range(numPairs):
            mid = (leftCones[i] + rightCones[i]) / 2
            midpoints.append(mid)
        
        if len(midpoints) == 0:
            return createStraightPath(self.carPosition, self.carDirection, 10)
        
        if len(midpoints) >= 2:
            # Multiple midpoints: create path through them
            path = np.array(midpoints)
            # Extend the path forward along the last segment direction
            lastDir = path[-1] - path[-2]
            lastDirNorm = lastDir / np.linalg.norm(lastDir)
            lastAngle = np.float64(angleFrom2dVector(lastDirNorm))
            extension = createStraightPath(path[-1], lastAngle, 5)
            path = np.row_stack((path, extension[1:]))  # skip first point (duplicate)
            return path
        
        # Single midpoint: blend direction with car's forward to prevent diagonal
        point = midpoints[0]
        direction = point - self.carPosition
        dirNorm = np.linalg.norm(direction)
        if dirNorm < 0.01:
            return createStraightPath(self.carPosition, self.carDirection, 10)
        
        unit_direction = direction / dirNorm
        
        # Car's forward direction vector
        carForward = angleToVector(self.carDirection)
        
        # Blend: 70% midpoint direction + 30% car forward
        # This prevents the path from aiming too far off-axis
        blended = 0.7 * unit_direction + 0.3 * carForward
        blended = blended / np.linalg.norm(blended)
        
        directionAngle = np.float64(angleFrom2dVector(blended))
        path = createStraightPath(self.carPosition, directionAngle, 10)
        return path

    """Efham dihh bete3mel eh belzabt"""
    def getPathFrom2PointsSameSide(
        self,
        cones: FloatArray,
        color: ConeTypes
    ) -> FloatArray:
        '''
        Calculates path with only 2 points/cones given
        '''
        pointsDirection = cones[1] - cones[0] #Gets direction vector between the 2 cones
        directionConeToPoint: FloatArray
        if color == ConeTypes.BLUE:
            directionConeToPoint = np.array([pointsDirection[1], -pointsDirection[0]])
        else:
            directionConeToPoint = np.array([-pointsDirection[1], pointsDirection[0]])
        if not  np.all(directionConeToPoint==0):
            directionConeToPoint = directionConeToPoint / np.linalg.norm(directionConeToPoint)
        # print(f"directionConeToPoint: {directionConeToPoint}")
        points: FloatArray = cones + directionConeToPoint * 1.5
        pointsDirectionAngle: np.float64 = np.float64(angleFrom2dVector(pointsDirection))
        """Could cause the problem with the hairpins? Examine it closer"""
        ### segment 3 create a 10 meter path from the offsetted point ###
        ### that is 1.5 meters parallel t the 1st cone ###
        path = createStraightPath(points[0], pointsDirectionAngle, 10)
        ### segment 2 extends the path from segment 3 backwards ###
        ### to reduce the need for sharp connections, and make everything go smoother ###
        pathExtension = self.extendPathBackwards(path)
        ### segment 1 connects the path update to the current path of the car ###
        pathExtention = self.connectPathToCar(pathExtension[0])
        if len(pathExtention) > 0:
            path = np.row_stack((pathExtention, path))
        # print(f"cones[1] - cones[0] = {pointsDirection}")
        # print(f"pointsDirectionAngle: {pointsDirectionAngle}")
        return path

    def connectPathToCar(self, firstPoint: FloatArray) -> FloatArray:
        """
        Connect the path update to the current path of the car. This is done by
        calculating the distance between the last point of the path update and the
        current position of the car. The path update is then shifted by this distance.
        """
        num = distanceBetweenPoints(self.carPosition, firstPoint)
        # print(f"num = {num}")
        if not math.isnan(num):
            numOfPoints = math.floor(num)
            direction = np.float64(angleFrom2dVector(firstPoint - self.carPosition))

            pathUpdate = createStraightPath(self.carPosition, direction, numOfPoints)
        else:
            pathUpdate = np.array([])

        return pathUpdate
    def extendPathBackwards(self, pathUpdate: FloatArray) -> FloatArray:
        """
        Extend the calculated path backwards to reduce the need for sharp connections.
        This helps avoid cone collisions during sharp turns.
        """
        if len(pathUpdate) < 2:
            return pathUpdate
        
        # Calculate how far back we need to extend
        distanceToFirstPoint = np.linalg.norm(self.carPosition - pathUpdate[0])
        
        # If path is already close to car, no need to extend
        if distanceToFirstPoint < 1.0:
            return pathUpdate
        
        # Determine the direction to extend backwards
        # Use the direction from second point to first point (reverse of path direction)
        if len(pathUpdate) >= 2:
            pathDirection = pathUpdate[1] - pathUpdate[0]  # Direction path is going
            backwardDirection = -pathDirection  # Opposite direction
            backwardDirection = backwardDirection / np.linalg.norm(backwardDirection)  # Normalize
        else:
            # Fallback: use car-to-path direction
            carToPath = pathUpdate[0] - self.carPosition
            backwardDirection = -carToPath / np.linalg.norm(carToPath)
        
        # Calculate how many points to add backwards
        # We want to extend far enough that the car is either on the path or very close to it
        extensionDistance = min(distanceToFirstPoint + 0.5, 3.0)  # Don't extend too far
        numBackwardPoints = int(extensionDistance / 0.5)  # 0.5m spacing
        
        # Generate backward extension points
        backwardPoints = []
        for i in range(1, numBackwardPoints + 1):
            backwardPoint = pathUpdate[0] + backwardDirection * (i * 0.5)
            backwardPoints.append(backwardPoint)
        
        # Reverse the backward points so they're in correct order
        backwardPoints.reverse()
        
        # Combine backward extension with original path
        if len(backwardPoints) > 0:
            backwardArray = np.array(backwardPoints)
            extendedPath = np.row_stack((backwardArray, pathUpdate))
            return extendedPath
        
        return pathUpdate

def sortCones(cones: FloatArray, carPosition: FloatArray) -> FloatArray:
    '''
    sorts the cones so that the closest one is first:
    e.g; compares the dustance from cone[0] to cone[1], and
    swaps them if cone[1] is closer to the car, ensuirng the path 
    uses the nearest cone first.
    
    '''
    sortedCones: FloatArray = cones.copy()
    if distanceBetweenPoints(carPosition, cones[0]) > distanceBetweenPoints(carPosition, cones[1]):
        sortedCones[0] = cones[1]
        sortedCones[1] = cones[0]
    return sortedCones

def createStraightPath(startPoint: FloatArray, direction: np.float64, numPoints: int) -> FloatArray:
    """
    Creates a list of points along a straight path with a given distance between points.

    Args:
        start_point: A tuple (x, y) representing the starting point.
        direction: Direction in degrees (0: right, 90: up, 180: left, 270: down).
        num_points: Total number of points in the path (including the starting point).

    Returns:
        A list of tuples (x, y) representing the points on the path.
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

def distanceBetweenPoints(point1: FloatArray, point2: FloatArray) -> np.float64:
    """
    Calculates the euclidean distance between two 2D points.

    Args:
        point1: A tuple (x, y) representing the first point.
        point2: A tuple (x, y) representing the second point.

    Returns:
        The distance between the two points.
        if distance between them < 0.001 meters, then it's a duplicate from sensor noise
        and deletes that duplicate to prevent errors in path planning
    """
    x1, y1 = point1
    x2, y2 = point2
    try:
        return np.float64(math.sqrt((x2 - x1)**2 + (y2 - y1)**2))
    except ValueError:
        return np.float64(0)

def duplicateConeCleaner(cones: NDArray) -> NDArray:
    if len(cones) < 2:
        return cones
    
    indices_to_delete = []
    
    for i in range(1, len(cones)):
        # Check adjacent cones
        if distanceBetweenPoints(cones[i], cones[i-1]) < 0.001:
            indices_to_delete.append(i)
            print("DEBUG_TRACE: deleted duplicate cone")
            
    if indices_to_delete:
        cones = np.delete(cones, indices_to_delete, axis=0)
        
    return cones